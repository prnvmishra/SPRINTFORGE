"""Throwaway probe: what does project generation do for a Data Analyst stack?"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import LearningDigitalTwin, Project, User
from app.services.sprint_generator import generate_project_plan


def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    user = User(email="probe@example.com", name="Probe", hashed_password="x")
    db.add(user)
    db.flush()
    twin = LearningDigitalTwin(user_id=user.id)
    db.add(twin)
    db.flush()
    return db, twin


for stack in (["SQL", "Spreadsheet", "Statistics"], ["SQLite", "Excel", "Tableau"]):
    db, twin = session()
    project = Project(
        user_id=twin.user_id,
        title="Sales Funnel Analysis",
        idea="Analyse a sales funnel and report where revenue leaks.",
        tech_stack=stack,
        complexity="intermediate",
        desired_outcome="A dashboard answering where revenue leaks.",
    )
    db.add(project)
    db.flush()
    result = generate_project_plan(db, twin, project)
    print("=" * 70)
    print("stack:", stack)
    print(result)
    for sprint in project.sprints:
        print(f"  [{sprint.milestone}] {sprint.name}")
        for ticket in sprint.tickets:
            print(f"     {ticket.key} {ticket.title!r} skill={ticket.target_skill_id}")
