"""Engineering-ticket templates keyed by knowledge-graph skill.

The sprint generator picks templates for the skills implied by the learner's
tech stack, then contextualises them with the project domain. Every template
ships a deterministic `validation_spec` so a ticket can never be marked Done by
clicking a button — the submitted code has to satisfy real checks.

Placeholders: {domain} project title, {entity} primary domain noun,
{entity_plural} its plural form.
"""

from __future__ import annotations

from typing import Any

from app.data.ticket_templates_data import (
    DATA_SPRINT_THEMES,
    DATA_STARTER_FILES,
    DATA_TICKET_TEMPLATES,
)

#: A declared value that actually applies something. The CSS-wide keywords are
#: the only way to satisfy a `css_property` check without styling anything.
_REAL_VALUE = r"^(?!(?:inherit|initial|unset|revert|revert-layer)$).+"

# ---------------------------------------------------------------------------
# Pattern vocabulary for the web (HTML/CSS) tickets.
#
# `regex` checks run against the file with comments stripped, so a
# commented-out rule can never satisfy one. The helpers below add the two other
# defences the old checks lacked:
#   * `_rule` ties a declaration to a selector *inside the same block* — the
#     `[^{}]*` fences never cross a brace — so declaring `padding` on an
#     unrelated rule cannot satisfy a check aimed at `header`.
#   * every value is pinned to a range or a real-token pattern, so `padding: 0`,
#     `gap: 0` or an empty value fails.
# ---------------------------------------------------------------------------

#: An identifier boundary on both sides: `.card` is not satisfied by `.card-top`,
#: and the bare element `a` is not satisfied by `.avatar`.
_BOUND = r"(?![\w-])"


def _decl(prop: str, value: str = r"[^;}]*\S") -> str:
    """`prop: value`, guarded so `color` is not matched by `background-color`."""
    return r"(?<![\w-])" + prop + r"\s*:\s*" + value


def _rule(selector: str, declaration: str) -> str:
    """A declaration in the same block as a rule whose selector mentions `selector`."""
    return r"(?:^|[{};])[^{}]*" + selector + _BOUND + r"[^{}]*\{[^{}]*" + declaration


#: Element selectors that must not be matched inside a class/id name.
_EL = r"(?<![\w.#-])"

#: Colour-ish values. Rules out an empty declaration and the CSS-wide keywords.
_COLOR = (
    r"(?!(?:inherit|initial|unset|revert)\s*[;}])"
    r"(?:#[0-9a-f]{3,8}|rgba?\(|hsla?\(|var\(\s*--[\w-]+|[a-z]{3,})"
)

#: Lengths from 8px / 0.5rem upward, and from 16px / 1rem upward.
_LEN_8_PLUS = r"(?:(?:[89]|[1-9]\d\d?|\d{4,})px|(?:0\.[5-9]\d*|[1-9][\d.]*)(?:rem|em))"
_LEN_16_PLUS = r"(?:(?:1[6-9]|[2-9]\d|\d{3,})px|(?:1|1\.\d+|[2-9][\d.]*)(?:rem|em))"
#: 12px / 0.75rem upward — the smallest padding that reads as deliberate.
_LEN_12_PLUS = r"(?:(?:1[2-9]|[2-9]\d|\d{3,})px|(?:0\.(?:7[5-9]|[89]\d*)|[1-9][\d.]*)(?:rem|em))"

#: Headline-sized type: 28px / 1.75rem upward.
_FONT_HEADLINE = r"(?:(?:2[89]|[3-9]\d|\d{3,})px|(?:1\.(?:7[5-9]|[89]\d*)|[2-9][\d.]*)(?:rem|em)|clamp\()"
#: A font-size that is set at all, in a unit that scales (so `font-size: 0` and
#: an empty value both fail). Used where the *range* is asserted by rendering.
_FONT_ANY = r"(?:[1-9][\d.]*(?:px|rem|em|%)|0\.[1-9]\d*(?:rem|em)|clamp\(|var\(\s*--)"

#: A custom-property reference. "Driven by custom properties" is only true if
#: the components actually read the tokens back out.
_VAR = r"var\(\s*--[\w-]+"

#: A radius that rounds visibly: 8px / 0.5rem upward, a percentage, or a token.
_RADIUS_8_PLUS = (
    r"(?:(?:[89]|[1-9]\d\d?|\d{4,})px|(?:0\.[5-9]\d*|[1-9][\d.]*)(?:rem|em)"
    r"|[1-9]\d*%|" + _VAR + r")"
)

#: A shadow/ring that actually paints: at least one length plus a colour, or a
#: token. `box-shadow: none` and `box-shadow: 0 0 0` fail.
_SHADOW = r"(?:[^;}]*[1-9][\d.]*(?:px|rem|em)[^;}]*|" + _VAR + r"[^;}]*)"

#: A transition with a real duration. `transition: none` and `0s` fail.
_TRANSITION = r"[^;}]*(?:[1-9]\d*m?s|0\.[1-9]\d*s)"

# --- HTML: hero region ------------------------------------------------------
#: The opening tag of the hero banner, then a fence that cannot leave the
#: section, so "somewhere else on the page" never satisfies a hero check.
_HERO_OPEN = r"<section\b[^>]*\bid\s*=\s*[\"']hero[\"'][^>]*>"
_IN_HERO = r"(?:(?!</section)[\s\S])*?"

#: An <img> whose src looks like a real URL/path (it must contain a `/` and a
#: filename-ish tail) and whose alt is at least two words of real text. Attribute
#: order is free. `src=""`/`alt=""` and `alt="img"` all fail.
#: The `nav` element and the hero's id, each fenced on both sides so
#: `.navigations ul.navbar` and `#hero-teaser` — selectors that merely contain
#: the token and match nothing in the real markup — cannot satisfy a check.
_NAV = _EL + r"nav" + _BOUND
_HERO_SEL = r"#hero" + _BOUND

#: The poster image inside a card, however the learner hooked it.
_CARD_IMG = r"(?:\.card[^{}]*" + _EL + r"img|\.poster|\.card__image)"

_REAL_IMG = (
    r"<img\b"
    r"(?=[^>]*\bsrc\s*=\s*[\"'][^\"'\s]*/[^\"'\s]{3,}[\"'])"
    r"(?=[^>]*\balt\s*=\s*[\"'][^\"']*[A-Za-z]{2,}[^\"']*\s+[^\"']*[A-Za-z]{2,}[^\"']*[\"'])"
    r"[^>]*>"
)


# ---------------------------------------------------------------------------
# Rendered checks for the styling tickets.
#
# `render_*` checks are graded by loading the assembled bundle in headless
# Chromium (see `app/services/render_judge.py`), so they assert the outcome the
# learner's eye is judging: resolved colours, real font metrics, real box
# geometry, real column counts. They are what makes "this looks like a product"
# gradeable at all — a textual check cannot tell `color: var(--muted)` (a real
# colour) from `color: var(--mutted)` (silently the inherited one).
#
# Two rules constrain which elements they may target:
#
#   * The entry document is always `index.html`, never the file under test, so
#     every rendered check declares `entry` explicitly. Left to default, a check
#     carrying `"file": "styles.css"` would try to render the stylesheet as HTML.
#   * They may only target elements the *markup* tickets produce (header, nav,
#     hero, `main`, the empty list section). The styling sprint runs before the
#     JS sprint, so at grading time `#…List` is still empty and no `.card`
#     exists in the DOM — a rendered check on `.card` would fail a correct
#     stylesheet. Card styling is therefore graded textually, with the value of
#     every declaration pinned to a range; the composed project is what proves
#     the cards look right (`scripts/verify_web_ticket_solutions.py`).
# ---------------------------------------------------------------------------

#: The two viewports the styling tickets are judged at: a laptop and a phone.
_WIDE = {"width": 1280, "height": 900}
_PHONE = {"width": 390, "height": 844}
_NARROW = {"width": 360, "height": 780}
_ULTRA = {"width": 1600, "height": 900}

#: Chromium's unstyled defaults, quoted exactly as `getComputedStyle` reports
#: them. A check that rejects these is a check that cannot pass on a stylesheet
#: which never touched the element.
_DEFAULT_LINK_BLUE = "rgb(0, 0, 238)"
#: Anything whose first family is a serif (the Times default) is rejected.
_NOT_SERIF_STACK = r"^(?!times|serif|\"?times)"


def _render(check_id: str, kind: str, selector: str, **spec: Any) -> dict[str, Any]:
    """A rendered check against the assembled page, with `index.html` as entry."""
    return {
        "id": check_id,
        "type": kind,
        "entry": "index.html",
        "selector": selector,
        **spec,
    }


# ---------------------------------------------------------------------------
# Reference solutions for the web tickets.
#
# Not served to the client: nothing in the API reads `solution_files`. They
# exist so `scripts/verify_web_ticket_solutions.py` can prove, for every
# template below, that a correct implementation passes every check *and* that an
# incomplete one fails — the guarantee the project tickets never had.
#
# `{entity}` / `{entity_plural}` / `{domain}` are substituted the same way the
# sprint generator substitutes them in the checks.
# ---------------------------------------------------------------------------

HTML_STRUCTURE_SOLUTION = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{domain}</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <header class="site-header">
      <h1>{domain}</h1>
    </header>
    <main id="app">
      <section id="hero">
        <h2>Tonight's {entity_plural}, booked in seconds</h2>
        <p>Browse what is showing near you and pick your seats without queueing.</p>
        <img
          src="https://picsum.photos/seed/{entity}-hero/1200/500"
          alt="Audience seated in a cinema before the film starts"
        />
      </section>
      <section id="{entity}List"></section>
    </main>
    <footer>
      <p>&copy; 2026 {domain}</p>
    </footer>
    <script src="script.js"></script>
  </body>
</html>
"""

#: The markup after the navigation ticket, used as the entry document when the
#: CSS solutions are verified and previewed.
HTML_NAVIGATION_SOLUTION = HTML_STRUCTURE_SOLUTION.replace(
    "      <h1>{domain}</h1>\n",
    """      <h1>{domain}</h1>
      <nav aria-label="Primary">
        <ul>
          <li><a href="#browse">Browse</a></li>
          <li><a href="#bookings">My Bookings</a></li>
          <li><a href="#account">Account</a></li>
        </ul>
      </nav>
""",
)

CSS_TOKENS_SOLUTION = """/* ---------------------------------------------------------------
   1. Design tokens — one place to change the whole theme.
   --------------------------------------------------------------- */
:root {
  --surface: #0e1117;
  --surface-raised: #161b26;
  --border: #252d3d;
  --text: #f3f5fa;
  --muted: #98a2b8;
  --accent: #ff5d73;
  --radius: 14px;
  --radius-sm: 10px;
  --shadow: 0 18px 40px rgba(3, 6, 14, 0.5);
  --font-sans: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

/* ---------------------------------------------------------------
   2. Page shell
   --------------------------------------------------------------- */
body {
  margin: 0;
  background-color: var(--surface);
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 32px;
  background-color: var(--surface-raised);
  border-bottom: 1px solid var(--border);
}

header h1 {
  margin: 0;
  font-size: 1.375rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

/* ---------------------------------------------------------------
   3. Navigation
   --------------------------------------------------------------- */
nav ul {
  display: flex;
  align-items: center;
  gap: 26px;
  margin: 0;
  padding: 0;
  list-style: none;
}

nav a {
  color: var(--muted);
  font-size: 0.9375rem;
  font-weight: 600;
  text-decoration: none;
  transition: color 160ms ease;
}

nav a:hover {
  color: var(--text);
}

nav a:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 4px;
  border-radius: 6px;
}

/* ---------------------------------------------------------------
   4. Hero
   --------------------------------------------------------------- */
#hero {
  padding: 64px 32px 40px;
  text-align: center;
}

#hero h2 {
  margin: 0 0 14px;
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.1;
  letter-spacing: -0.02em;
}

#hero p {
  max-width: 56ch;
  margin: 0 auto 32px;
  color: var(--muted);
  font-size: 1.0625rem;
}

#hero img {
  display: block;
  width: 100%;
  max-width: 100%;
  height: auto;
  aspect-ratio: 16 / 6;
  object-fit: cover;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

/* ---------------------------------------------------------------
   5. Footer
   --------------------------------------------------------------- */
footer {
  padding: 28px 32px 40px;
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.875rem;
}

footer p {
  margin: 0;
}
"""

CSS_CARD_GRID_SOLUTION = (
    CSS_TOKENS_SOLUTION
    + """
/* ---------------------------------------------------------------
   6. The {entity} grid — the column count follows the width, so no
   media query is needed for the tracks themselves.
   --------------------------------------------------------------- */
#{entity}List {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 28px;
  padding: 8px 32px 64px;
}

/* ---------------------------------------------------------------
   7. Cards
   --------------------------------------------------------------- */
.card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  background-color: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 10px 24px rgba(3, 6, 14, 0.35);
  transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease;
}

.card img {
  display: block;
  width: 100%;
  aspect-ratio: 2 / 3;
  height: auto;
  object-fit: cover;
  border-radius: var(--radius-sm);
}

.card h3 {
  margin: 0;
  font-size: 1.0625rem;
  font-weight: 650;
  line-height: 1.3;
  letter-spacing: -0.01em;
}

.card p {
  margin: 0;
  color: var(--muted);
  font-size: 0.875rem;
}

/* `margin-top: auto` pins the price to the bottom of the card, so the price
   line stays on one baseline across a row even when a title wraps. */
.card .price {
  margin-top: auto;
  color: var(--text);
  font-weight: 700;
}

.card:hover {
  transform: translateY(-6px);
  border-color: var(--accent);
  box-shadow: 0 24px 46px rgba(3, 6, 14, 0.6);
}

.card:focus-within {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
}
"""
)

CSS_RESPONSIVE_SOLUTION = (
    CSS_CARD_GRID_SOLUTION
    + """
/* ---------------------------------------------------------------
   8. The content column: fluid, but capped and centred so the grid
   never sprawls across a 27" monitor.
   --------------------------------------------------------------- */
main {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

/* ---------------------------------------------------------------
   9. Phones: one column, tighter spacing, a shorter banner.
   --------------------------------------------------------------- */
@media (max-width: 640px) {
  header {
    padding: 14px 20px;
  }

  nav ul {
    gap: 16px;
  }

  #hero {
    padding: 36px 20px 28px;
  }

  #hero p {
    margin-bottom: 24px;
    font-size: 1rem;
  }

  #hero img {
    aspect-ratio: 4 / 3;
  }

  #{entity}List {
    grid-template-columns: 1fr;
    gap: 20px;
    padding: 8px 20px 40px;
  }
}

/* ---------------------------------------------------------------
  10. Laptops and up: slightly larger cards.
   --------------------------------------------------------------- */
@media (min-width: 1024px) {
  #{entity}List {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  }
}
"""
)

JS_RENDER_LIST_SOLUTION = """const container = document.getElementById("{entity}List");

const {entity_plural} = [
  {
    id: 1,
    title: "Interstellar",
    genre: "Sci-fi",
    rating: 8.6,
    price: 320,
    poster: "https://picsum.photos/seed/{entity}-1/400/600",
  },
  {
    id: 2,
    title: "Spirited Away",
    genre: "Animation",
    rating: 8.6,
    price: 280,
    poster: "https://picsum.photos/seed/{entity}-2/400/600",
  },
  {
    id: 3,
    title: "Dune: Part Two",
    genre: "Sci-fi",
    rating: 8.5,
    price: 340,
    poster: "https://picsum.photos/seed/{entity}-3/400/600",
  },
  {
    id: 4,
    title: "Portrait of a Lady on Fire",
    genre: "Drama",
    rating: 8.1,
    price: 240,
    poster: "https://picsum.photos/seed/{entity}-4/400/600",
  },
  {
    id: 5,
    title: "Everything Everywhere All at Once",
    genre: "Adventure",
    rating: 7.8,
    price: 300,
    poster: "https://picsum.photos/seed/{entity}-5/400/600",
  },
  {
    id: 6,
    title: "Perfect Days",
    genre: "Drama",
    rating: 7.9,
    price: 260,
    poster: "https://picsum.photos/seed/{entity}-6/400/600",
  },
];

function cardMarkup(item) {
  return `
    <article class="card" data-id="${item.id}">
      <img src="${item.poster}" alt="Poster for ${item.title}" />
      <h3>${item.title}</h3>
      <p>${item.genre} &middot; ${item.rating}/10</p>
      <p class="price">From Rs ${item.price}</p>
    </article>
  `;
}

container.innerHTML = {entity_plural}.map(cardMarkup).join("");
"""

# --- Fundamentals: the two tickets that run before any DOM work -------------
#
# The Interactivity sprint used to open on `js_dom`, so the first line of
# JavaScript a learner ever wrote was a `querySelector`. These two tickets put
# the language first: values, strings and numbers, then functions and the array
# methods — graded by running the functions, not by matching keywords.

JS_BASICS_SOLUTION = """// Display formatting for the {entity} data.
// Every one of these takes data in and returns a string out: no DOM, no
// globals, so each one can be tested on its own.

const CURRENCY = "Rs";

function formatPrice(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) {
    return `${CURRENCY} --`;
  }
  return `${CURRENCY} ${amount.toFixed(0)}`;
}

function formatRating(value) {
  const rating = Number(value);
  if (!Number.isFinite(rating)) {
    return "Not rated";
  }
  return `${rating.toFixed(1)}/10`;
}

function formatMeta(item) {
  const genre = item && item.genre ? item.genre : "Uncategorised";
  return `${genre} \\u00b7 ${formatRating(item && item.rating)}`;
}

function truncate(text, limit) {
  const value = String(text === undefined || text === null ? "" : text);
  const max = Number(limit);
  if (!Number.isFinite(max) || value.length <= max) {
    return value;
  }
  return `${value.slice(0, max - 1).trimEnd()}\\u2026`;
}
"""

JS_FUNCTIONS_SOLUTION = (
    JS_BASICS_SOLUTION
    + """
// --- Pure list operations --------------------------------------------------
// Each returns a NEW array. Nothing here sorts or splices the caller's data,
// so the same source list can be filtered and sorted in any order.

function filterByGenre(items, genre) {
  const list = Array.isArray(items) ? items : [];
  if (!genre || genre === "all") {
    return list.slice();
  }
  return list.filter((item) => item && item.genre === genre);
}

function sortByRating(items) {
  const list = Array.isArray(items) ? items : [];
  return list.slice().sort((a, b) => Number(b.rating) - Number(a.rating));
}

function summarise(items) {
  const list = Array.isArray(items) ? items : [];
  if (list.length === 0) {
    return "Nothing to show yet";
  }
  const total = list.reduce((sum, item) => sum + Number(item.rating || 0), 0);
  const average = total / list.length;
  return `${list.length} results \\u00b7 avg ${average.toFixed(1)}`;
}
"""
)

JS_SELECTION_SOLUTION = (
    JS_RENDER_LIST_SOLUTION
    + """
// --- Selection -------------------------------------------------------------
// One listener on the container, not one per card: cards re-rendered later are
// covered for free, and there is nothing to tear down.

// A live region: screen readers announce the change without the focus moving.
let summary = document.getElementById("selectionSummary");
if (!summary) {
  summary = document.createElement("p");
  summary.id = "selectionSummary";
  summary.className = "selection-summary";
  summary.setAttribute("aria-live", "polite");
  container.parentNode.insertBefore(summary, container);
}

const state = {
  selected: null,
};

function renderSummary() {
  summary.textContent = state.selected
    ? `Selected: ${state.selected.title}`
    : "No {entity} selected yet";
}

container.addEventListener("click", (event) => {
  const card = event.target.closest(".card");
  if (!card || !container.contains(card)) return;

  const id = Number(card.dataset.id);
  const item = {entity_plural}.find((candidate) => candidate.id === id);
  if (!item) return;

  const previous = container.querySelector(".card.selected");
  if (previous && previous !== card) {
    previous.classList.remove("selected");
    previous.setAttribute("aria-pressed", "false");
  }

  const isSelected = card.classList.toggle("selected");
  card.setAttribute("aria-pressed", isSelected ? "true" : "false");
  state.selected = isSelected ? item : null;
  renderSummary();
});

renderSummary();
"""
)

JS_ASYNC_SOLUTION = """const container = document.getElementById("{entity}List");
const ENDPOINT = "/api/{entity_plural}";

function cardMarkup(item) {
  return `
    <article class="card" data-id="${item.id}">
      <img src="${item.poster}" alt="Poster for ${item.title}" />
      <h3>${item.title}</h3>
      <p>${item.genre} &middot; ${item.rating}/10</p>
      <p class="price">From Rs ${item.price}</p>
    </article>
  `;
}

// The three states are written into the same container, in the order the user
// experiences them: loading first, then whatever the response turned out to be.
async function loadItems() {
  container.innerHTML = `<p class="state state--loading">Loading {entity_plural}\u2026</p>`;

  const response = await fetch(ENDPOINT);
  const items = await response.json();

  if (items.length === 0) {
    container.innerHTML = `<p class="state state--empty">No {entity_plural} are showing right now.</p>`;
    return;
  }

  container.innerHTML = items.map(cardMarkup).join("");
}

loadItems();
"""

JS_RESILIENT_SOLUTION = """const container = document.getElementById("{entity}List");
const ENDPOINT = "/api/{entity_plural}";

function cardMarkup(item) {
  return `
    <article class="card" data-id="${item.id}">
      <img src="${item.poster}" alt="Poster for ${item.title}" />
      <h3>${item.title}</h3>
      <p>${item.genre} &middot; ${item.rating}/10</p>
      <p class="price">From Rs ${item.price}</p>
    </article>
  `;
}

async function loadItems() {
  container.innerHTML = `<p class="state state--loading">Loading {entity_plural}\u2026</p>`;

  try {
    const response = await fetch(ENDPOINT);
    if (!response.ok) {
      throw new Error(`The server responded with ${response.status}`);
    }

    const items = await response.json();

    if (items.length === 0) {
      container.innerHTML = `<p class="state state--empty">No {entity_plural} are showing right now.</p>`;
      return;
    }

    container.innerHTML = items.map(cardMarkup).join("");
  } catch (error) {
    // The failure has to be visible on the page. console.error is for us, not
    // for the person waiting on the listing.
    container.innerHTML = `
      <div class="state state--error" role="alert">
        <p>We could not load the {entity_plural}. ${error.message}</p>
        <button type="button" class="state__retry">Try again</button>
      </div>
    `;
    container.querySelector(".state__retry").addEventListener("click", loadItems);
  }
}

loadItems();
"""

API_CLIENT_SOLUTION = """// A thin client: one function per endpoint, every failure turned into an Error
// with a message the UI can show. Nothing in here touches the DOM.

const BASE_URL = "/api";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, options) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, options);
  } catch (error) {
    throw new ApiError(`The network request failed: ${error.message}`, 0);
  }

  if (!response.ok) {
    throw new ApiError(`Request to ${path} failed with status ${response.status}`, response.status);
  }

  return response.json();
}

async function listItems() {
  return request("/{entity_plural}");
}

async function getItem(id) {
  return request(`/{entity_plural}/${id}`);
}

async function createItem(payload) {
  return request("/{entity_plural}", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
"""

# --- React ------------------------------------------------------------------
#
# The React tickets are graded on App.jsx alone, so they are graded textually.
# The bar they hold is the same one the CSS tickets hold: semantic landmarks,
# real class hooks so the stylesheet still applies, keys from stable ids, and
# loading / empty / error treated as UI rather than as console output.

REACT_COMPONENTS_SOLUTION = """import React from "react";

const items = [
  {
    id: 1,
    title: "Interstellar",
    genre: "Sci-fi",
    rating: 8.6,
    price: 320,
    poster: "https://picsum.photos/seed/{entity}-1/400/600",
  },
  {
    id: 2,
    title: "Spirited Away",
    genre: "Animation",
    rating: 8.6,
    price: 280,
    poster: "https://picsum.photos/seed/{entity}-2/400/600",
  },
  {
    id: 3,
    title: "Dune: Part Two",
    genre: "Sci-fi",
    rating: 8.5,
    price: 340,
    poster: "https://picsum.photos/seed/{entity}-3/400/600",
  },
];

function Card({ item }) {
  return (
    <article className="card">
      <img className="card__poster" src={item.poster} alt={`Poster for ${item.title}`} />
      <h3>{item.title}</h3>
      <p>
        {item.genre} &middot; {item.rating}/10
      </p>
      <p className="price">From Rs {item.price}</p>
    </article>
  );
}

export default function App() {
  return (
    <main id="app">
      <section id="hero">
        <h2>Tonight's {entity_plural}, booked in seconds</h2>
      </section>
      <section id="{entity}List" className="listing" aria-label="Available {entity_plural}">
        {items.map((item) => (
          <Card key={item.id} item={item} />
        ))}
      </section>
    </main>
  );
}
"""

REACT_STATE_SOLUTION = """import React, { useState } from "react";

const items = [
  { id: 1, title: "Interstellar", genre: "Sci-fi", rating: 8.6, price: 320, poster: "https://picsum.photos/seed/{entity}-1/400/600" },
  { id: 2, title: "Spirited Away", genre: "Animation", rating: 8.6, price: 280, poster: "https://picsum.photos/seed/{entity}-2/400/600" },
  { id: 3, title: "Dune: Part Two", genre: "Sci-fi", rating: 8.5, price: 340, poster: "https://picsum.photos/seed/{entity}-3/400/600" },
];

function Card({ item, isSelected, onSelect }) {
  return (
    <article className={isSelected ? "card card--selected" : "card"}>
      <img className="card__poster" src={item.poster} alt={`Poster for ${item.title}`} />
      <h3>{item.title}</h3>
      <p>
        {item.genre} &middot; {item.rating}/10
      </p>
      <button
        type="button"
        className="card__select"
        aria-pressed={isSelected}
        onClick={() => onSelect(item)}
      >
        {isSelected ? "Selected" : `Select for Rs ${item.price}`}
      </button>
    </article>
  );
}

export default function App() {
  const [selected, setSelected] = useState(null);
  const [seats, setSeats] = useState([]);

  function handleSelect(item) {
    setSelected((current) => (current && current.id === item.id ? null : item));
    setSeats([]);
  }

  function addSeat(seat) {
    setSeats((current) => [...current, seat]);
  }

  return (
    <main id="app">
      <section id="{entity}List" className="listing" aria-label="Available {entity_plural}">
        {items.map((item) => (
          <Card
            key={item.id}
            item={item}
            isSelected={Boolean(selected) && selected.id === item.id}
            onSelect={handleSelect}
          />
        ))}
      </section>
      <aside className="summary" aria-live="polite">
        {selected ? (
          <>
            <h2>{selected.title}</h2>
            <p>{seats.length} seat(s) held</p>
            <button type="button" onClick={() => addSeat(seats.length + 1)}>
              Add a seat
            </button>
          </>
        ) : (
          <p className="summary__empty">Pick a {entity} to start booking.</p>
        )}
      </aside>
    </main>
  );
}
"""

REACT_FETCH_SOLUTION = """import React, { useEffect, useState } from "react";

function Card({ item }) {
  return (
    <article className="card">
      <img className="card__poster" src={item.poster} alt={`Poster for ${item.title}`} />
      <h3>{item.title}</h3>
      <p>
        {item.genre} &middot; {item.rating}/10
      </p>
    </article>
  );
}

export default function App() {
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch("/api/{entity_plural}", { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`The server responded with ${response.status}`);
        }
        const data = await response.json();
        setItems(data);
      } catch (requestError) {
        if (requestError.name !== "AbortError") {
          setError(requestError.message);
        }
      } finally {
        setIsLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, []);

  if (isLoading) {
    return (
      <main id="app">
        <p className="state state--loading" role="status">
          Loading {entity_plural}\\u2026
        </p>
      </main>
    );
  }

  if (error) {
    return (
      <main id="app">
        <div className="state state--error" role="alert">
          <p>We could not load the {entity_plural}.</p>
          <p className="state__detail">{error}</p>
        </div>
      </main>
    );
  }

  if (items.length === 0) {
    return (
      <main id="app">
        <p className="state state--empty">No {entity_plural} are showing right now.</p>
      </main>
    );
  }

  return (
    <main id="app">
      <section id="{entity}List" className="listing" aria-label="Available {entity_plural}">
        {items.map((item) => (
          <Card key={item.id} item={item} />
        ))}
      </section>
    </main>
  );
}
"""

# ---------------------------------------------------------------------------
# Layer-2 behaviour harness for async data loading.
#
# The harness owns the network function, the DOM and the renderer, and runs the
# learner's whole file (wrapped as `__userMain`) once per scenario. Because the
# learner cannot choose what the request does, a hard-coded
# `Promise.resolve({ ok: true })` can never satisfy the failure scenarios.
# ---------------------------------------------------------------------------

ASYNC_LOADING_PRELUDE = r"""
let __scenario = () => { throw new Error('no scenario configured'); };
let __jsonParsed = false;
let __rendered = null;
// DOM-mutation bookkeeping. `__requestStarted` flips when the harness-owned
// network entry point is called, so the harness can tell writes that happened
// *before* the request (the loading indicator) apart from writes that happened
// *after* it settled (the real success/error rendering).
let __requestStarted = false;
let __domAtRequest = '';
let __postRequestWrites = 0;

function __recordWrite() {
  if (__requestStarted) __postRequestWrites++;
  __note();
}

function __serializeNode(node, depth) {
  if (node === null || node === undefined) return '';
  if (typeof node !== 'object') return String(node);
  if ((depth || 0) > 6) return '';
  if (typeof node.tagName === 'string' || node._attrs) {
    const tag = String(node.tagName || 'div').toLowerCase();
    const attrs = Object.keys(node._attrs || {})
      .map((k) => ' ' + k + '="' + node._attrs[k] + '"')
      .join('');
    const kids = (node.children || [])
      .map((child) => __serializeNode(child, (depth || 0) + 1))
      .join('');
    return '<' + tag + attrs + '>' + (node._html || '') + kids + (node._text || '') + '</' + tag + '>';
  }
  try {
    return JSON.stringify(node);
  } catch (e) {
    return String(node);
  }
}

function __serializeChildren(node, depth) {
  return (node.children || [])
    .map((child) => __serializeNode(child, (depth || 0) + 1))
    .join('');
}

function __adopt(parent, child) {
  if (child && typeof child === 'object') { child.parentNode = parent; }
}

function __descendants(el) {
  const out = [];
  (el.children || []).forEach((child) => {
    out.push(child);
    __descendants(child).forEach((node) => out.push(node));
  });
  return out;
}

// One simple selector: `.class`, `#id`, `[attr]` or a tag name. Enough for the
// container-scoped queries the tickets ask for; a compound selector simply does
// not match rather than throwing.
function __matchesOne(el, selector) {
  const sel = String(selector || '').trim();
  if (!sel || !el) return false;
  if (sel.charAt(0) === '.') {
    return el.classList ? el.classList.contains(sel.slice(1)) : false;
  }
  if (sel.charAt(0) === '#') return el.id === sel.slice(1);
  const attr = sel.match(/^\[([\w-]+)\]$/);
  if (attr) return el.getAttribute ? el.getAttribute(attr[1]) !== null : false;
  return String(el.tagName || '').toLowerCase() === sel.toLowerCase();
}

function __matchesSelector(el, selector) {
  return String(selector || '')
    .split(',')
    .some((part) => __matchesOne(el, part));
}

function __makeElement(tag) {
  const el = {
    tagName: tag || 'div',
    _html: '',
    _text: '',
    _attrs: {},
    children: [],
    style: {},
    // A real element knows its parent. Without it, `container.parentNode` was
    // `undefined` and the idiomatic way to add a sibling live region —
    // `container.parentNode.insertBefore(node, container)`, which is the only
    // option when the ticket does not let the learner edit index.html — died
    // with "Cannot read properties of undefined", blamed on their code.
    parentNode: null,
    appendChild(child) { el.children.push(child); __adopt(el, child); __recordWrite(); return child; },
    append(...kids) { kids.forEach((k) => { el.children.push(k); __adopt(el, k); }); __recordWrite(); },
    prepend(...kids) { kids.forEach((k) => { el.children.unshift(k); __adopt(el, k); }); __recordWrite(); },
    replaceChildren(...kids) { el.children = kids; kids.forEach((k) => __adopt(el, k)); __recordWrite(); },
    insertAdjacentHTML(_position, html) { el._html += String(html); __recordWrite(); },
    insertBefore(child, reference) {
      const at = reference ? el.children.indexOf(reference) : 0;
      el.children.splice(at < 0 ? el.children.length : at, 0, child);
      __adopt(el, child);
      __recordWrite();
      return child;
    },
    setAttribute(name, value) {
      el._attrs[String(name).toLowerCase()] = String(value);
      __recordWrite();
    },
    removeAttribute(name) { delete el._attrs[String(name).toLowerCase()]; },
    getAttribute(name) {
      const value = el._attrs[String(name).toLowerCase()];
      return value === undefined ? null : value;
    },
    addEventListener() {},
    // A no-op `remove()` made every implementation that clears by detaching
    // nodes — rather than by assigning innerHTML — look as though it never
    // cleared the loading state.
    remove() {
      const parent = el.parentNode;
      if (parent && parent.children) {
        const at = parent.children.indexOf(el);
        if (at !== -1) { parent.children.splice(at, 1); }
      }
      el.parentNode = null;
      __recordWrite();
    },
    // Scoping a query to a container (`list.querySelectorAll('.card')`) is basic
    // practice and is what the selection ticket asks for, but only `document`
    // used to carry these, so element-scoped queries threw
    // "querySelectorAll is not a function" and failed the whole run.
    querySelectorAll(selector) {
      return __descendants(el).filter((node) => __matchesSelector(node, selector));
    },
    querySelector(selector) {
      const found = __descendants(el).filter((node) => __matchesSelector(node, selector));
      return found.length > 0 ? found[0] : null;
    },
    closest(selector) {
      let node = el;
      while (node) {
        if (__matchesSelector(node, selector)) return node;
        node = node.parentNode;
      }
      return null;
    },
  };
  // classList and className are two views of the same class attribute, so a
  // learner who sets `el.className = 'error'` is seen the same as one who calls
  // `el.classList.add('error')`.
  const readClasses = () => String(el._attrs['class'] || '').split(/\s+/).filter(Boolean);
  const writeClasses = (list) => { el._attrs['class'] = list.join(' '); __recordWrite(); };
  el.classList = {
    add(...c) { const s = new Set(readClasses()); c.forEach((x) => s.add(x)); writeClasses(Array.from(s)); },
    remove(...c) { const s = new Set(readClasses()); c.forEach((x) => s.delete(x)); writeClasses(Array.from(s)); },
    toggle(c) { const s = new Set(readClasses()); s.has(c) ? s.delete(c) : s.add(c); writeClasses(Array.from(s)); },
    contains(c) { return readClasses().indexOf(c) !== -1; },
    _values: () => readClasses(),
    _clear: () => { el._attrs['class'] = ''; },
  };
  Object.defineProperty(el, 'className', {
    get: () => String(el._attrs['class'] || ''),
    set: (value) => { el._attrs['class'] = String(value); __recordWrite(); },
  });
  Object.defineProperty(el, 'id', {
    get: () => String(el._attrs['id'] || ''),
    set: (value) => { el._attrs['id'] = String(value); __recordWrite(); },
  });
  // innerHTML serialises appended children too: building elements with
  // createElement/appendChild must be judged exactly like assigning innerHTML.
  Object.defineProperty(el, 'innerHTML', {
    get: () => el._html + __serializeChildren(el, 0),
    set: (value) => { el._html = String(value); el.children = []; __recordWrite(); },
  });
  Object.defineProperty(el, 'outerHTML', {
    get: () => __serializeNode(el, 0),
    set: (value) => { el._html = String(value); el.children = []; __recordWrite(); },
  });
  Object.defineProperty(el, 'textContent', {
    get: () => el._text + __serializeChildren(el, 0).replace(/<[^>]*>/g, ' '),
    set: (value) => { el._text = String(value); el.children = []; __recordWrite(); },
  });
  Object.defineProperty(el, 'innerText', {
    get: () => el.textContent,
    set: (value) => { el._text = String(value); el.children = []; __recordWrite(); },
  });
  return el;
}

const movieList = __makeElement('ul');
// The listing lives inside a document in the browser, so it has somewhere to
// put a sibling. `document.body` is that ancestor here.
const __pageRoot = __makeElement('main');
__pageRoot.appendChild(movieList);
globalThis.movieList = movieList;
globalThis.document = {
  body: __pageRoot,
  querySelector: () => movieList,
  querySelectorAll: () => [movieList],
  getElementById: () => movieList,
  getElementsByClassName: () => [movieList],
  createElement: (tag) => __makeElement(tag),
  addEventListener() {},
};
globalThis.window = globalThis;
globalThis.alert = () => {};

function __okResponse(data) {
  return {
    ok: true,
    status: 200,
    statusText: 'OK',
    json: async () => { __jsonParsed = true; __note(); return data; },
    text: async () => { __jsonParsed = true; __note(); return JSON.stringify(data); },
  };
}

function __failResponse(status) {
  return {
    ok: false,
    status: status || 500,
    statusText: 'Server Error',
    json: async () => { __jsonParsed = true; __note(); return {}; },
    text: async () => { __jsonParsed = true; __note(); return ''; },
  };
}

globalThis.renderMovies = (items) => {
  __rendered = items;
  movieList.children = Array.isArray(items) ? items.slice() : [items];
  __recordWrite();
};
globalThis.renderItems = globalThis.renderMovies;
globalThis.render = globalThis.renderMovies;

// Every network entry point the learner might call is owned by the harness. The
// moment one is called we snapshot the DOM, so the state painted before the
// request (the loading indicator) can never be mistaken for the result.
globalThis.loadMovies = async (..._args) => {
  __note();
  __requestStarted = true;
  __postRequestWrites = 0;
  __domAtRequest = __domText();
  return __scenario();
};
globalThis.loadItems = globalThis.loadMovies;
globalThis.loadData = globalThis.loadMovies;
globalThis.fetchMovies = globalThis.loadMovies;
globalThis.fetch = globalThis.loadMovies;

function __setup(scenario) {
  __scenario = scenario;
  __jsonParsed = false;
  __rendered = null;
  __requestStarted = false;
  __domAtRequest = '';
  __postRequestWrites = 0;
  movieList._html = '';
  movieList._text = '';
  movieList._attrs = {};
  movieList.children = [];
  __resetErrors();
}

function __domText() {
  return [
    movieList._html,
    __serializeChildren(movieList, 0),
    movieList._text,
    Object.keys(movieList._attrs || {})
      .map((k) => k + '="' + movieList._attrs[k] + '"')
      .join(' '),
  ].join(' ');
}

// "Loading" is matched on whole words only: "Unable to load movies" is NOT a
// loading state, while "Loading…", "spinner" and "please wait" are.
const __LOADING_RE = /\b(loading|spinner|skeleton|fetching)\b|please\s+wait/i;

// Wording-independent evidence that the page is telling the user something went
// wrong: an error-shaped hook (class/id/role/data-* naming an error or alert) or
// any of the common failure phrasings learners actually write.
const __ERROR_HOOK_RE =
  /(class|id|role|data-[\w-]*)\s*=\s*["']?[^"'>]*\b(error|errors|alert|danger|fail|failed|failure|warning|problem)\b/i;
const __FAILURE_WORDS_RE =
  /\b(error|failed|failure|unable|cannot|can't|couldn't|could\s+not|went\s+wrong|try\s+again|retry|problem|oops|sorry|unavailable|denied|timed\s+out|timeout|refused|offline|down)\b/i;

function __hasErrorHook() {
  return __ERROR_HOOK_RE.test(__domText());
}

function __mentionsFailure() {
  return __FAILURE_WORDS_RE.test(__domText());
}

function __mentionsLoading() {
  return __LOADING_RE.test(__domText());
}

function __errorSuffix() {
  if (!__runtimeErrors.length) return '';
  return ' (your code threw ' + __runtimeErrors.join('; ') + ')';
}

// A genuine error state must satisfy ALL of the following. No single exact
// sentence is ever required, so "Unable to load movies", "Something went wrong"
// and "Could not fetch" all qualify.
//   1. Something was written to the DOM *after* the request started. A loading
//      indicator painted before the first await, or a catch block that only
//      calls console.error, therefore cannot pass.
//   2. The DOM is not empty.
//   3. The visible state actually changed from the snapshot taken when the
//      request started, so re-rendering the same loading markup is not enough.
//   4. The page no longer reads as a loading state, unless it also carries an
//      error hook or failure wording (so "Loading failed — try again" counts).
function __expectErrorState() {
  if (__postRequestWrites === 0) {
    return (
      'nothing was written to the page after the request failed — the error path ' +
      'never rendered an error state' +
      __errorSuffix()
    );
  }
  const text = __domText().trim();
  if (!text) {
    return 'the page is empty after the failure, so the user is told nothing' + __errorSuffix();
  }
  if (text === __domAtRequest.trim()) {
    return 'the page still shows exactly what it showed before the request' + __errorSuffix();
  }
  if (__mentionsLoading() && !__hasErrorHook() && !__mentionsFailure()) {
    return 'the DOM still shows the loading state instead of an error state' + __errorSuffix();
  }
  if (!__hasErrorHook() && !__mentionsFailure()) {
    return (
      'the page changed but shows nothing error-shaped — render a visible message ' +
      '(or an element with an error/alert class or role)' +
      __errorSuffix()
    );
  }
  return true;
}

// Kept for specs that predate __expectErrorState; same rule, boolean result.
function __errorShown() {
  return __expectErrorState() === true;
}

function __successShown() {
  return __rendered !== null || movieList.children.length > 0 || __domText().trim().length > 0;
}

function __expectSuccess() {
  if (!__jsonParsed) {
    return 'response.json() was never called, so the payload was never read' + __errorSuffix();
  }
  if (__postRequestWrites === 0 || !__successShown()) {
    return 'the data arrived but nothing was rendered into the page' + __errorSuffix();
  }
  if (__mentionsLoading()) {
    return 'the DOM still shows the loading state after the data arrived' + __errorSuffix();
  }
  if (__runtimeErrors.length) {
    return 'your code threw on the success path: ' + __runtimeErrors.join('; ');
  }
  return true;
}
"""

ASYNC_LOADING_ASSERTIONS = [
    {
        "id": "rejection_contained",
        "requirement_indexes": [0, 3],
        "label": "A rejected request never escapes and the page shows an error",
        "concept": "promise rejection",
        "hint": "await on a rejected promise throws — catch it and render an error state.",
        "expression": (
            "__setup(() => Promise.reject(new Error('network down')));"
            " await __userMain();"
            " return __expectErrorState();"
        ),
    },
    {
        "id": "non_ok_not_parsed",
        "requirement_index": 1,
        "label": "A 500 response is treated as an error and the body is not parsed",
        "concept": "HTTP status codes",
        "hint": "Check response.ok before calling response.json().",
        "expression": (
            "__setup(() => __failResponse(500));"
            " await __userMain();"
            " if (__jsonParsed) return 'response.json() was called even though the response"
            " status was 500 — check response.ok first';"
            " return __expectErrorState();"
        ),
    },
    {
        "id": "success_renders",
        "requirement_index": None,
        "label": "A successful response renders the list and clears the loading state",
        "concept": "async/await",
        "hint": (
            "Parse the body after the status check, render the result, and replace the"
            " loading indicator with the rendered list."
        ),
        "expression": (
            "__setup(() => __okResponse([{ id: 1, title: 'Arrival' }]));"
            " await __userMain();"
            " return __expectSuccess();"
        ),
    },
]

ASYNC_LOADING_BEHAVIOUR: dict[str, Any] = {
    "file": "script.js",
    "wrap_as": "__userMain",
    "prelude": ASYNC_LOADING_PRELUDE,
    "assertions": ASYNC_LOADING_ASSERTIONS,
}

TICKET_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    # -------------------------------------------------------------- HTML
    "html_basics": [
        {
            "slug": "html-structure",
            "title": "Create the base HTML structure for {domain}",
            "description": (
                "Set up the document skeleton for {domain}. It needs a header with the product "
                "name, a hero banner that greets the visitor with a headline, a tagline and a "
                "real image, a main region that will later hold the {entity} list, and a footer."
            ),
            "requirements": [
                "Add a <header> containing an <h1> with the product name",
                "Add a <main> element with id \"app\"",
                "Inside <main>, add a <section> with id \"hero\" holding an <h2> headline and a <p> tagline",
                "Give the hero a banner <img> with a real src and a descriptive alt of at least two words",
                "Inside <main>, add a <section> with id \"{entity}List\"",
                "Add a <footer> element",
            ],
            "acceptance_criteria": [
                "The page has exactly one <h1>",
                "<main id=\"app\"> exists and contains the hero and the {entity} list section",
                "The hero shows a headline, a tagline and a banner image with meaningful alt text",
                "Header and footer landmarks are present",
            ],
            "estimated_minutes": 25,
            "files": ["index.html"],
            "solution_files": {"index.html": HTML_STRUCTURE_SOLUTION},
            "checks": [
                {"id": "header", "type": "html_element", "file": "index.html", "selector": "header", "label": "<header> landmark exists", "concept": "landmarks", "requirement_index": 0},
                {"id": "h1", "type": "html_element", "file": "index.html", "selector": "h1", "non_empty_text": True, "label": "<h1> with the product name", "concept": "headings hierarchy", "requirement_index": 0},
                {"id": "main", "type": "html_element", "file": "index.html", "selector": "main#app", "label": "<main id=\"app\"> exists", "concept": "landmarks", "requirement_index": 1},
                {"id": "hero", "type": "html_element", "file": "index.html", "selector": "section#hero", "label": "<section id=\"hero\"> exists", "concept": "semantic html", "requirement_index": 2},
                {"id": "hero_in_main", "type": "html_nested", "file": "index.html", "selector": "section#hero", "parent": "main", "label": "The hero is inside <main>", "concept": "nesting", "requirement_index": 2},
                # Scoped to the hero and pinned to real text: an empty <h2></h2>
                # or a headline elsewhere on the page cannot satisfy these.
                {"id": "hero_headline", "type": "regex", "file": "index.html", "pattern": _HERO_OPEN + _IN_HERO + r"<h2\b[^>]*>\s*[^<\s][^<]{4,}", "ignore_case": True, "label": "The hero has an <h2> headline with real text", "concept": "headings hierarchy", "hint": "Put the <h2> inside <section id=\"hero\"> and give it at least a few words.", "requirement_index": 2},
                {"id": "hero_tagline", "type": "regex", "file": "index.html", "pattern": _HERO_OPEN + _IN_HERO + r"<p\b[^>]*>\s*[^<\s][^<]{14,}", "ignore_case": True, "label": "The hero has a <p> tagline with a real sentence", "concept": "semantic html", "hint": "A sentence of supporting copy under the headline, inside the hero section.", "requirement_index": 2},
                {"id": "hero_image", "type": "html_element", "file": "index.html", "selector": "img", "with_attributes": {"src": "/", "alt": "*"}, "label": "A banner <img> with a src and an alt exists", "concept": "images", "hint": "src must point somewhere real (a URL or a path) and alt must describe the picture.", "requirement_index": 3},
                {"id": "hero_image_real", "type": "regex", "file": "index.html", "pattern": _HERO_OPEN + _IN_HERO + _REAL_IMG, "ignore_case": True, "label": "The hero's <img> has a real src and a descriptive alt", "concept": "images", "hint": "src=\"\" or alt=\"\" renders nothing useful. Use e.g. https://picsum.photos/seed/hero/1200/500 and an alt of two or more words.", "requirement_index": 3},
                {"id": "list_section", "type": "html_element", "file": "index.html", "selector": "section#{entity}List", "label": "<section id=\"{entity}List\"> exists", "concept": "semantic html", "requirement_index": 4},
                {"id": "nested", "type": "html_nested", "file": "index.html", "selector": "section#{entity}List", "parent": "main", "label": "List section is inside <main>", "concept": "nesting", "requirement_index": 4},
                {"id": "footer", "type": "html_element", "file": "index.html", "selector": "footer", "label": "<footer> landmark exists", "concept": "landmarks", "requirement_index": 5},
            ],
        }
    ],
    "html_semantics": [
        {
            "slug": "navigation",
            "title": "Build the navigation system",
            "description": (
                "Add an accessible primary navigation to {domain} with links to Browse, "
                "My Bookings and Account. Screen-reader users must be able to identify it."
            ),
            "requirements": [
                "Add a <nav> element inside the header",
                "Give the <nav> an aria-label attribute",
                "Add a <ul> with at least three <a> links",
            ],
            "acceptance_criteria": [
                "<nav aria-label=\"...\"> exists inside the header",
                "Navigation links are marked up as a list",
                "At least three anchors with href attributes are present",
            ],
            "estimated_minutes": 25,
            "files": ["index.html"],
            "solution_files": {"index.html": HTML_NAVIGATION_SOLUTION},
            "checks": [
                # Requirement 0 ("inside the header") went ungraded until now:
                # a <nav> anywhere on the page satisfied the checks below.
                {"id": "nav_in_header", "type": "html_nested", "file": "index.html", "selector": "nav", "parent": "header", "label": "The <nav> is inside the <header>", "concept": "landmarks", "hint": "Primary navigation belongs in the header landmark, beside the product name.", "requirement_index": 0},
                {"id": "nav", "type": "html_element", "file": "index.html", "selector": "nav", "with_attributes": {"aria-label": "*"}, "label": "<nav> has an aria-label", "concept": "aria", "requirement_index": 1},
                {"id": "nav_list", "type": "html_nested", "file": "index.html", "selector": "ul", "parent": "nav", "label": "Links are inside a <ul> in the nav", "concept": "semantic html", "requirement_index": 2},
                {"id": "links", "type": "html_element", "file": "index.html", "selector": "a", "min_count": 3, "with_attributes": {"href": "*"}, "label": "At least three links with href", "concept": "elements", "requirement_index": 2},
            ],
        }
    ],
    # --------------------------------------------------------------- CSS
    "css_basics": [
        {
            "slug": "design-tokens",
            "title": "Establish the visual foundation",
            "description": (
                "Give {domain} a design system instead of browser defaults. You are building "
                "four things: a token block that owns every colour and radius, a page shell "
                "with a real type scale, a header bar with a horizontal nav whose links look "
                "and behave like product navigation, and a hero with a constrained measure "
                "and a properly cropped banner.\n\n"
                "Suggested tokens (names are yours, these are the roles):\n"
                "  --surface  page background        --surface-raised  header/card surface\n"
                "  --border   hairline separators    --text            primary copy\n"
                "  --muted    secondary copy         --accent          one highlight colour\n"
                "  --radius   corner rounding        --font-sans       your font stack\n\n"
                "Use one accent colour and stick to it. The graded targets: body text at a "
                "line-height of 1.5+, the header <h1> between 18px and 30px, the hero "
                "headline 32px or more, and a banner that keeps a fixed aspect ratio."
            ),
            "requirements": [
                "Declare at least four design tokens with real values in a :root block, and read them back with var() in the rules below",
                "Style body from the tokens: background-color and color both via var(), and margin: 0 so the shell reaches the edges",
                "Set a sans-serif font-family stack on body (not the browser's serif default) and a line-height of 1.5 or more",
                "Build a type scale: an explicit font-size on the header <h1> that renders between 18px and 30px, and a hero headline that renders at 32px or more",
                "Make the <header> a bar: at least 8px of padding, its own background colour, and a bottom edge (border-bottom or box-shadow)",
                "Lay the nav's <ul> out horizontally with display: flex, a gap of 8px or more and no list markers",
                "Style the nav links: a colour of your own (never the browser's default blue) and text-decoration: none",
                "Give the nav links interaction states: a :hover change and a visible :focus-visible outline",
                "Give the hero at least 16px of padding and constrain the tagline to a readable measure (a max-width around 56ch) centred with auto margins",
                "Make the banner image fluid (max-width: 100%), crop it to a fixed aspect-ratio with object-fit: cover, and round its corners",
                "Finish the shell: give the <footer> at least 16px of padding, a border-top and muted text so it closes the page instead of dangling",
            ],
            "acceptance_criteria": [
                ":root owns the palette and the components read it back through var()",
                "The page renders in your own colours and font stack, with a deliberate type scale",
                "The header reads as a bar and the navigation runs horizontally with hover and focus states",
                "The hero has a constrained, centred measure and a banner cropped to a fixed aspect ratio",
                "The footer closes the page with a border, padding and secondary text",
            ],
            "estimated_minutes": 35,
            "files": ["styles.css"],
            "solution_files": {"styles.css": CSS_TOKENS_SOLUTION},
            "checks": [
                # Each token must carry a real value: `--brand: ;` declares a
                # property the browser discards, so matching the colon alone
                # accepted a stylesheet that applies nothing.
                {"id": "root_tokens", "type": "regex", "file": "styles.css", "pattern": r":root\s*\{(?:[^}]*--[\w-]+\s*:[^;}]*[^\s;}]){4,}", "label": ":root declares at least four design tokens", "concept": "specificity", "hint": "One :root block holding the palette, the radius and the font stack — each with a real value.", "requirement_index": 0},
                {"id": "token_reuse", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _VAR + r"[\s\S]*" + _VAR + r"[\s\S]*" + _VAR, "label": "The tokens are read back with var() at least three times", "concept": "specificity", "hint": "Tokens nobody references are decoration. Use `var(--surface)`, `var(--text)`, `var(--accent)` in the rules.", "requirement_index": 0},
                # `value_pattern` only rules out the placeholder keywords, which
                # declare the property without applying anything. Any real
                # colour or font stack still passes, so a ticket already in
                # progress is unaffected.
                {"id": "body_bg", "type": "css_property", "file": "styles.css", "selector": "body", "property": "background-color", "value_pattern": _REAL_VALUE, "label": "body has background-color", "concept": "colors", "requirement_index": 1},
                {"id": "body_color", "type": "css_property", "file": "styles.css", "selector": "body", "property": "color", "value_pattern": _REAL_VALUE, "label": "body has a text color", "concept": "colors", "requirement_index": 1},
                {"id": "body_uses_tokens", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_EL + "body", _decl("background(?:-color)?", _VAR)), "label": "body's background comes from a token", "concept": "colors", "hint": "`body { background-color: var(--surface); }` — the theme should be changeable from :root alone.", "requirement_index": 1},
                {"id": "body_margin", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_EL + "body", _decl("margin", r"0")), "label": "body's default margin is removed", "concept": "box model", "hint": "`margin: 0` on body — the browser's 8px margin leaves a pale gutter around your header.", "requirement_index": 1},
                # Rendered: proves the declared colour actually resolves. A
                # typo'd token (`var(--surfcae)`) computes to transparent, which
                # a textual check cannot see.
                _render("body_paints", "render_color", "body", property="background-color", require_opaque=True, viewport=_WIDE, label="The page background actually paints on screen", concept="colors", hint="A misspelled token resolves to nothing and the page stays default white.", requirement_index=1),
                {"id": "font", "type": "css_property", "file": "styles.css", "selector": "body", "property": "font-family", "value_pattern": _REAL_VALUE, "label": "body sets font-family", "concept": "box model", "requirement_index": 2},
                {"id": "body_line_height", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_EL + "body", _decl("line-height", r"(?:1\.[4-9]\d*|[2-9][\d.]*|1[4-9]\d*%|[2-9]\d\d%|(?:2[4-9]|[3-9]\d)px)")), "label": "body sets a line-height of 1.5 or more", "concept": "typography", "hint": "`line-height: 1.6` — default leading makes paragraphs look cramped.", "requirement_index": 2},
                _render("body_font_renders", "render_computed_style", "body", property="font-family", value_pattern=_NOT_SERIF_STACK, viewport=_WIDE, label="The rendered page is not set in the default serif", concept="typography", hint="Times New Roman is the tell-tale sign of an unstyled page. Lead your stack with a UI font.", requirement_index=2),
                {"id": "h1_size", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_EL + "header" + r"[^{}]*" + _EL + "h1", _decl("font-size", _FONT_ANY)), "label": "The header <h1> has an explicit font-size", "concept": "typography", "hint": "`header h1 { font-size: 1.375rem; }` — the browser default (2em) is a document title, not a product wordmark.", "requirement_index": 3},
                _render("h1_scale_renders", "render_computed_style", "header h1", property="font-size", min_value=18, max_value=30, viewport=_WIDE, label="The header wordmark renders between 18px and 30px", concept="typography", hint="Anything at the 32px browser default is not a scale you chose.", requirement_index=3),
                {"id": "hero_headline", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_HERO_SEL + "[^{}]*" + _EL + "h[12]", _decl("font-size", _FONT_HEADLINE)), "label": "The hero headline is 1.75rem or larger", "concept": "typography", "hint": "`#hero h2 { font-size: clamp(2rem, 4vw, 3rem); }` — a hero headline at body size does not read as a hero.", "requirement_index": 3},
                _render("hero_headline_renders", "render_computed_style", "#hero h2", property="font-size", min_value=32, viewport=_WIDE, label="The hero headline renders at 32px or more", concept="typography", requirement_index=3),
                # Everything below ties a declaration to a selector inside the
                # same block and pins the value to a range, so `padding: 0`,
                # `gap: 0`, an empty value or a commented-out rule all fail.
                {"id": "header_padding", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_EL + "header", _decl("padding", r"(?:[^;}]*\s)?" + _LEN_8_PLUS)), "label": "The header has at least 8px of padding", "concept": "spacing", "hint": "A bar needs breathing room: `header { padding: 18px 32px; }`.", "requirement_index": 4},
                {"id": "header_background", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_EL + "header", _decl("background(?:-color)?", _COLOR)), "label": "The header has its own background colour", "concept": "colors", "hint": "Give the header a surface of its own (a token via var() is fine) so it separates from the page.", "requirement_index": 4},
                {"id": "header_edge", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_EL + "header", r"(?:" + _decl("border-bottom", r"[^;}]*[\d.]+(?:px|rem|em)") + r"|" + _decl("box-shadow", _SHADOW) + r")"), "label": "The header is separated by a bottom border or a shadow", "concept": "colors", "hint": "`border-bottom: 1px solid var(--border)` — a hairline is what makes a bar read as a bar.", "requirement_index": 4},
                _render("header_row_renders", "render_row_layout", "header", min_children=2, viewport=_WIDE, label="The wordmark and the nav sit on one row", concept="flexbox", hint="`display: flex; justify-content: space-between` on the header — stacked blocks are the unstyled default.", requirement_index=4),
                {"id": "nav_horizontal", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_NAV + "[^{}]*" + _EL + "ul", _decl("display", r"(?:inline-)?(?:flex|grid)")), "label": "The nav's <ul> is a flex row", "concept": "flexbox", "hint": "`nav ul { display: flex; }` — without it the links stack vertically as a bullet list.", "requirement_index": 5},
                {"id": "nav_gap", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_NAV + "[^{}]*" + _EL + "ul", _decl("gap", r"(?:[^;}]*\s)?" + _LEN_8_PLUS)), "label": "The nav links are separated by a gap of 8px or more", "concept": "spacing", "hint": "Add `gap: 24px` to the same `nav ul` rule. `gap: 0` does not separate anything.", "requirement_index": 5},
                {"id": "nav_markers", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_NAV + "[^{}]*" + _EL + "ul", _decl("list-style(?:-type)?", "none")), "label": "The nav loses its list markers", "concept": "lists", "hint": "`list-style: none` on the <ul> — the markup stays a list, the bullets go.", "requirement_index": 5},
                _render("nav_row_renders", "render_row_layout", "nav ul", min_children=3, viewport=_WIDE, label="The nav links render side by side", concept="flexbox", requirement_index=5),
                {"id": "nav_link_color", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_NAV + "[^{}]*" + _EL + "a", _decl("color", _COLOR)), "label": "The nav links declare a colour", "concept": "colors", "hint": "`nav a { color: var(--muted); }` — anchors do not inherit colour from the header.", "requirement_index": 6},
                {"id": "nav_link_underline", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_NAV + "[^{}]*" + _EL + "a", _decl("text-decoration(?:-line)?", "none")), "label": "The nav links drop their underline", "concept": "selectors", "requirement_index": 6},
                _render("nav_link_not_blue", "render_computed_style", "nav a", property="color", value_not_in=[_DEFAULT_LINK_BLUE], all_match=True, viewport=_WIDE, label="No link renders in the browser's default blue", concept="colors", hint="rgb(0, 0, 238) underlined is what an unstyled page looks like. Colour the links yourself.", requirement_index=6),
                {"id": "nav_link_hover", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_NAV + "[^{}]*" + _EL + r"a\s*:\s*hover", r"[\w-]+\s*:[^;}]*\S"), "label": "The nav links have a :hover state with a real declaration", "concept": "selectors", "hint": "`nav a:hover { color: var(--text); }`. An empty rule is not a hover state.", "requirement_index": 7},
                {"id": "nav_link_focus", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_NAV + "[^{}]*" + _EL + r"a\s*:\s*focus(?:-visible)?", r"(?:" + _decl("outline", r"(?!none)[^;}]*\S") + r"|" + _decl("box-shadow", _SHADOW) + r")"), "label": "The nav links have a visible :focus-visible outline", "concept": "aria", "hint": "`nav a:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }` — keyboard users need to see where they are.", "requirement_index": 7},
                {"id": "hero_padding", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_HERO_SEL, _decl("padding", r"(?:[^;}]*\s)?" + _LEN_16_PLUS)), "label": "The hero has at least 16px of padding", "concept": "spacing", "requirement_index": 8},
                {"id": "tagline_measure", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_HERO_SEL + "[^{}]*" + _EL + "p", _decl("max-width", r"[^;}]*[\d.]+\s*(?:ch|rem|em|px)")), "label": "The hero tagline is capped to a readable measure", "concept": "typography", "hint": "`#hero p { max-width: 56ch; }` — a line of text 1200px wide is unreadable.", "requirement_index": 8},
                _render("tagline_measure_renders", "render_box", "#hero p", max_width_ratio=0.85, viewport=_WIDE, label="The tagline renders narrower than the hero", concept="typography", hint="If the paragraph still spans the full hero width, the max-width is not taking effect.", requirement_index=8),
                _render("tagline_centred_renders", "render_centered", "#hero p", within="#hero", viewport=_WIDE, label="The tagline is centred in the hero", concept="box model", hint="`margin: 0 auto` centres a block once it has a max-width.", requirement_index=8),
                {"id": "banner_fluid_width", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_HERO_SEL + "[^{}]*" + _EL + "img", _decl("max-width", "100%")), "label": "The banner is capped at 100% of its container", "concept": "responsive images", "hint": "Without `max-width: 100%` a 1200px banner forces a horizontal scrollbar.", "requirement_index": 9},
                {"id": "banner_aspect", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_HERO_SEL + "[^{}]*" + _EL + "img", r"(?:" + _decl("aspect-ratio", r"[\d.]+\s*(?:/\s*[\d.]+)?") + r"|" + _decl("(?:max-)?height", r"[\d.]+(?:px|rem|em|vh)") + r")"), "label": "The banner is cropped to a fixed aspect ratio", "concept": "responsive images", "hint": "`#hero img { aspect-ratio: 16 / 6; }` — a banner as tall as it is wide swamps the page.", "requirement_index": 9},
                {"id": "banner_fit", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_HERO_SEL + "[^{}]*" + _EL + "img", _decl("object-fit", r"(?:cover|contain)")), "label": "The banner uses object-fit so it is not squashed", "concept": "responsive images", "hint": "Forcing an aspect ratio without `object-fit: cover` distorts the photograph.", "requirement_index": 9},
                {"id": "banner_radius", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_HERO_SEL + "[^{}]*" + _EL + "img", _decl("border-radius", _RADIUS_8_PLUS)), "label": "The banner has rounded corners", "concept": "box model", "requirement_index": 9},
                # 1216px of hero content width: a banner left at `height: auto`
                # renders ~912px tall, a cropped one ~456px. The ceiling is what
                # proves the aspect ratio took effect on screen.
                _render("banner_box_renders", "render_box", "#hero img", min_width_ratio=0.8, max_width_ratio=1.0, min_height=140, max_height=760, viewport=_WIDE, label="The banner fills the hero width at a controlled height", concept="responsive images", hint="An uncropped banner renders taller than the viewport; a cropped one is a band across the top.", requirement_index=9),
                {"id": "footer_padding", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_EL + "footer", _decl("padding", r"(?:[^;}]*\s)?" + _LEN_16_PLUS)), "label": "The footer has at least 16px of padding", "concept": "spacing", "hint": "An unstyled footer is a line of text stuck to the bottom-left corner.", "requirement_index": 10},
                {"id": "footer_border", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_EL + "footer", _decl("border-top", r"[^;}]*[\d.]+(?:px|rem|em)")), "label": "The footer is separated by a top border", "concept": "colors", "hint": "`border-top: 1px solid var(--border)` closes the page.", "requirement_index": 10},
                {"id": "footer_muted", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_EL + "footer", _decl("color", _COLOR)), "label": "The footer text is set in a secondary colour", "concept": "colors", "hint": "`color: var(--muted)` — the copyright line should not compete with the headline.", "requirement_index": 10},
            ],
        }
    ],
    "css_layout": [
        {
            "slug": "card-grid",
            "title": "Style the {entity} cards and grid",
            "description": (
                "Turn the {entity} listing into a grid of cards that look like a product "
                "catalogue. Reuse the tokens from the previous ticket — no new colours.\n\n"
                "Two ideas do most of the work here:\n"
                "  * `grid-template-columns: repeat(auto-fill, minmax(220px, 1fr))` lets the "
                "column count follow the available width, so you never hand-write breakpoints "
                "for the tracks.\n"
                "  * A card reads as a surface when it has all four of a background, a "
                "hairline border, a radius and a shadow — any one alone looks unfinished.\n\n"
                "Make the card a flex column with a gap so the poster, title and meta line "
                "space themselves, and give the hover state a transition so it eases rather "
                "than snaps."
            ),
            "requirements": [
                "Make #{entity}List a grid whose columns follow the width: repeat(auto-fill, minmax(220px, 1fr)), plus padding around the listing",
                "Separate the cards with a gap of 16px or more",
                "Give .card a real surface: a background colour from a token, a 1px border, a border-radius of 8px or more, at least 12px of padding and a box-shadow",
                "Lay the card's contents out as a flex column with a gap so the poster, title and meta line are evenly spaced",
                "Set the card's typography: an explicit font-size on .card h3 with margin: 0, and the meta paragraphs in the muted token",
                "Style the poster: width 100%, a fixed aspect-ratio, object-fit: cover and its own border-radius",
                "Make the hover state feel deliberate: a transition with a duration on .card, and a :hover rule that lifts the card with transform or a stronger shadow",
            ],
            "acceptance_criteria": [
                "The listing reflows from one to many columns without a media query",
                "Cards read as surfaces: background, border, radius, padding and shadow together",
                "Poster, title and meta line sit in an evenly spaced column with deliberate type",
                "Posters share one aspect ratio and are cropped, not stretched",
                "Hovering a card animates a lift rather than jumping",
            ],
            "estimated_minutes": 35,
            "files": ["styles.css"],
            "solution_files": {"styles.css": CSS_CARD_GRID_SOLUTION},
            "checks": [
                {"id": "grid", "type": "regex", "file": "styles.css", "pattern": r"#\w*[Ll]ist[^{]*\{[^}]*display\s*:\s*(grid|flex)", "label": "Listing container uses grid or flex", "concept": "grid", "requirement_index": 0},
                {"id": "grid_auto_tracks", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"#\w*[Ll]ist", _decl("grid-template-columns", r"[^;}]*repeat\(\s*auto-(?:fill|fit)\s*,\s*minmax\(")), "label": "The columns follow the width with auto-fill and minmax()", "concept": "grid", "hint": "`repeat(auto-fill, minmax(220px, 1fr))` — a fixed `repeat(4, 1fr)` cannot adapt.", "requirement_index": 0},
                {"id": "list_padding", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"#\w*[Ll]ist", _decl("padding", r"(?:[^;}]*\s)?" + _LEN_8_PLUS)), "label": "The listing has padding around it", "concept": "spacing", "hint": "Cards touching the window edge look like a bug, not a layout.", "requirement_index": 0},
                _render("list_grid_renders", "render_computed_style", "#{entity}List", property="display", value_pattern="grid", viewport=_WIDE, label="The listing renders as a grid container", concept="grid", requirement_index=0),
                _render("list_columns_renders", "render_grid_columns", "#{entity}List", min=3, viewport=_WIDE, label="The listing renders at least three columns on a laptop", concept="grid", hint="At 1280px a 220px minimum should give four or five tracks. One track means the track list is not doing what you think.", requirement_index=0),
                # The gap must be a real length declared on the listing
                # container itself: a bare `gap:` anywhere in the file used to
                # satisfy this, including `gap: 0` on an unrelated rule.
                {"id": "gap", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"#\w*[Ll]ist", _decl("gap", r"(?:[^;}]*\s)?" + _LEN_16_PLUS)), "label": "A gap of 16px or more separates the cards", "concept": "spacing", "hint": "Declare `gap` on the listing container, with a real length.", "requirement_index": 1},
                _render("list_gap_renders", "render_computed_style", "#{entity}List", property="column-gap", min_value=16, viewport=_WIDE, label="The rendered gap between columns is 16px or more", concept="spacing", requirement_index=1),
                {"id": "card_surface", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"\.card", _decl("background(?:-color)?", _VAR)), "label": ".card has a surface colour from a token", "concept": "colors", "hint": "`background-color: var(--surface-raised)` — a card the same colour as the page is not a card.", "requirement_index": 2},
                {"id": "card_border", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"\.card", _decl("border", r"[^;}]*[\d.]+(?:px|rem|em)")), "label": ".card has a hairline border", "concept": "box model", "hint": "`border: 1px solid var(--border)` defines the card's edge against the page.", "requirement_index": 2},
                {"id": "card_radius", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"\.card", _decl("border-radius", _RADIUS_8_PLUS)), "label": ".card has a border-radius of 8px or more", "concept": "box model", "requirement_index": 2},
                {"id": "card_padding", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"\.card", _decl("padding", r"(?:[^;}]*\s)?" + _LEN_12_PLUS)), "label": ".card has at least 12px of padding", "concept": "box model", "requirement_index": 2},
                {"id": "card_shadow", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"\.card", _decl("box-shadow", _SHADOW)), "label": ".card casts a shadow", "concept": "box model", "hint": "A soft shadow is what lifts a card off the surface. `box-shadow: 0 10px 24px rgba(0, 0, 0, 0.35)`.", "requirement_index": 2},
                {"id": "card_flow", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"\.card", _decl("display", r"(?:flex|grid)")), "label": ".card lays its contents out with flex or grid", "concept": "flexbox", "hint": "`display: flex; flex-direction: column;` lets one `gap` space every child.", "requirement_index": 3},
                {"id": "card_gap", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"\.card", _decl("gap", r"(?:[^;}]*\s)?" + _LEN_8_PLUS)), "label": ".card spaces its children with a gap", "concept": "spacing", "requirement_index": 3},
                {"id": "card_title_size", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"\.card[^{}]*" + _EL + "h3", _decl("font-size", _FONT_ANY)), "label": ".card h3 has an explicit font-size", "concept": "typography", "hint": "`.card h3 { font-size: 1.0625rem; }` — the default h3 is oversized inside a card.", "requirement_index": 4},
                {"id": "card_title_margin", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"\.card[^{}]*" + _EL + "h3", _decl("margin", r"0")), "label": ".card h3 drops its default margins", "concept": "box model", "hint": "Heading margins fight the card's `gap`. Set `margin: 0` and let the gap do the spacing.", "requirement_index": 4},
                {"id": "card_meta_color", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"\.card[^{}]*" + _EL + "p", _decl("color", _VAR)), "label": "The card's meta text uses the muted token", "concept": "colors", "hint": "`.card p { color: var(--muted); }` gives the card a visual hierarchy.", "requirement_index": 4},
                {"id": "poster_width", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_CARD_IMG, _decl("width", "100%")), "label": "The card's poster fills the card width", "concept": "responsive images", "hint": "`.card img { width: 100%; }` — an intrinsically sized poster makes every card a different width.", "requirement_index": 5},
                {"id": "poster_aspect", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_CARD_IMG, r"(?:" + _decl("aspect-ratio", r"[\d.]+\s*(?:/\s*[\d.]+)?") + r"|" + _decl("height", r"[\d.]+(?:px|rem|em|vh)") + r")"), "label": "The poster has a fixed aspect ratio or height", "concept": "responsive images", "hint": "`aspect-ratio: 2 / 3` (or a fixed height) keeps every poster the same shape.", "requirement_index": 5},
                {"id": "poster_fit", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_CARD_IMG, _decl("object-fit", r"(?:cover|contain)")), "label": "The poster uses object-fit so it is not stretched", "concept": "responsive images", "hint": "Forcing an aspect ratio without `object-fit: cover` distorts the artwork.", "requirement_index": 5},
                {"id": "poster_radius", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_CARD_IMG, _decl("border-radius", _RADIUS_8_PLUS)), "label": "The poster's corners are rounded", "concept": "box model", "hint": "A square poster inside a rounded card is the detail that gives the whole grid away.", "requirement_index": 5},
                {"id": "card_transition", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(r"\.card", _decl("transition", _TRANSITION)), "label": ".card declares a transition with a real duration", "concept": "selectors", "hint": "`transition: transform 200ms ease, box-shadow 200ms ease;` — without it the hover snaps.", "requirement_index": 6},
                {"id": "card_hover", "type": "regex", "file": "styles.css", "pattern": r"\.card:hover\s*\{[^}]*[\w-]+\s*:[^;}]*\S", "label": ".card:hover defines a hover effect", "concept": "selectors", "requirement_index": 6},
                {"id": "card_hover_lift", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": r"\.card\s*:\s*hover\s*\{[^}]*(?:" + _decl("transform", r"(?!none)[^;}]*\S") + r"|" + _decl("box-shadow", _SHADOW) + r")", "label": ".card:hover lifts the card with transform or a stronger shadow", "concept": "selectors", "hint": "`transform: translateY(-6px)` plus a deeper shadow is the whole effect.", "requirement_index": 6},
            ],
        }
    ],
    "css_responsive": [
        {
            "slug": "responsive",
            "title": "Make the layout responsive",
            "description": (
                "{domain} has to hold up from a 360px phone to a 27-inch monitor, and the "
                "answer is different at each end: on a wide screen the content needs a cap "
                "so lines of text do not run for 2000px, and on a phone the grid needs to "
                "become a single column with tighter spacing and a smaller headline.\n\n"
                "Work mobile-first: the base rules should already be fluid, and the media "
                "query should only carry what genuinely changes. Aim for a breakpoint around "
                "640px, cap the content column at roughly 1200px, and remember the hero "
                "headline — display type that works at 1280px is shouting at 390px. "
                "clamp() counts if you prefer it to a media query."
            ),
            "requirements": [
                "Keep the layout fluid: cap the <main> content column with a max-width and centre it with auto margins, and make sure nothing overflows a 360px-wide viewport",
                "Add at least one media query with a real breakpoint",
                "Below the breakpoint, collapse the {entity} grid to a single column",
                "Above the breakpoint, the grid must still render at least three columns at 1280px",
                "Scale the hero headline down for small screens: 40px or more at 1280px, and no more than 34px at 390px",
            ],
            "acceptance_criteria": [
                "The content column is capped and centred on a wide screen, and nothing overflows at 360px",
                "A media query carries the small-screen rules",
                "The grid renders one column on a phone and three or more on a laptop",
                "The hero headline is display-sized on a laptop and readable on a phone",
            ],
            "estimated_minutes": 30,
            "files": ["styles.css"],
            "solution_files": {"styles.css": CSS_RESPONSIVE_SOLUTION},
            "checks": [
                {"id": "container_cap", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_EL + "main", _decl("max-width", r"[^;}]*[\d.]+\s*(?:px|rem|em|ch|vw)")), "label": "<main> is capped with a max-width", "concept": "fluid units", "hint": "`main { max-width: 1200px; }` — an uncapped grid sprawls across a wide monitor.", "requirement_index": 0},
                {"id": "container_centre", "type": "regex", "file": "styles.css", "ignore_case": True, "pattern": _rule(_EL + "main", _decl("margin(?:-inline)?", r"[^;}]*auto")), "label": "<main> is centred with auto margins", "concept": "box model", "hint": "`margin: 0 auto` — a capped column pinned to the left edge looks broken.", "requirement_index": 0},
                _render("main_cap_renders", "render_box", "main", max_width=1320, viewport=_ULTRA, label="The content column stays capped on a 1600px screen", concept="fluid units", requirement_index=0),
                _render("main_centred_renders", "render_centered", "main", viewport=_ULTRA, label="The capped column is centred on a wide screen", concept="box model", requirement_index=0),
                _render("header_fits_renders", "render_box", "header", max_width=366, viewport=_NARROW, label="The header fits a 360px viewport", concept="mobile first", requirement_index=0),
                _render("banner_fits_renders", "render_box", "#hero img", max_width=366, viewport=_NARROW, label="The banner fits a 360px viewport", concept="responsive images", requirement_index=0),
                _render("list_fits_renders", "render_box", "#{entity}List", max_width=366, viewport=_NARROW, label="The listing fits a 360px viewport", concept="mobile first", requirement_index=0),
                {"id": "media", "type": "css_at_rule", "file": "styles.css", "pattern": r"@media[^{]*\(", "label": "A media query is present", "concept": "media queries", "requirement_index": 1},
                {"id": "single_column", "type": "regex", "file": "styles.css", "pattern": r"@media[\s\S]*?(grid-template-columns\s*:\s*1fr|flex-direction\s*:\s*column|display\s*:\s*block)", "label": "Small screens collapse to one column", "concept": "mobile first", "requirement_index": 2},
                _render("one_column_renders", "render_computed_style", "#{entity}List", property="grid-template-columns", value_pattern=r"^[\d.]+px$", viewport=_PHONE, label="The listing renders exactly one column at 390px", concept="mobile first", hint="A single track means one column. Two or more tracks at phone width give you 150px-wide cards.", requirement_index=2),
                _render("wide_columns_renders", "render_grid_columns", "#{entity}List", min=3, viewport=_WIDE, label="The listing still renders three or more columns at 1280px", concept="grid", hint="Collapsing to one column everywhere is not responsive either.", requirement_index=3),
                _render("headline_wide_renders", "render_computed_style", "#hero h2", property="font-size", min_value=40, viewport=_WIDE, label="The hero headline renders at 40px or more at 1280px", concept="typography", requirement_index=4),
                _render("headline_phone_renders", "render_computed_style", "#hero h2", property="font-size", max_value=34, viewport=_PHONE, label="The hero headline renders at 34px or less at 390px", concept="media queries", hint="Either a media query or `clamp(2rem, 4vw, 3rem)` will do it.", requirement_index=4),
            ],
        }
    ],
    # ---------------------------------------------------------------- JS
    # The Interactivity sprint used to open on `js_dom`, because these two
    # groups had no templates at all and the generator silently skipped them.
    # The first JavaScript a learner wrote was therefore a querySelector. These
    # two tickets put the language first, and both are graded by *running* the
    # functions, so a keyword-shaped file cannot pass them.
    "js_basics": [
        {
            "slug": "format-helpers",
            "title": "Write the display formatting for {entity} data",
            "description": (
                "Before anything reaches the page, the raw {entity} data has to become "
                "strings a person can read. `price: 320` is a number; `Rs 320` is a price. "
                "`rating: 8.63` is a float; `8.6/10` is a rating.\n\n"
                "Write four small functions in script.js. Each one takes data in and "
                "returns a string out — no DOM, no globals — which is exactly why each one "
                "can be tested on its own, and why they are graded by being called rather "
                "than by being read.\n\n"
                "Two rules that will be enforced:\n"
                "  * Build the strings with template literals (`` `${CURRENCY} ${amount}` ``), "
                "not with `+` chains.\n"
                "  * A value that is not a number must never reach the page as `NaN`. "
                "`Number(\"abc\")` is `NaN`, and `NaN` printed in a card is the classic "
                "first bug."
            ),
            "requirements": [
                "Write formatPrice(value): return the price as a display string with a currency marker, built with a template literal",
                "Guard the numbers: a value that is not a number must never come back as NaN",
                "Write formatRating(value): the rating to one decimal place, out of 10",
                "Write formatMeta(item): the card's meta line — the genre, a separator and the formatted rating",
                "Write truncate(text, limit): shorten text longer than limit, and leave shorter text exactly as it is",
                "Declare values with const and let only — no var anywhere in the file",
                "Compare with === and !== — loose equality (== / !=) is banned",
            ],
            "acceptance_criteria": [
                "All four functions exist, are called by the grader and return the strings described",
                "Non-numeric input produces a readable fallback rather than NaN",
                "Strings are assembled with template literals",
                "The file uses block-scoped declarations and strict equality throughout",
            ],
            "estimated_minutes": 30,
            "files": ["script.js"],
            "solution_files": {"script.js": JS_BASICS_SOLUTION},
            "checks": [
                {"id": "syntax", "type": "js_syntax", "file": "script.js", "label": "script.js is valid JavaScript", "concept": "syntax", "requirement_index": None, "precondition": True},
                {"id": "format_price_real", "type": "js_not_trivial", "file": "script.js", "name": "formatPrice", "label": "formatPrice has a real implementation", "concept": "functions", "hint": "An empty body or a constant return is not a formatter.", "requirement_index": 0},
                {"id": "template_literal", "type": "regex", "file": "script.js", "pattern": r"`[^`]*\$\{[^}]+\}", "label": "Strings are built with template literals", "concept": "strings", "hint": "`${CURRENCY} ${amount}` reads better than \"Rs \" + amount and is what the ticket grades.", "requirement_index": 0},
                {"id": "format_rating_real", "type": "js_not_trivial", "file": "script.js", "name": "formatRating", "label": "formatRating has a real implementation", "concept": "numbers", "requirement_index": 2},
                {"id": "format_meta_real", "type": "js_not_trivial", "file": "script.js", "name": "formatMeta", "label": "formatMeta has a real implementation", "concept": "functions", "requirement_index": 3},
                {"id": "truncate_real", "type": "js_not_trivial", "file": "script.js", "name": "truncate", "label": "truncate has a real implementation", "concept": "strings", "requirement_index": 4},
                {"id": "no_var", "type": "not_regex", "file": "script.js", "pattern": r"(?<![\w$.])var\s+[A-Za-z_$]", "label": "No var declarations", "concept": "variables", "hint": "var is function-scoped and hoisted; const and let are not.", "requirement_index": 5},
                {"id": "strict_equality", "type": "not_regex", "file": "script.js", "pattern": r"(?<![=!<>])==(?!=)|(?<![!<>=])!=(?!=)", "label": "Only === and !== are used", "concept": "operators", "hint": "== coerces: \"8\" == 8 is true. Use === so a string rating never silently equals a number.", "requirement_index": 6},
            ],
            "behaviour": {
                "file": "script.js",
                "assertions": [
                    {
                        "id": "price_formats",
                        "requirement_index": 0,
                        "label": "formatPrice(320) returns a currency string containing the amount",
                        "concept": "strings",
                        "hint": "Return something like `Rs 320` — a string with the amount in it.",
                        "expression": (
                            "const out = formatPrice(320);"
                            " if (typeof out !== 'string') return 'formatPrice must return a string, got ' + typeof out;"
                            " if (!out.includes('320')) return 'formatPrice(320) returned \"' + out + '\" — the amount is missing';"
                            " if (out.trim() === '320') return 'formatPrice returned the bare number — add a currency marker';"
                            " return true;"
                        ),
                    },
                    {
                        "id": "price_guards_nan",
                        "requirement_index": 1,
                        "label": "formatPrice never renders NaN for junk input",
                        "concept": "numbers",
                        "hint": "Number(\"sold out\") is NaN. Check with Number.isFinite and return a fallback.",
                        "expression": (
                            "const out = formatPrice('sold out');"
                            " if (typeof out !== 'string') return 'formatPrice must always return a string';"
                            " if (/nan/i.test(out)) return 'formatPrice(\"sold out\") returned \"' + out + '\" — NaN reached the UI';"
                            " return true;"
                        ),
                    },
                    {
                        "id": "rating_one_decimal",
                        "requirement_index": 2,
                        "label": "formatRating(8.63) reads as 8.6 out of 10",
                        "concept": "numbers",
                        "hint": "toFixed(1) fixes the decimal place; the /10 tells the reader the scale.",
                        "expression": (
                            "const out = formatRating(8.63);"
                            " if (typeof out !== 'string') return 'formatRating must return a string';"
                            " if (!out.includes('8.6')) return 'formatRating(8.63) returned \"' + out + '\" — round to one decimal place';"
                            " if (out.includes('8.63')) return 'formatRating(8.63) returned \"' + out + '\" — it was not rounded';"
                            " return true;"
                        ),
                    },
                    {
                        "id": "meta_combines",
                        "requirement_index": 3,
                        "label": "formatMeta joins the genre and the formatted rating",
                        "concept": "strings",
                        "hint": "Reuse formatRating inside formatMeta rather than repeating the rounding.",
                        "expression": (
                            "const out = formatMeta({ genre: 'Drama', rating: 8.1, title: 'Perfect Days' });"
                            " if (typeof out !== 'string') return 'formatMeta must return a string';"
                            " if (!out.includes('Drama')) return 'formatMeta returned \"' + out + '\" — the genre is missing';"
                            " if (!out.includes('8.1')) return 'formatMeta returned \"' + out + '\" — the rating is missing';"
                            " return true;"
                        ),
                    },
                    {
                        "id": "truncate_shortens",
                        "requirement_index": 4,
                        "label": "truncate shortens a long title to the limit",
                        "concept": "strings",
                        "hint": "slice() to the limit and add an ellipsis; the result must not be longer than the limit.",
                        "expression": (
                            "const out = truncate('Everything Everywhere All at Once', 12);"
                            " if (typeof out !== 'string') return 'truncate must return a string';"
                            " if (out.length > 12) return 'truncate(..., 12) returned ' + out.length + ' characters';"
                            " if (out === 'Everything Everywhere All at Once') return 'truncate returned the text unchanged';"
                            " return true;"
                        ),
                    },
                    {
                        "id": "truncate_leaves_short_text",
                        "requirement_index": 4,
                        "label": "truncate leaves text shorter than the limit exactly as it is",
                        "concept": "control flow",
                        "hint": "Return early when the text already fits — no ellipsis on a short title.",
                        "expression": (
                            "const out = truncate('Dune', 12);"
                            " return out === 'Dune' ? true : 'truncate(\"Dune\", 12) returned \"' + out + '\" instead of \"Dune\"';"
                        ),
                    },
                ],
            },
        }
    ],
    "js_functions": [
        {
            "slug": "list-operations",
            "title": "Extract the {entity} filtering and sorting into pure functions",
            "description": (
                "The listing needs to be filterable by genre and sortable by rating. Write "
                "those as pure functions before any of it is wired to a button, because a "
                "function that only takes data and returns data is the one you can actually "
                "reason about — and the one the grader can run a hundred times.\n\n"
                "The rule that makes them pure: never touch the caller's array. "
                "`items.sort()` sorts in place, so the source list silently changes order "
                "for everyone else holding a reference to it. `items.slice().sort()` does "
                "not. The grader checks the caller's array afterwards, so an in-place sort "
                "fails even though the returned value looks right."
            ),
            "requirements": [
                "Write filterByGenre(items, genre) returning a new array; a missing genre or \"all\" returns every item",
                "Write sortByRating(items) returning a new array ordered from the highest rating to the lowest",
                "Keep both functions pure: the array passed in must come back unchanged, in its original order",
                "Write summarise(items) returning a one-line summary with the count and the average rating",
                "Handle an empty list: summarise must return a readable message, never \"NaN\" or a crash",
                "Build the results with the array methods — filter, slice, sort and reduce — not index loops pushing into a shared array",
            ],
            "acceptance_criteria": [
                "Filtering and sorting both return new arrays with the right contents",
                "The source array is never mutated by either function",
                "summarise reports the count and the average, and survives an empty list",
                "The implementations use the array methods rather than manual loops",
            ],
            "estimated_minutes": 35,
            "files": ["script.js"],
            "solution_files": {"script.js": JS_FUNCTIONS_SOLUTION},
            "checks": [
                {"id": "syntax", "type": "js_syntax", "file": "script.js", "label": "script.js is valid JavaScript", "concept": "syntax", "requirement_index": None, "precondition": True},
                {"id": "filter_real", "type": "js_not_trivial", "file": "script.js", "name": "filterByGenre", "label": "filterByGenre has a real implementation", "concept": "array methods", "requirement_index": 0},
                {"id": "sort_real", "type": "js_not_trivial", "file": "script.js", "name": "sortByRating", "label": "sortByRating has a real implementation", "concept": "array methods", "requirement_index": 1},
                # An in-place sort on the parameter is the defect this ticket
                # exists to teach, so it is banned textually as well as caught
                # by the purity scenario below.
                {"id": "no_mutation", "type": "not_regex", "file": "script.js", "pattern": r"(?<![\w$.])items\s*\.\s*(?:sort|reverse|splice|push|pop|shift|unshift)\s*\(", "label": "The argument array is never mutated in place", "concept": "immutability", "hint": "items.sort() reorders the caller's array. Copy first: items.slice().sort(...).", "requirement_index": 2},
                {"id": "summarise_real", "type": "js_not_trivial", "file": "script.js", "name": "summarise", "label": "summarise has a real implementation", "concept": "functions", "requirement_index": 3},
                {"id": "uses_filter", "type": "js_calls", "file": "script.js", "callee": ".filter", "label": "Genuinely calls .filter()", "concept": "array methods", "requirement_index": 5},
                {"id": "uses_reduce", "type": "js_calls", "file": "script.js", "callee": ".reduce", "label": "Genuinely calls .reduce()", "concept": "array methods", "hint": "The average is a fold over the list — reduce is what it is for.", "requirement_index": 5},
            ],
            "behaviour": {
                "file": "script.js",
                "assertions": [
                    {
                        "id": "filters_by_genre",
                        "requirement_index": 0,
                        "label": "filterByGenre keeps only the matching genre",
                        "concept": "array methods",
                        "expression": (
                            "const data = [{ id: 1, genre: 'Drama', rating: 7 }, { id: 2, genre: 'Sci-fi', rating: 9 },"
                            " { id: 3, genre: 'Drama', rating: 8 }];"
                            " const out = filterByGenre(data, 'Drama');"
                            " if (!Array.isArray(out)) return 'filterByGenre must return an array';"
                            " if (out.length !== 2) return 'expected 2 Drama items, got ' + out.length;"
                            " return out.every((item) => item.genre === 'Drama') ? true : 'a non-Drama item survived the filter';"
                        ),
                    },
                    {
                        "id": "filter_all_returns_everything",
                        "requirement_index": 0,
                        "label": "filterByGenre with no genre (or \"all\") returns every item",
                        "concept": "control flow",
                        "hint": "The \"All genres\" tab passes nothing — that must not filter everything away.",
                        "expression": (
                            "const data = [{ id: 1, genre: 'Drama' }, { id: 2, genre: 'Sci-fi' }];"
                            " const every = filterByGenre(data, 'all');"
                            " const none = filterByGenre(data, '');"
                            " if (!Array.isArray(every) || every.length !== 2) return '\"all\" returned ' + (every && every.length) + ' items instead of 2';"
                            " if (!Array.isArray(none) || none.length !== 2) return 'an empty genre returned ' + (none && none.length) + ' items instead of 2';"
                            " return true;"
                        ),
                    },
                    {
                        "id": "sorts_high_to_low",
                        "requirement_index": 1,
                        "label": "sortByRating orders from the highest rating to the lowest",
                        "concept": "array methods",
                        "hint": "sort((a, b) => b.rating - a.rating) — the default sort compares strings.",
                        "expression": (
                            "const data = [{ id: 1, rating: 7.2 }, { id: 2, rating: 9.1 }, { id: 3, rating: 8.4 }];"
                            " const out = sortByRating(data);"
                            " if (!Array.isArray(out) || out.length !== 3) return 'sortByRating must return all 3 items';"
                            " const order = out.map((item) => item.id).join(',');"
                            " return order === '2,3,1' ? true : 'got the order ' + order + ', expected 2,3,1 (highest rating first)';"
                        ),
                    },
                    {
                        "id": "does_not_mutate_the_caller",
                        "requirement_index": 2,
                        "label": "Neither function reorders or empties the array it was given",
                        "concept": "immutability",
                        "hint": "Array.prototype.sort mutates. Copy with slice() or [...items] before sorting.",
                        "expression": (
                            "const data = [{ id: 1, genre: 'Drama', rating: 7.2 }, { id: 2, genre: 'Sci-fi', rating: 9.1 },"
                            " { id: 3, genre: 'Drama', rating: 8.4 }];"
                            " const before = data.map((item) => item.id).join(',');"
                            " const sorted = sortByRating(data);"
                            " const filtered = filterByGenre(data, 'Drama');"
                            " const after = data.map((item) => item.id).join(',');"
                            " if (after !== before) return 'the source array came back as ' + after + ' instead of ' + before + ' — something sorted or spliced it in place';"
                            " if (sorted === data) return 'sortByRating returned the same array object it was given, not a copy';"
                            " if (filtered === data) return 'filterByGenre returned the same array object it was given, not a copy';"
                            " return true;"
                        ),
                    },
                    {
                        "id": "summarises_count_and_average",
                        "requirement_index": 3,
                        "label": "summarise reports the count and the average rating",
                        "concept": "array methods",
                        "expression": (
                            "const out = summarise([{ rating: 8 }, { rating: 9 }, { rating: 7 }]);"
                            " if (typeof out !== 'string') return 'summarise must return a string';"
                            " if (!out.includes('3')) return 'summarise returned \"' + out + '\" — the count of 3 is missing';"
                            " if (!out.includes('8')) return 'summarise returned \"' + out + '\" — the average of 8.0 is missing';"
                            " return true;"
                        ),
                    },
                    {
                        "id": "empty_list_is_survivable",
                        "requirement_index": 4,
                        "label": "summarise([]) returns a readable message rather than NaN",
                        "concept": "edge cases",
                        "hint": "Dividing a total of 0 by a length of 0 is NaN. Return early when the list is empty.",
                        "expression": (
                            "const out = summarise([]);"
                            " if (typeof out !== 'string') return 'summarise([]) must still return a string';"
                            " if (/nan/i.test(out)) return 'summarise([]) returned \"' + out + '\" — NaN reached the UI';"
                            " if (!out.trim()) return 'summarise([]) returned an empty string — say that there is nothing to show';"
                            " return true;"
                        ),
                    },
                ],
            },
        }
    ],
    "js_dom": [
        {
            "slug": "render-list",
            "title": "Render the {entity} list from data",
            "description": (
                "A {entity_plural} array is already defined in script.js. Render it into "
                "#{entity}List as .card elements, and select the container from the DOM.\n\n"
                "The stylesheet already targets a specific card shape, so use these element "
                "names or the cards will render unstyled:\n"
                "  <article class=\"card\"> wrapping an <img>, an <h3> title, a <p> meta line "
                "and a <p class=\"price\"> line."
            ),
            "requirements": [
                "Select the #{entity}List container with querySelector or getElementById",
                "Iterate over the {entity_plural} array",
                "Create a .card element per item and insert it into the container",
                "Give each card an <img> using the item's poster URL and an alt describing it",
                "Do not use document.write",
            ],
            "acceptance_criteria": [
                "The container is selected from the DOM",
                "Each item produces a .card element",
                "Cards are appended to the container",
                "Every card shows the item's poster image with alt text",
            ],
            "estimated_minutes": 35,
            "files": ["script.js"],
            "solution_files": {"script.js": JS_RENDER_LIST_SOLUTION},
            "checks": [
                {"id": "select", "type": "regex", "file": "script.js", "pattern": r"(getElementById\(|querySelector\()", "label": "Selects the container from the DOM", "concept": "querySelector", "requirement_index": 0},
                {"id": "syntax", "type": "js_syntax", "file": "script.js", "label": "script.js is valid JavaScript", "concept": "syntax", "requirement_index": None, "precondition": True},
                {"id": "iterate", "type": "regex", "file": "script.js", "pattern": r"(\.map\(|\.forEach\(|for\s*\(|for\s+of)", "label": "Iterates over the data array", "concept": "DOM updates", "requirement_index": 1},
                {"id": "card_class", "type": "regex", "file": "script.js", "pattern": r"card", "label": "Produces elements with the .card class", "concept": "DOM updates", "requirement_index": 2},
                {"id": "insert", "type": "regex", "file": "script.js", "pattern": r"(appendChild|append\(|insertAdjacentHTML|innerHTML\s*(\+?)=)", "label": "Inserts the cards into the DOM", "concept": "DOM updates", "requirement_index": 2},
                # The poster has to be a real <img> built from the item's own
                # field: a hard-coded URL, a bare `poster` mention in a comment
                # (comments are stripped) or an <img> with no alt all fail.
                {"id": "poster_element", "type": "regex", "file": "script.js", "ignore_case": True, "pattern": r"(?:<img\b[^>]*\bsrc\s*=|createElement\(\s*[\"']img[\"']\s*\)|new\s+Image\()", "label": "Each card contains an <img> element", "concept": "DOM updates", "hint": "Either put `<img src=... alt=...>` in the card markup or create it with document.createElement(\"img\").", "requirement_index": 3},
                {"id": "poster_from_data", "type": "regex", "file": "script.js", "pattern": r"(?:\.poster\b|\[\s*[\"']poster[\"']\s*\]|\{[^{}]*\bposter\b[^{}]*\}\s*(?:\)|=>|=[^=]))", "label": "The image URL comes from the item's poster field", "concept": "DOM updates", "hint": "Read `item.poster` (or destructure `poster`) instead of hard-coding one URL for every card.", "requirement_index": 3},
                {"id": "poster_alt", "type": "regex", "file": "script.js", "ignore_case": True, "pattern": r"(?:\balt\s*=\s*[\"'`][^\"'`]*[A-Za-z]|\.alt\s*=\s*[^;\n]*[A-Za-z]|setAttribute\(\s*[\"']alt[\"']\s*,\s*[^)]*[A-Za-z])", "label": "The image carries non-empty alt text", "concept": "images", "hint": "alt=\"\" tells a screen reader the picture is decorative. Describe it, e.g. alt={{`Poster for ${{item.title}}`}}.", "requirement_index": 3},
                {"id": "no_document_write", "type": "not_regex", "file": "script.js", "pattern": r"document\.write", "label": "Does not use document.write", "concept": "DOM updates", "requirement_index": 4},
            ],
        },
        {
            "slug": "selection-state",
            "title": "Implement {entity} selection and booking state",
            "description": (
                "Clicking a card selects that {entity}: the card is highlighted, the "
                "selection is recorded in state, and a summary tells the user what they "
                "have picked.\n\n"
                "Wire it with one listener on the container, not one per card. Cards are "
                "re-rendered whenever the list changes, and per-card listeners die with the "
                "elements they were attached to — delegation survives that for free. "
                "`event.target.closest(\".card\")` walks up from whatever was actually "
                "clicked (usually the poster or the title) to the card itself, and returns "
                "null for clicks that missed, which is the guard clause you need.\n\n"
                "Selection is also state a screen reader has to be able to read. A "
                "highlight colour is invisible to it, so the selected card carries "
                "`aria-pressed`, and the summary is a live region that announces itself "
                "when it changes."
            ),
            "requirements": [
                "Register a single click listener on the #{entity}List container — delegation, not one listener per card, and no inline onclick attributes",
                "Resolve the clicked card with event.target.closest(\".card\") and return early when the click landed outside a card",
                "Look the item up from the data by the card's data-id, so state holds the {entity} rather than the DOM node",
                "Keep the selection in a state object, and remove 'selected' from the previously selected card so only one is ever active",
                "Mirror the selection for assistive technology by setting aria-pressed on the card",
                "Render the current selection into a live region (aria-live) that also reads sensibly before anything is selected",
            ],
            "acceptance_criteria": [
                "One delegated listener handles every card, including cards rendered later",
                "Clicks outside a card are ignored instead of throwing",
                "Exactly one card carries the 'selected' class at a time, and state holds the item",
                "The selection is exposed through aria-pressed and announced through a live region",
            ],
            "estimated_minutes": 40,
            "files": ["script.js"],
            "solution_files": {"script.js": JS_SELECTION_SOLUTION},
            "checks": [
                {"id": "syntax", "type": "js_syntax", "file": "script.js", "label": "script.js is valid JavaScript", "concept": "syntax", "requirement_index": None, "precondition": True},
                {"id": "click", "type": "js_calls", "file": "script.js", "callee": "addEventListener", "label": "Genuinely calls addEventListener", "concept": "event listeners", "requirement_index": 0},
                {"id": "click_type", "type": "regex", "file": "script.js", "pattern": r"addEventListener\(\s*[\"']click[\"']", "label": "Registers a click listener", "concept": "event listeners", "requirement_index": 0},
                # One listener per card is the defect delegation exists to fix:
                # bind inside a loop and every re-render leaks another listener.
                {"id": "no_per_card_listeners", "type": "not_regex", "file": "script.js", "pattern": r"(?:forEach|\.map)\s*\([\s\S]{0,300}?addEventListener\s*\(\s*[\"']click[\"']", "label": "No listener is attached per card inside a loop", "concept": "event delegation", "hint": "Attach one listener to the container and read event.target inside it.", "requirement_index": 0},
                {"id": "no_inline_handlers", "type": "not_regex", "file": "script.js", "pattern": r"\bon(?:click|mousedown)\s*=", "label": "No inline onclick attributes", "concept": "event listeners", "hint": "Inline handlers put behaviour back in the markup and cannot be removed.", "requirement_index": 0},
                {"id": "uses_closest", "type": "js_calls", "file": "script.js", "callee": ".closest", "label": "Resolves the card with .closest()", "concept": "event delegation", "hint": "event.target is the <img> or <h3> that was clicked; .closest(\".card\") walks up to the card.", "requirement_index": 1},
                {"id": "guards_missed_clicks", "type": "regex", "file": "script.js", "pattern": r"closest\([^)]*\)[\s\S]{0,400}?\breturn\b", "label": "Clicks outside a card return early", "concept": "control flow", "hint": ".closest() returns null when nothing matched — `if (!card) return;` before you touch it.", "requirement_index": 1},
                {"id": "reads_data_id", "type": "regex", "file": "script.js", "pattern": r"(?:dataset\s*\.\s*id|getAttribute\(\s*[\"']data-id[\"']\s*\))", "label": "Reads the card's data-id", "concept": "datasets", "hint": "The card was rendered with data-id=\"${item.id}\" — read it back with card.dataset.id.", "requirement_index": 2},
                {"id": "looks_item_up", "type": "regex", "file": "script.js", "pattern": r"\.(?:find|filter)\s*\(", "label": "Looks the item up in the data by id", "concept": "array methods", "hint": "items.find((candidate) => candidate.id === id) — state should hold the {entity}, not the <article>.", "requirement_index": 2},
                {"id": "state_object", "type": "regex", "file": "script.js", "pattern": r"(?:const|let)\s+\w*[Ss]tate\w*\s*=\s*\{", "label": "The selection lives in a state object", "concept": "state", "hint": "`const state = { selected: null };` — one place the rest of the app can read.", "requirement_index": 3},
                {"id": "selected_class", "type": "regex", "file": "script.js", "pattern": r"classList\s*\.\s*(?:add|toggle)\(\s*[\"']selected[\"']", "label": "The active card gains the 'selected' class", "concept": "DOM updates", "requirement_index": 3},
                {"id": "clears_previous", "type": "regex", "file": "script.js", "pattern": r"classList\s*\.\s*remove\(\s*[\"']selected[\"']", "label": "The previously selected card loses the class", "concept": "DOM updates", "hint": "Without this every card you click stays highlighted, and 'selected' stops meaning anything.", "requirement_index": 3},
                {"id": "aria_pressed", "type": "regex", "file": "script.js", "pattern": r"[\"']aria-pressed[\"']", "label": "The card exposes aria-pressed", "concept": "aria", "hint": "card.setAttribute(\"aria-pressed\", isSelected ? \"true\" : \"false\") — a colour change is not announced.", "requirement_index": 4},
                {"id": "live_region", "type": "regex", "file": "script.js", "pattern": r"[\"']aria-live[\"']", "label": "The summary is a live region", "concept": "aria", "hint": "aria-live=\"polite\" makes the summary announce itself when it changes.", "requirement_index": 5},
                {"id": "summary", "type": "regex", "file": "script.js", "pattern": r"(?:textContent|innerText|innerHTML)\s*=", "label": "Writes the selection back to the DOM", "concept": "DOM updates", "requirement_index": 5},
                {"id": "summary_empty_state", "type": "regex", "file": "script.js", "pattern": r"(?:textContent|innerText|innerHTML)\s*=\s*[\s\S]{0,200}?\?[\s\S]{0,200}?:", "label": "The summary has an unselected state as well as a selected one", "concept": "control flow", "hint": "Before anything is picked the summary should still say something, e.g. \"No {entity} selected yet\".", "requirement_index": 5},
            ],
        },
    ],
    "js_async": [
        {
            "slug": "load-data",
            "title": "Load {entity_plural} asynchronously",
            "description": (
                "Replace the hard-coded array with an async loader. The interesting part is "
                "not the `await` — it is the two or three seconds before it resolves, and "
                "the case where the response comes back with nothing in it.\n\n"
                "A request has three outcomes the user can see, and all three are UI:\n"
                "  * **loading** — painted before the request goes out, so the page is never "
                "a blank rectangle;\n"
                "  * **empty** — a response that parsed fine and contained zero "
                "{entity_plural}, which is a sentence, not an empty grid;\n"
                "  * **loaded** — the cards, which must *replace* the loading state rather "
                "than appear underneath it.\n\n"
                "Write the loading and the result into the same container so the second "
                "write clears the first. (Failure is the next ticket; assume the request "
                "succeeds here.)"
            ),
            "requirements": [
                "Declare an async function that loads the {entity_plural} and awaits the request — no nested .then chains",
                "Paint a loading state into the container before the request is made",
                "Replace the loading state with the rendered cards once the data resolves",
                "Render an explicit empty state when the response contains no {entity_plural}",
                "Call the loader once at the end of the file so the page loads its own data",
            ],
            "acceptance_criteria": [
                "An async function awaits the data call instead of nesting callbacks",
                "A loading state is visible before the request and gone after it settles",
                "A response with no items produces a readable message, not an empty page",
                "The loader runs on page load",
            ],
            "estimated_minutes": 30,
            "files": ["script.js"],
            "solution_files": {"script.js": JS_ASYNC_SOLUTION},
            "checks": [
                {"id": "syntax", "type": "js_syntax", "file": "script.js", "label": "script.js is valid JavaScript", "concept": "syntax", "requirement_index": None, "precondition": True},
                {"id": "async_fn", "type": "js_async_function", "file": "script.js", "label": "Declares an async function that awaits its data call", "concept": "promises", "requirement_index": 0},
                {"id": "not_trivial", "type": "js_not_trivial", "file": "script.js", "label": "The loader has a real implementation", "concept": "async/await", "requirement_index": 0},
                {"id": "no_callback_hell", "type": "not_regex", "file": "script.js", "pattern": r"\.then\([\s\S]{0,80}\.then\([\s\S]{0,80}\.then\(", "label": "Avoids deeply nested .then chains", "concept": "async/await", "requirement_index": 0},
                # Position-aware: a DOM write before the awaited request and
                # another to the same target after it. A loading state that is
                # never cleared, or one added only after the data arrives, fails.
                {"id": "loading_sequence", "type": "js_loading_sequence", "file": "script.js", "label": "A loading state is painted before the request and replaced after it", "concept": "loading states", "hint": "Write the loading markup into the container before `await`, then overwrite the same container with the result.", "requirement_indexes": [1, 2]},
                {"id": "empty_state", "type": "regex", "file": "script.js", "pattern": r"(?:!\s*\w+(?:\.\w+)*\.length|\w+(?:\.\w+)*\.length\s*===?\s*0|\w+(?:\.\w+)*\.length\s*<\s*1)", "label": "An empty response is detected", "concept": "edge cases", "hint": "`if (items.length === 0) { ... }` — a response of [] is a valid response.", "requirement_index": 3},
                {"id": "empty_state_message", "type": "regex", "file": "script.js", "ignore_case": True, "pattern": r"(?:no|none|nothing|empty)[^<`\"']{0,40}(?:showing|available|found|yet|right now|to show|match)", "label": "The empty state says something the user can read", "concept": "empty states", "hint": "An empty grid tells the user nothing. Say \"No {entity_plural} are showing right now.\"", "requirement_index": 3},
                {"id": "invoked", "type": "regex", "file": "script.js", "pattern": r"\n\s*(?:await\s+)?\w*[Ll]oad\w*\s*\(\s*\)\s*;?", "label": "The loader is actually called", "concept": "async/await", "hint": "Declaring the function is not running it — call it at the end of the file.", "requirement_index": 4},
            ],
        }
    ],
    "js_async_error_handling": [
        {
            "slug": "resilient-loading",
            "title": "Make {entity} loading resilient to failures",
            "description": (
                "The loader currently crashes the page when the request rejects or returns a "
                "non-ok status. Handle both, and surface a user-visible error state."
            ),
            "requirements": [
                "Wrap the awaited call in try/catch, binding the error: catch (error)",
                "Check response.ok and throw/handle the failure before parsing the body",
                "Act on the caught error — logging alone is not enough",
                "Write a user-visible error message into the DOM when loading fails",
                "Keep the loading state honest: paint it before the request and replace it once the request settles, whichever way it went",
                "Give the error state a way out — a retry control the user can click, and role=\"alert\" so it is announced",
            ],
            "acceptance_criteria": [
                "A rejected promise never escapes the loader",
                "Non-ok responses are treated as errors and the body is not parsed",
                "The failure path renders an error message in the page",
                "The loading state is never left on screen after the request settles",
                "The error state is announced and offers a retry",
            ],
            "estimated_minutes": 35,
            "files": ["script.js"],
            "solution_files": {"script.js": JS_RESILIENT_SOLUTION},
            "checks": [
                {"id": "syntax", "type": "js_syntax", "file": "script.js", "label": "script.js is valid JavaScript", "concept": "syntax", "hint": "The file must parse before any behaviour can be verified.", "requirement_index": None, "precondition": True},
                {"id": "try_catch", "type": "js_try_catch_await", "file": "script.js", "require_binding": True, "label": "The awaited call runs inside try/catch (error)", "concept": "try/catch", "hint": "The await must be lexically inside the try block, and catch must bind the error.", "requirement_index": 0},
                {"id": "response_ok", "type": "js_ok_before_parse", "file": "script.js", "label": "Checks response.ok and handles it before parsing", "concept": "HTTP status codes", "hint": "Throw or handle the non-ok case before calling response.json().", "requirement_index": 1},
                {"id": "catch_handles", "type": "js_catch_handles", "file": "script.js", "label": "The catch block acts on the caught error", "concept": "promise rejection", "requirement_index": 2},
                {"id": "error_ui", "type": "js_error_feedback", "file": "script.js", "label": "Renders an error state in the DOM on failure", "concept": "promise rejection", "hint": "console.error is not user-visible — write the message into an element.", "requirement_index": 3},
                {"id": "no_dead_code", "type": "js_no_unreachable", "file": "script.js", "label": "No unreachable error handling", "concept": "control flow", "requirement_index": None},
                {"id": "loading_sequence", "type": "js_loading_sequence", "file": "script.js", "label": "The loading state is painted before the request and replaced after it", "concept": "loading states", "hint": "Write the loading markup into the container before the try block, and overwrite the same container in both the success and the catch path.", "requirement_index": 4},
                {"id": "error_is_announced", "type": "regex", "file": "script.js", "pattern": r"role\s*=\s*[\\\"']?(?:alert|status)", "label": "The error state carries role=\"alert\"", "concept": "aria", "hint": "A red box is invisible to a screen reader. role=\"alert\" makes the failure announce itself.", "requirement_index": 5},
                {"id": "retry_affordance", "type": "regex", "file": "script.js", "ignore_case": True, "pattern": r"<button[^>]*>[^<]*(?:try again|retry|reload)|(?:try again|retry|reload)[^<]*</button>", "label": "The error state offers a retry control", "concept": "empty states", "hint": "A dead end is not an error state. Render a <button> that calls the loader again.", "requirement_index": 5},
            ],
            "behaviour": ASYNC_LOADING_BEHAVIOUR,
        }
    ],
    "api_integration": [
        {
            "slug": "api-client",
            "title": "Create the API client for {entity_plural}",
            "description": (
                "Every screen that needs {entity_plural} should ask one module for them, "
                "and that module should be the only place that knows the URL, the headers "
                "and what a failure looks like.\n\n"
                "Build it around one private `request(path, options)` helper that the "
                "endpoint functions call. Two failures have to be told apart, because they "
                "read differently to the user:\n"
                "  * the request never completed — `fetch` itself rejects (offline, DNS, "
                "CORS). Only a try/catch around the `fetch` call sees this one;\n"
                "  * the request completed and the server said no — `response.ok` is false. "
                "`fetch` does *not* reject on a 404 or a 500, which is the single most "
                "common bug in hand-written clients.\n\n"
                "Throw an Error carrying the status for the second case, and keep the DOM "
                "out of this file entirely: a client that renders is a client you cannot "
                "reuse."
            ),
            "requirements": [
                "Call fetch (a real call, not a mention) to reach the API",
                "Throw or return a structured error for non-ok responses",
                "Parse the JSON body only after the status check succeeds",
                "Catch rejections with catch (error) and act on the error — an empty catch fails",
                "Keep the endpoint URLs in one place: a base-URL constant the request helper builds on",
                "Expose one function per endpoint — a list call and a single-{entity} call — rather than one function that takes a path",
                "Keep the client free of the DOM: no innerHTML, no textContent, no document lookups in this file",
            ],
            "acceptance_criteria": [
                "fetch is genuinely called",
                "Non-ok responses produce an error path before parsing",
                "JSON parsing happens only on success",
                "Every catch clause acts on the error it receives",
                "The base URL is declared once and reused",
                "The module exposes named per-endpoint functions and touches no DOM",
            ],
            "estimated_minutes": 30,
            "files": ["script.js"],
            "solution_files": {"script.js": API_CLIENT_SOLUTION},
            "checks": [
                {"id": "syntax", "type": "js_syntax", "file": "script.js", "label": "script.js is valid JavaScript", "concept": "syntax", "requirement_index": None, "precondition": True},
                {"id": "fetch", "type": "js_calls", "file": "script.js", "callee": "fetch", "label": "Calls fetch", "concept": "fetch", "hint": "The word 'fetch' in a comment or string does not count — call it.", "requirement_index": 0},
                {"id": "ok_branch", "type": "js_ok_before_parse", "file": "script.js", "label": "Branches on response status before parsing", "concept": "HTTP status codes", "requirement_indexes": [1, 2]},
                {"id": "error_carries_status", "type": "regex", "file": "script.js", "pattern": r"(?:throw\s+new\s+\w*Error|new\s+\w*Error\s*\()[\s\S]{0,200}?response\s*\.\s*status", "label": "The non-ok error carries the HTTP status", "concept": "HTTP status codes", "hint": "`throw new Error(`Request failed with status ${response.status}`)` — \"something went wrong\" is not debuggable.", "requirement_index": 1},
                {"id": "handles_error", "type": "js_catch_handles", "file": "script.js", "label": "Surfaces errors rather than swallowing them", "concept": "promise rejection", "hint": "catch must bind the error and do something with it — rethrow, return it, or show it.", "requirement_index": 3},
                {"id": "try_wraps_fetch", "type": "js_try_catch_await", "file": "script.js", "callee": "fetch", "require_binding": True, "label": "The fetch call itself runs inside try/catch (error)", "concept": "try/catch", "hint": "fetch rejects when the request never completes. response.ok never gets a chance to be false.", "requirement_index": 3},
                {"id": "base_url", "type": "regex", "file": "script.js", "pattern": r"(?:const|let)\s+[A-Z_]{3,}\w*\s*=\s*[\"'`][^\"'`]*/[^\"'`]*[\"'`]", "label": "A base-URL constant is declared", "concept": "modules", "hint": "`const BASE_URL = \"/api\";` — one edit when the API moves, not fifteen.", "requirement_index": 4},
                                # Three *functions*, not three bindings: `const response = ...`
                # inside one giant loader used to satisfy this.
                {"id": "endpoint_functions", "type": "regex", "file": "script.js", "pattern": r"(?:(?:async\s+)?function\s+\w+|(?:const|let)\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)[\s\S]*?(?:(?:async\s+)?function\s+\w+|(?:const|let)\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)[\s\S]*?(?:(?:async\s+)?function\s+\w+|(?:const|let)\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)", "label": "The client is split into a request helper plus per-endpoint functions", "concept": "modules", "hint": "One function that takes a path is not a client — give each endpoint a name.", "requirement_index": 5},
                {"id": "list_endpoint", "type": "regex", "file": "script.js", "ignore_case": True, "pattern": r"(?:async\s+)?function\s+(?:list|getAll|fetchAll|load)\w*\s*\(|(?:const|let)\s+(?:list|getAll|fetchAll|load)\w*\s*=\s*(?:async\s*)?\(", "label": "A collection endpoint function exists", "concept": "modules", "hint": "Name it for the endpoint, e.g. `async function listItems()`.", "requirement_index": 5},
                {"id": "detail_endpoint", "type": "regex", "file": "script.js", "ignore_case": True, "pattern": r"(?:async\s+)?function\s+(?:get|find|fetch|show)\w*\s*\(\s*\w+|(?:const|let)\s+(?:get|find|fetch|show)\w*\s*=\s*(?:async\s*)?\(\s*\w+", "label": "A single-item endpoint function taking an id exists", "concept": "modules", "requirement_index": 5},
                {"id": "no_dom", "type": "not_regex", "file": "script.js", "pattern": r"(?:document\s*\.|innerHTML|textContent|innerText|querySelector)", "label": "The client never touches the DOM", "concept": "separation of concerns", "hint": "Return the data and let the caller render it — that is what makes this file reusable.", "requirement_index": 6},
                {"id": "no_dead_code", "type": "js_no_unreachable", "file": "script.js", "label": "No unreachable error handling", "concept": "control flow", "requirement_index": None},
            ],
        }
    ],
    # -------------------------------------------------------------- React
    "react_fundamentals": [
        {
            "slug": "react-components",
            "title": "Convert the {entity} list to React components",
            "description": (
                "Port the vanilla listing to React without losing anything the CSS tickets "
                "bought you. That is the whole risk of this ticket: it is very easy to end "
                "up with a page of unstyled <div>s, because JSX makes it so cheap to write "
                "them.\n\n"
                "So the same rules still apply, just expressed in JSX:\n"
                "  * the landmarks stay — `<main id=\"app\">`, the listing as a `<section>` "
                "carrying the same `id` the stylesheet targets;\n"
                "  * the card is still an `<article className=\"card\">` with its poster, "
                "its `<h3>` and its meta line — `className`, not `class`;\n"
                "  * the poster is still an `<img>` with an alt built from the item's own "
                "title.\n\n"
                "One React-specific rule: `key` must come from the item's stable id. "
                "`key={index}` looks identical until the list reorders, and then React "
                "reuses the wrong DOM node and your selected card jumps."
            ),
            "requirements": [
                "Create a function component named App and export it as the default export",
                "Create a separate Card component that takes the item through props rather than reading a global",
                "Render the list with .map, giving each element a key taken from the item's id — never the array index",
                "Keep the landmarks: <main id=\"app\"> wrapping a <section id=\"{entity}List\"> for the listing",
                "Keep the card markup the stylesheet targets: <article className=\"card\"> with an <h3> title and a meta line",
                "Render each item's own poster as an <img> whose alt is built from that item's title",
                "Use className (not class) and self-close void elements — JSX is not HTML",
            ],
            "acceptance_criteria": [
                "Two components exist, App renders Card through props, and App is the default export",
                "The list is keyed by a stable id",
                "The rendered tree keeps the landmarks and class hooks the stylesheet depends on",
                "Every card shows its own poster with descriptive alt text",
            ],
            "estimated_minutes": 40,
            "files": ["App.jsx"],
            "solution_files": {"App.jsx": REACT_COMPONENTS_SOLUTION},
            "checks": [
                {"id": "syntax", "type": "js_syntax", "file": "App.jsx", "label": "App.jsx is valid JavaScript/JSX", "concept": "syntax", "requirement_index": None, "precondition": True},
                {"id": "app_component", "type": "regex", "file": "App.jsx", "pattern": r"function\s+App\s*\(|const\s+App\s*=", "label": "An App component exists", "concept": "components", "requirement_index": 0},
                {"id": "export", "type": "regex", "file": "App.jsx", "pattern": r"export\s+default", "label": "App is the default export", "concept": "components", "requirement_index": 0},
                {"id": "card_component", "type": "regex", "file": "App.jsx", "pattern": r"(?:function|const)\s+[A-Z]\w*Card\b|(?:function|const)\s+Card\b", "label": "A capitalised Card component exists", "concept": "components", "hint": "React treats a lowercase name as an HTML tag: `card` renders <card>, not your component.", "requirement_index": 1},
                {"id": "card_takes_props", "type": "regex", "file": "App.jsx", "pattern": r"(?:function|const)\s+(?:[A-Z]\w*Card|Card)\b[^\n{]*\(\s*(?:\{[^)]*\}|props)", "label": "The Card component receives its data through props", "concept": "props", "hint": "`function Card({ item })` — a component reading a module-level array cannot be reused.", "requirement_index": 1},
                {"id": "card_rendered", "type": "regex", "file": "App.jsx", "pattern": r"<(?:[A-Z]\w*Card|Card)\b", "label": "App actually renders the Card component", "concept": "composition", "requirement_index": 1},
                {"id": "map", "type": "regex", "file": "App.jsx", "pattern": r"\.map\s*\(", "label": "Renders the list with .map", "concept": "rendering", "requirement_index": 2},
                {"id": "key_from_id", "type": "regex", "file": "App.jsx", "pattern": r"key\s*=\s*\{\s*[\w.]*\bid\b", "label": "The key comes from the item's id", "concept": "reconciliation", "hint": "`key={item.id}`. An index key breaks the moment the list is filtered or sorted.", "requirement_index": 2},
                {"id": "no_index_key", "type": "not_regex", "file": "App.jsx", "pattern": r"key\s*=\s*\{\s*(?:index|i|idx)\s*\}", "label": "The key is not the array index", "concept": "reconciliation", "requirement_index": 2},
                {"id": "main_landmark", "type": "regex", "file": "App.jsx", "pattern": r"<main\b[^>]*id\s*=\s*[\"']app[\"']", "label": "<main id=\"app\"> is present", "concept": "landmarks", "hint": "The stylesheet caps and centres `main`. A <div> wrapper throws that away.", "requirement_index": 3},
                {"id": "listing_section", "type": "regex", "file": "App.jsx", "pattern": r"<section\b[^>]*id\s*=\s*[\"']\{?\w*[Ll]ist[\"'}]", "label": "The listing keeps its section id", "concept": "landmarks", "hint": "`#{entity}List` is the grid container the CSS ticket styled.", "requirement_index": 3},
                {"id": "card_article", "type": "regex", "file": "App.jsx", "pattern": r"<article\b[^>]*className\s*=\s*[\{\"'][^>]*card", "label": "The card is an <article className=\"card\">", "concept": "semantic html", "requirement_index": 4},
                {"id": "card_heading", "type": "regex", "file": "App.jsx", "pattern": r"<h3\b[^>]*>\s*\{", "label": "The card title is an <h3> bound to the item", "concept": "headings hierarchy", "requirement_index": 4},
                {"id": "poster_img", "type": "regex", "file": "App.jsx", "pattern": r"<img\b[^>]*\bsrc\s*=\s*\{[^}]*\bposter\b", "label": "The poster src comes from the item's poster field", "concept": "images", "hint": "`src={item.poster}` — one hard-coded URL for every card is not a catalogue.", "requirement_index": 5},
                {"id": "poster_alt", "type": "regex", "file": "App.jsx", "pattern": r"<img\b[^>]*\balt\s*=\s*\{[^}]*\btitle\b|<img\b[^>]*\balt\s*=\s*\{`[^`]*\$\{", "label": "The poster's alt is built from the item's title", "concept": "images", "hint": "alt={`Poster for ${item.title}`} — a static alt describes every card identically.", "requirement_index": 5},
                {"id": "uses_classname", "type": "not_regex", "file": "App.jsx", "pattern": r"<\w+[^>]*\sclass\s*=", "label": "JSX uses className, not class", "concept": "jsx", "hint": "`class` is a reserved word in JavaScript; React silently drops the attribute.", "requirement_index": 6},
                {"id": "void_elements_closed", "type": "not_regex", "file": "App.jsx", "pattern": r"<(?:img|br|input|hr)\b(?:[^>/]|/(?!>))*>", "label": "Void elements are self-closed", "concept": "jsx", "hint": "`<img ... />`. An unclosed <img> is a JSX syntax error, not a forgiving HTML quirk.", "requirement_index": 6},
            ],
        }
    ],
    "react_state": [
        {
            "slug": "react-state",
            "title": "Manage selection state with hooks",
            "description": (
                "Lift the {entity} selection into React state. The card no longer reaches "
                "out and toggles a class on itself — it is handed `isSelected` and renders "
                "accordingly, and the parent owns the truth.\n\n"
                "Three things this ticket is strict about:\n"
                "  * **State is replaced, never edited.** `seats.push(seat)` mutates the "
                "array React is already holding, so the reference does not change and "
                "nothing re-renders. `setSeats((current) => [...current, seat])` does.\n"
                "  * **Updates that read the old value take a function.** "
                "`setSeats(seats.concat(seat))` reads a value that may already be stale; "
                "the updater form never does.\n"
                "  * **The selected state is still announced.** The selected card carries "
                "`aria-pressed`, and the summary panel is a live region — the same bar the "
                "vanilla selection ticket held."
            ),
            "requirements": [
                "Hold the selected {entity} in useState in the parent, not in the card",
                "Pass the selection down as a prop (isSelected) and the handler down as an on* prop",
                "Update state immutably: no push/splice/direct assignment, and use the updater form when the new value depends on the old one",
                "Drive the card's appearance from the prop — a conditional className, not a classList call",
                "Expose the selection to assistive technology with aria-pressed on the control",
                "Render a summary panel from state, with a live region and a sensible empty state before anything is selected",
            ],
            "acceptance_criteria": [
                "useState in the parent holds the selection and the card is a pure function of its props",
                "No state value is mutated in place",
                "The selected card is styled and announced from the same piece of state",
                "The summary reads correctly both before and after a selection",
            ],
            "estimated_minutes": 40,
            "files": ["App.jsx"],
            "solution_files": {"App.jsx": REACT_STATE_SOLUTION},
            "checks": [
                {"id": "syntax", "type": "js_syntax", "file": "App.jsx", "label": "App.jsx is valid JavaScript/JSX", "concept": "syntax", "requirement_index": None, "precondition": True},
                {"id": "usestate", "type": "js_calls", "file": "App.jsx", "callee": "useState", "label": "Calls useState", "concept": "useState", "requirement_index": 0},
                {"id": "selection_state", "type": "regex", "file": "App.jsx", "pattern": r"const\s*\[\s*\w*[Ss]elect\w*\s*,\s*set\w+\s*\]\s*=\s*useState", "label": "A selection state pair is destructured from useState", "concept": "useState", "hint": "`const [selected, setSelected] = useState(null);` in App, not in the card.", "requirement_index": 0},
                {"id": "handler_prop", "type": "regex", "file": "App.jsx", "pattern": r"on[A-Z]\w*\s*=\s*\{", "label": "Passes a handler down as an on* prop", "concept": "lifting state", "requirement_index": 1},
                {"id": "selection_prop", "type": "regex", "file": "App.jsx", "pattern": r"(?:isSelected|selected)\s*=\s*\{", "label": "The selected flag is passed down as a prop", "concept": "props", "hint": "The card should not work out whether it is selected — tell it.", "requirement_index": 1},
                {"id": "no_mutation", "type": "not_regex", "file": "App.jsx", "pattern": r"(?:\bstate\s*\.\s*\w+\s*=\s*[^=]|\.push\s*\(|\.splice\s*\(|\.pop\s*\(|\.shift\s*\()", "label": "Does not mutate state directly", "concept": "immutability", "hint": "push() keeps the same array reference, so React sees no change and skips the re-render.", "requirement_index": 2},
                {"id": "updater_form", "type": "regex", "file": "App.jsx", "pattern": r"set[A-Z]\w*\s*\(\s*\(\s*\w*\s*\)\s*=>", "label": "Uses the functional updater form of a setter", "concept": "state updates", "hint": "`setSeats((current) => [...current, seat])` — reading the state variable directly can read a stale value.", "requirement_index": 2},
                {"id": "spread_update", "type": "regex", "file": "App.jsx", "pattern": r"(?:\[\s*\.\.\.|\{\s*\.\.\.)", "label": "New state is built by spreading the old value", "concept": "immutability", "requirement_index": 2},
                {"id": "conditional_class", "type": "regex", "file": "App.jsx", "pattern": r"className\s*=\s*\{[^}]*(?:\?|&&)", "label": "The card's className is derived from the prop", "concept": "conditional rendering", "hint": "`className={isSelected ? \"card card--selected\" : \"card\"}` — React owns the DOM, so do not reach for classList.", "requirement_index": 3},
                {"id": "no_classlist", "type": "not_regex", "file": "App.jsx", "pattern": r"classList\s*\.|document\s*\.\s*querySelector", "label": "No direct DOM manipulation", "concept": "rendering", "hint": "Reaching into the DOM behind React's back is how the two go out of sync.", "requirement_index": 3},
                {"id": "aria_pressed", "type": "regex", "file": "App.jsx", "pattern": r"aria-pressed\s*=\s*\{", "label": "aria-pressed is bound to the selection state", "concept": "aria", "requirement_index": 4},
                {"id": "summary_live", "type": "regex", "file": "App.jsx", "pattern": r"aria-live\s*=", "label": "The summary panel is a live region", "concept": "aria", "requirement_index": 5},
                {"id": "summary_conditional", "type": "regex", "file": "App.jsx", "pattern": r"\{\s*\w+\s*\?[\s\S]{0,600}?:\s*(?:\(|<)", "label": "The summary renders an empty state as well as a selected state", "concept": "conditional rendering", "hint": "`{selected ? (...) : (<p>Pick a {entity} to start booking.</p>)}` — `&&` alone renders nothing at all when there is no selection.", "requirement_index": 5},
            ],
        }
    ],
    "react_data_fetching": [
        {
            "slug": "react-fetching",
            "title": "Fetch {entity_plural} inside React with loading and error states",
            "description": (
                "Load the {entity_plural} in an effect and treat every outcome as UI. A "
                "component that fetches has four states, and three of them are the ones "
                "that get skipped:\n"
                "  * **loading** — the first paint, before anything has arrived;\n"
                "  * **error** — announced with role=\"alert\", not logged to a console "
                "nobody has open;\n"
                "  * **empty** — the request succeeded and returned zero {entity_plural}, "
                "which is not an error and must not render as a blank page;\n"
                "  * **loaded** — the cards.\n\n"
                "Then clean up. An effect that is still in flight when the component "
                "unmounts will call `setState` on something that no longer exists, and if "
                "the effect re-runs, a slow first response can land *after* a fast second "
                "one and overwrite fresh data with stale data. An `AbortController` "
                "cancelled from the cleanup function fixes both — and remember that "
                "aborting makes `fetch` reject with an `AbortError`, which is not a failure "
                "worth showing the user."
            ),
            "requirements": [
                "Fetch inside useEffect with an explicit dependency array",
                "Track loading and error in state, and check response.ok before parsing the body",
                "Return a cleanup function that aborts the in-flight request (AbortController or an ignore flag)",
                "Ignore the AbortError a cancelled request produces instead of rendering it as a failure",
                "Render four distinct states: loading, error, empty and loaded",
                "Make the loading and error states accessible: role=\"status\" on the loading state, role=\"alert\" on the error",
                "Keep the loaded view's markup and class hooks — <section id=\"{entity}List\"> with keyed .card articles",
            ],
            "acceptance_criteria": [
                "useEffect has an explicit dependency array and returns a cleanup function",
                "Loading, error, empty and loaded each render something different",
                "A cancelled request never renders an error",
                "The failure path is announced, and the success path keeps the styled markup",
            ],
            "estimated_minutes": 45,
            "files": ["App.jsx"],
            "solution_files": {"App.jsx": REACT_FETCH_SOLUTION},
            "checks": [
                {"id": "syntax", "type": "js_syntax", "file": "App.jsx", "label": "App.jsx is valid JavaScript/JSX", "concept": "syntax", "requirement_index": None, "precondition": True},
                {"id": "effect", "type": "js_calls", "file": "App.jsx", "callee": "useEffect", "label": "Calls useEffect", "concept": "effects", "requirement_index": 0},
                {"id": "deps", "type": "regex", "file": "App.jsx", "pattern": r"useEffect\([\s\S]*?\}\s*,\s*\[", "label": "Provides a dependency array", "concept": "effects", "hint": "No dependency array means the effect runs after every render — a fetch loop.", "requirement_index": 0},
                {"id": "loading_state", "type": "regex", "file": "App.jsx", "pattern": r"const\s*\[\s*\w*(?:[Ll]oading|[Pp]ending)\w*\s*,\s*set\w+\s*\]\s*=\s*useState", "label": "Loading is held in state", "concept": "loading/error states", "requirement_index": 1},
                {"id": "error_state", "type": "regex", "file": "App.jsx", "pattern": r"const\s*\[\s*\w*[Ee]rror\w*\s*,\s*set\w+\s*\]\s*=\s*useState", "label": "The error is held in state", "concept": "loading/error states", "requirement_index": 1},
                {"id": "ok_before_parse", "type": "js_ok_before_parse", "file": "App.jsx", "label": "Checks response.ok before parsing the body", "concept": "HTTP status codes", "hint": "fetch does not reject on a 500 — the body would parse as an error page.", "requirement_index": 1},
                {"id": "try_catch", "type": "js_try_catch_await", "file": "App.jsx", "require_binding": True, "label": "Handles request failures with try/catch (error)", "concept": "promise rejection", "requirement_index": 1},
                {"id": "catch_handles", "type": "js_catch_handles", "file": "App.jsx", "label": "The catch block acts on the caught error", "concept": "promise rejection", "requirement_index": 1},
                {"id": "cleanup", "type": "regex", "file": "App.jsx", "pattern": r"return\s*\(\s*\)\s*=>", "label": "The effect returns a cleanup function", "concept": "cleanup", "hint": "`return () => controller.abort();` — without it a slow response can overwrite a fresh one.", "requirement_index": 2},
                {"id": "abort_controller", "type": "regex", "file": "App.jsx", "pattern": r"(?:new\s+AbortController|\bignore\s*=\s*true)", "label": "The in-flight request is actually cancelled", "concept": "cleanup", "requirement_index": 2},
                {"id": "abort_signal_passed", "type": "regex", "file": "App.jsx", "pattern": r"signal\s*:\s*\w+(?:\.\w+)*|\bignore\b", "label": "The abort signal is handed to fetch", "concept": "cleanup", "hint": "Creating a controller and never passing `{ signal: controller.signal }` cancels nothing.", "requirement_index": 2},
                {"id": "abort_ignored", "type": "regex", "file": "App.jsx", "pattern": r"AbortError|\bignore\b", "label": "A cancelled request is not shown as an error", "concept": "cleanup", "hint": "abort() rejects with an AbortError. Showing it means every navigation flashes a failure.", "requirement_index": 3},
                {"id": "loading_ui", "type": "regex", "file": "App.jsx", "ignore_case": True, "pattern": r"(?:loading|spinner|skeleton)[^<]{0,60}</|>[^<]{0,60}(?:loading|please wait)", "label": "The loading state renders visible UI", "concept": "loading states", "requirement_index": 4},
                {"id": "error_ui", "type": "regex", "file": "App.jsx", "ignore_case": True, "pattern": r"role\s*=\s*[\"']alert[\"']", "label": "The error state renders an alert region", "concept": "aria", "requirement_index": 5},
                {"id": "loading_status_role", "type": "regex", "file": "App.jsx", "pattern": r"role\s*=\s*[\"']status[\"']", "label": "The loading state carries role=\"status\"", "concept": "aria", "hint": "role=\"status\" tells a screen reader the page is busy rather than empty.", "requirement_index": 5},
                {"id": "empty_state", "type": "regex", "file": "App.jsx", "pattern": r"\.length\s*===?\s*0|\.length\s*<\s*1|!\s*\w+\.length", "label": "An empty result is detected separately from an error", "concept": "empty states", "hint": "An empty list is a successful response. Say so instead of rendering nothing.", "requirement_index": 4},
                {"id": "empty_message", "type": "regex", "file": "App.jsx", "ignore_case": True, "pattern": r"(?:no|none|nothing|empty)[^<`\"']{0,40}(?:showing|available|found|yet|right now|to show|match)", "label": "The empty state says something the user can read", "concept": "empty states", "requirement_index": 4},
                {"id": "listing_section", "type": "regex", "file": "App.jsx", "pattern": r"<section\b[^>]*id\s*=\s*[\"']\{?\w*[Ll]ist[\"'}]", "label": "The loaded view keeps the listing section id", "concept": "landmarks", "requirement_index": 6},
                {"id": "card_article", "type": "regex", "file": "App.jsx", "pattern": r"<article\b[^>]*className\s*=\s*[\{\"'][^>]*card", "label": "The loaded view keeps the .card markup", "concept": "semantic html", "requirement_index": 6},
                {"id": "key_from_id", "type": "regex", "file": "App.jsx", "pattern": r"key\s*=\s*\{\s*[\w.]*\bid\b", "label": "The rendered list is keyed by the item's id", "concept": "reconciliation", "requirement_index": 6},
            ],
        }
    ],
    # ------------------------------------------------------------- Backend
    "node_basics": [
        {
            "slug": "node-server",
            "title": "Stand up the Node.js server",
            "description": "Create the HTTP server for {domain} with a health endpoint and JSON responses.",
            "requirements": [
                "Create a server module that listens on a configurable port",
                "Expose GET /health returning JSON",
                "Read the port from process.env with a default",
            ],
            "acceptance_criteria": [
                "The server listens on a port from the environment",
                "/health responds with JSON",
                "The module can be started without errors",
            ],
            "estimated_minutes": 30,
            "files": ["server.js"],
            "checks": [
                {"id": "syntax", "type": "js_syntax", "file": "server.js", "label": "server.js is valid JavaScript", "concept": "syntax", "requirement_index": None, "precondition": True},
                {"id": "listen", "type": "regex", "file": "server.js", "pattern": r"\.listen\(", "label": "Server calls listen()", "concept": "runtime", "requirement_index": 0},
                {"id": "env_port", "type": "regex", "file": "server.js", "pattern": r"process\.env", "label": "Reads the port from process.env", "concept": "modules", "requirement_index": 2},
                {"id": "health", "type": "regex", "file": "server.js", "pattern": r"[\"']/health[\"']", "label": "Defines a /health route", "concept": "routes", "requirement_index": 1},
                {"id": "json", "type": "regex", "file": "server.js", "pattern": r"(res\.json|application/json)", "label": "Responds with JSON", "concept": "routes", "requirement_index": 1},
            ],
        }
    ],
    "rest_api": [
        {
            "slug": "rest-endpoints",
            "title": "Implement the {entity} REST endpoints",
            "description": "Add list, detail and create endpoints for {entity_plural}, with validation and correct status codes.",
            "requirements": [
                "GET /api/{entity_plural} returns the collection",
                "GET /api/{entity_plural}/:id returns 404 when missing",
                "POST /api/{entity_plural} validates the body and returns 201",
                "Invalid input returns 400",
            ],
            "acceptance_criteria": [
                "All three routes exist",
                "404 is returned for unknown ids",
                "201 is returned on creation and 400 on invalid input",
            ],
            "estimated_minutes": 45,
            "files": ["server.js"],
            "checks": [
                {"id": "syntax", "type": "js_syntax", "file": "server.js", "label": "server.js is valid JavaScript", "concept": "syntax", "requirement_index": None, "precondition": True},
                {"id": "list_route", "type": "regex", "file": "server.js", "pattern": r"get\(\s*[\"']/api/\w+[\"']", "label": "Collection route exists", "concept": "routes", "requirement_index": 0},
                {"id": "detail_route", "type": "regex", "file": "server.js", "pattern": r"get\(\s*[\"']/api/\w+/:\w+[\"']", "label": "Detail route with a path param exists", "concept": "routes", "requirement_index": 1},
                {"id": "post_route", "type": "regex", "file": "server.js", "pattern": r"post\(\s*[\"']/api/\w+[\"']", "label": "Create route exists", "concept": "routes", "requirement_index": 2},
                {"id": "status_404", "type": "regex", "file": "server.js", "pattern": r"404", "label": "Returns 404 for missing resources", "concept": "status codes", "requirement_index": 1},
                {"id": "status_201", "type": "regex", "file": "server.js", "pattern": r"201", "label": "Returns 201 on creation", "concept": "status codes", "requirement_index": 2},
                {"id": "status_400", "type": "regex", "file": "server.js", "pattern": r"400", "label": "Returns 400 for invalid input", "concept": "validation", "requirement_index": 3},
            ],
        }
    ],
    "database_modeling": [
        {
            "slug": "schema",
            "title": "Model the {domain} database schema",
            "description": "Design the relational schema: {entity_plural}, users and bookings with proper keys.",
            "requirements": [
                "Create the {entity_plural} table with a primary key",
                "Create a bookings table with a foreign key",
                "Add a NOT NULL constraint where required",
                "Add an index on the foreign key column",
            ],
            "acceptance_criteria": [
                "At least two tables exist",
                "A primary key and a foreign key are declared",
                "An index exists on the relationship column",
            ],
            "estimated_minutes": 35,
            "files": ["schema.sql"],
            "checks": [
                {"id": "create_tables", "type": "regex", "file": "schema.sql", "pattern": r"CREATE\s+TABLE[\s\S]*CREATE\s+TABLE", "label": "At least two tables are created", "concept": "schemas", "ignore_case": True, "requirement_index": 0},
                {"id": "primary_key", "type": "regex", "file": "schema.sql", "pattern": r"PRIMARY\s+KEY", "label": "A primary key is declared", "concept": "schemas", "ignore_case": True, "requirement_index": 0},
                {"id": "foreign_key", "type": "regex", "file": "schema.sql", "pattern": r"(REFERENCES|FOREIGN\s+KEY)", "label": "A foreign key relationship exists", "concept": "relations", "ignore_case": True, "requirement_index": 1},
                {"id": "not_null", "type": "regex", "file": "schema.sql", "pattern": r"NOT\s+NULL", "label": "NOT NULL constraints are used", "concept": "schemas", "ignore_case": True, "requirement_index": 2},
                {"id": "index", "type": "regex", "file": "schema.sql", "pattern": r"CREATE\s+INDEX", "label": "An index is created", "concept": "indexes", "ignore_case": True, "requirement_index": 3},
            ],
        }
    ],
}

# Data-analysis templates live in their own module (their SQL fixtures are bulky
# and validated at import time) and are part of the same registry.
TICKET_TEMPLATES.update(DATA_TICKET_TEMPLATES)


SPRINT_THEMES: list[tuple[str, str, list[str]]] = [
    (
        "Foundation",
        "Structure & Markup",
        ["html_basics", "html_semantics"],
    ),
    (
        "Foundation",
        "Styling & Layout",
        ["css_basics", "css_layout", "css_responsive"],
    ),
    (
        "Interactivity",
        "Client-side Behaviour",
        ["js_basics", "js_functions", "js_dom"],
    ),
    (
        "Data Layer",
        "Async & API Integration",
        ["js_async", "js_async_error_handling", "api_integration"],
    ),
    (
        "Application",
        "React Migration",
        ["react_fundamentals", "react_state", "react_data_fetching"],
    ),
    (
        "Backend",
        "Server & Persistence",
        ["node_basics", "rest_api", "database_modeling"],
    ),
    *DATA_SPRINT_THEMES,
]


STARTER_FILES: dict[str, str] = {
    "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{domain}</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <!-- Build the structure required by this ticket. -->
    <script src="script.js"></script>
  </body>
</html>
""",
    # A scaffold, not a solution: the section order a stylesheet should be read
    # in, the token roles named, and every block left empty. Nothing here
    # satisfies a check — an untouched starter fails all of them — but a learner
    # never has to invent the structure, which is where handwritten CSS usually
    # loses its coherence. Braces are doubled for `str.format`.
    "styles.css": """/* {domain} — stylesheet.
   Work top-down: tokens, then the page shell, then the components.
   Rule of thumb: every colour and every radius comes from a token, so the
   whole theme can be re-skinned from the :root block alone. */

/* 1. Design tokens ------------------------------------------------------
   Roles to fill in (names are yours):
     --surface         the page background
     --surface-raised  header and card surfaces, a step lighter or darker
     --border          hairline separators
     --text            primary copy
     --muted           secondary copy: meta lines, taglines
     --accent          exactly one highlight colour
     --radius          corner rounding
     --font-sans       your font stack, led by a UI font                  */
:root {{
}}

/* 2. Page shell ---------------------------------------------------------
   body: background-color and color from the tokens, the font stack,
   line-height 1.5+, and margin: 0 so the shell reaches the edges.        */
body {{
}}

/* 3. Header and navigation ---------------------------------------------
   header: padding, its own surface, a bottom hairline, contents in a row.
   nav ul: display: flex, a gap, list-style: none, padding: 0.
   nav a:  your own colour, no underline, :hover and :focus-visible.      */
header {{
}}

nav ul {{
}}

nav a {{
}}

/* 4. Hero --------------------------------------------------------------
   #hero:     generous padding.
   #hero h2:  display-sized type, tight line-height.
   #hero p:   a max-width around 56ch, centred with auto margins, muted.
   #hero img: width 100%, a fixed aspect-ratio, object-fit: cover, radius. */
#hero {{
}}

/* 5. Footer ------------------------------------------------------------
   padding, a border-top, and muted text.                                */
footer {{
}}

/* 6. Components --------------------------------------------------------
   The {entity} grid and the cards land here in a later ticket.           */
""",
    # Braces are doubled because the sprint generator runs this through
    # str.format to fill {domain}/{entity_plural}: a single `{` would raise and
    # the learner would be handed the placeholders verbatim.
    "script.js": """// {domain} client script.
// Sample data you can render until the API ticket is unlocked. Each item ships a
// poster URL, so the cards can show real artwork instead of text-only boxes.
//
// The stylesheet targets this card shape, so keep the element names when you
// build the markup — otherwise the styling ticket's rules will not apply:
//
//   <article class="card">
//     <img src="..." alt="Poster for ...">
//     <h3>Title</h3>
//     <p>Genre &middot; rating</p>
//     <p class="price">From Rs 320</p>
//   </article>
const {entity_plural} = [
  {{
    id: 1,
    title: "Sample One",
    genre: "Drama",
    rating: 4.6,
    price: 12,
    poster: "https://picsum.photos/seed/{entity}-1/400/600",
  }},
  {{
    id: 2,
    title: "Sample Two",
    genre: "Thriller",
    rating: 4.2,
    price: 15,
    poster: "https://picsum.photos/seed/{entity}-2/400/600",
  }},
  {{
    id: 3,
    title: "Sample Three",
    genre: "Comedy",
    rating: 4.8,
    price: 10,
    poster: "https://picsum.photos/seed/{entity}-3/400/600",
  }},
  {{
    id: 4,
    title: "Sample Four",
    genre: "Documentary",
    rating: 4.4,
    price: 11,
    poster: "https://picsum.photos/seed/{entity}-4/400/600",
  }},
  {{
    id: 5,
    title: "Sample Five",
    genre: "Animation",
    rating: 4.7,
    price: 13,
    poster: "https://picsum.photos/seed/{entity}-5/400/600",
  }},
  {{
    id: 6,
    title: "Sample Six",
    genre: "Action",
    rating: 4.1,
    price: 14,
    poster: "https://picsum.photos/seed/{entity}-6/400/600",
  }},
];

// Implement the ticket requirements below.
""",
    # A scaffold, not a solution: the component boundaries and the markup the
    # stylesheet already targets, with every body left empty. Nothing here
    # satisfies a check — an untouched starter fails all of them — but the
    # learner does not have to rediscover which landmarks the CSS depends on.
    "App.jsx": """import React from "react";

// {domain} — React port.
//
// Keep what the styling tickets bought you. The stylesheet targets:
//   <main id="app">
//     <section id="{entity}List">        the grid container
//       <article class="card">           one card per {entity}
//         <img>  <h3>  <p>  <p class="price">
//
// In JSX that markup is the same, with two differences: `class` becomes
// `className`, and void elements close themselves (`<img ... />`).

// Declare two components below and default-export the outer one:
//
//   * a card component, rendered purely from its props. Capitalise the name —
//     React reads a lowercase name as an HTML tag, so `card` renders <card>.
//   * App, which owns the data and maps over it. Give each element a `key`
//     taken from the item's id, never the array index.
""",
    "server.js": """// {domain} API server.
// Express is assumed to be available in the target environment.
const express = require("express");
const app = express();

app.use(express.json());

// Implement the ticket requirements below.

module.exports = app;
""",
    "schema.sql": """-- {domain} database schema.
-- Implement the ticket requirements below.
""",
    **DATA_STARTER_FILES,
}
