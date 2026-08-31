"""Grade a snippet against a real ticket's live spec, without writing anything.

Reads the ticket's stored validation_spec from the database and runs both
layers (static AST checks and behaviour tests) against the source in SOURCE.
The session is rolled back, so the learner's workspace and ticket status are
untouched.

    python scripts/grade_snippet.py --ticket <id>
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.models import Ticket
from app.services.ticket_service import _run_ticket_behaviour_tests
from app.services.validation_service import run_static_checks

SOURCE = """const entity = [
  { id: 1, title: "Sample One", price: 12 },
  { id: 2, title: "Sample Two", price: 15 }
];

const movieList = document.getElementById("movieList");

async function loadMovies() {
  // Show a loading state before the request starts.
  movieList.innerHTML = `
    <p id="loadingMessage">Loading movies...</p>
  `;

  try {
    // Use the async data source.
    const response = await fetch("/api/movies");

    // Handle non-OK responses before parsing the body.
    if (!response.ok) {
      throw new Error(`Failed to load movies: ${response.status}`);
    }

    const movies = await response.json();

    // Render only after the data has successfully resolved.
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
  } catch (ero) {
    // Actually use the caught error.
    console.error("Movie loading failed:", error);

    // Show a user-visible error state.
    movieList.innerHTML = `
      <p id="errorMessage" class="error" role="alert">
        Unable to load movies. Please try again.
      </p>
    `;
  }
}

loadMovies();
"""


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticket", required=True)
    parser.add_argument("--file", default="script.js")
    parser.add_argument(
        "--source",
        help="path to the snippet to grade (defaults to the SOURCE constant above)",
    )
    args = parser.parse_args()
    source = Path(args.source).read_text(encoding="utf-8") if args.source else SOURCE

    with SessionLocal() as db:
        ticket = db.get(Ticket, args.ticket)
        if ticket is None:
            print(f"No ticket with id {args.ticket}")
            return 1

        files = {args.file: source}
        spec = ticket.validation_spec or {}
        checks = spec.get("checks", [])

        print(f"{ticket.key} — {ticket.title}")
        print(f"spec: {len(checks)} checks, behaviour={bool(spec.get('behaviour'))}\n")

        static = [r.to_dict() for r in run_static_checks(files, checks)]
        s_pass = sum(1 for r in static if r["passed"])
        print(f"static checks: {s_pass}/{len(static)}")
        for r in static:
            print(f"  [{'PASS' if r['passed'] else 'FAIL'}] {r['label']}")
            if not r["passed"] and r.get("hint"):
                print(f"         hint: {r['hint']}")

        behaviour = await _run_ticket_behaviour_tests(ticket, files)
        b_pass = sum(1 for t in behaviour if t["passed"])
        print(f"\nbehaviour tests: {b_pass}/{len(behaviour)}")
        for t in behaviour:
            print(f"  [{'PASS' if t['passed'] else 'FAIL'}] {t['label']}")
            if not t["passed"]:
                for key in ("detail", "hint"):
                    if t.get(key):
                        print(f"         {key}: {t[key]}")

        overall = s_pass == len(static) and b_pass == len(behaviour)
        print(f"\nverdict: {'PASS' if overall else 'FAIL'}")

        db.rollback()
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
