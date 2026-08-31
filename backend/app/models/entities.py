import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.services import spec_interpolation


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(40), default="credentials")
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String(280), nullable=True)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False)

    twin: Mapped[Optional["LearningDigitalTwin"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class LearningDigitalTwin(Base, TimestampMixin):
    """Continuously updated model of what the learner can actually do."""

    __tablename__ = "learning_digital_twins"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)

    goal: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    experience_level: Mapped[str] = mapped_column(String(40), default="beginner")
    claimed_skills: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Placement: the learner declares a career path, then proves where they
    # actually stand before anything is recommended. `placement_sessions` maps a
    # probed skill_id to the AssessmentSession that probed it, so the result is
    # always recomputable from graded evidence rather than a stored score.
    path_id: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    placement_status: Mapped[str] = mapped_column(String(20), default="pending")
    placement_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    placement_sessions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    placement_result: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    overall_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    repeated_mistakes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    preferred_difficulty: Mapped[int] = mapped_column(Integer, default=3)
    avg_completion_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0)
    learning_velocity: Mapped[float] = mapped_column(Float, default=0.0)
    completed_projects: Mapped[int] = mapped_column(Integer, default=0)

    active_project_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    active_ticket_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    user: Mapped["User"] = relationship(back_populates="twin")
    verified_skills: Mapped[list["VerifiedSkill"]] = relationship(
        back_populates="twin", cascade="all, delete-orphan"
    )


class VerifiedSkill(Base, TimestampMixin):
    __tablename__ = "verified_skills"
    __table_args__ = (UniqueConstraint("twin_id", "skill_id", name="uq_twin_skill"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    twin_id: Mapped[str] = mapped_column(ForeignKey("learning_digital_twins.id", ondelete="CASCADE"), index=True)

    skill_id: Mapped[str] = mapped_column(String(80), index=True)
    skill_name: Mapped[str] = mapped_column(String(120))
    claimed_level: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    verified_level: Mapped[str] = mapped_column(String(40), default="unverified")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Raw signals feeding the deterministic confidence formula.
    assessment_correct: Mapped[int] = mapped_column(Integer, default=0)
    assessment_total: Mapped[int] = mapped_column(Integer, default=0)
    execution_passed: Mapped[int] = mapped_column(Integer, default=0)
    execution_total: Mapped[int] = mapped_column(Integer, default=0)
    hardest_difficulty_passed: Mapped[int] = mapped_column(Integer, default=0)
    attempts_streak: Mapped[int] = mapped_column(Integer, default=0)
    consistency_signal: Mapped[float] = mapped_column(Float, default=0.0)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    weak_concepts: Mapped[list[str]] = mapped_column(JSON, default=list)

    twin: Mapped["LearningDigitalTwin"] = relationship(back_populates="verified_skills")


class AssessmentSession(Base, TimestampMixin):
    __tablename__ = "assessment_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[str] = mapped_column(String(80), index=True)
    claimed_level: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="in_progress")
    current_difficulty: Mapped[int] = mapped_column(Integer, default=2)
    questions_asked: Mapped[int] = mapped_column(Integer, default=0)
    max_questions: Mapped[int] = mapped_column(Integer, default=5)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    asked_question_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    result: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    attempts: Mapped[list["AssessmentAttempt"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class AssessmentAttempt(Base, TimestampMixin):
    __tablename__ = "assessment_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("assessment_sessions.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[str] = mapped_column(String(80))
    question_type: Mapped[str] = mapped_column(String(40))
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    concept: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    user_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    evaluation: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    session: Mapped["AssessmentSession"] = relationship(back_populates="attempts")


class PracticeAttempt(Base, TimestampMixin):
    __tablename__ = "practice_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    module_id: Mapped[str] = mapped_column(String(120), index=True)
    skill_id: Mapped[str] = mapped_column(String(80), index=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    submitted_files: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    static_results: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    test_results: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    ai_evaluation: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    # Verified confidence for the target skill immediately before and after this
    # attempt was scored. NULL means "not captured", never "no change".
    confidence_before: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_after: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    idea: Mapped[str] = mapped_column(Text)
    tech_stack: Mapped[list[str]] = mapped_column(JSON, default=list)
    complexity: Mapped[str] = mapped_column(String(40), default="intermediate")
    desired_outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    plan_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="projects")
    sprints: Mapped[list["Sprint"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="Sprint.order_index"
    )


class Sprint(Base, TimestampMixin):
    __tablename__ = "sprints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    milestone: Mapped[str] = mapped_column(String(160), default="Milestone")
    name: Mapped[str] = mapped_column(String(160))
    goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="todo")

    project: Mapped["Project"] = relationship(back_populates="sprints")
    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="sprint", cascade="all, delete-orphan", order_by="Ticket.order_index"
    )


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    sprint_id: Mapped[str] = mapped_column(ForeignKey("sprints.id", ondelete="CASCADE"), index=True)
    key: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    target_skill_id: Mapped[str] = mapped_column(String(80), index=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=3)
    requirements: Mapped[list[str]] = mapped_column(JSON, default=list)
    acceptance_criteria: Mapped[list[str]] = mapped_column(JSON, default=list)
    dependencies: Mapped[list[str]] = mapped_column(JSON, default=list)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="locked")
    lock_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    validation_spec: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    starter_files: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    workspace_files: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    xp_reward: Mapped[int] = mapped_column(Integer, default=30)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    sprint: Mapped["Sprint"] = relationship(back_populates="tickets")
    attempts: Mapped[list["TicketAttempt"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )


class TicketAttempt(Base, TimestampMixin):
    __tablename__ = "ticket_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    submitted_files: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    static_results: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    test_results: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    ai_evaluation: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    # See PracticeAttempt: NULL means "not captured", never "no change".
    confidence_before: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_after: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    ticket: Mapped["Ticket"] = relationship(back_populates="attempts")


class ExecutionAttempt(Base, TimestampMixin):
    """Raw sandboxed code-execution record (language challenges, run button)."""

    __tablename__ = "execution_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    context_type: Mapped[str] = mapped_column(String(40), default="practice")
    context_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    language: Mapped[str] = mapped_column(String(40))
    provider: Mapped[str] = mapped_column(String(40), default="local")
    source_code: Mapped[str] = mapped_column(Text)
    passed_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    results: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)


class FailureAnalysis(Base, TimestampMixin):
    __tablename__ = "failure_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(String(40))
    source_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    skill_id: Mapped[str] = mapped_column(String(80), index=True)
    root_cause: Mapped[str] = mapped_column(Text)
    missing_concepts: Mapped[list[str]] = mapped_column(JSON, default=list)
    explanation: Mapped[str] = mapped_column(Text)
    remediation_module_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    remediation_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)


class RewardTransaction(Base, TimestampMixin):
    __tablename__ = "reward_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str] = mapped_column(String(200))
    source_type: Mapped[str] = mapped_column(String(40), default="practice")
    source_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)


class CommunityPost(Base, TimestampMixin):
    """Discussion message attached to a practice module, one reply level deep."""

    __tablename__ = "community_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    module_id: Mapped[str] = mapped_column(String(120), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    body: Mapped[str] = mapped_column(Text)

    user: Mapped["User"] = relationship()


class ActivityLog(Base, TimestampMixin):
    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(String(200))
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


# --------------------------------------------------------------------------
# Write-time guard: a spec never reaches the database with a placeholder in it
# --------------------------------------------------------------------------


def _refuse_leak(target: "Ticket", field: str, leaked: list[str], hint: str) -> None:
    raise spec_interpolation.SpecInterpolationError(
        f"refusing to store {field} for ticket {getattr(target, 'key', '?')} "
        f"({getattr(target, 'target_skill_id', '?')}): it still contains the unresolved "
        f"placeholder(s) {leaked} — {hint}"
    )


@event.listens_for(Ticket.validation_spec, "set", retval=True)
def _reject_unresolved_placeholders(target: "Ticket", value: Any, _old: Any, _initiator: Any) -> Any:
    """Refuse an uninterpolated `validation_spec` at assignment time.

    The bug this exists for was not a bad selector, it was a *stored* bad
    selector: a script wrote raw template checks and every later Run Checks
    faithfully asked the browser for `#{entity}List`. Matching-time guards can
    only report that; this is the point where it can still be prevented, and it
    fires for every writer including ones that never heard of
    `spec_interpolation.build_validation_spec`.
    """
    leaked = spec_interpolation.unresolved_placeholders((value or {}).get("checks"))
    if leaked:
        _refuse_leak(
            target,
            "a validation_spec whose checks",
            leaked,
            "interpolate it through app.services.spec_interpolation.build_validation_spec()",
        )
    return value


@event.listens_for(Ticket.requirements, "set", retval=True)
@event.listens_for(Ticket.acceptance_criteria, "set", retval=True)
def _reject_unresolved_brief_placeholders(
    target: "Ticket", value: Any, _old: Any, initiator: Any
) -> Any:
    """Refuse an uninterpolated brief at assignment time.

    The spec guard above only covers what *grades* a ticket. The brief is what
    the learner *reads*, and it was left unguarded: a ticket could be stored
    promising `Make #{entity}List a grid`, which is both meaningless to read and
    a strong hint that the same leak is sitting in the checks beside it. Both
    halves have to resolve from one context or the displayed requirement and the
    selector it is graded by can drift apart.
    """
    leaked = spec_interpolation.unresolved_placeholders(value)
    if leaked:
        _refuse_leak(
            target,
            f"a {getattr(initiator, 'key', 'brief')} list",
            leaked,
            "interpolate it through app.services.spec_interpolation.fill(..., strict=True) "
            "with app.services.spec_interpolation.context_for_ticket(ticket)",
        )
    return value
