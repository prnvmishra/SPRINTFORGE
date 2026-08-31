"""AI Project Manager: turns a project idea into Milestones → Sprints → Tickets.

Deliberately does NOT generate a finished solution. It produces an ordered
backlog of engineering tickets, each with deterministic acceptance checks, and
locks tickets whose prerequisite skills are not yet verified.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.data.ticket_templates import SPRINT_THEMES, STARTER_FILES, TICKET_TEMPLATES
from app.models import LearningDigitalTwin, Project, Sprint, Ticket
from app.services import digital_twin_service as twin_service
from app.services.knowledge_graph import get_knowledge_graph
from app.services.spec_interpolation import (
    STOP_WORDS,
    build_validation_spec,
    context_for_project,
    fill as _fill,
    infer_entity,
)

__all__ = [
    "STOP_WORDS",
    "generate_project_plan",
    "infer_entity",
    "next_actionable_ticket",
    "recompute_project_progress",
    "refresh_ticket_locks",
]


def generate_project_plan(
    db: Session,
    twin: LearningDigitalTwin,
    project: Project,
) -> dict[str, Any]:
    """Create sprints and tickets for a project, gated by the knowledge graph."""
    graph = get_knowledge_graph()
    context = context_for_project(project)

    stack_skills = graph.skills_for_stack(project.tech_stack)
    confidences, evidence, demonstrated = twin_service.gating_context(twin)
    complexity_bonus = {"beginner": -1, "intermediate": 0, "advanced": 1}.get(
        project.complexity.lower(), 0
    )

    order = 0
    ticket_number = 0
    created_sprints: list[Sprint] = []
    ticket_key_by_slug: dict[str, str] = {}

    for milestone, sprint_name, theme_skills in SPRINT_THEMES:
        # A theme skill only earns a sprint if it can actually contribute a
        # ticket. Filtering on `stack_skills` alone created sprints for skills
        # that had no templates at the time, so a generated board showed empty
        # sprints the learner could never act on.
        relevant = [s for s in theme_skills if s in stack_skills and TICKET_TEMPLATES.get(s)]
        if not relevant:
            continue

        sprint = Sprint(
            project_id=project.id,
            milestone=milestone,
            name=sprint_name,
            goal=f"{sprint_name} for {project.title}",
            order_index=order,
        )
        db.add(sprint)
        db.flush()
        created_sprints.append(sprint)
        order += 1

        for skill_id in relevant:
            for template in TICKET_TEMPLATES.get(skill_id, []):
                ticket_number += 1
                node = graph.get(skill_id)
                unlocked, gaps = graph.is_unlocked(skill_id, confidences, evidence, demonstrated)

                difficulty = max(1, min(10, (node.difficulty_weight if node else 3) + complexity_bonus))
                files = _fill(template.get("files", []), context)
                starter = {
                    name: _fill(STARTER_FILES.get(name, ""), context) for name in files
                }

                key = f"{_project_prefix(project.title)}-{ticket_number}"
                ticket_key_by_slug[template["slug"]] = key

                dependencies = [
                    ticket_key_by_slug[dep]
                    for dep in template.get("depends_on_slugs", [])
                    if dep in ticket_key_by_slug
                ]
                if not dependencies and ticket_number > 1:
                    dependencies = [f"{_project_prefix(project.title)}-{ticket_number - 1}"]

                if unlocked:
                    status = "todo" if ticket_number == 1 else "locked"
                    lock_reason = (
                        None
                        if ticket_number == 1
                        else f"Complete {dependencies[0]} first (sequential dependency)."
                    )
                else:
                    status = "locked"
                    gap = gaps[0]
                    lock_reason = (
                        f"Prerequisite not verified: {gap['skill_name']} is at "
                        f"{gap['confidence']}% confidence but {gap['required']}% is required before "
                        f"{graph.name_of(skill_id)} work can be validated."
                    )

                ticket = Ticket(
                    sprint_id=sprint.id,
                    key=key,
                    title=_fill(template["title"], context),
                    description=_fill(template["description"], context),
                    target_skill_id=skill_id,
                    difficulty=difficulty,
                    requirements=_fill(template["requirements"], context),
                    acceptance_criteria=_fill(template["acceptance_criteria"], context),
                    dependencies=dependencies,
                    estimated_minutes=template.get("estimated_minutes", 30),
                    order_index=ticket_number,
                    status=status,
                    lock_reason=lock_reason,
                    validation_spec=build_validation_spec(template, context),
                    starter_files=starter,
                    workspace_files=dict(starter),
                    xp_reward=30 if difficulty <= 6 else 50,
                )
                db.add(ticket)
                db.flush()

    rationale_parts = [
        f"{project.title} was decomposed into {len(created_sprints)} sprints across the skills "
        f"implied by your stack ({', '.join(project.tech_stack)}).",
        # Named from the sprints actually created. The old wording hardcoded the
        # web progression ("structure → styling → ... → backend"), which was
        # simply false on a board that has no styling or backend sprint at all.
        "Sprints follow the dependency order in the knowledge graph: "
        + " → ".join(sprint.name for sprint in created_sprints)
        + ".",
    ]
    blocked = [
        graph.name_of(sid)
        for sid in stack_skills
        if not graph.is_unlocked(sid, confidences, evidence, demonstrated)[0]
    ]
    if blocked:
        rationale_parts.append(
            "Tickets for " + ", ".join(dict.fromkeys(blocked)) +
            " start locked because their prerequisites are not yet verified by your Digital Twin."
        )
    project.plan_rationale = " ".join(rationale_parts)
    db.flush()

    return {
        "project_id": project.id,
        "sprints_created": len(created_sprints),
        "tickets_created": ticket_number,
        "rationale": project.plan_rationale,
    }


def _project_prefix(title: str) -> str:
    letters = re.findall(r"[A-Za-z]+", title)
    if not letters:
        return "TCK"
    if len(letters) == 1:
        return letters[0][:3].upper()
    return "".join(w[0] for w in letters[:3]).upper()


def recompute_project_progress(project: Project) -> float:
    tickets = [t for sprint in project.sprints for t in sprint.tickets]
    if not tickets:
        return 0.0
    done = sum(1 for t in tickets if t.status == "done")
    project.progress_percent = round(done / len(tickets) * 100, 1)
    for sprint in project.sprints:
        if not sprint.tickets:
            continue
        if all(t.status == "done" for t in sprint.tickets):
            sprint.status = "done"
        elif any(t.status in {"in_progress", "submitted", "under_review", "failed"} for t in sprint.tickets):
            sprint.status = "in_progress"
        else:
            sprint.status = "todo"
    if project.progress_percent >= 100:
        project.status = "completed"
    return project.progress_percent


def refresh_ticket_locks(
    db: Session, project: Project, twin: LearningDigitalTwin
) -> list[dict[str, Any]]:
    """Re-evaluate every locked ticket after the twin changes. Returns newly unlocked tickets."""
    graph = get_knowledge_graph()
    confidences, evidence, demonstrated = twin_service.gating_context(twin)
    tickets = sorted(
        (t for sprint in project.sprints for t in sprint.tickets), key=lambda t: t.order_index
    )
    done_keys = {t.key for t in tickets if t.status == "done"}
    newly_unlocked: list[dict[str, Any]] = []

    for ticket in tickets:
        if ticket.status not in {"locked"}:
            continue
        unlocked, gaps = graph.is_unlocked(ticket.target_skill_id, confidences, evidence, demonstrated)
        deps_met = all(dep in done_keys for dep in (ticket.dependencies or []))
        if unlocked and deps_met:
            ticket.status = "todo"
            ticket.lock_reason = None
            newly_unlocked.append({"ticket_id": ticket.id, "key": ticket.key, "title": ticket.title})
        elif not unlocked:
            gap = gaps[0]
            ticket.lock_reason = (
                f"Prerequisite not verified: {gap['skill_name']} is at {gap['confidence']}% "
                f"but {gap['required']}% is required."
            )
        else:
            pending = [d for d in (ticket.dependencies or []) if d not in done_keys]
            ticket.lock_reason = f"Blocked by {', '.join(pending)}." if pending else None
    db.flush()
    return newly_unlocked


def next_actionable_ticket(project: Project) -> Optional[Ticket]:
    tickets = sorted(
        (t for sprint in project.sprints for t in sprint.tickets), key=lambda t: t.order_index
    )
    for status in ("in_progress", "failed", "todo"):
        for ticket in tickets:
            if ticket.status == status:
                return ticket
    return None
