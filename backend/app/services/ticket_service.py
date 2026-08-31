"""Ticket lifecycle: start → run → submit → validate → unlock or remediate."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import LearningDigitalTwin, Ticket, TicketAttempt
from app.schemas.ai import EvaluationRequest, EvaluationResult
from app.services import digital_twin_service as twin_service
from app.services import failure_analysis_service, reward_service, sprint_generator
from app.services.ai_evaluator import get_ai_provider
from app.services.knowledge_graph import get_knowledge_graph
from app.services.project_preview_service import (
    build_project_preview,
    cumulative_files_before,
    provided_files,
)
from app.services.validation_service import (
    render_assembly_debug,
    run_behaviour_tests,
    run_static_checks,
)

ACTIONABLE_STATUSES = {"todo", "in_progress", "failed"}


def render_bundle_for(db: Session, ticket: Ticket) -> dict[str, str]:
    """The read-only page context a rendered check needs, from the one composer.

    `ticket.workspace_files` is the submission and stays the only thing textual
    and AST checks read. Rendered checks additionally need the document the
    stylesheet or script belongs to, which for a single-file ticket lives in an
    earlier ticket — so it is fetched here and handed to `run_static_checks` as a
    separate map, which layers the submission back on top.
    """
    return provided_files(db, ticket)


def _render_debug_field(
    files: dict[str, str],
    checks: list[dict[str, Any]],
    provided: dict[str, str],
) -> dict[str, Any]:
    """`{"render_debug": ...}` when the debug switch is on, otherwise `{}`.

    Spread into the response so the key is genuinely absent by default rather
    than present and null — a client cannot come to depend on a field that is not
    there.
    """
    debug = render_assembly_debug(files, checks, render_files=provided)
    return {"render_debug": debug} if debug is not None else {}


async def _run_ticket_behaviour_tests(
    ticket: Ticket, files: dict[str, str]
) -> list[dict[str, Any]]:
    """Layer 2: harness-driven behaviour tests, where the harness owns the network."""
    spec = (ticket.validation_spec or {}).get("behaviour") or {}
    assertions = spec.get("assertions") or []
    if not assertions:
        return []
    code_file = spec.get("file") or "script.js"
    return [
        outcome.to_dict()
        for outcome in await run_behaviour_tests(
            files.get(code_file, ""),
            assertions,
            spec.get("prelude", ""),
            spec.get("wrap_as"),
        )
    ]


def ticket_to_dict(
    ticket: Ticket,
    include_files: bool = False,
    db: Optional[Session] = None,
) -> dict[str, Any]:
    graph = get_knowledge_graph()
    payload: dict[str, Any] = {
        "id": ticket.id,
        "key": ticket.key,
        "title": ticket.title,
        "description": ticket.description,
        "target_skill_id": ticket.target_skill_id,
        "target_skill_name": graph.name_of(ticket.target_skill_id),
        "difficulty": ticket.difficulty,
        "requirements": ticket.requirements or [],
        "acceptance_criteria": ticket.acceptance_criteria or [],
        "dependencies": ticket.dependencies or [],
        "estimated_minutes": ticket.estimated_minutes,
        "status": ticket.status,
        "lock_reason": ticket.lock_reason,
        "xp_reward": ticket.xp_reward,
        "order_index": ticket.order_index,
        "sprint_id": ticket.sprint_id,
        "attempt_count": len(ticket.attempts),
        "started_at": ticket.started_at,
        "completed_at": ticket.completed_at,
    }
    if include_files:
        payload["files"] = ticket.workspace_files or ticket.starter_files or {}
        payload["editable_files"] = list((ticket.starter_files or {}).keys())
        payload["project_id"] = ticket.sprint.project_id
        payload["project_title"] = ticket.sprint.project.title
        payload["sprint_name"] = ticket.sprint.name
        payload["milestone"] = ticket.sprint.milestone
        if db is not None:
            # Additive: lets the PREVIEW tab be populated on open rather than
            # only as a side effect of Run.
            preview = build_project_preview(db, ticket)
            payload["preview"] = preview["html"]
            payload["preview_meta"] = preview["meta"]
            # The cumulative file map behind that document. The client recomposes
            # it locally with the live editor buffers on top, so a CSS- or JS-only
            # ticket previews as you type instead of only after a Run round trip.
            # Display only: grading reads `ticket.workspace_files`.
            payload["preview_files"] = preview["files"]
    return payload


def is_unopened(ticket: Ticket) -> bool:
    """Whether this workspace still holds nothing but the starter we handed over.

    Tickets are created with `workspace_files` pre-filled from `starter_files`,
    so "empty" is not a reliable test for untouched — the contents have to be
    compared. Anything else in there is the learner's, and is never overwritten.
    """
    workspace = ticket.workspace_files or {}
    starter = ticket.starter_files or {}
    return all(content == (starter.get(name) or "") for name, content in workspace.items())


def opening_files(db: Session, ticket: Ticket) -> dict[str, str]:
    """The files a ticket should open onto: project state, not a blank template.

    For each file this ticket owns, the cumulative content produced by the
    tickets before it on the board, falling back to the starter template when no
    previous ticket ever wrote that file. Restricted to the ticket's own
    filenames, because those are the only files it may edit and the only ones
    grading reads — the rest of the project reaches the learner through the
    preview, not the editor.
    """
    starter = ticket.starter_files or {}
    inherited = cumulative_files_before(db, ticket)
    return {name: inherited.get(name) or content for name, content in starter.items()}


def start_ticket(db: Session, twin: LearningDigitalTwin, ticket: Ticket) -> dict[str, Any]:
    if ticket.status == "locked":
        raise PermissionError(ticket.lock_reason or "This ticket is locked.")
    if ticket.status == "done":
        return ticket_to_dict(ticket, include_files=True, db=db)

    ticket.status = "in_progress"
    if ticket.started_at is None:
        ticket.started_at = datetime.now(timezone.utc)
    # Carry the project forward. Only an untouched workspace is reseeded: once
    # the learner has written anything, that buffer is theirs.
    if is_unopened(ticket):
        ticket.workspace_files = opening_files(db, ticket)
    twin.active_project_id = ticket.sprint.project_id
    twin.active_ticket_id = ticket.id
    twin_service.register_activity(
        db,
        twin.user_id,
        "ticket_started",
        f"Started {ticket.key}: {ticket.title}",
        None,
        {"ticket_id": ticket.id},
    )
    db.flush()
    return ticket_to_dict(ticket, include_files=True, db=db)


def workspace_with(ticket: Ticket, files: dict[str, str]) -> dict[str, str]:
    """The ticket's stored files with `files` layered over the ones it owns.

    Pure: computes the map without touching the row, so a caller that must not
    persist (see `run_ticket`) can still grade exactly what the learner typed.
    """
    allowed = set((ticket.starter_files or {}).keys())
    merged = dict(ticket.workspace_files or ticket.starter_files or {})
    for name, content in (files or {}).items():
        if name in allowed:
            merged[name] = content
    return merged


def save_workspace(db: Session, ticket: Ticket, files: dict[str, str]) -> dict[str, str]:
    merged = workspace_with(ticket, files)
    ticket.workspace_files = merged
    db.flush()
    return merged


async def run_ticket(db: Session, ticket: Ticket, files: dict[str, str]) -> dict[str, Any]:
    """Run button: deterministic checks only, no grading, no XP, no twin update."""
    # A verified workspace is the project's history: the cumulative preview and
    # every later ticket's opening files are composed from it. Run awards nothing
    # and re-grades nothing, so it must not be able to replace that work with a
    # scratch edit — which silently blanked the preview while the ticket still
    # read `done`. The buffer is still graded, so the feedback describes what the
    # learner actually typed; only the write is withheld.
    if ticket.status == "done":
        merged = workspace_with(ticket, files)
    else:
        merged = save_workspace(db, ticket, files)
    checks = (ticket.validation_spec or {}).get("checks", [])
    provided = render_bundle_for(db, ticket)
    static = [o.to_dict() for o in run_static_checks(merged, checks, render_files=provided)]
    behaviour = await _run_ticket_behaviour_tests(ticket, merged)
    # Display only, and built from a separate file map: the checks above have
    # already run against `merged` alone.
    preview = build_project_preview(db, ticket, merged)
    return {
        **_render_debug_field(merged, checks, provided),
        "config_errors": [s["id"] for s in static if s.get("config_error")],
        "static_results": static,
        # passed_count/total_count describe the static layer only; the behaviour
        # layer is reported separately so the two are never conflated.
        "passed_count": sum(1 for s in static if s["passed"]),
        "total_count": len(static),
        "test_results": behaviour,
        "tests_passed_count": sum(1 for t in behaviour if t["passed"]),
        "tests_total_count": len(behaviour),
        "preview": preview["html"],
        "preview_meta": preview["meta"],
        "preview_files": preview["files"],
    }


async def submit_ticket(
    db: Session,
    twin: LearningDigitalTwin,
    ticket: Ticket,
    files: dict[str, str],
    duration_seconds: float = 0.0,
) -> dict[str, Any]:
    if ticket.status == "locked":
        raise PermissionError(ticket.lock_reason or "This ticket is locked.")

    merged = save_workspace(db, ticket, files)
    graph = get_knowledge_graph()
    skill_id = ticket.target_skill_id

    ticket.status = "under_review"
    db.flush()

    checks = (ticket.validation_spec or {}).get("checks", [])
    provided = render_bundle_for(db, ticket)
    static_results = [
        o.to_dict() for o in run_static_checks(merged, checks, render_files=provided)
    ]
    test_results = await _run_ticket_behaviour_tests(ticket, merged)
    # A configuration error is our bug, so it is never attributed to the learner:
    # it is kept out of the failure analysis and out of the missing-concepts the
    # twin learns from. It still blocks verification — a check that never looked
    # at the submission cannot credit it — which is the same fail-closed rule an
    # unavailable browser follows.
    config_errors = [c for c in static_results if c.get("config_error")]
    failed_checks = [
        c
        for c in static_results + test_results
        if not c["passed"] and not c.get("config_error")
    ]
    deterministic_pass = bool(static_results) and not failed_checks and not config_errors

    submission_text = "\n\n".join(
        f"/* {name} */\n{content}" for name, content in merged.items()
    )

    provider = get_ai_provider()
    evaluation = await provider.evaluate(
        EvaluationRequest(
            skill_id=skill_id,
            skill_name=graph.name_of(skill_id),
            task_context=f"{ticket.key} · {ticket.title}\n\n{ticket.description}\n\n"
            + "Acceptance criteria:\n"
            + "\n".join(f"- {c}" for c in (ticket.acceptance_criteria or [])),
            requirements=ticket.requirements or [],
            user_submission=submission_text,
            language="web",
            current_difficulty=ticket.difficulty,
            deterministic_results=static_results + test_results,
        )
    )

    passed = deterministic_pass and evaluation.is_correct
    if not deterministic_pass:
        evaluation = EvaluationResult(**{**evaluation.model_dump(), "is_correct": False})

    xp_awarded = 0
    failure = None
    newly_unlocked: list[dict[str, Any]] = []
    milestone_bonus = 0

    # Read before the scoring engine overwrites it, otherwise the pre-attempt
    # value is gone and no honest delta can ever be shown.
    confidence_before = twin_service.confidence_of(twin, skill_id)

    if passed:
        ticket.status = "done"
        ticket.completed_at = datetime.now(timezone.utc)
        twin_service.record_execution_outcome(db, twin, skill_id, True, ticket.difficulty)
        xp_awarded = ticket.xp_reward
        reward_service.award_xp(
            db, twin, xp_awarded, f"Completed ticket {ticket.key}", "ticket", ticket.id
        )
        failure_analysis_service.resolve_open_analyses(db, twin.user_id, [skill_id])

        project = ticket.sprint.project
        sprint_completed = all(t.status == "done" for t in ticket.sprint.tickets)
        if sprint_completed:
            milestone_bonus = reward_service.XP_TABLE["milestone"]
            reward_service.award_xp(
                db,
                twin,
                milestone_bonus,
                f"Completed sprint: {ticket.sprint.name}",
                "milestone",
                ticket.sprint_id,
            )
        sprint_generator.recompute_project_progress(project)
        newly_unlocked = sprint_generator.refresh_ticket_locks(db, project, twin)
        if project.status == "completed":
            twin.completed_projects += 1
        twin.active_ticket_id = None
        twin_service.register_activity(
            db,
            twin.user_id,
            "ticket_completed",
            f"Completed {ticket.key}: {ticket.title}",
            f"+{xp_awarded + milestone_bonus} XP"
            + (f" · unlocked {len(newly_unlocked)} ticket(s)" if newly_unlocked else ""),
            {
                "ticket_id": ticket.id,
                "unlocked": newly_unlocked,
                "skill_id": skill_id,
                "confidence_before": confidence_before,
                "confidence_after": twin_service.confidence_of(twin, skill_id),
            },
        )
    else:
        ticket.status = "failed"
        twin_service.record_execution_outcome(
            db, twin, skill_id, False, ticket.difficulty, evaluation.missing_concepts
        )
        analysis = failure_analysis_service.analyze_failure(
            db, twin, skill_id, "ticket", ticket.id, evaluation, failed_checks
        )
        failure = failure_analysis_service.analysis_to_dict(analysis)
        twin_service.register_activity(
            db,
            twin.user_id,
            "ticket_failed",
            f"{ticket.key} needs rework",
            analysis.root_cause,
            {
                "ticket_id": ticket.id,
                "failure_analysis_id": analysis.id,
                "skill_id": skill_id,
                "confidence_before": confidence_before,
                "confidence_after": twin_service.confidence_of(twin, skill_id),
            },
        )

    twin_service.touch_activity_metrics(db, twin, duration_seconds)

    attempt = TicketAttempt(
        ticket_id=ticket.id,
        user_id=twin.user_id,
        submitted_files=dict(merged),
        passed=passed,
        static_results=static_results,
        test_results=test_results,
        ai_evaluation=evaluation.model_dump(),
        duration_seconds=duration_seconds,
        confidence_before=confidence_before,
        confidence_after=twin_service.confidence_of(twin, skill_id),
    )
    db.add(attempt)
    db.flush()

    skill = twin_service.get_or_create_skill(db, twin, skill_id)
    return {
        **_render_debug_field(merged, checks, provided),
        "attempt_id": attempt.id,
        "ticket": ticket_to_dict(ticket),
        "passed": passed,
        # Present and empty in the normal case, so a client can say "the grader
        # is broken" rather than having to infer it from a failing check.
        "config_errors": [c["id"] for c in config_errors],
        "static_results": static_results,
        "test_results": test_results,
        "passed_count": sum(1 for s in static_results if s["passed"]),
        "total_count": len(static_results),
        "tests_passed_count": sum(1 for t in test_results if t["passed"]),
        "tests_total_count": len(test_results),
        "evaluation": evaluation.model_dump(),
        "xp_awarded": xp_awarded + milestone_bonus,
        "milestone_bonus": milestone_bonus,
        "failure_analysis": failure,
        "unlocked_tickets": newly_unlocked,
        "skill": {
            "skill_id": skill.skill_id,
            "skill_name": skill.skill_name,
            "confidence": skill.confidence,
            "verified_level": skill.verified_level,
        },
        "overall_confidence": twin.overall_confidence,
        "xp": twin.xp,
        "level": twin.level,
    }


def reset_ticket(db: Session, ticket: Ticket) -> dict[str, Any]:
    """Discard this ticket's edits and reopen it on the state it started from.

    Reset goes back to the ticket's own starting point — the project as the
    previous tickets left it — not to a blank template, which would delete work
    the learner did in earlier tickets and never get it back.

    A verified ticket is not reset: its workspace is the record of what was
    graded, and rewriting that would rewrite project history for every ticket
    that inherits from it.
    """
    if ticket.status == "done":
        return ticket_to_dict(ticket, include_files=True, db=db)

    ticket.workspace_files = opening_files(db, ticket)
    if ticket.status in {"failed", "under_review", "submitted"}:
        ticket.status = "in_progress"
    db.flush()
    return ticket_to_dict(ticket, include_files=True, db=db)
