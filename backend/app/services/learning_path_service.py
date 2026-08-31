"""The learner's personalised route to their own goal, plus the audit trail of
how that route changed, plus the small resource layer for a single skill gap.

This is deliberately **not** a second curriculum catalog. `/paths` owns the
authored delivery vehicle (path -> course -> lesson -> test -> capstone). This
module owns the learner's *spine*: the ordered set of skills between where the
Digital Twin actually is and the goal it is aimed at, with one next action and
the deterministic reason for it. Where a spine skill happens to be taught by an
existing course, the course is referenced by id so the client links into the
existing course page instead of re-rendering it.

Everything here is derived from stored state:

* confidences come from ``path_service.learner_confidence`` — the identical map
  the course pages grade against, so the two screens cannot disagree;
* per-skill state comes from ``path_service.lesson_state`` — the identical
  predicate, so "locked" means the same thing on both screens;
* the next action comes from ``graph_router.recommend_next`` — the existing
  deterministic routing engine, called, never re-derived;
* adaptation events come from ``ActivityLog`` and ``FailureAnalysis`` rows only.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.assessment_bank import ITEMS_BY_SKILL
from app.data.learning_resources import EXTERNAL_RESOURCES
from app.data.paths import PATHS, course_ids_for_skill
from app.data.practice_modules import PRACTICE_MODULE_INDEX
from app.models import ActivityLog, FailureAnalysis, LearningDigitalTwin, Project, VerifiedSkill
from app.services import digital_twin_service as twin_service
from app.services import graph_router, path_service
from app.services.knowledge_graph import get_knowledge_graph

# ---------------------------------------------------------------------------
#  Per-skill state
# ---------------------------------------------------------------------------

# The three primitives already used across the product are `verified`
# (confidence >= threshold), `unlocked` (KnowledgeGraph.is_unlocked) and
# `needs_improvement` (confidence < threshold, as reported by the Digital Twin).
# `state` below is a *projection* of exactly those three plus "is there any
# evidence at all", so a client can switch on one value without a fourth
# vocabulary appearing. The mapping is total and evaluated in this order:
#
#   verified     -> verified (confidence >= threshold)
#   locked       -> not verified and not unlocked (missing_prerequisites non-empty)
#   not_started  -> unlocked, below threshold, and the twin holds no evidence
#                   (no graded assessment or execution attempt for the skill)
#   needs_work   -> unlocked, below threshold, has evidence, and the failure is
#                   named: weak concepts recorded or an unresolved
#                   FailureAnalysis for this skill
#   in_progress  -> unlocked, below threshold, has evidence, nothing flagged
#
# `verified` outranks `locked` because both flags can be true at once: a skill
# can be proven while a *prerequisite* has since fallen below threshold (the real
# learner's `js_dom` is exactly this today). Calling an already-proven skill
# "locked" would be wrong; the raw `unlocked` and `missing_prerequisites` fields
# are still returned so the client can show the prerequisite warning.
# `locked` otherwise outranks `needs_work`, because pointing a learner at a door
# they cannot open is worse than saying nothing.
STATES = ("locked", "verified", "needs_work", "in_progress", "not_started")


def _state_for(
    lesson: dict[str, Any],
    has_evidence: bool,
    flagged: bool,
) -> str:
    if lesson["verified"]:
        return "verified"
    if not lesson["unlocked"]:
        return "locked"
    if not has_evidence:
        return "not_started"
    return "needs_work" if flagged else "in_progress"


# ---------------------------------------------------------------------------
#  Spine construction
# ---------------------------------------------------------------------------


def _active_project(db: Session, twin: LearningDigitalTwin) -> Optional[Project]:
    if twin.active_project_id:
        project = db.get(Project, twin.active_project_id)
        if project:
            return project
    return db.scalar(
        select(Project)
        .where(Project.user_id == twin.user_id, Project.status == "active")
        .order_by(Project.created_at.desc())
    )


def _target_skills(twin: LearningDigitalTwin, project: Optional[Project]) -> tuple[list[str], str]:
    """The skills the goal actually requires, and where that came from.

    Priority: the active project's declared stack (the most concrete statement
    of what this learner is building), then the skills they claimed at
    onboarding, then — only if both are empty — the skills of the one available
    career path, because otherwise there is nothing to aim at.
    """
    graph = get_knowledge_graph()
    if project and project.tech_stack:
        return graph.skills_for_stack(project.tech_stack), "active_project_tech_stack"

    claimed = [s for s in (twin.claimed_skills or {}) if graph.get(s)]
    if claimed:
        expanded: list[str] = []
        for skill_id in claimed:
            for step in graph.learning_path(skill_id):
                if step not in expanded:
                    expanded.append(step)
        return expanded, "claimed_skills"

    available = next((p for p in PATHS if p["available"]), None)
    if available:
        skills = [s for c in available["courses"] for s in c["skills"]]
        return skills, f"default_path:{available['id']}"
    return [], "none"


def _course_ref(skill_id: str) -> Optional[dict[str, str]]:
    """Which existing course teaches this skill, for linking into `/paths`."""
    for path_id, course_id in course_ids_for_skill(skill_id):
        return {"path_id": path_id, "course_id": course_id}
    return None


def _dominant_path(spine_skills: list[str]) -> Optional[str]:
    """The available path covering the most of this learner's spine."""
    best: Optional[str] = None
    best_hits = 0
    for path in PATHS:
        if not path["available"]:
            continue
        owned = {s for c in path["courses"] for s in c["skills"]}
        hits = sum(1 for s in spine_skills if s in owned)
        if hits > best_hits:
            best, best_hits = path["id"], hits
    return best


def learning_path(db: Session, twin: LearningDigitalTwin) -> dict[str, Any]:
    graph = get_knowledge_graph()
    confidence = path_service.learner_confidence(db, twin)
    evidence = twin_service.evidence_set(twin)
    skills_by_id = {s.skill_id: s for s in twin.verified_skills}

    project = _active_project(db, twin)
    targets, target_source = _target_skills(twin, project)
    spine = path_service.ordered_skills(targets)

    open_gap_skills = set(
        db.scalars(
            select(FailureAnalysis.skill_id).where(
                FailureAnalysis.user_id == twin.user_id, FailureAnalysis.resolved.is_(False)
            )
        ).all()
    )

    recommendation = graph_router.recommend_next(db, twin)
    next_skill_id = recommendation.get("skill_id")

    steps: list[dict[str, Any]] = []
    for index, skill_id in enumerate(spine, start=1):
        lesson = path_service.lesson_state(skill_id, confidence)
        node = graph.get(skill_id)
        row: Optional[VerifiedSkill] = skills_by_id.get(skill_id)
        has_evidence = skill_id in evidence
        flagged = bool((row.weak_concepts if row else None)) or skill_id in open_gap_skills
        steps.append(
            {
                "order": index,
                **lesson,
                # The three existing primitives are in `lesson`
                # (verified / unlocked / missing_prerequisites); these add the
                # Digital Twin's own view of the same skill.
                "claimed_level": row.claimed_level if row else None,
                "verified_level": row.verified_level if row else None,
                "needs_improvement": (
                    row.confidence < graph.confidence_threshold if row else True
                ),
                "has_evidence": has_evidence,
                "weak_concepts": list(row.weak_concepts or []) if row else [],
                "has_open_gap": skill_id in open_gap_skills,
                "state": _state_for(lesson, has_evidence, flagged),
                "prerequisites": list(node.prerequisites) if node else [],
                "unlocks": list(node.unlocks) if node else [],
                "track": node.track if node else None,
                "difficulty_weight": node.difficulty_weight if node else None,
                "taught_by": _course_ref(skill_id),
                "is_next": False,
            }
        )

    # `is_next` is the routing engine's target when that skill is on the spine;
    # otherwise the first actionable, unproven step. Exactly one step is marked.
    next_step = next((s for s in steps if s["skill_id"] == next_skill_id), None)
    if next_step is None:
        next_step = next(
            (s for s in steps if s["unlocked"] and not s["verified"]), None
        )
    if next_step is not None:
        next_step["is_next"] = True

    path_id = _dominant_path(spine)
    next_course_id = None
    if path_id:
        detail = path_service.path_detail(db, twin, path_id)
        next_course_id = detail["next_course_id"] if detail else None

    verified_count = sum(1 for s in steps if s["state"] == "verified")

    return {
        "goal": {
            "goal": twin.goal,
            "experience_level": twin.experience_level,
            "target_stack": list(project.tech_stack or []) if project else [],
            "target_source": target_source,
            "path_id": path_id,
            "next_course_id": next_course_id,
            "active_project_id": project.id if project else None,
            "active_project_title": project.title if project else None,
        },
        "confidence_threshold": graph.confidence_threshold,
        "progress": {
            "skills_total": len(steps),
            "skills_verified": verified_count,
            "percent": (
                round(sum(s["confidence"] for s in steps) / len(steps), 1) if steps else 0.0
            ),
        },
        "path": steps,
        "milestones": _learning_milestones(db, twin, spine, confidence),
        "execution_milestones": _execution_milestones(project),
        "next_action": {
            # Reused verbatim from the deterministic routing engine. The
            # `assessment` and `project` branches legitimately omit
            # `skill_name` / `module_id`, hence the explicit `.get`s.
            "type": recommendation.get("type"),
            "skill_id": recommendation.get("skill_id"),
            "skill_name": recommendation.get("skill_name"),
            "module_id": recommendation.get("module_id"),
            "ticket_id": recommendation.get("ticket_id"),
            "title": recommendation.get("title"),
            "reason": recommendation.get("reason"),
            "explanation": recommendation.get("reason"),
            "reason_source": "deterministic_routing_engine",
            "evidence": recommendation.get("evidence") or {},
            "blocked_ticket": recommendation.get("blocked_ticket"),
            "resources": resources_for_skill(recommendation["skill_id"])["resources"]
            if recommendation.get("skill_id")
            else [],
        },
    }


# ---------------------------------------------------------------------------
#  Milestones
# ---------------------------------------------------------------------------


def _learning_milestones(
    db: Session,
    twin: LearningDigitalTwin,
    spine: list[str],
    confidence: dict[str, float],
) -> list[dict[str, Any]]:
    """Learning milestones = course boundaries of the dominant career path.

    A *learning* milestone and a *project execution* milestone are different
    things and are reported separately. Course boundaries are used here because
    they are the authored teaching unit the learner can actually open (they have
    a test and a capstone), whereas ``Sprint.milestone`` describes delivery
    phases of one project and only exists while a project exists. Sprint
    milestones are still returned, as ``execution_milestones``.
    """
    path_id = _dominant_path(spine)
    if not path_id:
        return []
    path = next(p for p in PATHS if p["id"] == path_id)
    spine_set = set(spine)

    milestones: list[dict[str, Any]] = []
    for course in path["courses"]:
        skills = [s for s in path_service.ordered_skills(course["skills"]) if s in spine_set]
        if not skills:
            continue
        lessons = [path_service.lesson_state(s, confidence) for s in skills]
        completed = sum(1 for l in lessons if l["verified"])
        if completed == len(lessons):
            status = "completed"
        elif any(l["confidence"] > 0 for l in lessons):
            status = "in_progress"
        elif not any(l["unlocked"] for l in lessons):
            status = "locked"
        else:
            status = "not_started"
        milestones.append(
            {
                "name": course["title"],
                "kind": "learning",
                "path_id": path_id,
                "course_id": course["id"],
                "status": status,
                "skills": [
                    {
                        "skill_id": l["skill_id"],
                        "skill_name": l["skill_name"],
                        "confidence": l["confidence"],
                        "verified": l["verified"],
                        "unlocked": l["unlocked"],
                    }
                    for l in lessons
                ],
                "completed_count": completed,
                "total_count": len(lessons),
            }
        )
    return milestones


def _execution_milestones(project: Optional[Project]) -> list[dict[str, Any]]:
    """Project delivery milestones, grouped by ``Sprint.milestone``.

    Distinct from learning milestones: these measure shipped tickets in one
    project, not verified skills on the route to the goal.
    """
    if not project:
        return []
    grouped: dict[str, list[Any]] = {}
    for sprint in project.sprints:
        grouped.setdefault(sprint.milestone, []).extend(sprint.tickets)

    milestones = []
    for name, tickets in grouped.items():
        done = sum(1 for t in tickets if t.status == "done")
        if tickets and done == len(tickets):
            status = "completed"
        elif any(t.status in {"in_progress", "under_review", "failed"} for t in tickets) or done:
            status = "in_progress"
        elif all(t.status == "locked" for t in tickets):
            status = "locked"
        else:
            status = "not_started"
        milestones.append(
            {
                "name": name,
                "kind": "project_execution",
                "project_id": project.id,
                "status": status,
                "skills": sorted({t.target_skill_id for t in tickets}),
                "completed_count": done,
                "total_count": len(tickets),
            }
        )
    return milestones


# ---------------------------------------------------------------------------
#  Adaptations
# ---------------------------------------------------------------------------

# Which ActivityLog event types represent a change to the recommended route.
# `assessment_started`, `ticket_started` and `account_created` are activity, not
# adaptation, so they are excluded.
ADAPTATION_EVENTS = {
    "onboarded",
    "project_created",
    "assessment_completed",
    "practice_passed",
    "practice_failed",
    "ticket_completed",
    "ticket_failed",
}


def _confidence_pair(meta: dict[str, Any]) -> tuple[Optional[float], Optional[float]]:
    """Only returns numbers that were actually written at the time of the event.

    Rows written before the write sites started capturing the pair have no
    honest value, so both stay None and the client must render "not recorded".
    """
    before = meta.get("confidence_before")
    after = meta.get("confidence_after")
    before = float(before) if isinstance(before, (int, float)) else None
    after = float(after) if isinstance(after, (int, float)) else None
    return before, after


def adaptations(db: Session, user_id: str, limit: int = 60) -> dict[str, Any]:
    """Reverse-chronological list of events that changed the recommended route.

    Every event traces to a stored row: an ``ActivityLog`` entry (with its
    ``meta``, which no endpoint previously exposed) and, where one exists, the
    ``FailureAnalysis`` it produced.
    """
    graph = get_knowledge_graph()
    logs = list(
        db.scalars(
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id, ActivityLog.event_type.in_(ADAPTATION_EVENTS))
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        ).all()
    )
    analyses = {
        a.id: a
        for a in db.scalars(
            select(FailureAnalysis).where(FailureAnalysis.user_id == user_id)
        ).all()
    }

    events: list[dict[str, Any]] = []
    for log in logs:
        meta = log.meta or {}
        before, after = _confidence_pair(meta)
        analysis = analyses.get(meta.get("failure_analysis_id")) if meta.get("failure_analysis_id") else None
        skill_id = meta.get("skill_id") or (analysis.skill_id if analysis else None)

        inserted: list[dict[str, str]] = []
        recommendation: Optional[dict[str, Any]] = None
        unlocked_tickets: list[dict[str, Any]] = []
        trigger = log.detail or log.title

        if analysis is not None:
            # A diagnosed gap physically inserts a remediation step ahead of the
            # work the learner was doing.
            module = (
                PRACTICE_MODULE_INDEX.get(analysis.remediation_module_id)
                if analysis.remediation_module_id
                else None
            )
            if module:
                inserted.append(
                    {
                        "skill_id": module["skill_id"],
                        "skill_name": graph.name_of(module["skill_id"]),
                        "module_id": module["id"],
                        "module_title": module["title"],
                    }
                )
                recommendation = {
                    "type": "remediation_practice",
                    "module_id": module["id"],
                    "title": module["title"],
                }
            trigger = (
                f"{analysis.source_type} failed on {graph.name_of(analysis.skill_id)}: "
                f"{analysis.root_cause}"
            )

        if log.event_type == "ticket_completed":
            unlocked_tickets = list(meta.get("unlocked") or [])

        events.append(
            {
                "id": log.id,
                "at": log.created_at,
                "event_type": log.event_type,
                "title": log.title,
                "trigger": trigger,
                "skill_id": skill_id,
                "skill_name": graph.name_of(skill_id) if skill_id else None,
                "confidence_before": before,
                "confidence_after": after,
                "confidence_delta": (
                    round(after - before, 1) if before is not None and after is not None else None
                ),
                "confidence_recorded": before is not None or after is not None,
                "inserted_skills": inserted,
                "recommendation": recommendation,
                "unlocked_tickets": unlocked_tickets,
                "resolved_gaps": meta.get("resolved_gaps"),
                "weak_concepts": meta.get("weak_concepts") or [],
                "failure": (
                    {
                        "id": analysis.id,
                        "root_cause": analysis.root_cause,
                        "missing_concepts": list(analysis.missing_concepts or []),
                        "explanation": analysis.explanation,
                        # `resolved` has no timestamp column, so a resolution
                        # cannot be dated. Only the current flag is reported.
                        "resolved": analysis.resolved,
                        "resolved_at": None,
                    }
                    if analysis
                    else None
                ),
                "source": {
                    "type": (
                        "ticket"
                        if meta.get("ticket_id")
                        else "practice"
                        if meta.get("module_id")
                        else "assessment"
                        if meta.get("session_id")
                        else "project"
                        if meta.get("project_id")
                        else "profile"
                    ),
                    "id": (
                        meta.get("ticket_id")
                        or meta.get("module_id")
                        or meta.get("session_id")
                        or meta.get("project_id")
                    ),
                },
            }
        )

    return {
        "events": events,
        "confidence_history_available_from": "recorded per event only where "
        "`confidence_recorded` is true; earlier events predate capture and are "
        "reported as null rather than estimated",
    }


# ---------------------------------------------------------------------------
#  Resources
# ---------------------------------------------------------------------------


def resources_for_skill(skill_id: str) -> dict[str, Any]:
    """Internal-first resources for one skill gap.

    Internal items are resolved live from what the product actually contains —
    the graph node's ``recommended_practice`` (validated against
    ``PRACTICE_MODULE_INDEX``), the adaptive assessment bank, and the course
    that teaches the skill — so a dead pointer is impossible. External items are
    the curated canonical docs in ``app.data.learning_resources``.
    """
    graph = get_knowledge_graph()
    node = graph.get(skill_id)
    if node is None:
        return {"skill_id": skill_id, "skill_name": None, "resources": [], "known_skill": False}

    resources: list[dict[str, Any]] = []

    # "Learn only what you need": a handful of entry points, not a catalog dump.
    # `dsa_arrays` alone recommends five language variants of the same problem.
    MAX_PRACTICE = 3
    for module_id in node.recommended_practice[:MAX_PRACTICE]:
        module = PRACTICE_MODULE_INDEX.get(module_id)
        if not module:
            continue
        resources.append(
            {
                "kind": "challenge" if module["kind"] == "challenge" else "interactive_practice",
                "title": module["title"],
                "minutes": module.get("estimated_minutes", 20),
                "target": "practice_module",
                "module_id": module["id"],
                "url": None,
                "internal": True,
            }
        )

    item_count = len(ITEMS_BY_SKILL.get(skill_id, []))
    if item_count:
        resources.append(
            {
                "kind": "assessment",
                "title": f"Adaptive check: {node.name}",
                # ~1.5 min per adaptive item, and a session asks at most 5.
                "minutes": max(3, min(item_count, 5) * 2),
                "target": "assessment",
                "skill_id": skill_id,
                "item_count": item_count,
                "url": None,
                "internal": True,
            }
        )

    course = _course_ref(skill_id)
    if course:
        resources.append(
            {
                "kind": "course_lesson",
                "title": f"Course covering {node.name}",
                "minutes": None,
                "target": "course",
                "path_id": course["path_id"],
                "course_id": course["course_id"],
                "url": None,
                "internal": True,
            }
        )

    for external in EXTERNAL_RESOURCES.get(skill_id, []):
        resources.append({**external, "target": "external", "internal": False})

    return {
        "skill_id": skill_id,
        "skill_name": node.name,
        "known_skill": True,
        "related_concepts": list(node.related_concepts),
        "resources": resources,
    }
