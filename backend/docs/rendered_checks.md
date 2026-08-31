# Rendered (browser) checks for HTML and CSS

HTML and CSS used to be graded by reading the source. `css_property`, `regex`
and `html_element` can prove that a declaration exists on a selector that looks
plausible; they cannot prove that the selector matches an element, that the
value is legal, or that the layout the requirement describes actually happened.

`app/services/render_judge.py` closes that gap. It assembles the learner's
bundle into one document (the same assembly the preview iframe uses), loads it in
headless Chromium via Playwright, and asserts on facts the browser computed.

The eight check types below are **additive**. Nothing about `css_property`,
`html_element`, `regex` or any other existing type changed, so every module that
does not opt in behaves exactly as before.

## The rules that keep them honest

1. **A fake must not pass.** Every verdict comes from the rendered page, and if
   the browser cannot run the check the check *fails* — see "When the browser is
   missing" below.
2. **A correct solution must not be rejected.** Assert outcomes, with ranges and
   tolerances: "three columns rendered", not "`grid-template-columns` is exactly
   `repeat(3, 1fr)`". If several techniques reach the same rendered result, all
   of them must pass. `tests/test_render_judge.py` has a parametrised test per
   check type that pins this down (flex/grid/inline-block/float all count as a
   row; auto margins, flex centring, grid centring and `translateX(-50%)` all
   count as centred).

## Common keys

| Key | Meaning |
| --- | --- |
| `type` | one of the eight below |
| `selector` | any CSS selector — this goes to `querySelectorAll`, not the limited static grammar |
| `entry` | the document to load; defaults to `file`, then `index.html` |
| `viewport` | `{"width": 1280, "height": 900}` by default |
| `min_count` | how many elements must match (default 1) |
| `tolerance` / `min_tolerance` | px slack; defaults to `max(2px, 2% of the reference length)` |
| `id`, `label`, `concept`, `hint`, `requirement_index` | as for every other check |

Checks that share an entry document *and* a viewport are graded in one page load.

## The check types

### `render_computed_style`
The computed value of one property. `value_in`, `value_pattern`, `value_not_in`,
`min_value`, `max_value` (numeric, read from the leading number, so `20px` works).
`all_match: true` requires every matching element to satisfy it; the default is
"at least one". `require_visible: true` ignores elements that are not rendered.

```python
{"type": "render_computed_style", "selector": ".panel", "property": "padding-top",
 "min_value": 16, "all_match": True}
```

### `render_grid_columns`
How many columns the grid **rendered**. `min`, `max`, `equals`. Zero-width tracks
(which `auto-fit` collapses and still reports) are not counted, and a grid with no
explicit track list falls back to where its children actually sit.
`require_grid: false` allows non-grid containers.

Two of these at two viewports is how "it reflows on its own" becomes checkable:
`min: 3` at 1280px and `max: 2` at 420px reject a hard-coded `1fr 1fr 1fr`.

### `render_row_layout`
Children really sit side by side. `min_children`, `min_row_pairs`, `max_rows`.
"Side by side" means the boxes share most of their vertical extent and each one
starts meaningfully right of the last, so centred children of different heights
pass and stacked full-width blocks never do. Any technique qualifies — use
`render_computed_style` on `display` if the requirement is specifically flexbox.

### `render_centered`
`axis`: `horizontal` (default), `vertical`, `both`. Compares the gaps inside the
parent's content box (or `within`'s). An element that fills its parent is
rejected rather than counted as trivially centred; pass `allow_full_width: true`
if that is genuinely what you mean.

### `render_visible`
Rendered at all: not `display: none`, not `visibility: hidden`, opacity above
0.05, a box of at least 1x1, not clipped away, not pushed off the page.
`min_height`, `min_width`, `non_empty` (text, or a media/form descendant).

### `render_color`
The colour as actually resolved, including through `var()`. `require_opaque`
(default true) rejects a value that resolved to nothing, `min_luminance` /
`max_luminance` bound the WCAG relative luminance, `near_rgb` +
`max_channel_distance` pin a target, and `differs_from_parent` catches the case
where an unresolvable token silently leaves the inherited colour in place.
Transparent backgrounds resolve up the ancestor chain by default.

### `render_box`
Geometry: `min_width`, `max_width`, `min_height`, `max_height`, plus
`min_width_ratio` / `max_width_ratio` (and the height equivalents) relative to
the parent's content box. Prefer the ratios — they survive a viewport change.

### `render_on_top`
The element is the topmost thing at its own centre point. With `over: <selector>`
the failure message says which element inside that selector is covering it.
This is how a z-index / stacking requirement becomes observable.

## When the browser is missing

`SPRINTFORGE_RENDER_JUDGE` selects the behaviour:

* **`require` (default)** — the check **fails**, with a detail line saying the
  browser was unavailable and a hint naming the install command. A submission is
  never credited for a check that did not run.
* **`skip`** — the check still reports `passed=False`, but carries
  `skipped=True` so a test environment can tell "not run" from "wrong". It is
  never a pass in either mode.

Install with `pip install playwright && playwright install chromium` (~300MB).

## Performance

One Chromium process is launched on first use and reused for the process
lifetime, on a dedicated worker thread (Playwright's sync API cannot run inside
the request's asyncio loop). Each job gets a fresh browser context so pages
cannot leak into each other. A cold first grade costs ~1.3s; subsequent grades of
a whole module's rendered suite cost ~60–100ms. Every job is bounded by
`SPRINTFORGE_RENDER_TIMEOUT` (20s) and a 6s page budget; a job that overruns
fails as a graded verdict and the browser is recycled. Remote requests never
leave the machine: images are answered with a fixed-size placeholder so geometry
is deterministic offline, and everything else remote is aborted.
