"""The curriculum's source of truth. Build-time only — never import at runtime.

Importing this module is expensive, and unavoidably so. The problem sets it
pulls in do not merely *declare* their scale cases, they **generate** them: the
tree, grid and word problems build multi-megabyte stdin strings from a seeded
RNG at import so that every language's judge sees byte-identical input. That
costs about ten seconds and a few hundred megabytes every time, which is fine
for a build step run once and fatal for an API cold start.

The API therefore never imports this. ``scripts/build_curriculum_manifest.py``
imports it once, writes the finished module dicts to
``app/data/cases/modules.json``, and :mod:`app.data.curriculum` reads that
manifest instead. Reference and wrong solutions stay here and are never carried
into the manifest, so there remains no path by which a solution reaches a
client.

Import this only from ``scripts/``: build, verification and authoring tools.

Adding a problem: see ``backend/docs/curriculum_authoring.md``.
"""

from __future__ import annotations

from typing import Any

from app.data.curriculum_basics_c import PROBLEMS as _BASICS_C
from app.data.curriculum_basics_cpp import PROBLEMS as _BASICS_CPP
from app.data.curriculum_basics_java import PROBLEMS as _BASICS_JAVA
from app.data.curriculum_basics_python import PROBLEMS as _BASICS_PYTHON
from app.data.curriculum_blind75_1 import PROBLEMS as _BLIND75_1
from app.data.curriculum_blind75_2 import PROBLEMS as _BLIND75_2
from app.data.curriculum_blind75_3 import PROBLEMS as _BLIND75_3
from app.data.curriculum_blind75_4 import PROBLEMS as _BLIND75_4
from app.data.curriculum_cp import CP_PROBLEMS as _CP_PROBLEMS
from app.data.curriculum_starters import build_starters

CP_PROBLEMS: list[dict[str, Any]] = [
    # Language fundamentals come first: syntax, types, control flow, strings,
    # arrays, then pointers/classes as the language demands. A learner should
    # not meet Blind 75 before they can write a loop in the language they are
    # being judged in.
    *_BASICS_C,
    *_BASICS_CPP,
    *_BASICS_JAVA,
    *_BASICS_PYTHON,
    *_CP_PROBLEMS,
    *_BLIND75_1,
    *_BLIND75_2,
    *_BLIND75_3,
    *_BLIND75_4,
]

_slugs = [problem["slug"] for problem in CP_PROBLEMS]
if len(set(_slugs)) != len(_slugs):
    raise RuntimeError("duplicate curriculum problem slug detected")

# Starters are generated from each problem's declarative ``io`` spec rather
# than hand-written, so adding a problem costs one spec instead of five files.
# See :mod:`app.data.curriculum_starters` and
# ``backend/docs/curriculum_authoring.md``.
STARTERS: dict[str, dict[str, str]] = {
    problem["slug"]: build_starters(problem) for problem in CP_PROBLEMS
}


def build_cp_modules() -> list[dict[str, Any]]:
    """One practice module per (problem, language), carrying its visible cases.

    Hidden cases are referenced by slug rather than embedded: they hold the
    scale inputs, and materialising all of them cost 580MB for data that only
    the grader reads. :func:`app.data.curriculum.graded_cases` fetches them when
    a submission is judged.
    """
    from app.data.curriculum import LANGUAGE_LABELS, _load_visible_cases

    generated = _load_visible_cases()
    modules: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for problem in CP_PROBLEMS:
        slug = problem["slug"]
        entry = generated.get(slug)
        if not entry:
            raise RuntimeError(
                f"No generated cases for '{slug}'. Run: "
                "python -m scripts.build_test_cases && python -m scripts.split_case_bank"
            )
        starters = STARTERS.get(slug, {})
        if not starters:
            raise RuntimeError(f"No starter code registered for '{slug}'")

        for language, starter in starters.items():
            module_id = f"cp-{slug}-{language}"
            if module_id in seen_ids:
                raise RuntimeError(f"Duplicate curriculum module id '{module_id}'")
            seen_ids.add(module_id)
            modules.append(
                {
                    "id": module_id,
                    "track": "competitive",
                    "kind": "challenge",
                    "language": language,
                    "technology": LANGUAGE_LABELS[language],
                    "skill_id": problem["skill_id"],
                    "title": f"{problem['title']} ({LANGUAGE_LABELS[language]})",
                    "difficulty": problem["difficulty"],
                    "estimated_minutes": problem["estimated_minutes"],
                    "summary": problem["statement"],
                    "problem_statement": problem["statement"],
                    "constraints": problem["constraints"],
                    "input_format": problem["input_format"],
                    "output_format": problem["output_format"],
                    "examples": problem["examples"],
                    "requirements": problem["criteria"],
                    "editable_files": ["solution"],
                    "files": {"solution": starter},
                    # Visible only, and shared across the languages of a slug:
                    # they see the same cases and nothing mutates them.
                    "test_cases": entry["visible"],
                    "cases_slug": slug,
                    "hidden_test_count": entry["hidden_count"],
                    "checks": [],
                }
            )
    return modules
