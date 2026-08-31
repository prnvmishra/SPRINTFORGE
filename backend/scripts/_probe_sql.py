from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import sql_judge

SPEC = {
    "schema": [
        """
        CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, city TEXT);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL, status TEXT);
        """
    ],
    "datasets": [
        {
            "name": "two paying customers",
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
            "name": "one paying customer",
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
    "reference": (
        "SELECT c.name, SUM(o.amount) AS total FROM customers c "
        "JOIN orders o ON o.customer_id = c.id WHERE o.status = 'paid' "
        "GROUP BY c.name"
    ),
}

sql_judge.validate_spec(SPEC, "probe")
print("spec validated")
print("probe query:", sql_judge.hardcode_probe(SPEC))

ATTEMPTS = {
    "correct": SPEC["reference"],
    "correct but different style": (
        "SELECT customers.name, SUM(orders.amount) AS total FROM orders, customers "
        "WHERE orders.customer_id = customers.id AND orders.status = 'paid' "
        "GROUP BY customers.name ORDER BY total DESC"
    ),
    "hardcoded": sql_judge.hardcode_probe(SPEC),
    "missing WHERE": (
        "SELECT c.name, SUM(o.amount) AS total FROM customers c "
        "JOIN orders o ON o.customer_id = c.id GROUP BY c.name"
    ),
    "wrong join": (
        "SELECT c.name, SUM(o.amount) AS total FROM customers c "
        "LEFT JOIN orders o ON o.id = c.id WHERE o.status = 'paid' GROUP BY c.name"
    ),
    "drop then select": "DROP TABLE orders; SELECT 1",
    "delete": "DELETE FROM orders",
    "semicolon in a string is fine": (
        "SELECT c.name, SUM(o.amount) AS total FROM customers c "
        "JOIN orders o ON o.customer_id = c.id WHERE o.status = 'paid' GROUP BY c.name"
    ),
    "runaway cross join": "SELECT a.id FROM orders a, orders b, orders c, customers d, customers e",
    "syntax error": "SELCT name FROM customers",
}

for label, query in ATTEMPTS.items():
    result = sql_judge.grade(query, SPEC)
    print("\n---", label, "->", "PASS" if result.passed else "FAIL")
    if result.rejection:
        print("    rejected:", result.rejection)
    for outcome in result.outcomes:
        print(f"    [{'ok  ' if outcome.passed else 'FAIL'}] {outcome.dataset}: {outcome.detail}")
