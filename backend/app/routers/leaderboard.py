from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.core.dependencies import CurrentUser, DbSession
from app.models import LearningDigitalTwin, User, VerifiedSkill
from app.schemas.core import LeaderboardEntry, LeaderboardOut
from app.services.knowledge_graph import get_knowledge_graph

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

# Deterministic, fully explainable ranking: every component is a signal the
# product already computes, normalised to 0-100 and weighted.
WEIGHTS = {"confidence": 0.45, "xp": 0.25, "verified_skills": 0.20, "level": 0.10}
XP_CEILING = 2000
SKILL_CEILING = 10
LEVEL_CEILING = 10

FORMULA: dict[str, Any] = {
    "expression": (
        "score = 0.45·confidence + 0.25·min(xp/2000, 1)·100 "
        "+ 0.20·min(verified_skills/10, 1)·100 + 0.10·min(level/10, 1)·100"
    ),
    "weights": WEIGHTS,
    "caps": {"xp": XP_CEILING, "verified_skills": SKILL_CEILING, "level": LEVEL_CEILING},
    "tie_break": "higher XP, then more verified skills, then earlier account creation",
    "components": [
        {"key": "confidence", "label": "Overall confidence", "weight": WEIGHTS["confidence"]},
        {"key": "xp", "label": "XP", "weight": WEIGHTS["xp"]},
        {"key": "verified_skills", "label": "Verified skills", "weight": WEIGHTS["verified_skills"]},
        {"key": "level", "label": "Level", "weight": WEIGHTS["level"]},
    ],
}


def compute_score(confidence: float, xp: int, verified_skills: int, level: int) -> float:
    normalised = {
        "confidence": max(0.0, min(confidence, 100.0)),
        "xp": min(xp / XP_CEILING, 1.0) * 100,
        "verified_skills": min(verified_skills / SKILL_CEILING, 1.0) * 100,
        "level": min(level / LEVEL_CEILING, 1.0) * 100,
    }
    return round(sum(WEIGHTS[key] * value for key, value in normalised.items()), 1)


@router.get("", response_model=LeaderboardOut)
def leaderboard(
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> LeaderboardOut:
    threshold = get_knowledge_graph().confidence_threshold

    verified_counts = dict(
        db.execute(
            select(VerifiedSkill.twin_id, func.count(VerifiedSkill.id))
            .where(VerifiedSkill.confidence >= threshold)
            .group_by(VerifiedSkill.twin_id)
        ).all()
    )

    rows = db.execute(
        select(User, LearningDigitalTwin).join(
            LearningDigitalTwin, LearningDigitalTwin.user_id == User.id, isouter=True
        )
    ).all()

    ranked = []
    for account, twin in rows:
        confidence = twin.overall_confidence if twin else 0.0
        xp = twin.xp if twin else 0
        level = twin.level if twin else 1
        verified = verified_counts.get(twin.id, 0) if twin else 0
        ranked.append(
            {
                "user": account,
                "score": compute_score(confidence, xp, verified, level),
                "xp": xp,
                "level": level,
                "verified": verified,
                "confidence": round(confidence, 1),
            }
        )

    ranked.sort(
        key=lambda row: (
            -row["score"],
            -row["xp"],
            -row["verified"],
            row["user"].created_at.timestamp() if row["user"].created_at else 0.0,
            row["user"].id,
        )
    )

    def to_entry(row: dict[str, Any], rank: int) -> LeaderboardEntry:
        account: User = row["user"]
        return LeaderboardEntry(
            rank=rank,
            user_id=account.id,
            name=account.name,
            avatar_url=account.avatar_url,
            score=row["score"],
            xp=row["xp"],
            level=row["level"],
            verified_skills=row["verified"],
            overall_confidence=row["confidence"],
            is_current_user=account.id == user.id,
        )

    entries = [to_entry(row, offset + index + 1) for index, row in enumerate(ranked[offset : offset + limit])]

    current_entry = None
    for index, row in enumerate(ranked):
        if row["user"].id == user.id:
            current_entry = to_entry(row, index + 1)
            break

    return LeaderboardOut(
        entries=entries,
        total=len(ranked),
        limit=limit,
        offset=offset,
        confidence_threshold=threshold,
        formula=FORMULA,
        current_user=current_entry,
    )
