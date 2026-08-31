"""Guarantees for the SQL judge and for every authored SQL question.

The judge exists because grading SQL by matching the query text passes work that
did nothing. These tests assert the properties that make it real grading:

* a correct query passes, including one written in a different but equivalent
  style to the reference;
* a **hardcoded constant** answer is rejected — asserted against every authored
  question by generating the constant from the question's own first dataset,
  rather than hoping an author remembered to think about it;
* a missing filter and a wrong join are rejected with a message that says what
  differed;
* a write, several statements and a runaway query are contained.
"""

from __future__ import annotations

import time

import pytest

from app.data.practice_sql import SQL_MODULES
from app.data.ticket_templates import TICKET_TEMPLATES
from app.services import sql_judge
from app.services.validation_service import run_static_checks

SPEC = {
    "schema": [
        """
        CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, city TEXT);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL, status TEXT);
        """
    ],
    "reference": (
        "SELECT c.name AS name, SUM(o.amount) AS total FROM customers c "
        "JOIN orders o ON o.customer_id = c.id WHERE o.status = 'paid' GROUP BY c.name"
    ),
    "datasets": [
        {
            "name": "two payers",
            "rows": {
                "customers": [
                    {"id": 1, "name": "Alice", "city": "Leeds"},
                    {"id": 2, "name": "Bob", "city": "Hull"},
                ],
                "orders": [
                    {"id": 1, "customer_id": 1, "amount": 40.0, "status": "paid"},
                    {"id": 2, "customer_id": 1, "amount": 2.0, "status": "refunded"},
                    {"id": 3, "customer_id": 2, "amount": 7.0, "status": "paid"},
                ],
            },
        },
        {
            "name": "one payer",
            "hidden": True,
            "rows": {
                "customers": [
                    {"id": 1, "name": "Cara", "city": "Perth"},
                    {"id": 2, "name": "Dan", "city": "Perth"},
                ],
                "orders": [
                    {"id": 1, "customer_id": 2, "amount": 11.5, "status": "paid"},
                    {"id": 2, "customer_id": 1, "amount": 99.0, "status": "refunded"},
                ],
            },
        },
    ],
}

#: Every SQL question shipped to a learner, from both surfaces.
AUTHORED_SPECS = [(m["id"], m["sql_spec"]) for m in SQL_MODULES] + [
    (f"{template['slug']}/{check['id']}", check["spec"])
    for templates in TICKET_TEMPLATES.values()
    for template in templates
    for check in template["checks"]
    if check.get("type") == "sql_query"
]


def test_there_are_authored_sql_questions():
    assert AUTHORED_SPECS, "no SQL question is registered, so nothing below is tested"


# --------------------------------------------------------------------------- #
#  Correctness
# --------------------------------------------------------------------------- #


def test_the_reference_query_passes():
    assert sql_judge.grade(SPEC["reference"], SPEC).passed


def test_an_equivalent_query_written_differently_also_passes():
    """A judge that only accepts the reference's phrasing is a text matcher."""
    equivalent = (
        "SELECT customers.name, SUM(orders.amount) AS revenue "
        "FROM orders, customers "
        "WHERE orders.customer_id = customers.id AND orders.status = 'paid' "
        "GROUP BY customers.name ORDER BY revenue DESC"
    )
    assert sql_judge.grade(equivalent, SPEC).passed


def test_a_cte_phrasing_also_passes():
    cte = (
        "WITH paid AS (SELECT * FROM orders WHERE status = 'paid') "
        "SELECT c.name, SUM(p.amount) FROM customers c "
        "JOIN paid p ON p.customer_id = c.id GROUP BY c.name"
    )
    assert sql_judge.grade(cte, SPEC).passed


# --------------------------------------------------------------------------- #
#  The cheat this design exists to defeat
# --------------------------------------------------------------------------- #


def test_a_hardcoded_constant_is_rejected():
    grade = sql_judge.grade(sql_judge.hardcode_probe(SPEC), SPEC)
    assert not grade.passed
    failed = [o for o in grade.outcomes if not o.passed]
    assert failed, "the constant satisfied every dataset"
    assert "missing" in failed[0].detail or "should not be there" in failed[0].detail


@pytest.mark.parametrize("name,spec", AUTHORED_SPECS, ids=[n for n, _ in AUTHORED_SPECS])
def test_every_authored_question_defeats_a_hardcoded_answer(name, spec):
    """The property is proved per question, not asserted once in a docstring.

    The constant is derived from the question's *own* first dataset, so it is the
    strongest hardcode a learner could write after seeing the sample data.
    """
    probe = sql_judge.hardcode_probe(spec)
    grade = sql_judge.grade(probe, spec)
    assert not grade.passed, (
        f"{name}: a hardcoded constant answer passes this question. Its datasets do "
        f"not disagree enough. Probe: {probe}"
    )


@pytest.mark.parametrize("name,spec", AUTHORED_SPECS, ids=[n for n, _ in AUTHORED_SPECS])
def test_every_authored_question_is_valid(name, spec):
    sql_judge.validate_spec(spec, name)


@pytest.mark.parametrize("name,spec", AUTHORED_SPECS, ids=[n for n, _ in AUTHORED_SPECS])
def test_every_authored_question_has_a_hidden_dataset(name, spec):
    """Grading data a learner can read is grading data a learner can fit to."""
    assert any(d.get("hidden") for d in spec["datasets"]), name


def test_validate_spec_rejects_datasets_that_agree():
    """The anti-hardcode rule is enforced on authors, not left to good intentions."""
    weak = {
        **SPEC,
        "datasets": [
            {**SPEC["datasets"][0], "name": "a"},
            {**SPEC["datasets"][0], "name": "b"},
        ],
    }
    with pytest.raises(sql_judge.SqlSpecError, match="hardcoded constant"):
        sql_judge.validate_spec(weak)


def test_validate_spec_rejects_a_single_dataset():
    with pytest.raises(sql_judge.SqlSpecError, match="at least 2 datasets"):
        sql_judge.validate_spec({**SPEC, "datasets": SPEC["datasets"][:1]})


def test_validate_spec_rejects_a_broken_reference():
    with pytest.raises(sql_judge.SqlSpecError):
        sql_judge.validate_spec({**SPEC, "reference": "SELECT nope FROM missing_table"})


# --------------------------------------------------------------------------- #
#  Honest failure messages
# --------------------------------------------------------------------------- #


def _details(query: str) -> str:
    grade = sql_judge.grade(query, SPEC)
    assert not grade.passed
    return " | ".join([grade.rejection or ""] + [o.detail for o in grade.outcomes])


def test_a_missing_where_clause_says_what_extra_appeared():
    detail = _details(
        "SELECT c.name, SUM(o.amount) FROM customers c "
        "JOIN orders o ON o.customer_id = c.id GROUP BY c.name"
    )
    assert "row" in detail
    assert "WHERE" in detail or "Unexpected" in detail or "missing" in detail


def test_a_wrong_join_says_which_rows_are_missing():
    detail = _details(
        "SELECT c.name, SUM(o.amount) FROM customers c "
        "LEFT JOIN orders o ON o.id = c.id WHERE o.status = 'paid' GROUP BY c.name"
    )
    assert "missing" in detail or "should not be there" in detail


def test_the_wrong_column_count_is_named_as_such():
    detail = _details("SELECT name FROM customers")
    assert "wrong number of columns" in detail


def test_ordering_is_compared_only_when_the_question_requires_it():
    ordered_spec = {
        **SPEC,
        "ordered": True,
        "reference": (
            "SELECT c.name AS name, SUM(o.amount) AS total FROM customers c "
            "JOIN orders o ON o.customer_id = c.id WHERE o.status = 'paid' "
            "GROUP BY c.name ORDER BY total DESC, name ASC"
        ),
    }
    wrong_order = (
        "SELECT c.name, SUM(o.amount) AS total FROM customers c "
        "JOIN orders o ON o.customer_id = c.id WHERE o.status = 'paid' "
        "GROUP BY c.name ORDER BY total ASC, name DESC"
    )
    ordered_grade = sql_judge.grade(wrong_order, ordered_spec)
    assert not ordered_grade.passed
    assert any("wrong order" in o.detail for o in ordered_grade.outcomes)

    # The same query is correct for the order-insensitive question.
    assert sql_judge.grade(wrong_order, SPEC).passed


def test_duplicate_rows_are_not_collapsed():
    """Order-insensitive comparison is a multiset, not a set."""
    spec = {
        "schema": ["CREATE TABLE t (v INTEGER);"],
        "reference": "SELECT v FROM t",
        "datasets": [
            {"name": "two ones", "rows": {"t": [{"v": 1}, {"v": 1}]}},
            {"name": "one one", "hidden": True, "rows": {"t": [{"v": 1}]}},
        ],
    }
    sql_judge.validate_spec(spec)
    assert not sql_judge.grade("SELECT DISTINCT v FROM t", spec).passed


# --------------------------------------------------------------------------- #
#  Containment
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "query",
    [
        "DROP TABLE orders",
        "DELETE FROM orders",
        "UPDATE orders SET amount = 0",
        "INSERT INTO orders (id) VALUES (99)",
        "PRAGMA table_list",
    ],
)
def test_writes_are_refused(query):
    grade = sql_judge.grade(query, SPEC)
    assert not grade.passed
    assert grade.rejection


def test_dropping_the_fixture_table_cannot_make_a_query_pass():
    """The whole point: a learner must not be able to empty the data and pass."""
    grade = sql_judge.grade("DROP TABLE orders; SELECT 'Alice', 40.0", SPEC)
    assert not grade.passed
    assert "single statement" in (grade.rejection or "")


def test_a_write_hidden_behind_a_read_is_still_refused():
    """Belt and braces: the authorizer, not just the keyword check."""
    grade = sql_judge.grade("SELECT load_extension('/tmp/x.so')", SPEC)
    assert not grade.passed
    assert any("refused" in o.detail for o in grade.outcomes)


def test_an_empty_submission_never_passes():
    for query in ("", "   ", "-- I will do this later"):
        grade = sql_judge.grade(query, SPEC)
        assert not grade.passed
        assert grade.rejection
        assert grade.outcomes == []


def test_a_runaway_query_ends_as_a_failure_not_a_hang():
    started = time.monotonic()
    grade = sql_judge.grade(
        "SELECT COUNT(*) AS a, 1 AS b FROM "
        "(WITH RECURSIVE forever(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM forever) "
        "SELECT n FROM forever)",
        SPEC,
    )
    elapsed = time.monotonic() - started
    assert not grade.passed
    assert elapsed < sql_judge.QUERY_TIMEOUT_SECONDS * len(SPEC["datasets"]) + 5
    assert any("stopped" in o.detail for o in grade.outcomes)


def test_an_unbounded_result_set_is_capped():
    grade = sql_judge.grade(
        "WITH RECURSIVE forever(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM forever) "
        "SELECT n, n FROM forever",
        SPEC,
    )
    assert not grade.passed
    assert any(str(sql_judge.MAX_RESULT_ROWS) in o.detail for o in grade.outcomes)


# --------------------------------------------------------------------------- #
#  Hidden datasets stay hidden on Run
# --------------------------------------------------------------------------- #


def test_run_grades_only_the_visible_datasets():
    visible = sql_judge.grade(SPEC["reference"], SPEC, include_hidden=False)
    assert [o.dataset for o in visible.outcomes] == ["two payers"]

    graded = sql_judge.grade(SPEC["reference"], SPEC, include_hidden=True)
    assert [o.dataset for o in graded.outcomes] == ["two payers", "one payer"]


def test_public_schema_withholds_hidden_datasets():
    published = sql_judge.public_schema(SPEC)
    assert [d["name"] for d in published["datasets"]] == ["two payers"]
    assert published["hidden_dataset_count"] == 1
    assert "Cara" not in str(published)


# --------------------------------------------------------------------------- #
#  The `sql_query` check type used by project tickets
# --------------------------------------------------------------------------- #


def _sql_check(spec: dict) -> list[dict]:
    return [
        {
            "id": "result",
            "type": "sql_query",
            "file": "query.sql",
            "spec": spec,
            "label": "query returns the right rows",
            "concept": "group by",
            "requirement_index": 0,
        }
    ]


def test_ticket_sql_check_passes_a_correct_query():
    outcomes = run_static_checks({"query.sql": SPEC["reference"]}, _sql_check(SPEC))
    assert [o.passed for o in outcomes] == [True]
    assert "correct on all" in outcomes[0].detail


def test_ticket_sql_check_rejects_a_hardcoded_query_and_explains_why():
    outcomes = run_static_checks(
        {"query.sql": sql_judge.hardcode_probe(SPEC)}, _sql_check(SPEC)
    )
    assert [o.passed for o in outcomes] == [False]
    assert outcomes[0].detail
    assert "row" in outcomes[0].detail


def test_ticket_sql_check_fails_closed_on_a_broken_spec():
    outcomes = run_static_checks({"query.sql": "SELECT 1"}, [
        {"id": "result", "type": "sql_query", "file": "query.sql", "spec": {}, "label": "x"}
    ])
    assert [o.passed for o in outcomes] == [False]


def test_ticket_sql_check_never_passes_an_empty_file():
    outcomes = run_static_checks({"query.sql": ""}, _sql_check(SPEC))
    assert [o.passed for o in outcomes] == [False]
