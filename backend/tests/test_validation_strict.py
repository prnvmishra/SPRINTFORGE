"""Strictness proofs for the AST-based JavaScript validator.

Every test here is a submission that used to pass the old regex checks (or that
must keep passing), asserted against the semantics the checks now enforce.
"""

from __future__ import annotations

import asyncio

import pytest

from app.data.practice_modules import PRACTICE_MODULE_INDEX
from app.data.ticket_templates import ASYNC_LOADING_BEHAVIOUR, TICKET_TEMPLATES
from app.services import js_ast
from app.services.sprint_generator import _fill
from app.services.validation_service import run_behaviour_tests, run_static_checks

FILE = "script.js"

TICKET_CHECKS = TICKET_TEMPLATES["js_async_error_handling"][0]["checks"]

REFERENCE_IMPLEMENTATION = """
movieList.innerHTML = `<p class="loading">Loading movies\\u2026</p>`;

try {
  const response = await loadMovies();
  if (!response.ok) {
    throw new Error("Request failed");
  }
  const movies = await response.json();
  movieList.innerHTML = movies.map((movie) => `<article class="card">${movie.title}</article>`).join("");
} catch (error) {
  console.error(error);
  movieList.innerHTML = `
    <div class="error" role="alert">
      <p>Unable to load movies.</p>
      <button type="button">Try again</button>
    </div>
  `;
}
"""


def results(source: str, checks: list[dict], filename: str = FILE) -> dict[str, bool]:
    return {o.id: o.passed for o in run_static_checks({filename: source}, checks)}


def check(check_type: str, **params) -> list[dict]:
    return [{"id": "target", "type": check_type, "file": FILE, "label": check_type, **params}]


def verdict(source: str, check_type: str, **params) -> bool:
    return results(source, check(check_type, **params))["target"]


def detail_of(source: str, check_type: str, **params):
    outcome = run_static_checks({FILE: source}, check(check_type, **params))[0]
    return outcome.detail, outcome.hint


# ---------------------------------------------------------------- 1. syntax


def test_invalid_catch_without_binding_fails_syntax():
    source = """
async function load() {
  try {
    const response = await loadMovies();
  } catch () {
    movieList.innerHTML = "error";
  }
}
"""
    outcomes = run_static_checks({FILE: source}, TICKET_CHECKS)
    assert all(not o.passed for o in outcomes)
    syntax = next(o for o in outcomes if o.id == "syntax")
    assert "Unexpected token" in (syntax.hint or "")
    assert "line" in (syntax.hint or "")


def test_catch_without_braces_binding_still_fails_every_check():
    """The exact submission from the bug report: 4/4 becomes 0/N."""
    source = "try { await loadMovies(); } catch () { }"
    assert not any(o.passed for o in run_static_checks({FILE: source}, TICKET_CHECKS))


# ------------------------------------------------- 2. try/catch actually wraps


def test_await_outside_try_fails():
    source = """
async function load() {
  const response = await loadMovies();
  try {
  } catch (error) {
    movieList.innerHTML = "error";
  }
}
"""
    assert verdict(source, "js_try_catch_await") is False


def test_await_inside_try_passes():
    source = """
async function load() {
  try {
    const response = await loadMovies();
  } catch (error) {
    movieList.textContent = error.message;
  }
}
"""
    assert verdict(source, "js_try_catch_await") is True


def test_catch_without_binding_fails_when_binding_required():
    source = """
async function load() {
  try {
    await loadMovies();
  } catch {
    movieList.innerHTML = "error";
  }
}
"""
    assert verdict(source, "js_try_catch_await", require_binding=True) is False


# ------------------------------------------------------ 3. catch must handle


def test_empty_catch_body_fails():
    source = """
async function load() {
  try {
    await loadMovies();
  } catch (error) {
  }
}
"""
    assert verdict(source, "js_catch_handles") is False


def test_comment_only_catch_body_fails():
    source = """
async function load() {
  try {
    await loadMovies();
  } catch (error) {
    // TODO: handle the error, show a nice message to the user
  }
}
"""
    assert verdict(source, "js_catch_handles") is False


# ------------------------------------------------ 4. ordering: ok before json


def test_json_parsed_before_ok_check_fails():
    source = """
async function load() {
  const response = await loadMovies();
  const movies = await response.json();
  if (!response.ok) {
    throw new Error("failed");
  }
  renderMovies(movies);
}
"""
    assert verdict(source, "js_ok_before_parse") is False


def test_ok_checked_and_thrown_before_json_passes():
    source = """
async function load() {
  const response = await loadMovies();
  if (!response.ok) {
    throw new Error("failed");
  }
  const movies = await response.json();
  renderMovies(movies);
}
"""
    assert verdict(source, "js_ok_before_parse") is True


def test_ok_branch_that_does_not_handle_fails():
    source = """
async function load() {
  const response = await loadMovies();
  if (!response.ok) {
    console.log("hmm");
  }
  const movies = await response.json();
}
"""
    assert verdict(source, "js_ok_before_parse") is False


# ------------------------------------------- 5. DOM feedback, not console.error


def test_console_error_only_fails_error_feedback():
    source = """
async function load() {
  try {
    await loadMovies();
  } catch (error) {
    console.error(error);
  }
}
"""
    assert verdict(source, "js_catch_handles") is True
    assert verdict(source, "js_error_feedback") is False


def test_dom_write_in_catch_passes_error_feedback():
    source = """
async function load() {
  try {
    await loadMovies();
  } catch (error) {
    movieList.insertAdjacentHTML("beforeend", "<p>Unable to load.</p>");
  }
}
"""
    assert verdict(source, "js_error_feedback") is True


# ------------------------------------------------------- 6. loading sequence


def test_loading_word_in_comment_only_fails():
    source = """
async function load() {
  // show a loading spinner here, isLoading = true
  const response = await loadMovies();
  renderMovies(await response.json());
}
"""
    assert verdict(source, "js_loading_sequence") is False


def test_loading_string_literal_only_fails():
    source = """
async function load() {
  const message = "Loading movies...";
  const response = await loadMovies();
  renderMovies(await response.json());
}
"""
    assert verdict(source, "js_loading_sequence") is False


def test_real_loading_mutation_before_and_after_passes():
    source = """
async function load() {
  movieList.innerHTML = "<p>Loading…</p>";
  const response = await loadMovies();
  const movies = await response.json();
  movieList.innerHTML = "";
  renderMovies(movies);
}
"""
    assert verdict(source, "js_loading_sequence") is True


def test_loading_cleared_through_a_render_helper_passes():
    """Extracting the repaint into a helper is better code, not a failure.

    Both helpers are *declared* above the loader, so every DOM write they perform
    sits at a source offset before the await. Bucketing writes by position alone
    reported this as "the loading state is never cleared after the request
    settles", so the check has to follow the call rather than the text.
    """
    source = """
function renderLoading() {
  movieList.innerHTML = "<p>Loading…</p>";
}

function renderMovies(movies) {
  movieList.innerHTML = "";
  movies.forEach((movie) => movieList.append(card(movie)));
}

async function load() {
  renderLoading();
  const response = await fetch("/api/movies");
  const movies = await response.json();
  renderMovies(movies);
}
"""
    assert verdict(source, "js_loading_sequence") is True


def test_helper_that_never_repaints_after_the_request_still_fails():
    """The call-graph resolution must not become a way to pass without clearing.

    `logResult` is called after the await but touches no DOM, so nothing repaints
    once the data lands and the loading state stays on screen.
    """
    source = """
function renderLoading() {
  movieList.innerHTML = "<p>Loading…</p>";
}

function logResult(movies) {
  console.log(movies.length);
}

async function load() {
  renderLoading();
  const response = await fetch("/api/movies");
  const movies = await response.json();
  logResult(movies);
}
"""
    assert verdict(source, "js_loading_sequence") is False


# ----------------------------------------------------- 7. no-op implementations


def test_empty_function_body_fails():
    assert verdict("async function loadMovies() {}", "js_not_trivial", name="loadMovies") is False


def test_comment_only_function_body_fails():
    source = """
async function loadMovies() {
  // TODO: implement this
}
"""
    assert verdict(source, "js_not_trivial", name="loadMovies") is False


def test_constant_return_body_fails():
    source = "async function loadMovies() { return null; }"
    assert verdict(source, "js_not_trivial", name="loadMovies") is False


# --------------------------------------------------------- 8. unreachable code


def test_error_handling_after_unconditional_return_fails():
    source = """
async function load() {
  const response = await loadMovies();
  return response;
  try {
    await loadMovies();
  } catch (error) {
    movieList.innerHTML = "error";
  }
}
"""
    assert verdict(source, "js_no_unreachable") is False


def test_reachable_code_passes_unreachable_check():
    assert verdict(REFERENCE_IMPLEMENTATION, "js_no_unreachable") is True


# ------------------------------------------------------ 9. real usage vs tokens


def test_fetch_in_comment_or_string_does_not_count():
    source = """
// we should fetch(url) here later
const note = "call fetch(url) to load the data";
"""
    assert verdict(source, "js_calls", callee="fetch") is False


def test_real_fetch_call_counts():
    source = "async function load() { const r = await fetch('/api/movies'); return r; }"
    assert verdict(source, "js_calls", callee="fetch") is True


# --------------------------------------- 9b. commented-out code does not count

COMMENT_ONLY_TABLE = """
<!--
<table>
  <thead><tr><th scope="col">Sprint</th></tr></thead>
  <tbody><tr><td>1</td></tr></tbody>
</table>
-->
"""

RENDERED_TABLE = """
<table>
  <thead><tr><th scope="col">Sprint</th></tr></thead>
  <tbody><tr><td>1</td></tr></tbody>
</table>
"""

TABLE_PATTERNS = [
    r"<table",
    r"<thead",
    r"<tbody",
    r"<th\b",
    r"scope\s*=",
    r"<td",
    r"<tr",
]


def _table_checks() -> list[dict]:
    return [
        {"id": f"p{i}", "type": "regex", "file": "index.html", "pattern": p, "label": p}
        for i, p in enumerate(TABLE_PATTERNS)
    ]


def test_comment_only_html_satisfies_no_positive_regex_check():
    """The reported hole: commented-out markup renders nothing, so it must
    score zero, while the same markup outside the comment still scores full."""
    checks = _table_checks()
    commented = run_static_checks({"index.html": COMMENT_ONLY_TABLE}, checks)
    rendered = run_static_checks({"index.html": RENDERED_TABLE}, checks)
    assert sum(o.passed for o in commented) == 0
    assert sum(o.passed for o in rendered) == len(checks)


def test_unterminated_html_comment_hides_the_rest_of_the_file():
    source = "<!-- oops\n<table><tr><td>1</td></tr></table>\n"
    assert verdict(source, "regex", pattern=r"<table") is False


def test_not_regex_treats_a_comment_as_absent_markup():
    """Symmetry with the positive case: commented-out markup renders nothing, so
    it neither satisfies a `regex` check nor violates a `not_regex` prohibition.
    Real inline styling still fails."""
    commented = '<p>ok</p>\n<!-- <div style="color: red">inline</div> -->\n'
    live = '<p>ok</p>\n<div style="color: red">inline</div>\n'
    assert verdict(commented, "not_regex", pattern=r"style\s*=") is True
    assert verdict(live, "not_regex", pattern=r"style\s*=") is False


def test_keep_comments_still_reads_the_raw_source():
    assert (
        verdict(COMMENT_ONLY_TABLE, "regex", pattern=r"<table", keep_comments=True) is True
    )


# ------------------------------------------------- 9c. css_property strictness

PLAN_CARD_CSS = """
.plan-cardxyz { border-radius: 12px; }
.card-header { padding: 4px; }
tbody { background-color: #111; }
"""


def test_css_property_rejects_a_near_miss_selector():
    assert (
        verdict(PLAN_CARD_CSS, "css_property", selector=".plan-card", property="border-radius")
        is False
    )
    assert (
        verdict(
            PLAN_CARD_CSS + ".plan-card { border-radius: 12px; }",
            "css_property",
            selector=".plan-card",
            property="border-radius",
        )
        is True
    )


def test_css_property_does_not_accept_a_longer_class_or_element():
    assert verdict(PLAN_CARD_CSS, "css_property", selector=".card", property="padding") is False
    assert verdict(PLAN_CARD_CSS, "css_property", selector="body", property="background-color") is False


def test_css_property_matches_a_selector_inside_a_compound_or_list():
    css = ".panel > .card:hover, main .card { display: flex; }"
    assert verdict(css, "css_property", selector=".card", property="display") is True


def test_css_property_value_pattern_rejects_a_wrong_value():
    css = ".page { display: block; }"
    assert (
        verdict(css, "css_property", selector=".page", property="display", value_pattern=r"^(flex|grid)$")
        is False
    )
    assert (
        verdict(
            ".page { display: flex; }",
            "css_property",
            selector=".page",
            property="display",
            value_pattern=r"^(flex|grid)$",
        )
        is True
    )


def test_css_property_value_in_rejects_a_wrong_value():
    assert (
        verdict(".page { display: inline; }", "css_property", selector=".page", property="display", value_in=["flex", "grid"])
        is False
    )
    assert (
        verdict(".page { display: grid; }", "css_property", selector=".page", property="display", value_in=["flex", "grid"])
        is True
    )


def test_css_property_without_a_value_constraint_still_asserts_presence_only():
    assert verdict(".page { display: block; }", "css_property", selector=".page", property="display") is True
    assert verdict(".page { color: red; }", "css_property", selector=".page", property="display") is False


def test_ticket_design_tokens_checks_reject_placeholder_values():
    checks = [c for c in TICKET_TEMPLATES["css_basics"][0]["checks"] if c["type"] == "css_property"]
    placeholder = "body { background-color: inherit; color: initial; font-family: unset; }"
    real = "body { background-color: #0b0b0f; color: #eee; font-family: system-ui, sans-serif; }"
    assert [o.passed for o in run_static_checks({"styles.css": placeholder}, checks)] == [False] * 3
    assert all(o.passed for o in run_static_checks({"styles.css": real}, checks))


def test_ticket_design_tokens_checks_are_not_satisfied_by_a_tbody_rule():
    """`body` used to match `tbody` by substring."""
    checks = [c for c in TICKET_TEMPLATES["css_basics"][0]["checks"] if c["type"] == "css_property"]
    css = "tbody { background-color: #111; color: #eee; font-family: serif; }"
    assert [o.passed for o in run_static_checks({"styles.css": css}, checks)] == [False] * 3


# ------------------------------------------- 10. the reference implementation


def test_reference_implementation_passes_every_ticket_check():
    outcomes = run_static_checks({FILE: REFERENCE_IMPLEMENTATION}, TICKET_CHECKS)
    failed = [(o.id, o.detail) for o in outcomes if not o.passed]
    assert failed == []


# ------------------------------------------------------------- fail closed

#: The ticket also carries textual checks (the error state's role and its retry
#: control), which read the source directly and are unaffected by the parser.
#: Fail-closed is a property of the AST-driven checks specifically.
JS_TICKET_CHECKS = [c for c in TICKET_CHECKS if c["type"].startswith("js_")]


def test_checks_fail_closed_when_the_ast_tool_is_unavailable(monkeypatch):
    js_ast.clear_parse_cache()
    monkeypatch.setattr(js_ast.shutil, "which", lambda _name: None)
    outcomes = run_static_checks({FILE: REFERENCE_IMPLEMENTATION}, JS_TICKET_CHECKS)
    js_ast.clear_parse_cache()
    assert all(not o.passed for o in outcomes)
    assert any("Node.js" in (o.hint or "") for o in outcomes)


def test_checks_fail_closed_when_the_parser_output_is_unreadable(monkeypatch):
    js_ast.clear_parse_cache()

    class _Proc:
        returncode = 0
        stdout = "not json"
        stderr = ""

    monkeypatch.setattr(js_ast.subprocess, "run", lambda *a, **k: _Proc())
    outcomes = run_static_checks({FILE: REFERENCE_IMPLEMENTATION}, JS_TICKET_CHECKS)
    js_ast.clear_parse_cache()
    assert all(not o.passed for o in outcomes)


# --------------------------------------------- layer 2: injected behaviour


def _behaviour(source: str):
    return asyncio.run(
        run_behaviour_tests(
            source,
            ASYNC_LOADING_BEHAVIOUR["assertions"],
            ASYNC_LOADING_BEHAVIOUR["prelude"],
            ASYNC_LOADING_BEHAVIOUR["wrap_as"],
        )
    )


def test_reference_implementation_passes_behaviour_tests():
    outcomes = _behaviour(REFERENCE_IMPLEMENTATION)
    failed = [(o.label, o.detail) for o in outcomes if not o.passed]
    assert failed == []


def test_hardcoded_resolved_promise_fails_the_failure_scenarios():
    """The harness owns the network function, so a fake response cannot pass."""
    fake = """
try {
  const response = await Promise.resolve({ ok: true, status: 200, json: async () => [] });
  if (!response.ok) {
    throw new Error("Request failed");
  }
  const movies = await response.json();
  movieList.innerHTML = movies.map((movie) => `<article class="card">${movie.title}</article>`).join("");
} catch (error) {
  movieList.innerHTML = "<p>Unable to load movies.</p>";
}
"""
    by_id = {o.id: o.passed for o in _behaviour(fake)}
    assert by_id["rejection_contained"] is False
    assert by_id["non_ok_not_parsed"] is False


def test_swallowed_rejection_fails_behaviour_tests():
    swallowed = """
try {
  const response = await loadMovies();
  const movies = await response.json();
  movieList.innerHTML = movies.map((movie) => `<article class="card">${movie.title}</article>`).join("");
} catch (error) {
  console.error(error);
}
"""
    by_id = {o.id: o.passed for o in _behaviour(swallowed)}
    assert by_id["rejection_contained"] is False
    assert by_id["non_ok_not_parsed"] is False


def test_invalid_syntax_reports_a_parse_error_instead_of_running():
    outcomes = _behaviour("try { await loadMovies(); } catch () { }")
    assert len(outcomes) == 1
    assert outcomes[0].passed is False
    assert "Unexpected token" in (outcomes[0].hint or "")


# ------------------------------------------- no regressions in other layers


def test_html_module_still_validates():
    module = PRACTICE_MODULE_INDEX["html-profile-card"]
    files = dict(module["files"])
    files.update(module.get("solution_files") or {})
    outcomes = run_static_checks(files, module["checks"])
    assert [o.id for o in outcomes if not o.passed] == []


def test_css_module_still_validates():
    module = PRACTICE_MODULE_INDEX["css-profile-card"]
    files = dict(module["files"])
    files.update(module.get("solution_files") or {})
    outcomes = run_static_checks(files, module["checks"])
    assert [o.id for o in outcomes if not o.passed] == []


def test_async_practice_module_solution_passes_its_checks():
    module = PRACTICE_MODULE_INDEX["js-async-error-handling"]
    files = dict(module["files"])
    files.update(module.get("solution_files") or {})
    outcomes = run_static_checks(files, module["checks"])
    assert [o.id for o in outcomes if not o.passed] == []


#: The same guarantee for project ticket templates: a reference solution exists
#: and satisfies every check the ticket grades. `scripts/verify_web_ticket_solutions.py`
#: additionally proves the negative side (fake submissions fail).
_TICKET_SOLUTIONS = sorted(
    (skill, template["slug"])
    for skill, templates in TICKET_TEMPLATES.items()
    for template in templates
    if template.get("solution_files")
)
_TICKET_CONTEXT = {"domain": "Movie Booking", "entity": "movie", "entity_plural": "movies"}


@pytest.mark.parametrize("skill,slug", _TICKET_SOLUTIONS, ids=lambda v: v)
def test_every_ticket_template_solution_passes_its_own_checks(skill, slug):
    template = next(t for t in TICKET_TEMPLATES[skill] if t["slug"] == slug)
    files = {
        name: _substitute(body) for name, body in _reference_project_files().items()
    }
    files.update({name: _substitute(body) for name, body in template["solution_files"].items()})
    outcomes = run_static_checks(files, _fill(template["checks"], _TICKET_CONTEXT))
    assert outcomes
    assert [o.id for o in outcomes if not o.passed] == []


def _substitute(text: str) -> str:
    for key, value in _TICKET_CONTEXT.items():
        text = text.replace("{" + key + "}", value)
    return text


def _reference_project_files() -> dict[str, str]:
    from app.data import ticket_templates as tt

    return {
        "index.html": tt.HTML_NAVIGATION_SOLUTION,
        "styles.css": tt.CSS_CARD_GRID_SOLUTION,
        "script.js": tt.JS_RENDER_LIST_SOLUTION,
    }


#: The styling tickets: the ones whose whole point is that the finished project
#: looks like a product, and therefore the ones most at risk of being graded by
#: checks that pass on work nobody did.
_STYLING_TICKETS = ["css_basics", "css_layout", "css_responsive"]


@pytest.mark.parametrize("skill", _STYLING_TICKETS)
def test_no_requirement_is_met_by_the_untouched_starter_stylesheet(skill):
    """A ticket must never be satisfiable by the file the learner was handed.

    The starter scaffolds the section order and names the token roles, so it
    looks like a stylesheet — which is exactly why this has to be asserted
    rather than assumed. Asserted per requirement rather than per check: a few
    outcome checks ("nothing overflows a 360px viewport") are legitimately true
    of an unstyled page, and what must not happen is a *requirement* being
    reported as met.
    """
    from app.data import ticket_templates as tt

    template = TICKET_TEMPLATES[skill][0]
    files = {name: _substitute(body) for name, body in _reference_project_files().items()}
    files["styles.css"] = _substitute(tt.STARTER_FILES["styles.css"].format(**_TICKET_CONTEXT))
    outcomes = run_static_checks(files, _fill(template["checks"], _TICKET_CONTEXT))

    owners: dict[int, list[bool]] = {}
    for outcome in outcomes:
        if outcome.precondition:
            continue
        for index in outcome.requirement_indexes or []:
            owners.setdefault(index, []).append(outcome.passed)

    met = [index for index, results in owners.items() if all(results)]
    assert met == [], [template["requirements"][i] for i in met]


@pytest.mark.parametrize("skill", _STYLING_TICKETS + ["html_basics", "html_semantics", "js_dom"])
def test_every_requirement_of_a_web_ticket_is_graded_by_a_check(skill):
    """Requirements and checks stay in lockstep: no requirement the product
    states may be unverifiable, or the panel starts claiming things it cannot
    know."""
    template = TICKET_TEMPLATES[skill][0]
    owned: set[int] = set()
    for spec in template["checks"]:
        if spec.get("precondition"):
            continue
        indexes = spec.get("requirement_indexes") or []
        single = spec.get("requirement_index")
        if isinstance(single, int):
            indexes = [*indexes, single]
        owned.update(indexes)
    ungraded = [
        (index, requirement)
        for index, requirement in enumerate(template["requirements"])
        if index not in owned
    ]
    assert ungraded == []


def test_misspelled_tokens_are_caught_even_though_the_text_looks_right():
    """`var(--surfcae)` is textually indistinguishable from a correct theme and
    renders as nothing. Only the render judge can tell them apart."""
    from app.data import ticket_templates as tt

    template = TICKET_TEMPLATES["css_basics"][0]
    files = {name: _substitute(body) for name, body in _reference_project_files().items()}
    files["styles.css"] = _substitute(
        tt.CSS_TOKENS_SOLUTION.replace("var(--surface)", "var(--surfcae)")
    )
    outcomes = run_static_checks(files, _fill(template["checks"], _TICKET_CONTEXT))
    failed = {o.id for o in outcomes if not o.passed}
    assert "body_paints" in failed


@pytest.mark.parametrize("module_id", sorted(PRACTICE_MODULE_INDEX))
def test_every_web_module_solution_passes_its_own_checks(module_id):
    module = PRACTICE_MODULE_INDEX[module_id]
    if module["kind"] != "web" or not module.get("solution_files"):
        pytest.skip("no reference solution")
    files = dict(module["files"])
    files.update(module["solution_files"])
    outcomes = run_static_checks(files, module.get("checks", []))
    assert [o.id for o in outcomes if not o.passed] == []


# --------------------------------------------------------- API client shape

def test_endpoint_pair_accepts_the_names_a_learner_actually_reaches_for():
    """The check grades the client's shape, not its vocabulary.

    The previous pair of regexes accepted only `list|getAll|fetchAll|load…` for
    the collection endpoint, so `fetchRecipes()` — the most obvious name, and one
    the brief never rules out — failed while an unrelated `loadMovies()` left over
    from an earlier ticket satisfied it without touching the API.
    """
    source = """
const API_BASE_URL = "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    throw new Error(`The service responded with ${response.status}`);
  }
  return response.json();
}

async function fetchRecipes() {
  return request("/recipes");
}

async function fetchRecipe(id) {
  return request(`/recipes/${id}`);
}
"""
    assert verdict(source, "js_endpoint_pair") is True


def test_endpoint_pair_rejects_one_function_that_takes_a_path():
    """The anti-pattern the ticket exists to rule out.

    `request` reaches the network and takes an argument, so on arity alone it
    reads as a single-item endpoint. There is no collection call, so the module
    exposes no endpoints at all.
    """
    source = """
const API_BASE_URL = "/api";

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }
  return response.json();
}
"""
    assert verdict(source, "js_endpoint_pair") is False


def test_endpoint_pair_rejects_a_client_with_only_a_list_call():
    """A helper plus a list call is not a pair.

    This is the case arity alone gets wrong: `request(p)` would be counted as the
    single-item endpoint even though it is the private helper the list call
    delegates to.
    """
    source = """
const API_BASE_URL = "/api";

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }
  return response.json();
}

async function listRecipes() {
  return request("/recipes");
}
"""
    assert verdict(source, "js_endpoint_pair") is False


def test_endpoint_pair_rejects_functions_that_never_reach_the_api():
    """Correctly named and correctly shaped, but reading a local array."""
    source = """
const API_BASE_URL = "/api";

function listRecipes() {
  return recipes;
}

function getRecipe(id) {
  return recipes.find((recipe) => recipe.id === id);
}
"""
    assert verdict(source, "js_endpoint_pair") is False


# ------------------------------------------------------------- useState pairs

def test_state_pair_accepts_the_hook_spelling_the_starter_hands_you():
    """`React.useState` is the only spelling available from `import React from "react"`.

    The previous regex required the hook to be written bare and required the state
    variable to be *named* for what it holds, so the natural port of the starter
    failed a check its own hint could not have warned about.
    """
    assert verdict("const [selectedIds, setSelectedIds] = React.useState([]);", "js_state_pair") is True
    assert verdict("const [selected, setSelected] = useState(null);", "js_state_pair") is True
    # The name of the value is not the check's business — `selection_prop`,
    # `aria_pressed` and `conditional_class` establish what the state means.
    assert verdict("const [tonight, setTonight] = useState([]);", "js_state_pair") is True


def test_state_pair_rejects_a_useState_that_is_never_destructured():
    """`const s = useState([])` gives you an array, not a value and a setter."""
    assert verdict("const s = useState([]);", "js_state_pair") is False


def test_state_pair_rejects_a_setter_not_named_for_what_it_does():
    assert verdict("const [selected, change] = useState(null);", "js_state_pair") is False


def test_state_pair_rejects_a_different_hook():
    assert verdict("const [a, setA] = useReducer(reducer, 0);", "js_state_pair") is False


# ------------------------------------------- wiring the failure into the UI

def _jsx_verdict(source: str) -> bool:
    outcome = run_static_checks(
        {"App.jsx": source},
        [{"id": "x", "type": "js_catch_sets_state", "file": "App.jsx", "label": "l"}],
    )[0]
    return outcome.passed


_FETCHING_COMPONENT = """
import React, { useEffect, useState } from "react";

function App() {
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch("/api/items", { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`Request failed with ${response.status}`);
        }
        setItems(await response.json());
      } catch (error) {
        if (error.name === "AbortError") return;
        __HANDLER__
      } finally {
        setIsLoading(false);
      }
    }
    load();
    return () => controller.abort();
  }, []);

  if (isLoading) return <p role="status">Loading…</p>;
  if (error) return <p role="alert">{error}</p>;
  return <section id="itemList" />;
}

export default App;
"""


def test_catch_that_only_logs_cannot_pass_the_error_state_requirement():
    """The false pass this check exists to close.

    A component can declare the error state, render a `role="alert"` branch and
    still only `console.error()` in the catch. Every check on those three things
    passes individually while the alert branch is unreachable code, so the user
    sees a spinner stop and nothing else. Only the wiring between them shows it.
    """
    assert _jsx_verdict(_FETCHING_COMPONENT.replace("__HANDLER__", "console.error(error);")) is False


def test_catch_that_records_the_failure_passes():
    assert _jsx_verdict(_FETCHING_COMPONENT.replace("__HANDLER__", "setError(error.message);")) is True
    # A fixed, friendlier message is a legitimate choice — the check is about the
    # failure reaching state, not about where the wording comes from.
    assert _jsx_verdict(_FETCHING_COMPONENT.replace("__HANDLER__", 'setError("We could not load that.");')) is True


def test_flipping_a_loading_flag_in_the_catch_is_not_recording_the_failure():
    assert _jsx_verdict(_FETCHING_COMPONENT.replace("__HANDLER__", "setIsLoading(false);")) is False


def test_empty_catch_never_records_the_failure():
    assert _jsx_verdict(_FETCHING_COMPONENT.replace("__HANDLER__", "")) is False


# --------------------------------------------------- REST routes and statuses

def _rest_outcomes(source: str):
    from app.data.ticket_templates import TICKET_TEMPLATES

    return run_static_checks({"server.js": source}, TICKET_TEMPLATES["rest_api"][0]["checks"])


_REAL_SERVER = """
const express = require("express");
const app = express();
app.use(express.json());

let items = [{ id: 1, title: "One", price: 10 }];
let nextId = 2;

app.get("/api/items", (req, res) => {
  res.json(items);
});

app.get("/api/items/:id", (req, res) => {
  const item = items.find((candidate) => candidate.id === Number(req.params.id));
  if (!item) {
    return res.status(404).json({ error: "not found" });
  }
  return res.json(item);
});

app.post("/api/items", (req, res) => {
  const body = req.body || {};
  if (typeof body.title !== "string" || body.title.trim() === "") {
    return res.status(400).json({ error: "title is required" });
  }
  const item = { id: nextId, title: body.title.trim(), price: body.price };
  nextId += 1;
  items.push(item);
  return res.status(201).json(item);
});

module.exports = app;
"""


def test_a_real_rest_implementation_passes_every_check():
    assert [o.id for o in _rest_outcomes(_REAL_SERVER) if not o.passed] == []


def test_three_empty_route_handlers_cannot_pass():
    """The exact payload that used to score full marks.

    Every route is registered, so the path regexes were satisfied, and the status
    codes appear in the file, so the bare `404`/`201`/`400` regexes were satisfied
    too. Nothing answers anything.
    """
    source = """
const express = require("express");
const app = express();
app.use(express.json());
app.get("/api/items", (req, res) => {});
app.get("/api/items/:id", (req, res) => {});
app.post("/api/items", (req, res) => {});
const codes = [404, 201, 400];
module.exports = app;
"""
    failed = {o.id for o in _rest_outcomes(source) if not o.passed}
    assert {"handlers_implemented", "status_404", "status_201", "status_400"} <= failed


def test_status_codes_mentioned_only_in_a_comment_cannot_pass():
    source = """
const express = require("express");
const app = express();
// documented: 404 when missing, 201 on create, 400 on invalid input
app.get("/api/items", (req, res) => res.json([]));
app.get("/api/items/:id", (req, res) => res.json({}));
app.post("/api/items", (req, res) => res.json({}));
module.exports = app;
"""
    failed = {o.id for o in _rest_outcomes(source) if not o.passed}
    assert {"status_404", "status_201", "status_400"} <= failed


def test_a_route_that_always_answers_404_is_not_a_lookup():
    """"Returns 404 when missing" is a branch, not the route's only behaviour."""
    source = """
const express = require("express");
const app = express();
app.get("/api/items", (req, res) => res.json([]));
app.get("/api/items/:id", (req, res) => res.status(404).json({}));
app.post("/api/items", (req, res) => res.status(201).json({}));
module.exports = app;
"""
    failed = {o.id for o in _rest_outcomes(source) if not o.passed}
    assert "status_404" in failed
    # The happy-path 201 is not required to be conditional.
    assert "status_201" not in failed


# --------------------------------------------------------------- SQL comments

def test_a_schema_of_nothing_but_sql_comments_cannot_pass():
    """The payload that used to score full marks on the schema ticket.

    `_strip_comments` knew about HTML, `/* */` and `//`, but not SQL's `--`, so
    every keyword the checks look for could sit in a comment and satisfy them.
    """
    from app.data.ticket_templates import TICKET_TEMPLATES

    source = (
        "-- PRIMARY KEY FOREIGN KEY NOT NULL CREATE INDEX\n"
        "-- CREATE TABLE recipes CREATE TABLE bookings\n"
        "SELECT 1;\n"
    )
    outcomes = run_static_checks(
        {"schema.sql": source}, TICKET_TEMPLATES["database_modeling"][0]["checks"]
    )
    assert [o.id for o in outcomes if o.passed] == []


def test_a_double_dash_inside_a_string_literal_is_not_a_comment():
    """Stripping has to stop at the quote, or it would eat real DDL."""
    from app.data.ticket_templates import TICKET_TEMPLATES

    source = (
        "CREATE TABLE t (a TEXT NOT NULL DEFAULT '-- not a comment');\n"
        "CREATE TABLE u (id INT PRIMARY KEY, t_a INT REFERENCES t(a));\n"
        "CREATE INDEX i ON u (t_a);\n"
    )
    outcomes = run_static_checks(
        {"schema.sql": source}, TICKET_TEMPLATES["database_modeling"][0]["checks"]
    )
    assert [o.id for o in outcomes if not o.passed] == []
