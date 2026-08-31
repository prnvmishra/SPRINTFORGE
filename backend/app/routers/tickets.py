from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.dependencies import CurrentTwin, CurrentUser, DbSession
from app.models import Ticket
from app.schemas.core import TicketFilesRequest
from app.services import ticket_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _load(db, user, ticket_id: str) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if not ticket or ticket.sprint.project.user_id != user.id:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket


@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, db: DbSession, user: CurrentUser) -> dict[str, Any]:
    ticket = _load(db, user, ticket_id)
    return ticket_service.ticket_to_dict(ticket, include_files=True, db=db)


@router.post("/{ticket_id}/start")
def start(ticket_id: str, db: DbSession, user: CurrentUser, twin: CurrentTwin) -> dict[str, Any]:
    ticket = _load(db, user, ticket_id)
    try:
        payload = ticket_service.start_ticket(db, twin, ticket)
    except PermissionError as exc:
        raise HTTPException(status_code=423, detail=str(exc))
    db.commit()
    return payload


@router.post("/{ticket_id}/run")
async def run(ticket_id: str, payload: TicketFilesRequest, db: DbSession, user: CurrentUser) -> dict[str, Any]:
    ticket = _load(db, user, ticket_id)
    result = await ticket_service.run_ticket(db, ticket, payload.files)
    db.commit()
    return result


@router.post("/{ticket_id}/submit")
async def submit(
    ticket_id: str, payload: TicketFilesRequest, db: DbSession, user: CurrentUser, twin: CurrentTwin
) -> dict[str, Any]:
    ticket = _load(db, user, ticket_id)
    try:
        result = await ticket_service.submit_ticket(
            db, twin, ticket, payload.files, payload.duration_seconds
        )
    except PermissionError as exc:
        raise HTTPException(status_code=423, detail=str(exc))
    db.commit()
    return result


@router.post("/{ticket_id}/reset")
def reset(ticket_id: str, db: DbSession, user: CurrentUser) -> dict[str, Any]:
    ticket = _load(db, user, ticket_id)
    payload = ticket_service.reset_ticket(db, ticket)
    db.commit()
    return payload
