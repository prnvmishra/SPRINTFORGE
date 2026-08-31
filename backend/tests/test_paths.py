"""Structural guarantees for the career path layer.

The registry is hand-authored data that the UI renders directly, so the failure
mode is a course that looks real but has nothing behind it. These tests assert
that a path advertised as available actually has teachable, testable content.
"""

from __future__ import annotations

import pytest

from app.data.assessment_bank import ITEMS_BY_SKILL
from app.data.paths import COURSE_INDEX, PATH_INDEX, PATHS, find_course
from app.services.knowledge_graph import get_knowledge_graph
from app.services.path_service import (
    MIN_ITEMS_FOR_COURSE_TEST,
    _modules_for_skills,
    _ordered_skills,
    _test_plan,
)

AVAILABLE_PATHS = [p for p in PATHS if p["available"]]
ALL_COURSES = [(p["id"], c) for p in PATHS for c in p["courses"]]


def test_path_ids_are_unique():
    ids = [p["id"] for p in PATHS]
    assert len(ids) == len(set(ids))


def test_at_least_one_path_is_available():
    assert AVAILABLE_PATHS, "no path has curriculum behind it"


@pytest.mark.parametrize("path", PATHS, ids=lambda p: p["id"])
def test_unavailable_paths_declare_no_courses(path):
    """An unavailable path must not ship half a curriculum."""
    if not path["available"]:
        assert path["courses"] == []
        assert path["planned_courses"], "a planned path should say what is planned"


@pytest.mark.parametrize("path", AVAILABLE_PATHS, ids=lambda p: p["id"])
def test_available_paths_have_courses(path):
    assert path["courses"], f"{path['id']} is available but has no courses"


@pytest.mark.parametrize("path_id,course", ALL_COURSES, ids=lambda v: getattr(v, "get", lambda _: v)("id") if isinstance(v, dict) else str(v))
def test_courses_reference_real_skills(path_id, course):
    graph = get_knowledge_graph()
    assert course["skills"], f"{course['id']} teaches nothing"
    for skill_id in course["skills"]:
        assert graph.get(skill_id), f"{course['id']} references unknown skill {skill_id}"


def test_course_ids_are_unique_within_a_path():
    assert len(COURSE_INDEX) == len(ALL_COURSES)


def test_every_course_is_testable():
    """A course with no assessable skills cannot verify anything it teaches."""
    untestable = []
    for path_id, course in ALL_COURSES:
        plan = _test_plan(_ordered_skills(course["skills"]))
        if not plan["available"]:
            untestable.append(f"{path_id}/{course['id']} ({plan['total_items']} items)")
    assert not untestable, "courses without a usable test: " + ", ".join(untestable)


def test_every_skill_in_an_available_path_has_questions():
    missing = [
        skill_id
        for path in AVAILABLE_PATHS
        for course in path["courses"]
        for skill_id in course["skills"]
        if len(ITEMS_BY_SKILL.get(skill_id, [])) == 0
    ]
    assert not missing, f"skills with no assessment items: {sorted(set(missing))}"


def test_ordered_skills_respects_prerequisites():
    """A skill must never be listed before a prerequisite in the same course."""
    graph = get_knowledge_graph()
    for _, course in ALL_COURSES:
        ordered = _ordered_skills(course["skills"])
        seen: set[str] = set()
        for skill_id in ordered:
            for prereq in graph.ancestors(skill_id):
                if prereq in course["skills"]:
                    assert prereq in seen, (
                        f"{course['id']}: {skill_id} listed before its prerequisite {prereq}"
                    )
            seen.add(skill_id)


def test_ordered_skills_is_a_permutation():
    """Ordering must not drop or duplicate a course's skills."""
    for _, course in ALL_COURSES:
        ordered = _ordered_skills(course["skills"])
        assert sorted(ordered) == sorted(course["skills"])


def test_course_projects_use_recognised_stack_entries():
    """A capstone whose stack maps to nothing would generate an empty project."""
    graph = get_knowledge_graph()
    for _, course in ALL_COURSES:
        project = course.get("project")
        if not project:
            continue
        assert project["tech_stack"], f"{course['id']} capstone has no stack"
        skills = graph.skills_for_stack(project["tech_stack"])
        assert skills, (
            f"{course['id']} capstone stack {project['tech_stack']} maps to no skills"
        )


def test_course_projects_have_distinct_titles():
    """Course capstones are matched to existing projects by title, so collisions
    would make one course show another's project as already started."""
    titles = [
        course["project"]["title"].lower()
        for _, course in ALL_COURSES
        if course.get("project")
    ]
    assert len(titles) == len(set(titles))


def test_find_course_is_scoped_to_its_path():
    """A course id must not resolve under a path that does not own it."""
    sde = PATH_INDEX["sde"]
    course_id = sde["courses"][0]["id"]
    assert find_course("sde", course_id) is not None
    assert find_course("data-analyst", course_id) is None


def test_min_items_threshold_is_enforced():
    plan = _test_plan(["react_dashboard"])
    assert plan["total_items"] >= MIN_ITEMS_FOR_COURSE_TEST
    assert plan["available"]

    empty = _test_plan(["definitely_not_a_skill"])
    assert empty["total_items"] == 0
    assert not empty["available"]
    assert empty["unavailable_reason"]


def test_modules_are_matched_by_skill():
    """Practice modules are discovered, not hardcoded, so a course picks up new
    problems automatically."""
    dsa = find_course("sde", "dsa-problem-solving")
    modules = _modules_for_skills(set(dsa["skills"]))
    assert modules, "the DSA course should pick up the judged CP problems"
    assert all(m["skill_id"] in dsa["skills"] for m in modules)
