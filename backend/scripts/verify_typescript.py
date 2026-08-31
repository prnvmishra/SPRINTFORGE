#!/usr/bin/env python3
"""Prove the TypeScript judge grades honestly, through the real judge.

Nothing here is asserted structurally. Every claim is executed by
`LocalSubprocessProvider`, i.e. by the same `tsc --strict` compile and `node` run
a learner's submission goes through.

For every TypeScript basics problem:

  * the reference solution PASSES every case, visible and hidden — which also
    proves the TypeScript reference and the Python oracle that derived the
    expectations agree, case for case;
  * the starter FAILS (it compiles, and it does not answer the problem);
  * every registered wrong solution FAILS at least one case;
  * a `console.log` of the first case's expected output — the laziest possible
    hardcode — FAILS.

Plus three properties of the language integration itself:

  * a program with a TYPE ERROR and otherwise perfect runtime logic is rejected;
  * `ts-array-rotate` (the cross-language algorithm challenge) is solvable in
    TypeScript and its starter is not;
  * with the toolchain hidden, the judge reports "TypeScript toolchain
    unavailable" rather than marking the submission wrong.

    cd backend
    PYTHONPATH=. .venv/bin/python scripts/verify_typescript.py
    PYTHONPATH=. .venv/bin/python scripts/verify_typescript.py --problems keyof-pluck
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.data.curriculum_basics_typescript import (  # noqa: E402
    REFERENCE_SOLUTIONS,
    TYPESCRIPT_BASICS_MODULES,
    WRONG_SOLUTIONS,
)
from app.data.curriculum import graded_cases  # noqa: E402
from app.data.practice_modules import PRACTICE_MODULE_INDEX  # noqa: E402
from app.schemas.execution import TestCase  # noqa: E402
from app.services import code_execution_service as ces  # noqa: E402
from app.services.code_execution_service import (  # noqa: E402
    LocalSubprocessProvider,
    time_limit_for,
)

LANGUAGE = "typescript"


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


def _judge(source: str, cases: list[TestCase]):
    return asyncio.run(LocalSubprocessProvider().run(LANGUAGE, source, cases))


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []

    def check(self, ok: bool, label: str, detail: str = "") -> None:
        if ok:
            print(f"      ok   {label}")
            return
        self.failures.append(f"{label}{f' — {detail}' if detail else ''}")
        print(f"      FAIL {label}")
        if detail:
            for line in detail.strip().splitlines()[:6]:
                print(f"           {line}")


def _verify_problem(module: dict, report: Report) -> None:
    module_id = module["id"]
    cases = _cases(module)
    print(f"\n  {module_id}  ({len(cases)} cases)")

    result = _judge(REFERENCE_SOLUTIONS[module_id], cases)
    if result.compile_error:
        report.check(False, "reference compiles", result.compile_error)
        return
    passed = sum(1 for r in result.results if r.passed)
    detail = "; ".join(
        f"{r.name}: expected {r.expected_stdout!r} got {r.stdout!r} {r.stderr.strip()[:120]}"
        for r in result.results
        if not r.passed
    )
    report.check(
        passed == len(cases),
        f"reference passes all {len(cases)} cases "
        f"(slowest {max((r.duration_ms for r in result.results), default=0)}ms)",
        detail,
    )

    starter = _judge(module["files"]["solution"], cases)
    report.check(
        not starter.compile_error,
        "starter type-checks (a starter that cannot compile teaches nothing)",
        starter.compile_error or "",
    )
    if not starter.compile_error:
        starter_passed = sum(1 for r in starter.results if r.passed)
        report.check(
            starter_passed < len(cases),
            f"starter fails the suite ({starter_passed}/{len(cases)} passed)",
            "the starter answers the problem",
        )

    for index, candidate in enumerate(WRONG_SOLUTIONS[module_id]):
        outcome = _judge(candidate, cases)
        if outcome.compile_error:
            # A wrong answer must be *plausible*: rejected for being wrong, not
            # for failing to compile, or it proves nothing about the cases.
            report.check(
                False,
                f"wrong #{index} is a plausible submission that compiles",
                outcome.compile_error,
            )
            continue
        rejected = [r.name for r in outcome.results if not r.passed]
        report.check(
            bool(rejected),
            f"wrong #{index} rejected by {len(rejected)} case(s)"
            + (f", first: {rejected[0]}" if rejected else ""),
            "it passes every case, so a learner making that mistake is told they "
            "were right",
        )

    # The laziest false pass there is: print the first case's answer and stop.
    constant = (
        f"const answer: string = {cases[0].expected_stdout!r};\nconsole.log(answer);\n"
    ).replace("'", '"')
    outcome = _judge(constant, cases)
    hardcode_passed = 0 if outcome.compile_error else sum(
        1 for r in outcome.results if r.passed
    )
    report.check(
        hardcode_passed < len(cases),
        f"a hardcoded constant fails ({hardcode_passed}/{len(cases)} passed)",
    )


def _verify_type_errors_fail(report: Report) -> None:
    """The product decision, made testable.

    This program's *runtime* behaviour is exactly correct — it would pass every
    case if the types were erased. It must still be rejected, because on a
    platform that teaches TypeScript, a type error is a wrong answer.
    """
    print("\n  type errors fail the submission")
    module = PRACTICE_MODULE_INDEX["ts-basics-annotate-totals"]
    cases = _cases(module)

    runtime_correct_but_ill_typed = """function summarise(values: string[]): string {
  let total: string = 0;
  for (const value of values) {
    total += value;
  }
  const mean: number = total / values.length;
  return `${total} ${mean.toFixed(2)}`;
}

const tokens: string[] = require("fs")
  .readFileSync(0, "utf8")
  .split(/\\s+/)
  .filter((token: string) => token.length > 0);
const n: number = Number(tokens[0]);
const values: number[] = tokens.slice(1, 1 + n).map(Number);
console.log(summarise(values));
"""
    result = _judge(runtime_correct_but_ill_typed, cases)
    report.check(
        bool(result.compile_error),
        "a type error is reported as a compile error",
        "the judge accepted a file tsc should have rejected",
    )
    report.check(
        result.compile_error is not None and "error TS" in result.compile_error,
        "the learner is shown tsc's diagnostic",
        (result.compile_error or "")[:300],
    )
    # The false pass this guards against: no cases ran, so nothing "passed".
    report.check(
        not result.all_passed and not result.results,
        "no case is recorded as passing when the file did not compile",
    )

    # And the inverse, so the check above is not passing for the wrong reason:
    # the same program with honest annotations is accepted.
    ok = _judge(REFERENCE_SOLUTIONS["ts-basics-annotate-totals"], cases)
    report.check(
        ok.all_passed, "the well-typed version of the same program still passes"
    )


def _verify_array_rotate(report: Report) -> None:
    print("\n  ts-array-rotate  (the cross-language algorithm challenge)")
    module = PRACTICE_MODULE_INDEX["ts-array-rotate"]
    cases = _cases(module)
    solution = """function rotate(arr: number[], k: number): number[] {
  const n: number = arr.length;
  if (n === 0) {
    return arr;
  }
  const shift: number = ((k % n) + n) % n;
  return arr.slice(n - shift).concat(arr.slice(0, n - shift));
}

const data: number[] = require("fs")
  .readFileSync(0, "utf8")
  .split(/\\s+/)
  .filter((token: string) => token.length > 0)
  .map(Number);
const n: number = data[0];
const k: number = data[1];
const arr: number[] = data.slice(2, 2 + n);
console.log(rotate(arr, k).join(" "));
"""
    result = _judge(solution, cases)
    report.check(
        not result.compile_error and result.all_passed,
        f"a correct TypeScript solution passes all {len(cases)} cases",
        result.compile_error
        or "; ".join(f"{r.name}: got {r.stdout!r}" for r in result.results if not r.passed),
    )
    starter = _judge(module["files"]["solution"], cases)
    report.check(not starter.compile_error, "starter type-checks", starter.compile_error or "")
    if not starter.compile_error:
        report.check(
            not starter.all_passed,
            "the starter does not solve it",
        )


def _verify_missing_toolchain(report: Report) -> None:
    """With no toolchain, the judge must blame the host, not the learner."""
    print("\n  missing toolchain reports clearly")
    module = PRACTICE_MODULE_INDEX["ts-basics-annotate-totals"]
    cases = _cases(module)

    original = ces._typescript_toolchain
    ces._typescript_toolchain = lambda: None  # type: ignore[assignment]
    try:
        result = _judge(REFERENCE_SOLUTIONS[module["id"]], cases)
    finally:
        ces._typescript_toolchain = original  # type: ignore[assignment]

    report.check(
        result.supported is False,
        "the result is marked unsupported, so the submission is not graded",
    )
    report.check(
        bool(result.compile_error)
        and "TypeScript toolchain unavailable" in result.compile_error,
        "the message names the missing toolchain",
        (result.compile_error or "")[:300],
    )
    report.check(
        not result.results and not result.all_passed,
        "no case is marked failed, so a broken host is not recorded as a wrong answer",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--problems",
        nargs="*",
        default=None,
        help="slugs to verify (default: all)",
    )
    args = parser.parse_args()

    print(f"=== typescript  (time limit {time_limit_for(LANGUAGE):.0f}s) ===")
    toolchain = ces._typescript_toolchain()
    if toolchain is None:
        print(
            "no TypeScript toolchain on this host. Run: cd backend && npm install"
        )
        return 1
    node, tsc, type_roots = toolchain
    print(f"node:      {node}")
    print(f"tsc:       {tsc}")
    print(f"typeRoots: {type_roots}")

    report = Report()
    modules = TYPESCRIPT_BASICS_MODULES
    if args.problems:
        wanted = {f"ts-basics-{slug}" for slug in args.problems}
        modules = [m for m in modules if m["id"] in wanted]
        if not modules:
            print(f"no problem matched {args.problems}")
            return 1
    for module in modules:
        _verify_problem(module, report)

    if not args.problems:
        _verify_type_errors_fail(report)
        _verify_array_rotate(report)
        _verify_missing_toolchain(report)

    print()
    if report.failures:
        print(f"FAIL: {len(report.failures)} check(s)")
        for line in report.failures:
            print(f"  - {line}")
        return 1
    print(
        f"OK: {len(modules)} TypeScript problem(s) verified through the real judge — "
        "references pass, starters fail, every wrong answer is caught, type errors "
        "are rejected, and a missing toolchain is reported rather than failed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
