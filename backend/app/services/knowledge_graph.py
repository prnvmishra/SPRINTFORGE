"""JSON-backed knowledge dependency graph and prerequisite routing engine."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Optional

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "skills_graph.json"


@dataclass
class SkillNode:
    id: str
    name: str
    track: str
    difficulty_weight: int
    prerequisites: list[str] = field(default_factory=list)
    unlocks: list[str] = field(default_factory=list)
    related_concepts: list[str] = field(default_factory=list)
    recommended_practice: list[str] = field(default_factory=list)


class KnowledgeGraph:
    def __init__(self, raw: dict[str, Any]) -> None:
        self.raw = raw
        self.confidence_threshold: float = float(raw.get("confidence_threshold", 65))
        self.nodes: dict[str, SkillNode] = {}
        for item in raw.get("skills", []):
            node = SkillNode(
                id=item["id"],
                name=item["name"],
                track=item.get("track", "general"),
                difficulty_weight=int(item.get("difficulty_weight", 3)),
                prerequisites=list(item.get("prerequisites", [])),
                unlocks=list(item.get("unlocks", [])),
                related_concepts=list(item.get("related_concepts", [])),
                recommended_practice=list(item.get("recommended_practice", [])),
            )
            self.nodes[node.id] = node
        self.concept_to_skill: dict[str, str] = {
            k.lower(): v for k, v in raw.get("concept_to_skill", {}).items()
        }

    # ---------------- basic access ----------------

    def get(self, skill_id: str) -> Optional[SkillNode]:
        return self.nodes.get(skill_id)

    def name_of(self, skill_id: str) -> str:
        node = self.get(skill_id)
        return node.name if node else skill_id.replace("_", " ").title()

    def all_nodes(self) -> list[SkillNode]:
        return list(self.nodes.values())

    def resolve_skill_from_concept(self, concept: str) -> Optional[str]:
        if not concept:
            return None
        key = concept.strip().lower()
        if key in self.concept_to_skill:
            return self.concept_to_skill[key]
        for concept_key, skill_id in self.concept_to_skill.items():
            if concept_key in key or key in concept_key:
                return skill_id
        for node in self.nodes.values():
            if node.name.lower() == key or node.id == key:
                return node.id
            for related in node.related_concepts:
                if related.lower() in key:
                    return node.id
        return None

    # ---------------- traversal ----------------

    def ancestors(self, skill_id: str) -> list[str]:
        """All transitive prerequisites, ordered from most foundational upward."""
        order: list[str] = []
        seen: set[str] = set()

        def walk(sid: str) -> None:
            node = self.get(sid)
            if not node:
                return
            for prereq in node.prerequisites:
                if prereq in seen:
                    continue
                seen.add(prereq)
                walk(prereq)
                order.append(prereq)

        walk(skill_id)
        return order

    def learning_path(self, target_skill_id: str) -> list[str]:
        path = self.ancestors(target_skill_id)
        if self.get(target_skill_id):
            path.append(target_skill_id)
        return path

    def missing_prerequisites(
        self,
        skill_id: str,
        confidences: dict[str, float],
        evidence: Optional[set[str]] = None,
        demonstrated: Optional[set[str]] = None,
        threshold: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Prerequisites (transitive) that are *known* to be below the mastery threshold.

        Two relaxations keep the gate honest without making it a dead end:

        - A prerequisite only blocks when the Digital Twin holds evidence about it.
          No evidence means unknown, not weak: the learner may attempt the work,
          and the attempt itself becomes the evidence.
        - A prerequisite is also satisfied when it was *demonstrated* — a graded
          submission passed at or above that skill's own difficulty. Proving it by
          doing counts, even if the aggregate confidence score is still climbing.

        Passing evidence=None disables the first relaxation.
        """
        limit = self.confidence_threshold if threshold is None else threshold
        gaps: list[dict[str, Any]] = []
        for prereq in self.ancestors(skill_id):
            if evidence is not None and prereq not in evidence:
                continue
            if demonstrated is not None and prereq in demonstrated:
                continue
            confidence = float(confidences.get(prereq, 0.0))
            if confidence < limit:
                gaps.append(
                    {
                        "skill_id": prereq,
                        "skill_name": self.name_of(prereq),
                        "confidence": round(confidence, 1),
                        "required": limit,
                        "difficulty_weight": self.get(prereq).difficulty_weight if self.get(prereq) else 3,
                        "recommended_practice": self.get(prereq).recommended_practice if self.get(prereq) else [],
                    }
                )
        return gaps

    def is_unlocked(
        self,
        skill_id: str,
        confidences: dict[str, float],
        evidence: Optional[set[str]] = None,
        demonstrated: Optional[set[str]] = None,
        threshold: Optional[float] = None,
    ) -> tuple[bool, list[dict[str, Any]]]:
        gaps = self.missing_prerequisites(skill_id, confidences, evidence, demonstrated, threshold)
        return (len(gaps) == 0, gaps)

    def unverified_prerequisites(self, skill_id: str, evidence: set[str]) -> list[str]:
        """Prerequisites the twin knows nothing about yet."""
        return [p for p in self.ancestors(skill_id) if p not in evidence]

    def skills_for_stack(self, tech_stack: Iterable[str]) -> list[str]:
        """Map a free-form tech stack to graph skill ids, ordered by dependency depth."""
        aliases = {
            "html": ["html_basics", "html_semantics"],
            "css": ["css_basics", "css_layout", "css_responsive"],
            "tailwind": ["css_basics", "css_layout", "css_responsive"],
            "javascript": ["js_basics", "js_functions", "js_dom", "js_async"],
            "js": ["js_basics", "js_functions", "js_dom", "js_async"],
            "typescript": ["js_basics", "js_functions", "typescript_basics", "js_async"],
            "ts": ["js_basics", "js_functions", "typescript_basics", "js_async"],
            "react": ["react_fundamentals", "react_state", "react_data_fetching"],
            "next.js": ["react_fundamentals", "react_state", "react_data_fetching"],
            "nextjs": ["react_fundamentals", "react_state", "react_data_fetching"],
            "node": ["node_basics", "rest_api"],
            "node.js": ["node_basics", "rest_api"],
            "express": ["node_basics", "rest_api"],
            "api": ["api_integration"],
            "rest": ["rest_api"],
            "database": ["database_modeling"],
            "postgres": ["database_modeling"],
            "postgresql": ["database_modeling"],
            "mongodb": ["database_modeling"],
            # "sql" used to resolve to `database_modeling` — schema *design* —
            # which meant a Data Analyst project asking for SQL generated a Node
            # server and a REST API, because database_modeling's prerequisite
            # chain is rest_api -> node_basics -> js_async. Analytical SQL is its
            # own skill line now; schema design is still reachable through
            # "database"/"postgres"/"mysql" above.
            "sql": ["sql_basics", "sql_joins", "sql_aggregation", "sql_analytics"],
            "sqlite": ["sql_basics", "sql_joins", "sql_aggregation"],
            "bigquery": ["sql_basics", "sql_joins", "sql_aggregation", "sql_analytics"],
            "spreadsheet": ["spreadsheet_modeling"],
            "spreadsheets": ["spreadsheet_modeling"],
            "excel": ["spreadsheet_modeling"],
            "google sheets": ["spreadsheet_modeling"],
            "sheets": ["spreadsheet_modeling"],
            "pandas": ["data_cleaning", "exploratory_analysis"],
            "data cleaning": ["data_cleaning"],
            "eda": ["exploratory_analysis"],
            "data analysis": ["exploratory_analysis"],
            "statistics": ["statistics_business"],
            "stats": ["statistics_business"],
            "a/b testing": ["statistics_business"],
            "charts": ["data_visualization"],
            "visualisation": ["data_visualization"],
            "visualization": ["data_visualization"],
            "dashboard": ["dashboard_design"],
            "dashboards": ["dashboard_design"],
            "tableau": ["data_visualization", "dashboard_design"],
            "power bi": ["data_visualization", "dashboard_design"],
            "looker": ["data_visualization", "dashboard_design"],
            "bi": ["dashboard_design"],
            "python": ["python_basics"],
            "java": ["java_basics"],
            "c": ["c_basics"],
            "c++": ["cpp_basics"],
            "cpp": ["cpp_basics"],
        }
        collected: list[str] = []
        for tech in tech_stack:
            key = str(tech).strip().lower()
            for skill_id in aliases.get(key, []):
                if skill_id not in collected:
                    collected.append(skill_id)
        if not collected:
            collected = ["html_basics", "css_basics", "js_basics"]

        expanded: list[str] = []
        for skill_id in collected:
            for path_skill in self.learning_path(skill_id):
                if path_skill not in expanded:
                    expanded.append(path_skill)
        expanded.sort(key=lambda sid: (self.get(sid).difficulty_weight if self.get(sid) else 3))
        return expanded


@lru_cache
def get_knowledge_graph() -> KnowledgeGraph:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return KnowledgeGraph(json.load(handle))
