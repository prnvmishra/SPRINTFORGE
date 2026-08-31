"""Locks the LeetCode-style judging contract.

The product promise is narrow and easy to regress: Run reveals only sample
cases, Submit grades everything, and a solution that merely satisfies the
samples must not be accepted. These tests assert that contract at the seams
where it could silently break — the module payload sent to the browser, and the
generated test bank behind it.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from app.data.curriculum import CURRICULUM_MODULES, TRACKS
from app.data.curriculum_cp import CP_PROBLEMS
from app.data.practice_modules import PRACTICE_MODULE_INDEX
from app.services.practice_service import module_detail
from app.services.validation_service import run_static_checks

CURRICULUM_IDS = [m["id"] for m in CURRICULUM_MODULES]


def test_curriculum_modules_are_registered():
    for module_id in CURRICULUM_IDS:
        assert module_id in PRACTICE_MODULE_INDEX


@pytest.mark.parametrize("module_id", CURRICULUM_IDS)
def test_every_problem_has_visible_and_hidden_cases(module_id):
    """A problem with no hidden cases cannot enforce the submit gate at all."""
    module = PRACTICE_MODULE_INDEX[module_id]
    cases = module["test_cases"]
    assert sum(1 for c in cases if not c["hidden"]) >= 1, "no sample case to run against"
    assert sum(1 for c in cases if c["hidden"]) >= 1, "no hidden case gating submission"


@pytest.mark.parametrize("module_id", CURRICULUM_IDS)
def test_hidden_cases_never_reach_the_client(module_id):
    """The detail payload is what the browser receives, so it must be clean.

    Sample cases are published deliberately; hidden inputs and their expected
    outputs must not appear anywhere in it, under any key.
    """
    detail = module_detail(module_id)
    assert detail is not None
    blob = json.dumps(detail)

    module = PRACTICE_MODULE_INDEX[module_id]
    for case in module["test_cases"]:
        if not case["hidden"]:
            continue
        assert case["name"] not in blob
        assert case["stdin"] not in blob
        # Short outputs like "0" or "3" legitimately collide with unrelated
        # numbers in the payload, so only assert on outputs long enough to be
        # unambiguous evidence of a leak.
        if len(case["expected_stdout"]) >= 6:
            assert case["expected_stdout"] not in blob

    assert detail["hidden_test_count"] == sum(
        1 for c in module["test_cases"] if c["hidden"]
    )


@pytest.mark.parametrize("module_id", CURRICULUM_IDS)
def test_reference_solutions_are_not_shipped(module_id):
    """Nothing in the served payload may contain a working solution."""
    detail = module_detail(module_id)
    blob = json.dumps(detail)
    for problem in CP_PROBLEMS:
        assert problem["reference"] not in blob
        for wrong in problem["wrong"]:
            assert wrong not in blob


@pytest.mark.parametrize("module_id", CURRICULUM_IDS)
def test_starter_code_does_not_solve_the_problem(module_id):
    """Starters must plumb I/O only, so a submitted starter fails the suite."""
    module = PRACTICE_MODULE_INDEX[module_id]
    starter = module["files"]["solution"]
    assert "TODO" in starter


@pytest.mark.parametrize("module_id", CURRICULUM_IDS)
def test_problems_state_constraints_and_criteria(module_id):
    module = PRACTICE_MODULE_INDEX[module_id]
    assert module["constraints"], "a judged problem must state its constraints"
    assert module["requirements"], "a judged problem must state its pass criteria"
    assert module["input_format"] and module["output_format"]
    assert module["examples"], "learners need at least one worked example"
    for example in module["examples"]:
        assert example["explanation"].strip()


def test_tracks_reference_real_skills():
    from app.services.knowledge_graph import get_knowledge_graph

    graph = get_knowledge_graph()
    for track in TRACKS.values():
        for skill_id in track["skills"]:
            assert graph.name_of(skill_id), f"{track['id']} references unknown skill {skill_id}"


def test_hidden_static_checks_are_skipped_on_run():
    """Run must not evaluate hidden checks for non-judge modules either."""
    checks = [
        {"id": "visible", "type": "html_element", "file": "index.html", "selector": "p"},
        {
            "id": "secret",
            "type": "html_element",
            "file": "index.html",
            "selector": "p",
            "hidden": True,
        },
    ]
    files = {"index.html": "<p>hi</p>"}

    visible_only = run_static_checks(files, checks, include_hidden=False)
    assert [o.id for o in visible_only] == ["visible"]

    graded = run_static_checks(files, checks, include_hidden=True)
    assert [o.id for o in graded] == ["visible", "secret"]
    assert [o.hidden for o in graded] == [False, True]


def test_generated_cases_are_up_to_date():
    """Guards against editing curriculum inputs without rebuilding the bank.

    This also re-runs the "wrong solutions must fail" verification, so a suite
    that has been weakened by an edit fails here rather than in production.
    """
    result = subprocess.run(
        [sys.executable, "-m", "scripts.build_test_cases", "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "generated_cases.json is stale or the suite no longer catches the known "
        f"wrong solutions.\n{result.stdout}\n{result.stderr}"
    )
