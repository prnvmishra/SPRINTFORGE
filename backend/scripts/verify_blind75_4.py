#!/usr/bin/env python3
"""Verify Blind 75 batch 4 (DP, graphs, matrix) end to end.

Modelled on ``scripts/build_test_cases.py`` and ``scripts/verify_languages.py``
but scoped to ``app/data/curriculum_blind75_4.py`` and self-contained, so it can
be run while other agents are mid-edit in the sibling batch files.

Two phases:

1. ``cases``     — derive every expected output from the reference (twice, to
                   catch non-determinism) and prove each declared ``wrong``
                   solution is rejected by at least one case.
2. ``languages`` — run a known-correct solution from
                   ``scripts/language_solutions_blind75_4.py`` through the real
                   judge for every language, and confirm the *generated starter*
                   fails.

    PYTHONPATH=. .venv/bin/python scripts/verify_blind75_4.py
    PYTHONPATH=. .venv/bin/python scripts/verify_blind75_4.py --phase cases
    PYTHONPATH=. .venv/bin/python scripts/verify_blind75_4.py --only b75-jump-game
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.data.curriculum_blind75_4 import PROBLEMS  # noqa: E402
from app.data.curriculum_starters import LANGUAGES, build_starters  # noqa: E402
from app.schemas.execution import TestCase  # noqa: E402
from app.services.code_execution_service import (  # noqa: E402
    LocalSubprocessProvider,
    time_limit_for,
)
from scripts.language_solutions_blind75_4 import SOLUTIONS  # noqa: E402

REFERENCE_TIMEOUT = 30.0
CANDIDATE_TIMEOUT = 10.0


def _run_python(source: str, stdin: str, timeout: float) -> tuple[bool, str, float]:
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / "main.py"
        path.write_text(source)
        started = time.monotonic()
        try:
            proc = subprocess.run(
                [sys.executable, str(path)],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return False, f"timed out after {timeout}s", timeout
        elapsed = time.monotonic() - started
        if proc.returncode != 0:
            return False, (proc.stderr or "non-zero exit").strip()[:300], elapsed
        return True, proc.stdout.strip(), elapsed


def build_cases(problem: dict, verbose: bool = True) -> tuple[list[dict], list[str]]:
    failures: list[str] = []
    slug = problem["slug"]
    cases: list[dict] = []
    for spec in problem["inputs"]:
        ok, out, elapsed = _run_python(problem["reference"], spec["stdin"], REFERENCE_TIMEOUT)
        if not ok:
            failures.append(f"{slug}: reference failed on '{spec['name']}': {out}")
            continue
        ok2, out2, _ = _run_python(problem["reference"], spec["stdin"], REFERENCE_TIMEOUT)
        if not ok2 or out2 != out:
            failures.append(f"{slug}: reference non-deterministic on '{spec['name']}'")
        cases.append(
            {
                "name": spec["name"],
                "stdin": spec["stdin"],
                "expected_stdout": out,
                "hidden": bool(spec["hidden"]),
            }
        )
        if verbose:
            shown = out if len(out) <= 40 else out[:37] + "..."
            print(f"    ok  {spec['name']:38} -> {shown!r}  ({elapsed * 1000:.0f}ms)")

    for index, wrong in enumerate(problem.get("wrong", []), start=1):
        caught = None
        for case in cases:
            ok, got, _ = _run_python(wrong, case["stdin"], CANDIDATE_TIMEOUT)
            if not ok or got != case["expected_stdout"]:
                caught = case["name"]
                break
        if caught is None:
            failures.append(f"{slug}: wrong solution #{index} PASSED EVERY CASE")
            if verbose:
                print(f"    !!  wrong #{index} passed every case")
        elif verbose:
            print(f"    caught wrong #{index} via {caught!r}")
    return cases, failures


async def _judge(language: str, source: str, cases: list[TestCase]):
    return await LocalSubprocessProvider().run(language, source, cases)


def check_languages(
    problem: dict, cases: list[dict], languages: list[str]
) -> list[str]:
    failures: list[str] = []
    slug = problem["slug"]
    starters = build_starters(problem)
    judge_cases = [
        TestCase(
            name=c["name"],
            stdin=c["stdin"],
            expected_stdout=c["expected_stdout"],
            hidden=c["hidden"],
            match="trimmed",
        )
        for c in cases
    ]
    for language in languages:
        solution = SOLUTIONS.get(slug, {}).get(language)
        if solution is None:
            failures.append(f"{slug}/{language}: no known-correct solution registered")
            print(f"    {language:11} NO SOLUTION REGISTERED")
            continue
        result = asyncio.run(_judge(language, solution, judge_cases))
        if result.compile_error:
            failures.append(f"{slug}/{language}: compile error")
            print(f"    {language:11} COMPILE ERROR\n{result.compile_error[:600]}")
            continue
        passed = sum(1 for r in result.results if r.passed)
        slowest = max((r.duration_ms for r in result.results), default=0)
        status = "PASS" if passed == len(judge_cases) else "FAIL"
        print(
            f"    {language:11} {status}  {passed}/{len(judge_cases)} cases "
            f"(slowest {slowest}ms, limit {time_limit_for(language):.0f}s)"
        )
        for r in result.results:
            if not r.passed:
                failures.append(f"{slug}/{language}: case '{r.name}' failed")
                print(
                    f"        x {r.name}: exit={r.exit_code} timed_out={r.timed_out} "
                    f"{r.stderr.strip()[:200]}"
                )

        starter_result = asyncio.run(_judge(language, starters[language], judge_cases))
        if starter_result.compile_error:
            failures.append(f"{slug}/{language}: STARTER does not compile")
            print(f"        starter compile error:\n{starter_result.compile_error[:600]}")
            continue
        starter_passed = sum(1 for r in starter_result.results if r.passed)
        if starter_passed == len(judge_cases):
            failures.append(f"{slug}/{language}: STARTER PASSES THE SUITE (false pass)")
            print("        x starter passes every case")
        else:
            print(f"        starter correctly fails ({starter_passed}/{len(judge_cases)})")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["cases", "languages", "all"], default="all")
    parser.add_argument("--languages", nargs="*", default=list(LANGUAGES))
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args()

    problems = PROBLEMS
    if args.only:
        wanted = set(args.only)
        problems = [p for p in PROBLEMS if p["slug"] in wanted]
        missing = wanted - {p["slug"] for p in problems}
        if missing:
            print(f"unknown slug(s): {sorted(missing)}")
            return 1

    failures: list[str] = []
    for problem in problems:
        print(f"\n  {problem['slug']}")
        cases, case_failures = build_cases(problem)
        failures.extend(case_failures)
        if args.phase in {"languages", "all"} and not case_failures:
            failures.extend(check_languages(problem, cases, args.languages))

    print()
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for line in failures:
            print(f"  - {line}")
        return 1
    print(f"OK: {len(problems)} problems verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
