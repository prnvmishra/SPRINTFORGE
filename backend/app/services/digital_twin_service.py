"""Owns all mutations of the Learning Digital Twin."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ActivityLog, LearningDigitalTwin, User, VerifiedSkill
from app.services.knowledge_graph import get_knowledge_graph
from app.services.scoring_engine import (
    compute_skill_confidence,
    explain_low_score,
    recompute_overall_confidence,
    verified_level_for,
)

CLAIMED_LEVEL_SEED = {"beginner": 1, "intermediate": 2, "advanced": 3}


def get_or_create_twin(db: Session, user: User) -> LearningDigitalTwin:
    twin = db.scalar(select(LearningDigitalTwin).where(LearningDigitalTwin.user_id == user.id))
    if twin is None:
        twin = LearningDigitalTwin(user_id=user.id)
        db.add(twin)
        db.flush()
    return twin


def get_or_create_skill(db: Session, twin: LearningDigitalTwin, skill_id: str) -> VerifiedSkill:
    graph = get_knowledge_graph()
    for skill in twin.verified_skills:
        if skill.skill_id == skill_id:
            return skill
    skill = VerifiedSkill(
        twin_id=twin.id,
        skill_id=skill_id,
        skill_name=graph.name_of(skill_id),
        weak_concepts=[],
        score_breakdown={},
    )
    db.add(skill)
    twin.verified_skills.append(skill)
    db.flush()
    return skill


def confidence_map(twin: LearningDigitalTwin) -> dict[str, float]:
    return {skill.skill_id: skill.confidence for skill in twin.verified_skills}


def confidence_of(twin: LearningDigitalTwin, skill_id: str) -> Optional[float]:
    """Current verified confidence, or None when the twin has no row for it.

    None is meaningful: it means "we have never scored this", which is not the
    same as 0.0. Callers recording a before/after pair must keep the distinction
    so no invented baseline ever reaches the learner.
    """
    for skill in twin.verified_skills:
        if skill.skill_id == skill_id:
            return skill.confidence
    return None


def evidence_set(twin: LearningDigitalTwin) -> set[str]:
    """Skills the twin has real evidence about (an attempt was actually graded)."""
    return {
        skill.skill_id
        for skill in twin.verified_skills
        if (skill.assessment_total + skill.execution_total) > 0
    }


def demonstrated_set(twin: LearningDigitalTwin) -> set[str]:
    """Skills proven by doing: a graded pass at or above the skill's own difficulty."""
    graph = get_knowledge_graph()
    demonstrated: set[str] = set()
    for skill in twin.verified_skills:
        node = graph.get(skill.skill_id)
        required = node.difficulty_weight if node else 3
        if skill.execution_passed > 0 and skill.hardest_difficulty_passed >= required:
            demonstrated.add(skill.skill_id)
    return demonstrated


def gating_context(twin: LearningDigitalTwin) -> tuple[dict[str, float], set[str], set[str]]:
    """Everything the knowledge graph needs to decide what is unlocked."""
    return confidence_map(twin), evidence_set(twin), demonstrated_set(twin)


def _rescore(db: Session, twin: LearningDigitalTwin, skill: VerifiedSkill) -> None:
    result = compute_skill_confidence(skill)
    skill.confidence = result["confidence"]
    skill.score_breakdown = result["breakdown"]
    skill.verified_level = verified_level_for(skill.confidence)
    recompute_overall_confidence(twin)
    db.flush()


def set_claimed_skills(db: Session, twin: LearningDigitalTwin, claimed: dict[str, str]) -> None:
    twin.claimed_skills = dict(claimed)
    for skill_id, level in claimed.items():
        skill = get_or_create_skill(db, twin, skill_id)
        skill.claimed_level = level
        _rescore(db, twin, skill)


def record_assessment_outcome(
    db: Session,
    twin: LearningDigitalTwin,
    skill_id: str,
    is_correct: bool,
    difficulty: int,
    missing_concepts: Optional[Iterable[str]] = None,
) -> VerifiedSkill:
    skill = get_or_create_skill(db, twin, skill_id)
    skill.assessment_total += 1
    if is_correct:
        skill.assessment_correct += 1
        skill.attempts_streak += 1
        skill.hardest_difficulty_passed = max(skill.hardest_difficulty_passed, difficulty)
    else:
        skill.attempts_streak = 0
        _register_weak_concepts(twin, skill, missing_concepts or [])
    skill.consistency_signal = _update_consistency(skill, is_correct)
    _rescore(db, twin, skill)
    return skill


def record_execution_outcome(
    db: Session,
    twin: LearningDigitalTwin,
    skill_id: str,
    passed: bool,
    difficulty: int,
    missing_concepts: Optional[Iterable[str]] = None,
) -> VerifiedSkill:
    skill = get_or_create_skill(db, twin, skill_id)
    skill.execution_total += 1
    if passed:
        skill.execution_passed += 1
        skill.attempts_streak += 1
        skill.hardest_difficulty_passed = max(skill.hardest_difficulty_passed, difficulty)
        _clear_weak_concepts(twin, skill, missing_concepts or [])
    else:
        skill.attempts_streak = 0
        _register_weak_concepts(twin, skill, missing_concepts or [])
    skill.consistency_signal = _update_consistency(skill, passed)
    _rescore(db, twin, skill)
    return skill


CONSISTENCY_ALPHA = 0.4


def _update_consistency(skill: VerifiedSkill, success: bool) -> float:
    """Exponential moving average of recent outcomes.

    A single slip should dent consistency, not erase it, and a streak should not
    reach full marks instantly — so early attempts are also floor-limited by the
    raw streak.
    """
    previous = float(skill.consistency_signal or 0.0)
    updated = previous * (1 - CONSISTENCY_ALPHA) + (1.0 if success else 0.0) * CONSISTENCY_ALPHA
    if success:
        updated = min(updated, min(1.0, skill.attempts_streak / 3.0))
    return round(max(0.0, min(1.0, updated)), 4)


def _register_weak_concepts(
    twin: LearningDigitalTwin, skill: VerifiedSkill, concepts: Iterable[str]
) -> None:
    weak = list(skill.weak_concepts or [])
    mistakes = dict(twin.repeated_mistakes or {})
    for concept in concepts:
        if not concept:
            continue
        if concept not in weak:
            weak.append(concept)
        mistakes[concept] = int(mistakes.get(concept, 0)) + 1
    skill.weak_concepts = weak
    twin.repeated_mistakes = mistakes


def _clear_weak_concepts(
    twin: LearningDigitalTwin, skill: VerifiedSkill, concepts: Iterable[str]
) -> None:
    resolved = {c for c in concepts if c}
    if not resolved:
        return
    skill.weak_concepts = [c for c in (skill.weak_concepts or []) if c not in resolved]


def register_activity(
    db: Session,
    user_id: str,
    event_type: str,
    title: str,
    detail: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
) -> ActivityLog:
    log = ActivityLog(
        user_id=user_id, event_type=event_type, title=title, detail=detail, meta=meta or {}
    )
    db.add(log)
    db.flush()
    return log


def touch_activity_metrics(
    db: Session, twin: LearningDigitalTwin, duration_seconds: float = 0.0
) -> None:
    """Update streak, average completion time and learning velocity."""
    now = datetime.now(timezone.utc)
    last = twin.last_active_date
    if last is not None:
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        delta_days = (now.date() - last.date()).days
        if delta_days == 1:
            twin.streak_days += 1
        elif delta_days > 1:
            twin.streak_days = 1
    else:
        twin.streak_days = 1
    twin.last_active_date = now

    if duration_seconds > 0:
        previous = twin.avg_completion_seconds or 0.0
        twin.avg_completion_seconds = round(
            duration_seconds if previous == 0 else (previous * 0.7 + duration_seconds * 0.3), 1
        )

    recent_cutoff = now - timedelta(days=7)
    recent = db.scalars(
        select(ActivityLog).where(
            ActivityLog.user_id == twin.user_id, ActivityLog.created_at >= recent_cutoff
        )
    ).all()
    twin.learning_velocity = round(len(recent) / 7.0, 2)
    twin.consistency_score = round(min(100.0, twin.streak_days * 12.5), 1)
    db.flush()


def plain_summary(skill: VerifiedSkill) -> str:
    """One jargon-free sentence a first-time user can act on.

    `explain_low_score` is the precise, auditable version; this is the version we
    put in front of someone who does not know what "difficulty mastery" means.
    """
    graph = get_knowledge_graph()
    threshold = graph.confidence_threshold
    breakdown = skill.score_breakdown or {}
    limiting = breakdown.get("limiting_factor")
    evidence = skill.assessment_total + skill.execution_total

    if evidence == 0:
        return "You told us you know this, but you haven't proved it yet. A short check will set your real score."
    if skill.weak_concepts:
        return f"You keep slipping on {skill.weak_concepts[0]}. Practise that one thing and this score moves."
    if skill.confidence >= threshold:
        return "Proved. You can build on this."
    if limiting == "assessment_accuracy":
        return "Your answers were mostly wrong on the harder questions, so this isn't proved yet."
    if limiting == "execution_success":
        return "Your code is failing more often than it passes. Fix one failing task to lift this."
    if limiting == "difficulty_mastery":
        return "You've only passed the easy version of this. Try one at the real difficulty."
    if limiting == "consistency":
        return "You get it right sometimes but not reliably. A couple of clean runs will settle it."
    return "Not proved yet. Practise once and this score updates."


def next_action_for(skill: VerifiedSkill) -> dict[str, Any]:
    """The single most useful thing this learner can do about this skill."""
    graph = get_knowledge_graph()
    node = graph.get(skill.skill_id)
    modules = list(node.recommended_practice) if node else []

    if skill.assessment_total == 0:
        return {
            "kind": "assessment",
            "label": "Take the quick check",
            "skill_id": skill.skill_id,
            "module_id": None,
        }
    return {
        "kind": "practice",
        "label": "Practise this",
        "skill_id": skill.skill_id,
        "module_id": modules[0] if modules else None,
    }


def skill_report(twin: LearningDigitalTwin) -> list[dict[str, Any]]:
    graph = get_knowledge_graph()
    report: list[dict[str, Any]] = []
    for skill in sorted(twin.verified_skills, key=lambda s: s.confidence, reverse=True):
        node = graph.get(skill.skill_id)
        report.append(
            {
                "skill_id": skill.skill_id,
                "skill_name": skill.skill_name,
                "claimed_level": skill.claimed_level,
                "verified_level": skill.verified_level,
                "confidence": skill.confidence,
                "needs_improvement": skill.confidence < graph.confidence_threshold,
                "weak_concepts": skill.weak_concepts or [],
                "breakdown": skill.score_breakdown or {},
                "explanation": explain_low_score(skill),
                "plain_summary": plain_summary(skill),
                "next_action": next_action_for(skill),
                "difficulty_weight": node.difficulty_weight if node else 3,
                "evidence": {
                    "assessment_correct": skill.assessment_correct,
                    "assessment_total": skill.assessment_total,
                    "execution_passed": skill.execution_passed,
                    "execution_total": skill.execution_total,
                    "hardest_difficulty_passed": skill.hardest_difficulty_passed,
                },
            }
        )
    return report
