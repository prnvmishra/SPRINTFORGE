"""Proof that the ticket preview is cumulative across a project.

Seeds an in-memory project with a done HTML ticket followed by a JS ticket, then
asserts the JS ticket's preview contains the earlier ticket's markup and the
learner's own script. Also exercises the synthesized-host fallback and asserts
the synthesized document never reaches the graders.

    PYTHONPATH=. .venv/bin/python scripts/verify_ticket_preview.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.data.ticket_templates import TICKET_TEMPLATES
from app.models import LearningDigitalTwin, Project, Sprint, Ticket, User
from app.services import project_preview_service, ticket_service

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Movie App</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <header><h1>Movie Tracker</h1></header>
    <main id="app">
      <section id="movieList"></section>
    </main>
    <script src="script.js"></script>
  </body>
</html>
"""

SCRIPT_JS = """
const movieList = document.getElementById("movieList");
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

failures: list[str] = []


def check(label: str, condition: bool) -> None:
    print(f"{'PASS' if condition else 'FAIL'}  {label}")
    if not condition:
        failures.append(label)


def build_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed(db, *, with_html_ticket: bool):
    template = TICKET_TEMPLATES["js_async_error_handling"][0]
    user = User(email="preview@example.com", name="Preview", hashed_password="x")
    db.add(user)
    db.flush()
    twin = LearningDigitalTwin(user_id=user.id)
    db.add(twin)
    project = Project(
        user_id=user.id, title="Movie App", idea="movies", tech_stack=["JavaScript"]
    )
    db.add(project)
    db.flush()

    structure = Sprint(
        project_id=project.id, name="Structure", milestone="Foundation", order_index=1
    )
    data_layer = Sprint(
        project_id=project.id, name="Async", milestone="Data Layer", order_index=2
    )
    db.add_all([structure, data_layer])
    db.flush()

    if with_html_ticket:
        db.add(
            Ticket(
                sprint_id=structure.id,
                key="MTB-8",
                title="Build the page shell",
                description="markup",
                target_skill_id="html_semantic_structure",
                order_index=1,
                status="done",
                starter_files={"index.html": "", "styles.css": ""},
                workspace_files={
                    "index.html": INDEX_HTML,
                    "styles.css": "body { background: #101010; }",
                },
            )
        )

    js_ticket = Ticket(
        sprint_id=data_layer.id,
        key="MTB-9",
        title=template["title"],
        description=template["description"],
        target_skill_id="js_async_error_handling",
        difficulty=6,
        requirements=template["requirements"],
        acceptance_criteria=template["acceptance_criteria"],
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
    db.add(js_ticket)
    db.flush()
    return twin, js_ticket


async def main() -> int:
    # ---------------------------------------------- cumulative path
    print("=== cumulative preview (earlier HTML ticket is done) ===")
    db = build_session()
    _, ticket = seed(db, with_html_ticket=True)
    result = await ticket_service.run_ticket(db, ticket, {"script.js": SCRIPT_JS})
    html = result["preview"] or ""
    meta = result["preview_meta"]

    check("preview is non-empty", bool(html.strip()))
    check("contains the earlier ticket's markup", 'id="movieList"' in html)
    check("contains the earlier ticket's CSS inlined", "background: #101010" in html)
    check("contains the learner's script", "Unable to load movies." in html)
    check("host document was not synthesized", meta["synthesized_host"] is False)
    check("counts verified tickets", meta["verified_tickets"] == 1)
    check("counts total tickets", meta["total_tickets"] == 2)
    check(
        "credits both tickets",
        meta["contributing_tickets"] == ["MTB-8", "MTB-9"],
    )
    print(f"      meta = {meta}")

    # ---------------------------------------------- synthesized fallback
    print("\n=== synthesized host (no HTML ticket in the project) ===")
    db2 = build_session()
    _, lone = seed(db2, with_html_ticket=False)
    result2 = await ticket_service.run_ticket(db2, lone, {"script.js": SCRIPT_JS})
    html2 = result2["preview"] or ""
    meta2 = result2["preview_meta"]

    check("fallback preview is non-empty", bool(html2.strip()))
    check("fallback is flagged as synthesized", meta2["synthesized_host"] is True)
    check("mount point for #movieList exists", 'id="movieList"' in html2)
    check(
        "mount points derived, not empty",
        "movieList" in meta2["mount_points"],
    )
    check("fallback inlines the learner's script", "Unable to load movies." in html2)
    print(f"      meta = {meta2}")

    # ---------------------------------------------- grading isolation
    print("\n=== grading isolation ===")
    check(
        "synthesized index.html never enters ticket.workspace_files",
        set(lone.workspace_files.keys()) == {"script.js"},
    )
    static_labels = {r["label"] for r in result2["static_results"]}
    check("static checks still ran", len(static_labels) > 0)
    html_only = await ticket_service.run_ticket(db2, lone, {"script.js": ""})
    check(
        "empty submission still fails its checks",
        any(not r["passed"] for r in html_only["static_results"]),
    )
    check(
        "reference submission still passes its checks",
        all(r["passed"] for r in result2["static_results"]),
    )

    # Preview assembly is a pure read: prove it does not mutate stored files.
    before = dict(lone.workspace_files)
    project_preview_service.build_project_preview(db2, lone, {"script.js": SCRIPT_JS})
    check("build_project_preview does not mutate workspace_files", lone.workspace_files == before)

    print("\nOK" if not failures else f"\n{len(failures)} failure(s): {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
