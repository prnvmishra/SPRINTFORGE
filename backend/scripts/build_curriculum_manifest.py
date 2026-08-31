"""Writes the practice-module manifest the API serves.

:mod:`app.data.curriculum_source` builds the modules, but importing it costs
about ten seconds and a few hundred megabytes because the problem sets generate
their scale inputs from a seeded RNG at import. Paying that once here, and
writing the result to ``app/data/cases/modules.json``, is what lets the API boot
in well under a second.

The manifest carries only what a client may see: statements, constraints,
examples, starters and the *visible* cases. Reference solutions, wrong
solutions and hidden cases are not in it.

Run after any change to a problem's statement, ``io`` spec or visible cases:

    python -m scripts.build_curriculum_manifest
    python -m scripts.build_curriculum_manifest --check   # CI: verify only

Requires the case store, so the full sequence from a clean checkout is:

    python -m scripts.build_test_cases
    python -m scripts.split_case_bank
    python -m scripts.build_curriculum_manifest
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from app.data.curriculum import CURRICULUM_MANIFEST_PATH  # noqa: E402
from app.data.curriculum_source import build_cp_modules  # noqa: E402

#: Fields that must never reach a client. Asserted rather than assumed: this
#: script is the only thing standing between the source problems, which do hold
#: reference solutions, and a file the API serves verbatim.
FORBIDDEN_KEYS = frozenset({"reference", "wrong", "solution_code", "io"})


def check_no_solutions(modules: list[dict]) -> None:
    for module in modules:
        leaked = FORBIDDEN_KEYS & set(module)
        if leaked:
            raise RuntimeError(
                f"{module['id']}: manifest would publish {sorted(leaked)}"
            )
        for case in module.get("test_cases", []):
            if case.get("hidden"):
                raise RuntimeError(
                    f"{module['id']}: a hidden case reached the manifest"
                )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the manifest is up to date without writing",
    )
    args = parser.parse_args()

    modules = build_cp_modules()
    check_no_solutions(modules)
    payload = json.dumps(modules, indent=2, sort_keys=True) + "\n"

    if args.check:
        if not CURRICULUM_MANIFEST_PATH.exists():
            print("modules.json is missing.", file=sys.stderr)
            return 1
        if CURRICULUM_MANIFEST_PATH.read_text() != payload:
            print(
                "modules.json is stale. Run: "
                "python -m scripts.build_curriculum_manifest",
                file=sys.stderr,
            )
            return 1
        print(f"OK: manifest matches the curriculum ({len(modules)} modules)")
        return 0

    CURRICULUM_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    CURRICULUM_MANIFEST_PATH.write_text(payload)
    print(
        f"Wrote {len(modules)} modules to {CURRICULUM_MANIFEST_PATH.name} "
        f"({CURRICULUM_MANIFEST_PATH.stat().st_size / 1e6:.1f}MB)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
