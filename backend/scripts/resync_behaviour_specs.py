"""Copy today's template validation_spec onto existing tickets.

Ticket specs are snapshotted at generation time, so fixing a template does not
reach tickets that already exist. This script re-syncs those snapshots and
nothing else: it never touches a ticket's status, XP, workspace or brief, which
is what distinguishes it from scripts/reset_false_pass.py.

By default it only considers skills whose template ships a layer-2 behaviour
spec, since that is the layer that changed.

    python scripts/resync_behaviour_specs.py
    python scripts/resync_behaviour_specs.py --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.data.ticket_templates import TICKET_TEMPLATES
from app.models import Ticket
from app.services.spec_interpolation import build_validation_spec, context_for_ticket
from scripts.reset_false_pass import template_spec


def skills_with_behaviour() -> set[str]:
    return {
        skill
        for skill, templates in TICKET_TEMPLATES.items()
        if any(t.get("behaviour", {}).get("assertions") for t in templates)
    }


#: Fields that declare which requirement a check grades. Copying only these
#: leaves a ticket graded by the spec it already had, so `--map-requirements` can
#: fix the requirement mapping without re-grading anything.
MAPPING_FIELDS = ("requirement_index", "requirement_indexes", "precondition")


def _mapping_by_id(specs: list[dict], requirement_count: int) -> dict[str, dict]:
    """Mapping fields per check id, with out-of-range pointers dropped.

    A ticket's stored requirements can differ from today's template, so an index
    the template declares may not exist on this ticket. Dropping it leaves the
    check unmapped (shown, but not attributed) rather than pointing at nothing.
    """
    index: dict[str, dict] = {}
    for spec in specs:
        declared = {k: spec[k] for k in MAPPING_FIELDS if k in spec}
        indexes = declared.get("requirement_indexes")
        if indexes is not None:
            kept = [i for i in indexes if 0 <= i < requirement_count]
            if len(kept) != len(indexes):
                print(f"  ! {spec.get('id')}: dropped out-of-range requirement pointer(s)")
            declared["requirement_indexes"] = kept or None
        single = declared.get("requirement_index")
        if isinstance(single, int) and not 0 <= single < requirement_count:
            print(f"  ! {spec.get('id')}: dropped out-of-range requirement_index {single}")
            declared["requirement_index"] = None
        if declared and spec.get("id"):
            index[spec["id"]] = declared
    return index


def _template_for(ticket: Ticket) -> dict | None:
    """The template variant this ticket was generated from.

    Variants of one skill share a file list, so `template_spec` can pick the
    wrong one; check-id overlap with the stored spec identifies it exactly.
    """
    templates = TICKET_TEMPLATES.get(ticket.target_skill_id) or []
    stored_ids = {c.get("id") for c in (ticket.validation_spec or {}).get("checks", []) or []}
    best, best_score = None, -1
    for template in templates:
        score = len(stored_ids & {c.get("id") for c in template.get("checks", [])})
        if score > best_score:
            best, best_score = template, score
    if best is None:
        return None
    if best_score <= 0:
        return template_spec(ticket)
    return build_validation_spec(best, context_for_ticket(ticket))


def merge_requirement_mapping(ticket: Ticket) -> dict | None:
    """Stored spec with today's requirement pointers merged in, or None if it
    already matches. Only the mapping fields are touched."""
    template = _template_for(ticket)
    if template is None:
        return None
    requirement_count = len(ticket.requirements or [])
    stored = ticket.validation_spec or {}
    merged = {**stored}
    changed = False

    check_map = _mapping_by_id(template.get("checks", []), requirement_count)
    checks = []
    for check in stored.get("checks", []) or []:
        declared = check_map.get(check.get("id"))
        if declared and any(check.get(k, "\0") != v for k, v in declared.items()):
            check = {**check, **declared}
            changed = True
        checks.append(check)
    merged["checks"] = checks

    template_behaviour = (template.get("behaviour") or {}).get("assertions", [])
    stored_behaviour = (stored.get("behaviour") or {}).get("assertions") or []
    if stored_behaviour:
        assertion_map = _mapping_by_id(template_behaviour, requirement_count)
        assertions = []
        for assertion in stored_behaviour:
            declared = assertion_map.get(assertion.get("id"))
            if declared and any(assertion.get(k, "\0") != v for k, v in declared.items()):
                assertion = {**assertion, **declared}
                changed = True
            assertions.append(assertion)
        merged["behaviour"] = {**(stored.get("behaviour") or {}), "assertions": assertions}

    return merged if changed else None


def map_requirements(db, apply: bool) -> int:
    tickets = db.scalars(select(Ticket)).all()
    changed = 0
    for ticket in tickets:
        merged = merge_requirement_mapping(ticket)
        if merged is None:
            continue
        annotated = sum(1 for c in merged["checks"] if "requirement_index" in c or "requirement_indexes" in c)
        print(
            f"{ticket.key:<8} {ticket.status:<12} {ticket.target_skill_id} "
            f"-> {annotated}/{len(merged['checks'])} checks carry a requirement pointer"
        )
        changed += 1
        if apply:
            ticket.validation_spec = merged
    if apply and changed:
        db.commit()
        print(f"\nMapped requirements on {changed} ticket(s). No status or XP changed.")
    elif not changed:
        print("Every ticket already carries today's requirement mapping.")
    else:
        print(f"\nDry run: {changed} ticket(s) would be updated. Re-run with --apply.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--all-skills",
        action="store_true",
        help="re-sync every ticket with a template, not just behaviour-bearing skills",
    )
    parser.add_argument(
        "--map-requirements",
        action="store_true",
        help=(
            "merge only the requirement_index/precondition pointers from today's "
            "templates onto every ticket's stored checks, leaving every other "
            "field (and any {placeholder}) untouched"
        ),
    )
    args = parser.parse_args()

    if args.map_requirements:
        with SessionLocal() as db:
            return map_requirements(db, args.apply)

    skills = None if args.all_skills else skills_with_behaviour()

    with SessionLocal() as db:
        tickets = db.scalars(select(Ticket)).all()
        changed: list[Ticket] = []
        for ticket in tickets:
            if skills is not None and ticket.target_skill_id not in skills:
                continue
            spec = template_spec(ticket)
            if spec is None or spec == (ticket.validation_spec or {}):
                continue
            changed.append(ticket)
            print(
                f"{ticket.key:<8} {ticket.status:<12} {ticket.target_skill_id} "
                f"-> {len(spec.get('checks', []))} checks, "
                f"{len((spec.get('behaviour') or {}).get('assertions', []))} behaviour assertions"
            )

        if not changed:
            print("Nothing to re-sync.")
            return 0

        if not args.apply:
            print(f"\nDry run: {len(changed)} ticket(s) would be re-synced. Re-run with --apply.")
            return 0

        for ticket in changed:
            ticket.validation_spec = template_spec(ticket)
        db.commit()
        print(f"\nRe-synced validation_spec on {len(changed)} ticket(s). No status or XP changed.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
