"""Grade a ticket exactly the way the Run Checks button does. Read-only.

Uses `ticket_service.render_bundle_for` for the read-only page context and
`validation_service.run_static_checks(files, checks, render_files=...)` on the
learner's stored workspace — the same two calls the API endpoint makes — and
prints the per-check verdict plus the requirement tally.

Writes nothing: no save_workspace, no status change, no attempt row.

    PYTHONPATH=. .venv/bin/python scripts/run_mtb4_real_path.py --key MTB-4
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Ticket
from app.services.ticket_service import render_bundle_for
from app.services.validation_service import run_static_checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", default="MTB-4")
    parser.add_argument("--status", default=None, help="only the row in this status")
    args = parser.parse_args()

    with SessionLocal() as db:
        tickets = db.scalars(select(Ticket).where(Ticket.key == args.key)).all()
        if args.status:
            tickets = [t for t in tickets if t.status == args.status]
        for ticket in tickets:
            checks = (ticket.validation_spec or {}).get("checks", []) or []
            files = ticket.workspace_files or {}
            provided = render_bundle_for(db, ticket)
            print("=" * 78)
            print(f"{ticket.key}  status={ticket.status}  id={ticket.id}")
            print(f"  workspace: { {k: len(v or '') for k, v in files.items()} }")
            print(f"  provided:  {sorted(provided)}")
            print(f"  checks:    {len(checks)}")
            outcomes = run_static_checks(files, checks, render_files=provided)
            for outcome in outcomes:
                mark = "PASS" if outcome.passed else ("CONFIG" if outcome.config_error else "FAIL")
                print(f"  [{mark:<6}] {outcome.id:<26} {outcome.label}")
                if not outcome.passed:
                    print(f"            {outcome.detail}")
            passed = sum(1 for o in outcomes if o.passed)
            config = [o.id for o in outcomes if o.config_error]
            print(f"\n  tally: {passed}/{len(outcomes)} checks passed")
            print(f"  validator configuration errors: {config or 'none'}")

            requirements = ticket.requirements or []
            owned: dict[int, list] = {}
            for outcome in outcomes:
                if outcome.precondition:
                    continue
                for index in outcome.requirement_indexes or (
                    [outcome.requirement_index] if outcome.requirement_index is not None else []
                ):
                    owned.setdefault(index, []).append(outcome)
            met = 0
            for index, requirement in enumerate(requirements):
                checks_for = owned.get(index, [])
                if not checks_for:
                    state = "not graded"
                elif all(o.passed for o in checks_for):
                    state = "met"
                    met += 1
                else:
                    state = "UNMET"
                print(f"  req[{index}] {state:<11} {requirement[:88]}")
            graded = sum(1 for i in range(len(requirements)) if owned.get(i))
            print(f"\n  requirements: {met}/{graded} met ({len(requirements)} total)")
    print("\nThis script wrote nothing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
