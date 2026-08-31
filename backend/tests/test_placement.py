"""Structural tests for the placement layer.

Placement is what the product promises instead of a self-rating, so the things
worth locking down are: every available path can actually be probed, a probe is
never asked from an empty bank, and the starting point it produces is the first
course the learner did not prove.
"""

from __future__ import annotations

import pytest

from app.data.assessment_bank import ITEMS_BY_SKILL
from app.data.paths import PATHS, PATH_INDEX
from app.services import placement_service as ps
from app.services.knowledge_graph import get_knowledge_graph

AVAILABLE_PATHS = [p["id"] for p in PATHS if p["available"]]


def test_there_is_at_least_one_available_path():
    assert AVAILABLE_PATHS, "placement is unreachable if no path is available"


@pytest.mark.parametrize("path_id", AVAILABLE_PATHS)
def test_available_path_has_a_probe_plan(path_id):
    plan = ps.probe_plan(path_id)
    assert plan, f"{path_id} is available but cannot be probed"


@pytest.mark.parametrize("path_id", AVAILABLE_PATHS)
def test_probe_plan_is_one_probe_per_probeable_course(path_id):
    path = PATH_INDEX[path_id]
    plan = ps.probe_plan(path_id)

    probed_courses = [p["course_id"] for p in plan]
    assert len(probed_courses) == len(set(probed_courses)), "a course was probed twice"

    skills = [p["skill_id"] for p in plan]
    assert len(skills) == len(set(skills)), "two courses share a probe skill"

    # Course order drives the starting point, so the plan must preserve it.
    course_order = [c["id"] for c in path["courses"]]
    assert probed_courses == [c for c in course_order if c in set(probed_courses)]


@pytest.mark.parametrize("path_id", AVAILABLE_PATHS)
def test_every_probe_has_enough_items_to_ask(path_id):
    for probe in ps.probe_plan(path_id):
        items = ITEMS_BY_SKILL.get(probe["skill_id"], [])
        assert len(items) >= ps.MIN_ITEMS_FOR_PROBE, probe["skill_id"]
        # Asking for more questions than exist would silently end the session
        # early and be scored as if the learner had answered them.
        assert 1 <= probe["questions"] <= len(items)


@pytest.mark.parametrize("path_id", AVAILABLE_PATHS)
def test_probe_targets_the_hardest_assessable_skill_of_its_course(path_id):
    """Passing a probe must mean the whole course can be skipped."""
    graph = get_knowledge_graph()
    path = PATH_INDEX[path_id]
    plans = {p["course_id"]: p["skill_id"] for p in ps.probe_plan(path_id)}

    for course in path["courses"]:
        chosen = plans.get(course["id"])
        if chosen is None:
            continue
        assessable = [
            s for s in course["skills"] if len(ITEMS_BY_SKILL.get(s, [])) >= ps.MIN_ITEMS_FOR_PROBE
        ]
        hardest = max(graph.get(s).difficulty_weight for s in assessable)
        assert graph.get(chosen).difficulty_weight == hardest


def test_paths_without_curriculum_cannot_be_probed():
    for path in PATHS:
        if path["available"]:
            continue
        assert ps.probe_plan(path["id"]) == [], path["id"]


def test_unknown_path_is_not_probeable():
    assert ps.probe_plan("does-not-exist") == []


# --------------------------------------------------------------------------- #
#  Starting point                                                             #
# --------------------------------------------------------------------------- #


def _rows(path_id: str, passed_course_ids: set[str]) -> list[dict]:
    return [
        {**probe, "passed": probe["course_id"] in passed_course_ids}
        for probe in ps.probe_plan(path_id)
    ]


def test_starting_point_is_the_first_unpassed_course():
    path_id = AVAILABLE_PATHS[0]
    courses = [c["id"] for c in PATH_INDEX[path_id]["courses"]]

    nothing_passed = ps._starting_point(path_id, _rows(path_id, set()))
    assert nothing_passed is not None
    assert nothing_passed["course_id"] == courses[0]

    first_passed = ps._starting_point(path_id, _rows(path_id, {courses[0]}))
    assert first_passed is not None
    assert first_passed["course_id"] == courses[1]


def test_starting_point_is_none_when_every_course_is_passed():
    path_id = AVAILABLE_PATHS[0]
    all_courses = {c["id"] for c in PATH_INDEX[path_id]["courses"]}
    assert ps._starting_point(path_id, _rows(path_id, all_courses)) is None


def test_starting_point_names_a_real_first_skill():
    path_id = AVAILABLE_PATHS[0]
    graph = get_knowledge_graph()
    start = ps._starting_point(path_id, _rows(path_id, set()))
    assert start is not None
    assert graph.get(start["first_skill_id"]) is not None
    assert start["first_skill_name"]


# --------------------------------------------------------------------------- #
#  Level banding                                                              #
# --------------------------------------------------------------------------- #


def test_no_evidence_never_reads_as_experienced():
    assert ps._level_for(0.0, 0) == "no_experience"


def test_level_never_decreases_as_accuracy_rises():
    order = ["no_experience", "early_basics", "intermediate", "advanced"]
    for passed in (0, 1, 3):
        ranks = [order.index(ps._level_for(a, passed)) for a in (0, 30, 55, 80, 100)]
        assert ranks == sorted(ranks), (passed, ranks)


def test_clearing_probes_is_required_for_the_top_band():
    """High accuracy on nothing verified must not read as advanced."""
    assert ps._level_for(100.0, 0) != "advanced"
    assert ps._level_for(100.0, 3) == "advanced"
