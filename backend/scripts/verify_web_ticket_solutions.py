"""Prove the web ticket templates are both passable and not fakeable.

Project ticket templates shipped no reference solution, so nothing ever proved
that a correct implementation satisfies their checks — only that a bad one
fails. This script closes both halves for every web template that carries
`solution_files`:

  * the reference solution must pass EVERY check (a check that stops matching
    its own solution is a failure here, not a silent skip), and
  * a set of deliberately fake/incomplete submissions must FAIL, each on the
    checks it is designed to defeat (empty values, commented-out rules,
    `<img src="" alt="">`, selectors that merely contain the target substring).

It also renders the reference solution through the real preview assembler and
asserts the finished page contains the nav, the headline and the <img>.

    cd backend && PYTHONPATH=. .venv/bin/python scripts/verify_web_ticket_solutions.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio

from app.data.ticket_templates import (
    API_CLIENT_SOLUTION,
    CSS_CARD_GRID_SOLUTION,
    CSS_RESPONSIVE_SOLUTION,
    CSS_TOKENS_SOLUTION,
    HTML_NAVIGATION_SOLUTION,
    HTML_STRUCTURE_SOLUTION,
    JS_ASYNC_SOLUTION,
    JS_BASICS_SOLUTION,
    JS_FUNCTIONS_SOLUTION,
    JS_RENDER_LIST_SOLUTION,
    JS_RESILIENT_SOLUTION,
    JS_SELECTION_SOLUTION,
    REACT_COMPONENTS_SOLUTION,
    REACT_FETCH_SOLUTION,
    REACT_STATE_SOLUTION,
    STARTER_FILES,
    TICKET_TEMPLATES,
)
from app.services import render_judge
from app.services.sprint_generator import _fill
from app.services.validation_service import run_behaviour_tests, run_static_checks

CONTEXT = {
    "domain": "Movie Ticket Booking System",
    "entity": "movie",
    "entity_plural": "movies",
}


def fill(text: str) -> str:
    """Placeholder substitution for solution files.

    `_fill` is used for the checks (exactly as the generator does it), but a
    solution file contains literal braces, which `str.format` would choke on.
    """
    for key, value in CONTEXT.items():
        text = text.replace("{" + key + "}", value)
    return text


# The other files a ticket's grader may see. Only the ticket's own file is ever
# the one under test; the rest is the project state that ticket builds on.
BASE_FILES = {
    "index.html": fill(HTML_NAVIGATION_SOLUTION),
    "styles.css": fill(CSS_RESPONSIVE_SOLUTION),
    "script.js": fill(JS_RENDER_LIST_SOLUTION),
}


def grade(template: dict[str, Any], files: dict[str, str]) -> list[dict[str, Any]]:
    checks = _fill(template["checks"], CONTEXT)
    return [o.to_dict() for o in run_static_checks({**BASE_FILES, **files}, checks)]


def failures(outcomes: list[dict[str, Any]]) -> list[str]:
    return [o["id"] for o in outcomes if not o["passed"]]


def grade_behaviour(template: dict[str, Any], source: str) -> list[dict[str, Any]]:
    """Run the template's layer-2 scenarios against a submission."""
    spec = template.get("behaviour") or {}
    if not spec.get("assertions"):
        return []
    return [
        outcome.to_dict()
        for outcome in asyncio.run(
            run_behaviour_tests(
                source,
                spec["assertions"],
                spec.get("prelude", ""),
                spec.get("wrap_as"),
            )
        )
    ]


# ---------------------------------------------------------------------------
# Deliberately broken submissions. Each names the check ids it must break.
# ---------------------------------------------------------------------------

HTML_NO_HERO = fill(
    HTML_STRUCTURE_SOLUTION.replace(
        """      <section id="hero">
        <h2>Tonight's {entity_plural}, booked in seconds</h2>
        <p>Browse what is showing near you and pick your seats without queueing.</p>
        <img
          src="https://picsum.photos/seed/{entity}-hero/1200/500"
          alt="Audience seated in a cinema before the film starts"
        />
      </section>
""",
        "",
    )
)

HTML_EMPTY_IMG = fill(HTML_STRUCTURE_SOLUTION).replace(
    'src="https://picsum.photos/seed/movie-hero/1200/500"\n          '
    'alt="Audience seated in a cinema before the film starts"',
    'src="" alt=""',
)

HTML_ALT_ONE_WORD = fill(HTML_STRUCTURE_SOLUTION).replace(
    'alt="Audience seated in a cinema before the film starts"', 'alt="img"'
)

HTML_COMMENTED_HERO = fill(HTML_STRUCTURE_SOLUTION).replace(
    '<section id="hero">', '<!-- <section id="hero">'
).replace("</section>\n      <section", "</section> -->\n      <section")

CSS_BODY_ONLY = """:root {
  --surface: #10131a;
  --text: #f2f4f8;
  --muted: #a5aec0;
  --accent: #ff5c7a;
}

body {
  margin: 0;
  background-color: var(--surface);
  color: var(--text);
  font-family: system-ui, sans-serif;
  line-height: 1.6;
}
"""

# Every value the ticket pins to a range, pushed to the value that declares the
# property while applying nothing: zero padding, zero gap, body-sized display
# type, an unrounded banner and a shadow of no size.
CSS_EMPTY_VALUES = (
    CSS_TOKENS_SOLUTION.replace("padding: 18px 32px;", "padding: 0;")
    .replace("gap: 26px;", "gap: 0;")
    .replace("font-size: clamp(2rem, 4vw, 3rem);", "font-size: 1rem;")
    .replace("font-size: 1.375rem;", "font-size: 2.5rem;")
    .replace("max-width: 56ch;", "max-width: none;")
    .replace("border-radius: var(--radius);\n  box-shadow", "border-radius: 2px;\n  box-shadow")
    .replace("aspect-ratio: 16 / 6;", "")
)

# The tokens are referenced, but every reference is misspelled. Textually this
# stylesheet is indistinguishable from a correct one; rendered, it paints
# nothing at all. This is the case only the render judge can catch.
CSS_TYPO_TOKENS = CSS_TOKENS_SOLUTION.replace("var(--surface)", "var(--surfcae)").replace(
    "var(--font-sans)", "var(--font-sanz)"
)

CSS_COMMENTED_OUT = CSS_BODY_ONLY + """
/*
header { padding: 18px 32px; background-color: #191d27; border-bottom: 1px solid #262c3a;
  display: flex; justify-content: space-between; }
header h1 { font-size: 1.375rem; }
nav ul { display: flex; gap: 24px; list-style: none; padding: 0; }
nav a { color: #a5aec0; text-decoration: none; }
nav a:hover { color: #ff5c7a; }
nav a:focus-visible { outline: 2px solid #ff5c7a; }
#hero { padding: 40px; }
#hero h2 { font-size: 2.5rem; }
#hero p { max-width: 56ch; margin: 0 auto; }
#hero img { max-width: 100%; height: auto; aspect-ratio: 16 / 6; object-fit: cover;
  border-radius: 14px; }
*/
"""

# `.header-note` and `.navigations ul.navbar` merely *contain* the substrings a
# naive check would look for, and none of these selectors match a real element.
CSS_LOOKALIKE_SELECTORS = CSS_BODY_ONLY + """
.header-note {
  padding: 18px 32px;
  background-color: #191d27;
  border-bottom: 1px solid #262c3a;
  display: flex;
  justify-content: space-between;
}

.header-note h1 {
  font-size: 1.375rem;
}

.navigations ul.navbar {
  display: flex;
  gap: 24px;
  list-style: none;
  padding: 0;
}

.navigations a.navlink {
  color: #a5aec0;
  text-decoration: none;
}

.navigations a.navlink:hover {
  color: #ff5c7a;
}

.navigations a.navlink:focus-visible {
  outline: 2px solid #ff5c7a;
}

#hero-teaser {
  padding: 40px;
}

#hero-teaser h2 {
  font-size: 2.5rem;
}

#hero-teaser p {
  max-width: 56ch;
  margin: 0 auto;
}

#hero-teaser img {
  max-width: 100%;
  aspect-ratio: 16 / 6;
  object-fit: cover;
  border-radius: 14px;
}
"""

CSS_GRID_NO_POSTER = fill(
    CSS_CARD_GRID_SOLUTION.replace(
        """
.card img {
  display: block;
  width: 100%;
  aspect-ratio: 2 / 3;
  height: auto;
  object-fit: cover;
  border-radius: var(--radius-sm);
}
""",
        "",
    )
)

CSS_GRID_STRETCHED_POSTER = fill(CSS_CARD_GRID_SOLUTION).replace(
    "  aspect-ratio: 2 / 3;\n  height: auto;\n  object-fit: cover;\n", "  height: auto;\n"
)

# A grid, but with hand-written fixed tracks and a flat card: the "before"
# picture the styling tickets exist to replace.
CSS_GRID_FLAT_CARDS = fill(
    CSS_TOKENS_SOLUTION
    + """
#{entity}List {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.card {
  padding: 4px;
}

.card img {
  width: 100%;
}

.card:hover {
  color: var(--accent);
}
"""
)

# Responsive in name only: one media query that changes nothing structural, no
# capped content column, and display type that never scales down.
CSS_RESPONSIVE_TOKEN_EFFORT = fill(
    CSS_CARD_GRID_SOLUTION.replace("font-size: clamp(2rem, 4vw, 3rem);", "font-size: 3rem;")
    + """
@media (max-width: 640px) {
  header {
    padding: 14px 20px;
  }
}
"""
)

JS_NO_POSTER = """const container = document.getElementById("movieList");
const movies = [{ id: 1, title: "Interstellar", price: 320 }];
container.innerHTML = movies
  .map((item) => `<article class="card"><h3>${item.title}</h3></article>`)
  .join("");
"""

JS_EMPTY_ALT = fill(JS_RENDER_LIST_SOLUTION).replace(
    'alt="Poster for ${item.title}"', 'alt=""'
)

JS_HARDCODED_POSTER = fill(JS_RENDER_LIST_SOLUTION).replace(
    "${item.poster}", "https://example.com/one.jpg"
)

#: The stylesheet a learner is handed. It scaffolds the section order and names
#: the token roles, and it must satisfy nothing at all: a ticket that passed on
#: an untouched starter file is the exact failure this file exists to prevent.
STARTER_CSS = fill(STARTER_FILES["styles.css"].format(**CONTEXT))

#: Every check in the foundation ticket that grades work beyond `:root` and
#: `body` — i.e. what must fail whenever the header, nav and hero were never
#: touched, however plausible the stylesheet looks.
CSS_BASICS_NOTHING_STYLED = [
    "h1_size", "h1_scale_renders", "hero_headline", "hero_headline_renders",
    "header_padding", "header_background", "header_edge", "header_row_renders",
    "nav_horizontal", "nav_gap", "nav_markers", "nav_row_renders",
    "nav_link_color", "nav_link_underline", "nav_link_not_blue",
    "nav_link_hover", "nav_link_focus",
    "hero_padding", "tagline_measure", "tagline_measure_renders",
    "tagline_centred_renders",
    "banner_fluid_width", "banner_aspect", "banner_fit", "banner_radius",
    "banner_box_renders", "token_reuse",
    "footer_padding", "footer_border", "footer_muted",
]

#: The script.js a learner is handed: sample data and nothing else. Every
#: graded check on every JS ticket must fail against it.
STARTER_JS = fill(STARTER_FILES["script.js"].format(**CONTEXT))
STARTER_JSX = STARTER_FILES["App.jsx"]

# --- js_basics -------------------------------------------------------------

# The functions exist and the file parses, but every body is a constant. This
# is what a learner writes when they are trying to satisfy a name-matching
# grader rather than the requirement.
JS_BASICS_STUBS = """function formatPrice(value) {
  return "Rs 0";
}

function formatRating(value) {
  return "0/10";
}

function formatMeta(item) {
  return "";
}

function truncate(text, limit) {
  return "";
}
"""

# Correct output, written the 2005 way: var, string concatenation and ==.
JS_BASICS_LEGACY_STYLE = """var CURRENCY = "Rs";

function formatPrice(value) {
  var amount = Number(value);
  if (amount != amount) {
    return CURRENCY + " --";
  }
  return CURRENCY + " " + amount.toFixed(0);
}

function formatRating(value) {
  var rating = Number(value);
  if (rating == undefined) {
    return "Not rated";
  }
  return rating.toFixed(1) + "/10";
}

function formatMeta(item) {
  return item.genre + " - " + formatRating(item.rating);
}

function truncate(text, limit) {
  var value = String(text);
  if (value.length <= limit) {
    return value;
  }
  return value.slice(0, limit - 1) + "...";
}
"""

# --- js_functions ----------------------------------------------------------

# Right answers, wrong ownership: sortByRating reorders the caller's array.
JS_FUNCTIONS_MUTATING = """function filterByGenre(items, genre) {
  if (!genre || genre === "all") {
    return items;
  }
  return items.filter((item) => item.genre === genre);
}

function sortByRating(items) {
  return items.sort((a, b) => b.rating - a.rating);
}

function summarise(items) {
  const total = items.reduce((sum, item) => sum + Number(item.rating), 0);
  return `${items.length} results \\u00b7 avg ${(total / items.length).toFixed(1)}`;
}
"""

# --- js_dom / selection-state ----------------------------------------------

# One listener per card, no closest(), no aria, no summary: the version that
# works once and breaks the first time the list re-renders.
JS_SELECTION_PER_CARD = fill(
    JS_RENDER_LIST_SOLUTION
    + """
const state = { selected: null };

document.querySelectorAll(".card").forEach((card) => {
  card.addEventListener("click", () => {
    card.classList.add("selected");
    state.selected = card;
  });
});
"""
)

# --- js_async --------------------------------------------------------------

# Awaits correctly and renders correctly, but the user stares at an empty
# container until the response lands, and an empty response renders nothing.
JS_ASYNC_NO_STATES = fill(
    """const container = document.getElementById("{entity}List");

async function loadItems() {
  const response = await fetch("/api/{entity_plural}");
  const items = await response.json();
  container.innerHTML = items.map((item) => `<article class="card"><h3>${item.title}</h3></article>`).join("");
}

loadItems();
"""
)

# --- api_integration -------------------------------------------------------

# The client the requirement-mapping test was written against: correct on the
# status check, but it hard-codes its URL, exposes one function and renders.
API_CLIENT_MONOLITH = """async function loadMovies() {
  try {
    const response = await fetch("/api/movies");
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    const movies = await response.json();
    document.getElementById("movieList").innerHTML = movies.length;
    return movies;
  } catch (error) {
    console.error(error);
    throw error;
  }
}
"""

# --- React -----------------------------------------------------------------

# JSX that renders: div soup, `class`, an index key and a hard-coded poster.
REACT_DIV_SOUP = """import React from "react";

const items = [{ id: 1, title: "Interstellar", genre: "Sci-fi", rating: 8.6, price: 320 }];

export default function App() {
  return (
    <div>
      <div class="list">
        {items.map((item, index) => (
          <div key={index}>
            <img src="https://example.com/one.jpg" alt="Poster">
            <div>{item.title}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
"""

# useState is called, but the array is pushed into and the card reaches into
# the DOM to highlight itself — the two mistakes React exists to prevent.
REACT_STATE_MUTATING = """import React, { useState } from "react";

const items = [{ id: 1, title: "Interstellar", price: 320 }];

function Card({ item, onSelect }) {
  return (
    <article className="card" onClick={() => onSelect(item)}>
      <h3>{item.title}</h3>
    </article>
  );
}

export default function App() {
  const [selected, setSelected] = useState(null);
  const [seats, setSeats] = useState([]);

  function handleSelect(item) {
    setSelected(item);
    seats.push(1);
    setSeats(seats);
    document.querySelector(".card").classList.add("card--selected");
  }

  return (
    <main id="app">
      <section id="movieList">
        {items.map((item) => (
          <Card key={item.id} item={item} onSelect={handleSelect} />
        ))}
      </section>
    </main>
  );
}
"""

# Fetches in an effect and renders the happy path. No cleanup, no status check,
# no error, no empty state — the component that works on a fast connection.
REACT_FETCH_HAPPY_PATH = """import React, { useEffect, useState } from "react";

export default function App() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    fetch("/api/movies")
      .then((response) => response.json())
      .then((data) => setItems(data));
  }, []);

  return (
    <main id="app">
      <section id="movieList" className="listing">
        {items.map((item) => (
          <article className="card" key={item.id}>
            <img className="card__poster" src={item.poster} alt={`Poster for ${item.title}`} />
            <h3>{item.title}</h3>
          </article>
        ))}
      </section>
    </main>
  );
}
"""

CASES: list[tuple[str, str, dict[str, str], list[str]]] = [
    # (template key, label, files under test, check ids that must fail)
    ("html_basics", "hero region deleted", {"index.html": HTML_NO_HERO},
     ["hero", "hero_in_main", "hero_headline", "hero_tagline", "hero_image", "hero_image_real"]),
    ("html_basics", 'img src="" alt=""', {"index.html": HTML_EMPTY_IMG},
     ["hero_image", "hero_image_real"]),
    ("html_basics", 'alt="img" (not descriptive)', {"index.html": HTML_ALT_ONE_WORD},
     ["hero_image_real"]),
    ("html_basics", "hero commented out", {"index.html": HTML_COMMENTED_HERO},
     ["hero", "hero_in_main", "hero_headline", "hero_tagline", "hero_image", "hero_image_real"]),
    ("css_basics", "body-only stylesheet (the black screen)", {"styles.css": CSS_BODY_ONLY},
     CSS_BASICS_NOTHING_STYLED),
    ("css_basics", "zeroed / body-sized values", {"styles.css": CSS_EMPTY_VALUES},
     ["banner_aspect", "banner_box_renders", "banner_radius", "h1_scale_renders",
      "header_padding", "hero_headline", "hero_headline_renders", "nav_gap",
      "tagline_measure", "tagline_measure_renders", "tagline_centred_renders"]),
    # The whole reason the render judge is worth its cost: textually this file is
    # the reference solution.
    ("css_basics", "tokens referenced but misspelled", {"styles.css": CSS_TYPO_TOKENS},
     ["body_font_renders", "body_paints"]),
    ("css_basics", "every rule commented out", {"styles.css": CSS_COMMENTED_OUT},
     CSS_BASICS_NOTHING_STYLED),
    ("css_basics", "lookalike selectors (.header-note, #hero-teaser)",
     {"styles.css": CSS_LOOKALIKE_SELECTORS},
     CSS_BASICS_NOTHING_STYLED),
    ("css_basics", "untouched starter stylesheet", {"styles.css": STARTER_CSS},
     CSS_BASICS_NOTHING_STYLED + [
         "root_tokens", "body_bg", "body_color", "body_uses_tokens", "body_margin",
         "body_paints", "font", "body_line_height", "body_font_renders",
     ]),
    ("css_layout", "no poster rules", {"styles.css": CSS_GRID_NO_POSTER},
     ["poster_width", "poster_aspect", "poster_fit", "poster_radius"]),
    ("css_layout", "poster left to stretch", {"styles.css": CSS_GRID_STRETCHED_POSTER},
     ["poster_aspect", "poster_fit"]),
    ("css_layout", "fixed tracks, flat cards", {"styles.css": CSS_GRID_FLAT_CARDS},
     ["grid_auto_tracks", "list_padding", "gap", "list_gap_renders", "card_surface",
      "card_border", "card_radius", "card_padding", "card_shadow", "card_flow", "card_gap",
      "card_title_size", "card_title_margin", "card_meta_color", "poster_aspect",
      "poster_fit", "poster_radius", "card_transition", "card_hover_lift"]),
    ("css_layout", "untouched starter stylesheet", {"styles.css": STARTER_CSS},
     [check["id"] for check in TICKET_TEMPLATES["css_layout"][0]["checks"]]),
    ("css_responsive", "one cosmetic media query", {"styles.css": CSS_RESPONSIVE_TOKEN_EFFORT},
     ["container_cap", "container_centre", "main_cap_renders", "main_centred_renders",
      "single_column", "headline_phone_renders"]),
    ("css_responsive", "untouched starter stylesheet", {"styles.css": STARTER_CSS},
     ["container_cap", "container_centre", "main_cap_renders", "main_centred_renders",
      "banner_fits_renders",
      "media", "single_column", "one_column_renders", "wide_columns_renders",
      "headline_wide_renders"]),
    ("js_dom", "text-only cards", {"script.js": JS_NO_POSTER},
     ["poster_element", "poster_from_data", "poster_alt"]),
    ("js_dom", 'alt="" on the poster', {"script.js": JS_EMPTY_ALT}, ["poster_alt"]),
    ("js_dom", "one hard-coded poster for every card", {"script.js": JS_HARDCODED_POSTER},
     ["poster_from_data"]),
]

#: Cases for the templates added/modernised in this pass. Kept in a second list
#: so the index of each case is (template key, slug) rather than "the first
#: template under this key" — several keys now ship more than one ticket.
SLUG_CASES: list[tuple[str, str, str, dict[str, str], list[str]]] = [
    # (template key, slug, label, files under test, check ids that must fail)
    ("js_basics", "format-helpers", "untouched starter script.js", {"script.js": STARTER_JS},
     ["format_price_real", "template_literal", "format_rating_real", "format_meta_real",
      "truncate_real"]),
    ("js_basics", "format-helpers", "named stubs returning constants",
     {"script.js": JS_BASICS_STUBS},
     ["format_price_real", "template_literal", "format_rating_real", "format_meta_real",
      "truncate_real"]),
    ("js_basics", "format-helpers", "var, string concatenation and ==",
     {"script.js": JS_BASICS_LEGACY_STYLE}, ["template_literal", "no_var", "strict_equality"]),
    ("js_functions", "list-operations", "untouched starter script.js", {"script.js": STARTER_JS},
     ["filter_real", "sort_real", "summarise_real", "uses_filter", "uses_reduce"]),
    ("js_functions", "list-operations", "sorts the caller's array in place",
     {"script.js": JS_FUNCTIONS_MUTATING}, ["no_mutation"]),
    ("js_dom", "selection-state", "a listener per card, no delegation",
     {"script.js": JS_SELECTION_PER_CARD},
     ["no_per_card_listeners", "uses_closest", "guards_missed_clicks", "reads_data_id",
      "looks_item_up", "clears_previous", "aria_pressed", "live_region",
      "summary_empty_state"]),
    ("js_async", "load-data", "no loading state, no empty state",
     {"script.js": JS_ASYNC_NO_STATES},
     ["loading_sequence", "empty_state", "empty_state_message"]),
    ("api_integration", "api-client", "one monolithic function that renders",
     {"script.js": API_CLIENT_MONOLITH},
     ["base_url", "endpoint_functions", "detail_endpoint", "no_dom"]),
    ("react_fundamentals", "react-components", "div soup with class and an index key",
     {"App.jsx": REACT_DIV_SOUP},
     ["syntax", "card_component", "card_takes_props", "card_rendered", "key_from_id",
      "no_index_key", "main_landmark", "listing_section", "card_article", "card_heading",
      "poster_img", "poster_alt", "uses_classname", "void_elements_closed"]),
    ("react_state", "react-state", "pushes into state and reaches into the DOM",
     {"App.jsx": REACT_STATE_MUTATING},
     ["selection_prop", "no_mutation", "updater_form", "spread_update", "conditional_class",
      "no_classlist", "aria_pressed", "summary_live", "summary_conditional"]),
    ("react_fundamentals", "react-components", "untouched starter App.jsx",
     {"App.jsx": STARTER_JSX},
     [c["id"] for c in TICKET_TEMPLATES["react_fundamentals"][0]["checks"]
      if not c.get("precondition") and c["type"] != "not_regex"]),
    ("react_data_fetching", "react-fetching", "happy path only, no cleanup",
     {"App.jsx": REACT_FETCH_HAPPY_PATH},
     ["loading_state", "error_state", "ok_before_parse", "try_catch", "catch_handles",
      "cleanup", "abort_controller", "abort_signal_passed", "abort_ignored", "loading_ui",
      "error_ui", "loading_status_role", "empty_state", "empty_message"]),
]


def template_for(skill: str, slug: str) -> dict[str, Any]:
    return next(t for t in TICKET_TEMPLATES[skill] if t["slug"] == slug)


def main() -> int:
    problems: list[str] = []

    print("=" * 74)
    print("1. Reference solutions must pass every check")
    print("=" * 74)
    for skill, templates in TICKET_TEMPLATES.items():
        for template in templates:
            solution = template.get("solution_files")
            if not solution:
                continue
            files = {name: fill(body) for name, body in solution.items()}
            outcomes = grade(template, files)
            bad = failures(outcomes)
            status = "PASS" if not bad and outcomes else "FAIL"
            print(f"  [{status}] {skill}/{template['slug']}: {len(outcomes)} checks, "
                  f"{len(outcomes) - len(bad)} passed")
            if bad:
                for outcome in outcomes:
                    if not outcome["passed"]:
                        print(f"         - {outcome['id']}: {outcome['detail']}")
                problems.append(f"{skill}/{template['slug']} solution failed: {bad}")

    print()
    print("=" * 74)
    print("2. Fake / incomplete submissions must fail the checks they defeat")
    print("=" * 74)
    for skill, label, files, must_fail in CASES:
        template = TICKET_TEMPLATES[skill][0]
        outcomes = grade(template, files)
        failed = set(failures(outcomes))
        missing = [cid for cid in must_fail if cid not in failed]
        unexpected = sorted(failed - set(must_fail))
        ok = not missing and not unexpected
        print(f"  [{'PASS' if ok else 'FAIL'}] {skill}: {label} — "
              f"{len(failed)}/{len(outcomes)} checks failed as designed")
        if missing:
            print(f"         false pass: {missing} should have failed")
            problems.append(f"{skill}/{label}: {missing} did not fail")
        if unexpected:
            print(f"         collateral: {unexpected} failed but were not targeted")
            problems.append(f"{skill}/{label}: unexpected failures {unexpected}")

    for skill, slug, label, files, must_fail in SLUG_CASES:
        template = template_for(skill, slug)
        outcomes = grade(template, files)
        failed = set(failures(outcomes))
        missing = [cid for cid in must_fail if cid not in failed]
        unexpected = sorted(failed - set(must_fail))
        ok = not missing and not unexpected
        print(f"  [{'PASS' if ok else 'FAIL'}] {skill}/{slug}: {label} — "
              f"{len(failed)}/{len(outcomes)} checks failed as designed")
        if missing:
            print(f"         false pass: {missing} should have failed")
            problems.append(f"{skill}/{slug} ({label}): {missing} did not fail")
        if unexpected:
            print(f"         collateral: {unexpected} failed but were not targeted")
            problems.append(f"{skill}/{slug} ({label}): unexpected failures {unexpected}")

    print()
    print("=" * 74)
    print("2b. Layer-2 behaviour: the reference solution must satisfy every scenario")
    print("=" * 74)
    for skill, templates in TICKET_TEMPLATES.items():
        for template in templates:
            solution = template.get("solution_files")
            if not solution or not (template.get("behaviour") or {}).get("assertions"):
                continue
            code_file = (template["behaviour"].get("file")) or "script.js"
            source = fill(solution.get(code_file, ""))
            outcomes = grade_behaviour(template, source)
            bad = failures(outcomes)
            status = "PASS" if outcomes and not bad else "FAIL"
            print(f"  [{status}] {skill}/{template['slug']}: {len(outcomes)} scenarios, "
                  f"{len(outcomes) - len(bad)} passed")
            for outcome in outcomes:
                if not outcome["passed"]:
                    print(f"         - {outcome['id']}: {outcome['detail']}")
            if bad or not outcomes:
                problems.append(f"{skill}/{template['slug']} behaviour failed: {bad}")

    # The behaviour scenarios are the only defence against a formatter that
    # returns a plausible-looking constant, so prove they bite.
    BEHAVIOUR_CASES = [
        ("js_basics", "format-helpers", "constant stubs", JS_BASICS_STUBS),
        ("js_functions", "list-operations", "in-place sort", JS_FUNCTIONS_MUTATING),
    ]
    for skill, slug, label, source in BEHAVIOUR_CASES:
        template = template_for(skill, slug)
        outcomes = grade_behaviour(template, source)
        bad = failures(outcomes)
        print(f"  [{'PASS' if bad else 'FAIL'}] {skill}/{slug}: {label} — "
              f"{len(bad)}/{len(outcomes)} scenarios failed")
        for outcome in outcomes:
            if not outcome["passed"]:
                print(f"         - {outcome['id']}: {outcome['detail']}")
        if not bad:
            problems.append(f"{skill}/{slug} ({label}): every behaviour scenario passed")

    print()
    print("=" * 74)
    print("3. Render proof — the assembled page a learner actually sees")
    print("=" * 74)
    page = render_judge.assemble_page(BASE_FILES, "index.html")
    markers = {
        "<nav": "<nav" in page,
        'aria-label="Primary"': 'aria-label="Primary"' in page,
        "<h1> product name": "Movie Ticket Booking System" in page,
        "hero <h2> headline": "booked in seconds" in page,
        "banner <img>": "picsum.photos/seed/movie-hero" in page,
        "poster <img> in script": "picsum.photos/seed/movie-1" in page,
        "nav styled horizontally": "display: flex" in page,
        "design tokens in :root": "--surface:" in page and "--accent:" in page,
        "components read the tokens": page.count("var(--") > 10,
        "grid tracks follow the width": "repeat(auto-fill, minmax(" in page,
        "posters cropped to one shape": "aspect-ratio: 2 / 3" in page,
        "cards have a shadow": "box-shadow" in page,
        "hover eases rather than snaps": "transition:" in page,
        "footer closes the page": "border-top" in page,
        "phone breakpoint present": "@media (max-width: 640px)" in page,
    }
    for name, found in markers.items():
        print(f"  [{'PASS' if found else 'FAIL'}] {name}")
        if not found:
            problems.append(f"render proof: {name} missing from the assembled page")
    print(f"  assembled document: {len(page)} characters")

    print()
    if problems:
        print(f"FAILED — {len(problems)} problem(s):")
        for problem in problems:
            print(f"  * {problem}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
