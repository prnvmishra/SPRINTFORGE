"""Locks the `/paths` response shape.

The lesson-status logic was extracted from `path_service.course_detail` into the
shared `lesson_state` helper so the personalised learning path grades against
the identical predicate. The frontend reads these payloads directly, so the keys
(and their order, which is what a snapshot of a dict preserves) must be exactly
what they were before that extraction.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import LearningDigitalTwin, User
from app.services import digital_twin_service as twin_service
from app.services import path_service

PATH_KEYS = ["id", "label", "tagline", "blurb", "roles", "available", "course_count", "planned_courses", "progress"]
COURSE_SUMMARY_KEYS = [
    "id",
    "path_id",
    "title",
    "blurb",
    "skill_count",
    "module_count",
    "practice_count",
    "test_available",
    "test_item_count",
    "has_project",
    "project_started_id",
    "estimated_minutes",
    "progress",
]
PATH_DETAIL_KEYS = [
    "id",
    "label",
    "tagline",
    "blurb",
    "roles",
    "available",
    "planned_courses",
    "courses",
    "next_course_id",
    "progress",
]
COURSE_DETAIL_KEYS = [
    "id",
    "path_id",
    "path_label",
    "title",
    "blurb",
    "lessons",
    "modules",
    "test",
    "project",
    "progress",
    "pass_mark",
]
LESSON_KEYS = [
    "order",
    "skill_id",
    "skill_name",
    "confidence",
    "verified",
    "unlocked",
    "missing_prerequisites",
    "item_count",
]


def _session_with_learner():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    user = User(email="paths-contract@example.com", name="Contract", hashed_password="x")
    db.add(user)
    db.flush()
    twin = LearningDigitalTwin(user_id=user.id)
    db.add(twin)
    db.flush()
    twin_service.record_execution_outcome(db, twin, "html_basics", True, 1)
    twin_service.record_execution_outcome(db, twin, "css_basics", False, 2, ["box model"])
    db.flush()
    return db, twin


def test_list_paths_shape_unchanged():
    db, twin = _session_with_learner()
    payload = path_service.list_paths(db, twin)
    assert list(payload) == ["paths"]
    for path in payload["paths"]:
        assert list(path) == PATH_KEYS
        assert list(path["progress"]) == ["courses_total", "courses_completed", "percent"]


def test_path_detail_shape_unchanged():
    db, twin = _session_with_learner()
    detail = path_service.path_detail(db, twin, "sde")
    assert list(detail) == PATH_DETAIL_KEYS
    for course in detail["courses"]:
        assert list(course) == COURSE_SUMMARY_KEYS
        assert list(course["progress"]) == [
            "skills_total",
            "skills_verified",
            "percent",
            "complete",
        ]


def test_course_detail_shape_unchanged():
    db, twin = _session_with_learner()
    detail = path_service.course_detail(db, twin, "sde", "web-foundations")
    assert list(detail) == COURSE_DETAIL_KEYS
    assert detail["lessons"]
    for lesson in detail["lessons"]:
        assert list(lesson) == LESSON_KEYS
    assert [lesson["order"] for lesson in detail["lessons"]] == list(
        range(1, len(detail["lessons"]) + 1)
    )


def test_course_detail_lessons_match_shared_lesson_state():
    db, twin = _session_with_learner()
    confidence = path_service.learner_confidence(db, twin)
    detail = path_service.course_detail(db, twin, "sde", "web-foundations")
    for lesson in detail["lessons"]:
        shared = path_service.lesson_state(lesson["skill_id"], confidence)
        assert {"order": lesson["order"], **shared} == lesson


def test_unknown_path_and_course_still_return_none():
    db, twin = _session_with_learner()
    assert path_service.path_detail(db, twin, "nope") is None
    assert path_service.course_detail(db, twin, "sde", "nope") is None
