"""Serves guided roadmaps, annotated with what the learner has already proved.

The annotation is the whole point. A roadmap on its own is a reading list any
site could print. Cross-referenced against the learner's verified confidence it
becomes "you have already proved four of these five prerequisites, so start at
step two" — which is the same promise the graded path makes, held to the same
standard of evidence.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.data.roadmaps import ROADMAP_INDEX, ROADMAPS, SKILL_ALIASES, normalise
from app.services.knowledge_graph import get_knowledge_graph
from app.services import path_service
from app.models import LearningDigitalTwin


def _confidence_map(
    db: Session, twin: Optional[LearningDigitalTwin]
) -> dict[str, float]:
    """Graded against the same numbers as every other screen, via path_service.

    Anonymous callers have no twin, and get an empty map rather than zeros — a
    missing measurement is not a measured zero.
    """
    if twin is None:
        return {}
    return path_service.learner_confidence(db, twin)


def _prerequisites(
    roadmap: dict[str, Any],
    graph: Any,
    confidence: dict[str, float],
    threshold: float,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for skill_id in roadmap.get("prerequisites", []):
        score = confidence.get(skill_id)
        out.append(
            {
                "skill_id": skill_id,
                "skill_name": graph.name_of(skill_id),
                # None means "we have never measured this", which is different
                # from a measured zero and is shown differently.
                "confidence": score,
                "verified": score is not None and score >= threshold,
                "graded_here": graph.get(skill_id) is not None,
            }
        )
    return out


def _summary(roadmap: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": roadmap["id"],
        "label": roadmap["label"],
        "summary": roadmap["summary"],
        "step_count": len(roadmap["steps"]),
        "prerequisite_ids": list(roadmap.get("prerequisites", [])),
    }


def catalogue() -> list[dict[str, Any]]:
    return [_summary(roadmap) for roadmap in ROADMAPS]


def detail(
    db: Session, twin: Optional[LearningDigitalTwin], roadmap_id: str
) -> Optional[dict[str, Any]]:
    roadmap = ROADMAP_INDEX.get(roadmap_id)
    if roadmap is None:
        return None

    graph = get_knowledge_graph()
    threshold = float(graph.confidence_threshold)
    confidence = _confidence_map(db, twin)
    prerequisites = _prerequisites(roadmap, graph, confidence, threshold)

    unmet = [p for p in prerequisites if p["graded_here"] and not p["verified"]]

    return {
        "id": roadmap["id"],
        "label": roadmap["label"],
        "summary": roadmap["summary"],
        "why": roadmap["why"],
        "course": roadmap.get("course"),
        "steps": roadmap["steps"],
        "prerequisites": prerequisites,
        "unmet_prerequisites": unmet,
        # Said plainly here so no caller has to infer it from the absence of a
        # confidence field.
        "graded": False,
        "disclaimer": (
            "This is a guided roadmap, not a verified skill. SprintForge does not "
            "run checks against this subject yet, so finishing it will not change "
            "your confidence scores."
        ),
    }


def resolve(db: Session, twin: Optional[LearningDigitalTwin], query: str) -> dict[str, Any]:
    """Answer "can you teach me X?" with one of three honest outcomes.

    Graded skills and roadmaps are matched in one pass and the longest alias
    wins, rather than checking skills first and roadmaps second. Priority by
    category would answer "I want to learn React Native" with React, because
    React is graded and matches earlier — the more specific request has to win
    regardless of which side of the line it falls on.
    """
    graph = get_knowledge_graph()
    text = normalise(query)

    # (alias length, kind, target)
    best: tuple[int, str, Any] | None = None

    def offer(alias: str, kind: str, target: Any, weight: int | None = None) -> None:
        nonlocal best
        needle = normalise(alias).strip()
        if not needle:
            return
        score = len(needle) if weight is None else weight
        if f" {needle} " in text and (best is None or score > best[0]):
            best = (score, kind, target)

    # Punctuation-bearing names have to be read before normalisation flattens
    # them: "c++" and "c#" both reduce to "c", which otherwise resolves a
    # request for C++ to the C curriculum.
    # Set directly rather than through `offer`, whose containment test is run
    # against the normalised text where "c++" no longer exists.
    raw = query.lower()
    if "c++" in raw and graph.get("cpp_basics") is not None:
        best = (99, "graded_skill", "cpp_basics")

    for alias, skill_id in SKILL_ALIASES.items():
        if graph.get(skill_id) is not None:
            offer(alias, "graded_skill", skill_id)
    for concept, skill_id in graph.concept_to_skill.items():
        if graph.get(skill_id) is not None:
            offer(concept, "graded_skill", skill_id)
    for skill_id, node in graph.nodes.items():
        offer(skill_id.replace("_", " "), "graded_skill", skill_id)
        offer(node.name, "graded_skill", skill_id)

    for roadmap in ROADMAPS:
        for alias in [roadmap["id"].replace("_", " "), roadmap["label"], *roadmap["aliases"]]:
            offer(alias, "roadmap", roadmap["id"])

    if best is None:
        return {
            "outcome": "unknown",
            "skill_id": None,
            "skill_name": None,
            "roadmap": None,
            "available": catalogue(),
        }

    _, kind, target = best
    if kind == "graded_skill":
        return {
            "outcome": "graded_skill",
            "skill_id": target,
            "skill_name": graph.name_of(target),
            "roadmap": None,
        }

    return {
        "outcome": "roadmap",
        "skill_id": None,
        "skill_name": None,
        "roadmap": detail(db, twin, target),
    }
