"""SQL practice questions, graded by executing the query.

Read `docs/sql_authoring.md` before adding one. The short version:

* Declare `schema` (DDL), two or more `datasets` of fixture rows, and a
  `reference` query that is correct. Expected results are *derived* by running
  the reference — never write them by hand.
* The datasets must disagree on the answer. `sql_judge.validate_spec` refuses
  the question otherwise, because a hardcoded `SELECT 'Alice', 42` would pass.
* Mark at least one dataset `hidden: True`. Visible datasets are published to
  the learner (they are the data in the question); hidden ones only grade on
  Submit.
* Set `ordered: True` only when the question genuinely requires a row order,
  and then say so in the requirements.

These three questions exist to prove the machinery end to end — one filter, one
join-plus-aggregate, one ordered top-N. The ~50-question bank is authored on top
of them.
"""

from __future__ import annotations

from typing import Any

from app.data.practice_sql_bank import SQL_BANK
from app.services import sql_judge

# --------------------------------------------------------------------------- #
#  Shared fixture world: a small e-commerce schema reused by all three         #
#  questions, so a learner reads one data model instead of three.              #
# --------------------------------------------------------------------------- #

SHOP_SCHEMA = [
    """
    CREATE TABLE customers (
        id      INTEGER PRIMARY KEY,
        name    TEXT    NOT NULL,
        city    TEXT,
        signup  TEXT    NOT NULL
    );
    CREATE TABLE orders (
        id          INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(id),
        product     TEXT    NOT NULL,
        amount      REAL    NOT NULL,
        status      TEXT    NOT NULL
    );
    """
]


def _shop(customers: list[tuple], orders: list[tuple]) -> dict[str, Any]:
    """Fixture rows from tuples, so a dataset stays readable at a glance."""
    return {
        "customers": [
            {"id": i, "name": n, "city": c, "signup": s} for i, n, c, s in customers
        ],
        "orders": [
            {"id": i, "customer_id": c, "product": p, "amount": a, "status": st}
            for i, c, p, a, st in orders
        ],
    }


# Dataset A: two cities, one refund, one customer who never ordered.
_DATASET_A = _shop(
    customers=[
        (1, "Alice Okafor", "Leeds", "2023-01-14"),
        (2, "Bo Chen", "Leeds", "2023-02-02"),
        (3, "Carla Ruiz", "Bristol", "2023-02-19"),
        (4, "Dev Patel", "Bristol", "2024-03-01"),
    ],
    orders=[
        (1, 1, "Standing desk", 320.00, "paid"),
        (2, 1, "Desk mat", 24.50, "paid"),
        (3, 2, "Monitor arm", 89.99, "paid"),
        (4, 2, "Cable tray", 18.00, "refunded"),
        (5, 3, "Standing desk", 320.00, "paid"),
        (6, 3, "Monitor arm", 89.99, "pending"),
    ],
)

# Dataset B: deliberately different shape — a third city, a customer whose only
# order is refunded, and a different winner per city. A constant answer that
# satisfies A cannot satisfy this.
_DATASET_B = _shop(
    customers=[
        (1, "Erin Vale", "Cardiff", "2022-11-30"),
        (2, "Femi Adeyemi", "Cardiff", "2024-01-08"),
        (3, "Greta Lind", "Oslo", "2023-07-21"),
    ],
    orders=[
        (1, 1, "Desk mat", 24.50, "refunded"),
        (2, 2, "Standing desk", 320.00, "paid"),
        (3, 2, "Desk mat", 24.50, "paid"),
        (4, 2, "Desk mat", 24.50, "paid"),
        (5, 3, "Monitor arm", 89.99, "paid"),
    ],
)

# Dataset C: the degenerate cases authors forget — nobody qualifies, and an
# aggregate therefore has to return no rows rather than a row of NULLs.
_DATASET_C = _shop(
    customers=[
        (1, "Hana Sato", "Kyoto", "2024-05-05"),
        (2, "Ivan Petrov", "Kyoto", "2024-05-06"),
    ],
    orders=[
        (1, 1, "Cable tray", 18.00, "refunded"),
        (2, 2, "Cable tray", 18.00, "pending"),
    ],
)


SCHEMA_NOTE = (
    "Two tables:\n\n"
    "`customers(id, name, city, signup)` — one row per customer; `signup` is an "
    "ISO date string.\n"
    "`orders(id, customer_id, product, amount, status)` — one row per order; "
    "`status` is one of `paid`, `pending`, `refunded`.\n\n"
    "Only `paid` orders count as revenue. Your query is run against several "
    "datasets, including ones you cannot see, so it has to answer the question "
    "rather than reproduce one particular answer."
)


# --------------------------------------------------------------------------- #
#  1. Filtering — sql_basics                                                   #
# --------------------------------------------------------------------------- #

_FILTER_SPEC: dict[str, Any] = {
    "schema": SHOP_SCHEMA,
    "reference": (
        "SELECT name, city FROM customers WHERE signup >= '2024-01-01'"
    ),
    "ordered": False,
    "datasets": [
        {"name": "sample: Leeds and Bristol", "rows": _DATASET_A},
        {"name": "hidden: Cardiff and Oslo", "rows": _DATASET_B, "hidden": True},
        {"name": "hidden: nobody qualifies", "rows": _DATASET_C, "hidden": True},
    ],
}

# Dataset C has two 2024 signups, so it is not an empty-answer case for this
# question; the empty case is covered by the aggregation question below.

_FILTER_QUESTION: dict[str, Any] = {
    "id": "sql-customer-filter",
    "title": "Customers Who Signed Up in 2024",
    "kind": "sql",
    "practice_layer": "query",
    "skill_id": "sql_basics",
    "technology": "SQL",
    "language": "sql",
    "concept": "where",
    "difficulty": 2,
    "estimated_minutes": 15,
    "summary": (
        "Return the name and city of every customer who signed up on or after "
        "1 January 2024."
    ),
    "problem_statement": (
        "The growth team wants to know who joined this year.\n\n"
        "Return **two columns**, `name` and `city`, for every customer whose "
        "`signup` date is on or after `2024-01-01`. Row order does not matter.\n\n"
        + SCHEMA_NOTE
    ),
    "requirements": [
        "Return exactly two columns: the customer's name and city",
        "Include only customers who signed up on or after 2024-01-01",
        "Do not filter on anything else — every 2024 customer counts, ordered or not",
    ],
    "editable_files": ["query.sql"],
    "files": {
        "query.sql": (
            "-- Return name and city for customers who signed up on or after 2024-01-01.\n"
            "-- TODO: write the query.\n"
        )
    },
    "solution_files": {"query.sql": _FILTER_SPEC["reference"]},
    "sql_spec": _FILTER_SPEC,
    "checks": [],
}


# --------------------------------------------------------------------------- #
#  2. Join + aggregate — sql_aggregation                                       #
# --------------------------------------------------------------------------- #

_REVENUE_SPEC: dict[str, Any] = {
    "schema": SHOP_SCHEMA,
    "reference": (
        "SELECT c.city AS city, SUM(o.amount) AS revenue "
        "FROM customers c JOIN orders o ON o.customer_id = c.id "
        "WHERE o.status = 'paid' "
        "GROUP BY c.city"
    ),
    "ordered": False,
    "datasets": [
        {"name": "sample: Leeds and Bristol", "rows": _DATASET_A},
        {"name": "hidden: Cardiff and Oslo", "rows": _DATASET_B, "hidden": True},
        # No paid orders at all: the correct answer is zero rows, not a row of
        # NULLs. This is what catches an aggregate written without a GROUP BY.
        {"name": "hidden: no paid orders", "rows": _DATASET_C, "hidden": True},
    ],
}

_REVENUE_QUESTION: dict[str, Any] = {
    "id": "sql-revenue-by-city",
    "title": "Paid Revenue by City",
    "kind": "sql",
    "practice_layer": "query",
    "skill_id": "sql_aggregation",
    "secondary_skill_id": "sql_joins",
    "technology": "SQL",
    "language": "sql",
    "concept": "group by",
    "difficulty": 4,
    "estimated_minutes": 25,
    "summary": (
        "Join customers to their orders and total the paid revenue per city. "
        "Cities with no paid revenue must not appear."
    ),
    "problem_statement": (
        "Finance wants revenue split by city.\n\n"
        "Return **two columns**, `city` and `revenue`, where `revenue` is the "
        "sum of `amount` over that city's **paid** orders. A city with no paid "
        "orders must not appear in the result at all — and if no order anywhere "
        "is paid, the correct answer is zero rows, not one row of NULLs. Row "
        "order does not matter.\n\n" + SCHEMA_NOTE
    ),
    "requirements": [
        "Join orders to customers on the customer id",
        "Count only orders with status 'paid' — pending and refunded are not revenue",
        "Group by city and sum the order amounts",
        "Return no rows when nothing is paid, rather than a single NULL row",
    ],
    "editable_files": ["query.sql"],
    "files": {
        "query.sql": (
            "-- Return city and total paid revenue per city.\n"
            "-- TODO: write the query.\n"
        )
    },
    "solution_files": {"query.sql": _REVENUE_SPEC["reference"]},
    "sql_spec": _REVENUE_SPEC,
    "checks": [],
}


# --------------------------------------------------------------------------- #
#  3. Ordered top-N — sql_analytics                                            #
# --------------------------------------------------------------------------- #

_TOP_SPEC: dict[str, Any] = {
    "schema": SHOP_SCHEMA,
    "reference": (
        "SELECT o.product AS product, COUNT(*) AS units "
        "FROM orders o WHERE o.status = 'paid' "
        "GROUP BY o.product "
        "ORDER BY units DESC, product ASC "
        "LIMIT 2"
    ),
    # This question states its order, so the judge compares row order too.
    "ordered": True,
    "datasets": [
        {"name": "sample: Leeds and Bristol", "rows": _DATASET_A},
        {"name": "hidden: Cardiff and Oslo", "rows": _DATASET_B, "hidden": True},
        {"name": "hidden: no paid orders", "rows": _DATASET_C, "hidden": True},
    ],
}

_TOP_QUESTION: dict[str, Any] = {
    "id": "sql-top-product-per-city",
    "title": "Two Best-Selling Products",
    "kind": "sql",
    "practice_layer": "query",
    "skill_id": "sql_analytics",
    "secondary_skill_id": "sql_aggregation",
    "technology": "SQL",
    "language": "sql",
    "concept": "ranking",
    "difficulty": 6,
    "estimated_minutes": 30,
    "summary": (
        "Rank products by paid units sold and return the top two, most sold "
        "first, with product name breaking ties."
    ),
    "problem_statement": (
        "Merchandising wants the two best sellers.\n\n"
        "Return **two columns**, `product` and `units`, where `units` is the "
        "number of **paid** orders for that product. Return at most two rows, "
        "ordered by `units` **descending**; where two products tie on units, the "
        "one whose name sorts first alphabetically comes first.\n\n"
        "**Row order is graded for this question.** A result with the right rows "
        "in the wrong order is wrong.\n\n" + SCHEMA_NOTE
    ),
    "requirements": [
        "Count paid orders per product, not the sum of their amounts",
        "Return the product name and the unit count, in that column order",
        "Order by units descending, then by product name ascending to break ties",
        "Return at most two rows",
    ],
    "editable_files": ["query.sql"],
    "files": {
        "query.sql": (
            "-- Return the two best-selling products by paid unit count.\n"
            "-- Order matters: units descending, then product name ascending.\n"
            "-- TODO: write the query.\n"
        )
    },
    "solution_files": {"query.sql": _TOP_SPEC["reference"]},
    "sql_spec": _TOP_SPEC,
    "checks": [],
}


SQL_MODULES: list[dict[str, Any]] = [
    _FILTER_QUESTION,
    _REVENUE_QUESTION,
    _TOP_QUESTION,
]

# The authored bank — ten questions per SQL skill — lives in its own module so
# this file stays readable as the format reference. It is the same dict shape
# and goes through the same import-time validation below.
SQL_MODULES.extend(SQL_BANK)

# Import-time refusal, not a test-only assertion: a question whose datasets all
# share one answer would let a hardcoded constant pass, and it must never reach
# a learner. `validate_spec` also re-derives every expected result from the
# reference, so a fixture edit that breaks the reference fails here immediately.
for _module in SQL_MODULES:
    sql_judge.validate_spec(_module["sql_spec"], f"practice_sql: {_module['id']}")
