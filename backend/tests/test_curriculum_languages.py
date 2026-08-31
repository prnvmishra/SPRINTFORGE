"""Locks the multi-language curriculum foundation.

Two things are asserted here that the judge contract cannot see on its own:

1. every curriculum problem is expanded into every supported language, with
   unique ids and a generated starter that plumbs I/O only; and
2. for the two languages added most recently (Java and C), a known-correct
   solution really does pass the judge while the starter really does fail it.

(2) is executed, not asserted structurally: a Java module that compiles but
cannot read its own input, or a starter that accidentally answers the samples,
would otherwise ship unnoticed. The exhaustive version of this check, over the
hidden scale cases and all five languages, is ``scripts/verify_languages.py``.
"""

from __future__ import annotations

import asyncio
import shutil

import pytest

from app.data.curriculum import CP_PROBLEMS as ALL_CP_PROBLEMS
from app.data.curriculum import CURRICULUM_MODULES, LANGUAGE_LABELS
from app.data.curriculum_cp import CP_PROBLEMS
from app.data.curriculum_starters import LANGUAGES, build_starters, languages_for
from app.data.practice_modules import PRACTICE_MODULE_INDEX
from app.schemas.execution import TestCase as JudgeCase
from app.services.code_execution_service import (
    LANGUAGE_SPECS,
    LocalSubprocessProvider,
    _java_bin_dir,
)
from scripts.language_solutions import SOLUTIONS

NEW_LANGUAGES = ("java", "c")


def test_every_supported_language_is_labelled():
    assert set(LANGUAGES) == set(LANGUAGE_LABELS)
    assert {"java", "c"} <= set(LANGUAGES)
    for language in LANGUAGES:
        assert language in LANGUAGE_SPECS, f"{language} has no executor spec"


def test_every_problem_is_expanded_into_its_languages():
    """Algorithmic problems reach all five languages; language-specific ones do not.

    A problem may declare a ``languages`` list, which is how a pointer-arithmetic
    exercise stays out of Python instead of being restated as something it is
    not. Everything else must still reach every language, so a forgotten
    restriction cannot quietly shrink the catalogue.
    """
    by_language: dict[str, set[str]] = {language: set() for language in LANGUAGES}
    for module in CURRICULUM_MODULES:
        by_language[module["language"]].add(module["id"])

    expected: dict[str, set[str]] = {language: set() for language in LANGUAGES}
    for problem in ALL_CP_PROBLEMS:
        for language in languages_for(problem):
            expected[language].add(f"cp-{problem['slug']}-{language}")

    assert by_language == expected
    assert len(CURRICULUM_MODULES) == sum(len(ids) for ids in expected.values())

    # Every unrestricted problem is still five modules wide.
    for problem in ALL_CP_PROBLEMS:
        if problem.get("languages"):
            continue
        assert languages_for(problem) == LANGUAGES


def test_module_ids_are_unique_and_in_the_catalogue():
    ids = [module["id"] for module in CURRICULUM_MODULES]
    assert len(ids) == len(set(ids))
    for module_id in ids:
        assert module_id in PRACTICE_MODULE_INDEX


@pytest.mark.parametrize("problem", CP_PROBLEMS, ids=lambda p: p["slug"])
def test_generated_starters_plumb_io_without_solving(problem):
    starters = build_starters(problem)
    assert set(starters) == set(LANGUAGES)
    for language, starter in starters.items():
        assert "TODO" in starter, f"{language} starter has no TODO marker"
        assert problem["reference"] not in starter
        assert "return 0" in starter, f"{language} starter must stub its answer"

    # Language-specific scaffolding the executor requires to run the file at all.
    assert "public class Main" in starters["java"]
    assert "int main(void)" in starters["c"]
    assert "int main()" in starters["cpp"]
    assert "sys.stdin" in starters["python"]
    assert "readFileSync" in starters["javascript"]

    # Where the problem declares a 64-bit quantity, the fixed-width languages
    # must hand the learner a 64-bit type: overflow there is silent, not a crash.
    io = problem["io"]
    wants_64_bit = io["returns"] == "long" or any(
        read["type"] == "long" for read in io["reads"]
    )
    if wants_64_bit:
        assert "long long" in starters["c"]
        assert "long long" in starters["cpp"]
        assert "long " in starters["java"]

    # Scanner cannot read n = 200000 inside the time limit.
    assert "new Scanner" not in starters["java"]
    assert "FastReader" in starters["java"]


def test_no_problem_asks_stdin_for_a_count_it_could_compute():
    """A derivable count on stdin silently shifts a correct solution's input.

    The owner submitted a working spiral-matrix solution that read ``r`` and
    ``c`` and then the grid, and was failed: the format also carried
    ``k = r * c``, which his code consumed as the first cell. Any problem that
    states both dimensions of a matrix must therefore *derive* the element
    count rather than read it, and its cases must carry only the two
    dimensions on line 1.

    A count is only redundant when it is derivable. A bare list needs its
    length, an edge count is not implied by a vertex count, and a second list's
    length is not implied by the first's — those stay on stdin.
    """
    for problem in ALL_CP_PROBLEMS:
        io = problem["io"]
        if io["mode"] != "tokens":
            continue
        names = [read["name"] for read in io["reads"]]
        if not {"r", "c"} <= set(names):
            continue

        by_name = {read["name"]: read for read in io["reads"]}
        counts = {read["count"] for read in io["reads"] if read.get("count")}
        for count in counts:
            read = by_name.get(count)
            if read is None:
                continue
            assert read.get("value"), (
                f"{problem['slug']} reads {count!r} from stdin, but a matrix problem "
                "stating r and c can compute its element count; declare it as a "
                'derived read ({"value": "r * c"}) instead'
            )

        for case in problem["inputs"]:
            first_line = case["stdin"].split("\n", 1)[0].split()
            assert len(first_line) == 2, (
                f"{problem['slug']} case {case['name']!r} puts {len(first_line)} tokens "
                f"on line 1 ({first_line}); a matrix problem states r and c only"
            )


def test_derived_reads_cannot_refer_forward():
    """Generating code that uses a variable before it is set is a silent bug in C."""
    problem = {
        "slug": "made-up",
        "io": {
            "mode": "tokens",
            "function": "f",
            "todo": "t",
            "reads": [
                {"name": "k", "type": "int", "value": "r * c"},
                {"name": "r", "type": "int"},
                {"name": "c", "type": "int"},
            ],
            "args": ["k"],
            "returns": "int",
        },
    }
    with pytest.raises(ValueError, match="not read before it"):
        build_starters(problem)


@pytest.mark.parametrize(
    "slug", ["b75-spiral-matrix", "b75-rotate-image", "b75-set-matrix-zeroes"]
)
def test_sequence_answer_starters_do_not_promise_a_scalar(slug):
    """A problem whose answer is printed must not be handed an ``int`` signature."""
    problem = next(p for p in ALL_CP_PROBLEMS if p["slug"] == slug)
    assert problem["io"]["returns"] == "void"

    starters = build_starters(problem)
    function = problem["io"]["function"]
    camel = function.split("_")[0] + "".join(
        part.capitalize() for part in function.split("_")[1:]
    )
    assert f"void {camel}(" in starters["cpp"]
    assert f"static void {camel}(" in starters["java"]
    assert f"void {function}(" in starters["c"]
    # main must not print the call's value: there is no value.
    assert f"std::cout << {camel}(" not in starters["cpp"]
    assert f"println({camel}(" not in starters["java"]
    assert f"print({function}(" not in starters["python"]
    assert f"console.log({camel}(" not in starters["javascript"]


def _toolchain_available(language: str) -> bool:
    if language == "java":
        return _java_bin_dir() is not None
    spec = LANGUAGE_SPECS[language]
    compile_cmd = spec.get("compile")
    if compile_cmd and shutil.which(list(compile_cmd)[0]) is None:  # type: ignore[arg-type]
        return False
    return True


def _visible_cases(module: dict) -> list[TestCase]:
    return [
        JudgeCase(
            name=case["name"],
            stdin=case["stdin"],
            expected_stdout=case["expected_stdout"],
            hidden=case["hidden"],
            match=case.get("match", "trimmed"),
        )
        for case in module["test_cases"]
        if not case["hidden"]
    ]


@pytest.mark.parametrize("language", NEW_LANGUAGES)
@pytest.mark.parametrize("problem", CP_PROBLEMS, ids=lambda p: p["slug"])
def test_correct_solution_passes_and_starter_fails(problem, language):
    if not _toolchain_available(language):
        pytest.skip(f"no working {language} toolchain on this host")

    slug = problem["slug"]
    module = PRACTICE_MODULE_INDEX[f"cp-{slug}-{language}"]
    cases = _visible_cases(module)
    assert cases, "expected at least one visible case"

    provider = LocalSubprocessProvider()
    solution = SOLUTIONS[slug][language]
    result = asyncio.run(provider.run(language, solution, cases))
    assert not result.compile_error, result.compile_error
    failed = [(r.name, r.stderr) for r in result.results if not r.passed]
    assert not failed, f"correct {language} solution for {slug} failed: {failed}"

    starter_result = asyncio.run(provider.run(language, module["files"]["solution"], cases))
    assert not starter_result.compile_error, (
        f"{language} starter for {slug} does not compile: {starter_result.compile_error}"
    )
    assert not all(r.passed for r in starter_result.results), (
        f"{language} starter for {slug} passes the visible cases — it solves the problem"
    )
