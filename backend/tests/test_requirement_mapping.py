"""Proofs that the requirements panel and the grader can never disagree.

The brief's "N/M met" ratio is derived from the requirement pointers the specs
declare (`requirement_index` / `requirement_indexes` / `precondition`). These
tests pin the data (every pointer is in range) and the derivation (the ratio a
client computes from real check outcomes), so the MTB-10 class of bug — all
checks green, "1/4 met" — cannot come back.

`derive_rows` mirrors `matchRequirements` in
frontend/components/workspace/requirement-progress.tsx for the annotated path.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data.practice_modules import PRACTICE_MODULES
from app.data.ticket_templates import API_CLIENT_SOLUTION, TICKET_TEMPLATES
from app.services.validation_service import run_static_checks

API_CLIENT = TICKET_TEMPLATES["api_integration"][0]

# The reference solution, with the generator's placeholders resolved the way a
# real Movie Ticket Booking board resolves them. Every check green.
PASSING_API_CLIENT = API_CLIENT_SOLUTION.replace("{entity_plural}", "movies").replace(
    "{entity}", "movie"
)


def specs_of(entry: dict[str, Any]) -> list[dict[str, Any]]:
    return list(entry.get("checks", [])) + list(
        (entry.get("behaviour") or {}).get("assertions", [])
    )


def annotated_entries() -> list[tuple[str, dict[str, Any]]]:
    entries = [
        (f"{skill}/{template['slug']}", template)
        for skill, templates in TICKET_TEMPLATES.items()
        for template in templates
    ]
    entries += [(module["id"], module) for module in PRACTICE_MODULES]
    return [(name, entry) for name, entry in entries if specs_of(entry)]


def derive_rows(requirements: list[str], checks: list[dict[str, Any]]) -> list[str]:
    """The status the UI shows per requirement, from the declared mapping."""
    grading = [c for c in checks if not c.get("precondition")]
    owners: dict[int, list[dict[str, Any]]] = {}
    for check in grading:
        indexes = check.get("requirement_indexes")
        if indexes is None:
            single = check.get("requirement_index")
            indexes = [single] if isinstance(single, int) else []
        for index in indexes:
            if 0 <= index < len(requirements):
                owners.setdefault(index, []).append(check)

    all_passed = bool(checks) and all(c["passed"] for c in checks)
    rows = []
    for index in range(len(requirements)):
        owned = owners.get(index, [])
        if not owned:
            rows.append("ungraded")
        elif all_passed or all(c["passed"] for c in owned):
            rows.append("passed")
        else:
            rows.append("failed")
    return rows


def ratio(rows: list[str]) -> tuple[int, int]:
    graded = [r for r in rows if r != "ungraded"]
    return sum(1 for r in graded if r == "passed"), len(graded)


def run(source: str, template: dict[str, Any]) -> list[dict[str, Any]]:
    return [o.to_dict() for o in run_static_checks({"script.js": source}, template["checks"])]


# ------------------------------------------------------------------ the data


@pytest.mark.parametrize("name,entry", annotated_entries(), ids=lambda v: v if isinstance(v, str) else "")
def test_declared_requirement_pointers_are_in_range(name: str, entry: dict[str, Any]) -> None:
    requirements = entry.get("requirements", [])
    for spec in specs_of(entry):
        indexes = spec.get("requirement_indexes") or []
        single = spec.get("requirement_index")
        if isinstance(single, int):
            indexes = [*indexes, single]
        for index in indexes:
            assert 0 <= index < len(requirements), (
                f"{name}: check '{spec.get('id')}' points at requirement {index}, "
                f"but the template ships {len(requirements)} requirements"
            )


@pytest.mark.parametrize("name,entry", annotated_entries(), ids=lambda v: v if isinstance(v, str) else "")
def test_every_check_declares_what_it_grades(name: str, entry: dict[str, Any]) -> None:
    for spec in specs_of(entry):
        assert "requirement_index" in spec or "requirement_indexes" in spec, (
            f"{name}: check '{spec.get('id')}' declares no requirement mapping, so the UI "
            "would fall back to guessing from wording"
        )


def test_preconditions_never_claim_a_requirement() -> None:
    for name, entry in annotated_entries():
        for spec in specs_of(entry):
            if spec.get("precondition"):
                assert spec.get("requirement_index") is None, name
                assert not spec.get("requirement_indexes"), name


# ------------------------------------------------------------- the derivation


def test_mtb10_all_checks_green_yields_every_requirement_met() -> None:
    checks = run(PASSING_API_CLIENT, API_CLIENT)
    assert all(c["passed"] for c in checks), [c["id"] for c in checks if not c["passed"]]

    total = len(API_CLIENT["requirements"])
    rows = derive_rows(API_CLIENT["requirements"], checks)
    assert rows == ["passed"] * total
    assert ratio(rows) == (total, total)


def test_a_failing_check_marks_only_its_own_requirement() -> None:
    # The client renders instead of returning data: "no_dom" (the last
    # requirement) fails and nothing else does.
    source = PASSING_API_CLIENT.replace(
        "  return response.json();",
        '  document.getElementById("movieList").textContent = "ok";\n'
        "  return response.json();",
    )
    checks = run(source, API_CLIENT)
    assert [c["id"] for c in checks if not c["passed"]] == ["no_dom"]

    rows = derive_rows(API_CLIENT["requirements"], checks)
    total = len(API_CLIENT["requirements"])
    assert rows == ["passed"] * (total - 1) + ["failed"]
    assert ratio(rows) == (total - 1, total)


def test_ok_before_parse_failure_marks_both_requirements_it_grades() -> None:
    # The status check is gone, so the body is parsed whatever the server said.
    source = PASSING_API_CLIENT.replace(
        """  if (!response.ok) {
    throw new ApiError(`Request to ${path} failed with status ${response.status}`, response.status);
  }

""",
        "",
    )
    checks = run(source, API_CLIENT)
    assert [c["id"] for c in checks if not c["passed"]] == [
        "ok_branch",
        "error_carries_status",
    ]
    rows = derive_rows(API_CLIENT["requirements"], checks)
    # `ok_branch` grades requirements 1 and 2; `error_carries_status` also
    # grades 1. Everything else stays green.
    assert rows[1] == "failed" and rows[2] == "failed"
    assert [r for i, r in enumerate(rows) if i not in (1, 2)] == ["passed"] * (
        len(rows) - 2
    )


def test_precondition_failure_does_not_move_the_ratio() -> None:
    template = TICKET_TEMPLATES["js_dom"][0]
    requirements = template["requirements"]
    checks = run("const broken = (", template)
    syntax = next(c for c in checks if c["id"] == "syntax")
    assert syntax["precondition"] is True and syntax["passed"] is False

    rows = derive_rows(requirements, checks)
    _, total = ratio(rows)
    # Every requirement is graded by a non-precondition check, so the broken
    # file never consumes a requirement slot.
    assert total == len(requirements) == 5
    assert "ungraded" not in rows


def test_ungraded_requirements_are_excluded_not_failed() -> None:
    # A requirement nothing points at is reported as ungraded and left out of
    # the ratio entirely, rather than counting as a failure the learner cannot
    # act on.
    requirements = ["graded", "ungraded", "also graded"]
    checks = [
        {"id": "a", "requirement_index": 0, "passed": True},
        {"id": "b", "requirement_index": 2, "passed": False},
    ]
    rows = derive_rows(requirements, checks)
    assert rows == ["passed", "ungraded", "failed"]
    assert ratio(rows) == (1, 2)


def test_every_js_async_requirement_is_graded() -> None:
    # The async ticket used to ship a requirement ("render only after the data
    # resolves") that no check graded, so a learner could never see it turn
    # green. js_loading_sequence now grades it.
    template = TICKET_TEMPLATES["js_async"][0]
    checks = run("const broken = 1;", template)
    rows = derive_rows(template["requirements"], checks)
    assert "ungraded" not in rows


def test_run_static_checks_carries_the_mapping_into_the_response() -> None:
    checks = run(PASSING_API_CLIENT, API_CLIENT)
    by_id = {c["id"]: c for c in checks}
    assert by_id["fetch"]["requirement_index"] == 0
    assert by_id["ok_branch"]["requirement_indexes"] == [1, 2]
    assert by_id["syntax"]["precondition"] is True
    assert by_id["no_dead_code"]["requirement_index"] is None
    assert all(c["requirement_mapped"] for c in checks)
