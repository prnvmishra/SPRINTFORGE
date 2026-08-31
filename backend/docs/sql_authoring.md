# Authoring a SQL question

SQL questions are **executed**, not pattern-matched. `app/services/sql_judge.py`
seeds an in-memory SQLite database per fixture dataset, runs your reference query
to derive the expected result, runs the learner's query, and compares the two
result sets. Practice questions live in `app/data/practice_sql.py`; project
tickets use the same judge through the `sql_query` check type
(`app/data/ticket_templates_data.py`).

## The spec

```python
SPEC = {
    "schema": ["CREATE TABLE orders (...); CREATE TABLE customers (...);"],
    "reference": "SELECT c.city AS city, SUM(o.amount) AS revenue FROM ... GROUP BY c.city",
    "ordered": False,          # compare row order too?  default False
    "require_columns": False,  # compare column names?   default False
    "read_only": True,         # reject non-SELECT statements. default True
    "datasets": [
        {"name": "sample: two cities", "rows": {"customers": [{...}], "orders": [{...}]}},
        {"name": "hidden: one city",   "rows": {...}, "hidden": True},
    ],
}
```

| Key | Meaning |
| --- | --- |
| `schema` | list of DDL scripts, run with `executescript`, applied to every dataset |
| `datasets` | **two or more**; `rows` is `{table: [row dict, ...]}`; `hidden: True` withholds it from Run and from the payload sent to the browser |
| `reference` | a query known to be correct. **The only source of expected results** — never write expected rows by hand |
| `ordered` | `True` only when the question genuinely requires a row order, and then say so in the requirements |
| `require_columns` | `True` only when the question demands specific column names |

Validate at import time, the way `practice_sql.py` and
`ticket_templates_data.py` do — not only in a test:

```python
sql_judge.validate_spec(SPEC, "practice_sql: my-question")
```

`validate_spec` re-derives every expected result from the reference, refuses a
question with fewer than two datasets, refuses one where every dataset yields
the same answer, and refuses one whose reference does not pass its own datasets.

## How expected results are declared

They are not. You declare the reference query; the judge runs it per dataset and
that *is* the expectation. Editing a fixture row therefore cannot leave a stale
hand-typed expectation behind — the failure mode that makes a judge lie.

## Ordering

Row order is undefined without `ORDER BY`, so the default comparison is
order-insensitive but **multiset**-based: duplicate rows still have to match in
number. Set `ordered: True` for a question that requires an order (top-N,
ranking), and the judge compares sequences and reports "the right rows, in the
wrong order" rather than a confusing row diff. If you set `ordered: True`, give
the reference a fully deterministic `ORDER BY` — add a tiebreak column, or two
runs of the same reference can disagree and the question becomes flaky.

## Defeating the hardcoded answer

The cheat is `SELECT 'Alice' AS name, 42 AS orders`. It is a legal read that
touches no table, so no amount of containment stops it. What stops it is
**multiple datasets whose correct answers differ**: a constant satisfies at most
one. `sql_judge.hardcode_probe(spec)` builds that constant query from the first
dataset's answer, and `tests/test_sql_judge.py` runs it against every authored
question and requires a rejection. This is the single most important property of
a SQL question — design the datasets for it first, not last.

## Traps found the hard way

- **Two datasets are not enough if they agree.** Vary the *answer*, not just the
  names. `validate_spec` catches this, so trust it rather than eyeballing.
- **Empty answers are a distinct case.** For an aggregate question include a
  dataset where nothing qualifies: `SELECT SUM(x) FROM t` returns one NULL row,
  `... GROUP BY city` returns none. Which one is correct is part of the
  question, and only a dataset can pin it down.
- **NULL is not zero and not absent.** `status != 'refunded'` silently drops
  NULL statuses; `COUNT(amount)` skips NULLs while `COUNT(*)` does not. Put a
  NULL in a fixture deliberately and decide what the right answer is.
- **Column names are not compared by default.** `SELECT name` and `SELECT name
  AS customer` are the same answer, so only set `require_columns` when the
  question actually asks for the alias — otherwise you fail correct work.
- **Types are normalised, strings are not.** Ints and floats compare
  numerically (`2 == 2.0`) and floats are rounded to 6 dp, because `AVG` differs
  in the last bits between equivalent plans. `'Alice'` and `'alice'` are
  genuinely different answers and are left alone.
- **Reference `ORDER BY` on a non-unique key is flaky.** Ties break arbitrarily.
  Always add a deterministic tiebreak (`ORDER BY units DESC, product ASC`).
- **Do not interpolate project context into SQL identifiers.** Ticket templates
  are run through `.format()`, and a domain noun inferred from free text can be
  a SQL keyword (`order`). The warehouse table names are fixed; only the prose
  is contextualised.
- **A rejected query has no dataset verdicts.** An empty submission, several
  statements, or a write produces `SqlGrade.rejection` and an empty
  `outcomes` list, so any `all(...)` over the outcomes must be guarded with
  `bool(outcomes)` or the submission passes vacuously.

## What the learner can and cannot do

Enforced by `sql_judge`, in this order:

1. Empty or comment-only submissions are rejected.
2. Several statements are rejected — `SELECT ';' AS x` is still one statement,
   because SQLite's own parser decides where the first one ends.
3. When `read_only` (the default), a statement starting with a write keyword is
   rejected with a message naming the keyword. A typo like `SELCT` deliberately
   falls through so SQLite reports the real syntax error.
4. Execution runs under an authorizer permitting reads only, so anything that
   slipped past step 3 — including `load_extension` — is refused at prepare
   time and the fixture table cannot be dropped.
5. A wall-clock deadline (`QUERY_TIMEOUT_SECONDS`) interrupts a runaway query,
   and `MAX_RESULT_ROWS` caps the result set, so an unbounded recursive CTE ends
   as a graded failure rather than a hung request.
