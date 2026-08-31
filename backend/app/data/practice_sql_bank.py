"""The SQL question bank for the Data Analyst path — ten questions per skill.

`practice_sql.py` holds the three proof-of-concept questions that establish the
format; this file holds the bank authored on top of them and is imported there,
so `SQL_MODULES` stays the single list the registry extends.

Everything here obeys the contract in `docs/sql_authoring.md`:

* Two fixture *worlds* (a retail store and a sales pipeline) are declared once,
  each with three datasets whose correct answers differ, so the hardcoded
  constant answer is structurally impossible rather than merely discouraged.
* Expected results are never written down: `reference` is the only source, and
  `sql_judge.validate_spec` re-derives every expectation at import time.
* Every question also declares `wrong` — queries a learner plausibly writes that
  must be *rejected*. They are held in `WRONG_SOLUTIONS`, keyed by module id,
  and `scripts/verify_data_analyst_curriculum.py` runs each one through the real
  judge and fails the build if any of them passes. Nothing in this module is
  shipped to a client: `practice_service.module_detail` builds its payload from
  an explicit key list.
"""

from __future__ import annotations

from typing import Any, Optional

# --------------------------------------------------------------------------- #
#  World 1 — STORE: customers and orders.                                     #
#                                                                             #
#  `city` and `amount` are nullable on purpose. NULL is the single most        #
#  common source of a wrong analyst answer, so it is in the fixtures rather    #
#  than in a footnote.                                                        #
# --------------------------------------------------------------------------- #

STORE_SCHEMA = [
    """
    CREATE TABLE customers (
        id      INTEGER PRIMARY KEY,
        name    TEXT    NOT NULL,
        city    TEXT,
        tier    TEXT,
        signup  TEXT    NOT NULL
    );
    CREATE TABLE orders (
        id          INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(id),
        product     TEXT    NOT NULL,
        category    TEXT    NOT NULL,
        amount      REAL,
        quantity    INTEGER NOT NULL,
        status      TEXT    NOT NULL,
        placed_on   TEXT    NOT NULL
    );
    """
]

STORE_NOTE = (
    "Two tables:\n\n"
    "`customers(id, name, city, tier, signup)` — one row per customer. `city` "
    "and `tier` can be NULL; `signup` is an ISO date string.\n"
    "`orders(id, customer_id, product, category, amount, quantity, status, "
    "placed_on)` — one row per order. `status` is one of `paid`, `pending`, "
    "`refunded`; `amount` is the line total in pounds and **can be NULL** when "
    "an order has not been priced yet; `placed_on` is an ISO date.\n\n"
    "Only `paid` orders count as revenue. Your query runs against several "
    "datasets, including ones you cannot see, so it has to answer the question "
    "rather than reproduce one particular answer."
)


def _store(customers: list[tuple], orders: list[tuple]) -> dict[str, Any]:
    return {
        "customers": [
            {"id": i, "name": n, "city": c, "tier": t, "signup": s}
            for i, n, c, t, s in customers
        ],
        "orders": [
            {
                "id": i,
                "customer_id": c,
                "product": p,
                "category": k,
                "amount": a,
                "quantity": q,
                "status": st,
                "placed_on": d,
            }
            for i, c, p, k, a, q, st, d in orders
        ],
    }


# Two cities, a NULL city that *does* buy things, a customer who never ordered,
# a NULL amount, an order on the quarter boundary, and a customer whose earliest
# order carries the highest id — every one of those exists to reject a specific
# plausible-but-wrong query rather than to decorate the fixture.
_STORE_1 = _store(
    customers=[
        (1, "Alice Okafor", "Leeds", "gold", "2023-01-14"),
        (2, "Bo Chen", "Leeds", "silver", "2024-02-02"),
        (3, "Carla Ruiz", "Bristol", "gold", "2024-03-19"),
        (4, "Dev Patel", None, "bronze", "2022-11-05"),
        (5, "Eve Adams", "Bristol", "silver", "2024-07-01"),
        (6, "Finn Doyle", "Leeds", "bronze", "2021-06-06"),
    ],
    orders=[
        (1, 1, "Standing desk", "furniture", 320.00, 1, "paid", "2024-01-01"),
        (2, 1, "Desk mat", "accessories", 24.50, 2, "paid", "2024-01-20"),
        (3, 2, "Monitor arm", "accessories", 89.99, 1, "paid", "2024-02-05"),
        (4, 2, "Cable tray", "accessories", 18.00, 3, "refunded", "2024-02-11"),
        (5, 3, "Standing desk", "furniture", 320.00, 1, "paid", "2024-03-02"),
        (6, 3, "Monitor arm", "accessories", None, 1, "pending", "2024-03-15"),
        (7, 5, "Task chair", "furniture", 210.00, 1, "paid", "2024-04-01"),
        (8, 1, "Task chair", "furniture", 210.00, 1, "paid", "2024-05-06"),
        (9, 4, "Desk mat", "accessories", 24.50, 1, "paid", "2024-06-06"),
        (10, 1, "Footrest", "accessories", 30.00, 1, "paid", "2023-12-20"),
    ],
)

# A different shape entirely: other cities, a NULL tier, a customer whose only
# order is refunded, repeated purchases of one product, and an order in 2025.
_STORE_2 = _store(
    customers=[
        (1, "Erin Vale", "Cardiff", "silver", "2022-11-30"),
        (2, "Femi Adeyemi", "Cardiff", "gold", "2024-01-08"),
        (3, "Greta Lind", "Oslo", None, "2023-07-21"),
        (4, "Hugo Reis", "Oslo", "bronze", "2024-09-09"),
        (5, "Iris Bell", "Oslo", "silver", "2024-04-04"),
    ],
    orders=[
        (1, 1, "Desk mat", "accessories", 24.50, 1, "refunded", "2024-02-02"),
        (2, 2, "Standing desk", "furniture", 320.00, 2, "paid", "2024-03-03"),
        (3, 2, "Desk mat", "accessories", 24.50, 1, "paid", "2024-03-04"),
        (4, 2, "Desk mat", "accessories", 24.50, 1, "paid", "2024-06-04"),
        (5, 3, "Monitor arm", "accessories", 89.99, 1, "paid", "2024-07-15"),
        # A high-value order that is *not* paid, so a query that forgets the
        # status filter is caught rather than accidentally right.
        (6, 4, "Task chair", "furniture", 210.00, 1, "pending", "2024-10-01"),
        (7, 3, "Task chair", "furniture", 210.00, 1, "paid", "2025-01-05"),
        # Exactly on the £100 threshold, and exactly on the £300 band boundary:
        # `>` and `>=` are different answers on this dataset.
        (8, 1, "Monitor stand", "accessories", 100.00, 1, "paid", "2024-08-08"),
        (9, 5, "Desk riser", "furniture", 300.00, 1, "paid", "2024-09-09"),
    ],
)

# The degenerate dataset authors forget: nothing is paid, so an aggregate has to
# return no rows rather than a row of NULLs.
_STORE_3 = _store(
    customers=[
        (1, "Hana Sato", "Kyoto", "bronze", "2024-05-05"),
        (2, "Ivan Petrov", None, "bronze", "2023-05-06"),
    ],
    orders=[
        (1, 1, "Cable tray", "accessories", 18.00, 1, "refunded", "2024-05-10"),
        (2, 2, "Cable tray", "accessories", None, 2, "pending", "2024-05-11"),
    ],
)

STORE_DATASETS = [
    {"name": "sample: Leeds and Bristol", "rows": _STORE_1},
    {"name": "hidden: Cardiff and Oslo", "rows": _STORE_2, "hidden": True},
    {"name": "hidden: nothing is paid", "rows": _STORE_3, "hidden": True},
]


# --------------------------------------------------------------------------- #
#  World 2 — SALES: a pipeline with regions, reps and dated deals.            #
#                                                                             #
#  This world exists for the time-series and ranking work: month-over-month,  #
#  running totals, per-group top-N, and a region with no reps so an outer      #
#  join is genuinely different from an inner one.                             #
# --------------------------------------------------------------------------- #

SALES_SCHEMA = [
    """
    CREATE TABLE regions (
        id   INTEGER PRIMARY KEY,
        name TEXT    NOT NULL
    );
    CREATE TABLE reps (
        id        INTEGER PRIMARY KEY,
        name      TEXT    NOT NULL,
        region_id INTEGER REFERENCES regions(id),
        hire_date TEXT    NOT NULL
    );
    CREATE TABLE deals (
        id        INTEGER PRIMARY KEY,
        rep_id    INTEGER NOT NULL REFERENCES reps(id),
        product   TEXT    NOT NULL,
        amount    REAL    NOT NULL,
        closed_on TEXT    NOT NULL,
        stage     TEXT    NOT NULL
    );
    """
]

SALES_NOTE = (
    "Three tables:\n\n"
    "`regions(id, name)` — sales regions. A region can have no reps.\n"
    "`reps(id, name, region_id, hire_date)` — one row per sales rep; "
    "`region_id` can be NULL for an unassigned rep.\n"
    "`deals(id, rep_id, product, amount, closed_on, stage)` — one row per deal. "
    "`stage` is one of `won`, `lost`, `open`; `closed_on` is an ISO date, so "
    "`substr(closed_on, 1, 7)` is the month.\n\n"
    "Only `won` deals count as booked revenue. Your query runs against several "
    "datasets, including ones you cannot see."
)


def _sales(regions: list[tuple], reps: list[tuple], deals: list[tuple]) -> dict[str, Any]:
    return {
        "regions": [{"id": i, "name": n} for i, n in regions],
        "reps": [
            {"id": i, "name": n, "region_id": r, "hire_date": h} for i, n, r, h in reps
        ],
        "deals": [
            {
                "id": i,
                "rep_id": r,
                "product": p,
                "amount": a,
                "closed_on": c,
                "stage": s,
            }
            for i, r, p, a, c, s in deals
        ],
    }


_SALES_1 = _sales(
    regions=[(1, "EMEA"), (2, "APAC")],
    reps=[
        (1, "Ana Duarte", 1, "2022-01-05"),
        (2, "Ben Ortiz", 1, "2023-03-10"),
        (3, "Cai Wen", 2, "2023-06-01"),
        (4, "Dia Kaur", None, "2024-02-02"),
    ],
    deals=[
        (1, 1, "Platform", 5000.0, "2024-01-15", "won"),
        (2, 1, "Platform", 3000.0, "2024-02-20", "won"),
        (3, 2, "Addon", 1500.0, "2024-01-25", "lost"),
        (4, 2, "Platform", 4000.0, "2024-03-05", "won"),
        (5, 3, "Addon", 2500.0, "2024-02-11", "won"),
        (6, 3, "Platform", 7000.0, "2024-04-01", "open"),
        (7, 4, "Addon", 1000.0, "2024-03-30", "won"),
        (8, 1, "Addon", 2000.0, "2024-05-10", "won"),
    ],
)

_SALES_2 = _sales(
    regions=[(1, "AMER"), (2, "EMEA"), (3, "LATAM")],
    reps=[
        (1, "Eli Novak", 1, "2021-09-09"),
        (2, "Fay Bello", 2, "2024-01-02"),
        (3, "Gus Meier", 1, "2022-04-04"),
        # A rep with no deals at all: "has a deal that was not won" and "has no
        # won deal" are different sets because of her.
        (4, "Hana Oduya", 2, "2024-03-03"),
    ],
    deals=[
        (1, 1, "Platform", 9000.0, "2024-02-01", "won"),
        (2, 1, "Addon", 500.0, "2024-02-15", "won"),
        (3, 2, "Platform", 9000.0, "2024-03-01", "lost"),
        (4, 3, "Addon", 3000.0, "2024-03-20", "won"),
        (5, 3, "Addon", 3000.0, "2024-04-20", "won"),
        (6, 3, "Platform", 12000.0, "2024-06-01", "open"),
    ],
)

# Nothing is won: a booked-revenue aggregate must return no rows here.
_SALES_3 = _sales(
    regions=[(1, "EMEA"), (2, "APAC")],
    reps=[(1, "Hal Byrne", 1, "2024-05-01"), (2, "Ida Fors", 2, "2024-05-02")],
    deals=[
        (1, 1, "Addon", 800.0, "2024-06-01", "open"),
        (2, 2, "Addon", 900.0, "2024-06-02", "lost"),
    ],
)

SALES_DATASETS = [
    {"name": "sample: EMEA and APAC", "rows": _SALES_1},
    {"name": "hidden: AMER, EMEA and LATAM", "rows": _SALES_2, "hidden": True},
    {"name": "hidden: nothing is won", "rows": _SALES_3, "hidden": True},
]


WORLDS: dict[str, tuple[list[str], list[dict[str, Any]], str]] = {
    "store": (STORE_SCHEMA, STORE_DATASETS, STORE_NOTE),
    "sales": (SALES_SCHEMA, SALES_DATASETS, SALES_NOTE),
}


# --------------------------------------------------------------------------- #
#  Question builder                                                           #
# --------------------------------------------------------------------------- #

#: module id -> wrong queries that must be rejected. Consumed by
#: `scripts/verify_data_analyst_curriculum.py`; never served.
WRONG_SOLUTIONS: dict[str, list[str]] = {}

SQL_BANK: list[dict[str, Any]] = []


def _question(
    *,
    id: str,
    title: str,
    skill_id: str,
    concept: str,
    difficulty: int,
    minutes: int,
    summary: str,
    statement: str,
    requirements: list[str],
    reference: str,
    world: str,
    wrong: list[str],
    secondary_skill_id: Optional[str] = None,
    ordered: bool = False,
    require_columns: bool = False,
) -> dict[str, Any]:
    """One question, in the same dict shape as the three reference questions."""
    schema, datasets, note = WORLDS[world]
    if not wrong:
        raise ValueError(f"{id}: a question with no wrong solution proves nothing")

    spec: dict[str, Any] = {
        "schema": schema,
        "reference": reference,
        "ordered": ordered,
        "require_columns": require_columns,
        "datasets": datasets,
    }

    order_note = (
        "\n\n**Row order is graded for this question.** The right rows in the "
        "wrong order is a wrong answer."
        if ordered
        else ""
    )
    alias_note = (
        "\n\n**Column names are graded for this question**, so alias your "
        "columns exactly as named above."
        if require_columns
        else ""
    )

    module = {
        "id": id,
        "title": title,
        "kind": "sql",
        "practice_layer": "query",
        "skill_id": skill_id,
        "technology": "SQL",
        "language": "sql",
        "concept": concept,
        "difficulty": difficulty,
        "estimated_minutes": minutes,
        "summary": summary,
        "problem_statement": statement + order_note + alias_note + "\n\n" + note,
        "requirements": requirements,
        "editable_files": ["query.sql"],
        "files": {
            "query.sql": (
                f"-- {title}\n"
                f"-- {summary}\n"
                "-- TODO: write the query.\n"
            )
        },
        "solution_files": {"query.sql": reference},
        "sql_spec": spec,
        "checks": [],
    }
    if secondary_skill_id:
        module["secondary_skill_id"] = secondary_skill_id

    WRONG_SOLUTIONS[id] = list(wrong)
    SQL_BANK.append(module)
    return module


# --------------------------------------------------------------------------- #
#  sql_basics — SELECT, WHERE, ORDER BY, DISTINCT, NULL                       #
# --------------------------------------------------------------------------- #

_question(
    id="sql-basics-gold-customers",
    title="Gold-tier Customers",
    skill_id="sql_basics",
    concept="where",
    difficulty=1,
    minutes=10,
    summary="List the name of every gold-tier customer.",
    statement=(
        "Return **one column**, the `name` of every customer whose `tier` is "
        "exactly `gold`. Row order does not matter."
    ),
    requirements=[
        "Return exactly one column: the customer's name",
        "Include only customers whose tier is 'gold'",
        "Do not return a row for any other tier, and do not return NULL tiers",
    ],
    reference="SELECT name FROM customers WHERE tier = 'gold'",
    world="store",
    wrong=[
        # Returns everybody.
        "SELECT name FROM customers",
        # 'Gold' is not 'gold' — string comparison is case sensitive here.
        "SELECT name FROM customers WHERE tier = 'Gold'",
        # Two columns where one was asked for.
        "SELECT name, tier FROM customers WHERE tier = 'gold'",
    ],
)

_question(
    id="sql-basics-cities-distinct",
    title="Distinct Cities We Ship To",
    skill_id="sql_basics",
    concept="distinct",
    difficulty=2,
    minutes=12,
    summary="List each city that appears in the customer table exactly once, ignoring unknown cities.",
    statement=(
        "Return **one column**, `city`, listing every city that appears in "
        "`customers` — each city once, no duplicates. Customers whose `city` is "
        "NULL have no known city and must not produce a row. Row order does not "
        "matter."
    ),
    requirements=[
        "Return exactly one column of city names",
        "Return each city once — no duplicates",
        "Exclude customers whose city is NULL",
    ],
    reference="SELECT DISTINCT city FROM customers WHERE city IS NOT NULL",
    world="store",
    wrong=[
        # Duplicates: Leeds twice.
        "SELECT city FROM customers WHERE city IS NOT NULL",
        # `!= NULL` (and `<> NULL`) is never true, but DISTINCT still keeps the
        # NULL row out of… no: it removes nothing, so the NULL row is dropped by
        # the comparison and this looks right until you notice it returns
        # nothing at all on some data. Included because learners write it.
        "SELECT DISTINCT city FROM customers WHERE city <> NULL",
        # Keeps the NULL city.
        "SELECT DISTINCT city FROM customers",
    ],
)

_question(
    id="sql-basics-null-city",
    title="Customers With No City on File",
    skill_id="sql_basics",
    concept="null handling",
    difficulty=2,
    minutes=12,
    summary="Find the customers whose city is missing.",
    statement=(
        "Data quality wants the rows to chase up.\n\n"
        "Return **two columns**, `name` and `tier`, for every customer whose "
        "`city` is NULL. Row order does not matter."
    ),
    requirements=[
        "Return the customer's name and tier, in that column order",
        "Select rows where city is NULL using IS NULL, not an equality test",
        "Return no rows when every customer has a city",
    ],
    reference="SELECT name, tier FROM customers WHERE city IS NULL",
    world="store",
    wrong=[
        # `= NULL` is never true: this returns nothing.
        "SELECT name, tier FROM customers WHERE city = NULL",
        # The empty string is not NULL.
        "SELECT name, tier FROM customers WHERE city = ''",
        # Inverted filter.
        "SELECT name, tier FROM customers WHERE city IS NOT NULL",
    ],
)

_question(
    id="sql-basics-large-orders",
    title="Orders Over £100",
    skill_id="sql_basics",
    concept="where",
    difficulty=2,
    minutes=12,
    summary="List the paid orders worth more than £100.",
    statement=(
        "Return **two columns**, `product` and `amount`, for every order that is "
        "`paid` **and** has an `amount` strictly greater than 100. An order with "
        "a NULL amount has no known value and cannot qualify. Row order does not "
        "matter."
    ),
    requirements=[
        "Return the product and the amount, in that column order",
        "Include only orders with status 'paid'",
        "Include only amounts strictly greater than 100 — 100 itself does not qualify",
    ],
    reference="SELECT product, amount FROM orders WHERE status = 'paid' AND amount > 100",
    world="store",
    wrong=[
        # Forgets the status filter.
        "SELECT product, amount FROM orders WHERE amount > 100",
        # `>=` lets a boundary row in on data where one sits exactly at 100.
        "SELECT product, amount FROM orders WHERE status = 'paid' AND amount >= 100",
        # Drops the amount filter.
        "SELECT product, amount FROM orders WHERE status = 'paid'",
    ],
)

_question(
    id="sql-basics-order-by-amount",
    title="Three Biggest Paid Orders",
    skill_id="sql_basics",
    concept="order by",
    difficulty=3,
    minutes=15,
    summary="Return the three largest paid orders, biggest first, with the order id breaking ties.",
    statement=(
        "Return **two columns**, `product` and `amount`, for the three largest "
        "`paid` orders. Order by `amount` descending; where two orders tie on "
        "amount, the one with the **smaller order id** comes first. Return at "
        "most three rows."
    ),
    requirements=[
        "Include only paid orders",
        "Order by amount descending, then by order id ascending to break ties",
        "Return at most three rows",
        "Return the product and the amount, in that column order",
    ],
    reference=(
        "SELECT product, amount FROM orders WHERE status = 'paid' "
        "ORDER BY amount DESC, id ASC LIMIT 3"
    ),
    world="store",
    ordered=True,
    wrong=[
        # Ascending.
        "SELECT product, amount FROM orders WHERE status = 'paid' ORDER BY amount ASC LIMIT 3",
        # No limit.
        "SELECT product, amount FROM orders WHERE status = 'paid' ORDER BY amount DESC, id ASC",
        # Ignores status.
        "SELECT product, amount FROM orders ORDER BY amount DESC, id ASC LIMIT 3",
    ],
)

_question(
    id="sql-basics-accessories-in",
    title="Accessory and Furniture Orders in Q1",
    skill_id="sql_basics",
    concept="where",
    difficulty=3,
    minutes=15,
    summary="Filter orders by a date range and a status set.",
    statement=(
        "Return **three columns**, `id`, `product` and `placed_on`, for every "
        "order placed in the first quarter of 2024 — that is, `placed_on` "
        "between `2024-01-01` and `2024-03-31` inclusive — whose status is "
        "either `paid` or `pending`. Refunded orders are excluded. Row order "
        "does not matter."
    ),
    requirements=[
        "Return the order id, product and placed_on date, in that column order",
        "Include only orders placed between 2024-01-01 and 2024-03-31 inclusive",
        "Include orders with status 'paid' or 'pending', and exclude 'refunded'",
    ],
    reference=(
        "SELECT id, product, placed_on FROM orders "
        "WHERE placed_on BETWEEN '2024-01-01' AND '2024-03-31' "
        "AND status IN ('paid', 'pending')"
    ),
    world="store",
    wrong=[
        # Exclusive bounds drop the boundary rows.
        (
            "SELECT id, product, placed_on FROM orders "
            "WHERE placed_on > '2024-01-01' AND placed_on < '2024-03-31' "
            "AND status IN ('paid', 'pending')"
        ),
        # `status != 'refunded'` is the same set here, but the date window is
        # wrong: a whole year.
        (
            "SELECT id, product, placed_on FROM orders "
            "WHERE placed_on LIKE '2024%' AND status != 'refunded'"
        ),
        # AND/OR precedence: the status test only binds to the second date.
        (
            "SELECT id, product, placed_on FROM orders "
            "WHERE placed_on >= '2024-01-01' AND placed_on <= '2024-03-31' "
            "OR status = 'pending'"
        ),
    ],
)

_question(
    id="sql-basics-like-desk",
    title="Products With 'Desk' in the Name",
    skill_id="sql_basics",
    concept="select",
    difficulty=2,
    minutes=12,
    summary="Find the distinct products whose name contains the word desk.",
    statement=(
        "Return **one column**, `product`, listing each distinct product whose "
        "name contains the text `desk` (in any case — `Standing desk` and "
        "`Desk mat` both count). Each product name once. Row order does not "
        "matter."
    ),
    requirements=[
        "Return one column of distinct product names",
        "Match the substring 'desk' case-insensitively, anywhere in the name",
        "Return each matching product exactly once",
    ],
    reference="SELECT DISTINCT product FROM orders WHERE lower(product) LIKE '%desk%'",
    world="store",
    wrong=[
        # Anchored: only matches names that start with desk.
        "SELECT DISTINCT product FROM orders WHERE lower(product) LIKE 'desk%'",
        # Duplicates.
        "SELECT product FROM orders WHERE lower(product) LIKE '%desk%'",
        # Everything.
        "SELECT DISTINCT product FROM orders",
    ],
)

_question(
    id="sql-basics-line-total",
    title="Line Totals for Paid Orders",
    skill_id="sql_basics",
    concept="select",
    difficulty=3,
    minutes=15,
    summary="Compute a derived column: amount times quantity, aliased as line_total.",
    statement=(
        "Return **two columns**, `product` and `line_total`, for every `paid` "
        "order, where `line_total` is `amount * quantity`. Name the second "
        "column exactly `line_total`. Row order does not matter."
    ),
    requirements=[
        "Return the product and the computed total, in that column order",
        "line_total is amount multiplied by quantity",
        "Alias the computed column exactly 'line_total'",
        "Include only paid orders",
    ],
    reference=(
        "SELECT product, amount * quantity AS line_total FROM orders "
        "WHERE status = 'paid'"
    ),
    world="store",
    require_columns=True,
    wrong=[
        # Forgets the quantity.
        "SELECT product, amount AS line_total FROM orders WHERE status = 'paid'",
        # Right numbers, wrong column name — this question demands the alias.
        "SELECT product, amount * quantity FROM orders WHERE status = 'paid'",
        # Adds instead of multiplying.
        "SELECT product, amount + quantity AS line_total FROM orders WHERE status = 'paid'",
    ],
)

_question(
    id="sql-basics-case-band",
    title="Label Each Paid Order by Size",
    skill_id="sql_basics",
    concept="select",
    difficulty=4,
    minutes=18,
    summary="Use CASE to bucket paid orders into small, medium and large.",
    statement=(
        "Return **two columns**, `product` and `band`, for every `paid` order. "
        "`band` is:\n\n"
        "* `large` when `amount` is 300 or more,\n"
        "* `medium` when `amount` is 100 or more but less than 300,\n"
        "* `small` otherwise.\n\n"
        "Name the second column exactly `band`. Row order does not matter."
    ),
    requirements=[
        "Return the product and the band label, in that column order",
        "large is amount >= 300, medium is 100 <= amount < 300, small is the rest",
        "Alias the computed column exactly 'band'",
        "Include only paid orders",
    ],
    reference=(
        "SELECT product, CASE WHEN amount >= 300 THEN 'large' "
        "WHEN amount >= 100 THEN 'medium' ELSE 'small' END AS band "
        "FROM orders WHERE status = 'paid'"
    ),
    world="store",
    require_columns=True,
    wrong=[
        # Boundaries off by one class: 300 lands in medium.
        (
            "SELECT product, CASE WHEN amount > 300 THEN 'large' "
            "WHEN amount >= 100 THEN 'medium' ELSE 'small' END AS band "
            "FROM orders WHERE status = 'paid'"
        ),
        # Branch order wrong: everything >= 100 is labelled medium.
        (
            "SELECT product, CASE WHEN amount >= 100 THEN 'medium' "
            "WHEN amount >= 300 THEN 'large' ELSE 'small' END AS band "
            "FROM orders WHERE status = 'paid'"
        ),
        # Constant label.
        "SELECT product, 'medium' AS band FROM orders WHERE status = 'paid'",
    ],
)

_question(
    id="sql-basics-not-refunded",
    title="Every Order That Was Not Refunded",
    skill_id="sql_basics",
    concept="null handling",
    difficulty=3,
    minutes=15,
    summary="Exclude one status while keeping rows whose amount is unknown.",
    statement=(
        "Return **three columns**, `id`, `status` and `amount`, for every order "
        "whose status is **not** `refunded`. An order whose `amount` is NULL is "
        "still an order and must be returned, NULL amount and all. Row order "
        "does not matter."
    ),
    requirements=[
        "Return the order id, status and amount, in that column order",
        "Exclude only orders with status 'refunded'",
        "Keep orders whose amount is NULL — a missing amount is not a reason to drop the row",
    ],
    reference="SELECT id, status, amount FROM orders WHERE status <> 'refunded'",
    world="store",
    wrong=[
        # Silently drops the NULL-amount row.
        "SELECT id, status, amount FROM orders WHERE status <> 'refunded' AND amount > 0",
        # Keeps everything.
        "SELECT id, status, amount FROM orders",
        # Only paid: pending orders are missing.
        "SELECT id, status, amount FROM orders WHERE status = 'paid'",
    ],
)


# --------------------------------------------------------------------------- #
#  sql_joins                                                                  #
# --------------------------------------------------------------------------- #

_question(
    id="sql-joins-order-customer",
    title="Who Placed Each Paid Order",
    skill_id="sql_joins",
    concept="inner join",
    difficulty=3,
    minutes=15,
    summary="Join orders to customers and return the buyer's name with each paid order.",
    statement=(
        "Return **two columns**, the customer's `name` and the order's "
        "`product`, for every `paid` order. Row order does not matter."
    ),
    requirements=[
        "Join orders to customers on the customer id",
        "Return the customer name and the product, in that column order",
        "Include only paid orders",
    ],
    reference=(
        "SELECT c.name, o.product FROM orders o "
        "JOIN customers c ON c.id = o.customer_id WHERE o.status = 'paid'"
    ),
    world="store",
    wrong=[
        # No join condition: a cross product.
        "SELECT c.name, o.product FROM orders o, customers c WHERE o.status = 'paid'",
        # Joins on the wrong key.
        (
            "SELECT c.name, o.product FROM orders o "
            "JOIN customers c ON c.id = o.id WHERE o.status = 'paid'"
        ),
        # Drops the status filter.
        "SELECT c.name, o.product FROM orders o JOIN customers c ON c.id = o.customer_id",
    ],
)

_question(
    id="sql-joins-left-join-counts",
    title="Paid Order Count for Every Customer",
    skill_id="sql_joins",
    concept="left join",
    difficulty=5,
    minutes=25,
    summary="Every customer appears, including those with zero paid orders.",
    statement=(
        "Return **two columns**, `name` and `paid_orders`, with **one row per "
        "customer** — including customers who have never placed a paid order, "
        "who get `0`. Row order does not matter."
    ),
    requirements=[
        "Return one row for every customer, even one with no paid orders",
        "paid_orders counts that customer's orders with status 'paid'",
        "A customer with no paid orders must show 0, not NULL and not a missing row",
        "Put the status condition where it does not turn the outer join back into an inner one",
    ],
    reference=(
        "SELECT c.name AS name, COUNT(o.id) AS paid_orders FROM customers c "
        "LEFT JOIN orders o ON o.customer_id = c.id AND o.status = 'paid' "
        "GROUP BY c.id, c.name"
    ),
    world="store",
    secondary_skill_id="sql_aggregation",
    wrong=[
        # The classic: filtering the outer table in WHERE drops the zero rows.
        (
            "SELECT c.name AS name, COUNT(o.id) AS paid_orders FROM customers c "
            "LEFT JOIN orders o ON o.customer_id = c.id "
            "WHERE o.status = 'paid' GROUP BY c.id, c.name"
        ),
        # Inner join: customers with no orders vanish.
        (
            "SELECT c.name AS name, COUNT(o.id) AS paid_orders FROM customers c "
            "JOIN orders o ON o.customer_id = c.id AND o.status = 'paid' "
            "GROUP BY c.id, c.name"
        ),
        # COUNT(*) counts the padding row, so a customer with no orders gets 1.
        (
            "SELECT c.name AS name, COUNT(*) AS paid_orders FROM customers c "
            "LEFT JOIN orders o ON o.customer_id = c.id AND o.status = 'paid' "
            "GROUP BY c.id, c.name"
        ),
    ],
)

_question(
    id="sql-joins-never-ordered",
    title="Customers Who Never Ordered Anything",
    skill_id="sql_joins",
    concept="join keys",
    difficulty=4,
    minutes=20,
    summary="An anti-join: customers with no rows in orders at all.",
    statement=(
        "Return **one column**, `name`, for every customer who has no rows in "
        "`orders` whatsoever — regardless of status. Row order does not matter."
    ),
    requirements=[
        "Return one column of customer names",
        "Include a customer only when they have no orders at all",
        "Do not return duplicates",
    ],
    reference=(
        "SELECT c.name FROM customers c "
        "WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id)"
    ),
    world="store",
    wrong=[
        # Inverted: returns the customers who did order.
        (
            "SELECT c.name FROM customers c "
            "WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id)"
        ),
        # Counts unpaid orders as "never ordered".
        (
            "SELECT c.name FROM customers c "
            "WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id "
            "AND o.status = 'paid')"
        ),
        # Everybody.
        "SELECT name FROM customers",
    ],
)

_question(
    id="sql-joins-city-products",
    title="City and Product for Paid Orders",
    skill_id="sql_joins",
    concept="cardinality",
    difficulty=4,
    minutes=20,
    summary="Join and de-duplicate: which cities bought which products.",
    statement=(
        "Return **two columns**, `city` and `product`, listing each distinct "
        "(city, product) pair for which a `paid` order exists. A customer with "
        "no city on file cannot contribute a pair. Each pair once. Row order "
        "does not matter."
    ),
    requirements=[
        "Join paid orders to their customer",
        "Return distinct (city, product) pairs, in that column order",
        "Exclude orders whose customer has a NULL city",
    ],
    reference=(
        "SELECT DISTINCT c.city AS city, o.product AS product FROM orders o "
        "JOIN customers c ON c.id = o.customer_id "
        "WHERE o.status = 'paid' AND c.city IS NOT NULL"
    ),
    world="store",
    wrong=[
        # Duplicate pairs from repeat purchases.
        (
            "SELECT c.city AS city, o.product AS product FROM orders o "
            "JOIN customers c ON c.id = o.customer_id "
            "WHERE o.status = 'paid' AND c.city IS NOT NULL"
        ),
        # Keeps the NULL city pair.
        (
            "SELECT DISTINCT c.city AS city, o.product AS product FROM orders o "
            "JOIN customers c ON c.id = o.customer_id WHERE o.status = 'paid'"
        ),
        # Left join from customers invents rows with NULL products.
        (
            "SELECT DISTINCT c.city AS city, o.product AS product FROM customers c "
            "LEFT JOIN orders o ON o.customer_id = c.id "
            "WHERE c.city IS NOT NULL"
        ),
    ],
)

_question(
    id="sql-joins-rep-region",
    title="Every Rep and Their Region",
    skill_id="sql_joins",
    concept="left join",
    difficulty=4,
    minutes=20,
    summary="Keep the unassigned rep by joining outward from reps.",
    statement=(
        "Return **two columns**, the rep's `name` and their region's `name` "
        "aliased as `region`. A rep with no region (`region_id` is NULL) must "
        "still appear, with `region` NULL. Row order does not matter."
    ),
    requirements=[
        "Return one row per rep, including reps with no region",
        "Return the rep name then the region name, aliased 'region'",
        "A rep with no region shows NULL for region rather than being dropped",
    ],
    reference=(
        "SELECT r.name AS name, g.name AS region FROM reps r "
        "LEFT JOIN regions g ON g.id = r.region_id"
    ),
    world="sales",
    require_columns=True,
    wrong=[
        # Inner join drops the unassigned rep.
        "SELECT r.name AS name, g.name AS region FROM reps r JOIN regions g ON g.id = r.region_id",
        # Joined the wrong way round: regions with no reps appear instead.
        (
            "SELECT r.name AS name, g.name AS region FROM regions g "
            "LEFT JOIN reps r ON r.region_id = g.id"
        ),
        # Columns swapped.
        (
            "SELECT g.name AS name, r.name AS region FROM reps r "
            "LEFT JOIN regions g ON g.id = r.region_id"
        ),
    ],
)

_question(
    id="sql-joins-region-won-deals",
    title="Won Deals per Region, Three Tables Deep",
    skill_id="sql_joins",
    concept="inner join",
    difficulty=5,
    minutes=25,
    summary="Join deals to reps to regions and total the won amount per region.",
    statement=(
        "Return **two columns**, `region` and `booked`, where `booked` is the "
        "total `amount` of `won` deals closed by reps in that region. A region "
        "with no won deals must not appear, and a deal closed by a rep with no "
        "region contributes to no region. Row order does not matter."
    ),
    requirements=[
        "Join deals to reps, and reps to regions",
        "Count only deals with stage 'won'",
        "Group by region and sum the deal amounts",
        "Return no rows when nothing anywhere is won",
    ],
    reference=(
        "SELECT g.name AS region, SUM(d.amount) AS booked FROM deals d "
        "JOIN reps r ON r.id = d.rep_id JOIN regions g ON g.id = r.region_id "
        "WHERE d.stage = 'won' GROUP BY g.name"
    ),
    world="sales",
    secondary_skill_id="sql_aggregation",
    wrong=[
        # Counts open and lost deals as booked.
        (
            "SELECT g.name AS region, SUM(d.amount) AS booked FROM deals d "
            "JOIN reps r ON r.id = d.rep_id JOIN regions g ON g.id = r.region_id "
            "GROUP BY g.name"
        ),
        # Left join from regions invents a NULL row for a region with no reps.
        (
            "SELECT g.name AS region, SUM(d.amount) AS booked FROM regions g "
            "LEFT JOIN reps r ON r.region_id = g.id "
            "LEFT JOIN deals d ON d.rep_id = r.id AND d.stage = 'won' "
            "GROUP BY g.name"
        ),
        # Counts deals instead of summing them.
        (
            "SELECT g.name AS region, COUNT(*) AS booked FROM deals d "
            "JOIN reps r ON r.id = d.rep_id JOIN regions g ON g.id = r.region_id "
            "WHERE d.stage = 'won' GROUP BY g.name"
        ),
    ],
)

_question(
    id="sql-joins-fanout-guard",
    title="Customer Revenue Without Double Counting",
    skill_id="sql_joins",
    concept="fan-out",
    difficulty=6,
    minutes=28,
    summary="One row per customer with their paid revenue — the join must not multiply rows.",
    statement=(
        "Return **two columns**, `name` and `revenue`, with exactly one row per "
        "customer who has at least one `paid` order. `revenue` is the sum of "
        "`amount * quantity` over that customer's paid orders. Two customers "
        "can share a name in general, so group by the customer's id rather than "
        "their name. Row order does not matter."
    ),
    requirements=[
        "Return the customer name and their revenue, in that column order",
        "revenue sums amount * quantity over the customer's paid orders",
        "Return exactly one row per qualifying customer — no duplicated rows",
        "Customers with no paid orders do not appear",
    ],
    reference=(
        "SELECT c.name AS name, SUM(o.amount * o.quantity) AS revenue "
        "FROM customers c JOIN orders o ON o.customer_id = c.id "
        "WHERE o.status = 'paid' GROUP BY c.id, c.name"
    ),
    world="store",
    secondary_skill_id="sql_aggregation",
    wrong=[
        # No grouping at all: one row per order.
        (
            "SELECT c.name AS name, o.amount * o.quantity AS revenue "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "WHERE o.status = 'paid'"
        ),
        # Ignores quantity.
        (
            "SELECT c.name AS name, SUM(o.amount) AS revenue "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "WHERE o.status = 'paid' GROUP BY c.id, c.name"
        ),
        # Left join adds a NULL-revenue row for customers with nothing paid.
        (
            "SELECT c.name AS name, SUM(o.amount * o.quantity) AS revenue "
            "FROM customers c LEFT JOIN orders o ON o.customer_id = c.id "
            "AND o.status = 'paid' GROUP BY c.id, c.name"
        ),
    ],
)

_question(
    id="sql-joins-repeat-product-buyers",
    title="Customers Who Bought the Same Product Twice",
    skill_id="sql_joins",
    concept="join keys",
    difficulty=6,
    minutes=28,
    summary="A self-join (or a grouped count) over paid orders of the same product.",
    statement=(
        "Return **two columns**, `name` and `product`, for every "
        "(customer, product) pair where that customer has **two or more** "
        "`paid` orders of that product. Each pair once. Row order does not "
        "matter."
    ),
    requirements=[
        "Consider only paid orders",
        "Return the customer name and the product, in that column order",
        "Include a pair only when the customer has at least two paid orders of that product",
        "Return each pair exactly once, however many repeats there were",
    ],
    reference=(
        "SELECT c.name AS name, o.product AS product FROM orders o "
        "JOIN customers c ON c.id = o.customer_id WHERE o.status = 'paid' "
        "GROUP BY c.id, c.name, o.product HAVING COUNT(*) >= 2"
    ),
    world="store",
    secondary_skill_id="sql_aggregation",
    wrong=[
        # `> 2` needs three orders.
        (
            "SELECT c.name AS name, o.product AS product FROM orders o "
            "JOIN customers c ON c.id = o.customer_id WHERE o.status = 'paid' "
            "GROUP BY c.id, c.name, o.product HAVING COUNT(*) > 2"
        ),
        # Every pair, repeat or not.
        (
            "SELECT DISTINCT c.name AS name, o.product AS product FROM orders o "
            "JOIN customers c ON c.id = o.customer_id WHERE o.status = 'paid'"
        ),
        # A self-join without the id guard pairs a row with itself.
        (
            "SELECT DISTINCT c.name AS name, a.product AS product FROM orders a "
            "JOIN orders b ON b.customer_id = a.customer_id AND b.product = a.product "
            "JOIN customers c ON c.id = a.customer_id "
            "WHERE a.status = 'paid' AND b.status = 'paid'"
        ),
    ],
)

_question(
    id="sql-joins-tier-category-matrix",
    title="Which Tiers Buy Which Categories",
    skill_id="sql_joins",
    concept="inner join",
    difficulty=5,
    minutes=24,
    summary="Count paid orders per (tier, category), treating an unknown tier as its own bucket.",
    statement=(
        "Return **three columns**, `tier`, `category` and `orders`, counting "
        "`paid` orders per customer tier and product category. A customer whose "
        "`tier` is NULL must be reported under the literal tier "
        "`unknown`. Row order does not matter."
    ),
    requirements=[
        "Join paid orders to their customer",
        "Group by tier and category and count the orders",
        "Report a NULL tier as the string 'unknown' rather than dropping the rows",
        "Return the tier, category and count, in that column order",
    ],
    reference=(
        "SELECT COALESCE(c.tier, 'unknown') AS tier, o.category AS category, "
        "COUNT(*) AS orders FROM orders o JOIN customers c ON c.id = o.customer_id "
        "WHERE o.status = 'paid' GROUP BY COALESCE(c.tier, 'unknown'), o.category"
    ),
    world="store",
    secondary_skill_id="sql_aggregation",
    wrong=[
        # Leaves the NULL tier as NULL.
        (
            "SELECT c.tier AS tier, o.category AS category, COUNT(*) AS orders "
            "FROM orders o JOIN customers c ON c.id = o.customer_id "
            "WHERE o.status = 'paid' GROUP BY c.tier, o.category"
        ),
        # Drops the NULL-tier rows entirely.
        (
            "SELECT c.tier AS tier, o.category AS category, COUNT(*) AS orders "
            "FROM orders o JOIN customers c ON c.id = o.customer_id "
            "WHERE o.status = 'paid' AND c.tier IS NOT NULL "
            "GROUP BY c.tier, o.category"
        ),
        # Counts every status.
        (
            "SELECT COALESCE(c.tier, 'unknown') AS tier, o.category AS category, "
            "COUNT(*) AS orders FROM orders o JOIN customers c ON c.id = o.customer_id "
            "GROUP BY COALESCE(c.tier, 'unknown'), o.category"
        ),
    ],
)

_question(
    id="sql-joins-reps-without-won-deals",
    title="Reps With No Won Deal",
    skill_id="sql_joins",
    concept="left join",
    difficulty=5,
    minutes=24,
    summary="Find reps who have never closed a won deal, including reps with no deals at all.",
    statement=(
        "Return **one column**, `name`, for every rep who has not closed a "
        "single `won` deal. A rep with no deals at all qualifies. Row order "
        "does not matter."
    ),
    requirements=[
        "Return one column of rep names",
        "Include reps who have deals but none of them won",
        "Include reps who have no deals at all",
        "Exclude every rep with at least one won deal",
    ],
    reference=(
        "SELECT r.name FROM reps r WHERE NOT EXISTS "
        "(SELECT 1 FROM deals d WHERE d.rep_id = r.id AND d.stage = 'won')"
    ),
    world="sales",
    wrong=[
        # "has a non-won deal" is not "has no won deal".
        (
            "SELECT DISTINCT r.name FROM reps r JOIN deals d ON d.rep_id = r.id "
            "WHERE d.stage <> 'won'"
        ),
        # Misses reps with no deals at all.
        (
            "SELECT r.name FROM reps r JOIN deals d ON d.rep_id = r.id "
            "GROUP BY r.id, r.name HAVING SUM(CASE WHEN d.stage = 'won' THEN 1 ELSE 0 END) = 0"
        ),
        # Inverted.
        (
            "SELECT r.name FROM reps r WHERE EXISTS "
            "(SELECT 1 FROM deals d WHERE d.rep_id = r.id AND d.stage = 'won')"
        ),
    ],
)


# --------------------------------------------------------------------------- #
#  sql_aggregation                                                            #
# --------------------------------------------------------------------------- #

_question(
    id="sql-agg-orders-per-status",
    title="How Many Orders in Each Status",
    skill_id="sql_aggregation",
    concept="count",
    difficulty=2,
    minutes=12,
    summary="Count the orders in each status.",
    statement=(
        "Return **two columns**, `status` and `orders`, counting the rows in "
        "`orders` for each distinct status. A status with no orders simply does "
        "not appear. Row order does not matter."
    ),
    requirements=[
        "Return the status and the row count, in that column order",
        "Group by status",
        "Count rows, not amounts — a NULL amount is still an order",
    ],
    reference="SELECT status, COUNT(*) AS orders FROM orders GROUP BY status",
    world="store",
    wrong=[
        # COUNT(amount) skips the NULL-amount row.
        "SELECT status, COUNT(amount) AS orders FROM orders GROUP BY status",
        # One row for the whole table.
        "SELECT status, COUNT(*) AS orders FROM orders",
        # Distinct products is not a row count.
        "SELECT status, COUNT(DISTINCT product) AS orders FROM orders GROUP BY status",
    ],
)

_question(
    id="sql-agg-revenue-per-category",
    title="Paid Revenue by Category",
    skill_id="sql_aggregation",
    concept="sum",
    difficulty=3,
    minutes=18,
    summary="Total the paid revenue for each product category.",
    statement=(
        "Return **two columns**, `category` and `revenue`, where `revenue` is "
        "the sum of `amount * quantity` over that category's `paid` orders. A "
        "category with no paid orders must not appear; if nothing is paid the "
        "answer is zero rows. Row order does not matter."
    ),
    requirements=[
        "Include only paid orders",
        "revenue sums amount * quantity, not amount alone",
        "Group by category",
        "Return no rows when nothing is paid, rather than one NULL row",
    ],
    reference=(
        "SELECT category, SUM(amount * quantity) AS revenue FROM orders "
        "WHERE status = 'paid' GROUP BY category"
    ),
    world="store",
    wrong=[
        # No GROUP BY: one NULL row survives the empty case.
        "SELECT category, SUM(amount * quantity) AS revenue FROM orders WHERE status = 'paid'",
        # Ignores quantity.
        (
            "SELECT category, SUM(amount) AS revenue FROM orders "
            "WHERE status = 'paid' GROUP BY category"
        ),
        # Includes refunds and pending orders.
        "SELECT category, SUM(amount * quantity) AS revenue FROM orders GROUP BY category",
    ],
)

_question(
    id="sql-agg-average-order-value",
    title="Average Paid Order Value per City",
    skill_id="sql_aggregation",
    concept="average",
    difficulty=4,
    minutes=20,
    summary="Average amount of paid orders per city, rounded to two decimals.",
    statement=(
        "Return **two columns**, `city` and `avg_amount`, where `avg_amount` is "
        "the average `amount` of that city's `paid` orders, rounded to two "
        "decimal places. Customers with no city do not form a city. Row order "
        "does not matter."
    ),
    requirements=[
        "Include only paid orders whose customer has a city",
        "Average the amount per city and round to two decimal places",
        "Return the city and the rounded average, in that column order",
        "Return no rows when no paid order has a city",
    ],
    reference=(
        "SELECT c.city AS city, ROUND(AVG(o.amount), 2) AS avg_amount "
        "FROM orders o JOIN customers c ON c.id = o.customer_id "
        "WHERE o.status = 'paid' AND c.city IS NOT NULL GROUP BY c.city"
    ),
    world="store",
    secondary_skill_id="sql_joins",
    wrong=[
        # SUM is not AVG.
        (
            "SELECT c.city AS city, ROUND(SUM(o.amount), 2) AS avg_amount "
            "FROM orders o JOIN customers c ON c.id = o.customer_id "
            "WHERE o.status = 'paid' AND c.city IS NOT NULL GROUP BY c.city"
        ),
        # Averages every status.
        (
            "SELECT c.city AS city, ROUND(AVG(o.amount), 2) AS avg_amount "
            "FROM orders o JOIN customers c ON c.id = o.customer_id "
            "WHERE c.city IS NOT NULL GROUP BY c.city"
        ),
        # Keeps the NULL city as a group.
        (
            "SELECT c.city AS city, ROUND(AVG(o.amount), 2) AS avg_amount "
            "FROM orders o JOIN customers c ON c.id = o.customer_id "
            "WHERE o.status = 'paid' GROUP BY c.city"
        ),
    ],
)

_question(
    id="sql-agg-having-big-spenders",
    title="Customers Who Spent More Than £300",
    skill_id="sql_aggregation",
    concept="having",
    difficulty=5,
    minutes=22,
    summary="Filter groups, not rows: total paid spend above a threshold.",
    statement=(
        "Return **two columns**, `name` and `spend`, for every customer whose "
        "total `paid` spend — the sum of `amount * quantity` — is strictly "
        "greater than 300. Row order does not matter."
    ),
    requirements=[
        "Sum amount * quantity over each customer's paid orders",
        "Keep only customers whose total is strictly greater than 300",
        "Filter on the group total with HAVING, not on individual rows",
        "Return the customer name and their total, in that column order",
    ],
    reference=(
        "SELECT c.name AS name, SUM(o.amount * o.quantity) AS spend "
        "FROM customers c JOIN orders o ON o.customer_id = c.id "
        "WHERE o.status = 'paid' GROUP BY c.id, c.name "
        "HAVING SUM(o.amount * o.quantity) > 300"
    ),
    world="store",
    secondary_skill_id="sql_joins",
    wrong=[
        # Filters rows instead of groups: keeps only big single orders.
        (
            "SELECT c.name AS name, SUM(o.amount * o.quantity) AS spend "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "WHERE o.status = 'paid' AND o.amount * o.quantity > 300 "
            "GROUP BY c.id, c.name"
        ),
        # No threshold at all.
        (
            "SELECT c.name AS name, SUM(o.amount * o.quantity) AS spend "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "WHERE o.status = 'paid' GROUP BY c.id, c.name"
        ),
        # `>= 300` includes a customer sitting exactly on the boundary.
        (
            "SELECT c.name AS name, SUM(o.amount * o.quantity) AS spend "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "WHERE o.status = 'paid' GROUP BY c.id, c.name "
            "HAVING SUM(o.amount * o.quantity) >= 300"
        ),
    ],
)

_question(
    id="sql-agg-distinct-products-per-customer",
    title="How Many Different Products Each Customer Bought",
    skill_id="sql_aggregation",
    concept="count",
    difficulty=4,
    minutes=20,
    summary="COUNT(DISTINCT ...) — repeat purchases of one product count once.",
    statement=(
        "Return **two columns**, `name` and `products`, where `products` is the "
        "number of **different** products that customer has bought in `paid` "
        "orders. Customers with no paid orders do not appear. Row order does "
        "not matter."
    ),
    requirements=[
        "Include only paid orders",
        "Count distinct products per customer, so three orders of one product count as one",
        "Return one row per customer with at least one paid order",
        "Return the customer name and the count, in that column order",
    ],
    reference=(
        "SELECT c.name AS name, COUNT(DISTINCT o.product) AS products "
        "FROM customers c JOIN orders o ON o.customer_id = c.id "
        "WHERE o.status = 'paid' GROUP BY c.id, c.name"
    ),
    world="store",
    secondary_skill_id="sql_joins",
    wrong=[
        # Counts orders, not products.
        (
            "SELECT c.name AS name, COUNT(o.product) AS products "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "WHERE o.status = 'paid' GROUP BY c.id, c.name"
        ),
        # Includes refunded and pending orders.
        (
            "SELECT c.name AS name, COUNT(DISTINCT o.product) AS products "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "GROUP BY c.id, c.name"
        ),
        # Left join adds a zero row for customers with nothing paid.
        (
            "SELECT c.name AS name, COUNT(DISTINCT o.product) AS products "
            "FROM customers c LEFT JOIN orders o ON o.customer_id = c.id "
            "AND o.status = 'paid' GROUP BY c.id, c.name"
        ),
    ],
)

_question(
    id="sql-agg-min-max-window-per-category",
    title="Cheapest and Priciest Paid Order per Category",
    skill_id="sql_aggregation",
    concept="group by",
    difficulty=4,
    minutes=20,
    summary="MIN and MAX side by side, grouped by category.",
    statement=(
        "Return **three columns**, `category`, `cheapest` and `priciest`, being "
        "the smallest and largest `amount` among that category's `paid` orders. "
        "Row order does not matter."
    ),
    requirements=[
        "Include only paid orders",
        "Group by category",
        "Return the category, then the minimum amount, then the maximum amount",
        "Return no rows when nothing is paid",
    ],
    reference=(
        "SELECT category, MIN(amount) AS cheapest, MAX(amount) AS priciest "
        "FROM orders WHERE status = 'paid' GROUP BY category"
    ),
    world="store",
    require_columns=True,
    wrong=[
        # Swapped.
        (
            "SELECT category, MAX(amount) AS cheapest, MIN(amount) AS priciest "
            "FROM orders WHERE status = 'paid' GROUP BY category"
        ),
        # Whole-table extremes repeated per category.
        (
            "SELECT category, (SELECT MIN(amount) FROM orders WHERE status = 'paid') AS cheapest, "
            "(SELECT MAX(amount) FROM orders WHERE status = 'paid') AS priciest "
            "FROM orders WHERE status = 'paid' GROUP BY category"
        ),
        # Ignores status.
        (
            "SELECT category, MIN(amount) AS cheapest, MAX(amount) AS priciest "
            "FROM orders GROUP BY category"
        ),
    ],
)

_question(
    id="sql-agg-monthly-orders",
    title="Paid Orders per Month",
    skill_id="sql_aggregation",
    concept="group by",
    difficulty=4,
    minutes=20,
    summary="Group by the year-month prefix of the order date.",
    statement=(
        "Return **two columns**, `month` and `orders`, counting `paid` orders "
        "per calendar month, where `month` is the `YYYY-MM` prefix of "
        "`placed_on`. Row order does not matter."
    ),
    requirements=[
        "Derive the month as the first seven characters of placed_on",
        "Count paid orders per month",
        "Alias the columns exactly 'month' and 'orders'",
        "Do not count refunded or pending orders",
    ],
    reference=(
        "SELECT substr(placed_on, 1, 7) AS month, COUNT(*) AS orders FROM orders "
        "WHERE status = 'paid' GROUP BY substr(placed_on, 1, 7)"
    ),
    world="store",
    require_columns=True,
    wrong=[
        # Groups by the full date, so each day is its own "month".
        (
            "SELECT placed_on AS month, COUNT(*) AS orders FROM orders "
            "WHERE status = 'paid' GROUP BY placed_on"
        ),
        # Groups by year.
        (
            "SELECT substr(placed_on, 1, 4) AS month, COUNT(*) AS orders FROM orders "
            "WHERE status = 'paid' GROUP BY substr(placed_on, 1, 4)"
        ),
        # Counts every status.
        (
            "SELECT substr(placed_on, 1, 7) AS month, COUNT(*) AS orders FROM orders "
            "GROUP BY substr(placed_on, 1, 7)"
        ),
    ],
)

_question(
    id="sql-agg-refund-rate",
    title="Refund Rate per Customer",
    skill_id="sql_aggregation",
    concept="average",
    difficulty=6,
    minutes=28,
    summary="A conditional count over a total count, rounded — the shape of every rate metric.",
    statement=(
        "Return **two columns**, `name` and `refund_rate`, where `refund_rate` "
        "is the share of that customer's orders that are `refunded`, as a "
        "fraction between 0 and 1 rounded to three decimal places. Every "
        "customer with at least one order appears, including those whose rate "
        "is 0. Row order does not matter."
    ),
    requirements=[
        "Consider all of a customer's orders as the denominator, whatever the status",
        "The numerator is that customer's refunded orders",
        "Round the fraction to three decimal places",
        "Include customers whose rate is 0, and exclude customers with no orders",
    ],
    reference=(
        "SELECT c.name AS name, ROUND(SUM(CASE WHEN o.status = 'refunded' THEN 1 ELSE 0 END) "
        "* 1.0 / COUNT(*), 3) AS refund_rate "
        "FROM customers c JOIN orders o ON o.customer_id = c.id "
        "GROUP BY c.id, c.name"
    ),
    world="store",
    secondary_skill_id="sql_joins",
    wrong=[
        # Integer division: every rate collapses to 0.
        (
            "SELECT c.name AS name, ROUND(SUM(CASE WHEN o.status = 'refunded' THEN 1 ELSE 0 END) "
            "/ COUNT(*), 3) AS refund_rate "
            "FROM customers c JOIN orders o ON o.customer_id = c.id GROUP BY c.id, c.name"
        ),
        # Filtering to refunds first makes every surviving rate 1.0 and drops
        # the customers whose rate is 0.
        (
            "SELECT c.name AS name, ROUND(COUNT(*) * 1.0 / COUNT(*), 3) AS refund_rate "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "WHERE o.status = 'refunded' GROUP BY c.id, c.name"
        ),
        # Counts refunds instead of rating them.
        (
            "SELECT c.name AS name, SUM(CASE WHEN o.status = 'refunded' THEN 1 ELSE 0 END) "
            "AS refund_rate FROM customers c JOIN orders o ON o.customer_id = c.id "
            "GROUP BY c.id, c.name"
        ),
    ],
)

_question(
    id="sql-agg-category-share",
    title="Each Category's Share of Paid Revenue",
    skill_id="sql_aggregation",
    concept="sum",
    difficulty=6,
    minutes=28,
    summary="A group total divided by the overall total, as a percentage.",
    statement=(
        "Return **two columns**, `category` and `share_pct`, where `share_pct` "
        "is that category's `paid` revenue (`amount * quantity`) as a "
        "percentage of the total paid revenue across all categories, rounded to "
        "one decimal place. Row order does not matter."
    ),
    requirements=[
        "Include only paid orders",
        "The denominator is total paid revenue across every category, not the category's own",
        "Express the share as a percentage rounded to one decimal place",
        "Return no rows when nothing is paid",
    ],
    reference=(
        "SELECT category, ROUND(SUM(amount * quantity) * 100.0 / "
        "(SELECT SUM(amount * quantity) FROM orders WHERE status = 'paid'), 1) AS share_pct "
        "FROM orders WHERE status = 'paid' GROUP BY category"
    ),
    world="store",
    require_columns=True,
    wrong=[
        # Denominator includes refunds and pending orders.
        (
            "SELECT category, ROUND(SUM(amount * quantity) * 100.0 / "
            "(SELECT SUM(amount * quantity) FROM orders), 1) AS share_pct "
            "FROM orders WHERE status = 'paid' GROUP BY category"
        ),
        # Every category is 100% of itself.
        (
            "SELECT category, ROUND(SUM(amount * quantity) * 100.0 / "
            "SUM(amount * quantity), 1) AS share_pct "
            "FROM orders WHERE status = 'paid' GROUP BY category"
        ),
        # Fraction, not percentage.
        (
            "SELECT category, ROUND(SUM(amount * quantity) * 1.0 / "
            "(SELECT SUM(amount * quantity) FROM orders WHERE status = 'paid'), 1) AS share_pct "
            "FROM orders WHERE status = 'paid' GROUP BY category"
        ),
    ],
)

_question(
    id="sql-agg-won-deal-stats",
    title="Won Deal Count and Average per Product",
    skill_id="sql_aggregation",
    concept="group by",
    difficulty=5,
    minutes=24,
    summary="Two aggregates in one grouped query over the pipeline.",
    statement=(
        "Return **three columns**, `product`, `deals` and `avg_amount`, over "
        "`won` deals only: how many were won per product and their average "
        "`amount` rounded to two decimal places. Row order does not matter."
    ),
    requirements=[
        "Include only deals with stage 'won'",
        "Group by product",
        "Return the product, the count of won deals, and the rounded average amount",
        "Return no rows when nothing is won",
    ],
    reference=(
        "SELECT product, COUNT(*) AS deals, ROUND(AVG(amount), 2) AS avg_amount "
        "FROM deals WHERE stage = 'won' GROUP BY product"
    ),
    world="sales",
    require_columns=True,
    wrong=[
        # Includes open and lost.
        (
            "SELECT product, COUNT(*) AS deals, ROUND(AVG(amount), 2) AS avg_amount "
            "FROM deals GROUP BY product"
        ),
        # Sum masquerading as an average.
        (
            "SELECT product, COUNT(*) AS deals, ROUND(SUM(amount), 2) AS avg_amount "
            "FROM deals WHERE stage = 'won' GROUP BY product"
        ),
        # Counts distinct reps rather than deals.
        (
            "SELECT product, COUNT(DISTINCT rep_id) AS deals, ROUND(AVG(amount), 2) AS avg_amount "
            "FROM deals WHERE stage = 'won' GROUP BY product"
        ),
    ],
)


# --------------------------------------------------------------------------- #
#  sql_analytics — CTEs, subqueries, window functions                         #
# --------------------------------------------------------------------------- #

_question(
    id="sql-analytics-above-average-orders",
    title="Paid Orders Above the Average",
    skill_id="sql_analytics",
    concept="subquery",
    difficulty=4,
    minutes=20,
    summary="Compare each row against an aggregate of the whole table.",
    statement=(
        "Return **two columns**, `id` and `amount`, for every `paid` order "
        "whose `amount` is strictly greater than the average amount of all "
        "`paid` orders. Row order does not matter."
    ),
    requirements=[
        "Compute the average over paid orders only",
        "Return paid orders strictly above that average",
        "Return the order id and its amount, in that column order",
        "Return no rows when nothing is paid",
    ],
    reference=(
        "SELECT id, amount FROM orders WHERE status = 'paid' AND amount > "
        "(SELECT AVG(amount) FROM orders WHERE status = 'paid')"
    ),
    world="store",
    wrong=[
        # Right threshold, wrong population: a pending order above the average
        # is not a paid order above the average.
        (
            "SELECT id, amount FROM orders WHERE amount > "
            "(SELECT AVG(amount) FROM orders WHERE status = 'paid')"
        ),
        # `>=` changes nothing on most data but flips a dataset where an order
        # sits exactly on the mean… and more importantly this one compares to
        # the *minimum*.
        (
            "SELECT id, amount FROM orders WHERE status = 'paid' AND amount > "
            "(SELECT MIN(amount) FROM orders WHERE status = 'paid')"
        ),
        # No comparison at all.
        "SELECT id, amount FROM orders WHERE status = 'paid'",
    ],
)

_question(
    id="sql-analytics-cte-city-leaders",
    title="Cities Beating the Average City",
    skill_id="sql_analytics",
    concept="cte",
    difficulty=6,
    minutes=28,
    summary="Aggregate in a CTE, then filter the aggregate against its own average.",
    statement=(
        "Return **two columns**, `city` and `revenue`, for every city whose "
        "total `paid` revenue (`amount * quantity`) is strictly greater than "
        "the average city's total paid revenue. Customers with no city do not "
        "form a city. Row order does not matter."
    ),
    requirements=[
        "Total paid revenue per city first, then compare against the average of those totals",
        "The comparison is against the mean of the per-city totals, not the mean order value",
        "Exclude customers with no city",
        "Return the city and its revenue, in that column order",
    ],
    reference=(
        "WITH city_revenue AS ("
        "  SELECT c.city AS city, SUM(o.amount * o.quantity) AS revenue "
        "  FROM customers c JOIN orders o ON o.customer_id = c.id "
        "  WHERE o.status = 'paid' AND c.city IS NOT NULL GROUP BY c.city"
        ") SELECT city, revenue FROM city_revenue "
        "WHERE revenue > (SELECT AVG(revenue) FROM city_revenue)"
    ),
    world="store",
    wrong=[
        # Compares a city total against the mean *order* value.
        (
            "SELECT c.city AS city, SUM(o.amount * o.quantity) AS revenue "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "WHERE o.status = 'paid' AND c.city IS NOT NULL GROUP BY c.city "
            "HAVING SUM(o.amount * o.quantity) > (SELECT AVG(amount * quantity) "
            "FROM orders WHERE status = 'paid')"
        ),
        # Every city.
        (
            "SELECT c.city AS city, SUM(o.amount * o.quantity) AS revenue "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "WHERE o.status = 'paid' AND c.city IS NOT NULL GROUP BY c.city"
        ),
        # Below the average instead of above it.
        (
            "WITH city_revenue AS ("
            "  SELECT c.city AS city, SUM(o.amount * o.quantity) AS revenue "
            "  FROM customers c JOIN orders o ON o.customer_id = c.id "
            "  WHERE o.status = 'paid' AND c.city IS NOT NULL GROUP BY c.city"
            ") SELECT city, revenue FROM city_revenue "
            "WHERE revenue < (SELECT AVG(revenue) FROM city_revenue)"
        ),
    ],
)

_question(
    id="sql-analytics-top-rep-per-region",
    title="Top Rep in Each Region",
    skill_id="sql_analytics",
    concept="ranking",
    difficulty=7,
    minutes=32,
    summary="One row per region: the rep with the highest booked revenue, name breaking ties.",
    statement=(
        "Return **three columns**, `region`, `rep` and `booked`, giving for each "
        "region the rep with the highest total `won` amount. Where two reps in "
        "a region tie, the one whose name sorts first alphabetically wins. Only "
        "reps with at least one won deal are candidates, and a region with no "
        "won deals does not appear. Row order does not matter."
    ),
    requirements=[
        "Total won amounts per rep within their region",
        "Return exactly one row per region that has any won deal",
        "Break a tie on booked revenue by the rep name, ascending",
        "Return the region, the rep name and the booked total, in that column order",
    ],
    reference=(
        "WITH rep_totals AS ("
        "  SELECT g.name AS region, r.name AS rep, SUM(d.amount) AS booked "
        "  FROM deals d JOIN reps r ON r.id = d.rep_id "
        "  JOIN regions g ON g.id = r.region_id "
        "  WHERE d.stage = 'won' GROUP BY g.name, r.name"
        "), ranked AS ("
        "  SELECT region, rep, booked, ROW_NUMBER() OVER ("
        "    PARTITION BY region ORDER BY booked DESC, rep ASC) AS rn "
        "  FROM rep_totals"
        ") SELECT region, rep, booked FROM ranked WHERE rn = 1"
    ),
    world="sales",
    secondary_skill_id="sql_aggregation",
    wrong=[
        # MAX of the total without carrying the matching rep name.
        (
            "SELECT g.name AS region, r.name AS rep, SUM(d.amount) AS booked "
            "FROM deals d JOIN reps r ON r.id = d.rep_id "
            "JOIN regions g ON g.id = r.region_id WHERE d.stage = 'won' "
            "GROUP BY g.name"
        ),
        # Every rep, not the top one.
        (
            "SELECT g.name AS region, r.name AS rep, SUM(d.amount) AS booked "
            "FROM deals d JOIN reps r ON r.id = d.rep_id "
            "JOIN regions g ON g.id = r.region_id WHERE d.stage = 'won' "
            "GROUP BY g.name, r.name"
        ),
        # Global top rep, not per region.
        (
            "WITH rep_totals AS ("
            "  SELECT g.name AS region, r.name AS rep, SUM(d.amount) AS booked "
            "  FROM deals d JOIN reps r ON r.id = d.rep_id "
            "  JOIN regions g ON g.id = r.region_id "
            "  WHERE d.stage = 'won' GROUP BY g.name, r.name"
            ") SELECT region, rep, booked FROM rep_totals "
            "ORDER BY booked DESC, rep ASC LIMIT 1"
        ),
    ],
)

_question(
    id="sql-analytics-running-total",
    title="Running Total of Booked Revenue",
    skill_id="sql_analytics",
    concept="running total",
    difficulty=7,
    minutes=32,
    summary="A cumulative sum of won deals ordered by close date.",
    statement=(
        "Return **three columns**, `closed_on`, `amount` and `running_total`, "
        "one row per `won` deal, where `running_total` is the cumulative sum of "
        "`amount` over the won deals up to and including that one, ordered by "
        "`closed_on` and then by deal `id`. Return the rows in that same order."
    ),
    requirements=[
        "Include only won deals",
        "Order by closed_on ascending, then by deal id ascending",
        "running_total is the cumulative amount up to and including the current row",
        "Return closed_on, amount and running_total, in that column order",
    ],
    reference=(
        "SELECT closed_on, amount, SUM(amount) OVER ("
        "ORDER BY closed_on, id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW"
        ") AS running_total FROM deals WHERE stage = 'won' ORDER BY closed_on, id"
    ),
    world="sales",
    ordered=True,
    require_columns=True,
    wrong=[
        # Grand total on every row.
        (
            "SELECT closed_on, amount, (SELECT SUM(amount) FROM deals WHERE stage = 'won') "
            "AS running_total FROM deals WHERE stage = 'won' ORDER BY closed_on, id"
        ),
        # No window ordering: the frame covers the whole partition.
        (
            "SELECT closed_on, amount, SUM(amount) OVER () AS running_total "
            "FROM deals WHERE stage = 'won' ORDER BY closed_on, id"
        ),
        # Includes lost and open deals in the cumulative sum.
        (
            "SELECT closed_on, amount, SUM(amount) OVER ("
            "ORDER BY closed_on, id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW"
            ") AS running_total FROM deals ORDER BY closed_on, id"
        ),
    ],
)

_question(
    id="sql-analytics-month-over-month",
    title="Month-over-Month Change in Bookings",
    skill_id="sql_analytics",
    concept="window function",
    difficulty=8,
    minutes=35,
    summary="LAG over monthly totals: the change against the previous month present in the data.",
    statement=(
        "Return **three columns**, `month`, `booked` and `change`, one row per "
        "month in which at least one deal was `won`. `month` is the `YYYY-MM` "
        "prefix of `closed_on`, `booked` is that month's won total, and `change` "
        "is `booked` minus the previous month's `booked` — the previous month "
        "**present in the result**, not the previous calendar month. The first "
        "month has no previous month, so its `change` is NULL. Return the rows "
        "ordered by `month` ascending."
    ),
    requirements=[
        "Total won amounts per YYYY-MM month",
        "change is this month's total minus the previous present month's total",
        "The earliest month's change is NULL rather than 0",
        "Return the rows ordered by month ascending",
    ],
    reference=(
        "WITH monthly AS ("
        "  SELECT substr(closed_on, 1, 7) AS month, SUM(amount) AS booked "
        "  FROM deals WHERE stage = 'won' GROUP BY substr(closed_on, 1, 7)"
        ") SELECT month, booked, booked - LAG(booked) OVER (ORDER BY month) AS change "
        "FROM monthly ORDER BY month"
    ),
    world="sales",
    ordered=True,
    require_columns=True,
    wrong=[
        # Zero instead of NULL for the first month.
        (
            "WITH monthly AS ("
            "  SELECT substr(closed_on, 1, 7) AS month, SUM(amount) AS booked "
            "  FROM deals WHERE stage = 'won' GROUP BY substr(closed_on, 1, 7)"
            ") SELECT month, booked, booked - COALESCE(LAG(booked) OVER (ORDER BY month), 0) "
            "AS change FROM monthly ORDER BY month"
        ),
        # LEAD looks the wrong way.
        (
            "WITH monthly AS ("
            "  SELECT substr(closed_on, 1, 7) AS month, SUM(amount) AS booked "
            "  FROM deals WHERE stage = 'won' GROUP BY substr(closed_on, 1, 7)"
            ") SELECT month, booked, booked - LEAD(booked) OVER (ORDER BY month) AS change "
            "FROM monthly ORDER BY month"
        ),
        # Includes lost and open deals.
        (
            "WITH monthly AS ("
            "  SELECT substr(closed_on, 1, 7) AS month, SUM(amount) AS booked "
            "  FROM deals GROUP BY substr(closed_on, 1, 7)"
            ") SELECT month, booked, booked - LAG(booked) OVER (ORDER BY month) AS change "
            "FROM monthly ORDER BY month"
        ),
    ],
)

_question(
    id="sql-analytics-first-order-per-customer",
    title="Each Customer's First Paid Order",
    skill_id="sql_analytics",
    concept="window function",
    difficulty=7,
    minutes=30,
    summary="One row per customer: the earliest paid order, order id breaking a same-day tie.",
    statement=(
        "Return **three columns**, `name`, `product` and `placed_on`, giving "
        "each customer's **earliest** `paid` order. If a customer has two paid "
        "orders on the same date, the one with the smaller order id wins. "
        "Customers with no paid order do not appear. Row order does not matter."
    ),
    requirements=[
        "Consider only paid orders",
        "Return exactly one row per customer with at least one paid order",
        "Pick the earliest placed_on, breaking a tie by the smaller order id",
        "Return the customer name, the product and the date, in that column order",
    ],
    reference=(
        "WITH ranked AS ("
        "  SELECT c.name AS name, o.product AS product, o.placed_on AS placed_on, "
        "  ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY o.placed_on, o.id) AS rn "
        "  FROM customers c JOIN orders o ON o.customer_id = c.id "
        "  WHERE o.status = 'paid'"
        ") SELECT name, product, placed_on FROM ranked WHERE rn = 1"
    ),
    world="store",
    secondary_skill_id="sql_joins",
    wrong=[
        # Earliest by insertion order rather than by date: the order with the
        # lowest id is not the one placed first.
        (
            "WITH ranked AS ("
            "  SELECT c.name AS name, o.product AS product, o.placed_on AS placed_on, "
            "  ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY o.id) AS rn "
            "  FROM customers c JOIN orders o ON o.customer_id = c.id "
            "  WHERE o.status = 'paid'"
            ") SELECT name, product, placed_on FROM ranked WHERE rn = 1"
        ),
        # Latest, not earliest.
        (
            "WITH ranked AS ("
            "  SELECT c.name AS name, o.product AS product, o.placed_on AS placed_on, "
            "  ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY o.placed_on DESC, o.id DESC) AS rn "
            "  FROM customers c JOIN orders o ON o.customer_id = c.id "
            "  WHERE o.status = 'paid'"
            ") SELECT name, product, placed_on FROM ranked WHERE rn = 1"
        ),
        # Every paid order.
        (
            "SELECT c.name AS name, o.product AS product, o.placed_on AS placed_on "
            "FROM customers c JOIN orders o ON o.customer_id = c.id "
            "WHERE o.status = 'paid'"
        ),
    ],
)

_question(
    id="sql-analytics-rank-with-ties",
    title="Rank Products by Paid Units, Ties Sharing a Rank",
    skill_id="sql_analytics",
    concept="ranking",
    difficulty=7,
    minutes=30,
    summary="RANK, not ROW_NUMBER: tied products share a rank and the next rank skips.",
    statement=(
        "Return **three columns**, `product`, `units` and `rank`, where `units` "
        "is the number of `paid` orders of that product and `rank` is its "
        "position when ordering by `units` descending. **Products with the same "
        "unit count share the same rank**, and the following rank skips "
        "accordingly (1, 2, 2, 4). Return the rows ordered by `units` "
        "descending, then by `product` ascending."
    ),
    requirements=[
        "Count paid orders per product",
        "Tied unit counts must share a rank, and the next rank must skip (1, 2, 2, 4)",
        "Return the rows ordered by units descending, then product ascending",
        "Alias the columns exactly 'product', 'units' and 'rank'",
    ],
    reference=(
        "WITH counts AS ("
        "  SELECT product, COUNT(*) AS units FROM orders WHERE status = 'paid' "
        "  GROUP BY product"
        ") SELECT product, units, RANK() OVER (ORDER BY units DESC) AS rank "
        "FROM counts ORDER BY units DESC, product ASC"
    ),
    world="store",
    ordered=True,
    require_columns=True,
    wrong=[
        # ROW_NUMBER gives tied products different ranks.
        (
            "WITH counts AS ("
            "  SELECT product, COUNT(*) AS units FROM orders WHERE status = 'paid' "
            "  GROUP BY product"
            ") SELECT product, units, ROW_NUMBER() OVER (ORDER BY units DESC, product) AS rank "
            "FROM counts ORDER BY units DESC, product ASC"
        ),
        # DENSE_RANK does not skip after a tie.
        (
            "WITH counts AS ("
            "  SELECT product, COUNT(*) AS units FROM orders WHERE status = 'paid' "
            "  GROUP BY product"
            ") SELECT product, units, DENSE_RANK() OVER (ORDER BY units DESC) AS rank "
            "FROM counts ORDER BY units DESC, product ASC"
        ),
        # Ranks ascending.
        (
            "WITH counts AS ("
            "  SELECT product, COUNT(*) AS units FROM orders WHERE status = 'paid' "
            "  GROUP BY product"
            ") SELECT product, units, RANK() OVER (ORDER BY units ASC) AS rank "
            "FROM counts ORDER BY units DESC, product ASC"
        ),
    ],
)

_question(
    id="sql-analytics-share-of-region",
    title="Each Rep's Share of Their Region",
    skill_id="sql_analytics",
    concept="window function",
    difficulty=8,
    minutes=35,
    summary="A partitioned window total as the denominator for a per-rep share.",
    statement=(
        "Return **three columns**, `region`, `rep` and `share_pct`, over `won` "
        "deals: each rep's booked total as a percentage of **their own "
        "region's** booked total, rounded to one decimal place. Only reps with "
        "at least one won deal appear. Row order does not matter."
    ),
    requirements=[
        "Total won amounts per rep, joined through to their region",
        "The denominator is the rep's own region's total, not the company total",
        "Express the share as a percentage rounded to one decimal place",
        "Return the region, the rep name and the share, in that column order",
    ],
    reference=(
        "WITH rep_totals AS ("
        "  SELECT g.name AS region, r.name AS rep, SUM(d.amount) AS booked "
        "  FROM deals d JOIN reps r ON r.id = d.rep_id "
        "  JOIN regions g ON g.id = r.region_id WHERE d.stage = 'won' "
        "  GROUP BY g.name, r.name"
        ") SELECT region, rep, ROUND(booked * 100.0 / "
        "SUM(booked) OVER (PARTITION BY region), 1) AS share_pct FROM rep_totals"
    ),
    world="sales",
    require_columns=True,
    wrong=[
        # Company-wide denominator.
        (
            "WITH rep_totals AS ("
            "  SELECT g.name AS region, r.name AS rep, SUM(d.amount) AS booked "
            "  FROM deals d JOIN reps r ON r.id = d.rep_id "
            "  JOIN regions g ON g.id = r.region_id WHERE d.stage = 'won' "
            "  GROUP BY g.name, r.name"
            ") SELECT region, rep, ROUND(booked * 100.0 / SUM(booked) OVER (), 1) AS share_pct "
            "FROM rep_totals"
        ),
        # Every rep is 100% of themselves.
        (
            "SELECT g.name AS region, r.name AS rep, ROUND(SUM(d.amount) * 100.0 / "
            "SUM(d.amount), 1) AS share_pct FROM deals d JOIN reps r ON r.id = d.rep_id "
            "JOIN regions g ON g.id = r.region_id WHERE d.stage = 'won' "
            "GROUP BY g.name, r.name"
        ),
        # Includes open and lost deals.
        (
            "WITH rep_totals AS ("
            "  SELECT g.name AS region, r.name AS rep, SUM(d.amount) AS booked "
            "  FROM deals d JOIN reps r ON r.id = d.rep_id "
            "  JOIN regions g ON g.id = r.region_id GROUP BY g.name, r.name"
            ") SELECT region, rep, ROUND(booked * 100.0 / "
            "SUM(booked) OVER (PARTITION BY region), 1) AS share_pct FROM rep_totals"
        ),
    ],
)

_question(
    id="sql-analytics-second-largest-deal",
    title="The Second Largest Won Deal per Rep",
    skill_id="sql_analytics",
    concept="ranking",
    difficulty=7,
    minutes=30,
    summary="Rank within a partition and take rank 2 — reps with only one won deal drop out.",
    statement=(
        "Return **two columns**, `rep` and `amount`, giving each rep's "
        "**second** largest `won` deal by amount, breaking a tie on amount by "
        "the smaller deal id. A rep with fewer than two won deals has no second "
        "deal and must not appear. Row order does not matter."
    ),
    requirements=[
        "Consider only won deals",
        "Rank a rep's won deals by amount descending, breaking ties by the smaller deal id",
        "Return the row at position two for each rep",
        "Reps with fewer than two won deals do not appear at all",
    ],
    reference=(
        "WITH ranked AS ("
        "  SELECT r.name AS rep, d.amount AS amount, ROW_NUMBER() OVER ("
        "    PARTITION BY d.rep_id ORDER BY d.amount DESC, d.id ASC) AS rn "
        "  FROM deals d JOIN reps r ON r.id = d.rep_id WHERE d.stage = 'won'"
        ") SELECT rep, amount FROM ranked WHERE rn = 2"
    ),
    world="sales",
    wrong=[
        # The largest, not the second.
        (
            "WITH ranked AS ("
            "  SELECT r.name AS rep, d.amount AS amount, ROW_NUMBER() OVER ("
            "    PARTITION BY d.rep_id ORDER BY d.amount DESC, d.id ASC) AS rn "
            "  FROM deals d JOIN reps r ON r.id = d.rep_id WHERE d.stage = 'won'"
            ") SELECT rep, amount FROM ranked WHERE rn = 1"
        ),
        # Second largest company-wide, repeated.
        (
            "WITH ranked AS ("
            "  SELECT r.name AS rep, d.amount AS amount, ROW_NUMBER() OVER ("
            "    ORDER BY d.amount DESC, d.id ASC) AS rn "
            "  FROM deals d JOIN reps r ON r.id = d.rep_id WHERE d.stage = 'won'"
            ") SELECT rep, amount FROM ranked WHERE rn = 2"
        ),
        # OFFSET on the whole table is not per rep.
        (
            "SELECT r.name AS rep, d.amount AS amount FROM deals d "
            "JOIN reps r ON r.id = d.rep_id WHERE d.stage = 'won' "
            "ORDER BY d.amount DESC, d.id ASC LIMIT 1 OFFSET 1"
        ),
    ],
)

_question(
    id="sql-analytics-repeat-customer-rate",
    title="Repeat Rate Among Paying Customers",
    skill_id="sql_analytics",
    concept="cte",
    difficulty=8,
    minutes=35,
    summary="One row, one number: the share of paying customers who paid more than once.",
    statement=(
        "Return **one row and one column**, `repeat_rate`: among customers with "
        "at least one `paid` order, the fraction who have **two or more** paid "
        "orders, rounded to three decimal places. When no customer has a paid "
        "order the answer is zero rows, not a NULL."
    ),
    requirements=[
        "The denominator is customers with at least one paid order",
        "The numerator is customers with two or more paid orders",
        "Round the fraction to three decimal places and alias it 'repeat_rate'",
        "Return zero rows when no customer has a paid order",
    ],
    reference=(
        "WITH paid_counts AS ("
        "  SELECT customer_id, COUNT(*) AS n FROM orders WHERE status = 'paid' "
        "  GROUP BY customer_id"
        ") SELECT ROUND(SUM(CASE WHEN n >= 2 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 3) "
        "AS repeat_rate FROM paid_counts HAVING COUNT(*) > 0"
    ),
    world="store",
    require_columns=True,
    wrong=[
        # Denominator is every customer, including those who never paid.
        (
            "WITH paid_counts AS ("
            "  SELECT customer_id, COUNT(*) AS n FROM orders WHERE status = 'paid' "
            "  GROUP BY customer_id"
            ") SELECT ROUND((SELECT COUNT(*) FROM paid_counts WHERE n >= 2) * 1.0 / "
            "(SELECT COUNT(*) FROM customers), 3) AS repeat_rate"
        ),
        # Integer division.
        (
            "WITH paid_counts AS ("
            "  SELECT customer_id, COUNT(*) AS n FROM orders WHERE status = 'paid' "
            "  GROUP BY customer_id"
            ") SELECT ROUND(SUM(CASE WHEN n >= 2 THEN 1 ELSE 0 END) / COUNT(*), 3) "
            "AS repeat_rate FROM paid_counts HAVING COUNT(*) > 0"
        ),
        # Returns a NULL row instead of no rows when nothing is paid.
        (
            "WITH paid_counts AS ("
            "  SELECT customer_id, COUNT(*) AS n FROM orders WHERE status = 'paid' "
            "  GROUP BY customer_id"
            ") SELECT ROUND(SUM(CASE WHEN n >= 2 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 3) "
            "AS repeat_rate FROM paid_counts"
        ),
    ],
)
