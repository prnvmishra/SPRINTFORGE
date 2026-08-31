#!/usr/bin/env python3
"""Verify Blind 75 batch 1 end to end.

Three checks, all executed rather than asserted structurally:

1. every worked ``example`` in the statement matches what the reference
   actually prints for that stdin (a mistyped example teaches the wrong
   thing, and nothing else in the build looks at them);
2. a known-correct solution in **all five** languages passes the full
   generated case bank through the real judge; and
3. the generated starter for each (problem, language) fails that bank, so the
   suite cannot be satisfied by the scaffolding alone.

    PYTHONPATH=. .venv/bin/python scripts/verify_blind75_1.py
    PYTHONPATH=. .venv/bin/python scripts/verify_blind75_1.py --languages python c
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.data.curriculum import CURRICULUM_MODULES  # noqa: E402
from app.data.curriculum_blind75_1 import PROBLEMS  # noqa: E402
from app.schemas.execution import TestCase  # noqa: E402
from app.services.code_execution_service import (  # noqa: E402
    LocalSubprocessProvider,
    time_limit_for,
)
from scripts.language_solutions_blind75_1 import SOLUTIONS  # noqa: E402

SLUGS = [problem["slug"] for problem in PROBLEMS]
ALL_LANGUAGES = ("python", "javascript", "java", "cpp", "c")


def _run_reference(source: str, stdin: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / "main.py"
        path.write_text(source)
        proc = subprocess.run(
            [sys.executable, str(path)],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip()[:400])
        return proc.stdout.strip()


def check_examples() -> list[str]:
    print("=== worked examples vs reference ===")
    failures: list[str] = []
    for problem in PROBLEMS:
        slug = problem["slug"]
        for index, example in enumerate(problem["examples"], start=1):
            got = _run_reference(problem["reference"], example["stdin"])
            want = example["stdout"].strip()
            if got != want:
                failures.append(f"{slug}: example #{index} says {want!r}, reference says {got!r}")
                print(f"  {slug:32} example #{index} MISMATCH want={want!r} got={got!r}")
        if not any(f.startswith(f"{slug}:") for f in failures):
            print(f"  {slug:32} ok ({len(problem['examples'])} examples)")
    return failures


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--languages", nargs="*", default=list(ALL_LANGUAGES))
    parser.add_argument("--slugs", nargs="*", default=SLUGS)
    parser.add_argument("--skip-starter-check", action="store_true")
    parser.add_argument("--skip-examples", action="store_true")
    args = parser.parse_args()

    failures: list[str] = []
    if not args.skip_examples:
        failures += check_examples()

    modules = {module["id"]: module for module in CURRICULUM_MODULES}
    for language in args.languages:
        print(f"\n=== {language}  (time limit {time_limit_for(language):.0f}s) ===")
        for slug in args.slugs:
            module = modules.get(f"cp-{slug}-{language}")
            if module is None:
                failures.append(f"{slug}/{language}: no module built")
                print(f"  {slug:32} NO MODULE")
                continue

            solution = SOLUTIONS.get(slug, {}).get(language)
            if solution is None:
                failures.append(f"{slug}/{language}: no known-correct solution registered")
                print(f"  {slug:32} NO SOLUTION REGISTERED")
                continue

            cases = _cases(module)
            result = asyncio.run(LocalSubprocessProvider().run(language, solution, cases))
            if result.compile_error:
                failures.append(f"{slug}/{language}: compile error")
                print(f"  {slug:32} COMPILE ERROR\n{result.compile_error}")
                continue

            passed = sum(1 for r in result.results if r.passed)
            slowest = max((r.duration_ms for r in result.results), default=0)
            status = "PASS" if passed == len(cases) else "FAIL"
            print(f"  {slug:32} {status}  {passed}/{len(cases)} cases  (slowest {slowest}ms)")
            for r in result.results:
                if not r.passed:
                    failures.append(f"{slug}/{language}: case '{r.name}' failed")
                    print(
                        f"      x {r.name}: exit={r.exit_code} timed_out={r.timed_out} "
                        f"got={r.stdout.strip()[:60]!r} {r.stderr.strip()[:200]}"
                    )

            if args.skip_starter_check:
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
    print("OK: blind75 batch 1 solved in every language, examples accurate, no starter false-passes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
