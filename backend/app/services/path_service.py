"""Composes career paths, courses and their progress for a given learner.

Everything here is derived, never stored: a course's skill order comes from the
knowledge graph, its practice modules are matched by ``skill_id``, its test
availability is read off the live assessment bank, and its progress is computed
from the learner's verified skills. That means authoring a new problem or
question changes what a course offers without a migration or a data edit.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.assessment_bank import ITEMS_BY_SKILL
from app.data.curriculum import hidden_case_count
from app.data.paths import PATH_INDEX, PATHS, find_course
from app.data.practice_modules import PRACTICE_MODULES
from app.models import LearningDigitalTwin, Project, VerifiedSkill
from app.services import reward_service
from app.services.knowledge_graph import get_knowledge_graph

# A course test needs enough items to adapt across difficulty; below this the
# result would be noise, so the course reports its test as unavailable instead
# of handing the learner a two-question "exam".
MIN_ITEMS_FOR_COURSE_TEST = 3


def _confidence_map(db: Session, twin: LearningDigitalTwin) -> dict[str, float]:
    rows = db.execute(
        select(VerifiedSkill.skill_id, VerifiedSkill.confidence).where(
            VerifiedSkill.twin_id == twin.id
        )
    ).all()
    return {skill_id: confidence for skill_id, confidence in rows}


def learner_confidence(db: Session, twin: LearningDigitalTwin) -> dict[str, float]:
    """Public accessor so other services grade against the identical numbers."""
    return _confidence_map(db, twin)


def _ordered_skills(skills: list[str]) -> list[str]:
    """Dependency-correct order, restricted to the course's own skills.

    The graph's learning_path pulls in transitive prerequisites from other
    courses too; those belong to the earlier course, so they are filtered out
    here while still fixing the relative order of what remains.
    """
    graph = get_knowledge_graph()
    ordered: list[str] = []
    for skill_id in skills:
        for step in graph.learning_path(skill_id):
            if step in skills and step not in ordered:
                ordered.append(step)
    # Anything the graph does not know about still deserves to be listed.
    ordered.extend(s for s in skills if s not in ordered)
    return ordered


def ordered_skills(skills: list[str]) -> list[str]:
    """Public alias for the dependency-correct ordering used by courses."""
    return _ordered_skills(skills)


def _modules_for_skills(skills: set[str]) -> list[dict[str, Any]]:
    graph = get_knowledge_graph()
    modules = [m for m in PRACTICE_MODULES if m["skill_id"] in skills]
    modules.sort(key=lambda m: (m["difficulty"], m["title"]))
    return [
        {
            "id": m["id"],
            "title": m["title"],
            "kind": m["kind"],
            "technology": m["technology"],
            "skill_id": m["skill_id"],
            "skill_name": graph.name_of(m["skill_id"]),
            "difficulty": m["difficulty"],
            "estimated_minutes": m.get("estimated_minutes", 20),
            "hidden_test_count": hidden_case_count(m),
            "xp_reward": reward_service.xp_for_difficulty(m["difficulty"]),
        }
        for m in modules
    ]


def _test_plan(skills: list[str]) -> dict[str, Any]:
    """Which of a course's skills can actually be assessed, and how.

    The bank is uneven — some skills have no items at all — so this reports the
    truth per skill rather than letting the learner start a test that cannot be
    graded.
    """
    stages = []
    for skill_id in skills:
        item_count = len(ITEMS_BY_SKILL.get(skill_id, []))
        stages.append(
            {
                "skill_id": skill_id,
                "skill_name": get_knowledge_graph().name_of(skill_id),
                "item_count": item_count,
                "available": item_count > 0,
            }
        )
    total_items = sum(s["item_count"] for s in stages)
    available = [s for s in stages if s["available"]]
    return {
        "stages": stages,
        "total_items": total_items,
        # Sequential model: one adaptive assessment per assessable skill, then
        # the course percentage is the mean of the stage scores.
        "mode": "sequential_per_skill",
        "available": total_items >= MIN_ITEMS_FOR_COURSE_TEST and bool(available),
        "unavailable_reason": (
            None
            if total_items >= MIN_ITEMS_FOR_COURSE_TEST and available
            else "Not enough assessment items are authored for this course yet."
        ),
        "pass_mark": get_knowledge_graph().confidence_threshold,
    }


def lesson_state(
    skill_id: str, confidence: dict[str, float], evidence: Optional[set[str]] = None
) -> dict[str, Any]:
    """The canonical per-skill state used by every learner-facing surface.

    Extracted from ``course_detail`` so the course pages and the personalised
    learning path answer "is this verified / unlocked?" with the *same*
    predicate. ``evidence`` defaults to every skill the twin has a row for,
    which keeps the gate consistent with the rest of the product: a prerequisite
    with no evidence is unknown rather than weak, so it never blocks a first
    attempt.
    """
    graph = get_knowledge_graph()
    known = set(confidence) if evidence is None else evidence
    score = confidence.get(skill_id, 0.0)
    unlocked, gaps = graph.is_unlocked(skill_id, confidence, evidence=known)
    return {
        "skill_id": skill_id,
        "skill_name": graph.name_of(skill_id),
        "confidence": round(score, 1),
        "verified": score >= graph.confidence_threshold,
        "unlocked": unlocked,
        "missing_prerequisites": gaps,
        "item_count": len(ITEMS_BY_SKILL.get(skill_id, [])),
    }


def _course_progress(skills: list[str], confidence: dict[str, float]) -> dict[str, Any]:
    threshold = get_knowledge_graph().confidence_threshold
    scores = [confidence.get(skill_id, 0.0) for skill_id in skills]
    verified = sum(1 for score in scores if score >= threshold)
    return {
        "skills_total": len(skills),
        "skills_verified": verified,
        "percent": round(sum(scores) / len(scores), 1) if scores else 0.0,
        "complete": bool(skills) and verified == len(skills),
    }


def _course_summary(
    path_id: str,
    course: dict[str, Any],
    confidence: dict[str, float],
    projects_by_title: dict[str, str],
) -> dict[str, Any]:
    skills = _ordered_skills(course["skills"])
    modules = _modules_for_skills(set(skills))
    test = _test_plan(skills)
    project = course.get("project")
    return {
        "id": course["id"],
        "path_id": path_id,
        "title": course["title"],
        "blurb": course["blurb"],
        "skill_count": len(skills),
        "module_count": len(modules),
        "practice_count": len(modules),
        "test_available": test["available"],
        "test_item_count": test["total_items"],
        "has_project": project is not None,
        "project_started_id": (
            projects_by_title.get(project["title"].lower()) if project else None
        ),
        "estimated_minutes": sum(m["estimated_minutes"] for m in modules),
        "progress": _course_progress(skills, confidence),
    }


def _projects_by_title(db: Session, twin: LearningDigitalTwin) -> dict[str, str]:
    """Lets a course show 'continue' instead of 'start' for its capstone."""
    rows = db.execute(
        select(Project.title, Project.id).where(Project.user_id == twin.user_id)
    ).all()
    return {title.lower(): project_id for title, project_id in rows}


def list_paths(db: Session, twin: LearningDigitalTwin) -> dict[str, Any]:
    confidence = _confidence_map(db, twin)
    projects = _projects_by_title(db, twin)

    paths = []
    for path in PATHS:
        courses = [
            _course_summary(path["id"], course, confidence, projects)
            for course in path["courses"]
        ]
        completed = sum(1 for c in courses if c["progress"]["complete"])
        percent = (
            round(sum(c["progress"]["percent"] for c in courses) / len(courses), 1)
            if courses
            else 0.0
        )
        paths.append(
            {
                "id": path["id"],
                "label": path["label"],
                "tagline": path["tagline"],
                "blurb": path["blurb"],
                "roles": path["roles"],
                "available": path["available"],
                "course_count": len(courses),
                "planned_courses": path.get("planned_courses", []),
                "progress": {
                    "courses_total": len(courses),
                    "courses_completed": completed,
                    "percent": percent,
                },
            }
        )
    return {"paths": paths}


def path_detail(
    db: Session, twin: LearningDigitalTwin, path_id: str
) -> Optional[dict[str, Any]]:
    path = PATH_INDEX.get(path_id)
    if not path:
        return None

    confidence = _confidence_map(db, twin)
    projects = _projects_by_title(db, twin)
    courses = [
        _course_summary(path_id, course, confidence, projects)
        for course in path["courses"]
    ]

    # The next course is the first incomplete one, so the path always has a
    # single obvious entry point rather than a wall of equal-looking cards.
    next_course = next((c["id"] for c in courses if not c["progress"]["complete"]), None)

    return {
        "id": path["id"],
        "label": path["label"],
        "tagline": path["tagline"],
        "blurb": path["blurb"],
        "roles": path["roles"],
        "available": path["available"],
        "planned_courses": path.get("planned_courses", []),
        "courses": courses,
        "next_course_id": next_course,
        "progress": {
            "courses_total": len(courses),
            "courses_completed": sum(1 for c in courses if c["progress"]["complete"]),
            "percent": (
                round(sum(c["progress"]["percent"] for c in courses) / len(courses), 1)
                if courses
                else 0.0
            ),
        },
    }


def course_detail(
    db: Session, twin: LearningDigitalTwin, path_id: str, course_id: str
) -> Optional[dict[str, Any]]:
    path = PATH_INDEX.get(path_id)
    course = find_course(path_id, course_id)
    if not path or not course:
        return None

    graph = get_knowledge_graph()
    confidence = _confidence_map(db, twin)
    projects = _projects_by_title(db, twin)
    threshold = graph.confidence_threshold

    skills = _ordered_skills(course["skills"])
    lessons = [
        {"order": index, **lesson_state(skill_id, confidence)}
        for index, skill_id in enumerate(skills, start=1)
    ]

    modules = _modules_for_skills(set(skills))
    project = course.get("project")

    return {
        "id": course["id"],
        "path_id": path_id,
        "path_label": path["label"],
        "title": course["title"],
        "blurb": course["blurb"],
        "lessons": lessons,
        "modules": modules,
        "test": _test_plan(skills),
        "project": (
            {
                **project,
                "existing_project_id": projects.get(project["title"].lower()),
            }
            if project
            else None
        ),
        "progress": _course_progress(skills, confidence),
        "pass_mark": threshold,
    }
