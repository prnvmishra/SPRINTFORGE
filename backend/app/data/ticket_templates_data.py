"""Project-ticket templates for the data-analysis skills.

Why this file exists
--------------------
`generate_project_plan` builds a board from `TICKET_TEMPLATES[skill_id]`. A skill
with no entry contributes no tickets, and — before the fix in
`sprint_generator` — its sprint was still created, so the board showed an empty
sprint. A Data Analyst project therefore produced either nothing or a Node/React
board (see the note on the `"sql"` stack alias in `knowledge_graph.py`).

How these are graded
--------------------
The seven SQL-shaped tickets are graded by the `sql_query` check, which
*executes* the learner's query against fixture datasets and compares the result
set with a reference query's — the same judge the SQL practice questions use, so
a ticket cannot be closed by a query that merely mentions `GROUP BY`, and a
correct query written in a different style is not failed. Every spec is
validated at import time: two or more datasets whose correct answers differ,
which is what stops a hardcoded constant.

The three remaining tickets (visualisation, dashboards, spreadsheet modelling)
deliver a written artefact — a chart spec, a dashboard spec, a formula sheet —
and there is nothing to execute, so their checks are structural. That is a real
limitation and is stated here rather than dressed up: they verify that the
learner made the required decisions explicitly, not that the decisions are good.
Read them as the same tier as the existing `database_modeling` schema ticket.
"""

from __future__ import annotations

from typing import Any

from app.services import sql_judge

# --------------------------------------------------------------------------- #
#  The warehouse the SQL tickets query.
#
#  Table names are fixed rather than interpolated from the project domain: a
#  domain noun is inferred from free text and would land inside SQL identifiers,
#  where a stray keyword (`order`) or an odd word breaks the DDL for everyone.
#  The ticket prose is contextualised instead.
# --------------------------------------------------------------------------- #

WAREHOUSE_SCHEMA = [
    """
    CREATE TABLE customers (
        id      INTEGER PRIMARY KEY,
        name    TEXT    NOT NULL,
        city    TEXT,
        channel TEXT,
        signup  TEXT    NOT NULL
    );
    CREATE TABLE orders (
        id          INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        product     TEXT    NOT NULL,
        amount      REAL,
        status      TEXT    NOT NULL,
        placed_at   TEXT    NOT NULL
    );
    CREATE TABLE raw_events (
        event_id    INTEGER,
        customer_id INTEGER,
        kind        TEXT,
        discount    REAL,
        occurred_at TEXT
    );
    """
]

SCHEMA_BRIEF = (
    "The warehouse gives you three tables:\n\n"
    "- `customers(id, name, city, channel, signup)`\n"
    "- `orders(id, customer_id, product, amount, status, placed_at)` — `status` is "
    "`paid`, `pending` or `refunded`; only `paid` is revenue, and `amount` may be NULL\n"
    "- `raw_events(event_id, customer_id, kind, discount, occurred_at)` — an "
    "append-only feed that repeats `event_id` on retry and leaves `discount` NULL "
    "when no promo code was used\n\n"
    "Your query is executed against several datasets, including ones you cannot "
    "see, so it must answer the question rather than reproduce one answer."
)


def _customers(rows: list[tuple]) -> list[dict[str, Any]]:
    return [
        {"id": i, "name": n, "city": c, "channel": ch, "signup": s}
        for i, n, c, ch, s in rows
    ]


def _orders(rows: list[tuple]) -> list[dict[str, Any]]:
    return [
        {
            "id": i,
            "customer_id": cid,
            "product": p,
            "amount": a,
            "status": st,
            "placed_at": at,
        }
        for i, cid, p, a, st, at in rows
    ]


def _events(rows: list[tuple]) -> list[dict[str, Any]]:
    return [
        {"event_id": e, "customer_id": c, "kind": k, "discount": d, "occurred_at": at}
        for e, c, k, d, at in rows
    ]


#: Dataset 1 — the shape a learner sees while developing.
_WAREHOUSE_A = {
    "customers": _customers(
        [
            (1, "Alice Okafor", "Leeds", "organic", "2023-01-14"),
            (2, "Bo Chen", "Leeds", "paid_ads", "2024-02-02"),
            (3, "Carla Ruiz", "Bristol", "organic", "2024-02-19"),
            (4, "Dev Patel", "Bristol", "referral", "2024-03-01"),
            (5, "Eve Nowak", "Bristol", "paid_ads", "2022-06-11"),
        ]
    ),
    "orders": _orders(
        [
            (1, 1, "Standing desk", 320.0, "paid", "2024-04-02"),
            (2, 1, "Desk mat", 24.5, "paid", "2024-04-09"),
            (3, 2, "Monitor arm", 89.99, "paid", "2024-04-11"),
            (4, 2, "Cable tray", 18.0, "refunded", "2024-04-12"),
            (5, 3, "Standing desk", 320.0, "paid", "2024-04-15"),
            (6, 3, "Monitor arm", None, "pending", "2024-04-16"),
            (7, 5, "Desk mat", 24.5, "paid", "2024-04-20"),
        ]
    ),
    "raw_events": _events(
        [
            (100, 1, "checkout", 5.0, "2024-04-02T10:00:00"),
            (100, 1, "checkout", 5.0, "2024-04-02T10:00:04"),
            (101, 2, "checkout", None, "2024-04-11T09:15:00"),
            (102, 3, "signup", None, "2024-02-19T08:00:00"),
            (103, 5, "checkout", 2.5, "2024-04-20T17:30:00"),
            (103, 5, "checkout", 2.5, "2024-04-20T17:30:02"),
        ]
    ),
}

#: Dataset 2 — a deliberately different world: different cities, a different
#: channel mix, a customer whose only order is refunded, and a NULL amount on a
#: *paid* order. Nothing a constant answer can straddle.
_WAREHOUSE_B = {
    "customers": _customers(
        [
            (1, "Erin Vale", "Cardiff", "referral", "2022-11-30"),
            (2, "Femi Adeyemi", "Cardiff", "organic", "2024-01-08"),
            (3, "Greta Lind", "Oslo", "paid_ads", "2024-07-21"),
            (4, "Hugo Meyer", "Oslo", "organic", "2024-08-02"),
        ]
    ),
    "orders": _orders(
        [
            (1, 1, "Desk mat", 24.5, "refunded", "2024-09-01"),
            (2, 2, "Standing desk", 320.0, "paid", "2024-09-03"),
            (3, 2, "Desk mat", 24.5, "paid", "2024-09-04"),
            (4, 3, "Monitor arm", 89.99, "paid", "2024-09-07"),
            (5, 4, "Cable tray", None, "paid", "2024-09-09"),
        ]
    ),
    "raw_events": _events(
        [
            (200, 2, "checkout", None, "2024-09-03T12:00:00"),
            (201, 3, "checkout", 9.0, "2024-09-07T13:00:00"),
            (201, 3, "checkout", 9.0, "2024-09-07T13:00:01"),
            (201, 3, "checkout", 9.0, "2024-09-07T13:00:03"),
            (202, 4, "signup", None, "2024-08-02T07:45:00"),
        ]
    ),
}

#: Dataset 3 — the degenerate world: nothing is paid, so aggregate answers must
#: be zero rows rather than a row of NULLs.
_WAREHOUSE_C = {
    "customers": _customers(
        [
            (1, "Hana Sato", "Kyoto", "organic", "2024-05-05"),
            (2, "Ivan Petrov", "Kyoto", "paid_ads", "2021-05-06"),
        ]
    ),
    "orders": _orders(
        [
            (1, 1, "Cable tray", 18.0, "refunded", "2024-06-01"),
            (2, 2, "Cable tray", 18.0, "pending", "2024-06-02"),
        ]
    ),
    "raw_events": _events(
        [
            (300, 1, "signup", None, "2024-05-05T06:00:00"),
            (301, 2, "checkout", 1.0, "2024-06-02T06:00:00"),
        ]
    ),
}


def _spec(
    reference: str,
    ordered: bool = False,
    require_columns: bool = False,
    datasets: tuple[str, ...] = ("A", "B", "C"),
) -> dict[str, Any]:
    worlds = {"A": _WAREHOUSE_A, "B": _WAREHOUSE_B, "C": _WAREHOUSE_C}
    labels = {
        "A": "sample: Leeds and Bristol",
        "B": "hidden: Cardiff and Oslo",
        "C": "hidden: nothing paid",
    }
    return {
        "schema": WAREHOUSE_SCHEMA,
        "reference": reference,
        "ordered": ordered,
        "require_columns": require_columns,
        "datasets": [
            {
                "name": labels[key],
                "rows": worlds[key],
                **({"hidden": True} if key != "A" else {}),
            }
            for key in datasets
        ],
    }


def _sql_check(
    check_id: str,
    label: str,
    spec: dict[str, Any],
    concept: str,
    requirement_index: int | None = None,
    hint: str | None = None,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "type": "sql_query",
        "file": "query.sql",
        "spec": spec,
        "label": label,
        "concept": concept,
        "requirement_index": requirement_index,
        **({"hint": hint} if hint else {}),
    }


# --------------------------------------------------------------------------- #
#  Reference queries, one per SQL ticket
# --------------------------------------------------------------------------- #

_ACTIVE_CUSTOMERS = _spec(
    "SELECT name, city FROM customers WHERE signup >= '2024-01-01'"
)

_ORDERS_WITH_CUSTOMER = _spec(
    "SELECT c.name AS name, o.product AS product, o.amount AS amount "
    "FROM orders o JOIN customers c ON c.id = o.customer_id "
    "WHERE o.status = 'paid' AND o.amount IS NOT NULL"
)

_REVENUE_BY_CITY = _spec(
    "SELECT c.city AS city, SUM(o.amount) AS revenue "
    "FROM customers c JOIN orders o ON o.customer_id = c.id "
    "WHERE o.status = 'paid' AND o.amount IS NOT NULL "
    "GROUP BY c.city"
)

_CITY_RANKING = _spec(
    "WITH totals AS ("
    "  SELECT c.city AS city, SUM(o.amount) AS revenue"
    "  FROM customers c JOIN orders o ON o.customer_id = c.id"
    "  WHERE o.status = 'paid' AND o.amount IS NOT NULL"
    "  GROUP BY c.city"
    ") "
    "SELECT city, revenue, RANK() OVER (ORDER BY revenue DESC) AS revenue_rank "
    "FROM totals ORDER BY revenue DESC, city ASC",
    ordered=True,
    require_columns=True,
)

_DEDUPED_EVENTS = _spec(
    "SELECT event_id, customer_id, MIN(occurred_at) AS occurred_at, "
    "COALESCE(discount, 0) AS discount "
    "FROM raw_events WHERE kind = 'checkout' "
    "GROUP BY event_id, customer_id, COALESCE(discount, 0)"
)

_CONVERSION_BY_CHANNEL = _spec(
    "SELECT c.channel AS channel, "
    "COUNT(DISTINCT c.id) AS customers, "
    "COUNT(DISTINCT CASE WHEN o.status = 'paid' THEN c.id END) AS buyers "
    "FROM customers c LEFT JOIN orders o ON o.customer_id = c.id "
    "GROUP BY c.channel"
)

_RELIABLE_SEGMENTS = _spec(
    "SELECT c.city AS city, COUNT(*) AS paid_orders, AVG(o.amount) AS avg_order "
    "FROM customers c JOIN orders o ON o.customer_id = c.id "
    "WHERE o.status = 'paid' AND o.amount IS NOT NULL "
    "GROUP BY c.city HAVING COUNT(*) >= 2"
)


DATA_TICKET_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    # ------------------------------------------------------------ sql_basics
    "sql_basics": [
        {
            "slug": "sql-active-customers",
            "title": "Pull the {domain} customer list for this year",
            "description": (
                "Before any {entity} analysis can start, {domain} needs a reliable "
                "list of the customers who joined this year. Write the query the "
                "rest of the reporting will build on.\n\n" + SCHEMA_BRIEF
            ),
            "requirements": [
                "Return exactly two columns: the customer's name and city",
                "Include only customers whose signup date is on or after 2024-01-01",
                "Select the columns you need explicitly — no SELECT *",
            ],
            "acceptance_criteria": [
                "The query returns name and city and nothing else",
                "Customers who signed up before 2024 are excluded",
                "The result is correct on fixture data the query has not seen",
            ],
            "estimated_minutes": 25,
            "files": ["query.sql"],
            "checks": [
                _sql_check(
                    "result",
                    "Returns the 2024 customers, executed against the fixtures",
                    _ACTIVE_CUSTOMERS,
                    "where",
                    requirement_index=1,
                    hint=(
                        "Compare the signup date as a string: ISO dates sort "
                        "correctly, so `signup >= '2024-01-01'` works."
                    ),
                ),
                {
                    "id": "no_star",
                    "type": "not_regex",
                    "file": "query.sql",
                    "pattern": r"(?i)select\s+\*",
                    "label": "Columns are selected explicitly, not with SELECT *",
                    "concept": "select",
                    "requirement_index": 2,
                },
            ],
        }
    ],
    # ------------------------------------------------------------- sql_joins
    "sql_joins": [
        {
            "slug": "sql-order-detail",
            "title": "Join {entity_plural} to the customers who bought them",
            "description": (
                "The {entity} table only carries a customer id, so no report can "
                "name a buyer. Produce the joined detail rows the {domain} "
                "reporting layer will read.\n\n" + SCHEMA_BRIEF
            ),
            "requirements": [
                "Return three columns: customer name, product and amount",
                "Join orders to customers on the customer id",
                "Include only paid orders that actually carry an amount",
            ],
            "acceptance_criteria": [
                "Every returned row names the customer who placed the order",
                "Pending and refunded orders are excluded",
                "Paid orders with a NULL amount do not appear as blank rows",
            ],
            "estimated_minutes": 30,
            "files": ["query.sql"],
            "checks": [
                _sql_check(
                    "result",
                    "Returns joined paid order detail, executed against the fixtures",
                    _ORDERS_WITH_CUSTOMER,
                    "inner join",
                    requirement_index=1,
                    hint=(
                        "A paid order can still have a NULL amount — `amount IS NOT "
                        "NULL` is a separate condition from the status filter."
                    ),
                ),
                {
                    "id": "explicit_join",
                    "type": "regex",
                    "file": "query.sql",
                    "pattern": r"(?i)\bjoin\b",
                    "label": "Uses an explicit JOIN rather than a comma cross join",
                    "concept": "join keys",
                    "requirement_index": 1,
                },
            ],
        }
    ],
    # ------------------------------------------------------- sql_aggregation
    "sql_aggregation": [
        {
            "slug": "sql-revenue-by-city",
            "title": "Report {domain} revenue by city",
            "description": (
                "The first number anyone will ask {domain} for is revenue split by "
                "city. Aggregate it from the order rows.\n\n" + SCHEMA_BRIEF
            ),
            "requirements": [
                "Return two columns: city and total paid revenue",
                "Count only paid orders, and only those with an amount",
                "Group by city so each city appears once",
                "Return no rows at all when nothing is paid, rather than one NULL row",
            ],
            "acceptance_criteria": [
                "Each city appears exactly once with its paid revenue",
                "Refunded and pending orders contribute nothing",
                "An all-unpaid dataset produces an empty result, not a NULL row",
            ],
            "estimated_minutes": 35,
            "files": ["query.sql"],
            "checks": [
                _sql_check(
                    "result",
                    "Returns paid revenue per city, executed against the fixtures",
                    _REVENUE_BY_CITY,
                    "group by",
                    requirement_index=2,
                    hint=(
                        "An aggregate without GROUP BY always returns one row — a "
                        "NULL one when there is no data. GROUP BY returns none."
                    ),
                ),
                {
                    "id": "grouped",
                    "type": "regex",
                    "file": "query.sql",
                    "pattern": r"(?i)group\s+by",
                    "label": "Aggregates with GROUP BY",
                    "concept": "group by",
                    "requirement_index": 2,
                },
            ],
        }
    ],
    # --------------------------------------------------------- sql_analytics
    "sql_analytics": [
        {
            "slug": "sql-city-ranking",
            "title": "Rank {domain} cities by revenue",
            "description": (
                "The summary tile needs cities in rank order with their rank shown, "
                "so a reader can see both the ordering and the gaps.\n\n"
                "Aggregate the revenue first, then rank the totals — a window "
                "function cannot rank an aggregate in the same query level.\n\n"
                + SCHEMA_BRIEF
            ),
            "requirements": [
                "Return three columns named exactly city, revenue and revenue_rank",
                "Aggregate paid revenue per city in a CTE or subquery first",
                "Rank by revenue descending, so rank 1 is the highest-revenue city",
                "Order the rows by revenue descending, then city ascending",
            ],
            "acceptance_criteria": [
                "Column names are exactly city, revenue, revenue_rank",
                "Rank 1 is the highest-revenue city",
                "Rows come back in the required order, not an arbitrary one",
            ],
            "estimated_minutes": 45,
            "files": ["query.sql"],
            "checks": [
                _sql_check(
                    "result",
                    "Returns the ranked city revenue, executed against the fixtures",
                    _CITY_RANKING,
                    "window function",
                    requirement_index=2,
                    hint=(
                        "This ticket grades row order and column names, so the "
                        "ORDER BY and the aliases both matter."
                    ),
                ),
                {
                    "id": "window",
                    "type": "regex",
                    "file": "query.sql",
                    "pattern": r"(?i)over\s*\(",
                    "label": "Uses a window function for the rank",
                    "concept": "ranking",
                    "requirement_index": 2,
                },
            ],
        }
    ],
    # --------------------------------------------------------- data_cleaning
    "data_cleaning": [
        {
            "slug": "sql-dedupe-feed",
            "title": "Clean the raw {entity} event feed",
            "description": (
                "`raw_events` is append-only and the client retries, so a checkout "
                "can be logged several times with the same `event_id`. `discount` "
                "is NULL when no promo code was used, which is a known zero rather "
                "than a missing measurement. Produce the cleaned checkout feed "
                "{domain} reporting can trust.\n\n" + SCHEMA_BRIEF
            ),
            "requirements": [
                "Return four columns: event_id, customer_id, occurred_at and discount",
                "Emit one row per checkout event, keeping the earliest occurred_at",
                "Represent a missing discount as 0, not NULL",
                "Include checkout events only",
            ],
            "acceptance_criteria": [
                "A retried event appears exactly once, at its first timestamp",
                "No discount value is NULL in the output",
                "Signup events are excluded",
            ],
            "estimated_minutes": 40,
            "files": ["query.sql"],
            "checks": [
                _sql_check(
                    "result",
                    "Returns the de-duplicated, NULL-free feed, executed against the fixtures",
                    _DEDUPED_EVENTS,
                    "duplicates",
                    requirement_index=1,
                    hint=(
                        "SELECT DISTINCT will not do it on its own: pick the "
                        "surviving row deliberately with MIN(occurred_at) or "
                        "ROW_NUMBER()."
                    ),
                ),
                {
                    "id": "null_handling",
                    "type": "regex",
                    "file": "query.sql",
                    "pattern": r"(?i)(coalesce|ifnull|case\s+when)",
                    "label": "Handles the NULL discount explicitly",
                    "concept": "missing values",
                    "requirement_index": 2,
                },
            ],
        }
    ],
    # -------------------------------------------------- exploratory_analysis
    "exploratory_analysis": [
        {
            "slug": "sql-conversion-by-channel",
            "title": "Segment {domain} conversion by acquisition channel",
            "description": (
                "The overall conversion rate hides everything useful. Break it down "
                "by the channel a customer arrived through, so a shift in the "
                "traffic mix cannot masquerade as a change in performance.\n\n"
                "Every channel must appear, including one where nobody has bought "
                "yet — a zero is a finding, and an inner join would delete it.\n\n"
                + SCHEMA_BRIEF
            ),
            "requirements": [
                "Return three columns: channel, the number of customers, and the number who have a paid order",
                "Count distinct customers, so a customer with three orders counts once",
                "Include every channel, even one with no buyers",
                "Group by channel",
            ],
            "acceptance_criteria": [
                "Each channel appears once with both counts",
                "A channel with no paid orders shows a buyer count of 0 rather than vanishing",
                "A customer with several orders is not counted several times",
            ],
            "estimated_minutes": 45,
            "files": ["query.sql"],
            "checks": [
                _sql_check(
                    "result",
                    "Returns per-channel customer and buyer counts, executed against the fixtures",
                    _CONVERSION_BY_CHANNEL,
                    "segmentation",
                    requirement_index=2,
                    hint=(
                        "A LEFT JOIN keeps the channel; putting the status filter in "
                        "WHERE would throw it away again. Filter inside the "
                        "aggregate instead, with COUNT(DISTINCT CASE WHEN ...)."
                    ),
                ),
                {
                    "id": "distinct_counting",
                    "type": "regex",
                    "file": "query.sql",
                    "pattern": r"(?i)count\s*\(\s*distinct",
                    "label": "Counts distinct customers rather than order rows",
                    "concept": "fan-out",
                    "requirement_index": 1,
                },
            ],
        }
    ],
    # --------------------------------------------------- statistics_business
    "statistics_business": [
        {
            "slug": "sql-reliable-segments",
            "title": "Report {domain} average order value with its sample size",
            "description": (
                "An average order value quoted for a city with one order is noise "
                "presented as a number. Report the average *with* the count it is "
                "based on, and suppress segments too small to say anything about.\n\n"
                + SCHEMA_BRIEF
            ),
            "requirements": [
                "Return three columns: city, the number of paid orders, and the average order amount",
                "Include only paid orders that carry an amount",
                "Suppress any city with fewer than 2 paid orders",
                "Group by city",
            ],
            "acceptance_criteria": [
                "Every returned row carries the sample size behind its average",
                "Cities with a single paid order do not appear",
                "The threshold is applied after aggregation, not before",
            ],
            "estimated_minutes": 40,
            "files": ["query.sql"],
            "checks": [
                _sql_check(
                    "result",
                    "Returns averages with sample sizes above the threshold, executed against the fixtures",
                    _RELIABLE_SEGMENTS,
                    "sampling",
                    requirement_index=2,
                    hint=(
                        "A count threshold is a condition on the group, so it "
                        "belongs in HAVING — WHERE cannot see COUNT(*)."
                    ),
                ),
                {
                    "id": "having",
                    "type": "regex",
                    "file": "query.sql",
                    "pattern": r"(?i)having",
                    "label": "Filters groups with HAVING",
                    "concept": "having",
                    "requirement_index": 2,
                },
            ],
        }
    ],
    # ---------------------------------------------------- data_visualization
    #
    # Structural checks only: a chart spec is prose, and there is nothing to
    # execute. They verify the decisions were made and recorded, not that they
    # were the right ones.
    "data_visualization": [
        {
            "slug": "chart-spec",
            "title": "Specify the {domain} revenue chart",
            "description": (
                "Before anything is drawn, write down what the chart is for. State "
                "the question it answers, the chart type and why, what each visual "
                "channel encodes, and the axis baseline — a truncated axis on a bar "
                "chart is the single most common way a chart misleads.\n\n"
                "This ticket is graded structurally: it checks that each decision "
                "is stated, not that it is the best one. Your reviewer judges the "
                "reasoning."
            ),
            "requirements": [
                "State the question the chart answers, as a question",
                "Name the chart type and justify it in one sentence",
                "Say what the x axis, y axis and colour each encode (or that colour encodes nothing)",
                "State the y-axis baseline explicitly and justify it if it is not zero",
                "List the data source: the table(s) and the filter applied",
            ],
            "acceptance_criteria": [
                "Every section is present and non-empty",
                "The chart type is justified rather than asserted",
                "The axis baseline decision is explicit",
            ],
            "estimated_minutes": 30,
            "files": ["chart_spec.md"],
            "checks": [
                {
                    "id": "not_empty",
                    "type": "min_lines",
                    "file": "chart_spec.md",
                    "count": 10,
                    "label": "The spec has actual content",
                    "concept": "chart choice",
                    "requirement_index": None,
                    "precondition": True,
                },
                {
                    "id": "question",
                    "type": "regex",
                    "file": "chart_spec.md",
                    "pattern": r"\?",
                    "label": "States the question the chart answers",
                    "concept": "chart choice",
                    "requirement_index": 0,
                },
                {
                    "id": "chart_type",
                    "type": "regex",
                    "file": "chart_spec.md",
                    "pattern": r"(?i)(bar|line|dot|scatter|area|histogram)\s*(chart|plot)?",
                    "label": "Names a chart type",
                    "concept": "chart choice",
                    "requirement_index": 1,
                },
                {
                    "id": "justification",
                    "type": "regex",
                    "file": "chart_spec.md",
                    "pattern": r"(?i)(because|since|so that|reason)",
                    "label": "Justifies the chart type rather than only naming it",
                    "concept": "chart choice",
                    "requirement_index": 1,
                    "hint": "One sentence starting 'because ...' is enough.",
                },
                {
                    "id": "encodings",
                    "type": "regex",
                    "file": "chart_spec.md",
                    "pattern": r"(?i)x\s*axis[\s\S]*y\s*axis[\s\S]*colou?r",
                    "label": "Says what the x axis, y axis and colour encode",
                    "concept": "encoding",
                    "requirement_index": 2,
                },
                {
                    "id": "baseline",
                    "type": "regex",
                    "file": "chart_spec.md",
                    "pattern": r"(?i)(baseline|start(s|ing)?\s+at|axis\s+(starts|begins)|zero|truncat)",
                    "label": "States the y-axis baseline explicitly",
                    "concept": "axis truncation",
                    "requirement_index": 3,
                },
                {
                    "id": "source",
                    "type": "regex",
                    "file": "chart_spec.md",
                    "pattern": r"(?i)(orders|customers|raw_events|table)",
                    "label": "Names the data source and filter",
                    "concept": "chart choice",
                    "requirement_index": 4,
                },
            ],
        }
    ],
    # ------------------------------------------------------- dashboard_design
    "dashboard_design": [
        {
            "slug": "dashboard-spec",
            "title": "Design the {domain} dashboard",
            "description": (
                "Specify the dashboard: who reads it, the decision it supports, and "
                "each tile with its metric definition. A metric without a written "
                "definition is how two dashboards come to disagree about the same "
                "word.\n\n"
                "Graded structurally — it checks that the definitions and the "
                "comparison baselines exist, not that the dashboard is good."
            ),
            "requirements": [
                "Name the audience and the decision the dashboard supports",
                "List each tile with its metric and the exact definition (window, de-duplication, filters)",
                "Give every KPI a comparison: a target, or the prior period",
                "Describe the drill-down path from a summary tile to the detail",
                "State the refresh cadence and what 'no data' displays as",
            ],
            "acceptance_criteria": [
                "Each tile has a written metric definition, not just a name",
                "Every KPI carries a baseline or target to compare against",
                "The drill-down path and the empty state are both specified",
            ],
            "estimated_minutes": 40,
            "files": ["dashboard.md"],
            "checks": [
                {
                    "id": "not_empty",
                    "type": "min_lines",
                    "file": "dashboard.md",
                    "count": 12,
                    "label": "The spec has actual content",
                    "concept": "dashboard layout",
                    "requirement_index": None,
                    "precondition": True,
                },
                {
                    "id": "audience",
                    "type": "regex",
                    "file": "dashboard.md",
                    "pattern": r"(?i)(audience|reader|for\s+the\s+\w+\s+team|exec|analyst|manager)",
                    "label": "Names the audience",
                    "concept": "audience",
                    "requirement_index": 0,
                },
                {
                    "id": "decision",
                    "type": "regex",
                    "file": "dashboard.md",
                    "pattern": r"(?i)(decision|decide|action|so that|in order to)",
                    "label": "States the decision the dashboard supports",
                    "concept": "narrative",
                    "requirement_index": 0,
                },
                {
                    "id": "definitions",
                    "type": "regex",
                    "file": "dashboard.md",
                    "pattern": r"(?i)(definition|defined as|counts?\s+(as|distinct)|window|rolling|last\s+\d+\s+days|distinct)",
                    "label": "Defines each metric, not just its name",
                    "concept": "kpi",
                    "requirement_index": 1,
                    "hint": "Say the window and the de-duplication rule: 'distinct users active in the last 7 days'.",
                },
                {
                    "id": "comparison",
                    "type": "regex",
                    "file": "dashboard.md",
                    "pattern": r"(?i)(target|baseline|prior|previous|vs\.?\s|compared|last\s+(week|month|quarter)|year\s*on\s*year)",
                    "label": "Every KPI has a target or a prior-period comparison",
                    "concept": "kpi",
                    "requirement_index": 2,
                },
                {
                    "id": "drilldown",
                    "type": "regex",
                    "file": "dashboard.md",
                    "pattern": r"(?i)(drill|click through|links? to|detail view|breakdown|filter to)",
                    "label": "Describes the drill-down path",
                    "concept": "drill-down",
                    "requirement_index": 3,
                },
                {
                    "id": "empty_state",
                    "type": "regex",
                    "file": "dashboard.md",
                    "pattern": r"(?i)(no data|empty|refresh|cadence|updated|stale)",
                    "label": "States the refresh cadence and the empty state",
                    "concept": "dashboard layout",
                    "requirement_index": 4,
                },
            ],
        }
    ],
    # ----------------------------------------------------- spreadsheet_modeling
    "spreadsheet_modeling": [
        {
            "slug": "spreadsheet-model",
            "title": "Build the {domain} revenue model",
            "description": (
                "Hand over a model a reviewer can re-run under different "
                "assumptions without editing a single formula. That means the "
                "assumptions live in their own labelled cells and every formula "
                "references them — a growth rate typed into twelve formulas cannot "
                "be found, changed consistently or reviewed.\n\n"
                "Submit the model as `model.csv`: the assumptions block, the header "
                "row, and the formulas as text (`=B4*$B$1`). Graded structurally."
            ),
            "requirements": [
                "Put every assumption in its own labelled cell in an assumptions block",
                "Reference assumptions with absolute references ($B$1) from the formulas",
                "Never hardcode a rate or a multiplier inside a formula",
                "Use a lookup formula (VLOOKUP, XLOOKUP or INDEX/MATCH) to bring in the per-product price",
                "Include a total row computed with a formula, not a typed number",
            ],
            "acceptance_criteria": [
                "Changing one assumption cell changes every dependent figure",
                "No numeric rate appears inside a formula",
                "The total is a formula, not a literal",
            ],
            "estimated_minutes": 40,
            "files": ["model.csv"],
            "checks": [
                {
                    "id": "not_empty",
                    "type": "min_lines",
                    "file": "model.csv",
                    "count": 6,
                    "label": "The model has rows",
                    "concept": "scenario model",
                    "requirement_index": None,
                    "precondition": True,
                },
                {
                    "id": "assumptions",
                    "type": "regex",
                    "file": "model.csv",
                    "pattern": r"(?i)(assumption|input|rate|growth)",
                    "label": "Has a labelled assumptions block",
                    "concept": "scenario model",
                    "requirement_index": 0,
                },
                {
                    "id": "absolute_ref",
                    "type": "regex",
                    "file": "model.csv",
                    "pattern": r"\$[A-Za-z]+\$?\d+",
                    "label": "Formulas reference assumptions absolutely ($B$1)",
                    "concept": "absolute reference",
                    "requirement_index": 1,
                    "hint": "A relative reference walks off the assumption when copied down.",
                },
                {
                    "id": "no_magic_number",
                    "type": "not_regex",
                    "file": "model.csv",
                    "pattern": r"=[^,\n]*\*\s*0?\.\d+",
                    "label": "No rate is hardcoded inside a formula",
                    "concept": "scenario model",
                    "requirement_index": 2,
                    "hint": "`=B4*0.08` hides the assumption. Point at the input cell instead.",
                },
                {
                    "id": "lookup",
                    "type": "regex",
                    "file": "model.csv",
                    "pattern": r"(?i)(vlookup|xlookup|index\s*\(|match\s*\(|lookup)",
                    "label": "Uses a lookup formula for the per-product price",
                    "concept": "lookup",
                    "requirement_index": 3,
                },
                {
                    "id": "total_formula",
                    "type": "regex",
                    "file": "model.csv",
                    "pattern": r"(?i)=\s*(sum|sumif|sumifs|subtotal)\s*\(",
                    "label": "The total is computed with a formula",
                    "concept": "formulas",
                    "requirement_index": 4,
                },
            ],
        }
    ],
}


#: Appended to `SPRINT_THEMES`. Data skills do not intersect the web themes, so
#: a data project gets only these sprints and an SDE project only the web ones.
DATA_SPRINT_THEMES: list[tuple[str, str, list[str]]] = [
    (
        "Data Foundation",
        "Querying & Aggregation",
        ["sql_basics", "sql_joins", "sql_aggregation", "sql_analytics"],
    ),
    (
        "Data Quality",
        "Cleaning & Exploration",
        ["data_cleaning", "exploratory_analysis"],
    ),
    (
        "Insight",
        "Statistics & Modelling",
        ["statistics_business", "spreadsheet_modeling"],
    ),
    (
        "Communication",
        "Visualisation & Dashboards",
        ["data_visualization", "dashboard_design"],
    ),
]


#: Starter files for the data deliverables, merged into `STARTER_FILES`.
DATA_STARTER_FILES: dict[str, str] = {
    "query.sql": """-- {domain}
-- Write the query this ticket asks for. It is executed against fixture
-- datasets (including ones you cannot see) and compared against a reference
-- result, so it has to answer the question rather than reproduce one answer.
""",
    "chart_spec.md": """# {domain} — chart specification

## Question this chart answers

## Chart type and why

## Encodings
- x axis:
- y axis:
- colour:

## Y-axis baseline

## Data source and filter
""",
    "dashboard.md": """# {domain} — dashboard specification

## Audience and the decision this supports

## Tiles
| Tile | Metric | Definition (window, de-duplication, filters) | Comparison |
| --- | --- | --- | --- |
|  |  |  |  |

## Drill-down path

## Refresh cadence and empty state
""",
    "model.csv": """Assumptions,,
Growth rate,0.00,<- the reviewer changes this cell only
,,
Product,Units,Revenue
,,
Total,,
""",
}


# Import-time validation. A ticket whose fixtures all share one answer would let
# a hardcoded constant close it, and a reference query that does not pass its own
# datasets would make the ticket unclosable. Both fail here, loudly, rather than
# on a learner's board.
for _skill, _templates in DATA_TICKET_TEMPLATES.items():
    for _template in _templates:
        for _check in _template["checks"]:
            if _check["type"] == "sql_query":
                sql_judge.validate_spec(
                    _check["spec"], f"ticket_templates_data: {_template['slug']}/{_check['id']}"
                )
