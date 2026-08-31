"""Placement: prove where a learner stands before recommending anything.

The product promise is that nobody is handed a curriculum on the strength of a
self-rating. So the flow is:

    declare a career path  ->  short graded probes  ->  a starting point

One **probe** per course: a short adaptive assessment on that course's hardest
probeable skill. Passing a probe is evidence the course is already known, so the
starting point is simply the first course whose probe was not passed.

Two design rules worth keeping:

* **Nothing is stored that cannot be recomputed.** ``placement_sessions`` maps a
  probed skill to the ``AssessmentSession`` that graded it, and every number in
  the result is derived from those sessions on read. There is no second copy of a
  score that can drift away from the evidence.
* **Stop as soon as the answer is known.** If a probe fails badly, the courses
  after it depend on the one that just failed, so asking about them teaches us
  nothing and only lengthens the check. Placement ends early and says so.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.data.assessment_bank import ITEMS_BY_SKILL
from app.data.paths import PATH_INDEX
from app.models import AssessmentSession, LearningDigitalTwin
from app.services.knowledge_graph import get_knowledge_graph

#: Questions per probe. Short on purpose — this is placement, not the course test.
PROBE_QUESTIONS = 3

#: A probe needs at least this many items in the bank to be worth asking.
MIN_ITEMS_FOR_PROBE = 2

#: Below this accuracy the courses after the probe cannot be meaningfully
#: assessed, because they build on the skill that just failed.
STOP_EARLY_ACCURACY = 40.0


# --------------------------------------------------------------------------- #
#  Plan construction                                                          #
# --------------------------------------------------------------------------- #


def _probe_skill_for_course(course: dict[str, Any]) -> Optional[str]:
    """The course's hardest skill that the bank can actually assess.

    Hardest rather than easiest: the point of a probe is to find out whether the
    course can be skipped, and only the top of a course can answer that.
    """
    graph = get_knowledge_graph()
    candidates = [
        skill_id
        for skill_id in course["skills"]
        if len(ITEMS_BY_SKILL.get(skill_id, [])) >= MIN_ITEMS_FOR_PROBE
    ]
    if not candidates:
        return None

    def rank(skill_id: str) -> tuple[int, int]:
        node = graph.get(skill_id)
        return (node.difficulty_weight if node else 0, len(ITEMS_BY_SKILL[skill_id]))

    return max(candidates, key=rank)


def probe_plan(path_id: str) -> list[dict[str, Any]]:
    """Ordered probes for a path: one per course that has assessable skills."""
    path = PATH_INDEX.get(path_id)
    if not path:
        return []
    graph = get_knowledge_graph()
    plan: list[dict[str, Any]] = []
    for course in path["courses"]:
        skill_id = _probe_skill_for_course(course)
        if not skill_id:
            continue
        plan.append(
            {
                "skill_id": skill_id,
                "skill_name": graph.name_of(skill_id),
                "course_id": course["id"],
                "course_title": course["title"],
                "questions": min(PROBE_QUESTIONS, len(ITEMS_BY_SKILL[skill_id])),
            }
        )
    return plan


def questions_for_probe(twin: LearningDigitalTwin, skill_id: str) -> int:
    for probe in probe_plan(twin.path_id or ""):
        if probe["skill_id"] == skill_id:
            return probe["questions"]
    return PROBE_QUESTIONS


def is_probe_skill(twin: LearningDigitalTwin, skill_id: str) -> bool:
    return skill_id in set(twin.placement_skills or [])


# --------------------------------------------------------------------------- #
#  Lifecycle                                                                  #
# --------------------------------------------------------------------------- #


def begin(db: Session, twin: LearningDigitalTwin, path_id: str) -> None:
    """Attach a path and a fresh probe plan. Safe to call again on path change."""
    plan = probe_plan(path_id)
    twin.path_id = path_id
    twin.placement_skills = [p["skill_id"] for p in plan]
    twin.placement_sessions = {}
    twin.placement_result = None
    # A path with no curriculum behind it has nothing to probe, so there is
    # nothing to place the learner against. Saying "complete" would be a lie;
    # "unavailable" is the honest terminal state.
    twin.placement_status = "in_progress" if plan else "unavailable"
    db.flush()


def register_probe_session(
    db: Session, twin: LearningDigitalTwin, skill_id: str, session_id: str
) -> None:
    sessions = dict(twin.placement_sessions or {})
    sessions[skill_id] = session_id
    twin.placement_sessions = sessions
    if twin.placement_status == "pending":
        twin.placement_status = "in_progress"
    db.flush()


def skip(db: Session, twin: LearningDigitalTwin) -> None:
    """Escape hatch. Recorded as skipped, never as passed."""
    twin.placement_status = "skipped"
    twin.placement_result = None
    db.flush()


def reset(db: Session, twin: LearningDigitalTwin) -> None:
    twin.placement_sessions = {}
    twin.placement_result = None
    twin.placement_status = "in_progress" if (twin.placement_skills or []) else "pending"
    db.flush()


# --------------------------------------------------------------------------- #
#  Reading state                                                              #
# --------------------------------------------------------------------------- #


def _probe_results(
    db: Session, twin: LearningDigitalTwin, plan: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Merge the plan with graded evidence from each probe's session."""
    graph = get_knowledge_graph()
    sessions = twin.placement_sessions or {}
    confidence = {s.skill_id: s.confidence for s in twin.verified_skills}

    rows: list[dict[str, Any]] = []
    for probe in plan:
        session_id = sessions.get(probe["skill_id"])
        session = db.get(AssessmentSession, session_id) if session_id else None
        result = (session.result or {}) if session and session.status == "completed" else {}
        done = bool(result)
        accuracy = float(result.get("accuracy") or 0.0) if done else None
        rows.append(
            {
                **probe,
                "session_id": session_id,
                "status": (
                    "complete" if done else "in_progress" if session else "not_started"
                ),
                "accuracy": accuracy,
                "verified_level": result.get("verified_level"),
                "confidence": round(confidence.get(probe["skill_id"], 0.0), 1) if done else None,
                "weak_concepts": result.get("weak_concepts") or [],
                # Passed means the graded confidence cleared the same bar the rest
                # of the platform uses, not merely that the probe was answered.
                "passed": (
                    confidence.get(probe["skill_id"], 0.0) >= graph.confidence_threshold
                    if done
                    else None
                ),
            }
        )
    return rows


def _level_for(accuracy: float, passed_count: int) -> str:
    if passed_count >= 3 and accuracy >= 80:
        return "advanced"
    if passed_count >= 1 and accuracy >= 55:
        return "intermediate"
    if accuracy >= 30:
        return "early_basics"
    return "no_experience"


def _first_module_for(skill_id: str) -> Optional[str]:
    node = get_knowledge_graph().get(skill_id)
    return next(iter(node.recommended_practice), None) if node else None


def _starting_point(path_id: str, rows: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """The first course whose probe was not passed. That is where to begin."""
    path = PATH_INDEX.get(path_id)
    if not path:
        return None
    passed = {r["course_id"] for r in rows if r["passed"]}
    graph = get_knowledge_graph()

    for course in path["courses"]:
        if course["id"] in passed:
            continue
        first_skill = course["skills"][0] if course["skills"] else None
        return {
            "path_id": path_id,
            "course_id": course["id"],
            "course_title": course["title"],
            "blurb": course["blurb"],
            "first_skill_id": first_skill,
            "first_skill_name": graph.name_of(first_skill) if first_skill else None,
            "first_module_id": _first_module_for(first_skill) if first_skill else None,
        }

    # Everything probed was passed: there is no earlier course to send them to.
    return None


def _summary_text(rows: list[dict[str, Any]], start: Optional[dict[str, Any]]) -> str:
    graded = [r for r in rows if r["status"] == "complete"]
    passed = [r for r in graded if r["passed"]]
    if start is None:
        return (
            f"You cleared every probe we ran ({len(passed)}/{len(graded)}). There is no earlier "
            "course to send you to, so the next real signal is a project under judged conditions."
        )
    if not passed:
        return (
            f"Across {len(graded)} graded probe(s) nothing cleared the verification bar yet, so "
            f"you start at the beginning: {start['course_title']}. That is not a setback — it "
            "means your route is built on evidence instead of a guess."
        )
    return (
        f"{len(passed)} of {len(graded)} probes cleared the bar. You can skip what you already "
        f"proved and start at {start['course_title']}."
    )


def state(db: Session, twin: LearningDigitalTwin) -> dict[str, Any]:
    """Full placement state, finalising it when the evidence is sufficient.

    Finalising on read keeps the client out of it: there is no "complete
    placement" call a browser could forget to make or make twice.
    """
    graph = get_knowledge_graph()
    path_id = twin.path_id or ""
    plan = probe_plan(path_id)

    # Keep the stored plan in step with the registry, so adding a course does not
    # leave existing learners probing a plan that no longer exists.
    planned = [p["skill_id"] for p in plan]
    if planned != list(twin.placement_skills or []) and twin.placement_status in {
        "pending",
        "in_progress",
    }:
        twin.placement_skills = planned
        db.flush()

    rows = _probe_results(db, twin, plan)
    graded = [r for r in rows if r["status"] == "complete"]

    stopped_early = False
    next_probe: Optional[dict[str, Any]] = None
    for row in rows:
        if row["status"] == "complete":
            if (row["accuracy"] or 0.0) < STOP_EARLY_ACCURACY:
                stopped_early = True
                break
            continue
        next_probe = row
        break

    complete = bool(plan) and (stopped_early or next_probe is None)

    result = twin.placement_result
    if complete and twin.placement_status not in {"skipped", "unavailable"}:
        accuracy = round(sum(r["accuracy"] or 0.0 for r in graded) / max(1, len(graded)), 1)
        passed_count = sum(1 for r in graded if r["passed"])
        level = _level_for(accuracy, passed_count)
        start = _starting_point(path_id, rows)
        result = {
            "level": level,
            "accuracy": accuracy,
            "probes_graded": len(graded),
            "probes_passed": passed_count,
            "stopped_early": stopped_early,
            "starting_point": start,
            "skip_courses": [
                {"course_id": r["course_id"], "course_title": r["course_title"]}
                for r in graded
                if r["passed"]
            ],
            "summary": _summary_text(rows, start),
        }
        if twin.placement_result != result or twin.placement_status != "complete":
            twin.placement_result = result
            twin.placement_status = "complete"
            db.flush()

    path = PATH_INDEX.get(path_id)
    return {
        "status": twin.placement_status or "pending",
        "path_id": path_id or None,
        "path_label": path["label"] if path else None,
        "confidence_threshold": graph.confidence_threshold,
        "questions_per_probe": PROBE_QUESTIONS,
        "total_probes": len(plan),
        "probes_completed": len(graded),
        "probes": rows,
        "next_probe": next_probe,
        "stopped_early": stopped_early,
        "result": result if (twin.placement_status == "complete") else None,
    }


def summary(db: Session, twin: LearningDigitalTwin) -> dict[str, Any]:
    """Read-only placement headline for surfaces that must not write.

    ``state`` finalises as a side effect, which is right for the placement page
    but wrong for a dashboard GET whose session is never committed.
    """
    plan = probe_plan(twin.path_id or "")
    rows = _probe_results(db, twin, plan)
    graded = [r for r in rows if r["status"] == "complete"]
    path = PATH_INDEX.get(twin.path_id or "")
    return {
        "status": twin.placement_status or "pending",
        "path_id": twin.path_id,
        "path_label": path["label"] if path else None,
        "total_probes": len(plan),
        "probes_completed": len(graded),
        "next_probe": next((r for r in rows if r["status"] != "complete"), None),
        "result": twin.placement_result,
        "required": needs_placement(twin),
    }


def needs_placement(twin: LearningDigitalTwin) -> bool:
    """True while a real recommendation would be a guess."""
    return (twin.placement_status or "pending") in {"pending", "in_progress"} and bool(
        probe_plan(twin.path_id or "")
    )
