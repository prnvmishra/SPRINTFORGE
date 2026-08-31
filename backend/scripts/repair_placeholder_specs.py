"""Resolve the `{placeholder}` leaks inside stored `validation_spec` rows.

Scope, deliberately narrow:

* Status, completed_at, XP, reward rows, attempt history, workspace files and
  starter files are never read for writing and never written.
* `validation_spec` is repaired by default. The brief (`requirements`,
  `acceptance_criteria`) is repaired only with `--include-brief`, because it
  changes what the learner is *shown*. Both need the owner's approval before
  `--apply`; see .cursor/rules/learner-data-is-sacred.mdc.
* Tickets are selected with `--key`, or with `--all` to sweep every row that
  carries a leak. `--all` reports by default like everything else here.
* The stored checks are *interpolated*, not regenerated from today's template.
  The learner keeps being graded by the same checks they already had; the only
  difference is that `#{entity}List` becomes `#movieList`.

Nothing is written without `--apply`, and `--apply` first writes a JSON snapshot
of the previous specs so the change can be reversed exactly.

    PYTHONPATH=. .venv/bin/python scripts/repair_placeholder_specs.py --key MTB-4 --key MTB-5
    PYTHONPATH=. .venv/bin/python scripts/repair_placeholder_specs.py --key MTB-4 --key MTB-5 --apply
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Ticket
from app.services.spec_interpolation import (
    context_for_ticket,
    fill,
    unresolved_placeholders,
)

SNAPSHOT_DIR = Path(__file__).resolve().parents[1] / "uploads" / "spec_snapshots"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--key",
        action="append",
        default=[],
        help="ticket key to repair; repeatable. Every ticket row with this key is included.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="consider every stored ticket, not just the ones named with --key.",
    )
    parser.add_argument(
        "--include-brief",
        action="store_true",
        help="also resolve placeholders in requirements/acceptance_criteria "
        "(changes what the learner reads).",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    keys = list(dict.fromkeys(args.key))
    if not keys and not args.all:
        parser.error("pass --key KEY (repeatable) or --all")

    with SessionLocal() as db:
        statement = select(Ticket) if args.all else select(Ticket).where(Ticket.key.in_(keys))
        tickets = db.scalars(statement).all()
        if not tickets:
            print(f"No ticket matches {keys or 'the whole table'}.")
            return 1

        snapshot: list[dict] = []
        repairs = 0
        brief_repairs = 0
        for ticket in sorted(tickets, key=lambda t: (t.key, t.id)):
            spec = ticket.validation_spec or {}
            leaked = unresolved_placeholders(spec)
            brief_leaks = unresolved_placeholders(
                {"requirements": ticket.requirements, "acceptance": ticket.acceptance_criteria}
            )
            if args.all and not leaked and not brief_leaks:
                continue
            context = context_for_ticket(ticket)
            print(
                f"\n{ticket.key}  status={ticket.status}  skill={ticket.target_skill_id}  "
                f"id={ticket.id}"
            )
            print(f"    project: {ticket.sprint.project.title!r}")
            print(f"    context: {context}")
            if not leaked:
                print("    validation_spec is already free of placeholders — nothing to do.")

            repaired = fill(spec, context, strict=True) if leaked else spec
            for index, (before, after) in enumerate(
                zip(spec.get("checks", []) or [], repaired.get("checks", []) or [])
            ):
                if before == after:
                    continue
                changed = {k: (before.get(k), after.get(k)) for k in after if before.get(k) != after.get(k)}
                print(f"    checks[{index}] {after.get('id')}")
                for field, (old, new) in changed.items():
                    print(f"        {field}: {old!r} -> {new!r}")
            entry: dict[str, Any] = {"ticket_id": ticket.id, "key": ticket.key}
            if leaked:
                entry["validation_spec"] = spec
                repairs += 1
                if args.apply:
                    ticket.validation_spec = repaired

            if brief_leaks:
                # The brief and the checks must resolve from the *same* context,
                # or the requirement a learner reads and the selector it is
                # graded by can name different things.
                new_requirements = fill(ticket.requirements or [], context, strict=True)
                new_criteria = fill(ticket.acceptance_criteria or [], context, strict=True)
                for label, old, new in (
                    ("requirements", ticket.requirements or [], new_requirements),
                    ("acceptance_criteria", ticket.acceptance_criteria or [], new_criteria),
                ):
                    for index, (before_line, after_line) in enumerate(zip(old, new)):
                        if before_line != after_line:
                            print(f"    {label}[{index}]: {before_line!r} -> {after_line!r}")
                if args.include_brief:
                    entry["requirements"] = list(ticket.requirements or [])
                    entry["acceptance_criteria"] = list(ticket.acceptance_criteria or [])
                    brief_repairs += 1
                    if args.apply:
                        ticket.requirements = new_requirements
                        ticket.acceptance_criteria = new_criteria
                else:
                    print(
                        f"    NOTE: the brief carries {brief_leaks}. Not touched — "
                        "pass --include-brief to resolve what the learner reads."
                    )

            if len(entry) > 2:
                snapshot.append(entry)

        print(
            f"\n{repairs} ticket(s) would have validation_spec rewritten; "
            f"{brief_repairs} would have their brief rewritten."
        )
        if not args.apply:
            print("Dry run. Nothing was written. Re-run with --apply.")
            return 0

        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = SNAPSHOT_DIR / f"validation_spec_before_{stamp}.json"
        path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        db.commit()
        print(
            f"Applied to {repairs} spec(s) and {brief_repairs} brief(s). "
            f"Previous values snapshotted at:\n  {path}"
        )
        print("Nothing else was written: no status, XP, reward, attempt or file changes.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
