from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.core.dependencies import CurrentTwin, CurrentUser, DbSession
from app.models import PracticeAttempt
from app.schemas.core import PracticeRunRequest, PracticeSubmitRequest
from app.services import practice_service
from app.services.code_execution_service import SUPPORTED_LANGUAGES

router = APIRouter(prefix="/practice", tags=["practice"])


@router.get("/modules")
def modules(
    technology: Optional[str] = Query(default=None),
    layer: Optional[str] = Query(default=None),
) -> dict[str, Any]:
    return {
        "modules": practice_service.list_modules(technology, layer),
        "supported_languages": SUPPORTED_LANGUAGES,
    }


@router.get("/modules/{module_id}")
def module(module_id: str) -> dict[str, Any]:
    detail = practice_service.module_detail(module_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Practice module not found.")
    return detail


@router.post("/modules/{module_id}/run")
async def run(module_id: str, payload: PracticeRunRequest, db: DbSession, user: CurrentUser) -> dict[str, Any]:
    try:
        result = await practice_service.run_module(db, user.id, module_id, payload.files, payload.stdin)
    except KeyError:
        raise HTTPException(status_code=404, detail="Practice module not found.")
    db.commit()
    return result


@router.post("/modules/{module_id}/submit")
async def submit(
    module_id: str, payload: PracticeSubmitRequest, db: DbSession, twin: CurrentTwin
) -> dict[str, Any]:
    try:
        result = await practice_service.submit_module(
            db, twin, module_id, payload.files, payload.duration_seconds
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Practice module not found.")
    db.commit()
    return result


@router.get("/attempts")
def attempts(db: DbSession, user: CurrentUser) -> dict[str, Any]:
    rows = db.scalars(
        select(PracticeAttempt)
        .where(PracticeAttempt.user_id == user.id)
        .order_by(PracticeAttempt.created_at.desc())
        .limit(50)
    ).all()
    return {
        "attempts": [
            {
                "id": a.id,
                "module_id": a.module_id,
                "skill_id": a.skill_id,
                "passed": a.passed,
                "xp_awarded": a.xp_awarded,
                "created_at": a.created_at,
                "feedback": (a.ai_evaluation or {}).get("feedback"),
            }
            for a in rows
        ]
    }
