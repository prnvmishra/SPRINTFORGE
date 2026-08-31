#!/usr/bin/env python3
"""Generate and verify the competitive-programming test suites.

Run from the backend directory:

    python -m scripts.build_test_cases          # regenerate + verify
    python -m scripts.build_test_cases --check  # verify only, no write (CI)

Three guarantees are enforced, and any failure aborts the build:

1. **Expected outputs are derived, not typed.** Every ``expected_stdout`` comes
   from executing the problem's reference solution, so a stale or mistyped
   answer cannot enter the bank.
2. **The reference is self-consistent.** It is executed twice per case and must
   agree with itself, which catches accidental non-determinism (unseeded
   randomness, set iteration order leaking into output).
3. **Wrong solutions must fail.** Each declared broken solution must fail at
   least one case. This is the check that makes "koi bhi code se saare test
   case pass na ho" a build-time property instead of a hope: if a bug survives
   the whole suite, the suite is too weak and the build tells us so.

Output: ``app/data/generated_cases.json``, consumed by ``app/data/curriculum.py``.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.data.curriculum_basics_c import PROBLEMS as _BASICS_C  # noqa: E402
from app.data.curriculum_basics_cpp import PROBLEMS as _BASICS_CPP  # noqa: E402
from app.data.curriculum_basics_java import PROBLEMS as _BASICS_JAVA  # noqa: E402
from app.data.curriculum_basics_python import PROBLEMS as _BASICS_PYTHON  # noqa: E402
from app.data.curriculum_blind75_1 import PROBLEMS as _BLIND75_1  # noqa: E402
from app.data.curriculum_blind75_2 import PROBLEMS as _BLIND75_2  # noqa: E402
from app.data.curriculum_blind75_3 import PROBLEMS as _BLIND75_3  # noqa: E402
from app.data.curriculum_blind75_4 import PROBLEMS as _BLIND75_4  # noqa: E402
from app.data.curriculum_cp import CP_PROBLEMS as _CP_PROBLEMS  # noqa: E402

# Mirrors the concatenation in app/data/curriculum.py, but without importing
# that module: it loads generated_cases.json at import time, which is exactly
# the file this script produces.
CP_PROBLEMS = [
    *_BASICS_C,
    *_BASICS_CPP,
    *_BASICS_JAVA,
    *_BASICS_PYTHON,
    *_CP_PROBLEMS,
    *_BLIND75_1,
    *_BLIND75_2,
    *_BLIND75_3,
    *_BLIND75_4,
]

OUTPUT_PATH = pathlib.Path(__file__).resolve().parents[1] / "app" / "data" / "generated_cases.json"

# Reference solutions get a generous ceiling; the point of the scale cases is to
# separate O(n) from O(n^2), and this bound is what a quadratic attempt blows.
REFERENCE_TIMEOUT = 30.0
CANDIDATE_TIMEOUT = 10.0


class ExecutionFailure(RuntimeError):
    pass


def run_python(source: str, stdin: str, timeout: float) -> tuple[str, float]:
    """Execute `source` with `stdin`, returning (trimmed stdout, seconds)."""
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
        except subprocess.TimeoutExpired as exc:
            raise ExecutionFailure(f"timed out after {timeout}s") from exc
        elapsed = time.monotonic() - started
        if proc.returncode != 0:
            raise ExecutionFailure((proc.stderr or "non-zero exit").strip()[:500])
        return proc.stdout.strip(), elapsed


def try_run(source: str, stdin: str, timeout: float) -> tuple[bool, str]:
    """Like `run_python` but converts failure into a sentinel instead of raising.

    A crash or timeout counts as a wrong answer, which is what we want when
    grading a candidate: a brute force that cannot finish has not solved it.
    """
    try:
        stdout, _ = run_python(source, stdin, timeout)
        return True, stdout
    except ExecutionFailure as exc:
        return False, str(exc)


def build_problem(problem: dict) -> dict:
    slug = problem["slug"]
    reference = problem["reference"]
    cases = []

    print(f"\n  {slug}")
    for spec in problem["inputs"]:
        stdin = spec["stdin"]
        try:
            expected, elapsed = run_python(reference, stdin, REFERENCE_TIMEOUT)
        except ExecutionFailure as exc:
            raise SystemExit(
                f"FAIL [{slug}] reference crashed on case '{spec['name']}': {exc}"
            )

        # Guarantee 2: the reference must agree with itself.
        repeat, _ = run_python(reference, stdin, REFERENCE_TIMEOUT)
        if repeat != expected:
            raise SystemExit(
                f"FAIL [{slug}] reference is non-deterministic on '{spec['name']}': "
                f"{expected!r} then {repeat!r}"
            )

        cases.append(
            {
                "name": spec["name"],
                "stdin": stdin,
                "expected_stdout": expected,
                "hidden": bool(spec["hidden"]),
                "match": spec.get("match", "trimmed"),
            }
        )
        shown = expected if len(expected) <= 40 else expected[:37] + "..."
        print(f"    ok  {spec['name']:32} -> {shown!r}  ({elapsed * 1000:.0f}ms)")

    # Guarantee 3: every declared wrong solution must be caught by the suite.
    for index, wrong in enumerate(problem.get("wrong", []), start=1):
        caught_by = None
        for case in cases:
            ok, got = try_run(wrong, case["stdin"], CANDIDATE_TIMEOUT)
            if not ok or got != case["expected_stdout"]:
                caught_by = case["name"]
                break
        if caught_by is None:
            raise SystemExit(
                f"FAIL [{slug}] wrong solution #{index} passed every case. "
                "The suite is too weak — add a discriminating hidden case."
            )
        print(f"    caught wrong #{index} via {caught_by!r}")

    return {
        "slug": slug,
        "cases": cases,
        "visible": sum(1 for c in cases if not c["hidden"]),
        "hidden": sum(1 for c in cases if c["hidden"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify only; fail if the committed file differs from a fresh build",
    )
    parser.add_argument(
        "--only",
        metavar="PREFIX",
        help=(
            "rebuild just the problems whose slug starts with PREFIX and merge the "
            "result into the existing file. A full run rebuilds every problem "
            "(~7 minutes) and re-derives 130MB of unchanged cases; this is for "
            "iterating on one batch. The output is byte-identical to a full run as "
            "long as the rest of the file was already up to date, which --check "
            "still verifies."
        ),
    )
    args = parser.parse_args()

    problems = CP_PROBLEMS
    if args.only:
        problems = [p for p in CP_PROBLEMS if p["slug"].startswith(args.only)]
        if not problems:
            print(f"FAIL no problem slug starts with {args.only!r}")
            return 1

    print(f"Building test suites for {len(problems)} problems")
    built = {problem["slug"]: build_problem(problem) for problem in problems}

    if args.only:
        existing = json.loads(OUTPUT_PATH.read_text()) if OUTPUT_PATH.exists() else {}
        existing.update(built)
        built = existing

    payload = json.dumps(built, indent=2, sort_keys=True) + "\n"

    if args.check:
        if not OUTPUT_PATH.exists():
            print(f"\nFAIL {OUTPUT_PATH.name} is missing; run without --check")
            return 1
        if OUTPUT_PATH.read_text() != payload:
            print(f"\nFAIL {OUTPUT_PATH.name} is stale; run without --check")
            return 1
        print(f"\nOK {OUTPUT_PATH.name} is up to date")
        return 0

    OUTPUT_PATH.write_text(payload)
    total_visible = sum(entry["visible"] for entry in built.values())
    total_hidden = sum(entry["hidden"] for entry in built.values())
    print(
        f"\nWrote {OUTPUT_PATH.relative_to(OUTPUT_PATH.parents[2])}: "
        f"{len(built)} problems, {total_visible} visible + {total_hidden} hidden cases"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
