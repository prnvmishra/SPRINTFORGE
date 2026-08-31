from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.dependencies import CurrentTwin, CurrentUser, DbSession
from app.models import Project
from app.schemas.core import ProjectCreateRequest
from app.services import digital_twin_service as twin_service
from app.services import graph_router, sprint_generator
from app.services.knowledge_graph import get_knowledge_graph
from app.services.project_preview_service import build_preview_for_project
from app.services.ticket_service import ticket_to_dict

router = APIRouter(prefix="/projects", tags=["projects"])


def _project_payload(project: Project, include_plan: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": project.id,
        "title": project.title,
        "idea": project.idea,
        "tech_stack": project.tech_stack,
        "complexity": project.complexity,
        "desired_outcome": project.desired_outcome,
        "status": project.status,
        "progress_percent": project.progress_percent,
        "plan_rationale": project.plan_rationale,
        "created_at": project.created_at,
        "sprint_count": len(project.sprints),
        "ticket_count": sum(len(s.tickets) for s in project.sprints),
        "tickets_done": sum(1 for s in project.sprints for t in s.tickets if t.status == "done"),
    }
    if include_plan:
        payload["sprints"] = [
            {
                "id": sprint.id,
                "name": sprint.name,
                "milestone": sprint.milestone,
                "goal": sprint.goal,
                "status": sprint.status,
                "order_index": sprint.order_index,
                "tickets": [ticket_to_dict(t) for t in sprint.tickets],
            }
            for sprint in project.sprints
        ]
    return payload


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest, db: DbSession, user: CurrentUser, twin: CurrentTwin
) -> dict[str, Any]:
    graph = get_knowledge_graph()

    project = Project(
        user_id=user.id,
        title=payload.title.strip(),
        idea=payload.idea.strip(),
        tech_stack=payload.tech_stack,
        complexity=payload.complexity,
        desired_outcome=payload.desired_outcome,
    )
    db.add(project)
    db.flush()

    # Claimed-but-unverified technologies are recorded, never trusted.
    claimed = dict(twin.claimed_skills or {})
    for tech in payload.known_technologies:
        for skill_id in graph.skills_for_stack([tech]):
            claimed.setdefault(skill_id, payload.experience_level)
    if claimed != (twin.claimed_skills or {}):
        twin_service.set_claimed_skills(db, twin, claimed)

    plan = sprint_generator.generate_project_plan(db, twin, project)
    twin.active_project_id = project.id
    twin_service.register_activity(
        db,
        user.id,
        "project_created",
        f"Created project: {project.title}",
        plan["rationale"],
        {"project_id": project.id, **plan},
    )
    db.commit()
    db.refresh(project)

    return {
        "project": _project_payload(project, include_plan=True),
        "plan": plan,
        "recommendation": graph_router.recommend_next(db, twin),
    }


@router.get("")
def list_projects(db: DbSession, user: CurrentUser) -> dict[str, Any]:
    projects = db.scalars(
        select(Project).where(Project.user_id == user.id).order_by(Project.created_at.desc())
    ).all()
    return {"projects": [_project_payload(p) for p in projects]}


@router.get("/{project_id}")
def get_project(project_id: str, db: DbSession, user: CurrentUser, twin: CurrentTwin) -> dict[str, Any]:
    project = db.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Locks depend on live twin state, so refresh them whenever the plan is read.
    sprint_generator.refresh_ticket_locks(db, project, twin)
    sprint_generator.recompute_project_progress(project)
    db.commit()
    db.refresh(project)

    next_ticket = sprint_generator.next_actionable_ticket(project)
    return {
        "project": _project_payload(project, include_plan=True),
        "next_ticket": ticket_to_dict(next_ticket) if next_ticket else None,
    }


@router.get("/{project_id}/sprints")
def project_sprints(project_id: str, db: DbSession, user: CurrentUser) -> dict[str, Any]:
    project = db.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {
        "sprints": [
            {
                "id": sprint.id,
                "name": sprint.name,
                "milestone": sprint.milestone,
                "goal": sprint.goal,
                "status": sprint.status,
                "order_index": sprint.order_index,
                "tickets": [ticket_to_dict(t) for t in sprint.tickets],
            }
            for sprint in project.sprints
        ]
    }


@router.get("/{project_id}/preview")
def project_preview(project_id: str, db: DbSession, user: CurrentUser) -> dict[str, Any]:
    """The whole product as built so far, assembled from verified tickets.

    Display only — the same service the ticket workspace uses, so the two can
    never disagree, and nothing here reaches the validators.
    """
    project = db.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found.")

    preview = build_preview_for_project(db, project.id, project.title)
    return {
        "project": {
            "id": project.id,
            "title": project.title,
            "status": project.status,
            "progress_percent": project.progress_percent,
        },
        "html": preview["html"],
        "meta": preview["meta"],
    }


@router.get("/{project_id}/next-ticket")
def next_ticket(project_id: str, db: DbSession, user: CurrentUser, twin: CurrentTwin) -> dict[str, Any]:
    project = db.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found.")
    sprint_generator.refresh_ticket_locks(db, project, twin)
    db.commit()
    ticket = sprint_generator.next_actionable_ticket(project)
    return {
        "ticket": ticket_to_dict(ticket) if ticket else None,
        "recommendation": graph_router.recommend_next(db, twin),
    }
