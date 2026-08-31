"""Derives the runtime case store from the built bank.

``generated_cases.json`` is the *authoring* artifact: one 197MB file that
``build_test_cases.py`` writes and the verify scripts merge into. Loading it at
import cost 580MB of peak memory and 14 seconds, because the whole bank is
parsed just to reach the handful of cases each module needs. That is what kept
the API off every free hosting tier, whose ceiling is 512MB.

Almost all of that weight is a few enormous hidden scale cases — the largest
single case is 6.9MB — and those are needed only when grading a submission.
The 280 visible cases together come to well under a megabyte.

So the runtime store splits along that line:

``cases/visible.json``
    Every visible case plus a hidden count, for all slugs. Tiny, read once at
    import, which is all the listing and detail screens ever need.

``cases/hidden/<slug>.json.gz``
    That slug's hidden cases, gzipped — 189MB of generated digits and text
    halves to 80MB, and this is the artifact a deployment has to carry. Read
    only when a submission for that slug is graded, and cached with a bounded
    LRU so memory stays flat.

This is a pure re-serialisation: no case is regenerated, reordered or altered,
so what a learner is graded against is byte-for-byte what it was before.

    python -m scripts.split_case_bank            # write the store
    python -m scripts.split_case_bank --check    # verify it matches the bank
"""

from __future__ import annotations

import argparse
import gzip
import json
import pathlib
import shutil
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]

# Deliberately not importing app.data.curriculum, which is the consumer of the
# store this script writes: it reads the store at import, so it cannot be loaded
# before the store exists. Same reason build_test_cases.py duplicates the
# problem list. These four paths must stay in step with that module.
_DATA = _ROOT / "app" / "data"
GENERATED_CASES_PATH = _DATA / "generated_cases.json"
CASES_VISIBLE_PATH = _DATA / "cases" / "visible.json"
CASES_HIDDEN_DIR = _DATA / "cases" / "hidden"
HIDDEN_SUFFIX = ".json.gz"


def build_store(bank: dict) -> tuple[dict, dict[str, list]]:
    """Partition the bank into the visible manifest and per-slug hidden lists."""
    visible: dict[str, dict] = {}
    hidden: dict[str, list] = {}
    for slug, entry in sorted(bank.items()):
        cases = entry.get("cases", [])
        slug_hidden = [c for c in cases if c.get("hidden")]
        visible[slug] = {
            "visible": [c for c in cases if not c.get("hidden")],
            "hidden_count": len(slug_hidden),
        }
        hidden[slug] = slug_hidden
    return visible, hidden


def _dump(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def write_store(visible: dict, hidden: dict[str, list]) -> None:
    # Replaced rather than merged: a slug deleted from the bank must not leave a
    # stale hidden file behind that would still be graded against.
    if CASES_HIDDEN_DIR.exists():
        shutil.rmtree(CASES_HIDDEN_DIR)
    CASES_HIDDEN_DIR.mkdir(parents=True)
    CASES_VISIBLE_PATH.write_text(_dump(visible))
    for slug, cases in hidden.items():
        path = CASES_HIDDEN_DIR / f"{slug}{HIDDEN_SUFFIX}"
        # mtime zeroed so the same bank produces byte-identical files, which is
        # what lets `--check` compare them at all.
        with gzip.GzipFile(path, "wb", compresslevel=6, mtime=0) as handle:
            handle.write(_dump(cases).encode())


def check_store(visible: dict, hidden: dict[str, list]) -> list[str]:
    problems: list[str] = []
    if not CASES_VISIBLE_PATH.exists():
        return [f"{CASES_VISIBLE_PATH.name} is missing"]
    if json.loads(CASES_VISIBLE_PATH.read_text()) != visible:
        problems.append(f"{CASES_VISIBLE_PATH.name} does not match the bank")
    for slug, cases in hidden.items():
        path = CASES_HIDDEN_DIR / f"{slug}{HIDDEN_SUFFIX}"
        if not path.exists():
            problems.append(f"hidden/{slug}{HIDDEN_SUFFIX} is missing")
        else:
            with gzip.open(path, "rb") as handle:
                # Compared as parsed data, not bytes: a different zlib build
                # would otherwise report every file stale for no real reason.
                if json.load(handle) != cases:
                    problems.append(
                        f"hidden/{slug}{HIDDEN_SUFFIX} does not match the bank"
                    )
    if CASES_HIDDEN_DIR.exists():
        for stale in sorted(CASES_HIDDEN_DIR.glob(f"*{HIDDEN_SUFFIX}")):
            if stale.name.removesuffix(HIDDEN_SUFFIX) not in hidden:
                problems.append(f"hidden/{stale.name} is not in the bank")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the store matches the bank without writing",
    )
    args = parser.parse_args()

    if not GENERATED_CASES_PATH.exists():
        print(
            f"{GENERATED_CASES_PATH.name} is missing. "
            "Run: python -m scripts.build_test_cases",
            file=sys.stderr,
        )
        return 1

    with GENERATED_CASES_PATH.open("rb") as handle:
        bank = json.load(handle)
    visible, hidden = build_store(bank)

    if args.check:
        problems = check_store(visible, hidden)
        if problems:
            print("The runtime case store is stale:", file=sys.stderr)
            for problem in problems:
                print(f"  - {problem}", file=sys.stderr)
            print("\nRun: python -m scripts.split_case_bank", file=sys.stderr)
            return 1
        print(f"OK: store matches the bank ({len(hidden)} slugs)")
        return 0

    write_store(visible, hidden)
    n_visible = sum(len(v["visible"]) for v in visible.values())
    n_hidden = sum(len(c) for c in hidden.values())
    print(
        f"Wrote {len(visible)} slugs: {n_visible} visible cases into "
        f"{CASES_VISIBLE_PATH.name} ({CASES_VISIBLE_PATH.stat().st_size / 1e6:.1f}MB), "
        f"{n_hidden} hidden cases into {CASES_HIDDEN_DIR.name}/"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
