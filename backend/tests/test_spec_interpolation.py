"""Template placeholders must never reach a selector engine.

The bug these cover: a re-sync script stored raw template checks, so a ticket's
selector stayed the literal string `#{entity}List` and the browser answered
`querySelectorAll('#{entity}List')` with "invalid selector" — a red check
against CSS that was correct.

Two halves, and both matter:

* interpolation happens on every write path, so a stored check says `#movieList`;
* if one ever leaks through anyway, it is reported as a *validator configuration
  error* rather than as the learner's failure.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.data.ticket_templates import TICKET_TEMPLATES
from app.models import Ticket
from app.services import render_judge, spec_interpolation
from app.services.spec_interpolation import (
    SpecInterpolationError,
    build_validation_spec,
    context_for,
    fill,
    unresolved_placeholders,
)
from app.services.validation_service import run_static_checks
from scripts.reset_false_pass import template_spec

BROWSER_AVAILABLE = render_judge.is_available()
needs_browser = pytest.mark.skipif(
    not BROWSER_AVAILABLE,
    reason="headless Chromium is not installed (`playwright install chromium`)",
)

# The live project MTB-4 belongs to.
MTB_TITLE = "Movie Ticket Booking System"
MTB_IDEA = "A movie ticket booking system where users browse movies and book seats"

#: A page shaped like the one the CSS tickets are graded against: the listing
#: container carries the real id the resolved selector must find.
PAGE = """<!DOCTYPE html>
<html lang="en">
  <head><link rel="stylesheet" href="styles.css" /></head>
  <body>
    <main id="app">
      <section id="movieList">
        <article class="card"><h2>One</h2></article>
        <article class="card"><h2>Two</h2></article>
        <article class="card"><h2>Three</h2></article>
        <article class="card"><h2>Four</h2></article>
      </section>
    </main>
  </body>
</html>
"""

CORRECT_CSS = """
body { margin: 0; }
#movieList {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
  padding: 24px;
}
.card { padding: 16px; background: #171a22; min-height: 80px; }
"""


def mtb_context() -> dict[str, str]:
    return context_for(MTB_IDEA, MTB_TITLE)


def css_layout_spec(context: dict[str, str]) -> dict:
    """The css_layout spec as the single interpolation path produces it."""
    return build_validation_spec(TICKET_TEMPLATES["css_layout"][0], context)


def grade(checks: list[dict], css: str = CORRECT_CSS) -> list:
    files = {"styles.css": css}
    return run_static_checks(files, checks, render_files={"index.html": PAGE})


def find(outcomes: list, check_id: str):
    return next(o for o in outcomes if o.id == check_id)


# -- 1. the resolution itself ------------------------------------------------


def test_mtb4_resolves_entity_placeholder_to_movie():
    spec = css_layout_spec(mtb_context())
    selectors = [c["selector"] for c in spec["checks"] if c.get("selector")]

    assert "#movieList" in selectors
    assert not any("{entity}" in s for s in selectors)
    assert unresolved_placeholders(spec) == []


# -- 2 & 3. the two checks that failed in production -------------------------


@needs_browser
def test_grid_computed_style_check_queries_the_resolved_selector():
    spec = css_layout_spec(mtb_context())
    outcome = find(grade(spec["checks"]), "list_grid_renders")

    assert outcome.passed, outcome.detail
    assert "movieList" in (outcome.detail or "")
    assert "invalid selector" not in (outcome.detail or "")


@needs_browser
def test_laptop_column_check_queries_the_resolved_selector():
    spec = css_layout_spec(mtb_context())
    outcome = find(grade(spec["checks"]), "list_columns_renders")

    assert outcome.passed, outcome.detail
    assert "invalid selector" not in (outcome.detail or "")


# -- 4. a different problem with a different entity --------------------------


def test_the_displayed_requirement_reads_the_resolved_selector():
    """What the learner reads names the same element the grader queries.

    The spec guard only covered checks, so a ticket could be stored asking the
    learner to "Make #{entity}List a grid" — unreadable, and no way to tell
    whether the grader agreed about which element was meant.
    """
    context = mtb_context()
    template = TICKET_TEMPLATES["css_layout"][0]
    requirements = fill(template["requirements"], context, strict=True)
    grid_requirement = next(r for r in requirements if "List" in r)

    assert "#movieList" in grid_requirement
    assert "{entity}" not in grid_requirement
    assert unresolved_placeholders(requirements) == []


def test_the_brief_and_the_validator_name_the_same_element():
    """One context feeds both, so the two can never drift apart."""
    context = mtb_context()
    template = TICKET_TEMPLATES["css_layout"][0]
    requirements = fill(template["requirements"], context, strict=True)
    selectors = [c["selector"] for c in css_layout_spec(context)["checks"] if c.get("selector")]

    assert "#movieList" in selectors
    assert any("#movieList" in r for r in requirements)


def test_storing_a_placeholder_bearing_brief_is_refused_at_write_time():
    ticket = Ticket()
    ticket.requirements = ["Make #movieList a grid"]

    for field in ("requirements", "acceptance_criteria"):
        with pytest.raises(spec_interpolation.SpecInterpolationError) as exc:
            setattr(ticket, field, ["Make #{entity}List a grid"])
        assert "entity" in str(exc.value)


def test_a_different_project_resolves_to_its_own_entity():
    recipes = context_for("A manager for my recipes and shopping lists", "Recipe Manager")
    spec = css_layout_spec(recipes)

    assert recipes["entity"] == "recipe"
    assert "#recipeList" in [c["selector"] for c in spec["checks"] if c.get("selector")]
    assert unresolved_placeholders(spec) == []


# -- 5. a leak is a configuration error, not a student failure ---------------


def test_unresolved_placeholder_is_a_configuration_error_not_a_failure():
    leaked = [
        {
            "id": "leaked",
            "type": "render_computed_style",
            "file": "styles.css",
            "selector": "#{entity}List",
            "property": "display",
            "value_pattern": "grid",
            "label": "The listing renders as a grid container",
            "requirement_index": 0,
        }
    ]
    outcome = find(grade(leaked), "leaked")

    # Unmistakably ours: flagged, explained as a configuration error, and told
    # not to be the learner's fault.
    assert outcome.config_error is True
    assert "validator configuration error" in (outcome.detail or "")
    assert "not in your code" in (outcome.hint or "")
    # And it cannot mark a requirement unmet or enter the met/total ratio.
    assert outcome.precondition is True
    assert outcome.requirement_index is None
    assert outcome.requirement_indexes is None
    # Still fails closed: a check that examined nothing never credits anything.
    assert outcome.passed is False


def test_textual_selector_checks_are_guarded_too():
    """The guard is not render-only: `query` and `css_has_property` are covered."""
    leaked = [
        {
            "id": "leaked_html",
            "type": "html_element",
            "file": "index.html",
            "selector": "section#{entity}List",
            "label": "<section> exists",
        },
        {
            "id": "leaked_css",
            "type": "css_property",
            "file": "styles.css",
            "selector": "#{entity}List",
            "property": "display",
            "label": "display declared",
        },
    ]
    outcomes = run_static_checks({"index.html": PAGE, "styles.css": CORRECT_CSS}, leaked)

    assert [o.config_error for o in outcomes] == [True, True]
    assert all(o.passed is False for o in outcomes)


def test_a_resolved_selector_is_not_flagged_as_a_configuration_error():
    spec = css_layout_spec(mtb_context())
    outcomes = grade(spec["checks"])

    assert not [o.id for o in outcomes if o.config_error]


# -- 6. the rest of the suite still works ------------------------------------


@needs_browser
def test_gap_and_render_checks_still_pass_after_resolution():
    spec = css_layout_spec(mtb_context())
    outcomes = grade(spec["checks"])
    gap = find(outcomes, "list_gap_renders")

    assert gap.passed, gap.detail
    # Scoped to selector health on purpose. `CORRECT_CSS` is a minimal fixture
    # that proves the grid resolves and renders; it does not attempt the card
    # styling the template also demands, so asserting every check passes would
    # make this test fail whenever the template gets stricter — which says
    # nothing about interpolation.
    broken_selectors = [
        (o.id, o.detail)
        for o in outcomes
        if not o.passed
        and (
            "invalid selector" in (o.detail or "")
            # A regex check's detail legitimately contains braces, so look for
            # the placeholder vocabulary rather than for any brace at all.
            or unresolved_placeholders(o.detail or "")
        )
    ]
    assert not broken_selectors, broken_selectors


# -- 7. the regression that actually caused this -----------------------------


def _fake_ticket(skill: str, title: str, idea: str, files: dict[str, str]) -> SimpleNamespace:
    """Just enough ticket for the script path, without touching the database."""
    project = SimpleNamespace(title=title, idea=idea)
    return SimpleNamespace(
        target_skill_id=skill,
        starter_files=files,
        validation_spec={},
        sprint=SimpleNamespace(project=project),
    )


@pytest.mark.parametrize("skill", sorted(TICKET_TEMPLATES))
def test_the_script_write_path_never_stores_a_placeholder(skill: str):
    """A ticket written through `scripts/` carries no placeholder in any check field.

    `template_spec` used to return the template's checks verbatim, which is how
    `#{entity}List` reached the database. It now goes through the one
    interpolation path, so this holds for every skill — not only the CSS ones.
    """
    ticket = _fake_ticket(skill, MTB_TITLE, MTB_IDEA, {})
    spec = template_spec(ticket)

    assert spec is not None
    assert unresolved_placeholders(spec) == []
    for check in spec["checks"]:
        for field, value in check.items():
            if isinstance(value, str):
                assert "{entity}" not in value and "{domain}" not in value, (skill, field)


@pytest.mark.parametrize("skill", sorted(TICKET_TEMPLATES))
def test_every_template_brief_resolves_for_every_skill(skill: str):
    """Configuration validation: no template can publish a brief it cannot resolve.

    A placeholder outside the known vocabulary would survive `fill` and reach
    the learner as literal `{...}`, so strict mode has to hold for the brief of
    every template, not just the ones a project happens to schedule.
    """
    context = mtb_context()

    for template in TICKET_TEMPLATES[skill]:
        for field in ("title", "description", "requirements", "acceptance_criteria"):
            resolved = fill(template.get(field) or [], context, strict=True)
            assert unresolved_placeholders(resolved) == [], (skill, field)


def test_storing_a_placeholder_bearing_spec_is_refused_at_write_time():
    """`str.format` failing silently is what let this survive; this fails loudly."""
    ticket = Ticket()

    with pytest.raises(SpecInterpolationError) as exc:
        ticket.validation_spec = {"checks": [{"id": "x", "selector": "#{entity}List"}]}
    assert "entity" in str(exc.value)

    ticket.validation_spec = {"checks": [{"id": "x", "selector": "#movieList"}]}
    assert ticket.validation_spec["checks"][0]["selector"] == "#movieList"


def test_strict_fill_refuses_a_context_missing_a_key():
    with pytest.raises(SpecInterpolationError):
        spec_interpolation.fill("#{entity}List", {"domain": "D"}, strict=True)


def test_interpolation_leaves_code_braces_alone():
    """JSX and template literals are not placeholders and must survive intact."""
    context = mtb_context()
    jsx = '<Card key={item.id} item={item} /> in the {entity} list'
    filled = spec_interpolation.fill(jsx, context)

    assert filled == '<Card key={item.id} item={item} /> in the movie list'
