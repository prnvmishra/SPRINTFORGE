"""Turns a failed submission into a root cause, a conceptual gap and a remediation plan."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.practice_modules import PRACTICE_MODULES
from app.models import FailureAnalysis, LearningDigitalTwin
from app.schemas.ai import EvaluationResult
from app.services.knowledge_graph import get_knowledge_graph


def find_remediation_module(
    skill_id: str, missing_concepts: list[str]
) -> Optional[dict[str, Any]]:
    """Prefer a module explicitly designed to remediate the failed concept."""
    normalized = {c.strip().lower() for c in missing_concepts if c}

    for module in PRACTICE_MODULES:
        if not module.get("is_remediation"):
            continue
        targets = {c.lower() for c in module.get("remediates_concepts", [])}
        if normalized & targets:
            return module

    graph = get_knowledge_graph()
    node = graph.get(skill_id)
    if node:
        for module_id in node.recommended_practice:
            for module in PRACTICE_MODULES:
                if module["id"] == module_id:
                    return module

    # Otherwise route to the weakest prerequisite that owns the failed concept.
    for concept in normalized:
        resolved = graph.resolve_skill_from_concept(concept)
        resolved_node = graph.get(resolved) if resolved else None
        if resolved_node:
            for module_id in resolved_node.recommended_practice:
                for module in PRACTICE_MODULES:
                    if module["id"] == module_id:
                        return module
    return None


def analyze_failure(
    db: Session,
    twin: LearningDigitalTwin,
    skill_id: str,
    source_type: str,
    source_id: Optional[str],
    evaluation: EvaluationResult,
    failed_checks: list[dict[str, Any]],
) -> FailureAnalysis:
    graph = get_knowledge_graph()
    skill_name = graph.name_of(skill_id)

    missing_concepts = list(evaluation.missing_concepts)
    for check in failed_checks:
        concept = check.get("concept")
        if concept and concept not in missing_concepts:
            missing_concepts.append(concept)

    root_cause = evaluation.conceptual_mistake or (
        f"Unmet requirement: {failed_checks[0].get('label')}" if failed_checks else "Requirements not met."
    )

    mistakes = twin.repeated_mistakes or {}
    repeats = [c for c in missing_concepts if int(mistakes.get(c, 0)) > 1]

    module = find_remediation_module(skill_id, missing_concepts)

    explanation_parts = [
        f"Root cause: {root_cause}",
        f"Missing concept{'s' if len(missing_concepts) != 1 else ''}: "
        + (", ".join(missing_concepts) if missing_concepts else skill_name)
        + ".",
    ]
    if failed_checks:
        explanation_parts.append(
            "Failing checks: " + "; ".join(c.get("label", "check") for c in failed_checks[:4]) + "."
        )
    if repeats:
        explanation_parts.append(
            "You have now hit " + ", ".join(repeats) + " more than once, so this is a pattern rather than a slip."
        )
    if module:
        explanation_parts.append(
            f"Recommended next step: complete the micro-practice \"{module['title']}\", "
            "then resubmit this task to re-verify the skill."
        )

    analysis = FailureAnalysis(
        user_id=twin.user_id,
        source_type=source_type,
        source_id=source_id,
        skill_id=skill_id,
        root_cause=root_cause,
        missing_concepts=missing_concepts,
        explanation=" ".join(explanation_parts),
        remediation_module_id=module["id"] if module else None,
        remediation_title=module["title"] if module else None,
    )
    db.add(analysis)
    db.flush()
    return analysis


def resolve_open_analyses(db: Session, user_id: str, concepts: list[str]) -> int:
    """Mark previously diagnosed gaps as resolved once the learner succeeds."""
    if not concepts:
        return 0
    open_analyses = db.scalars(
        select(FailureAnalysis).where(
            FailureAnalysis.user_id == user_id, FailureAnalysis.resolved.is_(False)
        )
    ).all()
    resolved_count = 0
    target = {c.strip().lower() for c in concepts if c}
    for analysis in open_analyses:
        owned = {c.strip().lower() for c in (analysis.missing_concepts or [])}
        if owned & target:
            analysis.resolved = True
            resolved_count += 1
    db.flush()
    return resolved_count


def analysis_to_dict(analysis: FailureAnalysis) -> dict[str, Any]:
    return {
        "id": analysis.id,
        "skill_id": analysis.skill_id,
        "skill_name": get_knowledge_graph().name_of(analysis.skill_id),
        "source_type": analysis.source_type,
        "source_id": analysis.source_id,
        "root_cause": analysis.root_cause,
        "missing_concepts": analysis.missing_concepts or [],
        "explanation": analysis.explanation,
        "remediation_module_id": analysis.remediation_module_id,
        "remediation_title": analysis.remediation_title,
        "resolved": analysis.resolved,
        "created_at": analysis.created_at,
    }
