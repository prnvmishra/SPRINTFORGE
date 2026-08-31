"""Report every unresolved template placeholder — in the templates and in the DB.

Read-only. Writes nothing, ever, so it is safe to run against the live database
(see .cursor/rules/learner-data-is-sacred.mdc).

Three sections:

  templates  every skill whose template strings carry a placeholder, and in
             which fields, so the blast radius is visible beyond CSS selectors.
  stored     every ticket whose stored `validation_spec`, requirements or
             acceptance criteria still contain one — i.e. the tickets that would
             grade a learner against `#{entity}List`.
  matchers   the subset of the above that reaches a selector engine, which is
             the set that produces "invalid selector".

    PYTHONPATH=. .venv/bin/python scripts/audit_spec_placeholders.py
    PYTHONPATH=. .venv/bin/python scripts/audit_spec_placeholders.py --templates-only
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.data.ticket_templates import STARTER_FILES, TICKET_TEMPLATES
from app.models import Ticket
from app.services.spec_interpolation import (
    PLACEHOLDER_NAMES,
    _PLACEHOLDER_RE,
    selector_leak,
)
from app.services.validation_service import _SELECTOR_FIELDS


def walk(value: Any, path: str = "") -> Iterator[tuple[str, str, str]]:
    """(path, placeholder name, surrounding text) for every placeholder inside."""
    if isinstance(value, str):
        for name in dict.fromkeys(_PLACEHOLDER_RE.findall(value)):
            yield path, name, " ".join(value.split())[:100]
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk(item, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from walk(item, f"{path}.{key}" if path else str(key))


def audit_templates() -> None:
    print("=" * 78)
    print(f"TEMPLATES — {len(TICKET_TEMPLATES)} skills, placeholders {sorted(PLACEHOLDER_NAMES)}")
    print("=" * 78)
    by_skill: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for skill, templates in TICKET_TEMPLATES.items():
        for template in templates:
            for path, name, _text in walk(template):
                # Collapse list indices so the report names fields, not positions.
                field = path.split("[")[0]
                by_skill[skill][field].add(name)
    for skill in sorted(by_skill):
        fields = by_skill[skill]
        print(f"\n{skill}")
        for field in sorted(fields):
            print(f"    {field:<44} {sorted(fields[field])}")
    print(f"\nskills carrying placeholders: {len(by_skill)} of {len(TICKET_TEMPLATES)}")

    starter = {
        name: sorted({n for _p, n, _t in walk(body)})
        for name, body in STARTER_FILES.items()
        if any(True for _ in walk(body))
    }
    print("\nstarter files carrying placeholders:")
    for name in sorted(starter):
        print(f"    {name:<20} {starter[name]}")


def audit_stored(templates_only: bool = False) -> int:
    if templates_only:
        return 0
    print("\n" + "=" * 78)
    print("STORED TICKETS")
    print("=" * 78)
    offenders = 0
    with SessionLocal() as db:
        tickets = db.scalars(select(Ticket)).all()
        for ticket in sorted(tickets, key=lambda t: (t.sprint.project.title, t.order_index)):
            findings = [
                *walk(ticket.validation_spec or {}, "validation_spec"),
                *walk(ticket.requirements or [], "requirements"),
                *walk(ticket.acceptance_criteria or [], "acceptance_criteria"),
            ]
            if not findings:
                continue
            offenders += 1
            matchers = [
                (path, name, text)
                for path, name, text in findings
                if path.rsplit(".", 1)[-1] in _SELECTOR_FIELDS
            ]
            print(
                f"\n{ticket.key:<8} {ticket.status:<12} {ticket.target_skill_id:<22} "
                f"project={ticket.sprint.project.title!r}"
            )
            print(f"         ticket id: {ticket.id}")
            for path, name, text in findings:
                reaches = " <-- REACHES A SELECTOR ENGINE" if (path, name, text) in matchers else ""
                print(f"    {{{name}}} at {path}{reaches}\n        {text}")
        print(
            f"\n{offenders} of {len(tickets)} stored ticket(s) carry an unresolved placeholder."
        )
    return offenders


def audit_matchers() -> None:
    """Template checks whose selector fields would be rejected by the guard."""
    print("\n" + "=" * 78)
    print("TEMPLATE CHECKS WHOSE SELECTOR WOULD BE REJECTED AT MATCH TIME")
    print("=" * 78)
    total = 0
    for skill, templates in sorted(TICKET_TEMPLATES.items()):
        for template in templates:
            for check in template.get("checks", []) or []:
                for field in _SELECTOR_FIELDS:
                    leak = selector_leak(check.get(field))
                    if leak:
                        total += 1
                        print(f"    {skill:<22} {check.get('id'):<26} {field}={check[field]!r}")
    print(f"\n{total} selector field(s) in the templates carry a placeholder.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--templates-only", action="store_true", help="skip the database")
    args = parser.parse_args()
    audit_templates()
    audit_matchers()
    audit_stored(args.templates_only)
    print("\nThis script wrote nothing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
