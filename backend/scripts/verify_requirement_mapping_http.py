"""Prove over live HTTP that the requirements panel agrees with the grader.

Runs MTB-10's stored workspace through POST /tickets/{id}/run on the running
server, then applies the requirement mapping exactly as the browser does and
prints the resulting "N/M met" ratio next to the grader's own check tally.

Read-only with respect to grading: /run awards no XP and changes no status.

    python scripts/verify_requirement_mapping_http.py [--key MTB-10] [--base http://127.0.0.1:8000]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models import Ticket


def derive_rows(requirements: list[str], checks: list[dict]) -> list[tuple[str, str, list[str]]]:
    """Mirrors matchRequirements() for checks that declare their mapping."""
    owners: dict[int, list[dict]] = {}
    for check in checks:
        if check.get("precondition"):
            continue
        indexes = check.get("requirement_indexes")
        if indexes is None:
            single = check.get("requirement_index")
            indexes = [single] if isinstance(single, int) else []
        for index in indexes:
            if 0 <= index < len(requirements):
                owners.setdefault(index, []).append(check)

    all_passed = bool(checks) and all(c["passed"] for c in checks)
    rows = []
    for index, requirement in enumerate(requirements):
        owned = owners.get(index, [])
        if not owned:
            status = "ungraded"
        elif all_passed or all(c["passed"] for c in owned):
            status = "passed"
        else:
            status = "failed"
        rows.append((requirement, status, [c["id"] for c in owned]))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", default="MTB-10")
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    with SessionLocal() as db:
        ticket = db.scalars(select(Ticket).where(Ticket.key == args.key)).first()
        if ticket is None:
            print(f"no ticket {args.key}")
            return 1
        ticket_id = ticket.id
        requirements = list(ticket.requirements or [])
        files = dict(ticket.workspace_files or {})
        status_before = ticket.status
        user_id = ticket.sprint.project.user_id

    token = create_access_token(user_id)
    response = httpx.post(
        f"{args.base}/tickets/{ticket_id}/run",
        json={"files": files},
        headers={"Authorization": f"Bearer {token}"},
        timeout=120,
    )
    print(f"POST /tickets/{{id}}/run -> HTTP {response.status_code}")
    response.raise_for_status()
    body = response.json()

    checks = list(body.get("static_results", [])) + list(body.get("test_results", []))
    print(f"\ngrader: {sum(1 for c in checks if c['passed'])}/{len(checks)} checks passed\n")
    print(f"{'check':<16}{'pass':<7}{'req':<10}{'precondition':<14}label")
    for check in checks:
        pointer = check.get("requirement_indexes") or check.get("requirement_index")
        print(
            f"{check['id']:<16}{str(check['passed']):<7}{str(pointer):<10}"
            f"{str(bool(check.get('precondition'))):<14}{check['label']}"
        )

    rows = derive_rows(requirements, checks)
    graded = [r for r in rows if r[1] != "ungraded"]
    met = sum(1 for r in graded if r[1] == "passed")
    print(f"\nrequirements panel: {met}/{len(graded)} met"
          f"{f' ({len(rows) - len(graded)} not graded)' if len(rows) != len(graded) else ''}")
    for index, (requirement, status, ids) in enumerate(rows):
        print(f"  {index:02d} {status:<9}{','.join(ids) or '-':<28}{requirement}")

    with SessionLocal() as db:
        after = db.scalars(select(Ticket).where(Ticket.key == args.key)).first()
        assert after is not None
        print(f"\nstatus: {status_before} -> {after.status} (unchanged)")
        if after.status != status_before:
            return 1

    contradiction = all(c["passed"] for c in checks) and met != len(graded)
    print("\nOK" if not contradiction else "\nFAIL: panel contradicts the grader")
    return 1 if contradiction else 0


if __name__ == "__main__":
    raise SystemExit(main())
