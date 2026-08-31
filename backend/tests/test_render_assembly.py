"""Rendered checks are graded against the runnable page, not one file in isolation.

A ticket owns only the files it lets the learner edit, so a CSS-only ticket holds
`styles.css` and nothing else. Rendering that alone has no meaning — there is no
document for the stylesheet to style — and every rendered check on such a ticket
failed with "no entry document 'index.html' in this submission".

The fix widens exactly one thing: the file map handed to the render sandbox. The
last test here is the guard on that — text and AST checks still read only the
files this ticket owns, so widening the page cannot hand out credit for work the
learner did in a different ticket.

Assembly is asserted without a browser: the "no entry document" verdict comes
from assembly, before Chromium is ever needed, so its absence proves the page was
composed. The rendered outcome itself is only asserted where Chromium exists.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.models import LearningDigitalTwin, Project, Sprint, Ticket, User
from app.services import render_judge, ticket_service

BROWSER_AVAILABLE = render_judge.is_available()
needs_browser = pytest.mark.skipif(
    not BROWSER_AVAILABLE,
    reason="headless Chromium is not installed (`playwright install chromium`)",
)

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Movie Ticket Booking</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <header class="site-header"><h1 class="wordmark">Cinephile</h1></header>
    <main id="app"><section id="movieList"></section></main>
    <script src="script.js"></script>
  </body>
</html>
"""

DARK_CSS = "body { margin: 0; background-color: #0b0c10; color: #e8e8ea; }"
SCRIPT = """
document.getElementById('movieList').innerHTML =
  '<article class="movie-card">Dune</article>';
"""

NO_ENTRY = "no entry document"


def build_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def build_project(db):
    user = User(email="assembly@example.com", name="Assembly", hashed_password="x")
    db.add(user)
    db.flush()
    db.add(LearningDigitalTwin(user_id=user.id))
    project = Project(
        user_id=user.id,
        title="Movie Ticket Booking System",
        idea="book tickets",
        tech_stack=["HTML", "CSS", "JavaScript"],
    )
    db.add(project)
    db.flush()
    sprint = Sprint(
        project_id=project.id, name="Build", milestone="Foundation", order_index=1
    )
    db.add(sprint)
    db.flush()
    return project, sprint


def add_ticket(
    db,
    sprint,
    key,
    order_index,
    *,
    files: dict[str, str],
    status: str = "done",
    checks: list[dict] | None = None,
):
    """A ticket owning exactly `files`, the way the generator builds them."""
    ticket = Ticket(
        sprint_id=sprint.id,
        key=key,
        title=key,
        description="task",
        target_skill_id="css_layout",
        order_index=order_index,
        status=status,
        validation_spec={"checks": checks or []},
        starter_files={name: "" for name in files},
        workspace_files=dict(files),
    )
    db.add(ticket)
    db.flush()
    return ticket


def results(db, ticket, files):
    outcome = asyncio.run(ticket_service.run_ticket(db, ticket, files))
    return {r["label"]: r for r in outcome["static_results"]}


def assert_assembled(result):
    """The page was composed; the verdict came from rendering or from its absence."""
    assert NO_ENTRY not in result["detail"], result["detail"]
    if BROWSER_AVAILABLE:
        assert result["passed"], result["detail"]


# --------------------------------------------------------------------------
# 1-4: every single-editable-file shape renders
# --------------------------------------------------------------------------


def test_css_only_ticket_renders_against_the_provided_document():
    db = build_session()
    _, sprint = build_project(db)
    add_ticket(db, sprint, "MTB-1", 1, files={"index.html": INDEX_HTML})
    css = add_ticket(
        db,
        sprint,
        "MTB-3",
        3,
        files={"styles.css": ""},
        status="in_progress",
        checks=[
            {
                "id": "bg",
                "label": "page background",
                "type": "render_color",
                "selector": "body",
                "property": "background-color",
                "max_luminance": 0.2,
            }
        ],
    )

    assert_assembled(results(db, css, {"styles.css": DARK_CSS})["page background"])
    # The graded workspace still holds only the file the learner may edit.
    assert set(css.workspace_files) == {"styles.css"}


def test_html_only_ticket_renders_with_the_provided_stylesheet():
    db = build_session()
    _, sprint = build_project(db)
    add_ticket(db, sprint, "MTB-1", 1, files={"styles.css": DARK_CSS})
    html = add_ticket(
        db,
        sprint,
        "MTB-2",
        2,
        files={"index.html": ""},
        status="in_progress",
        checks=[
            {
                "id": "bg",
                "label": "page background",
                "type": "render_color",
                "selector": "body",
                "property": "background-color",
                "max_luminance": 0.2,
            }
        ],
    )

    assert_assembled(results(db, html, {"index.html": INDEX_HTML})["page background"])


def test_js_only_ticket_renders_with_provided_html_and_css():
    db = build_session()
    _, sprint = build_project(db)
    add_ticket(db, sprint, "MTB-1", 1, files={"index.html": INDEX_HTML})
    add_ticket(db, sprint, "MTB-3", 3, files={"styles.css": DARK_CSS})
    js = add_ticket(
        db,
        sprint,
        "MTB-6",
        6,
        files={"script.js": ""},
        status="in_progress",
        checks=[
            {
                "id": "card",
                "label": "card rendered",
                "type": "render_visible",
                "selector": ".movie-card",
                "non_empty": True,
            }
        ],
    )

    assert_assembled(results(db, js, {"script.js": SCRIPT})["card rendered"])


def test_multi_file_ticket_assembles_all_of_its_editable_files():
    db = build_session()
    _, sprint = build_project(db)
    ticket = add_ticket(
        db,
        sprint,
        "MTB-1",
        1,
        files={"index.html": "", "styles.css": "", "script.js": ""},
        status="in_progress",
        checks=[
            {
                "id": "bg",
                "label": "page background",
                "type": "render_color",
                "selector": "body",
                "property": "background-color",
                "max_luminance": 0.2,
            },
            {
                "id": "card",
                "label": "card rendered",
                "type": "render_visible",
                "selector": ".movie-card",
                "non_empty": True,
            },
        ],
    )

    graded = results(
        db,
        ticket,
        {"index.html": INDEX_HTML, "styles.css": DARK_CSS, "script.js": SCRIPT},
    )
    assert_assembled(graded["page background"])
    assert_assembled(graded["card rendered"])


# --------------------------------------------------------------------------
# 5: a genuinely missing document is an error, never a pass
# --------------------------------------------------------------------------


def test_missing_entry_document_reports_an_assembly_error():
    db = build_session()
    _, sprint = build_project(db)
    orphan = add_ticket(
        db,
        sprint,
        "MTB-3",
        3,
        files={"styles.css": ""},
        status="in_progress",
        checks=[
            {
                "id": "bg",
                "label": "page background",
                "type": "render_color",
                "selector": "body",
                "property": "background-color",
                "max_luminance": 0.2,
            }
        ],
    )

    verdict = results(db, orphan, {"styles.css": DARK_CSS})["page background"]
    assert not verdict["passed"]
    assert NO_ENTRY in verdict["detail"]


# --------------------------------------------------------------------------
# 6: the guard — a wider page must not make any check easier to pass
# --------------------------------------------------------------------------


def test_text_checks_still_see_only_this_tickets_files():
    """The renderer gets the whole page; a text check still gets one ticket's file.

    `<header class="site-header">` exists in the provided `index.html`, so the
    render sandbox can see it. A regex check scoped to `index.html` on a ticket
    that does not own that file must still fail: the learner did not write it
    here, and crediting them would be a false pass.
    """
    db = build_session()
    _, sprint = build_project(db)
    add_ticket(db, sprint, "MTB-1", 1, files={"index.html": INDEX_HTML})
    css = add_ticket(
        db,
        sprint,
        "MTB-3",
        3,
        files={"styles.css": ""},
        status="in_progress",
        checks=[
            {
                "id": "markup",
                "label": "header markup",
                "type": "regex",
                "file": "index.html",
                "pattern": "site-header",
            },
            {
                "id": "own",
                "label": "own stylesheet",
                "type": "regex",
                "file": "styles.css",
                "pattern": "background-color",
            },
            {
                "id": "bg",
                "label": "page background",
                "type": "render_color",
                "selector": "body",
                "property": "background-color",
                "max_luminance": 0.2,
            },
        ],
    )

    graded = results(db, css, {"styles.css": DARK_CSS})
    assert not graded["header markup"]["passed"]
    # The learner's own file still grades normally, and the page still renders.
    assert graded["own stylesheet"]["passed"]
    assert NO_ENTRY not in graded["page background"]["detail"]


# --------------------------------------------------------------------------
# The debug field: off unless switched on, and never a leak when it is
# --------------------------------------------------------------------------

RENDER_CHECKS = [
    {
        "id": "bg",
        "label": "page background",
        "type": "render_color",
        "selector": "body",
        "property": "background-color",
        "max_luminance": 0.2,
    },
    {
        "id": "secret_scale_case",
        "label": "hidden expectation nobody should see",
        "type": "regex",
        "file": "styles.css",
        "pattern": "background-color",
        "hidden": True,
    },
]


def debug_scenario(db):
    _, sprint = build_project(db)
    add_ticket(db, sprint, "MTB-1", 1, files={"index.html": INDEX_HTML})
    return add_ticket(
        db,
        sprint,
        "MTB-3",
        3,
        files={"styles.css": ""},
        status="in_progress",
        checks=RENDER_CHECKS,
    )


def test_render_debug_is_absent_by_default():
    db = build_session()
    ticket = debug_scenario(db)

    outcome = asyncio.run(ticket_service.run_ticket(db, ticket, {"styles.css": DARK_CSS}))

    assert "render_debug" not in outcome


def test_render_debug_stays_off_in_production_even_when_set(monkeypatch):
    monkeypatch.setattr(settings, "RENDER_ASSEMBLY_DEBUG", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    db = build_session()
    ticket = debug_scenario(db)

    outcome = asyncio.run(ticket_service.run_ticket(db, ticket, {"styles.css": DARK_CSS}))

    assert "render_debug" not in outcome


def test_render_debug_reports_the_assembled_bundle_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "RENDER_ASSEMBLY_DEBUG", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    db = build_session()
    ticket = debug_scenario(db)

    outcome = asyncio.run(ticket_service.run_ticket(db, ticket, {"styles.css": DARK_CSS}))

    debug = outcome["render_debug"]
    # The whole point: the provided document is visibly part of the bundle, and
    # it is the entry the rendered checks resolved to.
    assert debug["files"] == ["index.html", "styles.css"]
    assert debug["entry"] == "index.html"
    assert debug["missing_entries"] == []
    assert set(debug["hashes"]) == {"index.html", "styles.css"}
    assert all(h.startswith("sha256:") for h in debug["hashes"].values())
    # A hash identifies content; it never carries it.
    assert debug["hashes"]["styles.css"] != debug["hashes"]["index.html"]


def test_render_debug_carries_no_file_bodies_or_check_data(monkeypatch):
    monkeypatch.setattr(settings, "RENDER_ASSEMBLY_DEBUG", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    db = build_session()
    ticket = debug_scenario(db)

    debug = asyncio.run(ticket_service.run_ticket(db, ticket, {"styles.css": DARK_CSS}))[
        "render_debug"
    ]
    serialised = json.dumps(debug)

    # No bodies, from either side of the bundle.
    assert "background-color" not in serialised
    assert "site-header" not in serialised
    assert "<html" not in serialised
    # Nothing about the checks: a hidden check's existence, id, label and target
    # are all outside what this field describes.
    for leak in ("secret_scale_case", "hidden expectation", "render_color", "hidden"):
        assert leak not in serialised


def test_render_debug_names_the_missing_entry_document(monkeypatch):
    """The field's reason for existing: diagnosing the failure without the database."""
    monkeypatch.setattr(settings, "RENDER_ASSEMBLY_DEBUG", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    db = build_session()
    _, sprint = build_project(db)
    orphan = add_ticket(
        db,
        sprint,
        "MTB-3",
        3,
        files={"styles.css": ""},
        status="in_progress",
        checks=RENDER_CHECKS,
    )

    debug = asyncio.run(ticket_service.run_ticket(db, orphan, {"styles.css": DARK_CSS}))[
        "render_debug"
    ]

    assert debug["files"] == ["styles.css"]
    assert debug["entry"] is None
    assert debug["missing_entries"] == ["index.html"]


def test_render_debug_is_omitted_when_a_ticket_has_no_rendered_checks(monkeypatch):
    monkeypatch.setattr(settings, "RENDER_ASSEMBLY_DEBUG", True)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    db = build_session()
    _, sprint = build_project(db)
    ticket = add_ticket(
        db,
        sprint,
        "MTB-1",
        1,
        files={"styles.css": ""},
        status="in_progress",
        checks=[
            {"id": "own", "label": "own", "type": "regex", "file": "styles.css", "pattern": "body"}
        ],
    )

    outcome = asyncio.run(ticket_service.run_ticket(db, ticket, {"styles.css": DARK_CSS}))

    assert "render_debug" not in outcome
