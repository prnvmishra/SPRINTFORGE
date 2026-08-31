"""Additive column migrations for databases created before a model gained a field.

`create_all()` only creates missing tables, so a column added to an existing
table would otherwise be missing forever on any database that already exists.
Each entry here is applied only when the column is absent, which keeps startup
safe to repeat and identical on SQLite and Postgres.
"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger("sprintforge")

# (table, column, SQL type accepted by both SQLite and Postgres)
ADDITIVE_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("users", "bio", "VARCHAR(280)"),
    # Confidence is overwritten in place by the scoring engine, so the value a
    # submission started from used to be destroyed. These record the pair at the
    # write site. Nullable on purpose: rows written before this existed have no
    # honest value and must stay NULL rather than be backfilled with a guess.
    ("practice_attempts", "confidence_before", "FLOAT"),
    ("practice_attempts", "confidence_after", "FLOAT"),
    ("ticket_attempts", "confidence_before", "FLOAT"),
    ("ticket_attempts", "confidence_after", "FLOAT"),
    # Placement. `placement_status` needs a default because existing rows are
    # real learners who have not been placed: "pending" is the honest value and
    # routes them through the same check a new signup gets.
    ("learning_digital_twins", "path_id", "VARCHAR(60)"),
    ("learning_digital_twins", "placement_status", "VARCHAR(20) DEFAULT 'pending'"),
    ("learning_digital_twins", "placement_skills", "JSON"),
    ("learning_digital_twins", "placement_sessions", "JSON"),
    ("learning_digital_twins", "placement_result", "JSON"),
)


def apply_additive_migrations(engine: Engine) -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for table, column, column_type in ADDITIVE_COLUMNS:
        if table not in existing_tables:
            continue
        columns = {col["name"] for col in inspector.get_columns(table)}
        if column in columns:
            continue
        with engine.begin() as connection:
            connection.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {column_type}'))
        logger.info("Migration: added %s.%s", table, column)
