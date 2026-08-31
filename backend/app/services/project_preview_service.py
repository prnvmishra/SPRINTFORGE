"""Cumulative project preview.

A ticket's workspace only holds its own files, so a JS-only ticket could never
render: there was no `index.html` anywhere in scope. The learner therefore never
saw the product they were building.

This module assembles a preview from the whole project — every verified ticket's
files layered in board order, then the current ticket's live buffers on top — and
synthesizes a neutral host document when the project has no HTML yet.

Display only. Nothing here is ever handed to the validators or to the behaviour
test harness; grading continues to read `ticket.workspace_files` exclusively.
"""

from __future__ import annotations

import html as html_escape
import re
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Sprint, Ticket
from app.services.practice_service import build_preview

ENTRY_FILE = "index.html"
BROWSER_SCRIPT = "script.js"

# Unverified but potentially holding work. `todo` is in the set because a ticket
# can be sent back to it — a reset against re-written templates does exactly
# that — while its workspace still holds everything the learner wrote. Dropping
# those would make the project render as if the work had been deleted. Nothing
# is layered in unconditionally: `learner_work` still ignores an untouched or
# emptied starter, so a ticket nobody has opened contributes nothing.
# `locked` stays out: it has never been openable.
IN_PROGRESS_STATUSES = {"todo", "in_progress", "failed", "under_review", "submitted"}

# `getElementById("x")` / `querySelector("#x")` and their single-quote forms.
_GET_BY_ID = re.compile(r"getElementById\(\s*[\"']([^\"']+)[\"']\s*\)")
_QUERY_SELECTOR = re.compile(r"querySelector(?:All)?\(\s*[\"']([^\"']+)[\"']\s*\)")
# `#id` or `tag#id`, optionally followed by more selector text we ignore.
_ID_SELECTOR = re.compile(r"^([a-zA-Z][\w-]*)?#([\w-]+)$")
_SAFE_ID = re.compile(r"^[A-Za-z][\w-]*$")


def _project_tickets(db: Session, project_id: str) -> list[Ticket]:
    """Every ticket in the project, in sprint-board order, in a single query."""
    tickets = list(
        db.execute(
            select(Ticket)
            .join(Sprint, Ticket.sprint_id == Sprint.id)
            .where(Sprint.project_id == project_id)
            .options(selectinload(Ticket.sprint))
        )
        .scalars()
        .all()
    )

    # Milestones have no order column of their own; the board derives their order
    # from the first sprint that carries them, so mirror that here.
    milestone_rank: dict[str, int] = {}
    for ticket in sorted(tickets, key=lambda t: (t.sprint.order_index, t.order_index)):
        milestone_rank.setdefault(ticket.sprint.milestone or "", len(milestone_rank))

    return sorted(
        tickets,
        key=lambda t: (
            milestone_rank.get(t.sprint.milestone or "", 0),
            t.sprint.order_index,
            t.order_index,
            t.key,
        ),
    )


def learner_work(ticket: Ticket) -> dict[str, str]:
    """The files in this ticket's workspace that the learner actually wrote.

    A file counts as this ticket's contribution only when it is non-blank *and*
    differs from the starter the ticket was handed. Both exclusions matter for
    composition:

    * An untouched starter is scaffolding we handed the learner, not work. Every
      styling ticket in a project ships the same near-empty `styles.css`
      template, so treating one as a contribution lets a later ticket nobody
      edited overwrite an earlier ticket's finished stylesheet.
    * A blank file carries no information for a *display* composition. Layering
      it over earlier content can only ever remove pixels from the page.

    Together these give the composition rule its one-way property: a later
    ticket can add to or rewrite the page, but it can never blank out an earlier
    ticket's work by holding nothing.
    """
    starter = ticket.starter_files or {}
    return {
        name: content
        for name, content in (ticket.workspace_files or {}).items()
        if (content or "").strip() and content != (starter.get(name) or "")
    }


def _cumulative_files(
    tickets: list[Ticket],
    current: Optional[Ticket],
    live_files: Optional[dict[str, str]],
) -> tuple[dict[str, str], list[str]]:
    """Layer verified work in board order, then the current ticket's live buffers.

    Later tickets win for the same filename — but only where the later ticket
    actually holds work for it (see `learner_work`), so the newest *written*
    `index.html` renders rather than the newest empty template. With no current
    ticket (the project-level preview) only verified work contributes.

    The current ticket's live editor buffers are the single unconditional
    override: a learner must see the edit they just ran, including deleting
    everything in a file, even before it is graded.
    """
    merged: dict[str, str] = {}
    contributors: list[str] = []

    for ticket in tickets:
        if (current is not None and ticket.id == current.id) or ticket.status != "done":
            continue
        files = learner_work(ticket)
        if not files:
            continue
        merged.update(files)
        contributors.append(ticket.key)

    if current is None:
        return merged, contributors

    # The current ticket's stored buffers. Its untouched starter files still
    # count where no earlier ticket ever wrote that filename — a skeleton
    # `index.html` we handed the learner is better to render than nothing — but
    # they must not override a file an earlier ticket actually produced, which is
    # exactly how a fresh CSS template erased the finished stylesheet.
    contributed = learner_work(current)
    own = {
        name: content
        for name, content in (current.workspace_files or current.starter_files or {}).items()
        if name in contributed or name not in merged
    }
    own.update(
        {name: content for name, content in (live_files or {}).items() if content is not None}
    )
    if own:
        merged.update(own)
        contributors.append(current.key)

    return merged, contributors


def cumulative_files_before(db: Session, ticket: Ticket) -> dict[str, str]:
    """The project's state as it stands when `ticket` opens.

    Everything the tickets ahead of it on the board actually produced, layered in
    board order. This is what a ticket should start from: "make the layout
    responsive" means nothing if the stylesheet it opens onto is blank.

    Only predecessors count. Work from later tickets is not history this ticket
    was built on, and inheriting it would let a reopened ticket absorb — and on
    the next save silently rewrite — work that came after it.
    """
    tickets = _project_tickets(db, ticket.sprint.project_id)
    inherited: dict[str, str] = {}
    for candidate in tickets:
        if candidate.id == ticket.id:
            break
        inherited.update(learner_work(candidate))
    return inherited


def provided_files(db: Session, ticket: Ticket) -> dict[str, str]:
    """The read-only documents this ticket is handed but may not edit.

    A ticket owns only the filenames it lets the learner edit, so a CSS-only
    ticket holds `styles.css` and nothing else. Rendering that in isolation is
    meaningless — there is no document for the stylesheet to style. The rest of
    the runnable page comes from the tickets ahead of it on the board: whatever
    they actually produced, and failing that the template they were handed, since
    an untouched `index.html` skeleton is still the document this ticket's CSS is
    written against.

    That is the one difference from `cumulative_files_before`, which is about the
    content a ticket *opens onto* and so counts learner work only. Only
    predecessors contribute, so a ticket can never be judged against a page a
    later ticket produced.

    Never merged into the graded file map: this is context for the renderer, and
    the caller layers the submission on top.
    """
    tickets = _project_tickets(db, ticket.sprint.project_id)
    provided: dict[str, str] = {}
    for candidate in tickets:
        if candidate.id == ticket.id:
            break
        contributed = learner_work(candidate)
        provided.update(contributed)
        for name, content in (
            candidate.workspace_files or candidate.starter_files or {}
        ).items():
            if name in contributed or name in provided:
                continue
            if (content or "").strip():
                provided[name] = content
    return provided


def _mount_ids(ticket: Optional[Ticket], files: dict[str, str]) -> list[str]:
    """DOM ids the ticket's script needs in order not to throw on load.

    Derived, never hardcoded: the ids the HTML checks assert on, plus whatever
    the cumulative script actually looks up.
    """
    ids: list[str] = []

    def add(candidate: str) -> None:
        if _SAFE_ID.match(candidate) and candidate not in ids:
            ids.append(candidate)

    for check in ((ticket.validation_spec if ticket else None) or {}).get("checks") or []:
        selector = (check or {}).get("selector")
        if not isinstance(selector, str):
            continue
        match = _ID_SELECTOR.match(selector.strip())
        if match:
            add(match.group(2))

    script = files.get("script.js", "")
    for target in _GET_BY_ID.findall(script):
        add(target)
    for selector in _QUERY_SELECTOR.findall(script):
        match = _ID_SELECTOR.match(selector.strip())
        if match:
            add(match.group(2))

    return ids


def _synthesize_host(title: str, mount_ids: list[str]) -> str:
    """A deliberately plain document so a script-only ticket still renders.

    Intentionally unstyled beyond legibility — this is a scaffold standing in for
    HTML the learner has not written yet, and it is labelled as such in the API
    response so the UI can say so.
    """
    mounts = "\n    ".join(
        f'<div id="{html_escape.escape(mount, quote=True)}"></div>' for mount in mount_ids
    )
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{html_escape.escape(title)}</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <h1>{html_escape.escape(title)}</h1>
    {mounts}
    <script src="script.js"></script>
  </body>
</html>
"""


def build_project_preview(
    db: Session,
    ticket: Ticket,
    live_files: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Preview HTML for the whole project plus metadata describing what it is."""
    tickets = _project_tickets(db, ticket.sprint.project_id)
    return _assemble(tickets, ticket, live_files, ticket.sprint.project.title)


def build_preview_for_project(db: Session, project_id: str, title: str) -> dict[str, Any]:
    """Whole-project preview: verified work, plus unfinished work layered on top.

    Same assembly as the workspace preview, so the Projects section and the
    ticket pane can never drift apart. The difference is that this view also
    layers in tickets the learner started but never got verified, because a
    half-built project that renders as empty reads as lost work. Everything
    unverified is reported as such in the metadata; nothing here is graded.
    """
    tickets = _project_tickets(db, project_id)
    return _assemble(tickets, None, None, title, include_in_progress=True)


def _in_progress_contributions(
    tickets: list[Ticket], current: Optional[Ticket]
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Files from tickets that were started but never verified, in board order.

    Same `learner_work` rule as verified tickets, for the same reason: an
    untouched or emptied starter file is not a contribution and must not undo
    shipped work.
    """
    files: dict[str, str] = {}
    contributors: list[dict[str, Any]] = []

    for ticket in tickets:
        if ticket.status not in IN_PROGRESS_STATUSES:
            continue
        if current is not None and ticket.id == current.id:
            continue
        work = learner_work(ticket)
        if not work:
            continue
        files.update(work)
        contributors.append(
            {
                "ticket_id": ticket.id,
                "key": ticket.key,
                "title": ticket.title,
                "status": ticket.status,
                "files": sorted(work.keys()),
                # Honest by construction: this ticket has not passed validation,
                # so its contribution is unverified and the work is unfinished.
                "verified": False,
                "incomplete": True,
            }
        )

    return files, contributors


def _assemble(
    tickets: list[Ticket],
    current: Optional[Ticket],
    live_files: Optional[dict[str, str]],
    title: str,
    include_in_progress: bool = False,
) -> dict[str, Any]:
    files, verified_contributors = _cumulative_files(tickets, current, live_files)

    in_progress_files: dict[str, str] = {}
    in_progress_contributors: list[dict[str, Any]] = []
    if include_in_progress:
        in_progress_files, in_progress_contributors = _in_progress_contributions(
            tickets, current
        )
        # Verified work first, unfinished work on top: the learner needs to see
        # the state of the thing they are actually holding.
        files = {**files, **in_progress_files}

    contributors = verified_contributors + [c["key"] for c in in_progress_contributors]

    synthesized = ENTRY_FILE not in files
    mount_ids: list[str] = []
    if synthesized:
        mount_ids = _mount_ids(current, files)
        renderable = any(
            name.endswith((".js", ".css", ".html")) and (files.get(name) or "").strip()
            for name in files
        )
        if not renderable:
            return _empty(tickets, contributors, verified_contributors, in_progress_contributors)
        files = dict(files)
        files[ENTRY_FILE] = _synthesize_host(title, mount_ids)

    # Half-written scripts are the normal case for unfinished work, and an
    # uncaught throw would leave the frame blank. Guarding only the render copy
    # keeps the file map the client recomposes from byte-exact.
    render_files = _guard_scripts(files, set(in_progress_files))
    preview = _append_unreferenced(
        build_preview(render_files, {"entry_file": ENTRY_FILE}), render_files
    )
    return {
        "html": preview,
        # The exact map the document above was composed from, synthesized host
        # included, so a client can recompose it locally with live editor
        # buffers layered on top instead of asking for a rebuild per keystroke.
        # These are the learner's own files and nothing else — no solution
        # files, no hidden test data, no other learners' work.
        "files": dict(files),
        "meta": _meta(
            tickets,
            contributors,
            verified_contributors,
            in_progress_contributors,
            sorted(files.keys()),
            synthesized,
            mount_ids,
        ),
    }


def _guard_scripts(files: dict[str, str], unverified: set[str]) -> dict[str, str]:
    """Wrap unverified JS so a throw reports to the console instead of the page."""
    if not unverified:
        return files
    guarded = dict(files)
    for name in unverified:
        if not name.lower().endswith(".js"):
            continue
        source = guarded.get(name) or ""
        if not source.strip():
            continue
        guarded[name] = (
            "try {\n"
            f"{source}\n"
            "} catch (error) {\n"
            f"  console.error('Unfinished work in {name} did not run:', error);\n"
            "}"
        )
    return guarded


def _meta(
    tickets: list[Ticket],
    contributors: list[str],
    verified_contributors: list[str],
    in_progress_contributors: list[dict[str, Any]],
    files: list[str],
    synthesized: bool,
    mount_ids: list[str],
) -> dict[str, Any]:
    return {
        "verified_tickets": sum(1 for t in tickets if t.status == "done"),
        "total_tickets": len(tickets),
        "files": files,
        "contributing_tickets": contributors,
        "verified_contributors": verified_contributors,
        "in_progress_contributors": in_progress_contributors,
        "unfinished_tickets": [c for c in in_progress_contributors if c["incomplete"]],
        "includes_unverified": bool(in_progress_contributors),
        "synthesized_host": synthesized,
        "mount_points": mount_ids,
    }


def _append_unreferenced(
    html: Optional[str], files: dict[str, str]
) -> Optional[str]:
    """Add stylesheets and scripts the entry document never linked.

    The bundler only inlines what a tag points at, so an earlier ticket's HTML
    that predates the stylesheet would drop a later ticket's CSS entirely — the
    learner writes styles and the preview stays unstyled. The client-side
    composer already appends in this case; matching it here keeps the two
    renderers from disagreeing.
    """
    if html is None:
        return None
    appended: list[str] = []
    for name, content in files.items():
        if name == ENTRY_FILE or not (content or "").strip() or content in html:
            continue
        if name.lower().endswith(".css"):
            appended.append(f"<style>\n{content}\n</style>")
        elif name == BROWSER_SCRIPT:
            # Only the conventional browser entry point. A project can also hold
            # `server.js` or a schema file, and running those in the iframe would
            # throw rather than render anything.
            appended.append(f"<script>\n{content}\n</script>")
    if not appended:
        return html
    block = "\n".join(appended)
    if "</body>" in html:
        return html.replace("</body>", f"{block}\n</body>")
    return f"{html}\n{block}"


def _empty(
    tickets: list[Ticket],
    contributors: list[str],
    verified_contributors: Optional[list[str]] = None,
    in_progress_contributors: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    return {
        "html": None,
        "files": {},
        "meta": _meta(
            tickets,
            contributors,
            verified_contributors if verified_contributors is not None else contributors,
            in_progress_contributors or [],
            [],
            False,
            [],
        ),
    }
