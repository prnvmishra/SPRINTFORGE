#!/usr/bin/env python3
"""Verify the language-fundamentals problems end to end, through the real judge.

Five checks per problem, all executed rather than asserted structurally:

1. every worked ``example`` in the statement matches what the reference
   actually prints for that stdin — a mistyped example teaches the wrong thing
   and nothing else in the build looks at them;
2. the reference solution **passes every case**, visible and hidden, run
   through ``LocalSubprocessProvider`` — the same judge a learner's submission
   goes through, not a comparison done in-process;
3. every declared wrong solution **fails at least one case**. This is the check
   that makes a false pass impossible: if a broken solution survives the whole
   bank, the bank is too weak and this script says so;
4. a known-correct solution in the problem's **own language** passes every
   case, which is the only thing that proves a C-only pointer problem is
   actually solvable in C; and
5. the generated starter **fails**, so the scaffolding alone cannot pass.

    PYTHONPATH=. .venv/bin/python scripts/verify_basics.py
    PYTHONPATH=. .venv/bin/python scripts/verify_basics.py --languages c cpp
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.data.curriculum import CURRICULUM_MODULES, graded_cases  # noqa: E402
from app.data.curriculum_basics_c import PROBLEMS as BASICS_C  # noqa: E402
from app.data.curriculum_basics_cpp import PROBLEMS as BASICS_CPP  # noqa: E402
from app.data.curriculum_basics_java import PROBLEMS as BASICS_JAVA  # noqa: E402
from app.data.curriculum_basics_python import PROBLEMS as BASICS_PYTHON  # noqa: E402
from app.schemas.execution import TestCase  # noqa: E402
from app.services.code_execution_service import (  # noqa: E402
    LocalSubprocessProvider,
    time_limit_for,
)
from scripts.language_solutions_basics import solution_for  # noqa: E402

PROBLEMS = [*BASICS_C, *BASICS_CPP, *BASICS_JAVA, *BASICS_PYTHON]
MODULES = {module["id"]: module for module in CURRICULUM_MODULES}


def _cases(module: dict) -> list[TestCase]:
    return [
        TestCase(
            name=case["name"],
            stdin=case["stdin"],
            expected_stdout=case["expected_stdout"],
            hidden=case["hidden"],
            match=case.get("match", "trimmed"),
        )
        for case in graded_cases(module)
    ]


def _judge(language: str, source: str, cases: list[TestCase]):
    return asyncio.run(LocalSubprocessProvider().run(language, source, cases))


def _run_reference(source: str, stdin: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / "main.py"
        path.write_text(source)
        proc = subprocess.run(
            [sys.executable, str(path)],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip()[:400])
        return proc.stdout.strip()


def check_examples(problems: list[dict]) -> list[str]:
    print("=== worked examples vs reference ===")
    failures: list[str] = []
    for problem in problems:
        slug = problem["slug"]
        bad = []
        for index, example in enumerate(problem["examples"], start=1):
            got = _run_reference(problem["reference"], example["stdin"])
            want = example["stdout"].strip()
            if got != want:
                bad.append(f"#{index} says {want!r}, reference says {got!r}")
        if bad:
            failures += [f"{slug}: example {item}" for item in bad]
            print(f"  {slug:34} MISMATCH {bad}")
        else:
            print(f"  {slug:34} ok ({len(problem['examples'])} examples)")
    return failures


def check_problem(problem: dict) -> list[str]:
    slug = problem["slug"]
    language = problem["languages"][0]
    failures: list[str] = []

    module = MODULES.get(f"cp-{slug}-{language}")
    if module is None:
        return [f"{slug}: no module built for {language}"]

    # A restricted problem must not have leaked into the other languages.
    strays = [
        other
        for other in ("python", "javascript", "java", "cpp", "c")
        if other != language and f"cp-{slug}-{other}" in MODULES
    ]
    if strays:
        failures.append(f"{slug}: expanded into {strays} despite languages=[{language}]")

    cases = _cases(module)
    visible = sum(1 for case in cases if not case.hidden)
    hidden = len(cases) - visible
    print(f"\n  {slug}  [{language}]  {visible} visible + {hidden} hidden")

    # 2 · the reference passes everything, through the judge.
    result = _judge("python", problem["reference"], cases)
    if result.compile_error:
        failures.append(f"{slug}: reference compile error")
        print(f"    reference COMPILE ERROR: {result.compile_error}")
    else:
        bad = [r.name for r in result.results if not r.passed]
        if bad:
            failures.append(f"{slug}: reference failed {bad}")
            print(f"    reference FAILED {bad}")
        else:
            slowest = max((r.duration_ms for r in result.results), default=0)
            print(f"    reference   PASS  {len(cases)}/{len(cases)}  (slowest {slowest}ms)")

    # 3 · every wrong solution is rejected.
    for index, wrong in enumerate(problem["wrong"], start=1):
        wrong_result = _judge("python", wrong, cases)
        rejected = [r.name for r in wrong_result.results if not r.passed]
        if not rejected:
            failures.append(f"{slug}: wrong #{index} PASSED every case")
            print(f"    wrong #{index}    FALSE PASS — the case bank is too weak")
        else:
            print(f"    wrong #{index}    correctly fails ({len(rejected)} case(s), "
                  f"first: {rejected[0]!r})")

    # 4 · the problem is solvable in its own language.
    try:
        solution = solution_for(problem)
    except KeyError as exc:
        failures.append(f"{slug}: {exc}")
        print(f"    {language} solution NOT REGISTERED")
        return failures

    solved = _judge(language, solution, cases)
    if solved.compile_error:
        failures.append(f"{slug}: {language} solution does not compile")
        print(f"    {language} solution COMPILE ERROR:\n{solved.compile_error}")
    else:
        bad = [(r.name, r.stdout.strip()[:60], r.stderr.strip()[:120]) for r in solved.results if not r.passed]
        if bad:
            failures.append(f"{slug}: {language} solution failed {[b[0] for b in bad]}")
            for name, out, err in bad:
                print(f"    x {language} solution failed {name!r} got={out!r} {err}")
        else:
            slowest = max((r.duration_ms for r in solved.results), default=0)
            print(f"    {language:7} sol PASS  {len(cases)}/{len(cases)}  (slowest {slowest}ms)")

    # 5 · the starter does not.
    starter = module["files"]["solution"]
    starter_result = _judge(language, starter, cases)
    if starter_result.compile_error:
        failures.append(f"{slug}: {language} STARTER does not compile")
        print(f"    starter COMPILE ERROR:\n{starter_result.compile_error}")
    elif all(r.passed for r in starter_result.results):
        failures.append(f"{slug}: {language} STARTER PASSES THE SUITE (false pass)")
        print("    x starter passes every case — the suite is worthless here")
    else:
        passed = sum(1 for r in starter_result.results if r.passed)
        print(f"    starter     correctly fails ({passed}/{len(cases)} passed)")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--languages", nargs="*", default=["c", "cpp", "java", "python"])
    parser.add_argument("--slugs", nargs="*", default=None)
    parser.add_argument("--skip-examples", action="store_true")
    args = parser.parse_args()

    problems = [p for p in PROBLEMS if p["languages"][0] in args.languages]
    if args.slugs:
        problems = [p for p in problems if p["slug"] in args.slugs]
    if not problems:
        print("no problems selected")
        return 1

    failures: list[str] = []
    if not args.skip_examples:
        failures += check_examples(problems)

    for language in args.languages:
        selected = [p for p in problems if p["languages"][0] == language]
        if not selected:
            continue
        print(f"\n=== {language}  ({len(selected)} problems, "
              f"time limit {time_limit_for(language):.0f}s) ===")
        for problem in selected:
            failures += check_problem(problem)

    print()
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for line in failures:
            print(f"  - {line}")
        return 1
    print(
        f"OK: {len(problems)} fundamentals problems — references pass, every wrong "
        "solution is rejected, each problem is solved in its own language, and no "
        "starter passes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
