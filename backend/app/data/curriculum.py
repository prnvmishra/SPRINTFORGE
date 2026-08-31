"""Serves the curriculum's practice modules to the API, cheaply.

One problem becomes one module per supported language (Python, JavaScript,
Java, C++, C), unless it declares its own ``languages`` list — which is how the
language-fundamentals problems keep a pointer-arithmetic exercise out of Python.

Those modules are *built* by :mod:`app.data.curriculum_source`, which is far too
expensive to import at runtime: the problem sets generate their multi-megabyte
scale inputs from a seeded RNG at import, costing about ten seconds and a few
hundred megabytes. So the build is done once by
``scripts/build_curriculum_manifest.py``, and this module reads the finished
manifest. Hidden cases stay out of the manifest too, behind
:func:`load_hidden_cases`, because they carry that same weight and only the
grader ever reads them.

Reference solutions are deliberately *not* carried into the emitted modules, so
there is no path by which a solution could be served to a client.

The build-time names (``CP_PROBLEMS``, ``STARTERS``, ``build_cp_modules``) are
still importable from here for the scripts that want them, and pull in the
expensive module only at that point.

Adding a problem: see ``backend/docs/curriculum_authoring.md``.
"""

from __future__ import annotations

import gzip
import json
import pathlib
from functools import lru_cache
from typing import Any

#: The authoring artifact: the whole bank in one file, written by
#: ``scripts/build_test_cases.py`` and merged into by the verify scripts. It is
#: deliberately *not* read at import — see :data:`CASES_VISIBLE_PATH`.
GENERATED_CASES_PATH = pathlib.Path(__file__).parent / "generated_cases.json"

#: The runtime store, derived from the bank by ``scripts/split_case_bank.py``.
#: Visible cases are small enough to hold for every slug at once; hidden ones
#: carry the multi-megabyte scale inputs and are loaded per slug on demand.
CASES_DIR = pathlib.Path(__file__).parent / "cases"
CASES_VISIBLE_PATH = CASES_DIR / "visible.json"
CASES_HIDDEN_DIR = CASES_DIR / "hidden"

#: Hidden cases are stored gzipped: they are mostly generated digits and text,
#: which halves to 80MB, and that is the artifact a deployment has to carry.
#: The cost is a few milliseconds per slug on first grade, paid once thanks to
#: the cache on :func:`load_hidden_cases`.
HIDDEN_SUFFIX = ".json.gz"

#: The finished practice modules, written by
#: ``scripts/build_curriculum_manifest.py``. This is what the API reads.
CURRICULUM_MANIFEST_PATH = CASES_DIR / "modules.json"

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
    """The whole bank. For build and verify scripts only, never at import.

    Streamed from the open file rather than via ``read_text`` so the decoded
    text and the parsed structure are not both alive at the peak.
    """
    if not GENERATED_CASES_PATH.exists():
        raise RuntimeError(
            "generated_cases.json is missing. Run: python -m scripts.build_test_cases"
        )
    with GENERATED_CASES_PATH.open("rb") as handle:
        return json.load(handle)


def _load_visible_cases() -> dict[str, Any]:
    if not CASES_VISIBLE_PATH.exists():
        raise RuntimeError(
            "The runtime case store is missing. Run: "
            "python -m scripts.build_test_cases && python -m scripts.split_case_bank"
        )
    with CASES_VISIBLE_PATH.open("rb") as handle:
        return json.load(handle)


@lru_cache(maxsize=4)
def load_hidden_cases(slug: str) -> tuple[dict[str, Any], ...]:
    """This slug's hidden cases, read on first use and cached.

    The cache is deliberately small: a single slug's hidden cases can run to
    tens of megabytes, so holding every slug ever graded would reintroduce the
    footprint this split exists to remove. Four is enough for a learner
    iterating on one problem, and bounds the worst case.

    A tuple because :func:`lru_cache` hands the same object to every caller and
    a shared mutable list would let one request corrupt the next one's cases.
    """
    path = CASES_HIDDEN_DIR / f"{slug}{HIDDEN_SUFFIX}"
    if not path.exists():
        raise RuntimeError(
            f"No hidden cases file for '{slug}'. Run: python -m scripts.split_case_bank"
        )
    with gzip.open(path, "rb") as handle:
        return tuple(json.load(handle))


def graded_cases(module: dict[str, Any]) -> list[dict[str, Any]]:
    """Every case a Submit is judged against, visible and hidden.

    Curriculum modules carry only their visible cases in memory and name their
    slug, so the hidden ones are fetched here. Hand-authored modules embed all
    of their cases directly and have no slug, and pass through unchanged.
    """
    cases = list(module.get("test_cases", []))
    slug = module.get("cases_slug")
    if slug:
        cases.extend(dict(case) for case in load_hidden_cases(slug))
    return cases


def hidden_case_count(module: dict[str, Any]) -> int:
    """How many hidden cases grade this module, without loading them."""
    embedded = sum(1 for case in module.get("test_cases", []) if case.get("hidden"))
    return embedded + module.get("hidden_test_count", 0)


LANGUAGE_LABELS = {
    "python": "Python",
    "javascript": "JavaScript",
    "java": "Java",
    "cpp": "C++",
    "c": "C",
}

@lru_cache(maxsize=1)
def _load_curriculum_modules() -> tuple[dict[str, Any], ...]:
    if not CURRICULUM_MANIFEST_PATH.exists():
        raise RuntimeError(
            "The curriculum manifest is missing. Run: "
            "python -m scripts.build_curriculum_manifest"
        )
    with CURRICULUM_MANIFEST_PATH.open("rb") as handle:
        return tuple(json.load(handle))


#: Names resolved on first access rather than at import.
#:
#: ``CURRICULUM_MODULES`` is deferred so that importing this module does not
#: require the manifest to exist yet — ``scripts/build_curriculum_manifest.py``
#: has to import its way here in order to *write* that file.
#:
#: The rest live in :mod:`app.data.curriculum_source`, which costs about ten
#: seconds to import. Keeping them reachable from here means the build and
#: verify scripts can go on importing them from their usual home, while the API,
#: which touches none of them, never pays for it.
_DEFERRED = {
    "CURRICULUM_MODULES": lambda: list(_load_curriculum_modules()),
    "CP_PROBLEMS": None,
    "STARTERS": None,
    "build_cp_modules": None,
}


def __getattr__(name: str) -> Any:
    if name not in _DEFERRED:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    loader = _DEFERRED[name]
    if loader is not None:
        return loader()
    from app.data import curriculum_source

    return getattr(curriculum_source, name)
