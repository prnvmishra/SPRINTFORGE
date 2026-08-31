"""Grade MTB-3 through the real pipeline, before and after render assembly.

Read-only by construction: the live database is copied to a temporary file first,
so nothing here can change a ticket status, an attempt or any XP.

The comparison is the point. `before` is what the evaluator did until now — the
ticket's own workspace handed to `run_static_checks` and nothing else. `after`
adds the read-only page context the ticket is provided but may not edit, exactly
as `ticket_service` now does.

    cd backend && PYTHONPATH=. .venv/bin/python scripts/run_mtb3_render_assembly.py
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.data.ticket_templates import HTML_NAVIGATION_SOLUTION, TICKET_TEMPLATES
from app.models import Ticket
from app.services.project_preview_service import provided_files
from app.services.sprint_generator import _fill
from app.services.validation_service import render_assembly_debug, run_static_checks

CONTEXT = {
    "domain": "Movie Ticket Booking System",
    "entity": "movie",
    "entity_plural": "movies",
}
TICKET_KEY = "MTB-3"
TEMPLATE_SLUG = "design-tokens"


def fill(text: str) -> str:
    for key, value in CONTEXT.items():
        text = text.replace("{" + key + "}", value)
    return text


def template() -> dict:
    for templates in TICKET_TEMPLATES.values():
        for candidate in templates:
            if candidate.get("slug") == TEMPLATE_SLUG:
                return candidate
    raise SystemExit(f"no template {TEMPLATE_SLUG!r}")


def report(title: str, outcomes: list[dict]) -> None:
    passed = sum(1 for o in outcomes if o["passed"])
    print(f"\n=== {title}: {passed}/{len(outcomes)} passed ===")
    for outcome in outcomes:
        if outcome["passed"]:
            continue
        print(f"  FAIL [{outcome['id']}] {outcome['label']}\n        {outcome['detail']}")


def main() -> None:
    source = Path(__file__).resolve().parents[1] / "sprintforge.db"
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "snapshot.db"
        shutil.copy(source, copy)
        db = sessionmaker(bind=create_engine(f"sqlite:///{copy}"))()

        ticket = db.execute(select(Ticket).where(Ticket.key == TICKET_KEY)).scalars().first()
        if ticket is None:
            raise SystemExit(f"{TICKET_KEY} is not in the database")

        spec = template()
        checks = _fill(spec["checks"], CONTEXT)
        kinds = Counter(c["type"] for c in checks)
        print(f"{TICKET_KEY} · {ticket.title} · {len(checks)} checks")
        print("check types:", dict(sorted(kinds.items())))
        print("ticket workspace files:", sorted((ticket.workspace_files or {}).keys()))

        context_files = provided_files(db, ticket)
        print("read-only files provided to the renderer:", sorted(context_files))

        submission = {"styles.css": fill(spec["solution_files"]["styles.css"])}

        print("\n--- render_debug, default configuration ---")
        print(render_assembly_debug(submission, checks, render_files=context_files))
        print("--- render_debug, RENDER_ASSEMBLY_DEBUG=true in development ---")
        settings.RENDER_ASSEMBLY_DEBUG = True
        print(
            json.dumps(
                render_assembly_debug(submission, checks, render_files=context_files), indent=2
            )
        )
        settings.RENDER_ASSEMBLY_DEBUG = False

        report("BEFORE (submission only)", [o.to_dict() for o in run_static_checks(submission, checks)])
        report(
            "AFTER (submission + provided page as it stands today)",
            [
                o.to_dict()
                for o in run_static_checks(submission, checks, render_files=context_files)
            ],
        )
        # The document MTB-1/MTB-2 produce once they are finished. Included so the
        # rendered checks can be seen judging a complete DOM rather than the
        # skeleton the learner has not filled in yet.
        report(
            "AFTER (submission + the finished project document)",
            [
                o.to_dict()
                for o in run_static_checks(
                    submission,
                    checks,
                    render_files={"index.html": fill(HTML_NAVIGATION_SOLUTION)},
                )
            ],
        )


if __name__ == "__main__":
    main()
