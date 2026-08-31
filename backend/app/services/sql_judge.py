"""SQLite-backed judge for SQL questions.

Why this exists
---------------
SQL is the central skill of the Data Analyst path and there was no way to
execute it: `code_execution_service` speaks python/javascript/java/c/cpp only,
and its contract is stdin -> stdout, which a query does not have. The
alternative — matching the query *text* against a pattern — is the permissive
grading this product treats as its worst defect: it passes `SELECT * FROM x`
for an aggregation question and fails a correct query written with a different
but equivalent join.

So a query is graded by running it. `sqlite3` is in the standard library, needs
no service, no container and no network, and its dialect is close enough to
ANSI SQL for analyst-level work (joins, aggregation, `GROUP BY`/`HAVING`,
subqueries, CTEs and window functions are all supported).

The contract
------------
An author declares a `schema`, two or more `datasets` of fixture rows, and a
`reference` query that is known to be correct. **Expected results are never
written by hand** — the judge runs the reference against each dataset and that
is the expected result set. A fixture edit therefore cannot silently
invalidate a hand-typed expectation.

Defeating the hardcoded answer
------------------------------
The cheat this design is built against is `SELECT 'Alice', 42` — a constant
that reproduces the answer without touching the data. The defence is
structural, not a heuristic: every question is graded against **several
datasets whose correct answers differ**, and `validate_spec` refuses a
question where they do not. A constant matches at most one dataset, so it is
always caught by another. `hardcode_probe` builds exactly that constant query
from the first dataset's answer, which is what the test suite uses to prove the
defence on every authored question rather than asserting it in prose.

Containment
-----------
The learner's query runs against a fresh in-memory database per dataset, under
an authorizer that permits reads and denies everything else, so `DROP TABLE
orders` is refused at prepare time and cannot make the remaining datasets pass
vacuously. Multiple statements are rejected before execution, a progress
handler aborts a runaway query on a wall-clock deadline, and the result set is
capped so a cross join cannot exhaust memory.
"""

from __future__ import annotations

import re
import sqlite3
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Optional

#: Wall clock allowed for one execution of the learner's query, per dataset.
#: Generous for analyst-scale fixtures (tens of rows) and short enough that a
#: cartesian product is reported as a graded failure rather than a hung request.
QUERY_TIMEOUT_SECONDS = 2.0

#: The progress handler runs every N virtual-machine instructions; it is the
#: only way to interrupt SQLite mid-query from Python.
_PROGRESS_INSTRUCTIONS = 1000

#: A correct analyst answer is small. Anything past this is a runaway join, and
#: the cap means we never materialise it.
MAX_RESULT_ROWS = 2000

#: Floats are rounded before comparison: `AVG` over the same rows can differ in
#: the last bits between two algebraically equal queries.
FLOAT_PRECISION = 6

#: Rows quoted back to the learner in a failure message. Enough to see the
#: shape of the mistake, not enough to reconstruct the answer key from a
#: hidden dataset.
_SAMPLE_ROWS = 3

#: Leading keywords that mean "this is not a read". They are named explicitly
#: rather than allow-listing `select`/`with`, so that a typo (`SELCT name ...`)
#: falls through to SQLite and the learner gets a real syntax error instead of
#: being told to write a SELECT when they already tried to. Writes that slip
#: past this list are still refused by the authorizer at prepare time.
_WRITE_KEYWORDS = frozenset(
    {
        "insert",
        "update",
        "delete",
        "drop",
        "create",
        "alter",
        "replace",
        "truncate",
        "attach",
        "detach",
        "pragma",
        "vacuum",
        "reindex",
        "begin",
        "commit",
        "rollback",
        "savepoint",
        "release",
        "analyze",
    }
)

# Authorizer action codes that a read-only analytical query legitimately needs.
# Everything else — INSERT/UPDATE/DELETE/DROP/ALTER/CREATE, ATTACH, PRAGMA,
# transactions, extension loading — is denied at statement-prepare time.
_ALLOWED_ACTIONS = frozenset(
    {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
        sqlite3.SQLITE_RECURSIVE,
    }
)

_ACTION_NAMES = {
    sqlite3.SQLITE_INSERT: "INSERT",
    sqlite3.SQLITE_UPDATE: "UPDATE",
    sqlite3.SQLITE_DELETE: "DELETE",
    sqlite3.SQLITE_DROP_TABLE: "DROP TABLE",
    sqlite3.SQLITE_DROP_VIEW: "DROP VIEW",
    sqlite3.SQLITE_DROP_INDEX: "DROP INDEX",
    sqlite3.SQLITE_CREATE_TABLE: "CREATE TABLE",
    sqlite3.SQLITE_CREATE_VIEW: "CREATE VIEW",
    sqlite3.SQLITE_CREATE_INDEX: "CREATE INDEX",
    sqlite3.SQLITE_ALTER_TABLE: "ALTER TABLE",
    sqlite3.SQLITE_ATTACH: "ATTACH",
    sqlite3.SQLITE_DETACH: "DETACH",
    sqlite3.SQLITE_PRAGMA: "PRAGMA",
    sqlite3.SQLITE_TRANSACTION: "BEGIN/COMMIT",
}


class SqlSpecError(ValueError):
    """A question spec is malformed or cannot enforce the anti-hardcode rule."""


@dataclass
class ResultSet:
    columns: list[str]
    rows: list[tuple[Any, ...]]
    truncated: bool = False


@dataclass
class DatasetOutcome:
    """How the learner's query fared against one fixture dataset."""

    dataset: str
    passed: bool
    detail: str
    hidden: bool = False


@dataclass
class SqlGrade:
    passed: bool
    outcomes: list[DatasetOutcome] = field(default_factory=list)
    #: Set when the query was rejected before any dataset ran (empty, multiple
    #: statements, a write, a syntax error). The datasets are then not graded,
    #: because there is nothing to grade.
    rejection: Optional[str] = None

    def to_check_dicts(self, concept: str = "sql") -> list[dict[str, Any]]:
        """Shaped like `CheckOutcome.to_dict()` so existing UI renders it."""
        if self.rejection is not None:
            return [
                {
                    "id": "sql_rejected",
                    "label": "Your query could not be graded",
                    "passed": False,
                    "concept": concept,
                    "hint": None,
                    "detail": self.rejection,
                    "hidden": False,
                    "requirement_index": None,
                    "requirement_indexes": None,
                    "precondition": True,
                    "requirement_mapped": True,
                }
            ]
        return [
            {
                "id": f"dataset_{index + 1}",
                "label": f"Dataset: {outcome.dataset}",
                "passed": outcome.passed,
                "concept": concept,
                "hint": None,
                "detail": outcome.detail,
                "hidden": outcome.hidden,
                "requirement_index": None,
                "requirement_indexes": None,
                "precondition": False,
                "requirement_mapped": False,
            }
            for index, outcome in enumerate(self.outcomes)
        ]


# --------------------------------------------------------------------------- #
#  Spec handling
# --------------------------------------------------------------------------- #


def _datasets(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return list(spec.get("datasets") or [])


def _dataset_name(dataset: dict[str, Any], index: int) -> str:
    return str(dataset.get("name") or f"dataset {index + 1}")


def _seed(spec: dict[str, Any], dataset: dict[str, Any]) -> sqlite3.Connection:
    """A fresh in-memory database holding one dataset, ready to be queried."""
    conn = sqlite3.connect(":memory:")
    for statement in spec.get("schema") or []:
        conn.executescript(statement)
    for table, rows in (dataset.get("rows") or {}).items():
        for row in rows:
            columns = list(row)
            placeholders = ", ".join("?" for _ in columns)
            quoted = ", ".join(f'"{c}"' for c in columns)
            conn.execute(
                f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})',
                [row[c] for c in columns],
            )
    conn.commit()
    return conn


def _strip_sql_comments(sql: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", sql or "", flags=re.DOTALL)
    return re.sub(r"--[^\n]*", " ", text)


def _has_trailing_statement(text: str) -> bool:
    """True when `text` holds a complete statement followed by more SQL.

    A plain `";" in text` test is wrong: `SELECT ';' AS sep` is one statement.
    So the string is scanned for the first semicolon at which the prefix is a
    *complete* statement (SQLite's own parser decides, so semicolons inside
    literals and comments do not count), and anything non-blank after it means a
    second statement was submitted.
    """
    for index, char in enumerate(text, start=1):
        if char != ";":
            continue
        if not sqlite3.complete_statement(text[:index]):
            continue
        return bool(_strip_sql_comments(text[index:]).strip())
    return False


def _statement_rejection(sql: str, read_only: bool) -> Optional[str]:
    """Reject before execution what execution should never be asked to contain."""
    stripped = (sql or "").strip()
    if not _strip_sql_comments(stripped).strip():
        return "you submitted an empty query."

    # `conn.execute` only ever runs the first statement, so a submission of
    # "DROP TABLE orders; SELECT ..." would otherwise be graded on whichever
    # half happened to come first. Refuse it outright.
    if _has_trailing_statement(stripped):
        return (
            "submit a single statement. Your query contains more than one statement "
            "(separated by ';'), and only the first one would ever run."
        )

    body = _strip_sql_comments(stripped).strip().rstrip(";").strip()
    if not body:
        return "you submitted an empty query."

    if read_only:
        first = re.match(r"[\s(]*([A-Za-z_]+)", body)
        keyword = (first.group(1) if first else "").lower()
        if keyword in _WRITE_KEYWORDS:
            return (
                f"this question asks for a read, but your statement starts with "
                f"'{keyword.upper()}'. Answer it with a SELECT (a WITH ... SELECT "
                f"is fine); the fixture data is not yours to change."
            )
    return None


def _authorizer(action: int, *_args: Any) -> int:
    if action in _ALLOWED_ACTIONS:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _execute(conn: sqlite3.Connection, sql: str) -> ResultSet:
    """Run the learner's query under read-only, time-bounded containment."""
    deadline = time.monotonic() + QUERY_TIMEOUT_SECONDS
    conn.set_authorizer(_authorizer)
    conn.set_progress_handler(
        lambda: 1 if time.monotonic() > deadline else 0, _PROGRESS_INSTRUCTIONS
    )
    try:
        cursor = conn.execute(sql)
        columns = [d[0] for d in (cursor.description or [])]
        rows = cursor.fetchmany(MAX_RESULT_ROWS + 1)
        truncated = len(rows) > MAX_RESULT_ROWS
        return ResultSet(columns=columns, rows=[tuple(r) for r in rows[:MAX_RESULT_ROWS]], truncated=truncated)
    finally:
        conn.set_progress_handler(None, 0)
        conn.set_authorizer(None)


def _error_message(exc: Exception) -> str:
    text = str(exc)
    if isinstance(exc, sqlite3.OperationalError) and "not authorized" in text:
        return (
            "your statement was refused: this question grades a read, so the "
            "connection permits table reads and nothing else — the fixture data "
            "cannot be modified, dropped or reached around."
        )
    if isinstance(exc, sqlite3.Warning):
        return f"only one statement can be executed: {text}"
    if isinstance(exc, sqlite3.OperationalError) and "interrupted" in text.lower():
        return (
            f"your query was still running after {QUERY_TIMEOUT_SECONDS:g}s and was "
            "stopped. Check for a join with no join condition."
        )
    return f"SQLite rejected your query: {text}"


# --------------------------------------------------------------------------- #
#  Result comparison
# --------------------------------------------------------------------------- #


def _normalise_value(value: Any) -> Any:
    """Make two algebraically equal values compare equal.

    `COUNT(*)` yields an int and `SUM(1)` a float in some plans, `1` and `1.0`
    are the same answer, and a float average differs in the last bits between
    equivalent queries. Strings are *not* normalised: 'Alice' and 'alice' are
    genuinely different answers.
    """
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, int):
        return float(value)
    if isinstance(value, float):
        return round(value, FLOAT_PRECISION)
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value


def _normalise_row(row: tuple[Any, ...]) -> tuple[Any, ...]:
    return tuple(_normalise_value(v) for v in row)


def _sort_key(row: tuple[Any, ...]) -> tuple[str, ...]:
    """A total order over mixed-type rows, so `None` and 3 can be sorted."""
    return tuple(f"{type(v).__name__}:{v!r}" for v in row)


def _format_row(row: tuple[Any, ...]) -> str:
    def cell(value: Any) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, float) and value == int(value):
            return str(int(value))
        return repr(value) if isinstance(value, str) else str(value)

    return "(" + ", ".join(cell(v) for v in row) + ")"


def _format_rows(rows: list[tuple[Any, ...]]) -> str:
    shown = ", ".join(_format_row(r) for r in rows[:_SAMPLE_ROWS])
    if len(rows) > _SAMPLE_ROWS:
        shown += f", ... (+{len(rows) - _SAMPLE_ROWS} more)"
    return shown


def compare_results(
    expected: ResultSet,
    actual: ResultSet,
    ordered: bool = False,
    require_columns: bool = False,
) -> tuple[bool, str]:
    """Compare result sets and explain the first real difference found.

    Ordering is the trap that makes naive SQL graders wrong in both directions.
    A query without `ORDER BY` returns rows in an order SQLite is free to
    change, so comparing sequences would fail a correct answer; comparing sets
    would pass an unordered answer to a "top 3 by revenue" question. So the
    author declares it: `ordered=False` (the default) compares as multisets —
    duplicates still matter — and `ordered=True` compares sequences and says so
    explicitly when only the order is wrong.

    Column *names* are not compared by default: `SELECT name` and
    `SELECT name AS customer` are the same answer. `require_columns=True` is for
    questions that explicitly demand an alias.
    """
    if actual.truncated:
        return False, (
            f"your query returned more than {MAX_RESULT_ROWS} rows, which no correct "
            "answer to this question does — most likely a join with no join condition."
        )

    if len(actual.columns) != len(expected.columns):
        return False, (
            f"wrong number of columns: expected {len(expected.columns)} "
            f"({', '.join(expected.columns)}), got {len(actual.columns)}"
            + (f" ({', '.join(actual.columns)})" if actual.columns else "")
        )

    if require_columns:
        want = [c.lower() for c in expected.columns]
        got = [c.lower() for c in actual.columns]
        if want != got:
            return False, (
                f"wrong column names: expected {', '.join(expected.columns)}, "
                f"got {', '.join(actual.columns)} — this question requires those names, "
                "so alias your columns."
            )

    expected_rows = [_normalise_row(r) for r in expected.rows]
    actual_rows = [_normalise_row(r) for r in actual.rows]

    expected_counts = Counter(expected_rows)
    actual_counts = Counter(actual_rows)

    missing = sorted((expected_counts - actual_counts).elements(), key=_sort_key)
    extra = sorted((actual_counts - expected_counts).elements(), key=_sort_key)

    if missing and extra:
        return False, (
            f"{len(missing)} row(s) missing and {len(extra)} unexpected row(s). "
            f"Missing: {_format_rows(missing)}. Unexpected: {_format_rows(extra)}."
        )
    if missing:
        return False, (
            f"{len(missing)} expected row(s) are missing from your result: "
            f"{_format_rows(missing)}."
            + (
                " Your query returned no rows at all."
                if not actual_rows
                else " Your filter is excluding rows it should keep."
            )
        )
    if extra:
        return False, (
            f"your result has {len(extra)} row(s) that should not be there: "
            f"{_format_rows(extra)}."
            + (
                " A missing or too-wide WHERE clause is the usual cause."
                if len(extra) >= len(expected_rows)
                else ""
            )
        )

    if ordered and actual_rows != expected_rows:
        return False, (
            "the right rows, in the wrong order. This question requires a specific "
            "order, so add (or fix) the ORDER BY clause."
        )

    return True, f"{len(actual_rows)} row(s), {len(actual.columns)} column(s) — correct"


# --------------------------------------------------------------------------- #
#  Grading
# --------------------------------------------------------------------------- #


def expected_for(spec: dict[str, Any], dataset: dict[str, Any]) -> ResultSet:
    """The reference query's result — the single source of expected output."""
    conn = _seed(spec, dataset)
    try:
        cursor = conn.execute(spec["reference"])
        columns = [d[0] for d in (cursor.description or [])]
        rows = [tuple(r) for r in cursor.fetchall()]
        return ResultSet(columns=columns, rows=rows)
    finally:
        conn.close()


def grade(user_sql: str, spec: dict[str, Any], include_hidden: bool = True) -> SqlGrade:
    """Grade a query against every dataset the question declares."""
    read_only = bool(spec.get("read_only", True))
    rejection = _statement_rejection(user_sql, read_only)
    if rejection:
        return SqlGrade(passed=False, rejection=rejection)

    ordered = bool(spec.get("ordered", False))
    require_columns = bool(spec.get("require_columns", False))

    outcomes: list[DatasetOutcome] = []
    for index, dataset in enumerate(_datasets(spec)):
        hidden = bool(dataset.get("hidden"))
        if hidden and not include_hidden:
            continue
        name = _dataset_name(dataset, index)
        expected = expected_for(spec, dataset)
        conn = _seed(spec, dataset)
        try:
            actual = _execute(conn, user_sql)
        except (sqlite3.Error, sqlite3.Warning) as exc:
            outcomes.append(
                DatasetOutcome(dataset=name, passed=False, detail=_error_message(exc), hidden=hidden)
            )
            continue
        finally:
            conn.close()
        passed, detail = compare_results(expected, actual, ordered, require_columns)
        outcomes.append(DatasetOutcome(dataset=name, passed=passed, detail=detail, hidden=hidden))

    if not outcomes:
        return SqlGrade(passed=False, rejection="this question declares no fixture datasets.")
    return SqlGrade(passed=all(o.passed for o in outcomes), outcomes=outcomes)


# --------------------------------------------------------------------------- #
#  Author-time guarantees
# --------------------------------------------------------------------------- #


def hardcode_probe(spec: dict[str, Any]) -> str:
    """The cheat, written out: a constant query returning dataset 1's answer.

    `SELECT 'Alice' AS name, 42 AS orders UNION ALL SELECT 'Bob', 7`. It is a
    legal read that touches no table, so containment does not stop it — only
    the second dataset does. Every SQL question is tested against this.
    """
    datasets = _datasets(spec)
    if not datasets:
        raise SqlSpecError("cannot build a hardcode probe without a dataset")
    expected = expected_for(spec, datasets[0])

    def literal(value: Any) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return str(int(value))
        if isinstance(value, (int, float)):
            return repr(value)
        return "'" + str(value).replace("'", "''") + "'"

    # Column names are quoted: a reference query may well return `COUNT(*)`.
    def alias(name: str) -> str:
        return '"' + str(name).replace('"', '""') + '"'

    if not expected.rows:
        # An empty answer is reproduced by a constant SELECT that returns nothing.
        selects = ", ".join(f"NULL AS {alias(c)}" for c in expected.columns)
        return f"SELECT {selects} WHERE 1 = 0"

    parts = []
    for position, row in enumerate(expected.rows):
        cells = [
            f"{literal(value)} AS {alias(expected.columns[i])}" if position == 0 else literal(value)
            for i, value in enumerate(row)
        ]
        parts.append("SELECT " + ", ".join(cells))
    return " UNION ALL ".join(parts)


def validate_spec(spec: dict[str, Any], where: str = "sql spec") -> None:
    """Fail loudly at import/test time if a question cannot grade honestly.

    The load-bearing rule is the last one: without two datasets whose correct
    answers differ, a hardcoded constant passes the question and the judge is
    theatre.
    """
    for key in ("schema", "datasets", "reference"):
        if not spec.get(key):
            raise SqlSpecError(f"{where}: missing '{key}'")

    datasets = _datasets(spec)
    if len(datasets) < 2:
        raise SqlSpecError(
            f"{where}: needs at least 2 datasets, so a hardcoded constant answer "
            f"cannot satisfy them all (got {len(datasets)})"
        )

    names = [_dataset_name(d, i) for i, d in enumerate(datasets)]
    if len(set(names)) != len(names):
        raise SqlSpecError(f"{where}: duplicate dataset names {names}")

    results = []
    for index, dataset in enumerate(datasets):
        try:
            results.append(expected_for(spec, dataset))
        except sqlite3.Error as exc:
            raise SqlSpecError(
                f"{where}: the reference query fails on '{names[index]}': {exc}"
            ) from exc

    first = results[0]
    if not first.columns:
        raise SqlSpecError(f"{where}: the reference query returns no columns")

    signatures = [
        (len(r.columns), Counter(_normalise_row(row) for row in r.rows)) for r in results
    ]
    if all(sig == signatures[0] for sig in signatures[1:]):
        raise SqlSpecError(
            f"{where}: every dataset produces the same expected result, so a "
            f"hardcoded constant answer would pass. Vary the fixture rows so at "
            f"least one dataset has a different answer."
        )

    grade_result = grade(spec["reference"], spec)
    if not grade_result.passed:
        failures = "; ".join(o.detail for o in grade_result.outcomes if not o.passed)
        raise SqlSpecError(f"{where}: the reference query does not pass its own datasets: {failures}")


def public_schema(spec: dict[str, Any]) -> dict[str, Any]:
    """What a learner may see: the DDL and the visible fixture rows.

    Hidden datasets are withheld the same way hidden judge cases are, so a
    query cannot be tuned against the data that grades it.
    """
    return {
        "schema": list(spec.get("schema") or []),
        "ordered": bool(spec.get("ordered", False)),
        "require_columns": bool(spec.get("require_columns", False)),
        "datasets": [
            {"name": _dataset_name(d, i), "rows": d.get("rows") or {}}
            for i, d in enumerate(_datasets(spec))
            if not d.get("hidden")
        ],
        "hidden_dataset_count": sum(1 for d in _datasets(spec) if d.get("hidden")),
    }
