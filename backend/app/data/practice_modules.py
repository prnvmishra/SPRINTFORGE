"""Practice module catalog.

Web modules use a "layer removal" model: a complete sample project exists, and
exactly one layer (HTML, CSS, JS or a React component) is stripped out for the
learner to rebuild. Language modules are classic judge-style challenges.

Stored as Python data (not JSON) so the embedded starter code stays readable.
"""

from __future__ import annotations

from typing import Any

from app.data.curriculum import CURRICULUM_MODULES
from app.data.curriculum_basics_typescript import TYPESCRIPT_BASICS_MODULES
from app.data.practice_css import CSS_MODULES
from app.data.practice_html import HTML_MODULES
from app.data.practice_js import JS_MODULES
from app.data.practice_analytics import ANALYTICS_MODULES
from app.data.practice_sql import SQL_MODULES

# ---------------------------------------------------------------------------
# Shared assets for the "Interactive Profile Card" sample project
# ---------------------------------------------------------------------------

PROFILE_CARD_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Interactive Profile Card</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <main class="page">
      <section class="profile-card">
        <img class="avatar" src="https://i.pravatar.cc/160?img=12" alt="Portrait of Ada Lovelace" />
        <h1 class="profile-name">Ada Lovelace</h1>
        <p class="profile-bio">
          Mathematician and the first computer programmer. Currently exploring
          analytical engines and async JavaScript.
        </p>
        <button id="followBtn" class="follow-btn" type="button">Follow</button>
        <p id="followerCount" class="follower-count">1024 followers</p>
      </section>
    </main>
    <script src="script.js"></script>
  </body>
</html>
"""

PROFILE_CARD_CSS = """:root {
  --surface: #12141c;
  --accent: #6366f1;
  --text: #e5e7eb;
}

body {
  margin: 0;
  min-height: 100vh;
  background-color: #0b0c10;
  color: var(--text);
  font-family: system-ui, -apple-system, sans-serif;
}

.page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
}

.profile-card {
  width: 100%;
  max-width: 340px;
  padding: 32px 24px;
  background-color: var(--surface);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  text-align: center;
  transition: transform 200ms ease, box-shadow 200ms ease;
}

.profile-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.45);
}

.avatar {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  object-fit: cover;
}

.follow-btn {
  margin-top: 16px;
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  background-color: var(--accent);
  color: white;
  font-weight: 600;
  cursor: pointer;
}

.follow-btn:hover {
  background-color: #4f46e5;
}

@media (max-width: 480px) {
  .profile-card {
    max-width: 100%;
    padding: 24px 16px;
  }
}
"""

PROFILE_CARD_JS = """const followBtn = document.getElementById("followBtn");
const followerCount = document.getElementById("followerCount");

let following = false;
let followers = 1024;

followBtn.addEventListener("click", () => {
  following = !following;
  followers = following ? followers + 1 : followers - 1;
  followBtn.textContent = following ? "Following" : "Follow";
  followerCount.textContent = `${followers} followers`;
});
"""


PRACTICE_MODULES: list[dict[str, Any]] = [
    # ------------------------------------------------------------------ HTML
    {
        "id": "html-profile-card",
        "title": "Interactive Profile Card — HTML Layer",
        "kind": "web",
        "practice_layer": "html",
        "skill_id": "html_semantics",
        "technology": "HTML",
        "difficulty": 2,
        "estimated_minutes": 20,
        "summary": "CSS and JavaScript are already wired up. Rebuild the missing HTML structure so the existing styles and behaviour work.",
        "requirements": [
            "Wrap the page content in a <main> element with class \"page\"",
            "Add a <section> with class \"profile-card\"",
            "Add a profile image with class \"avatar\" and descriptive alt text",
            "Add an <h1> with class \"profile-name\" containing the person's name",
            "Add a description paragraph with class \"profile-bio\"",
            "Add a <button> with id \"followBtn\"",
            "Add a paragraph with id \"followerCount\"",
        ],
        "editable_files": ["index.html"],
        "entry_file": "index.html",
        "files": {
            "index.html": "<!DOCTYPE html>\n<html lang=\"en\">\n  <head>\n    <meta charset=\"utf-8\" />\n    <title>Interactive Profile Card</title>\n    <link rel=\"stylesheet\" href=\"styles.css\" />\n  </head>\n  <body>\n    <!-- Build the profile card structure here -->\n\n    <script src=\"script.js\"></script>\n  </body>\n</html>\n",
            "styles.css": PROFILE_CARD_CSS,
            "script.js": PROFILE_CARD_JS,
        },
        "solution_files": {"index.html": PROFILE_CARD_HTML},
        "checks": [
            {
                "id": "main_page",
                "requirement_index": 0,
                "type": "html_element",
                "file": "index.html",
                "selector": "main.page",
                "label": "<main class=\"page\"> wrapper exists",
                "concept": "semantic html",
                "hint": "Use <main class=\"page\"> as the top-level landmark inside <body>.",
            },
            {
                "id": "card_section",
                "requirement_index": 1,
                "type": "html_element",
                "file": "index.html",
                "selector": "section.profile-card",
                "label": "<section class=\"profile-card\"> exists",
                "concept": "semantic html",
                "hint": "A card is a self-contained region, so use <section class=\"profile-card\">.",
            },
            {
                "id": "avatar",
                "requirement_index": 2,
                "type": "html_element",
                "file": "index.html",
                "selector": "img.avatar",
                "with_attributes": {"src": "*", "alt": "*"},
                "label": "Avatar image has class \"avatar\", src and non-empty alt",
                "concept": "alt text",
                "hint": "Every <img> needs a meaningful alt attribute for accessibility.",
            },
            {
                "id": "heading",
                "requirement_index": 3,
                "type": "html_element",
                "file": "index.html",
                "selector": "h1.profile-name",
                "non_empty_text": True,
                "label": "<h1 class=\"profile-name\"> contains the name",
                "concept": "headings hierarchy",
                "hint": "The card title is the page's primary heading: use <h1>.",
            },
            {
                "id": "bio",
                "requirement_index": 4,
                "type": "html_element",
                "file": "index.html",
                "selector": "p.profile-bio",
                "non_empty_text": True,
                "label": "Description paragraph with class \"profile-bio\"",
                "concept": "elements",
            },
            {
                "id": "follow_button",
                "requirement_index": 5,
                "type": "html_element",
                "file": "index.html",
                "selector": "button#followBtn",
                "label": "<button id=\"followBtn\"> exists",
                "concept": "elements",
                "hint": "script.js looks up document.getElementById(\"followBtn\").",
            },
            {
                "id": "follower_count",
                "requirement_index": 6,
                "type": "html_element",
                "file": "index.html",
                "selector": "p#followerCount",
                "label": "Follower count element with id \"followerCount\"",
                "concept": "elements",
            },
            {
                "id": "card_inside_main",
                "requirement_index": 1,
                "type": "html_nested",
                "file": "index.html",
                "selector": "section.profile-card",
                "parent": "main",
                "label": "Card is nested inside <main>",
                "concept": "nesting",
            },
        ],
    },
    # ------------------------------------------------------------------- CSS
    {
        "id": "css-profile-card",
        "title": "Interactive Profile Card — CSS Layer",
        "kind": "web",
        "practice_layer": "css",
        "skill_id": "css_layout",
        "technology": "CSS",
        "difficulty": 3,
        "estimated_minutes": 25,
        "summary": "The HTML and JavaScript are complete. The stylesheet was removed — style the card to spec.",
        "requirements": [
            "Give the page a dark background colour",
            "Centre the card horizontally and vertically using flexbox",
            "Give .profile-card rounded corners and a max width",
            "Make the avatar a circle",
            "Add a hover effect to .profile-card",
            "Style .follow-btn with a background colour and pointer cursor",
            "Add a responsive rule using a media query",
        ],
        "editable_files": ["styles.css"],
        "entry_file": "index.html",
        "files": {
            "index.html": PROFILE_CARD_HTML,
            "styles.css": "/* The stylesheet was removed. Rebuild it from the requirements. */\n",
            "script.js": PROFILE_CARD_JS,
        },
        "solution_files": {"styles.css": PROFILE_CARD_CSS},
        "checks": [
            {
                "id": "body_background",
                "requirement_index": 0,
                "type": "css_property",
                "file": "styles.css",
                "selector": "body",
                "property": "background-color",
                "label": "body has a background-color",
                "concept": "colors",
                "hint": "Set background-color on body (or html) to a dark value.",
            },
            {
                "id": "flex_center",
                "requirement_index": 1,
                "type": "css_property",
                "file": "styles.css",
                "selector": ".page",
                "property": "display",
                "label": ".page uses display (flex or grid) for centring",
                "concept": "flexbox",
                "hint": "display: flex plus align-items and justify-content centres the card.",
            },
            {
                "id": "justify",
                "requirement_index": 1,
                "type": "regex",
                "file": "styles.css",
                "pattern": r"justify-content\s*:\s*center",
                "label": "Content is horizontally centred (justify-content: center)",
                "concept": "alignment",
            },
            {
                "id": "align",
                "requirement_index": 1,
                "type": "regex",
                "file": "styles.css",
                "pattern": r"align-items\s*:\s*center",
                "label": "Content is vertically centred (align-items: center)",
                "concept": "alignment",
            },
            {
                "id": "radius",
                "requirement_index": 2,
                "type": "css_property",
                "file": "styles.css",
                "selector": ".profile-card",
                "property": "border-radius",
                "label": ".profile-card has border-radius",
                "concept": "box model",
            },
            {
                "id": "max_width",
                "requirement_index": 2,
                "type": "css_property",
                "file": "styles.css",
                "selector": ".profile-card",
                "property": "max-width",
                "label": ".profile-card constrains its width (max-width)",
                "concept": "box model",
            },
            {
                "id": "avatar_circle",
                "requirement_index": 3,
                "type": "regex",
                "file": "styles.css",
                "pattern": r"\.avatar[^{]*\{[^}]*border-radius\s*:\s*(50%|9999px|999px)",
                "label": "Avatar is circular (border-radius: 50%)",
                "concept": "box model",
            },
            {
                "id": "hover",
                "requirement_index": 4,
                "type": "regex",
                "file": "styles.css",
                "pattern": r"\.profile-card:hover\s*\{[^}]*\S",
                "label": ".profile-card:hover defines a hover effect",
                "concept": "selectors",
                "hint": "Add a .profile-card:hover rule with at least one declaration.",
            },
            {
                "id": "button_style",
                "requirement_index": 5,
                "type": "regex",
                "file": "styles.css",
                "pattern": r"\.follow-btn[^{]*\{[^}]*cursor\s*:\s*pointer",
                "label": ".follow-btn has cursor: pointer",
                "concept": "selectors",
            },
            {
                "id": "media_query",
                "requirement_index": 6,
                "type": "css_at_rule",
                "file": "styles.css",
                "pattern": r"@media[^{]*\(",
                "label": "A media query makes the layout responsive",
                "concept": "media queries",
                "hint": "Add @media (max-width: 480px) { ... } with at least one rule.",
            },
        ],
    },
    # -------------------------------------------------------------------- JS
    {
        "id": "js-profile-card",
        "title": "Interactive Profile Card — JavaScript Layer",
        "kind": "web",
        "practice_layer": "javascript",
        "skill_id": "js_dom",
        "technology": "JavaScript",
        "difficulty": 3,
        "estimated_minutes": 25,
        "summary": "HTML and CSS are complete. Add the missing interactivity: the follow button must toggle its label and update the follower count.",
        "requirements": [
            "Select #followBtn and #followerCount from the DOM",
            "Attach a click event listener to the button",
            "Toggle the button text between \"Follow\" and \"Following\"",
            "Increment the follower count when following, decrement when unfollowing",
            "Update the follower count element's text content",
        ],
        "editable_files": ["script.js"],
        "entry_file": "index.html",
        "files": {
            "index.html": PROFILE_CARD_HTML,
            "styles.css": PROFILE_CARD_CSS,
            "script.js": "// The JavaScript layer was removed.\n// Make the follow button work using the requirements on the left.\n",
        },
        "solution_files": {"script.js": PROFILE_CARD_JS},
        "checks": [
            {
                "id": "syntax",
                "requirement_index": None, "precondition": True,
                "type": "js_syntax",
                "file": "script.js",
                "label": "script.js is valid JavaScript",
                "concept": "syntax",
            },
            {
                "id": "select_button",
                "requirement_index": 0,
                "type": "regex",
                "file": "script.js",
                "pattern": r"(getElementById\(\s*[\"']followBtn[\"']\s*\)|querySelector\(\s*[\"']#followBtn[\"']\s*\))",
                "label": "Selects #followBtn from the DOM",
                "concept": "querySelector",
            },
            {
                "id": "select_count",
                "requirement_index": 0,
                "type": "regex",
                "file": "script.js",
                "pattern": r"(getElementById\(\s*[\"']followerCount[\"']\s*\)|querySelector\(\s*[\"']#followerCount[\"']\s*\))",
                "label": "Selects #followerCount from the DOM",
                "concept": "querySelector",
            },
            {
                "id": "listener",
                "requirement_index": 1,
                "type": "regex",
                "file": "script.js",
                "pattern": r"addEventListener\(\s*[\"']click[\"']",
                "label": "Registers a click event listener",
                "concept": "event listeners",
                "hint": "Use element.addEventListener(\"click\", handler) rather than inline onclick attributes.",
            },
            {
                "id": "toggle_text",
                "requirement_index": 2,
                "type": "regex",
                "file": "script.js",
                "pattern": r"[\"']Following[\"']",
                "label": "Uses the \"Following\" label when toggled on",
                "concept": "DOM updates",
            },
            {
                "id": "update_text",
                "requirement_index": 4,
                "type": "regex",
                "file": "script.js",
                "pattern": r"(textContent|innerText)\s*=",
                "label": "Writes back to the DOM via textContent",
                "concept": "DOM updates",
            },
        ],
        "behaviour": {
            "prelude": "",
            "assertions": [],
        },
    },
    # ------------------------------------------------------- Async remediation
    {
        "id": "js-async-error-handling",
        "title": "Handle Failed API Requests with async/await",
        "kind": "web",
        "practice_layer": "javascript",
        "skill_id": "js_async_error_handling",
        "technology": "JavaScript",
        "difficulty": 6,
        "estimated_minutes": 25,
        "is_remediation": True,
        "remediates_concepts": [
            "async error handling",
            "promise rejection",
            "try/catch",
            "fetch",
            "loading states",
        ],
        "summary": "A data-loading function crashes whenever the network promise rejects. Implement loadMovies so failures are handled instead of propagating.",
        "requirements": [
            "Export an async function loadMovies(fetchImpl) using async/await",
            "Return { status: \"success\", data } when the request resolves",
            "Catch rejections and return { status: \"error\", message } instead of throwing",
            "Treat a non-ok HTTP response as an error too",
            "Never let the function throw for a failed request",
        ],
        "editable_files": ["solution.js"],
        "language": "javascript",
        "files": {
            "solution.js": """/**
 * Load movies and NEVER throw.
 *
 * @param {Function} fetchImpl - fetch-like function returning a Promise
 * @returns {Promise<{status: "success"|"error", data?: any, message?: string}>}
 */
async function loadMovies(fetchImpl) {
  // TODO: await the request, handle rejection and non-ok responses.
}

module.exports = { loadMovies };
"""
        },
        "solution_files": {
            "solution.js": """async function loadMovies(fetchImpl) {
  try {
    const response = await fetchImpl("/api/movies");
    if (!response.ok) {
      return { status: "error", message: `Request failed with status ${response.status}` };
    }
    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "error", message: error.message };
  }
}

module.exports = { loadMovies };
"""
        },
        "checks": [
            {
                "id": "syntax",
                "requirement_index": None, "precondition": True,
                "type": "js_syntax",
                "file": "solution.js",
                "label": "solution.js is valid JavaScript",
                "concept": "syntax",
            },
            {
                "id": "async_fn",
                "requirement_index": 0,
                "type": "js_async_function",
                "file": "solution.js",
                "name": "loadMovies",
                "label": "loadMovies is declared async and awaits the request",
                "concept": "async/await",
            },
            {
                "id": "try_catch",
                "requirement_index": 2,
                "type": "js_try_catch_await",
                "file": "solution.js",
                "require_binding": True,
                "label": "The awaited call runs inside try/catch (error)",
                "concept": "try/catch",
                "hint": "An awaited promise that rejects throws; wrap that await in try/catch (error).",
            },
            {
                "id": "catch_handles",
                "requirement_index": 2,
                "type": "js_catch_handles",
                "file": "solution.js",
                "label": "The catch block acts on the caught error",
                "concept": "promise rejection",
                "hint": "An empty catch swallows the failure — return an error result instead.",
            },
            {
                "id": "ok_before_parse",
                "requirement_index": 3,
                "type": "js_ok_before_parse",
                "file": "solution.js",
                "label": "Checks response.ok before parsing the body",
                "concept": "HTTP status codes",
            },
            {
                "id": "not_trivial",
                "requirement_index": 0,
                "type": "js_not_trivial",
                "file": "solution.js",
                "name": "loadMovies",
                "label": "loadMovies has a real implementation",
                "concept": "async/await",
            },
        ],
        "behaviour": {
            "prelude": """
const okResponse = (data) => ({ ok: true, status: 200, json: async () => data });
const failResponse = () => ({ ok: false, status: 500, json: async () => ({}) });
""",
            "assertions": [
                {
                    "id": "success_path",
                    "requirement_index": 1,
                    "label": "returns status \"success\" with data when the request resolves",
                    "concept": "promises",
                    "expression": "const r = await loadMovies(async () => okResponse([{ id: 1 }])); return r && r.status === 'success' && Array.isArray(r.data) && r.data.length === 1;",
                },
                {
                    "id": "rejection_path",
                    "requirement_index": 2,
                    "label": "returns status \"error\" instead of throwing when the promise rejects",
                    "concept": "promise rejection",
                    "hint": "await on a rejected promise throws — catch it and return an error object.",
                    "expression": "const r = await loadMovies(async () => { throw new Error('network down'); }); return r && r.status === 'error' && typeof r.message === 'string';",
                },
                {
                    "id": "non_ok_path",
                    "requirement_index": 3,
                    "label": "treats a non-ok HTTP response as an error",
                    "concept": "HTTP status codes",
                    "expression": "const r = await loadMovies(async () => failResponse()); return r && r.status === 'error';",
                },
                {
                    "id": "never_throws",
                    "requirement_index": 4,
                    "label": "never rejects, even when fetch rejects synchronously",
                    "concept": "async error handling",
                    "expression": "try { const r = await loadMovies(() => Promise.reject(new Error('boom'))); return r && r.status === 'error'; } catch (e) { return false; }",
                },
            ],
        },
    },
    # ----------------------------------------------------------------- React
    {
        "id": "react-counter-hook",
        "title": "React — Implement the Missing useMovieSelection Hook",
        "kind": "web",
        "practice_layer": "react",
        "skill_id": "react_state",
        "technology": "React",
        "difficulty": 5,
        "estimated_minutes": 30,
        "summary": "The React app renders a movie list, but the state hook was removed. Implement useMovieSelection so selection and seat counting work.",
        "requirements": [
            "Implement useMovieSelection returning { selected, seats, selectMovie, addSeat, reset }",
            "selectMovie(movie) stores the selected movie and resets seats to 0",
            "addSeat() increases the seat count immutably",
            "reset() clears the selection",
            "Use useState (do not mutate state directly)",
        ],
        "editable_files": ["useMovieSelection.js"],
        "language": "javascript",
        "files": {
            "App.jsx": """import React from "react";
import { useMovieSelection } from "./useMovieSelection";

const MOVIES = [
  { id: 1, title: "Interstellar" },
  { id: 2, title: "Arrival" },
];

export default function App() {
  const { selected, seats, selectMovie, addSeat, reset } = useMovieSelection();

  return (
    <main>
      <ul>
        {MOVIES.map((movie) => (
          <li key={movie.id}>
            <button onClick={() => selectMovie(movie)}>{movie.title}</button>
          </li>
        ))}
      </ul>
      {selected && (
        <section>
          <h2>{selected.title}</h2>
          <p>Seats: {seats}</p>
          <button onClick={addSeat}>Add seat</button>
          <button onClick={reset}>Reset</button>
        </section>
      )}
    </main>
  );
}
""",
            "useMovieSelection.js": """// The hook implementation was removed.
// A minimal useState shim is injected by the test runner, so you can write
// idiomatic React code here.

function useMovieSelection() {
  // TODO: implement using useState
}

module.exports = { useMovieSelection };
""",
        },
        "solution_files": {
            "useMovieSelection.js": """function useMovieSelection() {
  const [selected, setSelected] = useState(null);
  const [seats, setSeats] = useState(0);

  function selectMovie(movie) {
    setSelected(movie);
    setSeats(0);
  }

  function addSeat() {
    setSeats((current) => current + 1);
  }

  function reset() {
    setSelected(null);
    setSeats(0);
  }

  return { selected, seats, selectMovie, addSeat, reset };
}

module.exports = { useMovieSelection };
"""
        },
        "checks": [
            {
                "id": "syntax",
                "requirement_index": None, "precondition": True,
                "type": "js_syntax",
                "file": "useMovieSelection.js",
                "label": "useMovieSelection.js is valid JavaScript",
                "concept": "syntax",
            },
            {
                "id": "uses_usestate",
                "requirement_index": 4,
                "type": "js_calls",
                "file": "useMovieSelection.js",
                "callee": "useState",
                "min_count": 1,
                "label": "Calls useState for state",
                "concept": "useState",
            },
            {
                "id": "not_trivial",
                "requirement_index": 0,
                "type": "js_not_trivial",
                "file": "useMovieSelection.js",
                "name": "useMovieSelection",
                "label": "useMovieSelection has a real implementation",
                "concept": "components",
            },
            {
                "id": "returns_api",
                "requirement_index": 0,
                "type": "regex",
                "file": "useMovieSelection.js",
                "pattern": r"return\s*\{[\s\S]*selectMovie[\s\S]*\}",
                "label": "Returns an object exposing selectMovie",
                "concept": "components",
            },
            {
                "id": "no_direct_mutation",
                "requirement_index": 4,
                "type": "not_regex",
                "file": "useMovieSelection.js",
                "pattern": r"(seats\s*\+\+|selected\.\w+\s*=)",
                "label": "Does not mutate state directly",
                "concept": "immutability",
                "hint": "State must be replaced via the setter, never mutated in place.",
            },
        ],
        "behaviour": {
            "prelude": """
// Tiny synchronous useState shim so hook logic can be unit tested headlessly.
let __cells = [];
let __cursor = 0;
function useState(initial) {
  const index = __cursor++;
  if (!(index in __cells)) __cells[index] = initial;
  const setter = (next) => {
    __cells[index] = typeof next === 'function' ? next(__cells[index]) : next;
  };
  return [__cells[index], setter];
}
function render(hook) {
  __cursor = 0;
  return hook();
}
function resetHooks() { __cells = []; __cursor = 0; }
""",
            "assertions": [
                {
                    "id": "initial_state",
                    "requirement_index": 0,
                    "label": "starts with no selection and zero seats",
                    "concept": "useState",
                    "expression": "resetHooks(); const api = render(useMovieSelection); return !api.selected && api.seats === 0;",
                },
                {
                    "id": "select_movie",
                    "requirement_index": 1,
                    "label": "selectMovie stores the selected movie",
                    "concept": "lifting state",
                    "expression": "resetHooks(); let api = render(useMovieSelection); api.selectMovie({ id: 7, title: 'Dune' }); api = render(useMovieSelection); return api.selected && api.selected.id === 7;",
                },
                {
                    "id": "add_seat",
                    "requirement_index": 2,
                    "label": "addSeat increments the seat count",
                    "concept": "immutability",
                    "expression": "resetHooks(); let api = render(useMovieSelection); api.selectMovie({ id: 1, title: 'A' }); api = render(useMovieSelection); api.addSeat(); api.addSeat(); api = render(useMovieSelection); return api.seats === 2;",
                },
                {
                    "id": "reset",
                    "requirement_index": 3,
                    "label": "reset clears the selection",
                    "concept": "useState",
                    "expression": "resetHooks(); let api = render(useMovieSelection); api.selectMovie({ id: 1, title: 'A' }); api = render(useMovieSelection); api.reset(); api = render(useMovieSelection); return !api.selected && api.seats === 0;",
                },
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Language challenge modules (compiler / stdin-stdout style)
# ---------------------------------------------------------------------------

ROTATE_STATEMENT = """Given an array of `n` integers and an integer `k`, rotate the array to the
right by `k` steps and print the result.

A right rotation moves the last element to the front. Rotating
`[1, 2, 3, 4, 5]` by `k = 2` produces `[4, 5, 1, 2, 3]`."""

ROTATE_IO = {
    "constraints": [
        "1 <= n <= 100000",
        "0 <= k <= 1000000000",
        "-1000000000 <= arr[i] <= 1000000000",
    ],
    "input_format": "Line 1: n and k separated by a space.\nLine 2: n space-separated integers.",
    "output_format": "A single line containing the rotated array, space-separated.",
}

ROTATE_TESTS = [
    {"name": "sample: rotate by 2", "stdin": "5 2\n1 2 3 4 5\n", "expected_stdout": "4 5 1 2 3", "hidden": False},
    {"name": "sample: single element", "stdin": "1 3\n7\n", "expected_stdout": "7", "hidden": False},
    {"name": "hidden: k equals n", "stdin": "4 4\n1 2 3 4\n", "expected_stdout": "1 2 3 4", "hidden": True},
    {"name": "hidden: k = 0", "stdin": "3 0\n9 8 7\n", "expected_stdout": "9 8 7", "hidden": True},
    {"name": "hidden: k > n", "stdin": "5 7\n1 2 3 4 5\n", "expected_stdout": "4 5 1 2 3", "hidden": True},
    {"name": "hidden: negatives", "stdin": "5 1\n-1 -2 -3 -4 -5\n", "expected_stdout": "-5 -1 -2 -3 -4", "hidden": True},
]

LANGUAGE_STARTERS = {
    "python": (
        "import sys\n\n\n"
        "def rotate(arr, k):\n"
        "    # TODO: return arr rotated right by k\n"
        "    return arr\n\n\n"
        "def main():\n"
        "    data = sys.stdin.read().split()\n"
        "    n, k = int(data[0]), int(data[1])\n"
        "    arr = [int(x) for x in data[2:2 + n]]\n"
        "    print(' '.join(map(str, rotate(arr, k))))\n\n\n"
        'if __name__ == "__main__":\n'
        "    main()\n"
    ),
    "javascript": (
        "function rotate(arr, k) {\n"
        "  // TODO: return arr rotated right by k\n"
        "  return arr;\n"
        "}\n\n"
        'const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);\n'
        "const n = data[0];\n"
        "const k = data[1];\n"
        "const arr = data.slice(2, 2 + n);\n"
        'console.log(rotate(arr, k).join(" "));\n'
    ),
    "java": (
        "import java.util.*;\n"
        "import java.io.*;\n\n"
        "public class Main {\n"
        "    static int[] rotate(int[] arr, long k) {\n"
        "        // TODO: return arr rotated right by k\n"
        "        return arr;\n"
        "    }\n\n"
        "    public static void main(String[] args) throws IOException {\n"
        "        StreamTokenizer in = new StreamTokenizer(new BufferedInputStream(System.in));\n"
        "        in.nextToken(); int n = (int) in.nval;\n"
        "        in.nextToken(); long k = (long) in.nval;\n"
        "        int[] arr = new int[n];\n"
        "        for (int i = 0; i < n; i++) { in.nextToken(); arr[i] = (int) in.nval; }\n"
        "        int[] out = rotate(arr, k);\n"
        "        StringBuilder sb = new StringBuilder();\n"
        "        for (int i = 0; i < out.length; i++) { if (i > 0) sb.append(' '); sb.append(out[i]); }\n"
        "        System.out.println(sb.toString());\n"
        "    }\n"
        "}\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "#include <stdlib.h>\n\n"
        "void rotate(int *arr, int n, long long k, int *out) {\n"
        "    /* TODO: fill out with arr rotated right by k */\n"
        "    for (int i = 0; i < n; i++) out[i] = arr[i];\n"
        "}\n\n"
        "int main(void) {\n"
        "    int n; long long k;\n"
        "    if (scanf(\"%d %lld\", &n, &k) != 2) return 0;\n"
        "    int *arr = malloc(sizeof(int) * n);\n"
        "    int *out = malloc(sizeof(int) * n);\n"
        "    for (int i = 0; i < n; i++) scanf(\"%d\", &arr[i]);\n"
        "    rotate(arr, n, k, out);\n"
        "    for (int i = 0; i < n; i++) printf(i ? \" %d\" : \"%d\", out[i]);\n"
        "    printf(\"\\n\");\n"
        "    free(arr); free(out);\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <bits/stdc++.h>\n"
        "using namespace std;\n\n"
        "vector<int> rotate_right(vector<int> arr, long long k) {\n"
        "    // TODO: return arr rotated right by k\n"
        "    return arr;\n"
        "}\n\n"
        "int main() {\n"
        "    ios::sync_with_stdio(false);\n"
        "    cin.tie(nullptr);\n"
        "    int n; long long k;\n"
        "    if (!(cin >> n >> k)) return 0;\n"
        "    vector<int> arr(n);\n"
        "    for (int i = 0; i < n; i++) cin >> arr[i];\n"
        "    vector<int> out = rotate_right(arr, k);\n"
        "    for (int i = 0; i < n; i++) cout << (i ? \" \" : \"\") << out[i];\n"
        "    cout << '\\n';\n"
        "    return 0;\n"
        "}\n"
    ),
    # Every declaration is annotated because the judge type-checks TypeScript
    # under `--strict`: an unannotated parameter is an error, and the learner
    # should be fighting the rotation, not the I/O they were handed.
    "typescript": (
        "function rotate(arr: number[], k: number): number[] {\n"
        "  // TODO: return arr rotated right by k\n"
        "  return arr;\n"
        "}\n\n"
        'const data: number[] = require("fs")\n'
        '  .readFileSync(0, "utf8")\n'
        "  .split(/\\s+/)\n"
        "  .filter((token: string) => token.length > 0)\n"
        "  .map(Number);\n"
        "const n: number = data[0];\n"
        "const k: number = data[1];\n"
        "const arr: number[] = data.slice(2, 2 + n);\n"
        'console.log(rotate(arr, k).join(" "));\n'
    ),
}

LANGUAGE_LABELS = {
    "python": ("py", "Python", "python_basics", 4),
    "javascript": ("js", "JavaScript", "js_basics", 4),
    "typescript": ("ts", "TypeScript", "typescript_basics", 4),
    "java": ("java", "Java", "java_basics", 4),
    "c": ("c", "C", "c_basics", 5),
    "cpp": ("cpp", "C++", "cpp_basics", 5),
}

for _language, (_prefix, _label, _skill, _difficulty) in LANGUAGE_LABELS.items():
    PRACTICE_MODULES.append(
        {
            "id": f"{_prefix}-array-rotate",
            "title": f"Rotate an Array by K Elements ({_label})",
            "kind": "challenge",
            "practice_layer": "algorithm",
            "skill_id": "dsa_arrays",
            "secondary_skill_id": _skill,
            "technology": _label,
            "language": _language,
            "difficulty": _difficulty,
            "estimated_minutes": 25,
            "summary": ROTATE_STATEMENT,
            "problem_statement": ROTATE_STATEMENT,
            "constraints": ROTATE_IO["constraints"],
            "input_format": ROTATE_IO["input_format"],
            "output_format": ROTATE_IO["output_format"],
            "requirements": [
                "Handle k larger than the array length",
                "Handle k = 0 without changing the array",
                "Run in linear time and avoid repeated single-step rotations",
            ],
            "editable_files": ["solution"],
            "files": {"solution": LANGUAGE_STARTERS[_language]},
            "test_cases": ROTATE_TESTS,
            "checks": [],
        }
    )


# Curriculum problems live in their own module because their test cases are
# generated and verified by a build step rather than written inline here.
PRACTICE_MODULES.extend(CURRICULUM_MODULES)

# Per-layer catalogues, split by file so each can grow independently.
PRACTICE_MODULES.extend(HTML_MODULES)
PRACTICE_MODULES.extend(CSS_MODULES)
PRACTICE_MODULES.extend(JS_MODULES)
# SQL questions are executed by `sql_judge` against fixture datasets rather than
# by the stdin/stdout judge, so they carry a `sql_spec` instead of `test_cases`.
PRACTICE_MODULES.extend(SQL_MODULES)
# The non-SQL half of the data-analyst path: cleaning, EDA, statistics,
# visualisation, dashboard and spreadsheet questions graded through stdin/stdout.
PRACTICE_MODULES.extend(ANALYTICS_MODULES)
# TypeScript basics: type-system problems, compiled with `tsc --strict` by the
# judge so a type error is a failed submission. See
# `app/data/curriculum_basics_typescript.py` and `backend/docs/typescript.md`.
PRACTICE_MODULES.extend(TYPESCRIPT_BASICS_MODULES)

_duplicate_ids = {m["id"] for m in PRACTICE_MODULES}
if len(_duplicate_ids) != len(PRACTICE_MODULES):
    raise RuntimeError("duplicate practice module id detected")

PRACTICE_MODULE_INDEX: dict[str, dict[str, Any]] = {m["id"]: m for m in PRACTICE_MODULES}
