"""End-to-end proof that the strict JS validation rejects broken submissions.

Creates a throwaway in-memory project/sprint/ticket from the
`js_async_error_handling` template, submits the invalid `catch ()` code and then
the reference implementation, and prints both API-shaped responses.

    python scripts/verify_strict_validation.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.data.ticket_templates import TICKET_TEMPLATES
from app.core.database import Base
from app.models import LearningDigitalTwin, Project, Sprint, Ticket, User
from app.services import ticket_service

INVALID = """
try {
  const response = await loadMovies();
} catch () {
  movieList.innerHTML = "<p>error</p>";
}
"""

REFERENCE = """
try {
  const response = await loadMovies();
  if (!response.ok) {
    throw new Error("Request failed");
  }
  const movies = await response.json();
  renderMovies(movies);
} catch (error) {
  console.error(error);
  movieList.innerHTML = `<p class="error">Unable to load movies.</p>`;
}
"""


def build_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed(db):
    template = TICKET_TEMPLATES["js_async_error_handling"][0]
    user = User(email="strict@example.com", name="Strict", hashed_password="x")
    db.add(user)
    db.flush()
    twin = LearningDigitalTwin(user_id=user.id)
    db.add(twin)
    project = Project(user_id=user.id, title="Movie App", idea="movies", tech_stack=["JavaScript"])
    db.add(project)
    db.flush()
    sprint = Sprint(project_id=project.id, name="Async", milestone="Data Layer", order_index=1)
    db.add(sprint)
    db.flush()
    ticket = Ticket(
        sprint_id=sprint.id,
        key="MOV-1",
        title=template["title"],
        description=template["description"],
        target_skill_id="js_async_error_handling",
        difficulty=6,
        requirements=template["requirements"],
        acceptance_criteria=template["acceptance_criteria"],
        estimated_minutes=35,
        order_index=1,
        status="in_progress",
        validation_spec={
            "checks": template["checks"],
            "behaviour": template.get("behaviour") or {},
        },
        starter_files={"script.js": ""},
        workspace_files={"script.js": ""},
        xp_reward=30,
    )
    db.add(ticket)
    db.flush()
    return twin, ticket


async def main() -> int:
    db = build_session()
    twin, ticket = seed(db)

    failures = 0
    for label, source in (("INVALID `catch ()`", INVALID), ("REFERENCE", REFERENCE)):
        run = await ticket_service.run_ticket(db, ticket, {"script.js": source})
        print(f"\n===== {label} — POST /tickets/{{id}}/run =====")
        print(json.dumps({k: v for k, v in run.items() if k != "preview"}, indent=2))

        submit = await ticket_service.submit_ticket(db, twin, ticket, {"script.js": source})
        print(f"\n===== {label} — POST /tickets/{{id}}/submit =====")
        print(
            json.dumps(
                {
                    "passed": submit["passed"],
                    "ticket_status": submit["ticket"]["status"],
                    "passed_count": submit["passed_count"],
                    "total_count": submit["total_count"],
                    "tests_passed_count": submit["tests_passed_count"],
                    "tests_total_count": submit["tests_total_count"],
                    "static_results": submit["static_results"],
                    "test_results": submit["test_results"],
                },
                indent=2,
            )
        )
        expected_pass = label == "REFERENCE"
        if submit["passed"] != expected_pass:
            failures += 1
            print(f"!! {label}: expected passed={expected_pass}, got {submit['passed']}")
        ticket.status = "in_progress"
        db.flush()

    print("\nOK" if failures == 0 else f"\n{failures} unexpected outcome(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
