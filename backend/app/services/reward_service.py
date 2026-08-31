"""XP, levels and reward transactions."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LearningDigitalTwin, RewardTransaction

XP_TABLE = {
    "practice_easy": 10,
    "practice_medium": 25,
    "practice_hard": 50,
    "ticket": 30,
    "milestone": 100,
    "assessment": 20,
    "remediation": 15,
}

LEVEL_STEP = 200


def xp_for_difficulty(difficulty: int) -> int:
    if difficulty <= 3:
        return XP_TABLE["practice_easy"]
    if difficulty <= 6:
        return XP_TABLE["practice_medium"]
    return XP_TABLE["practice_hard"]


def level_for_xp(xp: int) -> int:
    return max(1, xp // LEVEL_STEP + 1)


def award_xp(
    db: Session,
    twin: LearningDigitalTwin,
    amount: int,
    reason: str,
    source_type: str = "practice",
    source_id: Optional[str] = None,
) -> RewardTransaction:
    amount = max(0, int(amount))
    twin.xp += amount
    twin.level = level_for_xp(twin.xp)
    transaction = RewardTransaction(
        user_id=twin.user_id,
        amount=amount,
        reason=reason,
        source_type=source_type,
        source_id=source_id,
    )
    db.add(transaction)
    db.flush()
    return transaction


def reward_summary(db: Session, twin: LearningDigitalTwin) -> dict:
    recent = db.scalars(
        select(RewardTransaction)
        .where(RewardTransaction.user_id == twin.user_id)
        .order_by(RewardTransaction.created_at.desc())
        .limit(10)
    ).all()
    current_level_floor = (twin.level - 1) * LEVEL_STEP
    return {
        "xp": twin.xp,
        "level": twin.level,
        "xp_into_level": twin.xp - current_level_floor,
        "xp_for_next_level": LEVEL_STEP,
        "streak_days": twin.streak_days,
        "recent": [
            {
                "id": t.id,
                "amount": t.amount,
                "reason": t.reason,
                "source_type": t.source_type,
                "created_at": t.created_at,
            }
            for t in recent
        ],
    }
