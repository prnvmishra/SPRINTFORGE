"""Guided roadmaps for subjects the engine does not grade.

Kept apart from `/learning-path` deliberately. That endpoint returns a route
built from verified confidence and can gate what comes next; these are reading
plans. Mixing them would let a roadmap step look like a verified skill, which is
the one claim this product is not allowed to make loosely.

Anonymous access is fine for the catalogue and for a single roadmap — there is
nothing learner-specific in them. `prerequisites` is annotated with the caller's
own confidence only when a session is present.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.dependencies import DbSession, OptionalTwin
from app.services import roadmap_service

router = APIRouter(tags=["roadmaps"])


@router.get("/roadmaps")
def list_roadmaps() -> dict[str, Any]:
    return {"roadmaps": roadmap_service.catalogue()}


@router.get("/roadmaps/resolve")
def resolve_roadmap(
    db: DbSession,
    twin: OptionalTwin,
    q: str = Query(..., min_length=1, description="Free text, e.g. 'i want to learn docker'"),
) -> dict[str, Any]:
    """Answers "can you teach me X?" for arbitrary X.

    Three honest outcomes, and the caller is told which one it got: the skill is
    graded here, there is a guided roadmap for it, or we have nothing.
    """
    return roadmap_service.resolve(db, twin, q)


@router.get("/roadmaps/{roadmap_id}")
def get_roadmap(db: DbSession, twin: OptionalTwin, roadmap_id: str) -> dict[str, Any]:
    payload = roadmap_service.detail(db, twin, roadmap_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Unknown roadmap")
    return payload
