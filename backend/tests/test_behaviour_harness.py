"""Soundness proofs for layer 2 (the behaviour harness).

The harness must be sound in both directions:
  * correct code that does not await its top-level call must PASS,
  * code whose error path never renders an error state must FAIL,
and it must be fail-closed and bounded when the learner's code hangs.
"""

from __future__ import annotations

import asyncio

from app.data.ticket_templates import ASYNC_LOADING_BEHAVIOUR
from app.services.validation_service import run_behaviour_tests

FAILURE_TESTS = ("rejection_contained", "non_ok_not_parsed")


def grade(source: str):
    return asyncio.run(
        run_behaviour_tests(
            source,
            ASYNC_LOADING_BEHAVIOUR["assertions"],
            ASYNC_LOADING_BEHAVIOUR["prelude"],
            ASYNC_LOADING_BEHAVIOUR["wrap_as"],
        )
    )


def by_id(source: str):
    return {o.id: o for o in grade(source)}


# The submission that was graded 2/3 before the fix: `catch (ero)` binds one name
# and the body references another, so the error UI never renders.
VARIANT_A = """
const movieList = document.getElementById("movieList");

async function loadMovies() {
  movieList.innerHTML = `<p id="loadingMessage">Loading movies...</p>`;
  try {
    const response = await fetch("/api/movies");
    if (!response.ok) {
      throw new Error(`Failed to load movies: ${response.status}`);
    }
    const movies = await response.json();
    movieList.innerHTML = "";
    movies.forEach((movie) => {
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `<h3>${movie.title}</h3>`;
      movieList.appendChild(card);
    });
  } catch (ero) {
    console.error("Movie loading failed:", error);
    movieList.innerHTML = `
      <p id="errorMessage" class="error" role="alert">
        Unable to load movies. Please try again.
      </p>
    `;
  }
}

loadMovies();
"""

# The same submission, corrected: the catch binding matches, cards are built with
# createElement/appendChild, and the top-level call is NOT awaited.
VARIANT_B = VARIANT_A.replace("catch (ero)", "catch (error)")

CONSOLE_ONLY = """
const movieList = document.getElementById("movieList");

async function loadMovies() {
  movieList.innerHTML = `<p>Loading movies...</p>`;
  try {
    const response = await fetch("/api/movies");
    if (!response.ok) {
      throw new Error("bad status");
    }
    const movies = await response.json();
    movieList.innerHTML = movies.map((m) => `<li>${m.title}</li>`).join("");
  } catch (error) {
    console.error(error);
  }
}

loadMovies();
"""

LOADING_ONLY = """
const movieList = document.getElementById("movieList");

async function loadMovies() {
  movieList.innerHTML = `<p class="spinner">Loading movies...</p>`;
  try {
    const response = await fetch("/api/movies");
    const movies = await response.json();
    movieList.innerHTML = `<p class="spinner">Loading movies...</p>`;
  } catch (error) {
    movieList.innerHTML = `<p class="spinner">Loading movies...</p>`;
  }
}

loadMovies();
"""

FAKE_NETWORK = """
const movieList = document.getElementById("movieList");

async function loadMovies() {
  try {
    const response = await Promise.resolve({ ok: true, status: 200, json: async () => [] });
    if (!response.ok) {
      throw new Error("Request failed");
    }
    const movies = await response.json();
    movieList.innerHTML = "<ul></ul>";
  } catch (error) {
    movieList.innerHTML = `<p class="error">Unable to load movies.</p>`;
  }
}

loadMovies();
"""

VARIED_WORDINGS = [
    "Something went wrong.",
    "Could not fetch the movies.",
    "Sorry — the movies are unavailable right now.",
    "Loading failed. Please try again.",
]


def _plain_error_message(message: str) -> str:
    """A correct submission whose error text carries no error class or id."""
    return (
        "const movieList = document.getElementById('movieList');\n"
        "async function loadMovies() {\n"
        "  movieList.textContent = 'Loading movies...';\n"
        "  try {\n"
        "    const response = await fetch('/api/movies');\n"
        "    if (!response.ok) { throw new Error('bad status'); }\n"
        "    const movies = await response.json();\n"
        "    movieList.innerHTML = movies.map((m) => `<li>${m.title}</li>`).join('');\n"
        "  } catch (error) {\n"
        f"    movieList.textContent = {message!r};\n"
        "  }\n"
        "}\n"
        "loadMovies();\n"
    )


# ------------------------------------------------------------- outcomes 1 & 2


def test_variant_a_fails_because_its_catch_block_throws():
    outcomes = by_id(VARIANT_A)
    for test_id in FAILURE_TESTS:
        assert outcomes[test_id].passed is False, test_id
        detail = outcomes[test_id].detail or ""
        assert "ReferenceError" in detail or "error state" in detail, detail


def test_variant_b_passes_without_awaiting_the_top_level_call():
    failed = [(o.id, o.detail) for o in grade(VARIANT_B) if not o.passed]
    assert failed == []


# ----------------------------------------------------------- outcomes 3, 4, 5


def test_console_error_only_fails_the_failure_path():
    outcomes = by_id(CONSOLE_ONLY)
    for test_id in FAILURE_TESTS:
        assert outcomes[test_id].passed is False, test_id


def test_loading_indicator_alone_is_not_an_error_state():
    outcomes = by_id(LOADING_ONLY)
    for test_id in FAILURE_TESTS:
        assert outcomes[test_id].passed is False, test_id


def test_hardcoded_resolved_promise_still_fails():
    outcomes = by_id(FAKE_NETWORK)
    for test_id in FAILURE_TESTS:
        assert outcomes[test_id].passed is False, test_id


# ------------------------------------------------------------------ fairness


def test_varied_error_wordings_are_all_accepted():
    for message in VARIED_WORDINGS:
        outcomes = by_id(_plain_error_message(message))
        for test_id in FAILURE_TESTS:
            assert outcomes[test_id].passed is True, (message, outcomes[test_id].detail)


# ------------------------------------------------------- hints and diagnostics


def test_every_outcome_carries_a_hint_and_failures_carry_a_detail():
    for outcome in grade(VARIANT_A):
        assert outcome.hint, outcome.id
        if not outcome.passed:
            assert outcome.detail, outcome.id


# ------------------------------------------------------- bounded / fail closed


def test_a_promise_that_never_settles_fails_instead_of_hanging():
    source = """
const movieList = document.getElementById("movieList");
async function loadMovies() {
  movieList.innerHTML = "<p>Loading movies...</p>";
  await new Promise(() => {});
  movieList.innerHTML = "<p class='error'>Unable to load movies.</p>";
}
loadMovies();
"""
    assert [o.id for o in grade(source) if o.passed] == []


def test_a_self_rescheduling_interval_fails_instead_of_hanging():
    source = """
const movieList = document.getElementById("movieList");
setInterval(() => { movieList.innerHTML = "<p>Loading movies...</p>"; }, 1);
async function loadMovies() {
  try {
    const response = await fetch("/api/movies");
    const movies = await response.json();
  } catch (error) {
    console.error(error);
  }
}
loadMovies();
"""
    assert [o.id for o in grade(source) if o.passed] == []


def test_a_slow_but_finite_render_still_passes():
    """Learner delays are compressed, so a debounced render is not a failure."""
    source = """
const movieList = document.getElementById("movieList");
async function loadMovies() {
  movieList.innerHTML = "<p>Loading movies...</p>";
  try {
    const response = await fetch("/api/movies");
    if (!response.ok) { throw new Error("bad status"); }
    const movies = await response.json();
    await new Promise((resolve) => setTimeout(resolve, 500));
    movieList.innerHTML = movies.map((m) => `<li>${m.title}</li>`).join("");
  } catch (error) {
    await new Promise((resolve) => setTimeout(resolve, 500));
    movieList.innerHTML = `<p class="error">Unable to load movies.</p>`;
  }
}
loadMovies();
"""
    failed = [(o.id, o.detail) for o in grade(source) if not o.passed]
    assert failed == []


def test_unparseable_code_never_passes():
    outcomes = grade("try { await loadMovies(); } catch () { }")
    assert len(outcomes) == 1
    assert outcomes[0].passed is False


def test_dom_stub_supports_the_apis_earlier_tickets_require():
    """A live region and a container-scoped query must not kill the whole run.

    Earlier tickets require a selection summary in an `aria-live` region, and the
    ticket that asks for it does not let the learner edit `index.html`, so
    `container.parentNode.insertBefore(...)` is the only way to add it. The stub
    element had no `parentNode`, so this threw
    "Cannot read properties of undefined (reading 'insertBefore')" and every
    assertion in the later async ticket failed with an error blaming the learner.
    """
    source = """
const movieList = document.getElementById("movieList");

const summary = document.createElement("p");
summary.setAttribute("aria-live", "polite");
movieList.parentNode.insertBefore(summary, movieList);

async function loadMovies() {
  movieList.innerHTML = `<p>Loading movies...</p>`;
  try {
    const response = await fetch("/api/movies");
    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }
    const movies = await response.json();
    // Container-scoped query: also unavailable on the stub element before the
    // fix ("querySelectorAll is not a function").
    movieList.querySelectorAll(".card").forEach((card) => card.remove());
    movieList.innerHTML = "";
    movies.forEach((movie) => {
      const card = document.createElement("li");
      card.className = "card";
      card.textContent = movie.title;
      movieList.appendChild(card);
    });
  } catch (error) {
    movieList.innerHTML = `<p role="alert">Could not load movies. ${error.message}</p>`;
  }
}
loadMovies();
"""
    failed = [(o.id, o.detail) for o in grade(source) if not o.passed]
    assert failed == []


def test_a_missing_node_binary_fails_closed(monkeypatch):
    from app.services import code_execution_service as ces

    monkeypatch.setattr(ces.shutil, "which", lambda _name: None)
    outcomes = grade(VARIANT_B)
    assert [o.passed for o in outcomes] == [False]
