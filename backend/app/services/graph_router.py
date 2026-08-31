"""Decides what the learner should do next, and explains why.

Every recommendation carries an explanation built from real evidence: the
prerequisite that is below threshold, the failure analyses that produced the
gap, and the project ticket the gap is blocking.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.practice_modules import PRACTICE_MODULE_INDEX
from app.models import FailureAnalysis, LearningDigitalTwin, Project, Ticket
from app.services import digital_twin_service as twin_service
from app.services import placement_service
from app.services.failure_analysis_service import find_remediation_module
from app.services.knowledge_graph import get_knowledge_graph
from app.services.sprint_generator import next_actionable_ticket


def _open_analyses(db: Session, user_id: str) -> list[FailureAnalysis]:
    return list(
        db.scalars(
            select(FailureAnalysis)
            .where(FailureAnalysis.user_id == user_id, FailureAnalysis.resolved.is_(False))
            .order_by(FailureAnalysis.created_at.desc())
        ).all()
    )


def _active_project(db: Session, twin: LearningDigitalTwin) -> Optional[Project]:
    if twin.active_project_id:
        project = db.get(Project, twin.active_project_id)
        if project:
            return project
    return db.scalar(
        select(Project)
        .where(Project.user_id == twin.user_id, Project.status == "active")
        .order_by(Project.created_at.desc())
    )


def recommend_next(db: Session, twin: LearningDigitalTwin) -> dict[str, Any]:
    graph = get_knowledge_graph()

    # 0. Nothing below can be trusted before placement. Every branch after this
    #    reasons from confidence scores, and an unplaced learner's scores come
    #    from claims rather than evidence — so recommending a course here would be
    #    exactly the guess this product exists to avoid.
    if placement_service.needs_placement(twin):
        state = placement_service.summary(db, twin)
        probe = state.get("next_probe") or {}
        remaining = max(0, state["total_probes"] - state["probes_completed"])
        return {
            "type": "placement",
            "skill_id": probe.get("skill_id"),
            "skill_name": probe.get("skill_name"),
            "path_id": twin.path_id,
            "title": (
                f"Placement check: {probe['skill_name']}"
                if probe.get("skill_name")
                else "Take your placement check"
            ),
            "reason": (
                f"You chose {state['path_label'] or 'a career path'} but nothing has graded you on "
                f"it yet. {remaining} short check(s) of "
                f"{placement_service.PROBE_QUESTIONS} questions each tell us which courses you can "
                "skip and which one you should actually start at — so your route is built on "
                "evidence instead of your own estimate."
            ),
            "evidence": {
                "probes_completed": state["probes_completed"],
                "total_probes": state["total_probes"],
            },
        }

    confidences, evidence, demonstrated = twin_service.gating_context(twin)
    project = _active_project(db, twin)
    analyses = _open_analyses(db, twin.user_id)

    target_ticket: Optional[Ticket] = None
    blocked_ticket: Optional[Ticket] = None
    if project:
        target_ticket = next_actionable_ticket(project)
        if target_ticket is None:
            locked = sorted(
                (t for s in project.sprints for t in s.tickets if t.status == "locked"),
                key=lambda t: t.order_index,
            )
            blocked_ticket = locked[0] if locked else None

    # 1. An unresolved conceptual gap always wins: fix the cause, not the symptom.
    if analyses:
        analysis = analyses[0]
        module_id = analysis.remediation_module_id
        module = PRACTICE_MODULE_INDEX.get(module_id) if module_id else None
        if module is None:
            module = find_remediation_module(analysis.skill_id, analysis.missing_concepts or [])
        blocking = blocked_ticket or target_ticket
        reason_parts = [
            f"Your last failure on {graph.name_of(analysis.skill_id)} was caused by: {analysis.root_cause}",
        ]
        if analysis.missing_concepts:
            reason_parts.append(
                "The specific gap is " + ", ".join(analysis.missing_concepts[:3]) + "."
            )
        # Only claim a ticket dependency when the graph actually says so, otherwise
        # the explanation is provably wrong to the learner reading it.
        if blocking and analysis.skill_id in set(
            graph.learning_path(blocking.target_skill_id or "")
        ):
            reason_parts.append(
                f"That concept is required by ticket {blocking.key} — "
                f"\"{blocking.title}\" — in your active project, so clearing it unblocks real work."
            )
        elif blocking:
            reason_parts.append(
                f"Clearing it now keeps the gap from resurfacing later in your active project "
                f"(next up: {blocking.key} — \"{blocking.title}\")."
            )
        return {
            "type": "remediation_practice",
            "skill_id": analysis.skill_id,
            "skill_name": graph.name_of(analysis.skill_id),
            "module_id": module["id"] if module else None,
            "title": module["title"] if module else f"Practice {graph.name_of(analysis.skill_id)}",
            "reason": " ".join(reason_parts),
            "evidence": {
                "failure_analysis_id": analysis.id,
                "missing_concepts": analysis.missing_concepts or [],
                "repeated_mistakes": twin.repeated_mistakes or {},
            },
            "blocked_ticket": (
                {"id": blocking.id, "key": blocking.key, "title": blocking.title} if blocking else None
            ),
        }

    # 2. A locked ticket means a prerequisite is below threshold: route to the weakest one.
    if blocked_ticket:
        gaps = graph.missing_prerequisites(
            blocked_ticket.target_skill_id, confidences, evidence, demonstrated
        )
        if gaps:
            weakest = min(gaps, key=lambda g: g["confidence"])
            module_id = next(iter(weakest.get("recommended_practice") or []), None)
            module = PRACTICE_MODULE_INDEX.get(module_id) if module_id else None
            chain = " → ".join(
                graph.name_of(s) for s in graph.learning_path(blocked_ticket.target_skill_id)
            )
            return {
                "type": "prerequisite_practice",
                "skill_id": weakest["skill_id"],
                "skill_name": weakest["skill_name"],
                "module_id": module["id"] if module else None,
                "title": module["title"] if module else f"Practice {weakest['skill_name']}",
                "reason": (
                    f"Ticket {blocked_ticket.key} targets {graph.name_of(blocked_ticket.target_skill_id)}, "
                    f"which depends on {chain}. Your {weakest['skill_name']} confidence is "
                    f"{weakest['confidence']}% and {weakest['required']}% is required, so unlocking that "
                    "prerequisite is the fastest path to the ticket."
                ),
                "evidence": {"prerequisite_gaps": gaps, "dependency_chain": chain},
                "blocked_ticket": {
                    "id": blocked_ticket.id,
                    "key": blocked_ticket.key,
                    "title": blocked_ticket.title,
                },
            }
        return {
            "type": "ticket",
            "ticket_id": blocked_ticket.id,
            "skill_id": blocked_ticket.target_skill_id,
            "skill_name": graph.name_of(blocked_ticket.target_skill_id),
            "title": f"{blocked_ticket.key} · {blocked_ticket.title}",
            "reason": blocked_ticket.lock_reason
            or "This ticket is next in the dependency order of your project.",
            "evidence": {},
        }

    # 3. Otherwise continue the project.
    if target_ticket:
        return {
            "type": "ticket",
            "ticket_id": target_ticket.id,
            "skill_id": target_ticket.target_skill_id,
            "skill_name": graph.name_of(target_ticket.target_skill_id),
            "title": f"{target_ticket.key} · {target_ticket.title}",
            "reason": (
                f"All prerequisites for {graph.name_of(target_ticket.target_skill_id)} are verified "
                f"({round(confidences.get(target_ticket.target_skill_id, 0), 1)}% confidence on the target skill), "
                f"and {target_ticket.key} is the next ticket in dependency order for {target_ticket.sprint.project.title}."
            ),
            "evidence": {
                "sprint": target_ticket.sprint.name,
                "milestone": target_ticket.sprint.milestone,
                "difficulty": target_ticket.difficulty,
            },
        }

    # 4. No project yet: strengthen the weakest claimed skill, or verify claims.
    weak = sorted(
        (s for s in twin.verified_skills if s.confidence < graph.confidence_threshold),
        key=lambda s: s.confidence,
    )
    if weak:
        skill = weak[0]
        node = graph.get(skill.skill_id)
        module_id = next(iter(node.recommended_practice), None) if node else None
        module = PRACTICE_MODULE_INDEX.get(module_id) if module_id else None
        return {
            "type": "practice",
            "skill_id": skill.skill_id,
            "skill_name": skill.skill_name,
            "module_id": module["id"] if module else None,
            "title": module["title"] if module else f"Practice {skill.skill_name}",
            "reason": (
                f"{skill.skill_name} sits at {skill.confidence}% verified confidence, the lowest in your "
                f"Digital Twin, and it unlocks "
                + (", ".join(graph.name_of(u) for u in (node.unlocks if node else [])) or "further skills")
                + ". Raising it first prevents downstream failures."
            ),
            "evidence": {
                "confidence": skill.confidence,
                "weak_concepts": skill.weak_concepts or [],
                "breakdown": skill.score_breakdown or {},
            },
        }

    if not twin.verified_skills:
        return {
            "type": "assessment",
            "skill_id": None,
            "title": "Verify your claimed skills",
            "reason": (
                "Your Digital Twin has no verified evidence yet. SprintForge does not trust claimed "
                "levels, so start with an adaptive assessment to establish real confidence scores."
            ),
            "evidence": {},
        }

    return {
        "type": "project",
        "skill_id": None,
        "title": "Create your next project",
        "reason": (
            "Every tracked skill is above the mastery threshold, so the highest-value next step is "
            "applying them in a new project where SprintForge can find gaps under real conditions."
        ),
        "evidence": {"overall_confidence": twin.overall_confidence},
    }


def why_this_next(db: Session, twin: LearningDigitalTwin) -> dict[str, Any]:
    recommendation = recommend_next(db, twin)
    graph = get_knowledge_graph()
    skill_id = recommendation.get("skill_id")
    chain = graph.learning_path(skill_id) if skill_id else []
    return {
        "recommendation": recommendation,
        "explanation": recommendation["reason"],
        "dependency_chain": [
            {
                "skill_id": sid,
                "skill_name": graph.name_of(sid),
                "confidence": round(
                    next((s.confidence for s in twin.verified_skills if s.skill_id == sid), 0.0), 1
                ),
                "threshold": graph.confidence_threshold,
            }
            for sid in chain
        ],
    }
