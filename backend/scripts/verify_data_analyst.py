#!/usr/bin/env python3
"""Prove the Data Analyst curriculum cannot be passed by a wrong answer.

Everything here goes through the *real* graders — `sql_judge.grade` for the SQL
questions and ticket checks, and `LocalSubprocessProvider` (the same judge the
platform uses for learner submissions) for the Python analytics questions.
Nothing is compared against a hand-written expectation.

For every question it asserts three things:

  1. the reference solution passes every case, visible and hidden;
  2. every registered wrong answer fails at least one case;
  3. the shipped starter fails — a starter that passes means the suite is
     worthless for that question.

For the SQL questions and the ticket specs it additionally runs the judge's
`hardcode_probe`: a query returning the first dataset's answer as constants. It
must fail, which is what proves the datasets disagree enough that a memorised
answer is not a solution.

    cd backend && PYTHONPATH=. .venv/bin/python scripts/verify_data_analyst.py
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.data.practice_analytics import (  # noqa: E402
    ANALYTICS_MODULES,
    REFERENCE_SOLUTIONS as ANALYTICS_REFERENCE,
    WRONG_SOLUTIONS as ANALYTICS_WRONG,
)
from app.data.practice_sql_bank import (  # noqa: E402
    SQL_BANK,
    WRONG_SOLUTIONS as SQL_WRONG,
)
from app.data.ticket_templates_data import DATA_TICKET_TEMPLATES  # noqa: E402
from app.schemas.execution import TestCase  # noqa: E402
from app.services import sql_judge  # noqa: E402
from app.services.code_execution_service import LocalSubprocessProvider  # noqa: E402

FAILURES: list[str] = []


def _fail(message: str) -> None:
    FAILURES.append(message)
    print(f"      x {message}")


# --------------------------------------------------------------------------- #
#  SQL questions
# --------------------------------------------------------------------------- #


def _grade_sql(query: str, spec: dict) -> tuple[bool, str]:
    grade = sql_judge.grade(query, spec, include_hidden=True)
    if grade.rejection is not None:
        return grade.passed, f"rejected: {grade.rejection}"
    detail = "; ".join(
        f"{outcome.dataset}: {outcome.detail}"
        for outcome in grade.outcomes
        if not outcome.passed
    )
    return grade.passed, detail


def _verify_sql_spec(label: str, spec: dict, wrong: list[str]) -> None:
    reference = spec["reference"]
    passed, detail = _grade_sql(reference, spec)
    if not passed:
        _fail(f"{label}: REFERENCE FAILS ({detail})")
        return

    if not wrong:
        _fail(f"{label}: no wrong answer registered, so nothing is proved")

    for index, candidate in enumerate(wrong):
        candidate_passed, _ = _grade_sql(candidate, spec)
        if candidate_passed:
            _fail(f"{label}: WRONG ANSWER #{index} PASSES")

    probe_passed, _ = _grade_sql(sql_judge.hardcode_probe(spec), spec)
    if probe_passed:
        _fail(f"{label}: a hardcoded constant answer PASSES")


def verify_sql_questions() -> None:
    print(f"\n=== SQL practice questions ({len(SQL_BANK)}) ===")
    for module in SQL_BANK:
        spec = module["sql_spec"]
        wrong = SQL_WRONG.get(module["id"], [])
        before = len(FAILURES)
        _verify_sql_spec(module["id"], spec, wrong)
        status = "OK" if len(FAILURES) == before else "FAIL"
        print(
            f"  {module['id']:52} {status}  "
            f"{len(sql_judge._datasets(spec))} datasets, {len(wrong)} wrong answers"
        )


def verify_ticket_specs() -> None:
    checks = [
        (f"{skill}/{template['slug']}/{check['id']}", check)
        for skill, templates in DATA_TICKET_TEMPLATES.items()
        for template in templates
        for check in template["checks"]
        if check["type"] == "sql_query"
    ]
    print(f"\n=== Capstone ticket SQL checks ({len(checks)}) ===")
    for label, check in checks:
        spec = check["spec"]
        # A ticket ships no wrong answers of its own; the hardcode probe and an
        # unfiltered dump of the base table stand in for them.
        wrong = ["SELECT * FROM orders"]
        before = len(FAILURES)
        _verify_sql_spec(label, spec, wrong)
        status = "OK" if len(FAILURES) == before else "FAIL"
        print(f"  {label:58} {status}")


# --------------------------------------------------------------------------- #
#  Python analytics questions
# --------------------------------------------------------------------------- #


def _cases(module: dict) -> list[TestCase]:
    return [
        TestCase(
            name=case["name"],
            stdin=case["stdin"],
            expected_stdout=case["expected_stdout"],
            hidden=case["hidden"],
            match=case.get("match", "trimmed"),
        )
        for case in module["test_cases"]
    ]


def _judge_python(source: str, cases: list[TestCase]) -> tuple[int, list[str]]:
    result = asyncio.run(LocalSubprocessProvider().run("python", source, cases))
    if result.compile_error:
        return 0, [f"compile error: {result.compile_error.strip()[:200]}"]
    failed = [
        f"{r.name}: exit={r.exit_code} timed_out={r.timed_out} {r.stderr.strip()[:160]}"
        for r in result.results
        if not r.passed
    ]
    return sum(1 for r in result.results if r.passed), failed


def verify_analytics_questions() -> None:
    print(f"\n=== Python analytics questions ({len(ANALYTICS_MODULES)}) ===")
    for module in ANALYTICS_MODULES:
        module_id = module["id"]
        cases = _cases(module)
        before = len(FAILURES)

        passed, failed = _judge_python(ANALYTICS_REFERENCE[module_id], cases)
        if passed != len(cases):
            _fail(f"{module_id}: REFERENCE FAILS {len(failed)} case(s): {failed[:3]}")

        starter_passed, _ = _judge_python(module["files"]["solution"], cases)
        if starter_passed == len(cases):
            _fail(f"{module_id}: STARTER PASSES EVERY CASE (false pass)")

        wrong = ANALYTICS_WRONG.get(module_id, [])
        if not wrong:
            _fail(f"{module_id}: no wrong answer registered, so nothing is proved")
        for index, candidate in enumerate(wrong):
            candidate_passed, _ = _judge_python(candidate, cases)
            if candidate_passed == len(cases):
                _fail(f"{module_id}: WRONG ANSWER #{index} PASSES")

        status = "OK" if len(FAILURES) == before else "FAIL"
        print(
            f"  {module_id:36} {status}  {len(cases)} cases "
            f"({sum(1 for c in cases if c.hidden)} hidden), {len(wrong)} wrong answers"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        choices=["sql", "analytics", "tickets"],
        nargs="*",
        default=["sql", "analytics", "tickets"],
    )
    args = parser.parse_args()

    if "sql" in args.only:
        verify_sql_questions()
    if "tickets" in args.only:
        verify_ticket_specs()
    if "analytics" in args.only:
        verify_analytics_questions()

    print()
    if FAILURES:
        print(f"FAIL: {len(FAILURES)} problem(s)")
        for line in FAILURES:
            print(f"  - {line}")
        return 1
    print(
        "OK: every reference solution passes, every wrong answer and starter "
        "fails, and no hardcoded answer survives the datasets"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
