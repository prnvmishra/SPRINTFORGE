from typing import Any

from fastapi import APIRouter
from sqlalchemy import select

from app.core.dependencies import CurrentTwin, CurrentUser, DbSession
from app.data.paths import PATH_INDEX
from app.models import ActivityLog, FailureAnalysis, Project
from app.schemas.core import DigitalTwinOut, OnboardRequest, SkillOut, UserOut
from app.services import digital_twin_service as twin_service
from app.services import graph_router, placement_service, reward_service, sprint_generator
from app.services.failure_analysis_service import analysis_to_dict
from app.services.knowledge_graph import get_knowledge_graph
from app.services.ticket_service import ticket_to_dict

router = APIRouter(prefix="/profile", tags=["profile"])


def _twin_payload(twin) -> DigitalTwinOut:
    graph = get_knowledge_graph()
    skills = [SkillOut(**s) for s in twin_service.skill_report(twin)]
    return DigitalTwinOut(
        user_id=twin.user_id,
        goal=twin.goal,
        experience_level=twin.experience_level,
        claimed_skills=twin.claimed_skills or {},
        overall_confidence=twin.overall_confidence,
        xp=twin.xp,
        level=twin.level,
        streak_days=twin.streak_days,
        consistency_score=twin.consistency_score,
        learning_velocity=twin.learning_velocity,
        avg_completion_seconds=twin.avg_completion_seconds,
        preferred_difficulty=twin.preferred_difficulty,
        completed_projects=twin.completed_projects,
        repeated_mistakes=twin.repeated_mistakes or {},
        active_project_id=twin.active_project_id,
        active_ticket_id=twin.active_ticket_id,
        path_id=twin.path_id,
        placement_status=twin.placement_status or "pending",
        verified_skills=skills,
        skills_needing_improvement=[
            s for s in skills if s.confidence < graph.confidence_threshold
        ],
    )


@router.post("/onboard", response_model=DigitalTwinOut)
def onboard(payload: OnboardRequest, db: DbSession, user: CurrentUser, twin: CurrentTwin) -> DigitalTwinOut:
    twin.goal = payload.goal
    twin.experience_level = payload.experience_level
    twin_service.set_claimed_skills(db, twin, payload.claimed_skills)
    if payload.path_id and payload.path_id in PATH_INDEX:
        placement_service.begin(db, twin, payload.path_id)
    user.is_onboarded = True
    twin_service.register_activity(
        db,
        user.id,
        "onboarded",
        "Set learning goal",
        payload.goal,
        {"claimed_skills": payload.claimed_skills},
    )
    db.commit()
    db.refresh(twin)
    return _twin_payload(twin)


@router.get("/me", response_model=UserOut)
def profile_me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.get("/digital-twin", response_model=DigitalTwinOut)
def digital_twin(twin: CurrentTwin) -> DigitalTwinOut:
    return _twin_payload(twin)


@router.get("/dashboard")
def dashboard(db: DbSession, user: CurrentUser, twin: CurrentTwin) -> dict[str, Any]:
    graph = get_knowledge_graph()
    projects = list(
        db.scalars(
            select(Project).where(Project.user_id == user.id).order_by(Project.created_at.desc())
        ).all()
    )
    active_project = next((p for p in projects if p.status == "active"), projects[0] if projects else None)

    current_ticket = None
    current_sprint = None
    if active_project:
        ticket = sprint_generator.next_actionable_ticket(active_project)
        if ticket:
            current_ticket = ticket_to_dict(ticket)
            current_sprint = {
                "id": ticket.sprint.id,
                "name": ticket.sprint.name,
                "milestone": ticket.sprint.milestone,
                "status": ticket.sprint.status,
                "ticket_count": len(ticket.sprint.tickets),
                "tickets_done": sum(1 for t in ticket.sprint.tickets if t.status == "done"),
            }

    activity = db.scalars(
        select(ActivityLog)
        .where(ActivityLog.user_id == user.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(12)
    ).all()

    open_analyses = db.scalars(
        select(FailureAnalysis)
        .where(FailureAnalysis.user_id == user.id, FailureAnalysis.resolved.is_(False))
        .order_by(FailureAnalysis.created_at.desc())
        .limit(5)
    ).all()

    twin_payload = _twin_payload(twin)
    return {
        "user": UserOut.model_validate(user).model_dump(),
        "twin": twin_payload.model_dump(),
        "confidence_threshold": graph.confidence_threshold,
        "verified_skills": [s.model_dump() for s in twin_payload.verified_skills],
        "skills_needing_improvement": [
            s.model_dump() for s in twin_payload.skills_needing_improvement
        ],
        "active_project": (
            {
                "id": active_project.id,
                "title": active_project.title,
                "status": active_project.status,
                "progress_percent": active_project.progress_percent,
                "tech_stack": active_project.tech_stack,
                "sprint_count": len(active_project.sprints),
                "ticket_count": sum(len(s.tickets) for s in active_project.sprints),
                "tickets_done": sum(
                    1 for s in active_project.sprints for t in s.tickets if t.status == "done"
                ),
            }
            if active_project
            else None
        ),
        "current_sprint": current_sprint,
        "current_ticket": current_ticket,
        "projects": [
            {
                "id": p.id,
                "title": p.title,
                "status": p.status,
                "progress_percent": p.progress_percent,
                "tech_stack": p.tech_stack,
            }
            for p in projects
        ],
        "rewards": reward_service.reward_summary(db, twin),
        "placement": placement_service.summary(db, twin),
        "recommendation": graph_router.recommend_next(db, twin),
        "open_gaps": [analysis_to_dict(a) for a in open_analyses],
        "recent_activity": [
            {
                "id": a.id,
                "event_type": a.event_type,
                "title": a.title,
                "detail": a.detail,
                "created_at": a.created_at,
            }
            for a in activity
        ],
    }


@router.get("/activity")
def activity_log(db: DbSession, user: CurrentUser, limit: int = 30) -> dict[str, Any]:
    """The system log, for the Digital Twin page.

    Split out of the dashboard payload: the log is a record of the past, and the
    dashboard is about the next action, so it no longer belongs in that response.
    """
    events = db.scalars(
        select(ActivityLog)
        .where(ActivityLog.user_id == user.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(max(1, min(limit, 200)))
    ).all()
    return {
        "events": [
            {
                "id": a.id,
                "event_type": a.event_type,
                "title": a.title,
                "detail": a.detail,
                "created_at": a.created_at,
            }
            for a in events
        ]
    }


@router.get("/knowledge-graph")
def knowledge_graph(twin: CurrentTwin) -> dict[str, Any]:
    graph = get_knowledge_graph()
    confidences, evidence, demonstrated = twin_service.gating_context(twin)
    unlock_state = {
        node.id: graph.is_unlocked(node.id, confidences, evidence, demonstrated)
        for node in graph.all_nodes()
    }
    return {
        "confidence_threshold": graph.confidence_threshold,
        "nodes": [
            {
                "id": node.id,
                "name": node.name,
                "track": node.track,
                "difficulty_weight": node.difficulty_weight,
                "prerequisites": node.prerequisites,
                "unlocks": node.unlocks,
                "related_concepts": node.related_concepts,
                "recommended_practice": node.recommended_practice,
                "confidence": round(confidences.get(node.id, 0.0), 1),
                "has_evidence": node.id in evidence,
                "unlocked": unlock_state[node.id][0],
                # The gaps `is_unlocked` already computed were previously
                # discarded; the Skill Route rendering needs them to explain a
                # locked node without a second round-trip.
                "missing_prerequisites": unlock_state[node.id][1],
            }
            for node in graph.all_nodes()
        ],
    }
