"""Grade one hand-written submission against the js_async_error_handling ticket.

Used to reproduce a reported false pass. Prints every check with its verdict so
it is obvious which rule caught (or missed) the defect.

    python scripts/check_user_submission.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import ticket_service
from scripts.verify_strict_validation import build_session, seed

# Exactly as reported: line 8 is a bare `a`, so there is no function declaration
# at all, and the catch clause has no parameter binding.
SUBMISSION = """const entity = [
  { id: 1, title: "Sample One", price: 12 },
  { id: 2, title: "Sample Two", price: 15 }
];

const movieList = document.getElementById("movieList");

a
  // Show loading state while request is in progress
  movieList.innerHTML = `
    <p id="loadingMessage">Loading movies...</p>
  `;

  try {
    const response = await Promise.resolve({
      ok: true,
      json: async () => entity
    });

    // Check response.ok before parsing the body
    if (!response.ok) {
      throw new Error("Failed to load movies");
    }

    const movies = await response.json();

    // Clear loading state only after successful resolution
    movieList.innerHTML = "";

    movies.forEach((movie) => {
      const card = document.createElement("article");
      card.className = "card";

      card.innerHTML = `
        <h3>${movie.title}</h3>
        <p>Price: $${movie.price}</p>
        <button type="button">Book Ticket</button>
      `;

      movieList.appendChild(card);
    });
  } catch ()
}

loadMovies();
"""


async def main() -> int:
    db = build_session()
    twin, ticket = seed(db)

    result = await ticket_service.submit_ticket(db, twin, ticket, {"script.js": SUBMISSION})

    print(f"passed:        {result['passed']}")
    print(f"ticket status: {result['ticket']['status']}")
    print(f"checks:        {result['passed_count']}/{result['total_count']}")
    print(f"tests:         {result['tests_passed_count']}/{result['tests_total_count']}")

    print("\nstatic checks:")
    for check in result["static_results"]:
        mark = "PASS" if check["passed"] else "FAIL"
        print(f"  [{mark}] {check['label']}")
        if check.get("hint"):
            print(f"         hint: {check['hint']}")

    print("\nbehaviour tests:")
    for test in result["test_results"]:
        mark = "PASS" if test["passed"] else "FAIL"
        print(f"  [{mark}] {test['label']}")

    if result["passed"]:
        print("\n!! FALSE PASS — this submission must not pass.")
        return 1
    print("\nCorrectly rejected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
