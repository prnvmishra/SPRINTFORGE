"""Both directions of the rendered (headless-browser) judge.

The two halves of the standard are tested side by side, because either one alone
is a bug:

* a correct page — and every shipped module solution — passes every rendered
  check, so good work is never rejected;
* each class of fake that the text-based checks accept is rejected, with a
  message that says what was rendered versus what was required.

Rendering tests are skipped, loudly, when Chromium is not installed. The
"browser missing" behaviour itself is tested without a browser, so the
fail-closed contract is covered even in that environment.
"""

from __future__ import annotations

import pytest

from app.data.practice_modules import PRACTICE_MODULE_INDEX
from app.services import render_judge
from app.services.validation_service import run_static_checks

BROWSER_AVAILABLE = render_judge.is_available()
needs_browser = pytest.mark.skipif(
    not BROWSER_AVAILABLE,
    reason="headless Chromium is not installed (`playwright install chromium`)",
)

HTML = """<!DOCTYPE html>
<html lang="en">
  <head><link rel="stylesheet" href="styles.css" /></head>
  <body>
    <main class="page">
      <section class="board">
        <article class="tile"><h2>One</h2></article>
        <article class="tile"><h2>Two</h2></article>
        <article class="tile"><h2>Three</h2></article>
      </section>
      <div class="card"><p class="note">Centred card</p></div>
      <div class="overlay"><div class="modal">Modal</div></div>
    </main>
  </body>
</html>
"""

CORRECT_CSS = """
:root { --surface: #0b0b12; --ink: #eef1f6; --accent: #6ea8ff; }
body { margin: 0; background-color: var(--surface); color: var(--ink); }
.board { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.tile { padding: 24px; background: #171a22; }
.card { width: 320px; margin: 24px auto; padding: 16px; background: #171a22; }
.note { color: var(--accent); }
.overlay { position: relative; height: 200px; }
.modal { position: absolute; inset: 0; z-index: 2; background: #222; }
"""


def grade(css: str, checks: list[dict], html: str = HTML):
    files = {"index.html": html, "styles.css": css}
    return {o.id: o for o in run_static_checks(files, checks)}


def check(cid: str, **spec) -> dict:
    return {"id": cid, "label": cid, **spec}


ALL_KINDS = [
    check(
        "style",
        type="render_computed_style",
        selector=".tile",
        property="padding-top",
        min_value=16,
        all_match=True,
    ),
    check("columns", type="render_grid_columns", selector=".board", equals=3),
    check("row", type="render_row_layout", selector=".board", min_children=3, max_rows=1),
    check("centred", type="render_centered", selector=".card", axis="horizontal"),
    check("visible", type="render_visible", selector=".note", non_empty=True, min_height=8),
    check(
        "dark",
        type="render_color",
        selector="body",
        property="background-color",
        max_luminance=0.15,
    ),
    check(
        "accent",
        type="render_color",
        selector=".note",
        property="color",
        differs_from_parent=True,
    ),
    check("box", type="render_box", selector=".card", min_width=300, max_width=400),
    check("on_top", type="render_on_top", selector=".modal", over=".overlay"),
]


# ---------------------------------------------------------------- correct work


@needs_browser
def test_a_correct_page_passes_every_rendered_check():
    outcomes = grade(CORRECT_CSS, ALL_KINDS)
    failed = {cid: o.detail for cid, o in outcomes.items() if not o.passed}
    assert failed == {}


@needs_browser
def test_a_correct_page_reports_what_it_observed_even_when_passing():
    outcomes = grade(CORRECT_CSS, ALL_KINDS)
    assert "3 column(s)" in outcomes["columns"].detail
    assert "luminance" in outcomes["dark"].detail


@needs_browser
@pytest.mark.parametrize(
    "css",
    [
        # Grid with explicit tracks.
        ".board { display: grid; grid-template-columns: 1fr 1fr 1fr; }",
        # Grid with auto-fit, which resolves to three at this width.
        ".board { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }",
        # Grid with named lines around the tracks.
        ".board { display: grid; grid-template-columns: [a] 1fr [b] 1fr [c] 1fr [end]; }",
        # Inline grid is still a grid.
        ".board { display: inline-grid; grid-template-columns: repeat(3, 200px); }",
    ],
)
def test_any_legitimate_way_to_get_three_columns_passes(css):
    """Several techniques reach the same rendered outcome; all must be accepted."""
    outcomes = grade(css, [ALL_KINDS[1]])
    assert outcomes["columns"].passed, outcomes["columns"].detail


@needs_browser
@pytest.mark.parametrize(
    "css",
    [
        ".board { display: flex; gap: 16px; } .tile { flex: 1; }",
        ".board { display: grid; grid-template-columns: repeat(3, 1fr); }",
        ".tile { display: inline-block; width: 30%; }",
        ".board::after { content: ''; display: table; clear: both; } .tile { float: left; width: 30%; }",
    ],
)
def test_any_legitimate_way_to_get_a_row_passes(css):
    outcomes = grade(css, [ALL_KINDS[2]])
    assert outcomes["row"].passed, outcomes["row"].detail


@needs_browser
@pytest.mark.parametrize(
    "css",
    [
        ".card { width: 320px; margin: 0 auto; }",
        ".page { display: flex; justify-content: center; } .card { width: 320px; }",
        ".page { display: grid; justify-items: center; } .card { width: 320px; }",
        ".card { width: 320px; position: relative; left: 50%; transform: translateX(-50%); }",
    ],
)
def test_any_legitimate_way_to_centre_passes(css):
    outcomes = grade(css, [ALL_KINDS[3]])
    assert outcomes["centred"].passed, outcomes["centred"].detail


@needs_browser
def test_sub_pixel_and_near_miss_layouts_are_not_rejected():
    """Tolerances exist so rounding does not fail a correct solution."""
    css = ".card { width: 321px; margin-left: auto; margin-right: auto; }"
    outcomes = grade(css, [ALL_KINDS[3]])
    assert outcomes["centred"].passed, outcomes["centred"].detail


# ------------------------------------------------------------------- the fakes


@needs_browser
def test_a_stylesheet_whose_selectors_match_nothing_is_rejected():
    css = """
    .boardx { display: grid; grid-template-columns: repeat(3, 1fr); }
    .cardx { width: 320px; margin: 0 auto; }
    .tilex { padding: 24px; }
    body { background-color: #0b0b12; }
    """
    outcomes = grade(css, ALL_KINDS)
    assert not outcomes["columns"].passed
    assert "rendered 0" in outcomes["columns"].detail or "not a grid" in outcomes["columns"].detail
    assert not outcomes["centred"].passed
    assert not outcomes["style"].passed
    assert "'0px'" in outcomes["style"].detail


@needs_browser
def test_empty_and_invalid_declaration_values_are_rejected():
    css = """
    .board { display: grid; grid-template-columns: ; }
    .tile { padding: ; }
    body { background-color: var(--never-declared); }
    .note { color: var(--also-never-declared); }
    """
    outcomes = grade(css, ALL_KINDS)
    assert not outcomes["columns"].passed
    assert not outcomes["style"].passed
    assert not outcomes["dark"].passed
    assert "paints nothing" in outcomes["dark"].detail
    assert not outcomes["accent"].passed
    assert "did not resolve" in outcomes["accent"].detail


@needs_browser
def test_a_grid_that_declares_columns_but_renders_one_is_rejected():
    css = ".board { display: grid; grid-template-columns: 1fr; }"
    outcomes = grade(css, [ALL_KINDS[1]])
    assert not outcomes["columns"].passed
    assert "expected 3 columns, rendered 1" in outcomes["columns"].detail


@needs_browser
def test_a_declared_grid_that_never_applies_is_rejected():
    """The classic hole: a real rule, on a real selector, trapped in @media print."""
    css = """
    @media print {
      .board { display: grid; grid-template-columns: repeat(3, 1fr); }
    }
    """
    outcomes = grade(css, [ALL_KINDS[1]])
    assert not outcomes["columns"].passed
    assert "not a grid container" in outcomes["columns"].detail


@needs_browser
def test_a_flex_row_faked_with_floats_is_rejected_where_flex_is_the_requirement():
    css = """
    .board { overflow: hidden; }
    .tile { float: left; width: 30%; }
    """
    flex_required = check(
        "flex",
        type="render_computed_style",
        selector=".board",
        property="display",
        value_in=["flex", "inline-flex", "grid", "inline-grid"],
    )
    outcomes = grade(css, [flex_required])
    assert not outcomes["flex"].passed
    assert "-> 'block'" in outcomes["flex"].detail


@needs_browser
@pytest.mark.parametrize(
    "hidden_css,expected",
    [
        (".note { display: none; }", "display: none"),
        (".note { visibility: hidden; }", "visibility: hidden"),
        (".note { opacity: 0; }", "opacity: 0"),
        (".note { height: 0; overflow: hidden; }", "0px"),
        (".note { position: absolute; left: -9999px; }", "outside the page"),
    ],
)
def test_content_present_in_the_dom_but_not_rendered_is_rejected(hidden_css, expected):
    outcomes = grade(CORRECT_CSS + hidden_css, [ALL_KINDS[4]])
    assert not outcomes["visible"].passed
    assert expected in outcomes["visible"].detail


@needs_browser
def test_an_element_with_no_content_is_rejected_even_when_visible():
    html = HTML.replace('<p class="note">Centred card</p>', '<p class="note"></p>')
    outcomes = grade(CORRECT_CSS + ".note { min-height: 20px; }", [ALL_KINDS[4]], html=html)
    assert not outcomes["visible"].passed
    assert "renders no content" in outcomes["visible"].detail


@needs_browser
def test_an_element_painted_underneath_another_is_rejected():
    css = CORRECT_CSS.replace("z-index: 2;", "z-index: -1;")
    outcomes = grade(css, [ALL_KINDS[8]])
    assert not outcomes["on_top"].passed
    assert "topmost element" in outcomes["on_top"].detail


@needs_browser
def test_a_missing_element_is_reported_as_missing_not_as_a_pass():
    outcomes = grade(CORRECT_CSS, [check("gone", type="render_visible", selector=".nope")])
    assert not outcomes["gone"].passed
    assert "0 element(s) matching .nope" in outcomes["gone"].detail


@needs_browser
def test_an_invalid_selector_fails_closed():
    outcomes = grade(CORRECT_CSS, [check("bad", type="render_visible", selector=".a >>> .b")])
    assert not outcomes["bad"].passed
    assert "invalid selector" in outcomes["bad"].detail


# ------------------------------------------------- honest degradation & limits


def test_a_missing_browser_fails_the_check_rather_than_passing_it(monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise render_judge.RenderUnavailable("Playwright is not installed")

    monkeypatch.setattr(render_judge._BROWSER, "run", unavailable)
    outcomes = grade(CORRECT_CSS, ALL_KINDS)
    assert [o.passed for o in outcomes.values()] == [False] * len(ALL_KINDS)
    for outcome in outcomes.values():
        assert "browser was unavailable" in outcome.detail
        assert outcome.skipped is False


def test_a_missing_browser_is_marked_skipped_only_in_skip_mode(monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise render_judge.RenderUnavailable("Playwright is not installed")

    monkeypatch.setattr(render_judge._BROWSER, "run", unavailable)
    monkeypatch.setenv("SPRINTFORGE_RENDER_JUDGE", "skip")
    outcomes = grade(CORRECT_CSS, ALL_KINDS)
    # Skipped is a marker, never a pass: the ratio still records a failure.
    assert all(o.skipped and not o.passed for o in outcomes.values())


def test_a_hanging_page_is_reported_as_a_failure(monkeypatch):
    def hang(*_args, **_kwargs):
        raise TimeoutError("the page did not finish rendering within 20s")

    monkeypatch.setattr(render_judge._BROWSER, "run", hang)
    outcomes = grade(CORRECT_CSS, [ALL_KINDS[1]])
    assert not outcomes["columns"].passed
    assert "did not finish rendering" in outcomes["columns"].detail


def test_a_submission_without_the_entry_document_fails_loudly(monkeypatch):
    outcomes = {
        o.id: o
        for o in run_static_checks({"styles.css": CORRECT_CSS}, [ALL_KINDS[1]])
    }
    assert not outcomes["columns"].passed
    assert "no entry document" in outcomes["columns"].detail


def test_non_rendered_checks_never_touch_the_browser(monkeypatch):
    """A JS/SQL/text-only module must not pay for the browser at all."""
    calls = []
    monkeypatch.setattr(
        render_judge._BROWSER, "run", lambda *a, **k: calls.append(a) or []
    )
    run_static_checks(
        {"index.html": HTML, "styles.css": CORRECT_CSS},
        [
            {"id": "text", "type": "css_property", "file": "styles.css", "property": "display"},
            {"id": "dom", "type": "html_element", "file": "index.html", "selector": "main"},
        ],
    )
    assert calls == []


def test_rendered_checks_sharing_a_page_are_batched_into_one_load(monkeypatch):
    """Grading runs inside a request: one navigation per (document, viewport)."""
    loads = []
    real_run = render_judge._BROWSER.run

    def counting(html, viewport, specs):
        loads.append((viewport["width"], len(specs)))
        return real_run(html, viewport, specs) if BROWSER_AVAILABLE else [{} for _ in specs]

    monkeypatch.setattr(render_judge._BROWSER, "run", counting)
    checks = list(ALL_KINDS) + [
        check(
            "narrow",
            type="render_grid_columns",
            selector=".board",
            viewport={"width": 420, "height": 800},
            max=2,
        )
    ]
    grade(CORRECT_CSS, checks)
    assert sorted(loads) == [(420, 1), (1280, len(ALL_KINDS))]


@needs_browser
def test_the_browser_process_is_reused_across_submissions():
    """The second grade must not pay for a launch, or grading blocks a request."""
    import time

    grade(CORRECT_CSS, ALL_KINDS)
    start = time.perf_counter()
    grade(CORRECT_CSS, ALL_KINDS)
    assert (time.perf_counter() - start) < 3.0


# ------------------------------------------------------- the shipped solutions

RENDERED_MODULES = sorted(
    module_id
    for module_id, module in PRACTICE_MODULE_INDEX.items()
    if any(
        c.get("type") in render_judge.RENDER_CHECK_TYPES
        for c in module.get("checks", [])
    )
)


def test_the_rendered_checks_are_actually_wired_into_modules():
    assert len(RENDERED_MODULES) >= 4, RENDERED_MODULES


@needs_browser
@pytest.mark.parametrize("module_id", RENDERED_MODULES)
def test_every_module_with_rendered_checks_passes_them_with_its_own_solution(module_id):
    module = PRACTICE_MODULE_INDEX[module_id]
    assert module.get("solution_files"), "a rendered module needs a verified solution"
    files = dict(module["files"])
    files.update(module["solution_files"])
    outcomes = run_static_checks(files, module["checks"])
    assert [(o.id, o.detail) for o in outcomes if not o.passed] == []


#: Fakes built deliberately against the *text* checks of a real module: each one
#: satisfies (nearly) all of them and renders nothing like the requirement. The
#: assertion is the whole point of this work — the text layer accepts them, the
#: rendered layer does not.
MODULE_FAKES = {
    "css-grid-ops-dashboard": """
.dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px; grid-auto-rows: minmax(160px, auto); }
.panel--wide { grid-column: span 2; }
.panel--tall { grid-row: span 2; }
@media print { .panel { padding: 20px; } }
.dashboard { grid-template-columns: 1fr; }
""",
    "css-flexbox-app-header": """
@media print {
  .site-header { display: flex; align-items: center; gap: 16px; }
  .nav-links { display: flex; flex-wrap: wrap; list-style: none; }
  .header-actions { display: flex; margin-left: auto; }
}
.site-header { overflow: hidden; }
.site-header > * { float: left; }
.brand { flex-shrink: 0; }
.search-field { flex-grow: 1; min-width: 0; width: 80px; }
""",
    "css-custom-properties-theme": """
:root { --color-surface: ; --color-text: ; --color-accent: ; --color-muted: ; --space-md: 20px; }
body { background-color: var(--color-surfase); color: var(--color-txt); }
.stat-card { background-color: var(--color-surface); padding: var(--space-mdd); }
.stat-card__value { color: var(--color-accnt); }
.stat-card__label { color: var(--color-mutedd); }
[data-theme="dark"] { --color-surface: ; --color-text: ; }
""",
    "css-box-model-pricing": """
*, *::before, *::after { box-sizing: border-box; }
.plan-cardx { padding: 32px; border: 1px solid #ccc; border-radius: 12px;
  max-width: 360px; margin: 0 auto; }
.plan-card { padding: 32px; border: 1px solid #ccc; border-radius: 12px;
  max-width: 360px; margin: 0; }
.plan-features { list-style: none; padding-left: 0; }
.plan-feature { border-bottom: 1px solid #eee; padding-bottom: 8px; }
.plan-cta { display: inline-block; padding: 12px 24px; }
.plan-features { list-style: disc; }
""",
}


@needs_browser
@pytest.mark.parametrize("module_id", sorted(MODULE_FAKES))
def test_fakes_the_text_checks_accept_are_rejected_by_rendering(module_id):
    module = PRACTICE_MODULE_INDEX[module_id]
    files = dict(module["files"])
    files["styles.css"] = MODULE_FAKES[module_id]
    outcomes = run_static_checks(files, module["checks"])
    rendered = [
        o
        for c, o in zip(module["checks"], outcomes)
        if c["type"] in render_judge.RENDER_CHECK_TYPES
    ]
    text = [
        o
        for c, o in zip(module["checks"], outcomes)
        if c["type"] not in render_judge.RENDER_CHECK_TYPES
    ]
    # The fake is only interesting if it really does fool most of the text layer.
    assert sum(1 for o in text if o.passed) >= len(text) - 3, [
        o.id for o in text if not o.passed
    ]
    failed = [o for o in rendered if not o.passed]
    assert len(failed) >= 2, [(o.id, o.detail) for o in rendered]
    for outcome in failed:
        # Every rejection has to say what was observed, not just "failed".
        assert outcome.detail and len(outcome.detail) > 25, outcome.detail


@needs_browser
@pytest.mark.parametrize("module_id", RENDERED_MODULES)
def test_the_starter_files_fail_the_rendered_checks(module_id):
    """The starter must not be accepted — that would be the false pass again."""
    module = PRACTICE_MODULE_INDEX[module_id]
    outcomes = run_static_checks(dict(module["files"]), module["checks"])
    rendered = [
        o
        for c, o in zip(module["checks"], outcomes)
        if c["type"] in render_judge.RENDER_CHECK_TYPES
    ]
    assert any(not o.passed for o in rendered)
    assert all(o.detail for o in rendered), "a rendered verdict must always explain itself"
