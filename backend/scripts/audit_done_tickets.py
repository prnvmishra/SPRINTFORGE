"""Re-grade every completed ticket with the current strict validator.

Tickets completed before the AST-based validator landed may have passed under
the old permissive regex checks. This re-runs today's static checks against the
stored workspace files and reports which ones would no longer pass.

Read-only: nothing is written. Use scripts/reset_false_pass.py to act on the
findings.

    python scripts/audit_done_tickets.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.database import SessionLocal
from app.models import Project, Sprint, Ticket
from app.services.validation_service import run_static_checks


async def main() -> int:
    with SessionLocal() as db:
        tickets = db.scalars(
            select(Ticket)
            .options(joinedload(Ticket.sprint).joinedload(Sprint.project).joinedload(Project.user))
            .where(Ticket.status == "done")
            .order_by(Ticket.created_at)
        ).all()

        print(f"completed tickets: {len(tickets)}\n")
        if not tickets:
            return 0

        false_passes: list[tuple[Ticket, int, int, list[str]]] = []

        for ticket in tickets:
            files = ticket.workspace_files or {}
            checks = (ticket.validation_spec or {}).get("checks", [])
            if not checks:
                print(f"  {ticket.key:<8} {ticket.title[:44]:<44} no checks defined — skipped")
                continue

            results = [r.to_dict() for r in run_static_checks(files, checks)]
            passed = sum(1 for r in results if r["passed"])
            total = len(results)
            failing = [r["label"] for r in results if not r["passed"]]

            verdict = "OK" if passed == total else "WOULD FAIL"
            print(f"  {ticket.key:<8} {ticket.title[:44]:<44} {passed}/{total}  {verdict}")
            if passed != total:
                false_passes.append((ticket, passed, total, failing))

        print()
        if not false_passes:
            print("Every completed ticket still passes the strict validator.")
            return 0

        print(f"{len(false_passes)} ticket(s) would no longer pass:\n")
        for ticket, passed, total, failing in false_passes:
            project = ticket.sprint.project if ticket.sprint else None
            owner = project.user.name if project and project.user else "?"
            print(f"  {ticket.key} — {ticket.title}")
            print(f"    id:      {ticket.id}")
            print(f"    project: {project.title if project else '?'} (owner: {owner})")
            print(f"    checks:  {passed}/{total}")
            print(f"    xp:      {ticket.xp_reward}")
            for label in failing:
                print(f"      FAIL  {label}")
            print()

        print("Read-only audit. Nothing was changed.")
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
