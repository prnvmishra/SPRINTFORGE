"""Deterministic SprintForge Confidence Score.

Confidence = 40% assessment accuracy
           + 25% code execution success
           + 20% task difficulty mastery
           + 15% consistency
"""

from __future__ import annotations

from typing import Any

from app.models import LearningDigitalTwin, VerifiedSkill
from app.services.knowledge_graph import get_knowledge_graph

WEIGHTS = {
    "assessment_accuracy": 0.40,
    "execution_success": 0.25,
    "difficulty_mastery": 0.20,
    "consistency": 0.15,
}

MAX_DIFFICULTY = 10


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return max(0.0, min(1.0, numerator / denominator))


def compute_skill_confidence(skill: VerifiedSkill) -> dict[str, Any]:
    graph = get_knowledge_graph()
    node = graph.get(skill.skill_id)
    expected_difficulty = node.difficulty_weight if node else 5

    assessment_accuracy = _ratio(skill.assessment_correct, skill.assessment_total)
    execution_success = _ratio(skill.execution_passed, skill.execution_total)

    # Difficulty mastery compares the hardest passed task against the skill's
    # expected difficulty, so passing only trivial tasks cannot yield mastery.
    target = max(expected_difficulty, 1)
    difficulty_mastery = max(0.0, min(1.0, skill.hardest_difficulty_passed / target))

    consistency = max(0.0, min(1.0, float(skill.consistency_signal)))

    components = {
        "assessment_accuracy": assessment_accuracy,
        "execution_success": execution_success,
        "difficulty_mastery": difficulty_mastery,
        "consistency": consistency,
    }

    evidence = skill.assessment_total + skill.execution_total

    # A channel that was never exercised is unknown, not zero. Weights are
    # renormalised over the active channels so a learner is never penalised for
    # evidence SprintForge has not asked for yet. The published 40/25/20/15
    # ratios are preserved among whichever channels are active.
    active = {
        "assessment_accuracy": skill.assessment_total > 0,
        "execution_success": skill.execution_total > 0,
        "difficulty_mastery": evidence > 0,
        "consistency": evidence > 0,
    }
    active_weight = sum(WEIGHTS[k] for k, is_active in active.items() if is_active)
    if active_weight > 0:
        raw = (
            sum(components[k] * WEIGHTS[k] for k, is_active in active.items() if is_active)
            / active_weight
        ) * 100
    else:
        raw = 0.0

    # With very little evidence we damp the score so a single lucky answer
    # cannot mark a skill as verified.
    evidence_factor = min(1.0, 0.55 + 0.15 * evidence)
    confidence = round(raw * evidence_factor, 1)

    breakdown = {
        "components": {k: round(v * 100, 1) for k, v in components.items()},
        "weights": {k: int(v * 100) for k, v in WEIGHTS.items()},
        "active_channels": [k for k, is_active in active.items() if is_active],
        "effective_weights": {
            k: round(WEIGHTS[k] / active_weight * 100, 1) if active_weight and active[k] else 0.0
            for k in WEIGHTS
        },
        "contributions": {
            k: round(components[k] * WEIGHTS[k] / active_weight * 100, 1)
            if active_weight and active[k]
            else 0.0
            for k in WEIGHTS
        },
        "evidence_count": evidence,
        "evidence_factor": round(evidence_factor, 2),
        "expected_difficulty": expected_difficulty,
        "hardest_difficulty_passed": skill.hardest_difficulty_passed,
        "raw_score": round(raw, 1),
        "final_score": confidence,
        "limiting_factor": min(
            (k for k in WEIGHTS if active[k]),
            key=lambda k: components[k],
            default="assessment_accuracy",
        ),
    }
    return {"confidence": confidence, "breakdown": breakdown}


def verified_level_for(confidence: float) -> str:
    if confidence >= 85:
        return "advanced"
    if confidence >= 65:
        return "intermediate"
    if confidence >= 40:
        return "beginner"
    return "needs_improvement"


def explain_low_score(skill: VerifiedSkill) -> str:
    breakdown = skill.score_breakdown or {}
    components = breakdown.get("components", {})
    if not components:
        return "No evidence recorded yet. Take an assessment or complete a practice module to generate a score."

    limiting = breakdown.get("limiting_factor", "assessment_accuracy")
    labels = {
        "assessment_accuracy": "assessment accuracy",
        "execution_success": "code execution success rate",
        "difficulty_mastery": "difficulty mastery (you have not yet passed tasks at this skill's expected level)",
        "consistency": "consistency across recent attempts",
    }
    parts = [
        f"Confidence is {skill.confidence}% because your weakest signal is {labels.get(limiting, limiting)} "
        f"at {components.get(limiting, 0)}%."
    ]
    if skill.weak_concepts:
        parts.append("Recurring gaps: " + ", ".join(skill.weak_concepts[:4]) + ".")
    if breakdown.get("evidence_factor", 1) < 1:
        parts.append(
            f"Only {breakdown.get('evidence_count', 0)} evidence points exist, so the score is intentionally damped "
            "until you produce more verified work."
        )
    return " ".join(parts)


def recompute_overall_confidence(twin: LearningDigitalTwin) -> float:
    """Difficulty-weighted mean of all skill confidences."""
    graph = get_knowledge_graph()
    numerator = 0.0
    denominator = 0.0
    for skill in twin.verified_skills:
        node = graph.get(skill.skill_id)
        weight = node.difficulty_weight if node else 3
        numerator += skill.confidence * weight
        denominator += weight
    overall = round(numerator / denominator, 1) if denominator else 0.0
    twin.overall_confidence = overall
    return overall
