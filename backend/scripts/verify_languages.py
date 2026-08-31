#!/usr/bin/env python3
"""Prove every curriculum problem is solvable in every supported language.

For each (problem, language) it runs a known-correct solution through the *real*
judge (``LocalSubprocessProvider``) against the full generated case bank —
visible and hidden — and additionally runs the generated starter to confirm the
starter does **not** pass. A language is only "first class" when both hold.

    PYTHONPATH=. .venv/bin/python scripts/verify_languages.py
    PYTHONPATH=. .venv/bin/python scripts/verify_languages.py --languages java c
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.data.curriculum import CURRICULUM_MODULES  # noqa: E402
from app.schemas.execution import TestCase  # noqa: E402
from app.services.code_execution_service import (  # noqa: E402
    LocalSubprocessProvider,
    time_limit_for,
)
from scripts.language_solutions import SOLUTIONS  # noqa: E402


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


async def _judge(language: str, source: str, cases: list[TestCase]):
    return await LocalSubprocessProvider().run(language, source, cases)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--languages", nargs="*", default=["java", "c"])
    parser.add_argument(
        "--skip-starter-check",
        action="store_true",
        help="skip the (slower) proof that the starter fails the suite",
    )
    args = parser.parse_args()

    failures: list[str] = []
    for language in args.languages:
        print(f"\n=== {language}  (time limit {time_limit_for(language):.0f}s) ===")
        for module in CURRICULUM_MODULES:
            if module["language"] != language:
                continue
            slug = module["id"].removeprefix("cp-").removesuffix(f"-{language}")
            solution = SOLUTIONS.get(slug, {}).get(language)
            if solution is None:
                failures.append(f"{slug}/{language}: no known-correct solution registered")
                print(f"  {slug:28} NO SOLUTION REGISTERED")
                continue

            cases = _cases(module)
            result = asyncio.run(_judge(language, solution, cases))
            if result.compile_error:
                failures.append(f"{slug}/{language}: compile error")
                print(f"  {slug:28} COMPILE ERROR\n{result.compile_error}")
                continue

            passed = sum(1 for r in result.results if r.passed)
            slowest = max((r.duration_ms for r in result.results), default=0)
            status = "PASS" if passed == len(cases) else "FAIL"
            print(
                f"  {slug:28} {status}  {passed}/{len(cases)} cases  "
                f"(slowest {slowest}ms)"
            )
            for r in result.results:
                if not r.passed:
                    failures.append(f"{slug}/{language}: case '{r.name}' failed")
                    print(f"      x {r.name}: exit={r.exit_code} timed_out={r.timed_out} "
                          f"{r.stderr.strip()[:200]}")

            if args.skip_starter_check:
                continue
            starter = module["files"]["solution"]
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

    print()
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("OK: every problem solved in every requested language, no starter false-passes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
