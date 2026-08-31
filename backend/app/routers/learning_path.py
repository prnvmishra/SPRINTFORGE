"""The learner's personalised route, the adaptation audit trail, and resources.

Separate from `/paths` on purpose: `/paths` is the authored catalog, this is one
learner's spine to their own goal. Skills are cross-referenced to the catalog by
`path_id` / `course_id` rather than re-emitted.
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.dependencies import CurrentTwin, CurrentUser, DbSession
from app.services import learning_path_service

router = APIRouter(tags=["learning-path"])


@router.get("/learning-path")
def my_learning_path(db: DbSession, twin: CurrentTwin) -> dict[str, Any]:
    return learning_path_service.learning_path(db, twin)


@router.get("/adaptations")
def my_adaptations(db: DbSession, user: CurrentUser) -> dict[str, Any]:
    return learning_path_service.adaptations(db, user.id)


@router.get("/resources/{skill_id}")
def skill_resources(skill_id: str) -> dict[str, Any]:
    payload = learning_path_service.resources_for_skill(skill_id)
    if not payload["known_skill"]:
        raise HTTPException(status_code=404, detail="Unknown skill")
    return payload
