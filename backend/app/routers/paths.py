"""Career path browsing: paths, their courses, and a single course's contents."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.dependencies import CurrentUser, DbSession
from app.services import path_service
from app.services.digital_twin_service import get_or_create_twin

router = APIRouter(prefix="/paths", tags=["paths"])


@router.get("")
def list_paths(db: DbSession, user: CurrentUser) -> dict[str, Any]:
    twin = get_or_create_twin(db, user)
    return path_service.list_paths(db, twin)


@router.get("/{path_id}")
def get_path(path_id: str, db: DbSession, user: CurrentUser) -> dict[str, Any]:
    twin = get_or_create_twin(db, user)
    detail = path_service.path_detail(db, twin, path_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Path not found")
    return detail


@router.get("/{path_id}/courses/{course_id}")
def get_course(
    path_id: str, course_id: str, db: DbSession, user: CurrentUser
) -> dict[str, Any]:
    twin = get_or_create_twin(db, user)
    detail = path_service.course_detail(db, twin, path_id, course_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Course not found")
    return detail
