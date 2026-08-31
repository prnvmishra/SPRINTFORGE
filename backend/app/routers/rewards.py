from typing import Any

from fastapi import APIRouter
from sqlalchemy import select

from app.core.dependencies import CurrentTwin, CurrentUser, DbSession
from app.models import FailureAnalysis
from app.services import reward_service
from app.services.failure_analysis_service import analysis_to_dict

router = APIRouter(tags=["rewards"])


@router.get("/rewards/me")
def my_rewards(db: DbSession, twin: CurrentTwin) -> dict[str, Any]:
    return reward_service.reward_summary(db, twin)


@router.get("/failures/me")
def my_failures(db: DbSession, user: CurrentUser) -> dict[str, Any]:
    rows = db.scalars(
        select(FailureAnalysis)
        .where(FailureAnalysis.user_id == user.id)
        .order_by(FailureAnalysis.created_at.desc())
        .limit(50)
    ).all()
    return {"analyses": [analysis_to_dict(a) for a in rows]}
