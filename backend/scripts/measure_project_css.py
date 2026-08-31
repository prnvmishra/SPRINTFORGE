"""Measure the CSS actually reaching the page in a live project's preview.

Read-only. Prints per-ticket file sizes and the composed CSS character count,
which is the number the cumulative-preview bug is judged on.

    PYTHONPATH=. .venv/bin/python scripts/measure_project_css.py <project_id>
"""

from __future__ import annotations

import re
import sys

from app.core.database import SessionLocal
from app.models import Project
from app.services.project_preview_service import _project_tickets, build_preview_for_project

STYLE_BLOCK = re.compile(r"<style>(.*?)</style>", re.S)


def main(project_id: str) -> None:
    db = SessionLocal()
    try:
        project = db.get(Project, project_id)
        title = project.title if project else "Project"
        print(f"project: {title}")
        for ticket in _project_tickets(db, project_id):
            starter = {k: len(v or "") for k, v in (ticket.starter_files or {}).items()}
            work = {k: len(v or "") for k, v in (ticket.workspace_files or {}).items()}
            print(f"  {ticket.key:8} {ticket.status:12} starter={starter} workspace={work}")

        result = build_preview_for_project(db, project_id, title)
        html = result["html"] or ""
        blocks = STYLE_BLOCK.findall(html)
        print(f"style blocks: {len(blocks)} | total css chars: {sum(len(b) for b in blocks)}")
        print(f"meta.verified_tickets: {result['meta']['verified_tickets']}")
        print(f"contributing: {result['meta']['contributing_tickets']}")
    finally:
        db.close()


if __name__ == "__main__":
    main(sys.argv[1])
