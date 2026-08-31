"""Builds practice modules from the curriculum problem sets.

The competitive-programming problems in :mod:`app.data.curriculum_cp` are pure
data plus a reference solution. This module joins them with the verified test
cases produced by ``scripts/build_test_cases.py`` and emits dicts in the shape
the practice service already understands, one per (problem, language) pair.

A problem is expanded across all five supported languages (Python, JavaScript,
Java, C++, C) unless it declares its own ``languages`` list, which is how the
language-fundamentals problems keep a pointer-arithmetic exercise out of Python.
Starter code is generated from the problem's ``io`` spec by
:mod:`app.data.curriculum_starters`.

Reference solutions are deliberately *not* carried into the emitted modules, so
there is no path by which a solution could be served to a client.

Adding a problem: see ``backend/docs/curriculum_authoring.md``.
"""

from __future__ import annotations

import json
import pathlib
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
from app.data.curriculum_starters import build_starters

GENERATED_CASES_PATH = pathlib.Path(__file__).parent / "generated_cases.json"

# User-facing tracks. These are the lanes a learner picks between; each maps
# onto skills that already exist in the knowledge graph.
TRACKS: dict[str, dict[str, Any]] = {
    "competitive": {
        "id": "competitive",
        "label": "Competitive Programming",
        "blurb": "Algorithmic problems judged on correctness and complexity, stdin to stdout.",
        "skills": ["dsa_arrays", "python_basics"],
    },
    "backend": {
        "id": "backend",
        "label": "Backend Engineering",
        "blurb": "The logic behind APIs: pagination, rate limiting, routing, caching.",
        "skills": ["node_basics", "rest_api", "database_modeling"],
    },
    "mern": {
        "id": "mern",
        "label": "MERN Developer",
        "blurb": "State, data shaping and async patterns across a React and Node stack.",
        "skills": ["react_state", "react_data_fetching", "api_integration", "js_async"],
    },
    "webdev": {
        "id": "webdev",
        "label": "Web Development",
        "blurb": "The browser fundamentals: the DOM, events, layout and semantics.",
        "skills": ["js_dom", "js_functions", "css_layout", "html_semantics"],
    },
}


def _load_generated_cases() -> dict[str, Any]:
    if not GENERATED_CASES_PATH.exists():
        raise RuntimeError(
            "generated_cases.json is missing. Run: python -m scripts.build_test_cases"
        )
    return json.loads(GENERATED_CASES_PATH.read_text())


# --------------------------------------------------------------------------- #
#  Language starters                                                          #
# --------------------------------------------------------------------------- #
# Starters are generated from each problem's declarative ``io`` spec rather
# than hand-written, so adding a problem costs one spec instead of five files.
# See :mod:`app.data.curriculum_starters` and
# ``backend/docs/curriculum_authoring.md``.

LANGUAGE_LABELS = {
    "python": "Python",
    "javascript": "JavaScript",
    "java": "Java",
    "cpp": "C++",
    "c": "C",
}

STARTERS: dict[str, dict[str, str]] = {
    problem["slug"]: build_starters(problem) for problem in CP_PROBLEMS
}


def build_cp_modules() -> list[dict[str, Any]]:
    """One practice module per (problem, language), carrying verified cases."""
    generated = _load_generated_cases()
    modules: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for problem in CP_PROBLEMS:
        slug = problem["slug"]
        entry = generated.get(slug)
        if not entry:
            raise RuntimeError(
                f"No generated cases for '{slug}'. Run: python -m scripts.build_test_cases"
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
                    "test_cases": entry["cases"],
                    "checks": [],
                }
            )
    return modules


CURRICULUM_MODULES: list[dict[str, Any]] = build_cp_modules()
