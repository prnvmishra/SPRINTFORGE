"""The Data Analyst path's enabling layer is complete and self-consistent.

The path is still `available: False` — its courses and its ~50 practice
questions are authored on top of this. What these tests lock is the layer
underneath, so an author cannot land content on a foundation that has quietly
rotted: every data skill is in the graph with agreeing edges, is assessable, has
a ticket template, and produces a coherent project board.
"""

from __future__ import annotations

import pytest

from app.data.assessment_bank import ITEMS_BY_SKILL
from app.data.paths import PATH_INDEX
from app.data.practice_modules import PRACTICE_MODULE_INDEX
from app.data.practice_sql import SQL_MODULES
from app.data.ticket_templates import SPRINT_THEMES, STARTER_FILES, TICKET_TEMPLATES
from app.services.knowledge_graph import get_knowledge_graph
from app.services.path_service import MIN_ITEMS_FOR_COURSE_TEST, _test_plan

#: The skill line the Data Analyst path is built on. Named explicitly rather
#: than derived from the track, so deleting a node is a test failure and not a
#: silently smaller loop.
DATA_SKILLS = [
    "sql_basics",
    "sql_joins",
    "sql_aggregation",
    "sql_analytics",
    "data_cleaning",
    "exploratory_analysis",
    "statistics_business",
    "data_visualization",
    "dashboard_design",
    "spreadsheet_modeling",
]

#: What the path advertises it will teach, and the skill that covers each.
STATED_SCOPE = {
    "SQL": ["sql_basics", "sql_joins", "sql_aggregation", "sql_analytics"],
    "spreadsheet modelling": ["spreadsheet_modeling"],
    "statistics for business questions": ["statistics_business"],
    "dashboards": ["data_visualization", "dashboard_design"],
}


@pytest.mark.parametrize("skill_id", DATA_SKILLS)
def test_every_data_skill_is_in_the_graph(skill_id):
    node = get_knowledge_graph().get(skill_id)
    assert node is not None, f"{skill_id} is referenced but not in skills_graph.json"
    assert node.track == "data"
    assert node.related_concepts, f"{skill_id} has no concepts for remediation routing"


def test_the_stated_scope_of_the_path_is_covered():
    graph = get_knowledge_graph()
    for area, skills in STATED_SCOPE.items():
        assert skills, area
        for skill_id in skills:
            assert graph.get(skill_id), f"{area} claims {skill_id}, which does not exist"


def test_existing_skills_are_reused_rather_than_duplicated():
    """`python_basics` is a real prerequisite for the pandas-flavoured work."""
    graph = get_knowledge_graph()
    assert "python_basics" in graph.get("data_cleaning").prerequisites
    assert "data_cleaning" in graph.get("python_basics").unlocks
    # No parallel Python node was invented for the data track.
    assert [n.id for n in graph.all_nodes() if n.name == "Python Basics"] == ["python_basics"]


def test_the_data_skill_line_is_reachable_and_acyclic():
    """Each data skill's prerequisites resolve, and none is its own ancestor.

    `scripts/verify_graph_consistency.py` asserts this for the whole graph; this
    keeps it true for the data line specifically, in the suite.
    """
    graph = get_knowledge_graph()
    for skill_id in DATA_SKILLS:
        ancestors = graph.ancestors(skill_id)
        assert skill_id not in ancestors
        for prereq in ancestors:
            assert graph.get(prereq), f"{skill_id} requires missing {prereq}"


def test_the_entry_points_need_no_prerequisites():
    """A learner with no history must be able to start somewhere on this path."""
    graph = get_knowledge_graph()
    entry = [s for s in DATA_SKILLS if not graph.get(s).prerequisites]
    assert "sql_basics" in entry
    assert "spreadsheet_modeling" in entry


# --------------------------------------------------------------------------- #
#  Assessable
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("skill_id", DATA_SKILLS)
def test_every_data_skill_has_assessment_items(skill_id):
    """A course whose skills have no items offers a test that cannot be graded."""
    items = ITEMS_BY_SKILL.get(skill_id, [])
    assert len(items) >= 3, f"{skill_id} has {len(items)} items; a course test needs more"


@pytest.mark.parametrize("skill_id", DATA_SKILLS)
def test_data_items_spread_across_difficulties(skill_id):
    """The adaptive engine needs somewhere to move in both directions."""
    difficulties = {i["difficulty"] for i in ITEMS_BY_SKILL[skill_id]}
    assert len(difficulties) >= 3, f"{skill_id} items sit at {sorted(difficulties)}"


@pytest.mark.parametrize("skill_id", DATA_SKILLS)
def test_data_items_are_well_formed(skill_id):
    for item in ITEMS_BY_SKILL[skill_id]:
        assert item["explanation"].strip(), item["id"]
        assert item["concept"], item["id"]
        if item["type"] == "mcq":
            assert len(item["options"]) >= 3, item["id"]
            assert 0 <= item["correct_option"] < len(item["options"]), item["id"]
        else:
            assert item["expected_answer"].strip(), item["id"]
            assert item["answer_checks"], f"{item['id']} has no deterministic signal"


def test_a_prospective_data_course_would_have_a_usable_test():
    """The four planned courses' skill groups each clear the test threshold."""
    for area, skills in STATED_SCOPE.items():
        plan = _test_plan(skills)
        assert plan["available"], (
            f"a course covering {area} could not offer a test "
            f"({plan['total_items']} items, {MIN_ITEMS_FOR_COURSE_TEST} needed)"
        )


# --------------------------------------------------------------------------- #
#  Buildable: project tickets
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("skill_id", DATA_SKILLS)
def test_every_data_skill_has_a_ticket_template(skill_id):
    """Without one, the skill contributes nothing to a generated board."""
    assert TICKET_TEMPLATES.get(skill_id), f"{skill_id} has no ticket template"


@pytest.mark.parametrize("skill_id", DATA_SKILLS)
def test_data_templates_are_gradeable(skill_id):
    for template in TICKET_TEMPLATES[skill_id]:
        assert template["requirements"], template["slug"]
        assert template["acceptance_criteria"], template["slug"]
        assert template["checks"], f"{template['slug']} can be closed without grading"
        for name in template["files"]:
            assert name in STARTER_FILES, f"{template['slug']} has no starter for {name}"


@pytest.mark.parametrize("skill_id", DATA_SKILLS)
def test_data_template_checks_map_to_real_requirements(skill_id):
    for template in TICKET_TEMPLATES[skill_id]:
        count = len(template["requirements"])
        for check in template["checks"]:
            index = check.get("requirement_index")
            if index is None:
                continue
            assert 0 <= index < count, f"{template['slug']}/{check['id']} points at no requirement"


def test_every_data_skill_appears_in_a_sprint_theme():
    """A skill in no theme never reaches a board, template or not."""
    themed = {skill for _, _, skills in SPRINT_THEMES for skill in skills}
    assert set(DATA_SKILLS) <= themed


def test_sprint_themes_only_name_real_skills():
    graph = get_knowledge_graph()
    for _, name, skills in SPRINT_THEMES:
        for skill_id in skills:
            assert graph.get(skill_id), f"sprint '{name}' names unknown skill {skill_id}"


def test_sql_stack_maps_to_analytical_sql_not_a_node_server():
    """The bug this path exposed: "SQL" used to generate a Node/REST board."""
    skills = get_knowledge_graph().skills_for_stack(["SQL", "Spreadsheet", "Statistics"])
    assert "sql_basics" in skills
    assert "node_basics" not in skills
    assert "rest_api" not in skills


# --------------------------------------------------------------------------- #
#  Practisable: the proof-of-concept SQL questions
# --------------------------------------------------------------------------- #


def test_sql_practice_questions_are_registered():
    for module in SQL_MODULES:
        assert module["id"] in PRACTICE_MODULE_INDEX


@pytest.mark.parametrize("module", SQL_MODULES, ids=lambda m: m["id"])
def test_sql_practice_questions_are_well_formed(module):
    graph = get_knowledge_graph()
    assert module["kind"] == "sql"
    assert graph.get(module["skill_id"]), module["id"]
    assert module["requirements"], module["id"]
    assert module["problem_statement"].strip(), module["id"]
    assert module["editable_files"] == ["query.sql"]
    assert "TODO" in module["files"]["query.sql"], "the starter must not be the answer"


@pytest.mark.parametrize("module", SQL_MODULES, ids=lambda m: m["id"])
def test_sql_starter_does_not_pass(module):
    """A submitted starter must fail, exactly as it does for judged problems."""
    from app.services import sql_judge

    assert not sql_judge.grade(module["files"]["query.sql"], module["sql_spec"]).passed


@pytest.mark.parametrize("module", SQL_MODULES, ids=lambda m: m["id"])
def test_the_declared_solution_passes(module):
    from app.services import sql_judge

    assert sql_judge.grade(module["solution_files"]["query.sql"], module["sql_spec"]).passed


@pytest.mark.parametrize("module", SQL_MODULES, ids=lambda m: m["id"])
def test_hidden_fixture_data_never_reaches_the_client(module):
    """The same contract the stdin/stdout judge honours for hidden cases."""
    import json

    from app.services.practice_service import module_detail

    blob = json.dumps(module_detail(module["id"]))

    def strings(dataset):
        return {
            value
            for rows in dataset["rows"].values()
            for row in rows
            for value in row.values()
            if isinstance(value, str) and len(value) >= 6
        }

    datasets = module["sql_spec"]["datasets"]
    # Values shared with a visible dataset (product names, for instance) are
    # published deliberately, so only hidden-*only* values are evidence of a leak.
    visible = set().union(*(strings(d) for d in datasets if not d.get("hidden")))

    for dataset in datasets:
        if not dataset.get("hidden"):
            continue
        assert dataset["name"] not in blob
        for value in strings(dataset) - visible:
            assert value not in blob, f"{module['id']} leaks {value!r}"


@pytest.mark.parametrize("module", SQL_MODULES, ids=lambda m: m["id"])
def test_the_reference_query_is_never_shipped(module):
    import json

    from app.services.practice_service import module_detail

    blob = json.dumps(module_detail(module["id"]))
    assert module["sql_spec"]["reference"] not in blob


def test_the_path_is_available_and_every_course_is_teachable():
    """
    The path was held closed until courses existed. They do now, so the
    guarantee inverts: being available means every skill a course claims to
    teach is a real graph node with a real question bank behind it. An
    available path pointing at an empty skill is worse than a closed one.
    """
    from app.data.practice_modules import PRACTICE_MODULES
    from app.services.knowledge_graph import get_knowledge_graph

    graph = get_knowledge_graph()
    path = PATH_INDEX["data-analyst"]
    assert path["available"] is True
    assert path["courses"], "an available path must expose courses"

    counts: dict[str, int] = {}
    for module in PRACTICE_MODULES:
        counts[module.get("skill_id")] = counts.get(module.get("skill_id"), 0) + 1

    for course in path["courses"]:
        assert course["skills"], f"{course['id']} teaches nothing"
        for skill in course["skills"]:
            assert graph.get(skill), f"{course['id']} points at unknown skill {skill}"
            assert counts.get(skill, 0) >= 10, (
                f"{skill} backs {course['id']} with only {counts.get(skill, 0)} questions"
            )
