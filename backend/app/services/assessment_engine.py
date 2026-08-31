"""Adaptive skill-verification engine.

Difficulty walks up on success and down on failure. A wrong answer at the
learner's frontier triggers a diagnostic follow-up on the *same* concept one
level lower, which is how the exact conceptual gap gets isolated.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.data.assessment_bank import ITEM_INDEX, ITEMS_BY_SKILL
from app.models import AssessmentAttempt, AssessmentSession
from app.schemas.ai import EvaluationRequest, EvaluationResult
from app.services.ai_evaluator import get_ai_provider
from app.services.knowledge_graph import get_knowledge_graph

CLAIM_START_DIFFICULTY = {"beginner": 1, "intermediate": 4, "advanced": 6}


def start_difficulty_for_claim(claimed_level: Optional[str]) -> int:
    return CLAIM_START_DIFFICULTY.get((claimed_level or "beginner").lower(), 2)


def public_item(item: dict[str, Any]) -> dict[str, Any]:
    """Strip answers before sending an item to the client."""
    return {
        "id": item["id"],
        "skill_id": item["skill_id"],
        "type": item["type"],
        "difficulty": item["difficulty"],
        "concept": item.get("concept"),
        "prompt": item["prompt"],
        "code": item.get("code"),
        "options": item.get("options"),
        "language": item.get("language", "javascript"),
    }


def select_item(
    skill_id: str,
    target_difficulty: int,
    asked_ids: list[str],
    concept_focus: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    graph = get_knowledge_graph()
    pool = [i for i in ITEMS_BY_SKILL.get(skill_id, []) if i["id"] not in asked_ids]

    # When the learner needs an easier item than this skill offers, drop into the
    # prerequisite skills. That is the diagnostic follow-up: it isolates whether
    # the gap is in the skill itself or in its foundation.
    needs_easier = not pool or min(i["difficulty"] for i in pool) > target_difficulty
    if needs_easier:
        for prereq in reversed(graph.ancestors(skill_id)):
            fallback = [
                i
                for i in ITEMS_BY_SKILL.get(prereq, [])
                if i["id"] not in asked_ids and i["difficulty"] <= target_difficulty
            ]
            if fallback:
                pool = pool + fallback
                break

    if not pool:
        return None

    if concept_focus:
        focused = [i for i in pool if (i.get("concept") or "").lower() == concept_focus.lower()]
        if focused:
            pool = focused

    return min(pool, key=lambda i: (abs(i["difficulty"] - target_difficulty), i["difficulty"]))


def next_question(session: AssessmentSession) -> Optional[dict[str, Any]]:
    if session.questions_asked >= session.max_questions:
        return None
    concept_focus: Optional[str] = None
    if session.result and isinstance(session.result, dict):
        concept_focus = session.result.get("diagnostic_focus")
    return select_item(
        session.skill_id, session.current_difficulty, list(session.asked_question_ids or []), concept_focus
    )


async def evaluate_answer(item: dict[str, Any], answer: str, current_difficulty: int) -> EvaluationResult:
    """MCQs are graded deterministically; open items go through the AI evaluator."""
    if item["type"] == "mcq":
        try:
            chosen = int(str(answer).strip())
        except (TypeError, ValueError):
            chosen = -1
        is_correct = chosen == int(item["correct_option"])
        return EvaluationResult(
            is_correct=is_correct,
            conceptual_mistake=None if is_correct else item.get("concept"),
            next_difficulty=min(10, current_difficulty + 1) if is_correct else max(1, current_difficulty - 1),
            feedback=item.get("explanation", "Answer recorded."),
            missing_concepts=[] if is_correct else [item.get("concept") or item["skill_id"]],
            suggested_remediation=None if is_correct else f"Review {item.get('concept')}.",
            provider="deterministic",
        )

    # Layer 1 for open-ended items: deterministic regex signals.
    checks: list[dict[str, Any]] = []
    for index, pattern in enumerate(item.get("answer_checks", [])):
        matched = bool(re.search(pattern, answer or "", re.IGNORECASE | re.MULTILINE))
        checks.append(
            {
                "id": f"signal_{index + 1}",
                "label": f"Answer contains required signal {index + 1}",
                "passed": matched,
                "concept": item.get("concept"),
                "hint": item.get("explanation"),
            }
        )

    provider = get_ai_provider()
    result = await provider.evaluate(
        EvaluationRequest(
            skill_id=item["skill_id"],
            skill_name=get_knowledge_graph().name_of(item["skill_id"]),
            task_context=f"{item['prompt']}\n\n{item.get('code') or ''}",
            requirements=[item.get("explanation", "Answer the question correctly.")],
            user_submission=answer or "",
            language=item.get("language", "javascript"),
            current_difficulty=current_difficulty,
            deterministic_results=checks,
            expected_answer=item.get("expected_answer"),
        )
    )
    return result


def record_attempt(
    db: Session,
    session: AssessmentSession,
    item: dict[str, Any],
    answer: str,
    result: EvaluationResult,
    duration_seconds: float = 0.0,
) -> AssessmentAttempt:
    attempt = AssessmentAttempt(
        session_id=session.id,
        question_id=item["id"],
        question_type=item["type"],
        difficulty=item["difficulty"],
        concept=item.get("concept"),
        user_answer=answer,
        is_correct=result.is_correct,
        evaluation=result.model_dump(),
        duration_seconds=duration_seconds,
    )
    db.add(attempt)

    session.questions_asked += 1
    session.asked_question_ids = list(session.asked_question_ids or []) + [item["id"]]
    if result.is_correct:
        session.correct_count += 1
        session.current_difficulty = min(10, max(session.current_difficulty, item["difficulty"]) + 1)
        state = dict(session.result or {})
        state.pop("diagnostic_focus", None)
        session.result = state
    else:
        session.current_difficulty = max(1, item["difficulty"] - 1)
        # Queue a diagnostic follow-up on the same concept, one level easier.
        state = dict(session.result or {})
        state["diagnostic_focus"] = item.get("concept")
        session.result = state

    db.flush()
    return attempt


def finalize_session(db: Session, session: AssessmentSession) -> dict[str, Any]:
    graph = get_knowledge_graph()
    attempts = sorted(session.attempts, key=lambda a: a.created_at)

    total = len(attempts)
    correct = sum(1 for a in attempts if a.is_correct)
    accuracy = round(correct / total * 100, 1) if total else 0.0
    hardest_passed = max((a.difficulty for a in attempts if a.is_correct), default=0)
    hardest_failed = min((a.difficulty for a in attempts if not a.is_correct), default=0)

    concept_failures: dict[str, int] = {}
    for attempt in attempts:
        if attempt.is_correct:
            continue
        evaluation = attempt.evaluation or {}
        concepts = evaluation.get("missing_concepts") or []
        if attempt.concept:
            concepts = list({*concepts, attempt.concept})
        for concept in concepts:
            concept_failures[concept] = concept_failures.get(concept, 0) + 1

    weak_concepts = sorted(concept_failures, key=lambda c: concept_failures[c], reverse=True)
    gap_skills: list[str] = []
    for concept in weak_concepts:
        resolved = graph.resolve_skill_from_concept(concept)
        if resolved and resolved not in gap_skills:
            gap_skills.append(resolved)

    if accuracy >= 85 and hardest_passed >= 6:
        verified_level = "advanced"
    elif accuracy >= 60:
        verified_level = "intermediate"
    elif accuracy >= 35:
        verified_level = "beginner"
    else:
        verified_level = "needs_improvement"

    result = {
        "skill_id": session.skill_id,
        "skill_name": graph.name_of(session.skill_id),
        "claimed_level": session.claimed_level,
        "verified_level": verified_level,
        "accuracy": accuracy,
        "questions_answered": total,
        "correct_count": correct,
        "hardest_difficulty_passed": hardest_passed,
        "first_failed_difficulty": hardest_failed,
        "weak_concepts": weak_concepts,
        "gap_skills": [
            {"skill_id": sid, "skill_name": graph.name_of(sid)} for sid in gap_skills
        ],
        "claim_matches_reality": (session.claimed_level or "").lower() == verified_level,
        "timeline": [
            {
                "question_id": a.question_id,
                "difficulty": a.difficulty,
                "concept": a.concept,
                "is_correct": a.is_correct,
                "feedback": (a.evaluation or {}).get("feedback"),
            }
            for a in attempts
        ],
    }
    session.result = result
    session.status = "completed"
    db.flush()
    return result


def item_by_id(question_id: str) -> Optional[dict[str, Any]]:
    return ITEM_INDEX.get(question_id)
