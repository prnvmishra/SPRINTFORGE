from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.dependencies import CurrentTwin, CurrentUser, DbSession
from app.data.assessment_bank import ITEMS_BY_SKILL
from app.models import AssessmentSession
from app.schemas.core import (
    AssessmentQuestionOut,
    AssessmentStartRequest,
    AssessmentStateOut,
    AssessmentSubmitRequest,
    AssessmentSubmitResponse,
)
from app.services import assessment_engine
from app.services import digital_twin_service as twin_service
from app.services import failure_analysis_service, placement_service, reward_service
from app.services.knowledge_graph import get_knowledge_graph

router = APIRouter(prefix="/assessment", tags=["assessment"])


def _state(session: AssessmentSession, question: Optional[dict[str, Any]]) -> AssessmentStateOut:
    return AssessmentStateOut(
        session_id=session.id,
        skill_id=session.skill_id,
        status=session.status,
        questions_asked=session.questions_asked,
        max_questions=session.max_questions,
        correct_count=session.correct_count,
        current_difficulty=session.current_difficulty,
        question=AssessmentQuestionOut(**assessment_engine.public_item(question)) if question else None,
        result=session.result if session.status == "completed" else None,
    )


@router.get("/skills")
def assessable_skills() -> dict[str, Any]:
    graph = get_knowledge_graph()
    return {
        "skills": [
            {
                "skill_id": skill_id,
                "skill_name": graph.name_of(skill_id),
                "item_count": len(items),
                "difficulty_range": [items[0]["difficulty"], items[-1]["difficulty"]],
            }
            for skill_id, items in sorted(ITEMS_BY_SKILL.items())
        ]
    }


@router.post("/start", response_model=AssessmentStateOut)
def start(payload: AssessmentStartRequest, db: DbSession, user: CurrentUser, twin: CurrentTwin) -> AssessmentStateOut:
    if payload.skill_id not in ITEMS_BY_SKILL:
        raise HTTPException(status_code=404, detail=f"No assessment items for '{payload.skill_id}'.")

    claimed = payload.claimed_level or (twin.claimed_skills or {}).get(payload.skill_id)
    is_probe = payload.placement and placement_service.is_probe_skill(twin, payload.skill_id)
    max_questions = (
        placement_service.questions_for_probe(twin, payload.skill_id)
        if is_probe
        else payload.max_questions
    )
    session = AssessmentSession(
        user_id=user.id,
        skill_id=payload.skill_id,
        claimed_level=claimed,
        current_difficulty=assessment_engine.start_difficulty_for_claim(claimed),
        max_questions=max_questions,
        asked_question_ids=[],
        result={},
    )
    db.add(session)
    db.flush()

    if is_probe:
        placement_service.register_probe_session(db, twin, payload.skill_id, session.id)

    question = assessment_engine.next_question(session)
    if question is None:
        raise HTTPException(status_code=409, detail="No questions available for this skill.")

    twin_service.register_activity(
        db,
        user.id,
        "assessment_started",
        f"Started {get_knowledge_graph().name_of(payload.skill_id)} verification",
        f"Claimed level: {claimed or 'unspecified'}",
        {"session_id": session.id},
    )
    db.commit()
    db.refresh(session)
    return _state(session, question)


@router.get("/{session_id}", response_model=AssessmentStateOut)
def session_state(session_id: str, db: DbSession, user: CurrentUser) -> AssessmentStateOut:
    session = db.get(AssessmentSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Assessment session not found.")
    question = assessment_engine.next_question(session) if session.status == "in_progress" else None
    return _state(session, question)


@router.post("/submit", response_model=AssessmentSubmitResponse)
async def submit(
    payload: AssessmentSubmitRequest, db: DbSession, user: CurrentUser, twin: CurrentTwin
) -> AssessmentSubmitResponse:
    session = db.get(AssessmentSession, payload.session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Assessment session not found.")
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="This assessment session is already complete.")

    item = assessment_engine.item_by_id(payload.question_id)
    if not item:
        raise HTTPException(status_code=404, detail="Unknown question.")
    if payload.question_id in (session.asked_question_ids or []):
        raise HTTPException(status_code=409, detail="This question was already answered.")

    # The backend evaluates; the client never reports correctness.
    evaluation = await assessment_engine.evaluate_answer(item, payload.answer, session.current_difficulty)
    assessment_engine.record_attempt(db, session, item, payload.answer, evaluation, payload.duration_seconds)

    twin_service.record_assessment_outcome(
        db,
        twin,
        item["skill_id"],
        evaluation.is_correct,
        item["difficulty"],
        evaluation.missing_concepts,
    )

    failure_payload = None
    if not evaluation.is_correct:
        analysis = failure_analysis_service.analyze_failure(
            db, twin, item["skill_id"], "assessment", session.id, evaluation, []
        )
        failure_payload = failure_analysis_service.analysis_to_dict(analysis)

    question = assessment_engine.next_question(session)
    if question is None:
        result = assessment_engine.finalize_session(db, session)
        skill = twin_service.get_or_create_skill(db, twin, session.skill_id)
        skill.claimed_level = session.claimed_level or skill.claimed_level
        if result["accuracy"] >= 60:
            reward_service.award_xp(
                db,
                twin,
                reward_service.XP_TABLE["assessment"],
                f"Verified {skill.skill_name}",
                "assessment",
                session.id,
            )
        twin_service.register_activity(
            db,
            user.id,
            "assessment_completed",
            f"Verified {skill.skill_name}: {result['verified_level']}",
            f"Accuracy {result['accuracy']}% · confidence {skill.confidence}%",
            {"session_id": session.id, "weak_concepts": result["weak_concepts"]},
        )
        twin_service.touch_activity_metrics(db, twin)

    skill = twin_service.get_or_create_skill(db, twin, item["skill_id"])
    skill_payload = {
        "skill_id": skill.skill_id,
        "skill_name": skill.skill_name,
        "confidence": skill.confidence,
        "verified_level": skill.verified_level,
        "weak_concepts": skill.weak_concepts or [],
        "breakdown": skill.score_breakdown or {},
    }

    db.commit()
    db.refresh(session)

    return AssessmentSubmitResponse(
        is_correct=evaluation.is_correct,
        evaluation=evaluation.model_dump(),
        state=_state(session, question),
        skill=skill_payload,
        failure_analysis=failure_payload,
    )


@router.get("/{session_id}/result")
def result(session_id: str, db: DbSession, user: CurrentUser) -> dict[str, Any]:
    session = db.get(AssessmentSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Assessment session not found.")
    if session.status != "completed":
        raise HTTPException(status_code=409, detail="Assessment is still in progress.")
    return session.result or {}


@router.get("/history/all")
def history(db: DbSession, user: CurrentUser) -> dict[str, Any]:
    sessions = db.scalars(
        select(AssessmentSession)
        .where(AssessmentSession.user_id == user.id)
        .order_by(AssessmentSession.created_at.desc())
    ).all()
    return {
        "sessions": [
            {
                "id": s.id,
                "skill_id": s.skill_id,
                "skill_name": get_knowledge_graph().name_of(s.skill_id),
                "status": s.status,
                "claimed_level": s.claimed_level,
                "correct_count": s.correct_count,
                "questions_asked": s.questions_asked,
                "result": s.result,
                "created_at": s.created_at,
            }
            for s in sessions
        ]
    }
