# SprintForge Audit Log (append-only)

Auditor: agent run starting 2026-08-31.
Test account: `audit_bot_2026@example.com` (user id `d316daec-93a9-4c07-96bb-ac2ee2b0774f`).
No existing user data touched.

## Coverage actually achieved (read this before trusting anything below)

- Path `sde`, project **Aurora Recipe Studio**: tickets **ARS-1 … ARS-11 all `done`** (61.1% of the
  project) — HTML ×2, CSS ×3, JS ×4, async ×2. Every one solved with hand-written modern code and
  verified green; most also probed with deliberately bad submissions.
- **NOT reached**: ARS-12 (api_integration), ARS-13/14/15 (React), ARS-16/17/18 (Node, REST, schema),
  the entire **data-analyst** path (5 courses), and all **practice / DSA / language-basics** modules.
- Paths `data-scientist`, `devops-sre`, `qa-sdet` report `available: false` with 0 courses, so there is
  nothing to exercise there.
- So: **React, the API client, the backend/SQL tickets and the whole Data Analyst path remain
  unverified.** Accusation 4 is answered for JS/DOM/async only, not for React and beyond.

Backend test suite after all fixes: **3323 passed, 0 failed** (unsandboxed).

## Entries

- 2026-08-31 — Registered fresh audit account via `POST /auth/register`. HTTP 201.
- Onboarded to path `sde`, skipped placement.
- Created project **Aurora Recipe Studio** `51d512c3-3754-400e-81ed-22a375170dac`
  (stack html/css/js/react/api/node/database) → 6 sprints, 18 tickets, sequential unlock.
- **ARS-1** (html_basics, `ed90689b-fc6f-48cd-91e3-f793e8ea5386`) — PASSED first try, 12/12 static checks.
  Adversarial: empty file → FAIL (12/12 fail); junk div + `img src="" alt=""` → FAIL; entire
  correct solution wrapped in `<!-- -->` → FAIL. Grader is sound here.
- Preview after ARS-1: correct, cumulative, 1 verified contributor.

### BUG 1 (HIGH, FIXED) — `Run` silently destroys a verified ticket's work and blanks the preview
Repro: complete a ticket (status `done`), then `POST /tickets/{id}/run` with any other content
(e.g. the solution wrapped in an HTML comment). Observed: ticket stays `done` with XP retained,
`completed_at` intact, but `workspace_files` is replaced by the scratch buffer. The cumulative
project preview — composed from those same workspace files — became a single HTML comment, i.e.
a blank page. The corruption also propagated: ARS-2 had already inherited the broken `index.html`
via `opening_files`, so restoring ARS-1 alone did not repair the preview.
Root cause: `ticket_service.run_ticket` called `save_workspace` unconditionally, despite Run being
documented "no grading, no XP, no twin update". No status guard existed, while `start_ticket` and
`reset_ticket` both deliberately treat `done` as terminal.
Fix: added pure `workspace_with()`; `run_ticket` now grades the buffer without persisting when
status is `done`. Regression test `test_running_a_verified_ticket_does_not_overwrite_the_graded_work`
in `backend/tests/test_project_preview.py` (verified: fails without the guard, passes with it).
NOTE: the live server was started before this edit and has no `--reload`, so the running process
still executes the old code. Needs a backend restart to be live.

- **ARS-2** (html_semantics) — PASSED 4/4, +130 XP. Adversarial (no `aria-label`, 2 links, `div`
  instead of `ul`) → 3 of 4 checks FAIL. Correct.
- **ARS-3** (css_basics) — PASSED 39/39, +30 XP. Preview verified cumulative: `index.html` +
  `styles.css`, stylesheet inlined into the document (the `<link>` is replaced by `<style>`).
  Screenshot: `audit_screens/preview_after-ARS-3.png` — renders as a modern dark themed page.
  Adversarial: empty stylesheet → 0/39; selectors renamed to classes that match nothing
  (`.navbar-list`, `.foot`) → 9 FAIL. Correct rejection.
  NOT A BUG (my code was wrong): the rendered check "banner fills the hero width at a controlled
  height" failed my first attempt because `<img height="900">` makes `aspect-ratio` inert —
  `aspect-ratio` only computes a height when `height` is `auto`. Adding `height: auto` fixed it.
  The render layer caught a real 900px-tall banner that static analysis alone would have passed.

### BUG 2 (HIGH, NOT YET FIXED) — the CSS checks grade selector *text*, so correct class-based CSS fails
Repro on ARS-3 (`css_basics`), `styles.css`. Two stylesheets that produce a byte-identical rendered
page: one written with element selectors (`nav ul`, `nav a`, `footer`, `#hero img`), one written with
BEM classes that genuinely match the same elements (`.site-nav__list`, `.site-nav__link`,
`.site-footer`, `.hero__image`). Element version: 39/39 PASS. Class version: 22/39, **17 FAIL** —
including "The nav's `<ul>` is a flex row", "The nav links drop their underline", "The footer is
separated by a top border", "The banner has rounded corners".
Decisive evidence that the check cannot see whether a rule applies: the class-based stylesheet that
*does* style the page failed the **same** checks as an adversarial stylesheet whose selectors
(`.navbar-list`, `.foot`) match nothing at all. The grader cannot distinguish working CSS from CSS
that styles nothing.
Root cause: these checks are `type: "regex"` over the raw stylesheet built by `_rule()` in
`backend/app/data/ticket_templates.py` (e.g. line 1526 `nav_horizontal`), which requires the literal
element name to appear in the selector text inside the same `{}` block. The ticket brief never
requires element selectors; only the *hints* happen to show them. The reference solutions in
`ticket_templates.py` also use element selectors, which is why
`scripts/verify_web_ticket_solutions.py` never caught it.
Note the project already owns the correct tool: the `render_*` checks in `render_judge.py` read
*computed* styles from a real headless Chromium, and every one of them passed the class-based CSS
("The nav links render side by side", "No link renders in the browser's default blue", "The tagline
is centred in the hero"). The regex layer is a weaker parallel implementation of the same intent.
Recommended fix (does NOT weaken the grader — it strengthens it): replace the selector-text regexes
with `render_computed_style` checks, which assert the declaration actually takes effect on the target
element regardless of how it was selected. Left unfixed pending owner decision because it touches
many templates and changes what every existing learner is graded against (see
`.cursor/rules/learner-data-is-sacred.mdc` on regenerating `validation_spec`).

- **ARS-4** (css_layout) — PASSED 24/24 first try, +30 XP. Preview cumulative (4 contributors).
  Adversarial (gap 0, fixed columns, no transition) → 4 FAIL, correctly rejected.

### BUG 3 (HIGH, NOT YET FIXED) — the same CSS checks also PASS incorrect code (false positives)
Repro on ARS-4 (`css_layout`), `styles.css`. Take the passing stylesheet and delete every
resting-state declaration from `.card`, leaving the block as only
`display:flex; flex-direction:column; gap:12px; transition:...` — no background, no border, no
radius, no padding, no shadow. Keep `.card:hover { transform; box-shadow; border-color }` and
`.card img { border-radius: 10px }`.
Result: 21/24, and these two still **PASS** although the card has neither:
  * "`.card` casts a shadow" — satisfied by the shadow that only exists on `:hover`.
  * "`.card` has a border-radius of 8px or more" — satisfied by the radius on the *poster image*
    (`.card img`), not on the card.
So requirement 2 ("give `.card` a real surface: background, 1px border, radius, padding, shadow")
is only 3/5 enforced; a card with square corners and no resting shadow is accepted.
Root cause: `_rule()` in `backend/app/data/ticket_templates.py` (line ~49) builds
`(?:^|[{};])[^{}]*<selector>(?![\w-])[^{}]*\{[^{}]*<declaration>`. The trailing `[^{}]*` before the
brace lets arbitrary extra selector text sit between the token and the block, so `.card:hover {...}`
and `.card img {...}` both satisfy a check aimed at `.card`. The `_BOUND` guard only stops
`.cardxyz`; it does not stop descendant combinators or pseudo-classes.
- **ARS-7** (js_functions) — PASSED 13/13 first try, +30 XP. Adversarial: in-place `list.sort()` +
  index loop instead of `.filter()` → 2 FAIL; the purity violation was caught *at runtime* by
  inspecting the caller's array after the call, exactly as the brief promises.
- **ARS-8** (js_dom) — PASSED 9/9, +30 XP. Adversarial: hardcoded `innerHTML` string that never
  touches the data → 2 FAIL ("Iterates over the data array", "The image URL comes from the item's
  poster field"). This is the owner's "hardcoded HTML instead of real JS" case; it is rejected.
  **Preview verified with a real browser**: 6 `.card` elements rendered by the learner's JS, each with
  computed `background-color: rgb(23, 26, 33)` (the `--surface-raised` token) and
  `border-radius: 14px` (the `--radius` token). The stylesheet from ARS-3/ARS-4 genuinely applies to
  markup created by ARS-8's JavaScript. Screenshot: `audit_screens/preview_after-ARS-8.png`.
  (Poster images are blank only because the sandbox blocks `picsum.photos`; not a product defect.)
- **BUG 1 FIX VERIFIED LIVE**: after the supervisor restarted the backend, a garbage `run` against the
  already-`done` ARS-8 left `status=done` *and* the verified `script.js` byte-identical. Before the
  fix this destroyed the work and blanked the preview.

- **ARS-9** (js_dom, selection) — PASSED 16/16, +130 XP, but only after two cosmetic edits.

### BUG 4 (MEDIUM, NOT FIXED) — two JS checks grade identifier names and control-flow syntax
Repro on ARS-9 (`js_dom`), `script.js`. A correct, working implementation failed 2 of 16 checks:
  * "The selection lives in a state object" — pattern `(?:const|let)\s+\w*[Ss]tate\w*\s*=\s*\{`.
    My state object was named `selection`. Renaming it to `selectionState`, changing nothing else,
    makes it pass. The check grades the *identifier spelling*, not whether state exists.
  * "The summary has an unselected state as well as a selected one" — pattern requires a **ternary**
    in an assignment to `textContent`. My version used an early-`return` if/else that produces the
    same two strings. Rewriting it as a ternary makes it pass.
Verified decisively: changing only the variable name and the control-flow form took the submission
from 14/16 to **16/16** with byte-identical behaviour.
Root cause: same as BUG 2/3 — `type: "regex"` checks over source text where an AST or behaviour
assertion is the right instrument. This project already has both (`js_ast.py`, and the behaviour
harness that really does call the learner's functions), so the tools exist.

### BUG 5 (HIGH, FIXED) — `js_loading_sequence` rejects any loading state rendered via a helper
Repro on ARS-10 (`js_async`), `script.js`. A correct loader:
`renderLoading(); const r = await fetch(url); const d = await r.json(); renderRecipes(d);`
with `renderLoading` / `renderRecipes` declared above it fails with
"the loading state is never cleared after the request settles" (7/8). Inlining the post-await DOM
write into the loader body — same behaviour, worse code — passes 8/8.
Root cause: `js_loading_sequence` in `backend/app/services/validation_service.py` bucketed DOM writes
into `before` / `after` by **character offset** relative to the awaited request. Every write inside a
helper declared above the loader has an offset before the await, so `after` was always empty and no
extracted implementation could ever pass. The ticket brief's own three-states framing invites exactly
that structure.
Fix: added `_dom_writes_by_function()`, which resolves (transitively, recursion-safe) which DOM
targets each named function eventually writes. `js_loading_sequence` now also credits a
**call** to one of the learner's render helpers, at the position of the call. Following the call
graph rather than the text.
Tests added in `backend/tests/test_validation_strict.py`:
  * `test_loading_cleared_through_a_render_helper_passes` — the false negative above.
  * `test_helper_that_never_repaints_after_the_request_still_fails` — guards against the fix becoming
    a loophole: a post-await call to a helper that touches no DOM still FAILS.
Verified: full backend suite **3322 passed, 0 failed** (unsandboxed; sandboxed runs fail 8
`render_*` tests purely because Chromium is unavailable there, which is pre-existing).

- **ARS-10** (js_async) — PASSED 8/8, +30 XP (after the inlining workaround; the underlying check is
  now fixed as above).

### BUG 6 (HIGH, FIXED) — the behaviour-test DOM stub is missing APIs earlier tickets require
Repro on ARS-11 (`js_async_error_handling`), `script.js`. All three behaviour assertions failed with
`TypeError: Cannot read properties of undefined (reading 'insertBefore')`, then — after working around
that — with `TypeError: listContainer.querySelectorAll is not a function`. Both errors are reported to
the learner as *their* failure ("your code threw ..."), and they wipe out the whole behaviour layer.
Neither has anything to do with error handling.
Root cause: the JS DOM stub in `backend/app/data/ticket_templates.py` (`__makeElement`) omitted
  1. `parentNode` — so `container.parentNode.insertBefore(node, container)` throws. This is the only
     way to add the `aria-live` selection summary that **ARS-9 requirement 5 demands**, because ARS-9
     does not let the learner edit `index.html`.
  2. element-level `querySelector` / `querySelectorAll` / `closest` — only `document` had them, so the
     container-scoped queries ARS-9 requirement 3 invites (`container.querySelector('.card.selected')`)
     throw.
The product's own `JS_SELECTION_SOLUTION` reference also calls `container.parentNode.insertBefore`;
it escapes only by accident, because the stub's `document.getElementById` returns the container for
*any* id, so its `if (!summary)` guard never runs the insert.
Fix in `ticket_templates.py`: added `__adopt()` so append/prepend/insertBefore/replaceChildren set
`parentNode`; gave the root container a real `<main>` parent (and made that `document.body`);
implemented `insertBefore(child, reference)` properly; added element-scoped
`querySelector`/`querySelectorAll`/`closest` with a small simple-selector matcher (`.class`, `#id`,
`[attr]`, tag, comma lists).
Test added: `test_dom_stub_supports_the_apis_earlier_tickets_require` in
`backend/tests/test_behaviour_harness.py`.

### BUG 7 (MEDIUM, NOT FIXED) — error-state checks require string markup, contradicting ARS-8
Repro on ARS-11. Building the error state with DOM APIs —
`el.setAttribute("role", "alert")` and `document.createElement("button")` with
`textContent = "Try again"` — FAILS both:
  * "The error state carries `role=\"alert\"`" — pattern `role\s*=\s*["']?(?:alert|status)`
  * "The error state offers a retry control" — pattern `<button[^>]*>[^<]*(?:try again|retry|reload)`
Switching the identical UI to an `insertAdjacentHTML` template string makes both PASS.
This directly contradicts ARS-8, whose checks explicitly accept `createElement("img")` and whose
requirement 4 bans `document.write`; the curriculum teaches DOM construction and then grades for
HTML string literals.
Root cause: same family as BUG 2/3/4 — `type: "regex"` over source text.

- **ARS-11** (js_async_error_handling) — PASSED 12/12, +30 XP (after restructuring around the stub
  gaps below). Preview after ARS-11: 11 contributors, all three files, cumulative.

### IMPORTANT ARCHITECTURAL NOTE — spec fixes do not reach existing projects
`ticket.validation_spec` (checks *and* the behaviour-test prelude, including the DOM stub) is
snapshotted into the row by `build_validation_spec()` when the project is created. Restarting the
backend with the BUG 6 fix therefore did **not** change how my existing ARS-11 was graded; the frozen
prelude was still used. Any fix to a check or a prelude only reaches newly created projects unless
existing `validation_spec`s are regenerated — which
`.cursor/rules/learner-data-is-sacred.mdc` says needs the owner's approval, since it changes what
learners are graded against. **This needs an owner decision** (see report).

### BUG 8 (MEDIUM, FIXED) — the DOM stub's `remove()` was a no-op
Found while finishing ARS-11. `__makeElement().remove()` was `remove() {}`, so it never detached the
node. Any implementation that clears a container by removing the nodes it appended — instead of
assigning `innerHTML` — was graded "the DOM still shows the loading state after the data arrived"
even though it clears correctly in a browser.
Fix: `remove()` now splices the node out of `parentNode.children`, clears `parentNode` and records the
write. In `backend/app/data/ticket_templates.py`.

### BUG 9 (MEDIUM-HIGH, NOT FIXED — needs an owner decision) — the preview cannot serve the API the async tickets require
Repro: complete ARS-10/ARS-11 as specified (they instruct you to `fetch` the recipes) and open the
cumulative project preview. Verified in a real browser: `.card` count = **0**, and the only content is
`.list-error` → "We could not load the recipes. Failed to fetch — Try again".
The preview is assembled as a **static** HTML document (`project_preview_service` →
`practice_service.build_preview`) with no server and no `fetch` shim anywhere in the pipeline
(`rg 'fetch|serviceWorker|mock|/api/' backend/app/services/practice_service.py` → no matches). So from
ARS-10 until the REST endpoints exist at ARS-17, **7 consecutive tickets** can only ever render the
loading state followed by the error state.
The error handling itself is working exactly as designed — the page degrades to an announced error with
a retry instead of going blank, which is a credit to ARS-11. But the owner's requirement that the
preview "render correctly and update cumulatively after EVERY ticket" is **not** met across this span:
the visible product regresses from six styled cards (after ARS-8/ARS-9) to an error banner.
Recommended fix (owner's call): inject a preview-only `fetch` shim into the assembled document that
answers the project's own API paths from the ticket's sample data, labelled in `preview_meta` so the
UI can say "API responses are stubbed in preview"; or point the async ticket at a `recipes.json` the
preview can inline. Not implemented because it changes what every learner sees in the preview.

- **ARS-5** (css_responsive) — PASSED 13/13, +130 XP. All 13 are *rendered* checks measured at real
  viewports (360px / 390px / 1280px / 1600px). Adversarial (media query that collapses nothing,
  fixed 44px headline, no `max-width` on `main`) → 6 FAIL. This layer is genuinely strong.
- **ARS-6** (js_basics) — PASSED 14/14, +30 XP. **Behaviour tests really do execute the learner's
  functions** in the Node sandbox (`formatPrice(320)`, `formatRating(8.63)`, junk input, etc.).
  Adversarial: four functions stubbed to return constants → 7 FAIL (`js_not_trivial` catches the
  constant returns, even though 2 behaviour assertions coincidentally matched the hardcoded string —
  defence in depth worked); syntax error → parse precondition FAILS and behaviour tests refuse to
  run rather than passing by accident.
  MINOR (spec ambiguity, LOW): requirement 4 says "shorten text longer than limit" without saying
  whether the ellipsis counts toward the limit. The hidden check requires the *result* to be ≤ limit
  (`truncate(..., 12) returned 13 characters`). Both conventions are common; the requirement should
  say which. My first attempt was legitimately wrong, so this is a wording issue, not a broken check.

Same cure as BUG 2: assert the computed value on the element itself via `render_computed_style`
(with the element in its resting state), rather than pattern-matching selector text. One fix removes
both the false negatives and the false positives, because both come from grading text instead of
grading the rendered result.

