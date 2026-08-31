"""Send a project's finished tickets back to the learner against today's templates.

`reset_false_pass.py` revokes one ticket that slipped through a weak validator.
This is the project-wide case: the web ticket templates were rewritten (hero
section, horizontal nav, poster grid, fluid images), so work graded against the
old briefs was signed off for a bar that no longer exists. The learner's site
looks unstyled and their board says 5/5.

For every ticket in one project this:

  1. puts the status back to `todo` (a `done` ticket is only touched with
     --include-done, which has to be asked for),
  2. reverses the XP granted for it, including the sprint-completion bonus that
     the completion earned, and recomputes the level,
  3. re-syncs validation_spec, title, description, requirements, acceptance
     criteria and starter files from the current template,
  4. keeps everything the learner wrote. A workspace file is only replaced when
     it is byte-identical to the starter it was handed — untouched scaffolding.
     Their code stays in the editor so they can extend it rather than retype it.

Nothing is written without --apply, and --apply first writes a JSON snapshot of
every field it is about to change, so the run can be undone by hand.

    python scripts/reset_project_tickets.py --project <id>
    python scripts/reset_project_tickets.py --project <id> --include-done --apply
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
from app.data.ticket_templates import STARTER_FILES, TICKET_TEMPLATES
from app.models import LearningDigitalTwin, Project, RewardTransaction, Sprint, Ticket
from app.services.reward_service import level_for_xp
from app.services.sprint_generator import _fill, infer_entity, recompute_project_progress

SNAPSHOT_DIR = Path(__file__).resolve().parents[1] / "uploads" / "ticket_resets"

# The fields this script rewrites. Everything here is snapshotted before a write
# so the run is reversible from the file alone.
SNAPSHOT_FIELDS = (
    "status",
    "completed_at",
    "started_at",
    "title",
    "description",
    "requirements",
    "acceptance_criteria",
    "estimated_minutes",
    "validation_spec",
    "starter_files",
    "workspace_files",
)


def template_for(ticket: Ticket) -> dict[str, Any] | None:
    """The template this ticket would be generated from today.

    Templates are a list of variants per skill; match the one whose checks name
    the files the ticket actually ships, else the first.
    """
    templates = TICKET_TEMPLATES.get(ticket.target_skill_id)
    if not templates:
        return None
    shipped = set((ticket.starter_files or {}).keys())
    for template in templates:
        referenced = {c.get("file") for c in template["checks"] if c.get("file")}
        if shipped and referenced and shipped.issuperset(referenced):
            return template
    return templates[0]


def ticket_context(ticket: Ticket) -> dict[str, str]:
    project = ticket.sprint.project
    entity, entity_plural = infer_entity(project.idea, project.title)
    return {"domain": project.title, "entity": entity, "entity_plural": entity_plural}


def planned_changes(ticket: Ticket, template: dict[str, Any]) -> dict[str, Any]:
    """What this ticket would become, without touching it.

    Returned as a plain dict so the dry run prints exactly the values --apply
    will write; there is no second code path that could drift from the report.
    """
    context = ticket_context(ticket)
    filled = {key: _fill(template.get(key), context) for key in
              ("title", "description", "requirements", "acceptance_criteria")}
    spec = {
        "checks": _fill(template["checks"], context),
        "behaviour": _fill(template.get("behaviour") or {}, context),
    }
    old_starter = dict(ticket.starter_files or {})
    new_starter = {
        name: _fill(STARTER_FILES.get(name, ""), context) for name in old_starter
    }

    # The learner's code survives. Only a file still byte-identical to the
    # starter it was handed is refreshed: that is scaffolding we gave them, not
    # something they wrote.
    workspace = dict(ticket.workspace_files or {})
    refreshed: list[str] = []
    preserved: list[str] = []
    for name, fresh in new_starter.items():
        current = workspace.get(name)
        if current is None or not (current or "").strip() or current == old_starter.get(name):
            if current != fresh:
                refreshed.append(name)
            workspace[name] = fresh
        else:
            preserved.append(name)

    return {
        "title": filled["title"] or ticket.title,
        "description": filled["description"] or ticket.description,
        "requirements": list(filled["requirements"] or ticket.requirements or []),
        "acceptance_criteria": list(
            filled["acceptance_criteria"] or ticket.acceptance_criteria or []
        ),
        "estimated_minutes": template.get("estimated_minutes") or ticket.estimated_minutes,
        "validation_spec": spec,
        "starter_files": new_starter,
        "workspace_files": workspace,
        "_refreshed_files": refreshed,
        "_preserved_files": preserved,
    }


def snapshot(ticket: Ticket) -> dict[str, Any]:
    record: dict[str, Any] = {"id": ticket.id, "key": ticket.key}
    for field in SNAPSHOT_FIELDS:
        value = getattr(ticket, field)
        record[field] = value.isoformat() if isinstance(value, datetime) else value
    return record


def rewards_for(db, ticket: Ticket) -> list[RewardTransaction]:
    return list(
        db.scalars(
            select(RewardTransaction).where(RewardTransaction.source_id == ticket.id)
        ).all()
    )


def sprint_bonus_rewards(db, sprint: Sprint) -> list[RewardTransaction]:
    """The milestone bonus a now-undone sprint completion paid out."""
    return list(
        db.scalars(
            select(RewardTransaction).where(
                RewardTransaction.source_id == sprint.id,
                RewardTransaction.source_type == "milestone",
            )
        ).all()
    )


def describe_spec(spec: dict | None) -> str:
    if not spec:
        return "unavailable"
    checks = spec.get("checks") or []
    return f"{len(checks)} checks, behaviour={bool(spec.get('behaviour'))}"


def run(project_id: str, include_done: bool, apply: bool) -> int:
    with SessionLocal() as db:
        project = db.get(Project, project_id)
        if project is None:
            print(f"No project with id {project_id}")
            return 1

        tickets = sorted(
            db.scalars(
                select(Ticket).join(Sprint).where(Sprint.project_id == project.id)
            ).all(),
            key=lambda t: (t.sprint.order_index, t.order_index, t.key),
        )
        targets = [
            t for t in tickets if t.status == "done" or t.status in {"failed", "under_review"}
        ]
        if not include_done:
            targets = [t for t in targets if t.status != "done"]

        twin = db.scalars(
            select(LearningDigitalTwin).where(
                LearningDigitalTwin.user_id == project.user_id
            )
        ).first()

        print(f"project:  {project.title} ({project.id})")
        print(f"owner:    {project.user_id}")
        print(f"status:   {project.status}  progress {project.progress_percent}%")
        print(f"tickets:  {len(tickets)} total, {len(targets)} to reset")
        if not targets:
            print("\nNothing to do.")
            return 0

        refund = 0
        reward_rows: list[RewardTransaction] = []
        plans: list[tuple[Ticket, dict[str, Any]]] = []

        print()
        for ticket in targets:
            template = template_for(ticket)
            if template is None:
                print(f"  {ticket.key:<8} SKIPPED — no current template for "
                      f"{ticket.target_skill_id}")
                continue
            plan = planned_changes(ticket, template)
            plans.append((ticket, plan))

            rows = rewards_for(db, ticket)
            reward_rows.extend(rows)
            refund += sum(r.amount for r in rows)

            print(f"  {ticket.key:<8} {ticket.status} -> todo   [{ticket.target_skill_id}]")
            print(f"      title:       {ticket.title!r}")
            if plan["title"] != ticket.title:
                print(f"                -> {plan['title']!r}")
            print(f"      spec:        {describe_spec(ticket.validation_spec)}"
                  f"  ->  {describe_spec(plan['validation_spec'])}")
            print(f"      brief:       {len(ticket.requirements or [])} requirements"
                  f"  ->  {len(plan['requirements'])}")
            print(f"      xp revoked:  {sum(r.amount for r in rows)}"
                  f" across {len(rows)} transaction(s)")
            print(f"      starters:    "
                  f"{ {k: len(v or '') for k, v in (ticket.starter_files or {}).items()} }"
                  f" -> { {k: len(v or '') for k, v in plan['starter_files'].items()} }")
            print(f"      kept as written:  {plan['_preserved_files'] or 'none'}")
            print(f"      refreshed scaffold: {plan['_refreshed_files'] or 'none'}")

        # A sprint whose tickets are going back to todo is no longer complete, so
        # the completion bonus it paid has to go with them.
        touched_sprints = {t.sprint for t, _ in plans}
        for sprint in touched_sprints:
            rows = sprint_bonus_rewards(db, sprint)
            if rows:
                reward_rows.extend(rows)
                refund += sum(r.amount for r in rows)
                print(f"\n  sprint bonus revoked: {sprint.name} "
                      f"({sum(r.amount for r in rows)} XP)")

        print(f"\ntotal xp to revoke: {refund}")
        if twin:
            new_xp = max(0, twin.xp - refund)
            print(f"twin xp: {twin.xp} -> {new_xp} "
                  f"(level {twin.level} -> {level_for_xp(new_xp)})")
        else:
            print("no digital twin for this user; xp is only removed from the ledger")

        print("\nWhat is NOT touched: attempt history, other projects, other users, "
              "and any workspace file the learner edited.")

        if not apply:
            print("\nDry run. Re-run with --apply.")
            return 0

        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snapshot_path = SNAPSHOT_DIR / f"{project.id}-{stamp}.json"
        snapshot_path.write_text(
            json.dumps(
                {
                    "project_id": project.id,
                    "project_status": project.status,
                    "project_progress_percent": project.progress_percent,
                    "twin_xp": twin.xp if twin else None,
                    "twin_level": twin.level if twin else None,
                    "reward_transactions": [
                        {
                            "id": r.id,
                            "user_id": r.user_id,
                            "amount": r.amount,
                            "reason": r.reason,
                            "source_type": r.source_type,
                            "source_id": r.source_id,
                        }
                        for r in reward_rows
                    ],
                    "tickets": [snapshot(t) for t, _ in plans],
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        print(f"\nsnapshot written: {snapshot_path}")

        for ticket, plan in plans:
            for field in (
                "title",
                "description",
                "requirements",
                "acceptance_criteria",
                "estimated_minutes",
                "validation_spec",
                "starter_files",
                "workspace_files",
            ):
                setattr(ticket, field, plan[field])
            ticket.status = "todo"
            ticket.completed_at = None
            ticket.lock_reason = None

        for reward in reward_rows:
            db.delete(reward)
        if twin and refund:
            twin.xp = max(0, twin.xp - refund)
            twin.level = level_for_xp(twin.xp)

        recompute_project_progress(project)
        if project.progress_percent < 100 and project.status == "completed":
            project.status = "active"

        db.commit()

        print(f"\nApplied. {len(plans)} ticket(s) are back on the board as todo, "
              f"graded by the current templates.")
        print(f"project now: status={project.status} progress={project.progress_percent}%")
        if twin:
            print(f"twin now:    xp={twin.xp} level={twin.level}")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="project id to reset")
    parser.add_argument(
        "--include-done",
        action="store_true",
        help="also reset tickets that are already verified. Required to undo a "
        "completed project; without it only failed/under-review tickets move.",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    return run(args.project, args.include_done, args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
