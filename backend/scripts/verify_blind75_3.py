#!/usr/bin/env python3
"""Verify batch 3 of the Blind 75 set: trees, tries, heaps and backtracking.

Two independent checks, both against the *real* judge:

1. ``--cases`` mode re-derives every expected output from the reference and
   proves each declared wrong solution is rejected. This mirrors
   ``scripts/build_test_cases.py`` but only for this batch, so it can be run
   while other authors are still editing their own files.
2. The default mode runs a known-correct solution in Python, JavaScript, Java,
   C++ and C through ``LocalSubprocessProvider`` against the full generated case
   bank, and confirms the generated starter does **not** pass.

    PYTHONPATH=. .venv/bin/python scripts/verify_blind75_3.py
    PYTHONPATH=. .venv/bin/python scripts/verify_blind75_3.py --cases
    PYTHONPATH=. .venv/bin/python scripts/verify_blind75_3.py --slugs subsets
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.data.curriculum_blind75_3 import PROBLEMS  # noqa: E402
from app.schemas.execution import TestCase  # noqa: E402
from app.services.code_execution_service import (  # noqa: E402
    LocalSubprocessProvider,
    time_limit_for,
)
from scripts.build_test_cases import CANDIDATE_TIMEOUT, REFERENCE_TIMEOUT, run_python, try_run
from scripts.language_solutions_blind75_3 import SOLUTIONS  # noqa: E402

LANGUAGES = ("python", "javascript", "java", "cpp", "c")


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


def check_cases(slugs: set[str] | None) -> int:
    failures: list[str] = []
    for problem in PROBLEMS:
        slug = problem["slug"]
        if slugs and slug not in slugs:
            continue
        print(f"\n  {slug}")
        expectations = []
        for spec in problem["inputs"]:
            try:
                expected, elapsed = run_python(problem["reference"], spec["stdin"], REFERENCE_TIMEOUT)
            except Exception as exc:  # noqa: BLE001 - reported, not raised
                failures.append(f"{slug}: reference failed on '{spec['name']}': {exc}")
                print(f"    FAIL {spec['name']}: {exc}")
                continue
            expectations.append((spec["name"], spec["stdin"], expected))
            shown = expected if len(expected) <= 40 else expected[:37] + "..."
            print(f"    ok  {spec['name']:44} -> {shown!r}  ({elapsed * 1000:.0f}ms)")
        for index, wrong in enumerate(problem["wrong"], start=1):
            caught = None
            for name, stdin, expected in expectations:
                ok, got = try_run(wrong, stdin, CANDIDATE_TIMEOUT)
                if not ok or got != expected:
                    caught = name
                    break
            if caught is None:
                failures.append(f"{slug}: wrong #{index} passed every case")
                print(f"    FALSE PASS wrong #{index}")
            else:
                print(f"    caught wrong #{index} via {caught!r}")

    print()
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("OK: references derive every output and every wrong solution is rejected")
    return 0


def check_languages(slugs: set[str] | None, languages: list[str], skip_starter: bool) -> int:
    from app.data.curriculum import CURRICULUM_MODULES

    batch_slugs = {problem["slug"] for problem in PROBLEMS}
    failures: list[str] = []
    for language in languages:
        print(f"\n=== {language}  (time limit {time_limit_for(language):.0f}s) ===")
        for module in CURRICULUM_MODULES:
            if module["language"] != language:
                continue
            slug = module["id"].removeprefix("cp-").removesuffix(f"-{language}")
            if slug not in batch_slugs or (slugs and slug not in slugs):
                continue
            solution = SOLUTIONS.get(slug, {}).get(language)
            if solution is None:
                failures.append(f"{slug}/{language}: no known-correct solution registered")
                print(f"  {slug:44} NO SOLUTION REGISTERED")
                continue

            cases = _cases(module)
            result = asyncio.run(LocalSubprocessProvider().run(language, solution, cases))
            if result.compile_error:
                failures.append(f"{slug}/{language}: compile error")
                print(f"  {slug:44} COMPILE ERROR\n{result.compile_error}")
                continue
            passed = sum(1 for r in result.results if r.passed)
            slowest = max((r.duration_ms for r in result.results), default=0)
            status = "PASS" if passed == len(cases) else "FAIL"
            print(f"  {slug:44} {status}  {passed}/{len(cases)} cases  (slowest {slowest}ms)")
            for r in result.results:
                if not r.passed:
                    failures.append(f"{slug}/{language}: case '{r.name}' failed")
                    print(
                        f"      x {r.name}: exit={r.exit_code} timed_out={r.timed_out} "
                        f"{r.stderr.strip()[:200]}"
                    )

            if skip_starter:
                continue
            starter_result = asyncio.run(
                LocalSubprocessProvider().run(language, module["files"]["solution"], cases)
            )
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
    print("OK: every batch-3 problem solved in every language, no starter false-passes")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", action="store_true", help="reference/wrong-solution checks only")
    parser.add_argument("--slugs", nargs="*", default=None)
    parser.add_argument("--languages", nargs="*", default=list(LANGUAGES))
    parser.add_argument("--skip-starter-check", action="store_true")
    args = parser.parse_args()
    slugs = set(args.slugs) if args.slugs else None

    if args.cases:
        return check_cases(slugs)
    status = check_cases(slugs)
    return status or check_languages(slugs, args.languages, args.skip_starter_check)


if __name__ == "__main__":
    raise SystemExit(main())
