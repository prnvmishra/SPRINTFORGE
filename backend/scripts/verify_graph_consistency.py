"""Assert the knowledge graph's `unlocks` and `prerequisites` agree.

`prerequisites` is load-bearing: `ancestors()` walks it and it drives every lock
decision. `unlocks` is display-only and is what a Skill Route visualisation
draws. If the two disagree, the picture contradicts the locking the learner
actually experiences.

    python scripts/verify_graph_consistency.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.knowledge_graph import get_knowledge_graph


def main() -> int:
    graph = get_knowledge_graph()
    problems: list[str] = []

    for node in graph.all_nodes():
        for target_id in node.unlocks:
            target = graph.get(target_id)
            if target is None:
                problems.append(f"{node.id} unlocks unknown skill {target_id}")
            elif node.id not in target.prerequisites:
                problems.append(
                    f"{node.id} claims to unlock {target_id}, but {target_id}.prerequisites "
                    f"does not contain {node.id} — the drawn edge would not gate anything"
                )
        for prereq_id in node.prerequisites:
            source = graph.get(prereq_id)
            if source is None:
                problems.append(f"{node.id} requires unknown skill {prereq_id}")
            elif node.id not in source.unlocks:
                problems.append(
                    f"{prereq_id} gates {node.id}, but {prereq_id}.unlocks does not list it — "
                    f"the lock would be invisible in the graph view"
                )

    # A prerequisite cycle would make ancestors() unbounded work and no skill in
    # the cycle could ever unlock.
    for node in graph.all_nodes():
        if node.id in graph.ancestors(node.id):
            problems.append(f"{node.id} is its own transitive prerequisite")

    print(f"skills: {len(graph.all_nodes())}")
    print(f"edges (prerequisites): {sum(len(n.prerequisites) for n in graph.all_nodes())}")
    print(f"edges (unlocks): {sum(len(n.unlocks) for n in graph.all_nodes())}")
    if problems:
        for problem in problems:
            print(f"!! {problem}")
        print(f"\n{len(problems)} inconsistency(ies)")
        return 1
    print("\nOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
