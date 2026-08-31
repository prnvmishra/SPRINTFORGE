"""Placement endpoints: pick a path, prove your level, get a starting point."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.dependencies import CurrentTwin, CurrentUser, DbSession
from app.data.paths import PATH_INDEX
from app.services import digital_twin_service as twin_service
from app.services import placement_service

router = APIRouter(prefix="/placement", tags=["placement"])


class PlacementStartRequest(BaseModel):
    path_id: str = Field(min_length=1, max_length=60)


@router.get("")
def placement_state(db: DbSession, twin: CurrentTwin) -> dict[str, Any]:
    state = placement_service.state(db, twin)
    db.commit()
    return state


@router.post("/start")
def start(
    payload: PlacementStartRequest, db: DbSession, user: CurrentUser, twin: CurrentTwin
) -> dict[str, Any]:
    path = PATH_INDEX.get(payload.path_id)
    if not path:
        raise HTTPException(status_code=404, detail=f"Unknown path '{payload.path_id}'.")

    placement_service.begin(db, twin, payload.path_id)
    if twin.placement_status == "unavailable":
        raise HTTPException(
            status_code=409,
            detail=(
                f"{path['label']} has no curriculum behind it yet, so there is nothing to "
                "assess. Pick a path marked available."
            ),
        )

    twin_service.register_activity(
        db,
        user.id,
        "placement_started",
        f"Started placement for {path['label']}",
        f"{len(twin.placement_skills or [])} probes planned",
        {"path_id": payload.path_id},
    )
    state = placement_service.state(db, twin)
    db.commit()
    return state


@router.post("/skip")
def skip(db: DbSession, user: CurrentUser, twin: CurrentTwin) -> dict[str, Any]:
    placement_service.skip(db, twin)
    twin_service.register_activity(
        db,
        user.id,
        "placement_skipped",
        "Skipped placement",
        "Recommendations will run on claimed levels until real evidence exists.",
    )
    state = placement_service.state(db, twin)
    db.commit()
    return state


@router.post("/reset")
def reset(db: DbSession, twin: CurrentTwin) -> dict[str, Any]:
    placement_service.reset(db, twin)
    state = placement_service.state(db, twin)
    db.commit()
    return state
