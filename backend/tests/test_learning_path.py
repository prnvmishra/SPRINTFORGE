"""Tests for the personalised learning path, adaptations and resources.

All state is seeded into in-memory SQLite (never the shared database), the same
way `scripts/verify_strict_validation.py` does.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.data.learning_resources import EXTERNAL_RESOURCES
from app.data.paths import PATHS, course_ids_for_skill
from app.data.practice_modules import PRACTICE_MODULE_INDEX
from app.models import (
    ActivityLog,
    FailureAnalysis,
    LearningDigitalTwin,
    Project,
    Sprint,
    Ticket,
    User,
)
from app.services import learning_path_service as lps
from app.services import path_service
from app.services.knowledge_graph import get_knowledge_graph

ALLOWED_KINDS = {
    "concept_guide",
    "interactive_practice",
    "documentation",
    "challenge",
    "assessment",
    "course_lesson",
}


def build_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed_learner(db, *, with_project=True, with_failure=False):
    user = User(email="path-test@example.com", name="Path Test", hashed_password="x")
    db.add(user)
    db.flush()
    twin = LearningDigitalTwin(
        user_id=user.id,
        goal="Become a job-ready frontend engineer",
        experience_level="beginner",
        claimed_skills={"html_basics": "beginner", "css_basics": "beginner"},
    )
    db.add(twin)
    db.flush()

    # Real evidence, produced through the same service the app uses.
    from app.services import digital_twin_service as twin_service

    twin_service.record_execution_outcome(db, twin, "html_basics", True, 1)
    twin_service.record_execution_outcome(db, twin, "html_basics", True, 1)
    twin_service.record_execution_outcome(db, twin, "css_basics", False, 2, ["box model"])

    project = None
    if with_project:
        project = Project(
            user_id=user.id,
            title="Movie App",
            idea="movies",
            tech_stack=["HTML", "CSS", "JavaScript"],
        )
        db.add(project)
        db.flush()
        sprint = Sprint(
            project_id=project.id, name="Structure", milestone="Foundation", order_index=1
        )
        db.add(sprint)
        db.flush()
        db.add(
            Ticket(
                sprint_id=sprint.id,
                key="MOV-1",
                title="Base markup",
                description="d",
                target_skill_id="html_basics",
                difficulty=1,
                status="done",
                order_index=1,
            )
        )
        db.add(
            Ticket(
                sprint_id=sprint.id,
                key="MOV-2",
                title="Styling",
                description="d",
                target_skill_id="css_basics",
                difficulty=2,
                status="in_progress",
                order_index=2,
            )
        )
        twin.active_project_id = project.id
        db.flush()

    if with_failure:
        analysis = FailureAnalysis(
            user_id=user.id,
            source_type="ticket",
            source_id="MOV-2",
            skill_id="css_basics",
            root_cause="box model misunderstood",
            missing_concepts=["box model"],
            explanation="Root cause: box model misunderstood",
            remediation_module_id="css-profile-card",
            remediation_title="Interactive Profile Card — CSS Layer",
        )
        db.add(analysis)
        db.flush()
        db.add(
            ActivityLog(
                user_id=user.id,
                event_type="ticket_failed",
                title="MOV-2 needs rework",
                detail="box model misunderstood",
                meta={
                    "ticket_id": "MOV-2",
                    "failure_analysis_id": analysis.id,
                    "skill_id": "css_basics",
                    "confidence_before": 40.0,
                    "confidence_after": 31.5,
                },
            )
        )
        db.add(
            ActivityLog(
                user_id=user.id,
                event_type="ticket_completed",
                title="Completed MOV-1",
                detail="+30 XP · unlocked 1 ticket(s)",
                meta={
                    "ticket_id": "MOV-1",
                    "unlocked": [{"ticket_id": "t2", "key": "MOV-2", "title": "Styling"}],
                    "skill_id": "html_basics",
                },
            )
        )
        db.flush()

    db.flush()
    return user, twin


# --------------------------------------------------------------------- path


def test_path_is_ordered_by_prerequisites():
    db = build_session()
    _, twin = seed_learner(db)
    payload = lps.learning_path(db, twin)
    graph = get_knowledge_graph()
    seen: set[str] = set()
    spine = {s["skill_id"] for s in payload["path"]}
    for step in payload["path"]:
        for prereq in graph.ancestors(step["skill_id"]):
            if prereq in spine:
                assert prereq in seen, f"{step['skill_id']} listed before {prereq}"
        seen.add(step["skill_id"])


def test_exactly_one_step_is_next():
    db = build_session()
    _, twin = seed_learner(db)
    payload = lps.learning_path(db, twin)
    assert sum(1 for s in payload["path"] if s["is_next"]) == 1


def test_is_next_matches_routing_engine_when_on_spine():
    from app.services import graph_router

    db = build_session()
    _, twin = seed_learner(db)
    payload = lps.learning_path(db, twin)
    recommended = graph_router.recommend_next(db, twin).get("skill_id")
    marked = next(s for s in payload["path"] if s["is_next"])
    spine = {s["skill_id"] for s in payload["path"]}
    if recommended in spine:
        assert marked["skill_id"] == recommended
    else:
        assert marked["unlocked"] and not marked["verified"]


def test_state_vocabulary_rules():
    db = build_session()
    _, twin = seed_learner(db)
    payload = lps.learning_path(db, twin)
    threshold = payload["confidence_threshold"]
    for step in payload["path"]:
        assert step["state"] in lps.STATES
        if step["verified"]:
            assert step["state"] == "verified"
            assert step["confidence"] >= threshold
        elif not step["unlocked"]:
            assert step["state"] == "locked"
            assert step["missing_prerequisites"]
        elif not step["has_evidence"]:
            assert step["state"] == "not_started"
        else:
            assert step["state"] in {"needs_work", "in_progress"}


def test_state_agrees_with_paths_lesson_state():
    """The two surfaces must never disagree about verified/locked."""
    db = build_session()
    _, twin = seed_learner(db)
    payload = lps.learning_path(db, twin)
    confidence = path_service.learner_confidence(db, twin)
    for step in payload["path"]:
        lesson = path_service.lesson_state(step["skill_id"], confidence)
        assert lesson["verified"] == step["verified"]
        assert lesson["unlocked"] == step["unlocked"]
        assert lesson["confidence"] == step["confidence"]


def test_next_action_is_reused_verbatim_from_routing_engine():
    from app.services import graph_router

    db = build_session()
    _, twin = seed_learner(db)
    payload = lps.learning_path(db, twin)
    recommendation = graph_router.recommend_next(db, twin)
    assert payload["next_action"]["reason"] == recommendation["reason"]
    assert payload["next_action"]["type"] == recommendation["type"]
    assert payload["next_action"]["reason_source"] == "deterministic_routing_engine"


def test_goal_links_into_existing_catalog():
    db = build_session()
    _, twin = seed_learner(db)
    goal = lps.learning_path(db, twin)["goal"]
    assert goal["path_id"] in {p["id"] for p in PATHS if p["available"]}
    assert goal["target_source"] == "active_project_tech_stack"
    assert goal["target_stack"] == ["HTML", "CSS", "JavaScript"]


def test_taught_by_references_real_courses():
    db = build_session()
    _, twin = seed_learner(db)
    for step in lps.learning_path(db, twin)["path"]:
        ref = step["taught_by"]
        if ref is None:
            continue
        assert (ref["path_id"], ref["course_id"]) in {
            (p["id"], c["id"]) for p in PATHS for c in p["courses"]
        }


def test_learner_without_project_falls_back_to_claimed_skills():
    db = build_session()
    _, twin = seed_learner(db, with_project=False)
    payload = lps.learning_path(db, twin)
    assert payload["goal"]["target_source"] == "claimed_skills"
    assert payload["goal"]["target_stack"] == []
    assert payload["path"]


# --------------------------------------------------------------- milestones


def test_learning_milestones_group_by_course():
    db = build_session()
    _, twin = seed_learner(db)
    payload = lps.learning_path(db, twin)
    course_ids = {(p["id"], c["id"]) for p in PATHS for c in p["courses"]}
    assert payload["milestones"]
    for milestone in payload["milestones"]:
        assert milestone["kind"] == "learning"
        assert (milestone["path_id"], milestone["course_id"]) in course_ids
        assert milestone["completed_count"] <= milestone["total_count"]
        assert milestone["total_count"] == len(milestone["skills"])
        assert milestone["status"] in {"completed", "in_progress", "locked", "not_started"}


def test_execution_milestones_come_from_sprint_milestone():
    db = build_session()
    _, twin = seed_learner(db)
    payload = lps.learning_path(db, twin)
    assert [m["name"] for m in payload["execution_milestones"]] == ["Foundation"]
    milestone = payload["execution_milestones"][0]
    assert milestone["kind"] == "project_execution"
    assert milestone["total_count"] == 2
    assert milestone["completed_count"] == 1


def test_execution_milestones_empty_without_project():
    db = build_session()
    _, twin = seed_learner(db, with_project=False)
    assert lps.learning_path(db, twin)["execution_milestones"] == []


# ----------------------------------------------------------------- progress
#
# `percent` used to be the mean confidence across the route while both clients
# labelled it "% of the route verified", so a learner just under the threshold
# on every skill was told they had verified a chunk of a route with nothing
# verified on it. These pin the two numbers to their names.


def test_percent_counts_verified_skills_not_mean_confidence():
    db = build_session()
    _, twin = seed_learner(db)
    progress = lps.learning_path(db, twin)["progress"]
    expected = round(progress["skills_verified"] / progress["skills_total"] * 100, 1)
    assert progress["percent"] == expected


def test_percent_is_zero_while_nothing_is_verified():
    db = build_session()
    _, twin = seed_learner(db)
    progress = lps.learning_path(db, twin)["progress"]
    if progress["skills_verified"] == 0:
        assert progress["percent"] == 0.0
        # The seed has partial evidence, so the mean must not also be zero —
        # otherwise this test would pass against the old implementation too.
        assert progress["mean_confidence"] > 0


def test_mean_confidence_is_reported_separately():
    db = build_session()
    _, twin = seed_learner(db)
    payload = lps.learning_path(db, twin)
    steps = payload["path"]
    expected = round(sum(s["confidence"] for s in steps) / len(steps), 1)
    assert payload["progress"]["mean_confidence"] == expected


# -------------------------------------------------------------- adaptations


def test_adaptations_report_seeded_failure():
    db = build_session()
    user, _ = seed_learner(db, with_failure=True)
    events = lps.adaptations(db, user.id)["events"]
    assert events
    failure_event = next(e for e in events if e["event_type"] == "ticket_failed")
    assert failure_event["skill_id"] == "css_basics"
    assert "box model" in failure_event["trigger"]
    assert failure_event["failure"]["missing_concepts"] == ["box model"]
    assert failure_event["inserted_skills"][0]["module_id"] == "css-profile-card"
    assert failure_event["recommendation"]["module_id"] == "css-profile-card"
    assert failure_event["confidence_before"] == 40.0
    assert failure_event["confidence_delta"] == -8.5
    assert failure_event["confidence_recorded"] is True
    # No resolution timestamp exists in the schema.
    assert failure_event["failure"]["resolved_at"] is None


def test_adaptations_surface_unlocked_tickets():
    db = build_session()
    user, _ = seed_learner(db, with_failure=True)
    events = lps.adaptations(db, user.id)["events"]
    completed = next(e for e in events if e["event_type"] == "ticket_completed")
    assert completed["unlocked_tickets"][0]["key"] == "MOV-2"


def test_adaptations_never_invent_a_confidence_delta():
    db = build_session()
    user, _ = seed_learner(db, with_failure=True)
    for event in lps.adaptations(db, user.id)["events"]:
        if event["confidence_before"] is None or event["confidence_after"] is None:
            assert event["confidence_delta"] is None


def test_adaptations_are_reverse_chronological():
    db = build_session()
    user, _ = seed_learner(db, with_failure=True)
    stamps = [e["at"] for e in lps.adaptations(db, user.id)["events"]]
    assert stamps == sorted(stamps, reverse=True)


def test_adaptations_exclude_pure_activity_events():
    db = build_session()
    user, _ = seed_learner(db, with_failure=True)
    db.add(
        ActivityLog(
            user_id=user.id, event_type="ticket_started", title="Started MOV-2", meta={}
        )
    )
    db.flush()
    types = {e["event_type"] for e in lps.adaptations(db, user.id)["events"]}
    assert "ticket_started" not in types


# ---------------------------------------------------------------- resources


GRAPH_SKILL_IDS = [n.id for n in get_knowledge_graph().all_nodes()]


@pytest.mark.parametrize("skill_id", GRAPH_SKILL_IDS)
def test_every_graph_skill_has_a_small_honest_resource_set(skill_id):
    payload = lps.resources_for_skill(skill_id)
    assert payload["known_skill"]
    resources = payload["resources"]
    assert 2 <= len(resources) <= 8, f"{skill_id} has {len(resources)} resources"
    for resource in resources:
        assert resource["kind"] in ALLOWED_KINDS
        assert resource["title"]
        if resource["internal"]:
            assert resource["url"] is None
        else:
            assert resource["url"].startswith("https://")
            assert isinstance(resource["minutes"], int) and 0 < resource["minutes"] <= 60


@pytest.mark.parametrize("skill_id", GRAPH_SKILL_IDS)
def test_internal_resource_pointers_resolve(skill_id):
    for resource in lps.resources_for_skill(skill_id)["resources"]:
        if resource["target"] == "practice_module":
            assert resource["module_id"] in PRACTICE_MODULE_INDEX
        if resource["target"] == "course":
            assert (resource["path_id"], resource["course_id"]) in {
                (p["id"], c["id"]) for p in PATHS for c in p["courses"]
            }


def test_external_resources_only_cover_known_skills():
    assert set(EXTERNAL_RESOURCES) <= set(GRAPH_SKILL_IDS)


def test_unknown_skill_returns_no_resources():
    payload = lps.resources_for_skill("not_a_skill")
    assert payload["known_skill"] is False
    assert payload["resources"] == []


def test_next_action_resources_are_for_the_recommended_skill():
    db = build_session()
    _, twin = seed_learner(db)
    payload = lps.learning_path(db, twin)
    action = payload["next_action"]
    if action["skill_id"]:
        assert action["resources"] == lps.resources_for_skill(action["skill_id"])["resources"]
    else:
        assert action["resources"] == []


# ------------------------------------------------------------- graph hygiene


def test_unlocks_and_prerequisites_are_mutually_consistent():
    graph = get_knowledge_graph()
    problems = []
    for node in graph.all_nodes():
        for target_id in node.unlocks:
            target = graph.get(target_id)
            if target is None or node.id not in target.prerequisites:
                problems.append(f"{node.id} unlocks {target_id} but is not its prerequisite")
        for prereq_id in node.prerequisites:
            source = graph.get(prereq_id)
            if source is None or node.id not in source.unlocks:
                problems.append(f"{prereq_id} is a prerequisite of {node.id} but does not unlock it")
    assert not problems, "; ".join(problems)


def test_course_reverse_lookup_used_by_the_spine_is_stable():
    for skill_id in GRAPH_SKILL_IDS:
        for path_id, course_id in course_ids_for_skill(skill_id):
            assert path_id in {p["id"] for p in PATHS}
            assert course_id in {c["id"] for p in PATHS for c in p["courses"]}
