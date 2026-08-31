from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.dependencies import CurrentTwin, CurrentUser, DbSession
from app.data.practice_modules import PRACTICE_MODULE_INDEX
from app.models import Ticket
from app.schemas.ai import EvaluationRequest, MentorRequest, MentorTurn
from app.schemas.core import EvaluateRequestBody, MentorRequestBody
from app.services import graph_router
from app.services.ai_evaluator import get_ai_provider
from app.services.knowledge_graph import get_knowledge_graph

router = APIRouter(prefix="/ai", tags=["ai"])


def _unmet_from_last_attempt(attempts: Any) -> list[str]:
    """Labels of the checks that failed on the learner's most recent submission."""
    ordered = sorted(
        attempts or [], key=lambda a: a.created_at or datetime.min, reverse=True
    )
    if not ordered:
        return []
    results = (ordered[0].static_results or []) + (ordered[0].test_results or [])
    return [
        str(r.get("label") or r.get("id"))
        for r in results
        if isinstance(r, dict) and not r.get("passed", False) and (r.get("label") or r.get("id"))
    ][:8]


@router.get("/status")
def status() -> dict[str, Any]:
    return {
        "configured_provider": settings.AI_PROVIDER,
        "effective_provider": settings.ai_provider_effective,
        "mock_mode": settings.ai_provider_effective == "mock",
        "code_execution_provider": settings.CODE_EXECUTION_PROVIDER,
    }


@router.post("/evaluate")
async def evaluate(payload: EvaluateRequestBody, user: CurrentUser) -> dict[str, Any]:
    """Standalone evaluation endpoint. Deterministic layers still apply upstream
    for practice and tickets; this exposes the validated AI contract directly."""
    graph = get_knowledge_graph()
    provider = get_ai_provider()
    result = await provider.evaluate(
        EvaluationRequest(
            skill_id=payload.skill_id,
            skill_name=graph.name_of(payload.skill_id),
            task_context=payload.task_context,
            requirements=payload.requirements,
            user_submission=payload.user_submission,
            language=payload.language,
            current_difficulty=payload.current_difficulty,
        )
    )
    return result.model_dump()


@router.post("/mentor")
async def mentor(payload: MentorRequestBody, db: DbSession, user: CurrentUser) -> dict[str, Any]:
    context = payload.user_code
    task_context = None
    skill_id = payload.skill_id
    language = "text"
    # Trust the client for hint context only, then enrich from the last graded attempt
    # so the mentor stays specific even if the client sends nothing.
    failing_checks = [c for c in payload.failing_checks if c][:8]

    if payload.ticket_id:
        ticket = db.get(Ticket, payload.ticket_id)
        if not ticket or ticket.sprint.project.user_id != user.id:
            raise HTTPException(status_code=404, detail="Ticket not found.")
        skill_id = skill_id or ticket.target_skill_id
        task_context = (
            f"{ticket.key} · {ticket.title}\n{ticket.description}\n"
            + "\n".join(f"- {r}" for r in (ticket.requirements or []))
        )
        context = context or "\n\n".join(
            f"/* {n} */\n{c}" for n, c in (ticket.workspace_files or {}).items()
        )
        if not failing_checks:
            failing_checks = _unmet_from_last_attempt(ticket.attempts)
    elif payload.module_id:
        module = PRACTICE_MODULE_INDEX.get(payload.module_id)
        if not module:
            raise HTTPException(status_code=404, detail="Practice module not found.")
        skill_id = skill_id or module["skill_id"]
        language = module.get("language") or "text"
        task_context = f"{module['title']}\n{module['summary']}\n" + "\n".join(
            f"- {r}" for r in module.get("requirements", [])
        )

    mode = payload.mode if payload.mode in {"hint", "concept", "debug"} else "hint"
    graph = get_knowledge_graph()
    provider = get_ai_provider()
    response = await provider.mentor(
        MentorRequest(
            question=payload.question,
            skill_id=skill_id,
            skill_name=graph.name_of(skill_id) if skill_id else None,
            task_context=task_context,
            user_code=context,
            language=language,
            mode=mode,  # type: ignore[arg-type]
            failing_checks=failing_checks,
            history=[
                MentorTurn(
                    role="mentor" if turn.role == "mentor" else "user",
                    text=turn.text,
                )
                for turn in payload.history[-6:]
                if turn.text.strip()
            ],
        )
    )
    return response.model_dump()


@router.get("/why-this-next")
def why_this_next(db: DbSession, twin: CurrentTwin) -> dict[str, Any]:
    return graph_router.why_this_next(db, twin)
