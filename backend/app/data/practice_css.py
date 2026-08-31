"""CSS-layer practice modules.

Kept separate from `practice_modules.py` so each layer's catalogue can grow
without turning one file into a thousand-line wall. Registered by
`practice_modules.py` via `extend`, which also enforces unique ids.

Every module follows the "layer removal" model: the markup is given and locked,
and the learner writes `styles.css` only.

Strictness notes for anyone adding a module here
------------------------------------------------
`css_property` only proves that *some* rule whose selector text contains a
needle declares a property. It says nothing about the value, and nothing about
whether the rule matches an element. That is exactly the "declare an unused
class" hole, so it is used here only where a bare property is genuinely the
whole requirement.

The workhorse is a `regex` check built by `_rule()`, which ties one declaration
block to a selector that must mention a class/id that really exists in the
locked HTML, and then pins the value to a defensible range. `_media()` does the
same inside an at-rule body. Because the shipped markup is not editable, a
selector naming those hooks necessarily matches an element.
"""

from __future__ import annotations

from typing import Any

FILE = "styles.css"


# ---------------------------------------------------------------------------
# Pattern helpers
# ---------------------------------------------------------------------------


def _rule(selector: str, declaration: str) -> str:
    """A declaration inside a rule whose selector mentions `selector`.

    `[^{}]*` on both sides never crosses a brace, so the declaration proved is
    always in the *same* block as the selector — a learner cannot satisfy the
    check by putting the property on an unrelated rule. The trailing
    `(?![\\w-])` stops `.card` from being satisfied by `.card-header`.
    """
    return (
        r"(?:^|[{};])[^{}]*"
        + selector
        + r"(?![\w-])[^{}]*\{[^{}]*"
        + declaration
    )


def _base_rule(selector: str, declaration: str) -> str:
    """`_rule`, but the whole selector must be free of pseudo-classes.

    Used where the declaration only works in the element's resting state — a
    `transition` declared inside `:hover` eases one way only, and would
    otherwise satisfy a plain `_rule` check.
    """
    return (
        r"(?:^|[{};])[^{}:]*"
        + selector
        + r"(?![\w-])[^{}:]*\{[^{}]*"
        + declaration
    )


def _media(condition: str, selector: str, declaration: str) -> str:
    """`_rule` nested inside an at-rule whose prelude matches `condition`."""
    return (
        r"@media[^{]*"
        + condition
        + r"[^{]*\{(?:[^{}]*\{[^{}]*\})*?[^{}]*"
        + selector
        + r"(?![\w-])[^{}]*\{[^{}]*"
        + declaration
    )


def _decl(prop: str, value: str = r"[^;}]*\S") -> str:
    """`prop: value`, guarded so `color` is not matched by `background-color`."""
    return r"(?<![\w-])" + prop + r"\s*:\s*" + value


def _check(
    cid: str,
    requirement_index: int,
    pattern: str,
    label: str,
    concept: str,
    hint: str,
) -> dict[str, Any]:
    return {
        "id": cid,
        "requirement_index": requirement_index,
        "type": "regex",
        "file": FILE,
        "pattern": pattern,
        "ignore_case": True,
        "label": label,
        "concept": concept,
        "hint": hint,
    }


def _forbid(
    cid: str,
    requirement_index: int,
    pattern: str,
    label: str,
    concept: str,
    hint: str,
) -> dict[str, Any]:
    return {
        "id": cid,
        "requirement_index": requirement_index,
        "type": "not_regex",
        "file": FILE,
        "pattern": pattern,
        "label": label,
        "concept": concept,
        "hint": hint,
    }


def _authored() -> dict[str, Any]:
    """Precondition: the file holds real rules, not just the starter comments.

    Comments are stripped before `regex` runs, so a stylesheet of TODOs scores
    zero anyway; this exists so the learner sees *why* rather than a wall of
    unexplained red.
    """
    return {
        "id": "stylesheet_authored",
        "requirement_index": None,
        "precondition": True,
        "type": "regex",
        "file": FILE,
        "pattern": r"[^{}]+\{[^{}]*[\w-]+\s*:[^;}]+[;}]",
        "ignore_case": True,
        "label": "styles.css contains at least one complete CSS rule",
        "concept": "css syntax",
        "hint": "A rule is `selector { property: value; }`. Commented-out CSS does not count.",
    }


# Reusable value vocabularies. Ranges are wide enough that any defensible
# design passes, and narrow enough that a wrong layout does not.
_PX_8_PLUS = r"(?:(?:[89]|[1-9]\d+)px|(?:0\.[5-9]\d*|[1-9][\d.]*)rem)"
_PX_12_PLUS = r"(?:(?:1[2-9]|[2-9]\d|\d{3,})px|(?:0\.7[5-9]|0\.[89]\d*|[1-9][\d.]*)rem)"
_COLOR = r"(?:#[0-9a-f]{3,8}|rgba?\(|hsla?\(|var\(\s*--[\w-]+|[a-z]{3,})"


# ---------------------------------------------------------------------------
# Reference stylesheets
#
# Not served to the client: `practice_service.module_detail` builds its payload
# key by key and never reads `solution_files`. They exist so
# `test_every_web_module_solution_passes_its_own_checks` grades a real solution
# for every module in CI — a check that stops matching its own module is then a
# test failure rather than a silent skip.
# ---------------------------------------------------------------------------

BOX_MODEL_SOLUTION = """*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: #f5f6f8;
  font-family: system-ui, sans-serif;
}

.pricing-page {
  padding: 48px 16px;
}

.plan-card {
  max-width: 360px;
  margin: 0 auto;
  padding: 32px 28px;
  background: #fff;
  border: 1px solid #d7dae0;
  border-radius: 12px;
}

.plan-name {
  margin: 0 0 8px;
}

.plan-price {
  margin: 0 0 24px;
  font-size: 2rem;
}

.plan-features {
  list-style: none;
  padding-left: 0;
  margin: 0 0 24px;
}

.plan-feature {
  padding-bottom: 12px;
  margin-bottom: 12px;
  border-bottom: 1px solid #e6e8ec;
}

.plan-cta {
  display: inline-block;
  padding: 12px 24px;
  background: #2f6bff;
  color: #fff;
  border-radius: 8px;
  text-decoration: none;
}
"""

SELECTORS_SOLUTION = """body {
  font-family: system-ui, sans-serif;
  color: #1b1f24;
}

.nav-list {
  list-style: none;
  padding-left: 0;
}

.nav-link {
  color: #4a5560;
  text-decoration: none;
}

.nav-list > .nav-item {
  margin-bottom: 10px;
}

.nav-item.is-active .nav-link {
  color: #1140d8;
  font-weight: 700;
}

a[data-external="true"] {
  color: #0f7a5a;
  border-bottom: 1px dotted currentColor;
}

.doc p:first-of-type {
  font-size: 1.25rem;
  color: #3a434d;
}
"""

TYPOGRAPHY_SOLUTION = """body {
  font-family: "Iowan Old Style", Georgia, serif;
  line-height: 1.65;
  color: #23282e;
  margin: 0;
}

.article {
  padding: 48px 24px;
}

.article-body {
  max-width: 66ch;
}

.article-title {
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1.15;
  margin-bottom: 16px;
}

.article-lede {
  font-size: 1.25rem;
  color: #5a636d;
}

.section-title {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 1rem;
}

.pull-quote {
  font-style: italic;
  border-left: 4px solid #c9ced6;
  padding-left: 20px;
  margin-left: 0;
}
"""

VARIABLES_SOLUTION = """:root {
  --color-surface: #ffffff;
  --color-text: #171a1f;
  --color-accent: #2f6bff;
  --color-muted: #6b7480;
  --space-md: 20px;
}

[data-theme="dark"] {
  --color-surface: #0f1115;
  --color-text: #e8ebf0;
  --color-accent: #7aa2ff;
  --color-muted: #98a1ad;
}

body {
  margin: 0;
  background-color: var(--color-surface);
  color: var(--color-text);
  font-family: system-ui, sans-serif;
}

.app {
  padding: var(--space-md);
}

.stat-grid {
  display: grid;
  gap: var(--space-md);
}

.stat-card {
  background-color: var(--color-surface);
  padding: var(--space-md);
  border: 1px solid var(--color-muted);
  border-radius: 12px;
}

.stat-card__label {
  color: var(--color-muted);
  margin: 0;
}

.stat-card__value {
  color: var(--color-accent);
  font-size: 2rem;
  margin: 4px 0 0;
}
"""

FLEXBOX_SOLUTION = """body {
  margin: 0;
  font-family: system-ui, sans-serif;
}

.site-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
  border-bottom: 1px solid #dfe3e8;
}

.brand {
  flex-shrink: 0;
  font-weight: 700;
}

.search-field {
  flex-grow: 1;
  min-width: 0;
  padding: 8px 12px;
}

.nav-links {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  list-style: none;
  padding-left: 0;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}
"""

GRID_SOLUTION = """body {
  margin: 0;
  font-family: system-ui, sans-serif;
}

.dashboard {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  grid-auto-rows: minmax(160px, auto);
  gap: 20px;
  padding: 24px;
}

.panel {
  padding: 20px;
  background: #f7f8fa;
  border: 1px solid #e1e4e9;
  border-radius: 12px;
}

.panel--wide {
  grid-column: span 2;
}

.panel--tall {
  grid-row: span 2;
}
"""

POSITIONING_SOLUTION = """body {
  margin: 0;
  font-family: system-ui, sans-serif;
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e2e5ea;
}

.page {
  padding: 24px;
}

.hero {
  position: relative;
  margin: 0;
}

.hero-image {
  display: block;
  max-width: 100%;
  height: auto;
}

.badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 10px;
  background: #d92d20;
  color: #fff;
  border-radius: 999px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(12, 14, 18, 0.6);
}

.modal {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: min(90%, 420px);
  padding: 24px;
  background: #fff;
  border-radius: 12px;
}
"""

RESPONSIVE_SOLUTION = """body {
  margin: 0;
  font-family: system-ui, sans-serif;
}

.topbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
}

.nav-toggle {
  display: inline-block;
}

.desktop-nav {
  display: none;
  gap: 16px;
}

.pricing-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  padding: 20px;
}

.plan {
  border: 1px solid #e2e5ea;
  border-radius: 12px;
  padding: 16px;
}

.plan-image {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}

@media (min-width: 768px) {
  .pricing-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .desktop-nav {
    display: flex;
  }

  .nav-toggle {
    display: none;
  }
}

@media (min-width: 1024px) {
  .pricing-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
"""

TRANSITIONS_SOLUTION = """body {
  margin: 0;
  font-family: system-ui, sans-serif;
}

.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  padding: 24px;
}

.tile {
  overflow: hidden;
  border-radius: 12px;
  background: #f4f5f7;
  transition: transform 220ms ease-out, box-shadow 220ms ease-out;
}

.tile:hover {
  transform: translateY(-6px);
  box-shadow: 0 16px 32px rgba(10, 12, 16, 0.18);
}

.tile-image {
  display: block;
  width: 100%;
  height: auto;
  transition: transform 300ms ease-out;
}

.tile:hover .tile-image {
  transform: scale(1.06);
}

.tile-caption {
  padding: 12px 16px;
  margin: 0;
}

.cta-button {
  margin: 0 24px 40px;
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  background-color: #2f6bff;
  color: #fff;
  cursor: pointer;
  transition: background-color 180ms ease, transform 180ms ease;
}

.cta-button:hover {
  background-color: #1e50cc;
}

.cta-button:active {
  transform: translateY(2px);
}

@media (prefers-reduced-motion: reduce) {
  .tile,
  .tile-image,
  .cta-button {
    transition-duration: 0.01ms;
  }
}
"""

STATES_SOLUTION = """body {
  margin: 0;
  font-family: system-ui, sans-serif;
}

.ticket-form {
  max-width: 520px;
  margin: 40px auto;
  padding: 24px;
  display: grid;
  gap: 12px;
}

.field {
  padding: 10px 12px;
  border: 1px solid #c8cdd5;
  border-radius: 8px;
}

.field:focus {
  border-color: #2f6bff;
}

.required-label::after {
  content: " *";
  color: #d92d20;
}

.status-badge::before {
  content: "";
  display: inline-block;
  width: 10px;
  height: 10px;
  background-color: #f0a020;
  border-radius: 50%;
  margin-right: 8px;
}

.form-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.card-link:hover {
  text-decoration: underline;
}

.card-link:focus-visible {
  outline: 2px solid #2f6bff;
  outline-offset: 2px;
}

.action-btn {
  padding: 10px 18px;
  border: none;
  border-radius: 8px;
  background-color: #2f6bff;
  color: #fff;
  cursor: pointer;
}

.action-btn:hover {
  background-color: #1e50cc;
}

.action-btn:focus-visible {
  outline: 3px solid #0b2f8f;
  outline-offset: 3px;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
"""

# ---------------------------------------------------------------------------
# 1. Box model and spacing
# ---------------------------------------------------------------------------

PRICING_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Aurora Hosting — Pricing</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <main class="pricing-page">
      <article class="plan-card">
        <h2 class="plan-name">Team</h2>
        <p class="plan-price">$29<span class="plan-period">/month</span></p>
        <ul class="plan-features">
          <li class="plan-feature">10 projects</li>
          <li class="plan-feature">Unlimited collaborators</li>
          <li class="plan-feature">Daily backups</li>
        </ul>
        <a class="plan-cta" href="/signup">Start free trial</a>
      </article>
    </main>
  </body>
</html>
"""

BOX_MODEL_MODULE: dict[str, Any] = {
    "id": "css-box-model-pricing",
    "title": "Pricing Card — Box Model and Spacing",
    "kind": "web",
    "practice_layer": "css",
    "skill_id": "css_basics",
    "technology": "CSS",
    "difficulty": 2,
    "estimated_minutes": 20,
    "summary": (
        "The markup for a pricing card ships unstyled. Give it a predictable box "
        "model, real internal spacing, a border and a centred, capped width."
    ),
    "problem_statement": (
        "Aurora Hosting's pricing page renders as a wall of unstyled text. The "
        "markup is signed off and locked; you own styles.css only.\n\n"
        "Rebuild the card's box model. The design system says: every element sizes "
        "with border-box, the card carries 24–40px of internal padding, a 1–2px "
        "solid border and at least an 8px corner radius, and it never grows past "
        "400px — it sits centred in the page with automatic side margins. The "
        "feature list loses its bullets and its browser indent, each feature is "
        "separated by a 1px divider with at least 8px of breathing room beneath "
        "it, and the call to action becomes an inline-block with separate vertical "
        "and horizontal padding so it reads as a button, not a link."
    ),
    "constraints": [
        "Edit styles.css only — index.html is locked and must not be modified.",
        "Style the classes that already exist in the markup; do not invent new ones.",
        "The card must be capped between 320px and 400px wide (20rem–25rem is fine).",
        "Padding and radius values are graded as ranges, not exact numbers.",
        "Do not use !important.",
    ],
    "requirements": [
        "Apply box-sizing: border-box to every element with the universal selector",
        "Give .plan-card between 24px and 40px of padding",
        "Give .plan-card a 1–2px solid border and a corner radius of at least 8px",
        "Cap .plan-card between 320px and 400px wide and centre it with auto side margins",
        "Remove the bullets and the default left padding from .plan-features",
        "Separate each .plan-feature with a 1px solid bottom border and at least 8px of padding below it",
        "Render .plan-cta as an inline-block with separate vertical and horizontal padding",
    ],
    "editable_files": [FILE],
    "entry_file": "index.html",
    "files": {
        "index.html": PRICING_HTML,
        FILE: (
            "/* Aurora Hosting — pricing card.\n"
            "   index.html is locked. Build the box model here.\n"
            "   Hooks available: .pricing-page .plan-card .plan-name .plan-price\n"
            "                    .plan-features .plan-feature .plan-cta\n"
            "*/\n\n"
            "/* TODO: make every element size with border-box. */\n\n"
            "/* TODO: .plan-card — padding, border, radius, capped + centred width. */\n\n"
            "/* TODO: .plan-features — drop the markers and the browser indent. */\n\n"
            "/* TODO: .plan-feature — divider and spacing. */\n\n"
            "/* TODO: .plan-cta — make the link sit like a button. */\n"
        ),
    },
    "solution_files": {FILE: BOX_MODEL_SOLUTION},
    "checks": [
        _authored(),
        _check(
            "border_box",
            0,
            r"(?:^|[{};])\s*\*[^{}]*\{[^{}]*" + _decl("box-sizing", "border-box"),
            "The universal selector sets box-sizing: border-box",
            "box model",
            "Start the sheet with a `*` rule (often `*, *::before, *::after`) so padding "
            "and borders count inside the declared width.",
        ),
        _check(
            "card_padding",
            1,
            _rule(r"\.plan-card", _decl("padding", r"(?:(?:2[4-9]|3\d|40)px|(?:1\.[5-9]\d*|2(?:\.[0-5]\d*)?)rem)")),
            ".plan-card has 24–40px of padding",
            "box model",
            "Put the padding on .plan-card itself. A shorthand like `padding: 32px 24px` "
            "is fine as long as the first value is in range.",
        ),
        _check(
            "card_border",
            2,
            _rule(r"\.plan-card", _decl("border", r"[12]px\s+solid\s+\S")),
            ".plan-card has a 1–2px solid border",
            "box model",
            "`border: 1px solid <colour>` — the shorthand needs all three parts.",
        ),
        _check(
            "card_radius",
            2,
            _rule(r"\.plan-card", _decl("border-radius", r"(?:(?:[89]|[1-9]\d+)px|(?:0\.[5-9]\d*|[1-9][\d.]*)rem)")),
            ".plan-card has a corner radius of at least 8px",
            "box model",
            "border-radius accepts px or rem; anything from 8px up satisfies the design system.",
        ),
        _check(
            "card_max_width",
            3,
            _rule(r"\.plan-card", _decl("max-width", r"(?:(?:3[2-9]\d|400)px|2[0-5](?:\.\d+)?rem)")),
            ".plan-card is capped between 320px and 400px",
            "sizing",
            "Use max-width rather than width so the card can still shrink on a narrow screen.",
        ),
        _check(
            "card_centred",
            3,
            _rule(
                r"\.plan-card",
                r"(?:" + _decl("margin", r"(?:[^;}]*\s)?auto") + r"|" + _decl("margin-(?:left|right|inline)", r"auto") + r")",
            ),
            ".plan-card is centred with automatic side margins",
            "box model",
            "A block element with a max-width centres itself when its left and right "
            "margins are auto — `margin: 0 auto` is the usual shorthand.",
        ),
        _check(
            "list_reset",
            4,
            _rule(r"\.plan-features", _decl("list-style(?:-type)?", "none")),
            ".plan-features removes its list markers",
            "lists",
            "`list-style: none` on the <ul>, not on the individual items.",
        ),
        _check(
            "list_indent",
            4,
            _rule(r"\.plan-features", _decl(r"padding(?:-left|-inline-start)?", r"0(?![\d.])")),
            ".plan-features removes the browser's default left indent",
            "lists",
            "Browsers add ~40px of padding-left to a <ul>. Zero it out on .plan-features.",
        ),
        _check(
            "feature_divider",
            5,
            _rule(r"\.plan-feature", _decl("border-bottom", r"1px\s+solid\s+\S")),
            "Each .plan-feature has a 1px solid bottom divider",
            "box model",
            "Put the divider on the list item, not the list, so every row gets one.",
        ),
        _check(
            "feature_spacing",
            5,
            _rule(r"\.plan-feature", _decl(r"padding(?:-bottom|-block-end|-block)?", r"(?:[^;}]*\s)?" + _PX_8_PLUS)),
            "Each .plan-feature has at least 8px of padding below it",
            "spacing",
            "Text sitting directly on a divider looks cramped — add padding-bottom "
            "(or a padding shorthand whose bottom value is at least 8px).",
        ),
        _check(
            "cta_inline_block",
            6,
            _rule(r"\.plan-cta", _decl("display", r"inline-block")),
            ".plan-cta is displayed as an inline-block",
            "display",
            "An inline <a> ignores vertical padding. inline-block makes the box model apply.",
        ),
        _check(
            "cta_padding",
            6,
            _rule(r"\.plan-cta", _decl("padding", r"[\d.]+(?:px|rem|em)\s+[\d.]+(?:px|rem|em)")),
            ".plan-cta has separate vertical and horizontal padding",
            "spacing",
            "Buttons need more horizontal than vertical padding: `padding: 12px 24px`.",
        ),
        # --- rendered: the browser measures the box that was actually painted.
        {
            "id": "card_padding_rendered",
            "requirement_index": 1,
            "type": "render_computed_style",
            "selector": ".plan-card",
            "property": "padding-top",
            "min_value": 24,
            "max_value": 40,
            "label": ".plan-card renders 24–40px of top padding",
            "concept": "box model",
            "hint": (
                "This one is measured in a browser: the padding has to survive as a "
                "computed value, so an invalid or overridden declaration fails here even "
                "though the text is in the file."
            ),
        },
        {
            "id": "card_width_rendered",
            "requirement_index": 3,
            "type": "render_box",
            "selector": ".plan-card",
            "min_width": 300,
            "max_width": 400,
            "label": ".plan-card renders between 300px and 400px wide",
            "concept": "sizing",
            "hint": (
                "Measured on a 1280px-wide page. If the card still fills the window the "
                "cap is not being applied to it."
            ),
        },
        {
            "id": "card_centred_rendered",
            "requirement_index": 3,
            "type": "render_centered",
            "selector": ".plan-card",
            "axis": "horizontal",
            "label": ".plan-card is actually centred in the page",
            "concept": "box model",
            "hint": (
                "The gaps left and right of the rendered card must match. Any way of "
                "achieving that passes — auto margins, a centring parent, translate."
            ),
        },
        {
            "id": "list_reset_rendered",
            "requirement_index": 4,
            "type": "render_computed_style",
            "selector": ".plan-features",
            "property": "list-style-type",
            "value_in": ["none"],
            "label": ".plan-features renders without list markers",
            "concept": "lists",
            "hint": "The computed list-style-type has to be `none`, not merely declared.",
        },
        {
            "id": "cta_box_model_rendered",
            "requirement_index": 6,
            "type": "render_computed_style",
            "selector": ".plan-cta",
            "property": "display",
            "value_in": ["inline-block", "block", "flex", "inline-flex", "grid", "inline-grid"],
            "label": ".plan-cta renders as a box that honours vertical padding",
            "concept": "display",
            "hint": (
                "Anything but a plain `inline` box works here — inline-block is the usual "
                "choice, but flex or block are equally acceptable."
            ),
        },
    ],
}


# ---------------------------------------------------------------------------
# 2. Selectors and specificity
# ---------------------------------------------------------------------------

DOCS_NAV_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Orbit Docs</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <nav class="site-nav">
      <ul class="nav-list">
        <li class="nav-item"><a class="nav-link" href="/start">Getting started</a></li>
        <li class="nav-item is-active"><a class="nav-link" href="/api">API reference</a></li>
        <li class="nav-item"><a class="nav-link" href="/cli">CLI</a></li>
        <li class="nav-item">
          <a class="nav-link" href="https://status.orbit.dev" data-external="true">Status</a>
        </li>
      </ul>
    </nav>
    <article class="doc">
      <h1 class="doc-title">API reference</h1>
      <p>Every endpoint is versioned and returns JSON.</p>
      <p>Authentication uses a bearer token in the Authorization header.</p>
    </article>
  </body>
</html>
"""

SELECTORS_MODULE: dict[str, Any] = {
    "id": "css-selectors-specificity-nav",
    "title": "Docs Navigation — Selectors and Specificity",
    "kind": "web",
    "practice_layer": "css",
    "skill_id": "css_basics",
    "technology": "CSS",
    "difficulty": 3,
    "estimated_minutes": 22,
    "summary": (
        "Style a documentation sidebar using the right selector for each job: "
        "class, compound, child combinator, attribute and structural pseudo-class — "
        "with no id selectors and no !important."
    ),
    "problem_statement": (
        "Orbit's docs navigation needs styling, and the previous attempt was a "
        "specificity war: ids everywhere and !important on half the declarations. "
        "You are rebuilding it with the lowest-specificity selector that can do "
        "each job.\n\n"
        "Give every .nav-link a colour and strip its underline. Space the items "
        "apart using the direct-child combinator from .nav-list to .nav-item, so "
        "nested lists added later are untouched. The current page is marked with "
        "`is-active` on its <li>: use a compound selector on the active item to give "
        "its link a different colour and a weight of 600 or more — it must win on "
        "specificity, not on source order or !important. External links carry a "
        "`data-external` attribute: target them with an attribute selector. Finally, "
        "make the first paragraph of .doc stand out with a structural pseudo-class "
        "rather than a class you cannot add."
    ),
    "constraints": [
        "Edit styles.css only — index.html is locked.",
        "No id selectors (`#something`) anywhere in the stylesheet.",
        "No !important anywhere in the stylesheet.",
        "The active item must be targeted with a compound selector (.nav-item.is-active), not a lone class.",
        "The lede paragraph must be selected structurally (:first-child / :first-of-type), not by a new class.",
    ],
    "requirements": [
        "Give .nav-link a colour and remove its underline with text-decoration: none",
        "Space the items apart with a direct-child combinator (.nav-list > .nav-item)",
        "Give the active link a distinct colour via the compound selector .nav-item.is-active .nav-link",
        "Give the active link a font-weight of 600 or more",
        "Target external links with the attribute selector [data-external]",
        "Emphasise the first paragraph of .doc with a structural pseudo-class and a larger font-size",
        "Use no id selectors and no !important anywhere",
    ],
    "editable_files": [FILE],
    "entry_file": "index.html",
    "files": {
        "index.html": DOCS_NAV_HTML,
        FILE: (
            "/* Orbit Docs — navigation.\n"
            "   index.html is locked. Reach every element with selectors only.\n"
            "   Hooks: .site-nav .nav-list .nav-item .nav-item.is-active .nav-link\n"
            "          [data-external] .doc .doc-title\n"
            "   Rules: no #ids, no !important.\n"
            "*/\n\n"
            "/* TODO: base link styling. */\n\n"
            "/* TODO: item spacing via the direct-child combinator. */\n\n"
            "/* TODO: the active item, using a compound selector. */\n\n"
            "/* TODO: external links, using an attribute selector. */\n\n"
            "/* TODO: the first paragraph of .doc, using a structural pseudo-class. */\n"
        ),
    },
    "solution_files": {FILE: SELECTORS_SOLUTION},
    "checks": [
        _authored(),
        _check(
            "link_colour",
            0,
            _rule(r"\.nav-link", _decl("color", _COLOR)),
            ".nav-link declares a colour",
            "selectors",
            "A class selector on the anchor itself — links do not inherit colour from a parent.",
        ),
        _check(
            "link_underline",
            0,
            _rule(r"\.nav-link", _decl("text-decoration(?:-line)?", r"none")),
            ".nav-link removes its underline",
            "selectors",
            "`text-decoration: none` belongs on the anchor, not the list item.",
        ),
        _check(
            "child_combinator",
            1,
            r"\.nav-list\s*>\s*\.nav-item[^{}]*\{[^{}]*"
            + _decl(r"(?:margin|padding)(?:-[\w]+)?", r"(?:[^;}]*\s)?[\d.]+(?:px|rem|em)"),
            "Items are spaced via .nav-list > .nav-item",
            "combinators",
            "The `>` combinator matches only direct children. Give the item a margin or "
            "padding with a real length — a zero does not space anything.",
        ),
        _check(
            "active_colour",
            2,
            r"\.nav-item\.is-active[^{}]*\.nav-link[^{}]*\{[^{}]*" + _decl("color", _COLOR),
            "The active link is coloured via .nav-item.is-active .nav-link",
            "specificity",
            "Chain the two classes with no space (.nav-item.is-active) then descend to "
            "the link. That out-ranks the plain .nav-link rule on specificity.",
        ),
        _check(
            "active_weight",
            3,
            r"\.nav-item\.is-active[^{}]*\.nav-link[^{}]*\{[^{}]*"
            + _decl("font-weight", r"(?:[6-9]00|bold(?:er)?)"),
            "The active link is set to font-weight 600 or heavier",
            "typography",
            "600, 700 or `bold` all qualify; 500 is not enough to read as current.",
        ),
        _check(
            "attribute_selector",
            4,
            r"\[\s*data-external[^\]]*\][^{}]*\{[^{}]*[\w-]+\s*:[^;}]*\S",
            "External links are styled with the [data-external] attribute selector",
            "attribute selectors",
            "`[data-external]` matches the attribute's presence; `[data-external=\"true\"]` "
            "also works. The rule needs at least one real declaration.",
        ),
        _check(
            "structural_pseudo",
            5,
            r"\.doc[^{}]*\bp\s*:\s*(?:first-child|first-of-type)[^{}]*\{[^{}]*"
            + _decl("font-size", r"[\d.]+(?:px|rem|em|%)"),
            "The first .doc paragraph is selected structurally and given a font-size",
            "pseudo-classes",
            "`.doc p:first-child` (or :first-of-type) reaches the lede without touching "
            "the markup. Give it a larger font-size than the body copy.",
        ),
        _forbid(
            "no_ids",
            6,
            r"(?:^|[\s,>+~{}])#[a-z][\w-]*\s*[,.:\[]?[^;{}]*\{",
            "No id selectors are used",
            "specificity",
            "An id scores 100 in specificity and forces the next author to escalate. "
            "Every element here is reachable by class, attribute or position.",
        ),
        _forbid(
            "no_important",
            6,
            r"!\s*important",
            "No !important is used",
            "specificity",
            "!important is a specificity override, not a fix. Win with a compound "
            "selector instead.",
        ),
    ],
}


# ---------------------------------------------------------------------------
# 3. Typography
# ---------------------------------------------------------------------------

ARTICLE_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>The Long Read — Typography</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <article class="article">
      <h1 class="article-title">What a stylesheet owes the reader</h1>
      <p class="article-lede">
        Good typography is invisible. Bad typography is a wall of text nobody finishes.
      </p>
      <div class="article-body">
        <p>
          Line length, line height and contrast do more for readability than any
          font choice. A measure of roughly sixty characters is the classic target.
        </p>
        <h2 class="section-title">Measure and rhythm</h2>
        <p>
          Vertical rhythm comes from a consistent line-height expressed without a
          unit, so nested elements scale from their own font-size.
        </p>
        <blockquote class="pull-quote">
          Type is a beautiful group of letters, not a group of beautiful letters.
        </blockquote>
      </div>
    </article>
  </body>
</html>
"""

TYPOGRAPHY_MODULE: dict[str, Any] = {
    "id": "css-typography-longform",
    "title": "Long-form Article — Typographic Scale",
    "kind": "web",
    "practice_layer": "css",
    "skill_id": "css_basics",
    "technology": "CSS",
    "difficulty": 2,
    "estimated_minutes": 22,
    "summary": (
        "Set a readable long-form article: a font stack with a fallback, a unitless "
        "line-height, a real type scale, and a measure capped in ch units."
    ),
    "problem_statement": (
        "An editorial team is shipping long-form posts and the current default "
        "styling runs the text edge to edge in 16px Times. Make it readable.\n\n"
        "Set a font stack on <body> that names at least one family and ends in a "
        "generic fallback, and a unitless line-height between 1.5 and 1.8 so nested "
        "elements scale from their own size. Cap the measure: .article-body should "
        "be no wider than 55–75ch. Build a scale — .article-title between 2rem and "
        "3.5rem with a weight of 600 or more and a tighter line-height of at most "
        "1.3, and .article-lede larger than the body copy at 1.1rem–1.5rem with a "
        "muted colour. Section headings get uppercase letter-spacing, and the pull "
        "quote is italic with a left rule."
    ),
    "constraints": [
        "Edit styles.css only — index.html is locked.",
        "line-height on body must be unitless (1.6, not 1.6em or 26px).",
        "The measure must be expressed in ch units so it tracks the font.",
        "Font sizes are graded as ranges; use rem so the page respects user settings.",
        "Do not use !important.",
    ],
    "requirements": [
        "Give body a font stack with at least one family and a generic fallback",
        "Give body a unitless line-height between 1.5 and 1.8",
        "Cap .article-body's measure between 55ch and 75ch",
        "Size .article-title between 2rem and 3.5rem at font-weight 600 or more",
        "Tighten .article-title's line-height to 1.3 or less",
        "Size .article-lede between 1.1rem and 1.5rem and give it its own colour",
        "Give .section-title uppercase text-transform and positive letter-spacing",
        "Make .pull-quote italic with a left border rule",
    ],
    "editable_files": [FILE],
    "entry_file": "index.html",
    "files": {
        "index.html": ARTICLE_HTML,
        FILE: (
            "/* The Long Read — typography only.\n"
            "   index.html is locked.\n"
            "   Hooks: body .article .article-title .article-lede .article-body\n"
            "          .section-title .pull-quote\n"
            "*/\n\n"
            "/* TODO: body — font stack with a fallback, unitless line-height. */\n\n"
            "/* TODO: .article-body — cap the measure in ch. */\n\n"
            "/* TODO: the type scale: .article-title, .article-lede, .section-title. */\n\n"
            "/* TODO: .pull-quote. */\n"
        ),
    },
    "solution_files": {FILE: TYPOGRAPHY_SOLUTION},
    "checks": [
        _authored(),
        _check(
            "font_stack",
            0,
            _rule(
                r"(?<![\w.#-])body",
                _decl("font-family", r"[^;}]*,[^;}]*(?:serif|sans-serif|monospace|system-ui|ui-\w+)"),
            ),
            "body declares a font stack ending in a generic family",
            "typography",
            "A stack is a comma-separated list whose last entry is generic, e.g. "
            "`system-ui, -apple-system, sans-serif`. Without the fallback the page "
            "breaks wherever your first choice is missing.",
        ),
        _check(
            "line_height",
            1,
            _rule(r"(?<![\w.#-])body", _decl("line-height", r"1\.[5-8]\d*\s*[;}]")),
            "body has a unitless line-height between 1.5 and 1.8",
            "vertical rhythm",
            "Write `line-height: 1.6` with no unit — a unit freezes the value and "
            "nested elements inherit the wrong spacing.",
        ),
        _check(
            "measure",
            2,
            _rule(r"\.article-body", _decl("max-width", r"(?:5[5-9]|6\d|7[0-5])ch")),
            ".article-body caps its measure at 55–75ch",
            "measure",
            "1ch is the width of a `0` in the current font, so a ch cap keeps the line "
            "length right at any font-size. Aim for around 65ch.",
        ),
        _check(
            "title_size",
            3,
            _rule(r"\.article-title", _decl("font-size", r"(?:2|2\.\d+|3|3\.[0-5]\d*)rem")),
            ".article-title is sized between 2rem and 3.5rem",
            "type scale",
            "The headline should be clearly larger than the lede — 2.5rem is a good start.",
        ),
        _check(
            "title_weight",
            3,
            _rule(r"\.article-title", _decl("font-weight", r"(?:[6-9]00|bold(?:er)?)")),
            ".article-title is set to font-weight 600 or heavier",
            "type scale",
            "Browsers already bold an <h1>; declare the weight you actually want.",
        ),
        _check(
            "title_leading",
            4,
            _rule(r"\.article-title", _decl("line-height", r"(?:0\.\d+|1|1\.[0-3]\d*)\s*[;}]")),
            ".article-title tightens its line-height to 1.3 or less",
            "vertical rhythm",
            "Large type needs less leading than body copy, or the headline looks like "
            "two unrelated lines.",
        ),
        _check(
            "lede_size",
            5,
            _rule(r"\.article-lede", _decl("font-size", r"1\.[1-5]\d*rem")),
            ".article-lede is sized between 1.1rem and 1.5rem",
            "type scale",
            "The lede sits between the headline and the body: a step up from 1rem, "
            "nowhere near the headline.",
        ),
        _check(
            "lede_colour",
            5,
            _rule(r"\.article-lede", _decl("color", _COLOR)),
            ".article-lede declares its own colour",
            "colour",
            "A slightly muted colour separates the standfirst from the body copy.",
        ),
        _check(
            "section_transform",
            6,
            _rule(r"\.section-title", _decl("text-transform", r"uppercase")),
            ".section-title is uppercased",
            "typography",
            "`text-transform: uppercase` changes the rendering without shouting in the HTML.",
        ),
        _check(
            "section_tracking",
            6,
            _rule(r"\.section-title", _decl("letter-spacing", r"0*\.?[\d.]*[1-9][\d.]*(?:px|rem|em)")),
            ".section-title has positive letter-spacing",
            "typography",
            "Uppercase text needs extra tracking to stay legible — try 0.08em. A value "
            "of 0 does not count.",
        ),
        _check(
            "quote_italic",
            7,
            _rule(r"\.pull-quote", _decl("font-style", r"italic")),
            ".pull-quote is italic",
            "typography",
            "font-style: italic on the blockquote itself.",
        ),
        _check(
            "quote_rule",
            7,
            _rule(r"\.pull-quote", _decl("border-left", r"[\d.]+(?:px|rem|em)\s+solid\s+\S")),
            ".pull-quote has a solid left border rule",
            "box model",
            "`border-left: 4px solid <colour>` gives the quote its classic edge. Pair it "
            "with padding-left so the text is not touching the rule.",
        ),
    ],
}


# ---------------------------------------------------------------------------
# 4. Colour and custom properties
# ---------------------------------------------------------------------------

THEME_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Metrics — Themed Dashboard</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body data-theme="dark">
    <main class="app">
      <h1 class="app-title">This week</h1>
      <section class="stat-grid">
        <article class="stat-card">
          <p class="stat-card__label">Active users</p>
          <p class="stat-card__value">12,480</p>
        </article>
        <article class="stat-card">
          <p class="stat-card__label">Conversion</p>
          <p class="stat-card__value">3.4%</p>
        </article>
        <article class="stat-card">
          <p class="stat-card__label">Churn</p>
          <p class="stat-card__value">0.8%</p>
        </article>
      </section>
    </main>
  </body>
</html>
"""

VARIABLES_MODULE: dict[str, Any] = {
    "id": "css-custom-properties-theme",
    "title": "Metrics Dashboard — Design Tokens with Custom Properties",
    "kind": "web",
    "practice_layer": "css",
    "skill_id": "css_basics",
    "technology": "CSS",
    "difficulty": 3,
    "estimated_minutes": 25,
    "summary": (
        "Replace hard-coded colours with a token layer: define custom properties on "
        ":root, consume them with var(), and re-theme the whole dashboard by "
        "overriding four values on [data-theme=\"dark\"]."
    ),
    "problem_statement": (
        "The metrics dashboard is about to gain a dark theme, and today every colour "
        "is written inline in a dozen rules. Introduce a token layer instead.\n\n"
        "Declare the design tokens on :root: --color-surface, --color-text, "
        "--color-accent, --color-muted and --space-md. Consume them — <body> takes "
        "its background from the surface token and its colour from the text token, "
        ".stat-card takes its background from a token and its padding from --space-md, "
        ".stat-card__value is coloured with the accent token and .stat-card__label "
        "with the muted one. Then prove the layer works: an override block for "
        "[data-theme=\"dark\"] must redefine at least the surface and text tokens, and "
        "the whole page must re-theme without a single component rule changing."
    ),
    "constraints": [
        "Edit styles.css only — index.html is locked.",
        "Token names are fixed: --color-surface, --color-text, --color-accent, --color-muted, --space-md.",
        "Component rules must read tokens through var(); do not repeat literal colours in them.",
        "The dark theme must be an override of the token values, not a second set of component rules.",
        "Do not use !important.",
    ],
    "requirements": [
        "Define --color-surface, --color-text, --color-accent and --color-muted on :root",
        "Define a --space-md spacing token on :root",
        "Set body's background-color and color from the colour tokens with var()",
        "Give .stat-card a background-color from a token and padding from var(--space-md)",
        "Colour .stat-card__value with var(--color-accent)",
        "Colour .stat-card__label with var(--color-muted)",
        "Override at least --color-surface and --color-text inside a [data-theme=\"dark\"] block",
    ],
    "editable_files": [FILE],
    "entry_file": "index.html",
    "files": {
        "index.html": THEME_HTML,
        FILE: (
            "/* Metrics dashboard — design tokens.\n"
            "   index.html is locked. <body> already carries data-theme=\"dark\".\n"
            "   Hooks: :root [data-theme=\"dark\"] body .app .app-title\n"
            "          .stat-grid .stat-card .stat-card__label .stat-card__value\n"
            "*/\n\n"
            ":root {\n"
            "  /* TODO: --color-surface, --color-text, --color-accent, --color-muted, --space-md */\n"
            "}\n\n"
            "/* TODO: consume the tokens with var() in body and the card rules. */\n\n"
            "/* TODO: [data-theme=\"dark\"] — override token values only. */\n"
        ),
    },
    "solution_files": {FILE: VARIABLES_SOLUTION},
    "checks": [
        _authored(),
        _check(
            "root_colour_tokens",
            0,
            r":root[^{}]*\{[^{}]*--color-surface\s*:[^;}]*\S[^{}]*--color-text\s*:",
            ":root defines --color-surface and --color-text",
            "custom properties",
            "Custom properties are declared like any other property, inside a rule. "
            ":root is the document element, so tokens declared there are inherited "
            "everywhere.",
        ),
        _check(
            "root_accent_tokens",
            0,
            r":root[^{}]*\{[^{}]*--color-accent\s*:[^;}]*\S[^{}]*--color-muted\s*:",
            ":root defines --color-accent and --color-muted",
            "custom properties",
            "Declare all four colour tokens in the same :root block; order does not matter "
            "but the names must match exactly.",
        ),
        _check(
            "root_space_token",
            1,
            r":root[^{}]*\{[^{}]*--space-md\s*:\s*[\d.]+(?:px|rem|em)",
            ":root defines a --space-md length token",
            "custom properties",
            "Spacing deserves tokens too — `--space-md: 20px` keeps the rhythm consistent.",
        ),
        _check(
            "body_surface",
            2,
            _rule(r"(?<![\w.#-])body", _decl("background(?:-color)?", r"var\(\s*--color-surface")),
            "body reads its background from var(--color-surface)",
            "custom properties",
            "`background-color: var(--color-surface)` — the literal colour only ever "
            "appears in the token definition.",
        ),
        _check(
            "body_text",
            2,
            _rule(r"(?<![\w.#-])body", _decl("color", r"var\(\s*--color-text")),
            "body reads its colour from var(--color-text)",
            "custom properties",
            "Set it on body so every descendant inherits the themed text colour.",
        ),
        _check(
            "card_surface",
            3,
            _rule(r"\.stat-card", _decl("background(?:-color)?", r"var\(\s*--color-")),
            ".stat-card takes its background from a colour token",
            "custom properties",
            "Any of the colour tokens is acceptable here — what matters is that it is a "
            "var() and not a hard-coded hex.",
        ),
        _check(
            "card_padding_token",
            3,
            _rule(r"\.stat-card", _decl("padding", r"(?:[^;}]*\s)?var\(\s*--space-md")),
            ".stat-card pads itself with var(--space-md)",
            "custom properties",
            "`padding: var(--space-md)` — reusing the spacing token is what keeps cards "
            "aligned when the scale changes.",
        ),
        _check(
            "value_accent",
            4,
            _rule(r"\.stat-card__value", _decl("color", r"var\(\s*--color-accent")),
            ".stat-card__value uses var(--color-accent)",
            "custom properties",
            "The headline number is the accent; the label is not.",
        ),
        _check(
            "label_muted",
            5,
            _rule(r"\.stat-card__label", _decl("color", r"var\(\s*--color-muted")),
            ".stat-card__label uses var(--color-muted)",
            "custom properties",
            "Labels sit behind the numbers in the hierarchy — that is what the muted "
            "token is for.",
        ),
        _check(
            "dark_override",
            6,
            r"\[\s*data-theme[^\]]*\][^{}]*\{[^{}]*--color-surface\s*:[^;}]*\S[^{}]*--color-text\s*:",
            "[data-theme=\"dark\"] overrides --color-surface and --color-text",
            "theming",
            "Re-declare the token values inside `[data-theme=\"dark\"] { ... }`. Because the "
            "components read var(), nothing else has to change.",
        ),
        # --- rendered: a var() that resolves to nothing is invisible to text
        # checks but obvious to the browser, which reports the colour it painted.
        {
            "id": "body_surface_rendered",
            "requirement_index": 2,
            "type": "render_color",
            "selector": "body",
            "property": "background-color",
            "require_opaque": True,
            "max_luminance": 0.35,
            "label": "The page renders with the dark surface token applied",
            "concept": "custom properties",
            "hint": (
                "<body> carries data-theme=\"dark\", so the override must win and the "
                "painted background must be a real dark colour. A var() naming a token "
                "you never declared resolves to nothing and is caught here."
            ),
        },
        {
            "id": "body_text_rendered",
            "requirement_index": 2,
            "type": "render_color",
            "selector": "body",
            "property": "color",
            "require_opaque": True,
            "min_luminance": 0.25,
            "label": "The page text renders in the light text token",
            "concept": "custom properties",
            "hint": (
                "In the dark theme the text token has to be light enough to read against "
                "the surface. Any legible light colour passes."
            ),
        },
        {
            "id": "card_padding_rendered",
            "requirement_index": 3,
            "type": "render_computed_style",
            "selector": ".stat-card",
            "property": "padding-top",
            "min_value": 8,
            "label": ".stat-card renders the spacing token as real padding",
            "concept": "custom properties",
            "hint": (
                "`padding: var(--space-md)` only works if --space-md is a length. If the "
                "token is missing or not a length the computed padding is 0."
            ),
        },
        {
            "id": "value_accent_rendered",
            "requirement_index": 4,
            "type": "render_color",
            "selector": ".stat-card__value",
            "property": "color",
            "require_opaque": True,
            "differs_from_parent": True,
            "label": ".stat-card__value renders in a colour of its own",
            "concept": "custom properties",
            "hint": (
                "An accent that does not resolve simply inherits the body text colour, so "
                "this check compares the painted colour with the inherited one."
            ),
        },
        {
            "id": "label_muted_rendered",
            "requirement_index": 5,
            "type": "render_color",
            "selector": ".stat-card__label",
            "property": "color",
            "require_opaque": True,
            "differs_from_parent": True,
            "label": ".stat-card__label renders in a colour of its own",
            "concept": "custom properties",
            "hint": (
                "Same idea as the accent: the muted token has to resolve to something "
                "different from the inherited text colour."
            ),
        },
    ],
}


# ---------------------------------------------------------------------------
# 5. Flexbox
# ---------------------------------------------------------------------------

NAVBAR_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Fleetwise — App Shell</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="/">Fleetwise</a>
      <input class="search-field" type="search" placeholder="Search vehicles" />
      <nav class="primary-nav">
        <ul class="nav-links">
          <li><a href="/fleet">Fleet</a></li>
          <li><a href="/routes">Routes</a></li>
          <li><a href="/drivers">Drivers</a></li>
          <li><a href="/reports">Reports</a></li>
        </ul>
      </nav>
      <div class="header-actions">
        <button class="ghost-btn" type="button">Help</button>
        <button class="primary-btn" type="button">New trip</button>
      </div>
    </header>
    <main class="content">
      <p>Select a vehicle to begin.</p>
    </main>
  </body>
</html>
"""

FLEXBOX_MODULE: dict[str, Any] = {
    "id": "css-flexbox-app-header",
    "title": "App Header — Flexbox Layout",
    "kind": "web",
    "practice_layer": "css",
    "skill_id": "css_layout",
    "technology": "CSS",
    "difficulty": 3,
    "estimated_minutes": 26,
    "summary": (
        "Lay out a real application header with flexbox: a fixed brand, a search "
        "field that absorbs the leftover space, a nav that wraps, and an action "
        "group pinned to the right."
    ),
    "problem_statement": (
        "Fleetwise's header stacks vertically because nothing is laid out. Turn it "
        "into a single row with flexbox.\n\n"
        ".site-header becomes a flex row whose children are vertically centred, with "
        "a gap of at least 12px between them and enough padding to breathe. The "
        "brand must never be squashed — give it flex-shrink: 0. The search field "
        "absorbs whatever space is left: flex-grow of 1 or more, plus min-width: 0 "
        "so a long placeholder cannot push the row wider than the viewport (the "
        "classic flexbox overflow bug). .nav-links loses its bullets and becomes its "
        "own flex row that is allowed to wrap. .header-actions is a flex row of "
        "buttons pushed to the right with an auto left margin."
    ),
    "constraints": [
        "Edit styles.css only — index.html is locked.",
        "Use flexbox for the row; do not use float, absolute positioning or grid.",
        "Spacing between flex children must come from `gap`, not from per-child margins.",
        "The search field must set min-width: 0 so it can actually shrink.",
        "Do not use !important.",
    ],
    "requirements": [
        "Make .site-header a flex row with its children vertically centred",
        "Separate the header's children with a gap of at least 12px",
        "Stop .brand from shrinking with flex-shrink: 0",
        "Let .search-field absorb the leftover space with a flex-grow of 1 or more",
        "Give .search-field min-width: 0 so it can shrink below its content width",
        "Turn .nav-links into a flex row with no list markers that is allowed to wrap",
        "Push .header-actions to the right with an auto left margin and lay its buttons out in a row",
    ],
    "editable_files": [FILE],
    "entry_file": "index.html",
    "files": {
        "index.html": NAVBAR_HTML,
        FILE: (
            "/* Fleetwise — app header.\n"
            "   index.html is locked.\n"
            "   Hooks: .site-header .brand .search-field .primary-nav .nav-links\n"
            "          .header-actions .ghost-btn .primary-btn .content\n"
            "*/\n\n"
            "/* TODO: .site-header — flex row, centred, gapped, padded. */\n\n"
            "/* TODO: .brand — never shrink. */\n\n"
            "/* TODO: .search-field — grow into the leftover space, and be shrinkable. */\n\n"
            "/* TODO: .nav-links — flex row, no markers, wrap allowed. */\n\n"
            "/* TODO: .header-actions — pushed right, buttons in a row. */\n"
        ),
    },
    "solution_files": {FILE: FLEXBOX_SOLUTION},
    "checks": [
        _authored(),
        _check(
            "header_flex",
            0,
            _rule(r"\.site-header", _decl("display", r"(?:inline-)?flex")),
            ".site-header is a flex container",
            "flexbox",
            "`display: flex` on the container — the children become flex items automatically.",
        ),
        _check(
            "header_align",
            0,
            _rule(r"\.site-header", _decl("align-items", r"center")),
            ".site-header centres its children on the cross axis",
            "flexbox",
            "In a row, align-items works on the vertical axis. `center` lines the brand, "
            "field and buttons up on one baseline.",
        ),
        _check(
            "header_gap",
            1,
            _rule(r"\.site-header", _decl("gap", r"(?:[^;}]*\s)?" + _PX_12_PLUS)),
            ".site-header separates its children with a gap of 12px or more",
            "flexbox",
            "`gap` spaces flex children without adding a margin to the first or last one.",
        ),
        _check(
            "brand_no_shrink",
            2,
            _rule(
                r"\.brand",
                r"(?:" + _decl("flex-shrink", r"0(?![\d.])") + r"|" + _decl("flex", r"0\s+0\s+\S") + r")",
            ),
            ".brand is prevented from shrinking",
            "flexbox",
            "Flex items shrink by default. `flex-shrink: 0` (or `flex: 0 0 auto`) keeps "
            "the wordmark intact when the row gets tight.",
        ),
        _check(
            "search_grow",
            3,
            _rule(
                r"\.search-field",
                r"(?:" + _decl("flex-grow", r"[1-9]") + r"|" + _decl("flex", r"[1-9]") + r")",
            ),
            ".search-field grows into the leftover space",
            "flexbox",
            "`flex: 1` is shorthand for grow 1, shrink 1, basis 0 — the item takes "
            "whatever the others do not need.",
        ),
        _check(
            "search_min_width",
            4,
            _rule(r"\.search-field", _decl("min-width", r"0(?![\d.])")),
            ".search-field sets min-width: 0",
            "flexbox",
            "A flex item's default min-width is auto, so it refuses to shrink below its "
            "content and overflows the row. Setting it to 0 is the fix.",
        ),
        _check(
            "navlinks_flex",
            5,
            _rule(r"\.nav-links", _decl("display", r"(?:inline-)?flex")),
            ".nav-links is a flex row",
            "flexbox",
            "The <ul> is its own flex container; its <li> children line up horizontally.",
        ),
        _check(
            "navlinks_reset",
            5,
            _rule(r"\.nav-links", _decl("list-style(?:-type)?", r"none")),
            ".nav-links removes its list markers",
            "lists",
            "Navigation is still a list semantically; the markers just should not show.",
        ),
        _check(
            "navlinks_wrap",
            5,
            _rule(r"\.nav-links", r"(?:" + _decl("flex-wrap", r"wrap") + r"|" + _decl("flex-flow", r"[^;}]*wrap") + r")",),
            ".nav-links is allowed to wrap",
            "flexbox",
            "`flex-wrap: wrap` lets the links move to a second line instead of "
            "overflowing on a narrow window.",
        ),
        _check(
            "actions_flex",
            6,
            _rule(r"\.header-actions", _decl("display", r"(?:inline-)?flex")),
            ".header-actions lays its buttons out in a row",
            "flexbox",
            "Another small flex container — nesting them is normal and cheap.",
        ),
        _check(
            "actions_pushed_right",
            6,
            _rule(r"\.header-actions", _decl(r"margin(?:-left|-inline-start)?", r"(?:[^;}]*\s)?auto")),
            ".header-actions is pushed to the right with an auto left margin",
            "flexbox",
            "An `auto` margin absorbs all the free space on that side — it is the "
            "flexbox way to pin one item to the end without justify-content fighting "
            "the other children.",
        ),
        # --- rendered: a header that *says* flex but renders as a stack of
        # blocks (a typo'd selector, a rule trapped in @media print) fails here.
        {
            "id": "header_row_rendered",
            "requirement_index": 0,
            "type": "render_row_layout",
            "selector": ".site-header",
            "min_children": 4,
            "max_rows": 1,
            "label": "The header's children really render on one row",
            "concept": "flexbox",
            "hint": (
                "Measured from the painted boxes at 1280px: brand, search, nav and "
                "actions must sit side by side, not stacked."
            ),
        },
        {
            "id": "header_flex_rendered",
            "requirement_index": 0,
            "type": "render_computed_style",
            "selector": ".site-header",
            "property": "display",
            "value_in": ["flex", "inline-flex", "grid", "inline-grid"],
            "label": ".site-header computes to a flex (or grid) container",
            "concept": "flexbox",
            "hint": (
                "The row has to come from a real formatting context — floats cannot "
                "centre on the cross axis or honour `gap`. Grid is accepted too."
            ),
        },
        {
            "id": "search_grows_rendered",
            "requirement_index": 3,
            "type": "render_box",
            "selector": ".search-field",
            "min_width_ratio": 0.15,
            "label": ".search-field renders wide enough to have absorbed the free space",
            "concept": "flexbox",
            "hint": (
                "At 1280px an input that grows ends up far wider than its default ~170px. "
                "The threshold is deliberately loose — any real flex-grow passes."
            ),
        },
        {
            "id": "navlinks_row_rendered",
            "requirement_index": 5,
            "type": "render_row_layout",
            "selector": ".nav-links",
            "min_children": 4,
            "max_rows": 1,
            "label": "The four nav links render on one row",
            "concept": "flexbox",
            "hint": "The <li> items must sit beside each other at full width.",
        },
        {
            "id": "navlinks_markers_rendered",
            "requirement_index": 5,
            "type": "render_computed_style",
            "selector": ".nav-links",
            "property": "list-style-type",
            "value_in": ["none"],
            "label": ".nav-links renders without list markers",
            "concept": "lists",
            "hint": "The computed list-style-type must be `none`.",
        },
        {
            "id": "actions_row_rendered",
            "requirement_index": 6,
            "type": "render_row_layout",
            "selector": ".header-actions",
            "min_children": 2,
            "max_rows": 1,
            "label": "The two action buttons render side by side",
            "concept": "flexbox",
            "hint": "Help and New trip must share a row inside .header-actions.",
        },
    ],
}


# ---------------------------------------------------------------------------
# 6. CSS Grid
# ---------------------------------------------------------------------------

GRID_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Operations — Grid Dashboard</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <main class="dashboard">
      <section class="panel panel--wide">
        <h2 class="panel-title">Throughput</h2>
        <p>Requests per minute across all regions.</p>
      </section>
      <section class="panel panel--tall">
        <h2 class="panel-title">Incidents</h2>
        <p>Open incidents by severity.</p>
      </section>
      <section class="panel">
        <h2 class="panel-title">Latency</h2>
        <p>p95 response time.</p>
      </section>
      <section class="panel">
        <h2 class="panel-title">Error rate</h2>
        <p>5xx responses per minute.</p>
      </section>
      <section class="panel">
        <h2 class="panel-title">Deploys</h2>
        <p>Releases in the last 24 hours.</p>
      </section>
    </main>
  </body>
</html>
"""

GRID_MODULE: dict[str, Any] = {
    "id": "css-grid-ops-dashboard",
    "title": "Operations Dashboard — CSS Grid",
    "kind": "web",
    "practice_layer": "css",
    "skill_id": "css_layout",
    "technology": "CSS",
    "difficulty": 4,
    "estimated_minutes": 30,
    "summary": (
        "Build a fluid dashboard with CSS Grid: an auto-fitting track list with "
        "minmax, a real gutter, predictable row heights, and two panels that span "
        "extra columns and rows."
    ),
    "problem_statement": (
        "The operations dashboard renders five panels stacked in a column. Lay them "
        "out on a grid that reflows on its own — no media queries in this exercise.\n\n"
        ".dashboard becomes a grid whose columns are generated by "
        "`repeat(auto-fit, minmax(<min>, 1fr))`, so panels reflow from one column to "
        "many as the window grows without you hard-coding a count. Give it a gutter "
        "of at least 16px and a grid-auto-rows minimum so short panels do not "
        "collapse. Two panels break the rhythm: .panel--wide spans two columns and "
        ".panel--tall spans two rows. Both must degrade safely, so use `span` rather "
        "than fixed line numbers."
    ),
    "constraints": [
        "Edit styles.css only — index.html is locked.",
        "The layout must use CSS Grid; flexbox or floats will not satisfy the checks.",
        "Columns must be generated with repeat(auto-fit | auto-fill, minmax(...)) — no fixed column count.",
        "Spanning must use the `span` keyword, not absolute grid line numbers.",
        "No media queries are needed or accepted as the responsive mechanism here.",
    ],
    "requirements": [
        "Make .dashboard a grid container",
        "Generate the columns with repeat(auto-fit or auto-fill, minmax(..., 1fr))",
        "Give the grid a gutter of at least 16px",
        "Give the rows a minimum height with grid-auto-rows",
        "Make .panel--wide span two columns using the span keyword",
        "Make .panel--tall span two rows using the span keyword",
        "Give .panel internal padding of at least 16px so the content is not against the edge",
    ],
    "editable_files": [FILE],
    "entry_file": "index.html",
    "files": {
        "index.html": GRID_HTML,
        FILE: (
            "/* Operations dashboard — CSS Grid.\n"
            "   index.html is locked.\n"
            "   Hooks: .dashboard .panel .panel--wide .panel--tall .panel-title\n"
            "*/\n\n"
            "/* TODO: .dashboard — grid, auto-fitting minmax columns, gutter, row floor. */\n\n"
            "/* TODO: .panel — padding and surface. */\n\n"
            "/* TODO: .panel--wide / .panel--tall — spans. */\n"
        ),
    },
    "solution_files": {FILE: GRID_SOLUTION},
    "checks": [
        _authored(),
        _check(
            "dashboard_grid",
            0,
            _rule(r"\.dashboard", _decl("display", r"(?:inline-)?grid")),
            ".dashboard is a grid container",
            "css grid",
            "`display: grid` on the container; the panels become grid items with no "
            "extra markup.",
        ),
        _check(
            "auto_fit_columns",
            1,
            _rule(
                r"\.dashboard",
                _decl("grid-template-columns", r"repeat\(\s*auto-(?:fit|fill)\s*,\s*minmax\([^)]*,\s*1fr\s*\)"),
            ),
            "Columns are repeat(auto-fit/auto-fill, minmax(..., 1fr))",
            "css grid",
            "`repeat(auto-fit, minmax(240px, 1fr))` asks the browser to fit as many "
            "240px-or-wider columns as there is room for, then share the slack. A fixed "
            "`1fr 1fr 1fr` cannot reflow.",
        ),
        _check(
            "grid_gap",
            2,
            _rule(r"\.dashboard", _decl(r"(?:grid-)?gap", r"(?:[^;}]*\s)?(?:(?:1[6-9]|[2-9]\d|\d{3,})px|(?:1|1\.\d+|[2-9][\d.]*)rem)")),
            ".dashboard has a gutter of at least 16px",
            "css grid",
            "`gap: 20px` spaces rows and columns at once. Margins on grid items do not "
            "collapse the way you want here.",
        ),
        _check(
            "auto_rows",
            3,
            _rule(r"\.dashboard", _decl("grid-auto-rows", r"[^;}]*\S")),
            ".dashboard sets a minimum row height with grid-auto-rows",
            "css grid",
            "`grid-auto-rows: minmax(160px, auto)` gives implicit rows a floor while "
            "still letting tall content expand them.",
        ),
        _check(
            "wide_span",
            4,
            _rule(r"\.panel--wide", _decl("grid-column", r"[^;}]*span\s+2")),
            ".panel--wide spans two columns with the span keyword",
            "css grid",
            "`grid-column: span 2` is placement-independent, so it still works after the "
            "grid reflows. Line numbers like `1 / 3` break at narrow widths.",
        ),
        _check(
            "tall_span",
            5,
            _rule(r"\.panel--tall", _decl("grid-row", r"[^;}]*span\s+2")),
            ".panel--tall spans two rows with the span keyword",
            "css grid",
            "`grid-row: span 2` — the row axis works exactly like the column axis.",
        ),
        _check(
            "panel_padding",
            6,
            _rule(r"\.panel", _decl("padding", r"(?:[^;}]*\s)?(?:(?:1[6-9]|[2-9]\d|\d{3,})px|(?:1|1\.\d+|[2-9][\d.]*)rem)")),
            ".panel has at least 16px of internal padding",
            "spacing",
            "Grid controls the gaps between panels; the panel still owns the space "
            "inside its own border.",
        ),
        # --- rendered: the two viewports together are what make "it reflows on
        # its own" checkable. A hard-coded `1fr 1fr 1fr` renders three columns at
        # both widths and fails the narrow one.
        {
            "id": "grid_columns_wide_rendered",
            "requirement_index": 1,
            "type": "render_grid_columns",
            "selector": ".dashboard",
            "viewport": {"width": 1280, "height": 900},
            "min": 3,
            "label": ".dashboard renders at least three columns on a wide window",
            "concept": "css grid",
            "hint": (
                "Measured from the track list the browser generated at 1280px. If your "
                "minmax minimum is very large the grid cannot fit three columns."
            ),
        },
        {
            "id": "grid_columns_narrow_rendered",
            "requirement_index": 1,
            "type": "render_grid_columns",
            "selector": ".dashboard",
            "viewport": {"width": 420, "height": 900},
            "max": 2,
            "label": ".dashboard collapses to one or two columns on a narrow window",
            "concept": "css grid",
            "hint": (
                "This is what auto-fit + minmax buys you: the same stylesheet reflows. A "
                "fixed column count renders the same everywhere and fails here."
            ),
        },
        {
            "id": "panels_row_rendered",
            "requirement_index": 0,
            "type": "render_row_layout",
            "selector": ".dashboard",
            "min_children": 5,
            "min_row_pairs": 2,
            "label": "The panels really sit beside each other on the grid",
            "concept": "css grid",
            "hint": (
                "Five stacked blocks means nothing laid them out. At least three panels "
                "must share a row at 1280px."
            ),
        },
        {
            "id": "panel_padding_rendered",
            "requirement_index": 6,
            "type": "render_computed_style",
            "selector": ".panel",
            "property": "padding-top",
            "min_value": 16,
            "all_match": True,
            "label": "Every .panel renders at least 16px of top padding",
            "concept": "spacing",
            "hint": (
                "Every panel is measured, so a rule that only reaches some of them (or an "
                "invalid value that computes to 0) is caught."
            ),
        },
        {
            "id": "panels_visible_rendered",
            "requirement_index": 3,
            "type": "render_visible",
            "selector": ".panel",
            "min_height": 100,
            "non_empty": True,
            "label": "Panels render with a real height and visible content",
            "concept": "css grid",
            "hint": (
                "grid-auto-rows gives short panels a floor. A panel that renders a few "
                "pixels tall, or with nothing in it, fails."
            ),
        },
    ],
}


# ---------------------------------------------------------------------------
# 7. Positioning and stacking context
# ---------------------------------------------------------------------------

POSITION_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Northwind Store — Product</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <header class="site-header">
      <span class="brand">Northwind</span>
      <button class="cart-btn" type="button">Cart</button>
    </header>
    <main class="page">
      <figure class="hero">
        <img class="hero-image" src="https://picsum.photos/seed/nw/900/500" alt="Trail runner shoe" />
        <span class="badge">New</span>
        <figcaption class="hero-caption">Trailhead GTX</figcaption>
      </figure>
      <p class="blurb">A long paragraph of product copy goes here, repeated enough to scroll.</p>
      <p class="blurb">A long paragraph of product copy goes here, repeated enough to scroll.</p>
      <p class="blurb">A long paragraph of product copy goes here, repeated enough to scroll.</p>
    </main>
    <div class="modal-overlay">
      <div class="modal">
        <h2 class="modal-title">Size guide</h2>
        <p>Measure your foot from heel to toe.</p>
      </div>
    </div>
  </body>
</html>
"""

POSITIONING_MODULE: dict[str, Any] = {
    "id": "css-positioning-stacking",
    "title": "Product Page — Positioning and Stacking Order",
    "kind": "web",
    "practice_layer": "css",
    "skill_id": "css_layout",
    "technology": "CSS",
    "difficulty": 4,
    "estimated_minutes": 28,
    "summary": (
        "Pin a badge to a hero image, make the header stick, and centre a modal over "
        "a full-viewport overlay — with a z-index scale that is deliberate rather "
        "than a pile of 9999s."
    ),
    "problem_statement": (
        "Three overlay bugs on the Northwind product page all come from the same "
        "gap: nothing establishes a containing block, and z-index is guesswork.\n\n"
        "Make .hero a positioned ancestor so .badge can be absolutely positioned "
        "against it with top and right offsets — right now the badge escapes to the "
        "page corner. Make .site-header sticky at the top of the viewport. Then fix "
        "the stacking scale: the header sits on a z-index between 10 and 99, and the "
        ".modal-overlay — which is fixed and covers the whole viewport with all four "
        "offsets at 0 — sits at 100 or more so it is unambiguously above the header. "
        "Centre .modal inside the overlay with the top/left 50% plus "
        "translate(-50%, -50%) technique."
    ),
    "constraints": [
        "Edit styles.css only — index.html is locked.",
        "The badge must be positioned against .hero, so .hero needs position: relative.",
        "z-index scale is fixed by this exercise: .site-header 10–99, .modal-overlay 100 or more.",
        "The overlay must cover the viewport via all four offsets (or inset: 0), not a 100vw/100vh size.",
        "Centre the modal with transform: translate(-50%, -50%), not with flexbox.",
    ],
    "requirements": [
        "Give .hero position: relative so it becomes the badge's containing block",
        "Position .badge absolutely with top and right offsets",
        "Make .site-header sticky with top: 0",
        "Give .site-header a z-index between 10 and 99",
        "Make .modal-overlay fixed and cover the viewport with all four offsets at 0 (or inset: 0)",
        "Give .modal-overlay a z-index of 100 or more so it sits above the header",
        "Centre .modal with top/left 50% and transform: translate(-50%, -50%)",
    ],
    "editable_files": [FILE],
    "entry_file": "index.html",
    "files": {
        "index.html": POSITION_HTML,
        FILE: (
            "/* Northwind — positioning and stacking.\n"
            "   index.html is locked.\n"
            "   Hooks: .site-header .brand .cart-btn .page .hero .hero-image .badge\n"
            "          .hero-caption .blurb .modal-overlay .modal .modal-title\n"
            "   Scale: header z-index 10-99, overlay z-index 100+.\n"
            "*/\n\n"
            "/* TODO: .hero — establish the containing block. */\n\n"
            "/* TODO: .badge — pin to the top-right of the hero. */\n\n"
            "/* TODO: .site-header — stick to the top, with its layer in the scale. */\n\n"
            "/* TODO: .modal-overlay — fixed, full viewport, above the header. */\n\n"
            "/* TODO: .modal — centred on the overlay. */\n"
        ),
    },
    "solution_files": {FILE: POSITIONING_SOLUTION},
    "checks": [
        _authored(),
        _check(
            "hero_relative",
            0,
            _rule(r"\.hero", _decl("position", r"relative")),
            ".hero is position: relative",
            "containing block",
            "An absolutely positioned child is placed against its nearest positioned "
            "ancestor. Without this, the badge is placed against the viewport.",
        ),
        _check(
            "badge_absolute",
            1,
            _rule(r"\.badge", _decl("position", r"absolute")),
            ".badge is position: absolute",
            "positioning",
            "Absolute takes the badge out of flow so it can sit on top of the image.",
        ),
        _check(
            "badge_offsets",
            1,
            _rule(r"\.badge", _decl(r"top", r"[\d.]+(?:px|rem|em|%)") + r"[^{}]*" + _decl(r"right", r"[\d.]+(?:px|rem|em|%)")),
            ".badge sets top and right offsets",
            "positioning",
            "`position: absolute` alone leaves the element at its static position — you "
            "must also say where. Declare both top and right.",
        ),
        _check(
            "header_sticky",
            2,
            _rule(r"\.site-header", _decl("position", r"sticky")),
            ".site-header is position: sticky",
            "positioning",
            "Sticky behaves as relative until the scroll threshold, then as fixed — no "
            "layout jump, unlike position: fixed.",
        ),
        _check(
            "header_top",
            2,
            _rule(r"\.site-header", _decl("top", r"0(?![\d.])")),
            ".site-header declares top: 0",
            "positioning",
            "A sticky element without a threshold never sticks. `top: 0` is the threshold.",
        ),
        _check(
            "header_layer",
            3,
            _rule(r"\.site-header", _decl("z-index", r"[1-9]\d(?![\d.])")),
            ".site-header has a z-index between 10 and 99",
            "stacking context",
            "Pick a deliberate layer from the scale in the brief (e.g. 20). z-index only "
            "applies to positioned elements, which sticky is.",
        ),
        _check(
            "overlay_fixed",
            4,
            _rule(r"\.modal-overlay", _decl("position", r"fixed")),
            ".modal-overlay is position: fixed",
            "positioning",
            "Fixed anchors to the viewport, so the overlay stays put while the page "
            "behind it scrolls.",
        ),
        _check(
            "overlay_inset",
            4,
            _rule(
                r"\.modal-overlay",
                r"(?:"
                + _decl("inset", r"0(?![\d.])")
                + r"|"
                + _decl("top", r"0(?![\d.])")
                + r"[^{}]*"
                + _decl("bottom", r"0(?![\d.])")
                + r")",
            ),
            ".modal-overlay covers the viewport with zeroed offsets",
            "positioning",
            "`inset: 0` (or top/right/bottom/left all 0) stretches a fixed element to the "
            "whole viewport, and unlike 100vw it does not overflow when a scrollbar is "
            "present.",
        ),
        _check(
            "overlay_layer",
            5,
            _rule(r"\.modal-overlay", _decl("z-index", r"[1-9]\d{2,}(?![\d.])")),
            ".modal-overlay has a z-index of 100 or more",
            "stacking context",
            "The overlay must out-rank the sticky header's layer. Use the scale in the "
            "brief rather than reaching for 9999.",
        ),
        _check(
            "modal_offsets",
            6,
            _rule(r"\.modal", _decl("top", r"50%") + r"[^{}]*" + _decl("left", r"50%")),
            ".modal is offset to top: 50% and left: 50%",
            "positioning",
            "50%/50% puts the modal's top-left corner at the centre — the transform then "
            "pulls it back by half its own size.",
        ),
        _check(
            "modal_translate",
            6,
            _rule(r"\.modal", _decl("transform", r"[^;}]*translate\w*\(\s*-50%\s*,\s*-50%")),
            ".modal is pulled back with translate(-50%, -50%)",
            "transforms",
            "Percentages in `translate` resolve against the element's own size, which is "
            "why this centres an element of unknown dimensions.",
        ),
    ],
}


# ---------------------------------------------------------------------------
# 8. Responsive design with media queries
# ---------------------------------------------------------------------------

RESPONSIVE_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Cadence — Plans</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <header class="topbar">
      <span class="brand">Cadence</span>
      <button class="nav-toggle" type="button" aria-label="Menu">Menu</button>
      <nav class="desktop-nav">
        <a href="/features">Features</a>
        <a href="/pricing">Pricing</a>
        <a href="/docs">Docs</a>
      </nav>
    </header>
    <main>
      <section class="pricing-grid">
        <article class="plan">
          <img class="plan-image" src="https://picsum.photos/seed/a/600/300" alt="Solo plan" />
          <h2>Solo</h2>
          <p>$9 / month</p>
        </article>
        <article class="plan">
          <img class="plan-image" src="https://picsum.photos/seed/b/600/300" alt="Team plan" />
          <h2>Team</h2>
          <p>$29 / month</p>
        </article>
        <article class="plan">
          <img class="plan-image" src="https://picsum.photos/seed/c/600/300" alt="Scale plan" />
          <h2>Scale</h2>
          <p>$79 / month</p>
        </article>
      </section>
    </main>
  </body>
</html>
"""

RESPONSIVE_MODULE: dict[str, Any] = {
    "id": "css-responsive-pricing-grid",
    "title": "Pricing Page — Mobile-first Responsive Layout",
    "kind": "web",
    "practice_layer": "css",
    "skill_id": "css_responsive",
    "technology": "CSS",
    "difficulty": 4,
    "estimated_minutes": 28,
    "summary": (
        "Write a genuinely mobile-first stylesheet: one column by default, two "
        "columns from 768px, three from 1024px, fluid images, and a nav that swaps "
        "between a menu button and inline links."
    ),
    "problem_statement": (
        "Cadence's pricing page was written desktop-first with max-width queries and "
        "it collapses on a phone. Rewrite it mobile-first.\n\n"
        "The base rules — the ones outside every media query — describe the phone: "
        ".pricing-grid is a single-column grid, .desktop-nav is hidden and "
        ".nav-toggle is shown. Then layer on min-width queries only: at 768px (48em "
        "is equivalent and accepted) the grid goes to two columns and the desktop "
        "nav becomes visible while the toggle is hidden; at 1024px (64em) the grid "
        "goes to three columns. Images must be fluid everywhere: max-width 100% with "
        "height auto so they scale without distorting. A max-width media query "
        "anywhere in the file fails the exercise — the point is that a mobile-first "
        "sheet only ever adds."
    ),
    "constraints": [
        "Edit styles.css only — index.html is locked.",
        "Mobile-first: every media query must use min-width. No max-width queries at all.",
        "Breakpoints are 768px (or 48em) and 1024px (or 64em).",
        "The single-column, toggle-visible layout must be the base rules, not a query.",
        "Images must be fluid (max-width: 100% and height: auto), never fixed pixel widths.",
    ],
    "requirements": [
        "Make .pricing-grid a single-column grid in the base (mobile) rules",
        "Hide .desktop-nav and show .nav-toggle in the base rules",
        "Make .plan-image fluid with max-width: 100% and height: auto",
        "At a min-width of 768px (or 48em), give .pricing-grid two columns",
        "At the 768px breakpoint, reveal .desktop-nav and hide .nav-toggle",
        "At a min-width of 1024px (or 64em), give .pricing-grid three columns",
        "Use min-width queries only — no max-width media queries anywhere",
    ],
    "editable_files": [FILE],
    "entry_file": "index.html",
    "files": {
        "index.html": RESPONSIVE_HTML,
        FILE: (
            "/* Cadence — mobile-first pricing page.\n"
            "   index.html is locked.\n"
            "   Hooks: .topbar .brand .nav-toggle .desktop-nav .pricing-grid .plan .plan-image\n"
            "   Breakpoints: min-width 768px (48em) and 1024px (64em). min-width only.\n"
            "*/\n\n"
            "/* TODO: base = phone. One column, toggle visible, desktop nav hidden. */\n\n"
            "/* TODO: fluid images. */\n\n"
            "/* TODO: @media (min-width: 768px) — two columns, nav swap. */\n\n"
            "/* TODO: @media (min-width: 1024px) — three columns. */\n"
        ),
    },
    "solution_files": {FILE: RESPONSIVE_SOLUTION},
    "checks": [
        _authored(),
        _check(
            "base_single_column",
            0,
            _rule(r"\.pricing-grid", _decl("grid-template-columns", r"(?:1fr|repeat\(\s*1\s*,|minmax\()\s*[^;}]*")),
            ".pricing-grid is a single column in the base rules",
            "mobile first",
            "Write the phone layout with no query around it: "
            "`grid-template-columns: 1fr`. Everything else is an enhancement.",
        ),
        _check(
            "base_grid_display",
            0,
            _rule(r"\.pricing-grid", _decl("display", r"(?:inline-)?grid")),
            ".pricing-grid is a grid container",
            "css grid",
            "The column count is a grid property, so the container needs display: grid.",
        ),
        _check(
            "base_nav_hidden",
            1,
            _rule(r"\.desktop-nav", _decl("display", r"none")),
            ".desktop-nav is hidden by default",
            "mobile first",
            "On a phone the inline links do not fit — hide them in the base rules and "
            "bring them back at the breakpoint.",
        ),
        _check(
            "base_toggle_shown",
            1,
            _rule(r"\.nav-toggle", _decl("display", r"(?:block|inline-block|(?:inline-)?flex|inline)")),
            ".nav-toggle is displayed by default",
            "mobile first",
            "Declare the toggle's display explicitly so the desktop rule has something "
            "to override.",
        ),
        _check(
            "fluid_image_width",
            2,
            _rule(r"\.plan-image", _decl("max-width", r"100%")),
            ".plan-image is capped at 100% of its container",
            "responsive images",
            "`max-width: 100%` stops an intrinsically wide image from forcing a "
            "horizontal scrollbar.",
        ),
        _check(
            "fluid_image_height",
            2,
            _rule(r"\.plan-image", _decl("height", r"auto")),
            ".plan-image keeps its aspect ratio with height: auto",
            "responsive images",
            "Without `height: auto` the intrinsic height is kept and the image squashes.",
        ),
        _check(
            "tablet_two_columns",
            3,
            _media(
                r"min-width\s*:\s*(?:768px|48r?em)",
                r"\.pricing-grid",
                _decl("grid-template-columns", r"(?:repeat\(\s*2\s*,|1fr\s+1fr\s*[;}])"),
            ),
            "At min-width 768px, .pricing-grid becomes two columns",
            "media queries",
            "`@media (min-width: 768px) { .pricing-grid { grid-template-columns: repeat(2, 1fr); } }`. "
            "The declaration has to be inside the query, on .pricing-grid.",
        ),
        _check(
            "tablet_nav_shown",
            4,
            _media(
                r"min-width\s*:\s*(?:768px|48r?em)",
                r"\.desktop-nav",
                _decl("display", r"(?:block|(?:inline-)?flex|inline-block|grid)"),
            ),
            "At min-width 768px, .desktop-nav becomes visible",
            "media queries",
            "Override the base `display: none` inside the query — flex is a good choice "
            "for a row of links.",
        ),
        _check(
            "tablet_toggle_hidden",
            4,
            _media(r"min-width\s*:\s*(?:768px|48r?em)", r"\.nav-toggle", _decl("display", r"none")),
            "At min-width 768px, .nav-toggle is hidden",
            "media queries",
            "Showing both the menu button and the links at once is the bug this check "
            "exists to catch.",
        ),
        _check(
            "desktop_three_columns",
            5,
            _media(
                r"min-width\s*:\s*(?:1024px|64r?em)",
                r"\.pricing-grid",
                _decl("grid-template-columns", r"(?:repeat\(\s*3\s*,|1fr\s+1fr\s+1fr)"),
            ),
            "At min-width 1024px, .pricing-grid becomes three columns",
            "media queries",
            "A second, larger min-width query stacks on top of the first — later and "
            "more specific wins, so order the queries small to large.",
        ),
        _forbid(
            "no_max_width_queries",
            6,
            r"@media[^{]*max-width",
            "No max-width media queries are used",
            "mobile first",
            "A max-width query subtracts from a desktop layout. Mobile-first means the "
            "base rules are the smallest screen and every query adds.",
        ),
    ],
}


# ---------------------------------------------------------------------------
# 9. Transitions and transforms
# ---------------------------------------------------------------------------

GALLERY_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Atlas — Gallery</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <main class="gallery">
      <article class="tile">
        <img class="tile-image" src="https://picsum.photos/seed/1/600/400" alt="Coastline at dusk" />
        <p class="tile-caption">Coastline at dusk</p>
      </article>
      <article class="tile">
        <img class="tile-image" src="https://picsum.photos/seed/2/600/400" alt="Pine ridge" />
        <p class="tile-caption">Pine ridge</p>
      </article>
      <article class="tile">
        <img class="tile-image" src="https://picsum.photos/seed/3/600/400" alt="Salt flats" />
        <p class="tile-caption">Salt flats</p>
      </article>
    </main>
    <button class="cta-button" type="button">Load more</button>
  </body>
</html>
"""

_DURATION = r"(?:(?:1[5-9]\d|[23]\d\d|400)ms|0\.(?:1[5-9]|[23]\d?|4)s)"

TRANSITIONS_MODULE: dict[str, Any] = {
    "id": "css-transitions-gallery",
    "title": "Photo Gallery — Transitions and Transforms",
    "kind": "web",
    "practice_layer": "css",
    "skill_id": "css_basics",
    "technology": "CSS",
    "difficulty": 3,
    "estimated_minutes": 24,
    "summary": (
        "Add motion that a senior reviewer would sign off: named transition "
        "properties, durations in the 150–400ms band, transform-based hover and "
        "press states, and a prefers-reduced-motion escape hatch."
    ),
    "problem_statement": (
        "The Atlas gallery is static and the last attempt at motion used "
        "`transition: all 2s`, which animated layout properties and made the page "
        "feel broken. Redo it properly.\n\n"
        "Give .tile a transition that names the properties it animates — never `all` "
        "— with a duration between 150ms and 400ms and an explicit easing function. "
        "On hover the tile lifts with a transform: either a translateY of a negative "
        "amount or a scale slightly above 1. The image inside zooms on tile hover "
        "(.tile:hover .tile-image) and needs its own transition. The button reacts "
        "to both hover and press: a background change on hover and a downward "
        "translateY on :active. Finally, respect the OS setting — inside a "
        "`@media (prefers-reduced-motion: reduce)` block, cut transition durations "
        "to effectively zero."
    ),
    "constraints": [
        "Edit styles.css only — index.html is locked.",
        "`transition: all` is forbidden; name the properties you animate.",
        "Durations must land between 150ms and 400ms (0.15s–0.4s).",
        "Animate transform and opacity, not width/height/top/left — those trigger layout.",
        "A prefers-reduced-motion: reduce block is mandatory, not optional polish.",
    ],
    "requirements": [
        "Give .tile a transition that names transform and sets a 150–400ms duration",
        "Give .tile's transition an explicit easing function",
        "Lift .tile on hover with a translateY or a scale transform",
        "Zoom the image on tile hover with .tile:hover .tile-image and a scale transform",
        "Give .tile-image its own transition on transform",
        "Change .cta-button's background on hover and transition it",
        "Press .cta-button down on :active with a positive translateY",
        "Cut .tile's transition-duration to effectively zero inside @media (prefers-reduced-motion: reduce)",
        "Never use transition: all",
    ],
    "editable_files": [FILE],
    "entry_file": "index.html",
    "files": {
        "index.html": GALLERY_HTML,
        FILE: (
            "/* Atlas gallery — motion.\n"
            "   index.html is locked.\n"
            "   Hooks: .gallery .tile .tile-image .tile-caption .cta-button\n"
            "   Rules: no `transition: all`; durations 150-400ms; honour reduced motion.\n"
            "*/\n\n"
            "/* TODO: .tile — transition on transform, with easing. */\n\n"
            "/* TODO: .tile:hover — lift. */\n\n"
            "/* TODO: .tile-image + .tile:hover .tile-image — zoom. */\n\n"
            "/* TODO: .cta-button — hover background, :active press, transition. */\n\n"
            "/* TODO: @media (prefers-reduced-motion: reduce) — cut the motion. */\n"
        ),
    },
    "solution_files": {FILE: TRANSITIONS_SOLUTION},
    "checks": [
        _authored(),
        _check(
            "tile_transition",
            0,
            _base_rule(r"\.tile", _decl("transition(?:-property)?", r"[^;}]*transform[^;}]*")),
            ".tile transitions the transform property by name",
            "transitions",
            "`transition: transform 200ms ease-out` — naming the property means a later "
            "layout change is not accidentally animated.",
        ),
        _check(
            "tile_duration",
            0,
            _base_rule(r"\.tile", _decl("transition(?:-duration)?", r"[^;}]*" + _DURATION)),
            ".tile's transition lasts between 150ms and 400ms",
            "transitions",
            "Under ~150ms the change is not perceived as motion; over ~400ms the UI feels "
            "sluggish.",
        ),
        _check(
            "tile_easing",
            1,
            _base_rule(
                r"\.tile",
                _decl("transition(?:-timing-function)?", r"[^;}]*(?:ease-in-out|ease-out|ease-in|ease|linear|cubic-bezier\(|steps\()"),
            ),
            ".tile's transition names an easing function",
            "transitions",
            "Add `ease-out` (or a cubic-bezier) to the shorthand — motion that starts "
            "fast and settles reads as physical.",
        ),
        _check(
            "tile_hover_transform",
            2,
            _rule(
                r"\.tile:hover",
                _decl("transform", r"[^;}]*(?:translatey?\(\s*-[\d.]+|scale\w*\(\s*(?:1\.0*[1-9]|[2-9]))"),
            ),
            ".tile:hover lifts the card with a transform",
            "transforms",
            "Either `translateY(-6px)` (a negative Y moves up) or `scale(1.03)`. Changing "
            "`top` or `margin` instead would move the rest of the layout.",
        ),
        _check(
            "image_hover_zoom",
            3,
            _rule(
                r"\.tile:hover[^{}]*\.tile-image",
                _decl("transform", r"[^;}]*scale\w*\(\s*(?:1\.0*[1-9]|[2-9])"),
            ),
            ".tile:hover .tile-image scales the photo up",
            "combinators",
            "The hover lives on the tile but the transform belongs to the image, so the "
            "selector is `.tile:hover .tile-image`. A scale above 1 zooms in.",
        ),
        _check(
            "image_transition",
            4,
            _base_rule(r"\.tile-image", _decl("transition(?:-property)?", r"[^;}]*transform")),
            ".tile-image has its own transition on transform",
            "transitions",
            "A transition must be declared on the element in its resting state, not "
            "inside the :hover rule, or it only eases one way.",
        ),
        _check(
            "button_hover_background",
            5,
            _rule(r"\.cta-button:hover", _decl("background(?:-color)?", _COLOR)),
            ".cta-button:hover changes its background",
            "interactive states",
            "The hover affordance for a button is usually a background shift.",
        ),
        _check(
            "button_transition",
            5,
            _base_rule(
                r"\.cta-button",
                _decl("transition(?:-property)?", r"[^;}]*background(?:-color)?[^;}]*"),
            ),
            ".cta-button transitions its background-color by name",
            "transitions",
            "List both properties you animate: `transition: background-color 200ms ease, "
            "transform 200ms ease`.",
        ),
        _check(
            "button_active",
            6,
            _rule(r"\.cta-button:active", _decl("transform", r"[^;}]*translatey?\(\s*[\d.]+")),
            ".cta-button:active presses down with a positive translateY",
            "interactive states",
            "`transform: translateY(2px)` on :active makes the button feel physically "
            "pressed. A negative value would lift it instead.",
        ),
        _check(
            "reduced_motion",
            7,
            _media(
                r"prefers-reduced-motion",
                r"\.tile",
                _decl("transition(?:-duration)?", r"[^;}]*(?:0\.01ms|1ms|0s|none)"),
            ),
            "@media (prefers-reduced-motion: reduce) cuts .tile's transition duration",
            "accessibility",
            "Motion can cause nausea for some users. Inside the query, set "
            "`transition-duration: 0.01ms` on .tile (a selector list covering the tile, "
            "the image and the button is the usual way).",
        ),
        _forbid(
            "no_transition_all",
            8,
            r"transition(?:-property)?\s*:\s*(?:[^;}]*\s)?all(?![\w-])",
            "No `transition: all` is used",
            "transitions",
            "`all` animates properties you never intended, including expensive layout "
            "ones. Name transform, opacity and background-color explicitly.",
        ),
    ],
}


# ---------------------------------------------------------------------------
# 10. Pseudo-classes, pseudo-elements and interactive states
# ---------------------------------------------------------------------------

FORM_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Helpdesk — New Ticket</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <form class="ticket-form">
      <h1 class="form-title">New ticket</h1>
      <label class="field-label required-label" for="subject">Subject</label>
      <input class="field" id="subject" name="subject" type="text" required />
      <label class="field-label" for="details">Details</label>
      <textarea class="field" id="details" name="details" rows="4"></textarea>
      <p class="status-badge">Awaiting triage</p>
      <div class="form-actions">
        <a class="card-link" href="/tickets">Back to all tickets</a>
        <button class="action-btn" type="submit">Create ticket</button>
        <button class="action-btn" type="button" disabled>Save draft</button>
      </div>
    </form>
  </body>
</html>
"""

STATES_MODULE: dict[str, Any] = {
    "id": "css-interactive-states-form",
    "title": "Ticket Form — Interactive States and Pseudo-elements",
    "kind": "web",
    "practice_layer": "css",
    "skill_id": "css_basics",
    "technology": "CSS",
    "difficulty": 3,
    "estimated_minutes": 24,
    "summary": (
        "Give every interactive control a visible hover, keyboard-focus and disabled "
        "state, and generate the required-field marker and badge dot with "
        "pseudo-elements instead of extra markup."
    ),
    "problem_statement": (
        "The helpdesk form is unusable with a keyboard: the focus ring was removed "
        "globally, disabled buttons look clickable, and required fields are only "
        "marked in the HTML. Fix the state layer.\n\n"
        "Every control needs three states. .action-btn changes its background on "
        ":hover, shows a real focus ring on :focus-visible with a non-zero outline "
        "and an outline-offset, and when :disabled drops its opacity and switches "
        "the cursor to not-allowed. .field gets a changed border-colour on :focus. "
        ".card-link is styled on both :hover and :focus-visible so mouse and keyboard "
        "get the same affordance. Then generate content: .required-label::after adds "
        "a coloured asterisk, and .status-badge::before adds an inline-block dot with "
        "a width and a background. `outline: none` (or 0) must not appear anywhere — "
        "removing the focus ring without a replacement is the bug you are fixing."
    ),
    "constraints": [
        "Edit styles.css only — index.html is locked.",
        "Never write outline: none or outline: 0 — the keyboard ring must survive.",
        "Use :focus-visible for the keyboard ring, so a mouse click does not show it.",
        "Both pseudo-elements must declare `content` — without it they do not render.",
        "The asterisk and the badge dot must be generated in CSS, not added to the HTML.",
    ],
    "requirements": [
        "Change .action-btn's background on :hover",
        "Give .action-btn a visible :focus-visible outline with a non-zero width",
        "Offset that focus ring from the button with outline-offset",
        "Fade .action-btn:disabled with opacity and set cursor: not-allowed",
        "Change .field's border-colour on :focus",
        "Style .card-link on both :hover and :focus-visible",
        "Add a coloured asterisk with .required-label::after and the content property",
        "Add an inline-block dot with .status-badge::before, a width and a background",
        "Never remove the focus outline with outline: none or outline: 0",
    ],
    "editable_files": [FILE],
    "entry_file": "index.html",
    "files": {
        "index.html": FORM_HTML,
        FILE: (
            "/* Helpdesk — state layer.\n"
            "   index.html is locked.\n"
            "   Hooks: .ticket-form .form-title .field-label .required-label .field\n"
            "          .status-badge .form-actions .card-link .action-btn (+ [disabled])\n"
            "   Rules: no `outline: none`; keyboard ring via :focus-visible.\n"
            "*/\n\n"
            "/* TODO: .action-btn — :hover, :focus-visible ring, :disabled. */\n\n"
            "/* TODO: .field:focus — border colour. */\n\n"
            "/* TODO: .card-link — :hover and :focus-visible. */\n\n"
            "/* TODO: .required-label::after — the asterisk. */\n\n"
            "/* TODO: .status-badge::before — the dot. */\n"
        ),
    },
    "solution_files": {FILE: STATES_SOLUTION},
    "checks": [
        _authored(),
        _check(
            "btn_hover",
            0,
            _rule(r"\.action-btn:hover", _decl("background(?:-color)?", _COLOR)),
            ".action-btn:hover changes the background",
            "interactive states",
            "The selector is `.action-btn:hover` — a hover rule on a parent does not "
            "give the button its own affordance.",
        ),
        _check(
            "btn_focus_ring",
            1,
            _rule(
                r"\.action-btn:focus-visible",
                _decl("outline", r"[^;}]*[1-9][\d.]*(?:px|rem|em)"),
            ),
            ".action-btn:focus-visible draws an outline with a real width",
            "accessibility",
            "`outline: 2px solid <colour>` on :focus-visible. :focus-visible fires for "
            "keyboard navigation but not for a mouse click, which is why it replaced the "
            "old outline-removal habit.",
        ),
        _check(
            "btn_focus_offset",
            2,
            _rule(r"\.action-btn:focus-visible", _decl("outline-offset", r"[\d.]+(?:px|rem|em)")),
            ".action-btn:focus-visible sets an outline-offset",
            "accessibility",
            "Without an offset the ring hugs the border and is hard to see on a coloured "
            "button. 2px is plenty.",
        ),
        _check(
            "btn_disabled_opacity",
            3,
            _rule(r"\.action-btn:disabled|\.action-btn\[disabled", _decl("opacity", r"0?\.\d+")),
            ".action-btn:disabled is faded with opacity",
            "interactive states",
            "`:disabled` matches the button that already carries the attribute in the "
            "locked markup — no class needed.",
        ),
        _check(
            "btn_disabled_cursor",
            3,
            _rule(r"\.action-btn:disabled|\.action-btn\[disabled", _decl("cursor", r"not-allowed")),
            ".action-btn:disabled shows a not-allowed cursor",
            "interactive states",
            "The cursor is the fastest signal that a control will not respond.",
        ),
        _check(
            "field_focus",
            4,
            _rule(r"\.field:focus", _decl("border(?:-color)?", r"[^;}]*" + _COLOR)),
            ".field:focus changes its border colour",
            "interactive states",
            "Inputs need a focus treatment of their own; the browser default is easy to "
            "miss against a styled form.",
        ),
        _check(
            "link_hover",
            5,
            _rule(r"\.card-link:hover", r"[\w-]+\s*:[^;}]*\S"),
            ".card-link:hover is styled",
            "pseudo-classes",
            "At least one real declaration — an empty rule is not an affordance.",
        ),
        _check(
            "link_focus",
            5,
            _rule(r"\.card-link:focus-visible", r"[\w-]+\s*:[^;}]*\S"),
            ".card-link:focus-visible is styled",
            "accessibility",
            "You can group them — `.card-link:hover, .card-link:focus-visible { ... }` "
            "keeps mouse and keyboard in sync.",
        ),
        _check(
            "required_content",
            6,
            _rule(r"\.required-label::?after", _decl("content", r"[^;}]*[\"'']")),
            ".required-label::after declares a content string",
            "pseudo-elements",
            "A pseudo-element with no `content` never renders. `content: \" *\"` is enough.",
        ),
        _check(
            "required_colour",
            6,
            _rule(r"\.required-label::?after", _decl("color", _COLOR)),
            ".required-label::after is coloured",
            "pseudo-elements",
            "The asterisk should read as a warning colour, not as body text.",
        ),
        _check(
            "badge_content",
            7,
            _rule(r"\.status-badge::?before", _decl("content", r"[^;}]*[\"'']")),
            ".status-badge::before declares a content string",
            "pseudo-elements",
            "An empty string still counts: `content: \"\"` plus a size and a background "
            "gives you a dot with no markup.",
        ),
        _check(
            "badge_dot",
            7,
            _rule(r"\.status-badge::?before", _decl("width", r"[\d.]+(?:px|rem|em)")
                  + r"[^{}]*" + _decl("background(?:-color)?", _COLOR)),
            ".status-badge::before has a width and a background",
            "pseudo-elements",
            "A ::before is inline by default, so it also needs display: inline-block "
            "before a width applies.",
        ),
        _check(
            "badge_inline_block",
            7,
            _rule(r"\.status-badge::?before", _decl("display", r"(?:inline-block|block|(?:inline-)?flex)")),
            ".status-badge::before is displayed as an inline-block",
            "pseudo-elements",
            "Width and height are ignored on an inline box — switch it to inline-block.",
        ),
        _forbid(
            "no_outline_none",
            8,
            r"(?<![\w-])outline(?:-(?:style|width|color))?\s*:\s*(?:none|0)(?![\d.])",
            "The focus outline is never removed with outline: none / 0",
            "accessibility",
            "Removing the outline is what broke keyboard access here. Restyle the ring "
            "on :focus-visible instead of deleting it.",
        ),
    ],
}


CSS_MODULES: list[dict[str, Any]] = [
    BOX_MODEL_MODULE,
    SELECTORS_MODULE,
    TYPOGRAPHY_MODULE,
    VARIABLES_MODULE,
    FLEXBOX_MODULE,
    GRID_MODULE,
    POSITIONING_MODULE,
    RESPONSIVE_MODULE,
    TRANSITIONS_MODULE,
    STATES_MODULE,
]
