"""Revoke a ticket that passed under the old permissive validator.

Does three things for the named ticket:
  1. resets status to in_progress so it must be earned again,
  2. reverses the XP granted for that completion and recomputes level,
  3. re-syncs validation_spec from the current ticket template, so the retry is
     graded by today's strict AST checks instead of the weak regex snapshot
     stored when the ticket was generated.

Step 3 is also applied to tickets that are not yet completed (--sync-pending),
since their stored specs carry the same weak checks.

Nothing is written without --apply.

    python scripts/reset_false_pass.py --ticket <id>
    python scripts/reset_false_pass.py --ticket <id> --sync-pending --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.data.ticket_templates import STARTER_FILES, TICKET_TEMPLATES
from app.models import LearningDigitalTwin, RewardTransaction, Ticket
from app.services.reward_service import level_for_xp
from app.services.spec_interpolation import (
    build_validation_spec,
    context_for_ticket,
    fill as _fill,
)


def template_spec(ticket: Ticket) -> dict | None:
    """The strict spec this ticket would get if it were generated today.

    Interpolated through `spec_interpolation.build_validation_spec`, the same
    single path the generator uses. This function used to return
    `{"checks": chosen["checks"], ...}` — raw template checks — so a re-synced
    ticket kept `#{entity}List` in its selectors and every rendered check on it
    failed with "invalid selector" against correct work.
    """
    templates = TICKET_TEMPLATES.get(ticket.target_skill_id)
    if not templates:
        return None
    # Templates are a list of variants; match the one whose checks reference the
    # same files the ticket actually ships, else fall back to the first.
    shipped = set((ticket.starter_files or {}).keys())
    for template in templates:
        if shipped and shipped.issuperset({c.get("file") for c in template["checks"] if c.get("file")}):
            chosen = template
            break
    else:
        chosen = templates[0]
    return build_validation_spec(chosen, context_for_ticket(ticket))


def resync_brief(ticket: Ticket) -> bool:
    """Align the visible brief with the checks that actually grade the ticket.

    The stored requirements predate the strict validator and still promise things
    nothing enforces (e.g. a loading indicator), which is precisely the kind of
    mismatch that makes the grader look untrustworthy.
    """
    templates = TICKET_TEMPLATES.get(ticket.target_skill_id)
    if not templates:
        return False
    template = templates[0]
    context = context_for_ticket(ticket)
    changed = False
    # Interpolated for the same reason the checks are: a brief that reads
    # "the {entity} listing" is a placeholder leak the learner can see.
    requirements = _fill(template.get("requirements") or [], context, strict=True)
    criteria = _fill(template.get("acceptance_criteria") or [], context, strict=True)
    if requirements and ticket.requirements != requirements:
        ticket.requirements = list(requirements)
        changed = True
    if criteria and ticket.acceptance_criteria != criteria:
        ticket.acceptance_criteria = list(criteria)
        changed = True
    return changed


def describe(spec: dict | None) -> str:
    if not spec:
        return "unavailable"
    types = [c.get("type") for c in spec.get("checks", [])]
    return f"{len(types)} checks {types}, behaviour={bool(spec.get('behaviour'))}"


def resync_starters(ticket: Ticket) -> bool:
    """Refresh the scaffolding a not-done ticket ships with.

    The sample data in `script.js` gained a poster URL, and the js_dom ticket now
    grades that the card renders it — so a ticket still holding the old
    image-less starter would be asked for a field its data does not have. Only
    untouched files are replaced: anything the learner actually edited is left
    exactly as it is.
    """
    context = context_for_ticket(ticket)
    old_starter = dict(ticket.starter_files or {})
    new_starter = {
        name: _fill(STARTER_FILES.get(name, ""), context) for name in old_starter
    }
    if new_starter == old_starter:
        return False

    workspace = dict(ticket.workspace_files or {})
    for name, fresh in new_starter.items():
        stale = old_starter.get(name)
        if name not in workspace or not (workspace[name] or "").strip():
            continue
        if workspace[name] == stale:
            workspace[name] = fresh
    ticket.starter_files = new_starter
    ticket.workspace_files = workspace
    return True


def sync_pending_only(apply: bool) -> int:
    """Refresh specs and briefs on every not-done ticket. Revokes nothing.

    Live tickets were generated from older templates, so an in-progress ticket
    still shows the brief it was created with. Tickets that are already `done`
    are never touched: their work was verified against the spec of the day and
    re-grading it retroactively is not this script's job.
    """
    with SessionLocal() as db:
        pending = [
            t
            for t in db.scalars(select(Ticket).where(Ticket.status != "done")).all()
            if template_spec(t)
        ]
        print(f"pending tickets (status != done) with a current template: {len(pending)}")

        briefs = 0
        specs = 0
        starters = 0
        for ticket in pending:
            spec = template_spec(ticket)
            if ticket.validation_spec != spec:
                ticket.validation_spec = spec
                specs += 1
            if resync_brief(ticket):
                briefs += 1
            if resync_starters(ticket):
                starters += 1
            print(
                f"  {ticket.key:<8} {ticket.status:<12} {ticket.target_skill_id:<22} "
                f"{describe(spec)}"
            )

        print(f"\nspecs to update:    {specs}")
        print(f"briefs to update:   {briefs}")
        print(f"starters to update: {starters}")
        if not apply:
            print("\nDry run. Re-run with --apply.")
            return 0
        db.commit()
        print(f"\nApplied. Re-synced {specs} spec(s), {briefs} brief(s) and {starters} "
              f"starter set(s) across {len(pending)} pending ticket(s). "
              "No ticket was revoked.")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ticket",
        help="ticket id to revoke. Omit it (with --sync-pending) to only re-sync "
        "specs and briefs on tickets that are not done — nothing is revoked.",
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--sync-pending",
        action="store_true",
        help="also refresh validation_spec on tickets that are not done",
    )
    args = parser.parse_args()

    if not args.ticket:
        if not args.sync_pending:
            parser.error("pass --ticket <id>, or --sync-pending to only re-sync briefs")
        return sync_pending_only(apply=args.apply)

    with SessionLocal() as db:
        ticket = db.get(Ticket, args.ticket)
        if ticket is None:
            print(f"No ticket with id {args.ticket}")
            return 1

        twin = db.scalars(
            select(LearningDigitalTwin).where(
                LearningDigitalTwin.user_id == ticket.sprint.project.user_id
            )
        ).first()

        rewards = db.scalars(
            select(RewardTransaction).where(RewardTransaction.source_id == ticket.id)
        ).all()
        refund = sum(r.amount for r in rewards)

        print(f"ticket:        {ticket.key} — {ticket.title}")
        print(f"status:        {ticket.status} -> in_progress")
        print(f"stored files:  { {k: len(v or '') for k, v in (ticket.workspace_files or {}).items()} }")
        print(f"stored spec:   {describe(ticket.validation_spec)}")
        print(f"strict spec:   {describe(template_spec(ticket))}")
        print(f"xp to revoke:  {refund} across {len(rewards)} reward transaction(s)")
        if twin:
            new_xp = max(0, twin.xp - refund)
            print(f"twin xp:       {twin.xp} -> {new_xp} (level {twin.level} -> {level_for_xp(new_xp)})")

        pending: list[Ticket] = []
        if args.sync_pending:
            pending = [
                t
                for t in db.scalars(select(Ticket).where(Ticket.status != "done")).all()
                if t.id != ticket.id and template_spec(t)
            ]
            print(f"\npending tickets to re-sync: {len(pending)}")
            for t in pending:
                print(f"  {t.key:<8} {t.status:<12} {describe(t.validation_spec)}")

        if not args.apply:
            print("\nDry run. Re-run with --apply.")
            return 0

        spec = template_spec(ticket)
        if spec:
            ticket.validation_spec = spec
        ticket.status = "in_progress"
        briefs_updated = 1 if resync_brief(ticket) else 0

        for reward in rewards:
            db.delete(reward)
        if twin and refund:
            twin.xp = max(0, twin.xp - refund)
            twin.level = level_for_xp(twin.xp)

        for t in pending:
            t.validation_spec = template_spec(t)
            if resync_brief(t):
                briefs_updated += 1

        db.commit()

        print(f"\nRevoked {ticket.key}. XP removed: {refund}.")
        if twin:
            print(f"twin now: xp={twin.xp} level={twin.level}")
        if pending:
            print(f"Re-synced validation_spec on {len(pending)} pending ticket(s).")
        print(f"Briefs realigned with their checks: {briefs_updated}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
