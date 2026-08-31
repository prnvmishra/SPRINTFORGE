#!/usr/bin/env python3
"""Verify the Blind 75 batch 2 problems end to end.

Modelled on ``scripts/build_test_cases.py`` plus ``scripts/verify_languages.py``,
but scoped to the slugs owned by ``app/data/curriculum_blind75_2.py`` so this
batch can be verified while the other batches are still being written.

Two stages:

1. **Case bank.** Derive every ``expected_stdout`` by running the reference
   twice (non-determinism check) and prove each ``wrong`` solution is rejected
   by at least one case. With ``--write-cases`` the derived cases are merged
   into ``app/data/generated_cases.json`` so the app can be imported before the
   shared, full rebuild happens.
2. **Languages.** Run a known-correct solution for each problem in Python,
   JavaScript, C++, Java and C through the real judge against the full bank,
   and confirm the generated starter does *not* pass.

    PYTHONPATH=. .venv/bin/python scripts/verify_blind75_2.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.data.curriculum_blind75_2 import PROBLEMS  # noqa: E402
from app.data.curriculum_starters import LANGUAGES, build_starters  # noqa: E402
from app.schemas.execution import TestCase  # noqa: E402
from app.services.code_execution_service import (  # noqa: E402
    LocalSubprocessProvider,
    time_limit_for,
)
from scripts.build_test_cases import build_problem  # noqa: E402
from scripts.language_solutions_blind75_2 import SOLUTIONS  # noqa: E402

CASES_PATH = pathlib.Path(__file__).resolve().parents[1] / "app" / "data" / "generated_cases.json"


def build_cases(write: bool, problems: list[dict]) -> dict[str, dict]:
    built = {}
    for problem in problems:
        built[problem["slug"]] = build_problem(problem)
    if write:
        existing = json.loads(CASES_PATH.read_text()) if CASES_PATH.exists() else {}
        existing.update(built)
        CASES_PATH.write_text(json.dumps(existing, indent=2, sort_keys=True) + "\n")
        print(f"\nmerged {len(built)} problems into {CASES_PATH.name}")
    return built


def _cases(entry: dict) -> list[TestCase]:
    return [
        TestCase(
            name=case["name"],
            stdin=case["stdin"],
            expected_stdout=case["expected_stdout"],
            hidden=case["hidden"],
            match=case.get("match", "trimmed"),
        )
        for case in entry["cases"]
    ]


async def _judge(language: str, source: str, cases: list[TestCase]):
    return await LocalSubprocessProvider().run(language, source, cases)


def verify_languages(
    built: dict[str, dict], languages: list[str], problems: list[dict]
) -> list[str]:
    failures: list[str] = []
    for language in languages:
        print(f"\n=== {language}  (time limit {time_limit_for(language):.0f}s) ===")
        for problem in problems:
            slug = problem["slug"]
            cases = _cases(built[slug])
            solution = SOLUTIONS.get(slug, {}).get(language)
            if solution is None:
                failures.append(f"{slug}/{language}: no known-correct solution registered")
                print(f"  {slug:28} NO SOLUTION REGISTERED")
                continue

            result = asyncio.run(_judge(language, solution, cases))
            if result.compile_error:
                failures.append(f"{slug}/{language}: compile error")
                print(f"  {slug:28} COMPILE ERROR\n{result.compile_error}")
                continue
            passed = sum(1 for r in result.results if r.passed)
            slowest = max((r.duration_ms for r in result.results), default=0)
            status = "PASS" if passed == len(cases) else "FAIL"
            print(f"  {slug:28} {status}  {passed}/{len(cases)} cases  (slowest {slowest}ms)")
            for r in result.results:
                if not r.passed:
                    failures.append(f"{slug}/{language}: case '{r.name}' failed")
                    print(
                        f"      x {r.name}: exit={r.exit_code} timed_out={r.timed_out} "
                        f"{r.stderr.strip()[:300]}"
                    )

            starter = build_starters(problem)[language]
            starter_result = asyncio.run(_judge(language, starter, cases))
            if starter_result.compile_error:
                failures.append(f"{slug}/{language}: STARTER does not compile")
                print(f"      starter compile error:\n{starter_result.compile_error}")
                continue
            starter_passed = sum(1 for r in starter_result.results if r.passed)
            if starter_passed == len(cases):
                failures.append(f"{slug}/{language}: STARTER PASSES THE SUITE (false pass)")
                print("      x starter passes every case — the suite is worthless here")
            else:
                print(f"      starter correctly fails ({starter_passed}/{len(cases)} passed)")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--languages", nargs="*", default=list(LANGUAGES))
    parser.add_argument("--cases-only", action="store_true")
    parser.add_argument("--slugs", nargs="*", help="verify only these slugs")
    parser.add_argument(
        "--write-cases",
        action="store_true",
        help="merge the derived cases into generated_cases.json",
    )
    args = parser.parse_args()

    problems = [p for p in PROBLEMS if not args.slugs or p["slug"] in args.slugs]
    print(f"Building case banks for {len(problems)} problems")
    built = build_cases(args.write_cases, problems)
    if args.cases_only:
        print("\nOK: every reference is deterministic and every wrong solution is caught")
        return 0

    failures = verify_languages(built, args.languages, problems)
    print()
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for line in failures:
            print(f"  - {line}")
        return 1
    print(f"OK: {len(problems)} problems solved in every language, no starter false-passes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
