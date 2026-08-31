"""Cumulative preview: the file map shipped to the client, and the project view.

The workspace pane recomposes the preview locally from `preview_files` plus the
live editor buffers, so that map is now part of the contract: it has to be the
exact set the server rendered from, it has to be the learner's own work and
nothing else, and it must stay clear of grading.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import LearningDigitalTwin, Project, Sprint, Ticket, User
from app.services import project_preview_service, ticket_service

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Movie Ticket Booking</title>
  </head>
  <body>
    <main id="app"><section id="movieList"></section></main>
  </body>
</html>
"""

DARK_CSS = "body { background: #0b0c10; color: #e8e8ea; }"

# The same near-empty template every styling ticket on a board is handed.
CSS_STARTER = "/* styles */\nbody {\n}\n"


def build_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed(db, *, html_done: bool = True):
    """A project shaped like the reported one: HTML shipped, CSS ticket open."""
    user = User(email="preview@example.com", name="Preview", hashed_password="x")
    db.add(user)
    db.flush()
    db.add(LearningDigitalTwin(user_id=user.id))
    project = Project(
        user_id=user.id,
        title="Movie Ticket Booking System",
        idea="book tickets",
        tech_stack=["HTML", "CSS"],
    )
    db.add(project)
    db.flush()

    structure = Sprint(
        project_id=project.id, name="Structure", milestone="Foundation", order_index=1
    )
    styling = Sprint(project_id=project.id, name="Styling", milestone="Interface", order_index=2)
    db.add_all([structure, styling])
    db.flush()

    db.add(
        Ticket(
            sprint_id=structure.id,
            key="MTB-1",
            title="Build the page shell",
            description="markup",
            target_skill_id="html_semantic_structure",
            order_index=1,
            status="done" if html_done else "in_progress",
            starter_files={"index.html": ""},
            workspace_files={"index.html": INDEX_HTML},
        )
    )

    css_ticket = Ticket(
        sprint_id=styling.id,
        key="MTB-4",
        title="Style the movie cards and grid",
        description="styles",
        target_skill_id="css_layout",
        order_index=1,
        status="in_progress",
        validation_spec={"checks": []},
        # The reported shape: this workspace owns only the stylesheet.
        starter_files={"styles.css": ""},
        workspace_files={"styles.css": ""},
    )
    db.add(css_ticket)
    db.flush()
    return project, css_ticket


def test_css_only_ticket_ships_the_cumulative_file_map():
    db = build_session()
    _, ticket = seed(db)

    payload = ticket_service.ticket_to_dict(ticket, include_files=True, db=db)

    # The ticket's own workspace is still only its stylesheet — that is what the
    # editor opens and what grading reads.
    assert set(payload["files"]) == {"styles.css"}
    # The preview map additionally carries the project's HTML, which is the only
    # reason a CSS-only ticket can be rendered at all.
    assert "index.html" in payload["preview_files"]
    assert payload["preview_files"]["index.html"] == INDEX_HTML
    assert set(payload["preview_files"]) == set(payload["preview_meta"]["files"])


def test_preview_files_contain_only_the_learners_own_work():
    db = build_session()
    _, ticket = seed(db)
    payload = ticket_service.ticket_to_dict(ticket, include_files=True, db=db)

    stored = {"index.html", "styles.css"}
    assert set(payload["preview_files"]) <= stored
    # Nothing solution-shaped or test-shaped leaks into the display payload.
    assert not any(
        "solution" in name or "test" in name or "expected" in name
        for name in payload["preview_files"]
    )


def test_unverified_tickets_do_not_contribute():
    db = build_session()
    _, ticket = seed(db, html_done=False)
    payload = ticket_service.ticket_to_dict(ticket, include_files=True, db=db)

    # The HTML ticket is still in progress, so its markup is not project state.
    assert "index.html" not in payload["preview_files"]
    assert payload["preview_meta"]["contributing_tickets"] == ["MTB-4"]


def test_live_buffers_win_over_the_stored_copy():
    db = build_session()
    _, ticket = seed(db)

    result = asyncio.run(ticket_service.run_ticket(db, ticket, {"styles.css": DARK_CSS}))

    assert DARK_CSS in (result["preview"] or "")
    assert result["preview_files"]["styles.css"] == DARK_CSS


def test_preview_never_reaches_grading():
    db = build_session()
    _, ticket = seed(db)
    before = dict(ticket.workspace_files or {})

    project_preview_service.build_project_preview(db, ticket, {"styles.css": DARK_CSS})
    assert ticket.workspace_files == before

    asyncio.run(ticket_service.run_ticket(db, ticket, {"styles.css": DARK_CSS}))
    # Only the ticket's own editable file is persisted: the cumulative HTML and
    # the synthesized host stay out of the graded workspace.
    assert set(ticket.workspace_files) == {"styles.css"}


def test_project_preview_assembles_verified_work():
    db = build_session()
    project, _ = seed(db)

    result = project_preview_service.build_preview_for_project(db, project.id, project.title)

    assert 'id="movieList"' in (result["html"] or "")
    assert result["meta"]["verified_tickets"] == 1
    assert result["meta"]["total_tickets"] == 2
    assert result["meta"]["contributing_tickets"] == ["MTB-1"]
    assert result["meta"]["verified_contributors"] == ["MTB-1"]
    # The open CSS ticket holds nothing but its untouched starter file, so there
    # is no unfinished work to report.
    assert result["meta"]["in_progress_contributors"] == []
    assert result["meta"]["includes_unverified"] is False


def test_project_preview_layers_in_unfinished_work():
    db = build_session()
    project, ticket = seed(db, html_done=False)
    ticket.workspace_files = {"styles.css": DARK_CSS}
    db.flush()

    result = project_preview_service.build_preview_for_project(db, project.id, project.title)

    # Nothing is verified, yet the learner's half-built product renders.
    assert result["meta"]["verified_tickets"] == 0
    assert result["meta"]["verified_contributors"] == []
    assert 'id="movieList"' in (result["html"] or "")
    assert DARK_CSS in (result["html"] or "")

    assert result["meta"]["includes_unverified"] is True
    unfinished = result["meta"]["unfinished_tickets"]
    assert [c["key"] for c in unfinished] == ["MTB-1", "MTB-4"]
    assert all(c["verified"] is False and c["incomplete"] for c in unfinished)
    assert unfinished[0]["title"] == "Build the page shell"
    assert unfinished[0]["ticket_id"]
    assert unfinished[1]["files"] == ["styles.css"]


def test_verified_work_is_never_reported_as_verified_when_it_is_not():
    db = build_session()
    project, ticket = seed(db)
    ticket.workspace_files = {"styles.css": DARK_CSS}
    db.flush()

    meta = project_preview_service.build_preview_for_project(
        db, project.id, project.title
    )["meta"]

    assert meta["verified_contributors"] == ["MTB-1"]
    assert [c["key"] for c in meta["in_progress_contributors"]] == ["MTB-4"]
    # The verified count tracks the board, not what happens to be rendering.
    assert meta["verified_tickets"] == 1


def test_a_throwing_half_written_script_still_renders_the_page():
    db = build_session()
    project, ticket = seed(db)
    ticket.starter_files = {"script.js": ""}
    ticket.workspace_files = {"script.js": "document.querySelector('#nope').textContent = 1;"}
    db.flush()

    html = project_preview_service.build_preview_for_project(
        db, project.id, project.title
    )["html"] or ""

    assert 'id="movieList"' in html
    assert "try {" in html and "catch (error)" in html


def test_stylesheet_is_applied_even_when_the_html_never_linked_it():
    db = build_session()
    project, ticket = seed(db)
    ticket.workspace_files = {"styles.css": DARK_CSS}
    db.flush()

    # The seeded markup carries no <link>, which is the common case: the HTML was
    # written in an earlier ticket, before the stylesheet existed.
    assert "styles.css" not in INDEX_HTML

    result = project_preview_service.build_project_preview(db, ticket)
    assert DARK_CSS in (result["html"] or "")


def test_non_browser_files_are_not_injected_into_the_page():
    db = build_session()
    project, ticket = seed(db)
    ticket.workspace_files = {
        "styles.css": DARK_CSS,
        "server.js": "require('http').createServer().listen(3000);",
    }
    db.flush()

    html = project_preview_service.build_project_preview(db, ticket)["html"] or ""
    assert DARK_CSS in html
    # Node server code would throw in the iframe rather than render anything.
    assert "createServer" not in html


def add_styling_ticket(db, project, key, order_index, *, status, workspace=None):
    """Another styling ticket on the same board, handed the same CSS template."""
    sprint = (
        db.query(Sprint)
        .filter(Sprint.project_id == project.id, Sprint.name == "Styling")
        .one()
    )
    ticket = Ticket(
        sprint_id=sprint.id,
        key=key,
        title=f"Styling work {key}",
        description="styles",
        target_skill_id="css_layout",
        order_index=order_index,
        status=status,
        validation_spec={"checks": []},
        starter_files={"styles.css": CSS_STARTER},
        workspace_files={"styles.css": CSS_STARTER if workspace is None else workspace},
    )
    db.add(ticket)
    db.flush()
    return ticket


def test_a_later_untouched_ticket_cannot_erase_an_earlier_ticket():
    """The reported bug: five done tickets, the last untouched, and no CSS at all."""
    db = build_session()
    project, earlier = seed(db)
    earlier.status = "done"
    earlier.starter_files = {"styles.css": CSS_STARTER}
    earlier.workspace_files = {"styles.css": DARK_CSS}
    # A later styling ticket marked done whose stylesheet was never edited: it
    # holds the same template every styling ticket is handed.
    add_styling_ticket(db, project, "MTB-5", 2, status="done")
    db.flush()

    result = project_preview_service.build_preview_for_project(db, project.id, project.title)
    html = result["html"] or ""

    assert DARK_CSS in html
    assert CSS_STARTER not in html
    # The untouched ticket contributed nothing, so it is not a contributor.
    assert result["meta"]["contributing_tickets"] == ["MTB-1", "MTB-4"]


def test_the_open_ticket_s_untouched_starter_does_not_erase_earlier_css():
    """Opening the last styling ticket must not blank out the project's styles."""
    db = build_session()
    project, earlier = seed(db)
    earlier.status = "done"
    earlier.starter_files = {"styles.css": CSS_STARTER}
    earlier.workspace_files = {"styles.css": DARK_CSS}
    open_ticket = add_styling_ticket(db, project, "MTB-5", 2, status="in_progress")
    db.flush()

    html = project_preview_service.build_project_preview(db, open_ticket)["html"] or ""

    assert DARK_CSS in html
    assert CSS_STARTER not in html


def test_a_later_emptied_ticket_cannot_erase_an_earlier_ticket():
    db = build_session()
    project, earlier = seed(db)
    earlier.status = "done"
    earlier.workspace_files = {"styles.css": DARK_CSS}
    # Blanked rather than left untouched — an empty file can only remove pixels.
    add_styling_ticket(db, project, "MTB-5", 2, status="done", workspace="   \n")
    db.flush()

    html = (
        project_preview_service.build_preview_for_project(db, project.id, project.title)["html"]
        or ""
    )
    assert DARK_CSS in html


def test_a_ticket_opens_onto_the_previous_ticket_s_work():
    db = build_session()
    project, earlier = seed(db)
    earlier.status = "done"
    earlier.starter_files = {"styles.css": CSS_STARTER}
    earlier.workspace_files = {"styles.css": DARK_CSS}
    later = add_styling_ticket(db, project, "MTB-5", 2, status="todo")
    db.flush()

    twin = db.query(LearningDigitalTwin).one()
    payload = ticket_service.start_ticket(db, twin, later)

    # Not the blank template: the stylesheet the previous ticket produced.
    assert later.workspace_files == {"styles.css": DARK_CSS}
    assert payload["files"]["styles.css"] == DARK_CSS
    # Still only the files this ticket owns, so grading and the editor are
    # unchanged in scope.
    assert set(payload["files"]) == {"styles.css"}


def test_starting_a_ticket_never_overwrites_existing_learner_work():
    db = build_session()
    project, earlier = seed(db)
    earlier.status = "done"
    earlier.workspace_files = {"styles.css": DARK_CSS}
    in_flight = add_styling_ticket(
        db, project, "MTB-5", 2, status="in_progress", workspace="body { color: red; }"
    )
    db.flush()

    twin = db.query(LearningDigitalTwin).one()
    ticket_service.start_ticket(db, twin, in_flight)

    assert in_flight.workspace_files == {"styles.css": "body { color: red; }"}


def test_reset_returns_to_previous_work_not_a_blank_template():
    db = build_session()
    project, earlier = seed(db)
    earlier.status = "done"
    earlier.workspace_files = {"styles.css": DARK_CSS}
    later = add_styling_ticket(
        db, project, "MTB-5", 2, status="failed", workspace="body { broken"
    )
    db.flush()

    ticket_service.reset_ticket(db, later)

    assert later.workspace_files == {"styles.css": DARK_CSS}
    assert later.status == "in_progress"


def test_reopening_a_verified_ticket_does_not_rewrite_history():
    db = build_session()
    project, earlier = seed(db)
    earlier.status = "done"
    earlier.workspace_files = {"styles.css": DARK_CSS}
    done = add_styling_ticket(
        db, project, "MTB-5", 2, status="done", workspace="body { margin: 0; }"
    )
    db.flush()

    twin = db.query(LearningDigitalTwin).one()
    ticket_service.start_ticket(db, twin, done)
    ticket_service.reset_ticket(db, done)

    # The graded record of a verified ticket is untouched by either path.
    assert done.workspace_files == {"styles.css": "body { margin: 0; }"}
    assert done.status == "done"


def test_running_a_verified_ticket_does_not_overwrite_the_graded_work():
    """Run awards nothing and re-grades nothing, so it must not rewrite history.

    Pressing Run on an already-verified ticket used to persist the scratch buffer
    over the work that had passed. The ticket kept `done` and its XP while the
    cumulative preview — composed from that same workspace — went blank, and
    every later ticket then inherited the broken file.
    """
    db = build_session()
    project, done = seed(db)
    done.status = "done"
    done.starter_files = {"styles.css": CSS_STARTER}
    done.workspace_files = {"styles.css": DARK_CSS}
    db.flush()

    scratch = "/* commented out\n" + DARK_CSS + "\n*/"
    result = asyncio.run(ticket_service.run_ticket(db, done, {"styles.css": scratch}))

    # The verified work still stands, and so does the page built from it.
    assert done.workspace_files == {"styles.css": DARK_CSS}
    html = (
        project_preview_service.build_preview_for_project(db, project.id, project.title)["html"]
        or ""
    )
    assert "background: #0b0c10" in html
    assert "commented out" not in html

    # Run still reports on the buffer the learner actually typed, so the
    # feedback describes their edit rather than the stored file.
    assert result["preview"] is not None


def test_a_ticket_does_not_inherit_from_tickets_after_it():
    db = build_session()
    project, earlier = seed(db)
    earlier.status = "todo"
    earlier.starter_files = {"styles.css": CSS_STARTER}
    earlier.workspace_files = {"styles.css": CSS_STARTER}
    add_styling_ticket(db, project, "MTB-5", 2, status="done", workspace=DARK_CSS)
    db.flush()

    twin = db.query(LearningDigitalTwin).one()
    ticket_service.start_ticket(db, twin, earlier)

    # MTB-5 comes later on the board; absorbing its stylesheet here would let the
    # earlier ticket's next save overwrite work that came after it.
    assert earlier.workspace_files == {"styles.css": CSS_STARTER}


TOKENS_CSS = ":root { --surface: #0b0c10; }\nbody { background: var(--surface); margin: 0; }"
CARDS_CSS = TOKENS_CSS + "\n#movieList { display: grid; }\n.card { border-radius: 12px; }"
RESPONSIVE_CSS = CARDS_CSS + "\n@media (max-width: 640px) { #movieList { grid-template-columns: 1fr; } }"


def test_the_whole_stylesheet_survives_a_three_ticket_chain():
    """The reported failure end to end: tokens, then cards, then the media query.

    Each ticket owns the same filename, so the only thing that keeps all three
    fragments in the finished page is that each one opens onto the last one's
    stylesheet instead of a blank template.
    """
    db = build_session()
    project, tokens = seed(db)
    tokens.status = "done"
    tokens.starter_files = {"styles.css": CSS_STARTER}
    tokens.workspace_files = {"styles.css": TOKENS_CSS}
    cards = add_styling_ticket(db, project, "MTB-5", 2, status="todo")
    responsive = add_styling_ticket(db, project, "MTB-6", 3, status="todo")
    db.flush()
    twin = db.query(LearningDigitalTwin).one()

    # The cards ticket opens onto the token block and extends it.
    ticket_service.start_ticket(db, twin, cards)
    assert cards.workspace_files["styles.css"] == TOKENS_CSS
    ticket_service.save_workspace(db, cards, {"styles.css": CARDS_CSS})
    cards.status = "done"
    db.flush()

    # The responsive ticket opens onto both, and adds the media query.
    ticket_service.start_ticket(db, twin, responsive)
    assert responsive.workspace_files["styles.css"] == CARDS_CSS
    ticket_service.save_workspace(db, responsive, {"styles.css": RESPONSIVE_CSS})
    responsive.status = "done"
    db.flush()

    html = (
        project_preview_service.build_preview_for_project(db, project.id, project.title)["html"]
        or ""
    )

    # All three tickets' work is in the one rendered document.
    assert ":root" in html and "background: var(--surface)" in html
    assert ".card" in html and "#movieList { display: grid; }" in html
    assert "@media (max-width: 640px)" in html


def test_reset_keeps_the_inherited_stylesheet_after_the_learner_breaks_it():
    db = build_session()
    project, tokens = seed(db)
    tokens.status = "done"
    tokens.starter_files = {"styles.css": CSS_STARTER}
    tokens.workspace_files = {"styles.css": TOKENS_CSS}
    cards = add_styling_ticket(db, project, "MTB-5", 2, status="todo")
    db.flush()
    twin = db.query(LearningDigitalTwin).one()

    ticket_service.start_ticket(db, twin, cards)
    ticket_service.save_workspace(db, cards, {"styles.css": "/* wiped */"})
    ticket_service.reset_ticket(db, cards)

    # Back to the project as it was handed over, not to the blank template that
    # would have deleted the token block from the finished site.
    assert cards.workspace_files == {"styles.css": TOKENS_CSS}
    html = (
        project_preview_service.build_preview_for_project(db, project.id, project.title)["html"]
        or ""
    )
    assert ":root" in html
    assert "/* wiped */" not in html


def test_project_preview_is_empty_when_there_is_no_work_at_all():
    db = build_session()
    project, ticket = seed(db, html_done=False)
    # Nothing verified and nothing written: every workspace still holds only the
    # starter files it was handed.
    for open_ticket in db.query(Ticket).all():
        open_ticket.workspace_files = dict(open_ticket.starter_files or {})
    db.flush()

    result = project_preview_service.build_preview_for_project(db, project.id, project.title)

    # No HTML to render and no files at all: the UI needs a null here so it can
    # show a real empty state rather than a blank frame.
    assert result["html"] is None
    assert result["files"] == {}
    assert result["meta"]["verified_tickets"] == 0
    assert result["meta"]["contributing_tickets"] == []
    assert result["meta"]["unfinished_tickets"] == []
    assert result["meta"]["includes_unverified"] is False
