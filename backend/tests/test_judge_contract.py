"""Locks the LeetCode-style judging contract.

The product promise is narrow and easy to regress: Run reveals only sample
cases, Submit grades everything, and a solution that merely satisfies the
samples must not be accepted. These tests assert that contract at the seams
where it could silently break — the module payload sent to the browser, and the
generated test bank behind it.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys

import pytest

from app.data.curriculum import CURRICULUM_MODULES, TRACKS, graded_cases
from app.data.curriculum_cp import CP_PROBLEMS
from app.data.practice_modules import PRACTICE_MODULE_INDEX
from app.services.practice_service import module_detail
from app.services.validation_service import run_static_checks

CURRICULUM_IDS = [m["id"] for m in CURRICULUM_MODULES]

#: Every stdin/stdout-judged module, not just the generated curriculum ones.
#:
#: These invariants were parametrised over `CURRICULUM_MODULES` alone, which
#: covered 455 of 534 challenge modules. The 79 hand-authored ones were exempt
#: from every check below — including the hidden-case leak check — and that is
#: how six modules shipping no worked example stayed invisible. The contract is
#: a property of being judged, not of which file the module was written in.
#: `cases_slug` counts as being judged as much as an embedded case list does:
#: curriculum modules keep only their visible cases in memory and name the slug
#: whose hidden cases grade them, so testing for `test_cases` alone would start
#: silently exempting them the moment a slug had no visible case.
JUDGED_IDS = sorted(
    module_id
    for module_id, module in PRACTICE_MODULE_INDEX.items()
    if module.get("kind") == "challenge"
    and (module.get("test_cases") or module.get("cases_slug"))
)


def test_curriculum_modules_are_registered():
    for module_id in CURRICULUM_IDS:
        assert module_id in PRACTICE_MODULE_INDEX


@pytest.mark.parametrize("module_id", JUDGED_IDS)
def test_every_problem_has_visible_and_hidden_cases(module_id):
    """A problem with no hidden cases cannot enforce the submit gate at all."""
    module = PRACTICE_MODULE_INDEX[module_id]
    cases = graded_cases(module)
    assert sum(1 for c in cases if not c["hidden"]) >= 1, "no sample case to run against"
    assert sum(1 for c in cases if c["hidden"]) >= 1, "no hidden case gating submission"


@pytest.mark.parametrize("module_id", JUDGED_IDS)
def test_hidden_cases_never_reach_the_client(module_id):
    """The detail payload is what the browser receives, so it must be clean.

    Sample cases are published deliberately; hidden inputs and their expected
    outputs must not appear anywhere in it, under any key.
    """
    detail = module_detail(module_id)
    assert detail is not None
    blob = json.dumps(detail)

    # Deliberately the *graded* set, so the hidden cases are pulled off disk and
    # checked against the payload. Reading only the module's in-memory cases
    # would make this pass by having nothing hidden to look for.
    module = PRACTICE_MODULE_INDEX[module_id]
    all_cases = graded_cases(module)
    hidden = [c for c in all_cases if c["hidden"]]
    visible = [c for c in all_cases if not c["hidden"]]

    # The sharp assertions. A hidden case's name or its exact input appearing
    # anywhere in the payload is what actually gives an answer away, because it
    # ties a specific input to a specific expected output.
    for case in hidden:
        assert case["name"] not in blob, f"{module_id}: a hidden case name is served"
        assert case["stdin"] not in blob, (
            f"{module_id}: hidden input {case['stdin']!r} is published, which "
            "gives away that case's answer"
        )

    # Structural, so it cannot be satisfied by accident: the served case list is
    # exactly the visible cases, and nothing in it is flagged hidden.
    served = detail["sample_tests"]
    assert not any(c["hidden"] for c in served)
    assert [c["name"] for c in served] == [c["name"] for c in visible]
    assert detail["hidden_test_count"] == len(hidden)

    # There is deliberately no substring scan of the payload for hidden expected
    # outputs. One recurs inside unrelated public text often enough — "1 2 3 4"
    # within a worked example's input, "Sunday weekend" within a published
    # multi-line answer — that the check produced false alarms and no findings,
    # and a shared answer is not a leak anyway: two inputs can map to the same
    # output, and the learner still has to handle the hidden input to get there.
    # The input assertion above is what makes a specific case's answer safe.


@pytest.mark.parametrize("module_id", JUDGED_IDS)
def test_reference_solutions_are_not_shipped(module_id):
    """Nothing in the served payload may contain a working solution."""
    detail = module_detail(module_id)
    blob = json.dumps(detail)
    for problem in CP_PROBLEMS:
        assert problem["reference"] not in blob
        for wrong in problem["wrong"]:
            assert wrong not in blob


@pytest.mark.parametrize("module_id", JUDGED_IDS)
def test_starter_code_does_not_solve_the_problem(module_id):
    """Starters must plumb I/O only, so a submitted starter fails the suite."""
    module = PRACTICE_MODULE_INDEX[module_id]
    starter = module["files"]["solution"]
    assert "TODO" in starter


@pytest.mark.parametrize("module_id", JUDGED_IDS)
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


class _FakeJudge0Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _FakeJudge0Client:
    """Stands in for httpx.AsyncClient, answering with one canned verdict."""

    def __init__(self, payload):
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def post(self, *args, **kwargs):
        return _FakeJudge0Response(self._payload)


@pytest.mark.parametrize(
    "status_id,label",
    [(5, "time limit exceeded"), (6, "compilation error"), (11, "runtime error")],
)
def test_judge0_does_not_credit_a_submission_that_never_finished(
    monkeypatch, status_id, label
):
    """A run that did not complete is a failure, however much output matched.

    Judge0 reports the outcome as a status id; the expected text can still be on
    stdout when the sandbox killed the process (a timed-out O(n^2) solution that
    printed most of its answer) or when it crashed after printing. Crediting
    those is a false pass, and it is the one the scale cases exist to prevent.
    """
    import app.services.code_execution_service as ces
    from app.schemas.execution import TestCase

    monkeypatch.setattr(ces.settings, "JUDGE0_API_KEY", "test-key", raising=False)
    payload = {
        "stdout": "42\n",
        "stderr": "",
        # A compile error is reported through its own field, which short-circuits
        # before the per-case verdict; the other two reach the comparison.
        "compile_output": "error: expected ';'" if status_id == 6 else None,
        "status": {"id": status_id},
    }
    monkeypatch.setattr(
        ces.httpx, "AsyncClient", lambda *a, **k: _FakeJudge0Client(payload)
    )

    case = TestCase(name="scale", stdin="", expected_stdout="42")
    result = asyncio.run(ces.Judge0Provider().run("python", "print(42)", [case]))

    if status_id == 6:
        assert result.compile_error, f"{label} must be reported, not graded"
        assert not result.results
    else:
        assert result.results, f"{label} should still produce a graded row"
        assert not result.results[0].passed, (
            f"judge0 credited a submission that ended in {label}"
        )


def test_judge0_accepts_a_run_that_finished_with_the_right_answer():
    """The guard above must not reject a genuinely correct submission."""
    import app.services.code_execution_service as ces
    from app.schemas.execution import TestCase

    ces.settings.JUDGE0_API_KEY = "test-key"
    payload = {"stdout": "42\n", "stderr": "", "compile_output": None,
               "status": {"id": 3}}
    original = ces.httpx.AsyncClient
    ces.httpx.AsyncClient = lambda *a, **k: _FakeJudge0Client(payload)
    try:
        case = TestCase(name="ok", stdin="", expected_stdout="42")
        result = asyncio.run(ces.Judge0Provider().run("python", "print(42)", [case]))
    finally:
        ces.httpx.AsyncClient = original
    assert result.results[0].passed


def test_judge0_reports_a_time_limit_as_a_timeout():
    """"Too slow" and "wrong answer" are different diagnoses, and the learner is
    owed the accurate one."""
    import app.services.code_execution_service as ces
    from app.schemas.execution import TestCase

    ces.settings.JUDGE0_API_KEY = "test-key"
    payload = {"stdout": "", "stderr": "", "compile_output": None, "status": {"id": 5}}
    original = ces.httpx.AsyncClient
    ces.httpx.AsyncClient = lambda *a, **k: _FakeJudge0Client(payload)
    try:
        case = TestCase(name="scale", stdin="", expected_stdout="42")
        result = asyncio.run(ces.Judge0Provider().run("python", "x=1", [case]))
    finally:
        ces.httpx.AsyncClient = original
    assert result.results[0].timed_out is True
    assert result.results[0].passed is False


# ------------------------------------------------------------------- piston
#
# The remote providers had no coverage at all, which is how the Judge0 false
# pass above shipped. Piston gets the same treatment.


class _RecordingPistonClient:
    """Captures the request body so the timeout contract can be asserted."""

    def __init__(self, payload, sent):
        self._payload = payload
        self._sent = sent

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def post(self, *args, **kwargs):
        self._sent.append(kwargs.get("json"))
        return _FakeJudge0Response(self._payload)


def _run_piston(monkeypatch, run_stage, language="python"):
    import app.services.code_execution_service as ces
    from app.schemas.execution import TestCase

    sent: list[dict] = []
    payload = {"compile": {}, "run": run_stage}
    monkeypatch.setattr(
        ces.httpx, "AsyncClient", lambda *a, **k: _RecordingPistonClient(payload, sent)
    )
    case = TestCase(name="scale", stdin="", expected_stdout="42")
    result = asyncio.run(ces.PistonProvider().run(language, "print(42)", [case]))
    return result, sent


def test_piston_sends_our_own_time_limit(monkeypatch):
    """Otherwise the remote default decides, and the scale cases stop gating
    complexity at the limit the problem was measured against."""
    import app.services.code_execution_service as ces

    result, sent = _run_piston(monkeypatch, {"stdout": "42\n", "stderr": "", "code": 0})
    assert result.results[0].passed
    assert sent, "no request was captured"
    assert sent[0]["run_timeout"] == int(ces.time_limit_for("python") * 1000)


def test_piston_does_not_credit_a_killed_run(monkeypatch):
    """A program killed at the limit reports `code: null`, and matching output
    must not rescue it."""
    result, _ = _run_piston(
        monkeypatch,
        {"stdout": "42\n", "stderr": "", "code": None, "signal": "SIGKILL"},
    )
    assert result.results[0].passed is False
    assert result.results[0].timed_out is True


def test_piston_does_not_credit_a_nonzero_exit(monkeypatch):
    result, _ = _run_piston(
        monkeypatch, {"stdout": "42\n", "stderr": "boom", "code": 1}
    )
    assert result.results[0].passed is False


# ------------------------------------------------- the runtime case store
#
# Curriculum modules hold only their visible cases in memory and name a slug
# whose hidden cases are loaded from `app/data/cases/` on demand. That store is
# a derived, untracked build artifact, so it can be absent, stale, or — as
# happened when hidden cases moved to gzip — left in a format the loader no
# longer reads. Every one of those states breaks Submit for all 455 curriculum
# modules while the rest of the suite stays green, because nothing else here
# actually asks for a hidden case.


def test_every_curriculum_module_can_name_its_hidden_cases():
    """Cheap: checks the file the loader will open, without decompressing 76MB."""
    from app.data.curriculum import CASES_HIDDEN_DIR, HIDDEN_SUFFIX

    missing = []
    for module_id in CURRICULUM_IDS:
        slug = PRACTICE_MODULE_INDEX[module_id].get("cases_slug")
        if slug is None:
            continue
        if not (CASES_HIDDEN_DIR / f"{slug}{HIDDEN_SUFFIX}").exists():
            missing.append(slug)

    assert not missing, (
        f"{len(set(missing))} slugs have no hidden case file, so Submit fails for "
        "every module using them. Run: python -m scripts.split_case_bank\n"
        f"missing: {sorted(set(missing))[:10]}"
    )


def test_curriculum_modules_actually_grade():
    """The store must be readable, not merely present.

    One module per language, so a format the loader cannot open is caught without
    pulling the whole store into memory.
    """
    from app.data.curriculum import graded_cases

    seen: set[str] = set()
    checked = 0
    for module_id in CURRICULUM_IDS:
        module = PRACTICE_MODULE_INDEX[module_id]
        language = module.get("language")
        if language in seen:
            continue
        seen.add(language)
        cases = graded_cases(module)
        assert cases, f"{module_id} grades against nothing"
        assert any(c["hidden"] for c in cases), f"{module_id} has no hidden case to grade"
        checked += 1

    assert checked >= 5, f"only {checked} languages covered — expected the full set"


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


@pytest.mark.parametrize(
    "script",
    ["scripts.split_case_bank", "scripts.build_curriculum_manifest"],
)
def test_derived_artifacts_are_up_to_date(script):
    """The API serves these, so drift here is drift in what learners are graded on.

    Both are derived from the bank, and both are what the running API actually
    reads — a stale hidden-cases file would keep grading against inputs the
    curriculum no longer declares, silently and forever.
    """
    result = subprocess.run(
        [sys.executable, "-m", script, "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
