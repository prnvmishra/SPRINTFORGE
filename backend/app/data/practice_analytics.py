"""Python-analytics practice questions for the Data Analyst path.

Why these are stdin/stdout problems
-----------------------------------
The four SQL skills are graded by `sql_judge`. The other six data skills —
cleaning, EDA, statistics, visualisation, dashboards and spreadsheet modelling —
are *calculations*, and the honest way to grade a calculation is to run it. So
each question here is a `kind: "challenge"` module in Python, graded by the same
`code_execution_service` judge the DSA track uses: real subprocess, real time
limit, visible cases on Run and hidden cases on Submit.

That deliberately avoids two permissive alternatives. Grading a spreadsheet
formula or a chart by pattern-matching the source would pass `=SUM(A1:A9)`
written by luck and fail a correct `SUMPRODUCT`; asking an AI to mark the answer
would make the verdict unrepeatable. Instead the question states the arithmetic
exactly — including the percentile convention, the rounding, and what happens on
the empty input — and the learner's program has to produce it.

The authoring contract, enforced at import time by `_problem`
------------------------------------------------------------
* `reference` is a correct Python program and is **the only source of expected
  output**: every case's `expected_stdout`, and every worked example's `stdout`,
  is derived by running it. A hand-typed expectation cannot go stale here
  because there is no hand-typed expectation.
* `wrong` holds programs a learner plausibly writes that are subtly incorrect.
  Each one **must** produce different output from the reference on at least one
  declared case, or the import fails. That is what makes a false pass
  impossible: a question cannot ship until it is proven to reject the mistake it
  is about.
* `starter` must also fail. It plumbs the I/O and leaves the logic to a `TODO`,
  and the import refuses a starter that happens to pass.
* Every question declares at least one visible case (published to the learner)
  and at least one hidden case (only graded on Submit), so satisfying the
  samples is not sufficient.

Neither `reference` nor `wrong` is stored on the module dict, so neither can
reach a client: they live in `REFERENCE_SOLUTIONS` / `WRONG_SOLUTIONS`, keyed by
module id, and are consumed by
`scripts/verify_data_analyst_curriculum.py`, which re-proves all of the above
through the real subprocess judge rather than in-process.
"""

from __future__ import annotations

import io
import sys
from typing import Any, Optional

ANALYTICS_MODULES: list[dict[str, Any]] = []

#: module id -> the correct program. Never served.
REFERENCE_SOLUTIONS: dict[str, str] = {}

#: module id -> programs that must be rejected. Never served.
WRONG_SOLUTIONS: dict[str, list[str]] = {}


class AnalyticsAuthoringError(RuntimeError):
    """A question cannot grade honestly, so it must not be importable."""


def _run(source: str, stdin_text: str) -> str:
    """Run a program in-process against `stdin_text` and return its stdout.

    Only ever used on author-supplied programs (reference, wrong, starter) at
    import time, to derive expectations and prove the wrong answers are caught.
    Learner code is never run this way — that goes to the subprocess judge.
    """
    stdout = io.StringIO()
    original_stdin, original_stdout = sys.stdin, sys.stdout
    sys.stdin, sys.stdout = io.StringIO(stdin_text), stdout
    try:
        exec(compile(source, "<analytics-solution>", "exec"), {"__name__": "__main__"})
    finally:
        sys.stdin, sys.stdout = original_stdin, original_stdout
    return stdout.getvalue().strip()


def _run_or_error(source: str, stdin_text: str) -> Optional[str]:
    """Output, or None when the program crashed — a crash is a failure too."""
    try:
        return _run(source, stdin_text)
    except Exception:  # noqa: BLE001 - a broken candidate is simply "fails"
        return None


def _problem(
    *,
    id: str,
    title: str,
    skill_id: str,
    concept: str,
    difficulty: int,
    minutes: int,
    summary: str,
    statement: str,
    input_format: str,
    output_format: str,
    constraints: list[str],
    requirements: list[str],
    examples: list[dict[str, str]],
    cases: list[tuple[str, str, bool]],
    reference: str,
    starter: str,
    wrong: list[str],
    secondary_skill_id: Optional[str] = None,
) -> dict[str, Any]:
    """Assemble one module, deriving every expectation from `reference`."""
    if not wrong:
        raise AnalyticsAuthoringError(f"{id}: a question with no wrong answer proves nothing")
    if "TODO" not in starter:
        raise AnalyticsAuthoringError(f"{id}: the starter must leave a TODO")
    if not any(hidden for _, _, hidden in cases):
        raise AnalyticsAuthoringError(f"{id}: no hidden case, so Submit gates nothing")
    if not any(not hidden for _, _, hidden in cases):
        raise AnalyticsAuthoringError(f"{id}: no visible case for the learner to Run")

    test_cases = []
    for name, stdin_text, hidden in cases:
        expected = _run(reference, stdin_text)
        if not expected:
            raise AnalyticsAuthoringError(
                f"{id}: case '{name}' expects no output, which grades nothing"
            )
        test_cases.append(
            {
                "name": name,
                "stdin": stdin_text,
                "expected_stdout": expected,
                "hidden": hidden,
            }
        )

    expectations = [(c["stdin"], c["expected_stdout"]) for c in test_cases]

    def _caught(candidate: str) -> bool:
        return any(_run_or_error(candidate, stdin) != expected for stdin, expected in expectations)

    if not _caught(starter):
        raise AnalyticsAuthoringError(f"{id}: the starter passes every case — it solves the problem")
    for index, candidate in enumerate(wrong):
        if not _caught(candidate):
            raise AnalyticsAuthoringError(
                f"{id}: wrong answer #{index} passes every case, so a learner who "
                f"makes that mistake would be told they were right. Add a case that "
                f"distinguishes it."
            )

    worked = []
    for example in examples:
        worked.append(
            {
                "stdin": example["stdin"],
                "stdout": _run(reference, example["stdin"]),
                "explanation": example["explanation"],
            }
        )
    if not worked or not all(e["explanation"].strip() for e in worked):
        raise AnalyticsAuthoringError(f"{id}: every worked example needs an explanation")

    module: dict[str, Any] = {
        "id": id,
        "title": title,
        "kind": "challenge",
        "practice_layer": "analysis",
        "skill_id": skill_id,
        "technology": "Python",
        "language": "python",
        "concept": concept,
        "difficulty": difficulty,
        "estimated_minutes": minutes,
        "summary": summary,
        "problem_statement": statement,
        "constraints": constraints,
        "input_format": input_format,
        "output_format": output_format,
        "examples": worked,
        "requirements": requirements,
        "editable_files": ["solution"],
        "files": {"solution": starter},
        "test_cases": test_cases,
        "checks": [],
    }
    if secondary_skill_id:
        module["secondary_skill_id"] = secondary_skill_id

    REFERENCE_SOLUTIONS[id] = reference
    WRONG_SOLUTIONS[id] = list(wrong)
    ANALYTICS_MODULES.append(module)
    return module


# =========================================================================== #
#  data_cleaning                                                              #
# =========================================================================== #

_problem(
    id="an-clean-duplicate-emails",
    title="Count the Real Customers Behind Duplicate Emails",
    skill_id="data_cleaning",
    concept="duplicates",
    difficulty=3,
    minutes=20,
    summary="De-duplicate an email column that has not been normalised, and report how many rows were redundant.",
    statement=(
        "An export of the CRM has the same person in it several times: the email "
        "column has inconsistent case and stray surrounding whitespace, so "
        "`  Ada@Example.COM ` and `ada@example.com` are the same customer.\n\n"
        "Normalise each email by stripping surrounding whitespace and lowercasing "
        "it, then print how many distinct customers the file actually contains "
        "and how many rows were redundant duplicates."
    ),
    input_format=(
        "Line 1: n, the number of rows.\n"
        "Next n lines: one email address, possibly with surrounding whitespace "
        "and inconsistent case. An email never contains a comma."
    ),
    output_format=(
        "One line: the number of distinct normalised emails, a space, then the "
        "number of duplicate rows (n minus the distinct count)."
    ),
    constraints=["1 <= n <= 20000", "Every line holds a non-empty email address"],
    requirements=[
        "Compare emails case-insensitively",
        "Strip surrounding whitespace before comparing",
        "Print the distinct count and the duplicate count, space separated",
    ],
    examples=[
        {
            "stdin": "4\nada@example.com\n  Ada@Example.COM \nbob@example.com\nADA@EXAMPLE.COM\n",
            "explanation": (
                "Three rows normalise to ada@example.com and one to "
                "bob@example.com, so there are 2 distinct customers and 2 "
                "redundant rows."
            ),
        }
    ],
    cases=[
        ("sample: mixed case and padding", "4\nada@example.com\n  Ada@Example.COM \nbob@example.com\nADA@EXAMPLE.COM\n", False),
        ("sample: already clean", "3\na@x.com\nb@x.com\nc@x.com\n", False),
        ("hidden: single row", "1\n   ONE@X.COM\n", True),
        ("hidden: every row identical", "5\nq@x.com\nQ@X.com\n q@x.com \nQ@x.COM\nq@X.com\n", True),
        ("hidden: tabs and trailing spaces", "4\n\tzoe@x.com\t\nzoe@x.com\nZOE@x.com   \nyan@x.com\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    seen = set()
    for line in data[1:1 + n]:
        seen.add(line.strip().lower())
    print(f"{len(seen)} {n - len(seen)}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def distinct_customers(emails):
    # TODO: normalise each email (strip whitespace, lowercase) and return the
    # number of distinct customers.
    return len(emails)


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    emails = data[1:1 + n]
    distinct = distinct_customers(emails)
    print(f"{distinct} {n - distinct}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # No normalisation at all.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
distinct = len(set(data[1:1 + n]))
print(f"{distinct} {n - distinct}")
""",
        # Lowercases but does not strip.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
distinct = len({line.lower() for line in data[1:1 + n]})
print(f"{distinct} {n - distinct}")
""",
        # Reports the row count as the duplicate count.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
distinct = len({line.strip().lower() for line in data[1:1 + n]})
print(f"{distinct} {n}")
""",
    ],
)

_problem(
    id="an-clean-median-fill",
    title="Fill Missing Readings With the Median",
    skill_id="data_cleaning",
    concept="missing values",
    difficulty=4,
    minutes=22,
    summary="Impute NA values with the median of the known values, then report the mean of the completed column.",
    statement=(
        "A numeric column has gaps, written `NA`. Filling a gap with the mean "
        "drags the average towards whatever outliers exist, so the convention "
        "here is the **median** of the known values.\n\n"
        "Compute the median of the values that are present, replace every `NA` "
        "with it, and print the mean of the completed column rounded to two "
        "decimal places.\n\n"
        "The median of an even number of values is the average of the two "
        "middle values of the sorted list. At least one value is always present."
    ),
    input_format=(
        "Line 1: n, the number of values.\nNext n lines: an integer, or the "
        "literal `NA`."
    ),
    output_format="One line: the mean of the completed column, to exactly two decimal places.",
    constraints=[
        "1 <= n <= 20000",
        "-1000000 <= value <= 1000000",
        "At least one value is not NA",
    ],
    requirements=[
        "Compute the median from the present values only",
        "Use the average of the two middle values when the count of present values is even",
        "Replace every NA with that median before averaging",
        "Print the mean to exactly two decimal places",
    ],
    examples=[
        {
            "stdin": "5\n10\nNA\n20\n30\nNA\n",
            "explanation": (
                "The present values are 10, 20, 30, so the median is 20. The "
                "completed column is 10, 20, 20, 30, 20 — mean 20.00."
            ),
        }
    ],
    cases=[
        ("sample: three present, two missing", "5\n10\nNA\n20\n30\nNA\n", False),
        ("sample: even count of present values", "4\n1\n3\n5\nNA\n", False),
        ("hidden: no gaps at all", "3\n2\n4\n9\n", True),
        ("hidden: one present value, rest missing", "4\nNA\n7\nNA\nNA\n", True),
        ("hidden: outlier makes mean and median differ", "6\n1\n2\n3\n4\n1000\nNA\n", True),
        ("hidden: negatives", "5\n-10\n-2\nNA\n-6\n-4\n", True),
    ],
    reference="""import sys


def median(values):
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = [line.strip() for line in data[1:1 + n]]
    present = [int(v) for v in rows if v != "NA"]
    fill = median(present)
    completed = [float(v) if v != "NA" else fill for v in rows]
    print(f"{sum(completed) / len(completed):.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def fill_value(present):
    # TODO: return the median of the present values (average the two middle
    # values when there is an even number of them).
    return 0.0


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = [line.strip() for line in data[1:1 + n]]
    present = [int(v) for v in rows if v != "NA"]
    fill = fill_value(present)
    completed = [float(v) if v != "NA" else fill for v in rows]
    print(f"{sum(completed) / len(completed):.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Fills with the mean instead of the median.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rows = [line.strip() for line in data[1:1 + n]]
present = [int(v) for v in rows if v != "NA"]
fill = sum(present) / len(present)
completed = [float(v) if v != "NA" else fill for v in rows]
print(f"{sum(completed) / len(completed):.2f}")
""",
        # Drops the missing rows instead of imputing them.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rows = [line.strip() for line in data[1:1 + n]]
present = [int(v) for v in rows if v != "NA"]
print(f"{sum(present) / len(present):.2f}")
""",
        # Even-length median taken as the upper middle value.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rows = [line.strip() for line in data[1:1 + n]]
present = sorted(int(v) for v in rows if v != "NA")
fill = float(present[len(present) // 2])
completed = [float(v) if v != "NA" else fill for v in rows]
print(f"{sum(completed) / len(completed):.2f}")
""",
        # Fills with zero.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rows = [line.strip() for line in data[1:1 + n]]
completed = [float(v) if v != "NA" else 0.0 for v in rows]
print(f"{sum(completed) / len(completed):.2f}")
""",
    ],
)

_problem(
    id="an-clean-canonical-names",
    title="Canonicalise Messy Customer Names",
    skill_id="data_cleaning",
    concept="type coercion",
    difficulty=4,
    minutes=22,
    summary="Collapse whitespace and normalise case so the same person is one name, then list them in order.",
    statement=(
        "Names arrived from three different systems: some are shouted, some have "
        "double spaces, some have leading or trailing whitespace. "
        "`  ada   LOVELACE ` and `Ada Lovelace` are the same person.\n\n"
        "Canonicalise every name — strip the ends, collapse each run of "
        "whitespace to a single space, and title-case each word (first letter "
        "upper, the rest lower) — then print each distinct canonical name once, "
        "sorted alphabetically, one per line."
    ),
    input_format="Line 1: n. Next n lines: a name, possibly messy.",
    output_format="One canonical name per line, sorted ascending. No duplicates.",
    constraints=[
        "1 <= n <= 20000",
        "Names contain letters, spaces and hyphens only",
        "Every line contains at least one word",
    ],
    requirements=[
        "Strip leading and trailing whitespace",
        "Collapse internal runs of whitespace to a single space",
        "Title-case every word, so 'LOVELACE' becomes 'Lovelace'",
        "Print each distinct canonical name once, sorted ascending",
    ],
    examples=[
        {
            "stdin": "3\n  ada   LOVELACE \nAda Lovelace\nGRACE hopper\n",
            "explanation": (
                "The first two rows both canonicalise to 'Ada Lovelace', so it "
                "is printed once, before 'Grace Hopper'."
            ),
        }
    ],
    cases=[
        ("sample: shouting and double spaces", "3\n  ada   LOVELACE \nAda Lovelace\nGRACE hopper\n", False),
        ("sample: already canonical", "2\nAlan Turing\nBarbara Liskov\n", False),
        ("hidden: single messy name", "1\n   kATHERINE    johnson   \n", True),
        ("hidden: sorting is not input order", "4\nzoe adams\nAmy Zeal\nzoe   ADAMS\nAmy zeal\n", True),
        ("hidden: single-word names", "3\nMADONNA\nmadonna\nPrince\n", True),
    ],
    reference="""import sys


def canonical(name):
    return " ".join(word.capitalize() for word in name.split())


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    names = {canonical(line) for line in data[1:1 + n]}
    for name in sorted(names):
        print(name)


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def canonical(name):
    # TODO: strip the ends, collapse whitespace runs, title-case each word.
    return name


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    names = {canonical(line) for line in data[1:1 + n]}
    for name in sorted(names):
        print(name)


if __name__ == "__main__":
    main()
""",
    wrong=[
        # strip() only: internal double spaces still split the same person in two.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
names = {line.strip().title() for line in data[1:1 + n]}
for name in sorted(names):
    print(name)
""",
        # Collapses whitespace but leaves the case alone.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
names = {" ".join(line.split()) for line in data[1:1 + n]}
for name in sorted(names):
    print(name)
""",
        # Canonical but unsorted, and duplicates kept.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    print(" ".join(w.capitalize() for w in line.split()))
""",
    ],
)

_problem(
    id="an-clean-coerce-integers",
    title="Coerce a Text Column to Integers",
    skill_id="data_cleaning",
    concept="type coercion",
    difficulty=4,
    minutes=22,
    summary="Sum the values that are genuinely whole numbers and count the ones that are not.",
    statement=(
        "A quantity column came through as text. Some cells are whole numbers, "
        "possibly with a leading `+` or `-` and surrounding whitespace. The rest "
        "are not usable: `12.5`, `12 units`, `twelve`, `1e3` and the empty cell "
        "are all **invalid** for this column, and silently coercing them is how "
        "a total ends up wrong.\n\n"
        "Print the sum of the valid values and the number of invalid cells."
    ),
    input_format="Line 1: n. Next n lines: one raw cell, which may be empty.",
    output_format="One line: the sum of the valid integers, a space, then the count of invalid cells.",
    constraints=[
        "1 <= n <= 20000",
        "A cell is at most 40 characters",
        "The sum fits in a 64-bit integer",
    ],
    requirements=[
        "Accept an optional leading + or - followed by digits, with surrounding whitespace allowed",
        "Reject decimals, scientific notation, embedded text and the empty cell",
        "Print the sum of valid values, then the count of invalid cells",
        "A sum of zero valid values is 0, not blank",
    ],
    examples=[
        {
            "stdin": "5\n10\n-4\n12.5\n7 units\n  +3\n",
            "explanation": (
                "10, -4 and +3 are valid and total 9. '12.5' and '7 units' are "
                "invalid, so the count is 2."
            ),
        }
    ],
    cases=[
        ("sample: mixed validity", "5\n10\n-4\n12.5\n7 units\n  +3\n", False),
        ("sample: all valid", "3\n1\n2\n3\n", False),
        ("hidden: nothing is valid", "4\n\nabc\n1.0\n2e3\n", True),
        ("hidden: signs and padding", "4\n  -7  \n+0\n0\n -0 \n", True),
        ("hidden: digits with a trailing dot", "3\n5.\n5\n.5\n", True),
        ("hidden: underscores are not digits", "3\n1_000\n1000\n-1_0\n", True),
    ],
    reference="""import sys
import re

PATTERN = re.compile(r"^[+-]?[0-9]+$")


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    total = 0
    invalid = 0
    for raw in data[1:1 + n]:
        cell = raw.strip()
        if PATTERN.match(cell):
            total += int(cell)
        else:
            invalid += 1
    print(f"{total} {invalid}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def is_whole_number(cell):
    # TODO: return True only for an optional sign followed by digits.
    return True


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    total = 0
    invalid = 0
    for raw in data[1:1 + n]:
        cell = raw.strip()
        if is_whole_number(cell):
            total += int(cell)
        else:
            invalid += 1
    print(f"{total} {invalid}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # float() accepts decimals and scientific notation, then truncates.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
total = 0
invalid = 0
for raw in data[1:1 + n]:
    cell = raw.strip()
    try:
        total += int(float(cell))
    except ValueError:
        invalid += 1
print(f"{total} {invalid}")
""",
        # isdigit() rejects negative numbers, so they are counted as invalid.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
total = 0
invalid = 0
for raw in data[1:1 + n]:
    cell = raw.strip()
    if cell.isdigit():
        total += int(cell)
    else:
        invalid += 1
print(f"{total} {invalid}")
""",
        # Pulls the digits out of anything, so '7 units' silently becomes 7.
        """import sys
import re

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
total = 0
invalid = 0
for raw in data[1:1 + n]:
    found = re.findall(r"-?[0-9]+", raw)
    if found:
        total += int(found[0])
    else:
        invalid += 1
print(f"{total} {invalid}")
""",
    ],
)

_problem(
    id="an-clean-iqr-outliers",
    title="Drop Outliers With the 1.5 IQR Rule",
    skill_id="data_cleaning",
    concept="outliers",
    difficulty=6,
    minutes=28,
    summary="Remove values outside the 1.5 IQR fences and report how many went and what the mean became.",
    statement=(
        "One mistyped order value can move a mean by more than the rest of the "
        "data combined, so the values outside the interquartile fences are "
        "dropped before averaging.\n\n"
        "Use the **nearest-rank** convention, which is unambiguous on small "
        "samples. Sort the values ascending into `v[0..n-1]`. For a quantile "
        "`p`, the rank is `ceil(p * n)` clamped to the range 1..n, and the "
        "quantile is `v[rank - 1]`. So `Q1` uses `p = 0.25` and `Q3` uses "
        "`p = 0.75`.\n\n"
        "With `IQR = Q3 - Q1`, a value is an outlier when it is strictly below "
        "`Q1 - 1.5 * IQR` or strictly above `Q3 + 1.5 * IQR`. Print how many "
        "values were dropped and the mean of the values that remain, to two "
        "decimal places. At least one value always remains."
    ),
    input_format="Line 1: n. Line 2: n space-separated integers.",
    output_format="One line: the number of dropped values, a space, then the mean of the kept values to two decimal places.",
    constraints=[
        "1 <= n <= 20000",
        "-1000000 <= value <= 1000000",
        "Use the nearest-rank quantile defined above — other conventions give different answers",
    ],
    requirements=[
        "Compute Q1 and Q3 with the nearest-rank convention stated in the problem",
        "Fences are Q1 - 1.5*IQR and Q3 + 1.5*IQR, and only values strictly outside them are dropped",
        "Print the dropped count and the mean of the kept values to two decimal places",
        "Handle the case where nothing is dropped",
    ],
    examples=[
        {
            "stdin": "8\n10 12 11 13 12 11 10 900\n",
            "explanation": (
                "Sorted: 10 10 11 11 12 12 13 900. Q1 is the 2nd value (10) and "
                "Q3 the 6th (12), so IQR is 2 and the fences are 7 and 15. Only "
                "900 is outside, leaving a mean of 11.29."
            ),
        }
    ],
    cases=[
        ("sample: one huge outlier", "8\n10 12 11 13 12 11 10 900\n", False),
        ("sample: nothing to drop", "5\n4 5 6 5 4\n", False),
        ("hidden: single value", "1\n42\n", True),
        ("hidden: outliers on both sides", "9\n-500 10 11 12 13 12 11 10 400\n", True),
        ("hidden: all identical, IQR zero", "6\n7 7 7 7 7 7\n", True),
        # Q1=2, Q3=4, IQR=2, so the upper fence is exactly 7 and the 7 is kept.
        ("hidden: value exactly on the fence is kept", "4\n2 3 4 7\n", True),
        # Q1=11, Q3=15, IQR=4: 20 is outside the 1.0 fences but inside the 1.5
        # fences, so the multiplier is not a detail.
        ("hidden: 1.5 keeps what 1.0 would drop", "8\n10 11 12 13 14 15 16 20\n", True),
        # Nearest-rank drops the 30 here; interpolated quantiles (numpy's
        # default) keep it. The stated convention is the answer.
        ("hidden: the quantile convention decides", "8\n7 12 16 11 30 27 18 11\n", True),
    ],
    reference="""import sys
import math


def quantile(ordered, p):
    n = len(ordered)
    rank = min(max(math.ceil(p * n), 1), n)
    return float(ordered[rank - 1])


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    ordered = sorted(values)
    q1 = quantile(ordered, 0.25)
    q3 = quantile(ordered, 0.75)
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    kept = [v for v in values if low <= v <= high]
    print(f"{len(values) - len(kept)} {sum(kept) / len(kept):.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def fences(values):
    # TODO: return (low, high) from the nearest-rank Q1/Q3 and the 1.5 IQR rule.
    return float("-inf"), float("inf")


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    low, high = fences(values)
    kept = [v for v in values if low <= v <= high]
    print(f"{len(values) - len(kept)} {sum(kept) / len(kept):.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Standard-deviation rule instead of the IQR rule.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
mean = sum(values) / n
var = sum((v - mean) ** 2 for v in values) / n
sd = var ** 0.5
kept = [v for v in values if abs(v - mean) <= 3 * sd] or values
print(f"{len(values) - len(kept)} {sum(kept) / len(kept):.2f}")
""",
        # 1.0 IQR instead of 1.5.
        """import sys
import math

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
ordered = sorted(values)


def quantile(p):
    rank = min(max(math.ceil(p * n), 1), n)
    return float(ordered[rank - 1])


q1, q3 = quantile(0.25), quantile(0.75)
iqr = q3 - q1
kept = [v for v in values if q1 - iqr <= v <= q3 + iqr]
print(f"{len(values) - len(kept)} {sum(kept) / len(kept):.2f}")
""",
        # Strict inequalities at the fences drop the boundary value too.
        """import sys
import math

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
ordered = sorted(values)


def quantile(p):
    rank = min(max(math.ceil(p * n), 1), n)
    return float(ordered[rank - 1])


q1, q3 = quantile(0.25), quantile(0.75)
iqr = q3 - q1
kept = [v for v in values if q1 - 1.5 * iqr < v < q3 + 1.5 * iqr] or values
print(f"{len(values) - len(kept)} {sum(kept) / len(kept):.2f}")
""",
        # Linear-interpolation quantiles (numpy's default) are a different rule.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
ordered = sorted(values)


def quantile(p):
    if n == 1:
        return float(ordered[0])
    pos = p * (n - 1)
    low = int(pos)
    high = min(low + 1, n - 1)
    frac = pos - low
    return ordered[low] * (1 - frac) + ordered[high] * frac


q1, q3 = quantile(0.25), quantile(0.75)
iqr = q3 - q1
kept = [v for v in values if q1 - 1.5 * iqr <= v <= q3 + 1.5 * iqr]
print(f"{len(values) - len(kept)} {sum(kept) / len(kept):.2f}")
""",
    ],
)

_problem(
    id="an-clean-normalise-dates",
    title="Normalise Three Date Formats to ISO",
    skill_id="data_cleaning",
    concept="data types",
    difficulty=5,
    minutes=25,
    summary="Parse day-first and ISO dates, reject impossible ones, and output sorted ISO dates.",
    statement=(
        "Dates arrived in three shapes: `YYYY-MM-DD`, `DD/MM/YYYY` and "
        "`DD-MM-YYYY`. Note that the two-part-separator formats are "
        "**day first**, which is the trap: `03/04/2024` is 3 April, not 4 March."
        "\n\nConvert every parseable date to `YYYY-MM-DD` and print them sorted "
        "ascending, one per line, keeping duplicates. Then print a final line "
        "`invalid=k`, where `k` counts the rows that are not one of the three "
        "shapes or whose day or month is out of range (month 1-12, day 1-31; "
        "you do not need to validate month lengths)."
    ),
    input_format="Line 1: n. Next n lines: a raw date string, possibly padded.",
    output_format=(
        "Each valid date as YYYY-MM-DD on its own line, sorted ascending, then a "
        "final line `invalid=k`."
    ),
    constraints=[
        "1 <= n <= 20000",
        "Years are four digits",
        "Duplicated dates are printed as many times as they appear",
    ],
    requirements=[
        "Treat DD/MM/YYYY and DD-MM-YYYY as day first",
        "Accept YYYY-MM-DD as already ISO",
        "Count anything unparseable or out of range as invalid rather than guessing",
        "Print the valid dates sorted ascending, then the invalid count as 'invalid=k'",
    ],
    examples=[
        {
            "stdin": "4\n03/04/2024\n2024-01-02\n31-12-2023\nnot a date\n",
            "explanation": (
                "03/04/2024 is 3 April 2024. Sorted, the valid dates are "
                "2023-12-31, 2024-01-02 and 2024-04-03, and one row is invalid."
            ),
        }
    ],
    cases=[
        ("sample: one of each shape", "4\n03/04/2024\n2024-01-02\n31-12-2023\nnot a date\n", False),
        ("sample: day-first matters", "2\n04/03/2024\n03/04/2024\n", False),
        ("hidden: everything invalid", "3\n2024/13/01\n32-01-2024\n\n", True),
        ("hidden: duplicates are kept", "3\n01/02/2024\n2024-02-01\n01-02-2024\n", True),
        ("hidden: padded rows and single digits", "3\n  1/2/2024 \n2024-2-1\n 2024-02-01\n", True),
        ("hidden: month out of range", "3\n01/00/2024\n01/12/2024\n00/12/2024\n", True),
    ],
    reference="""import sys
import re

ISO = re.compile(r"^(\\d{4})-(\\d{1,2})-(\\d{1,2})$")
DAY_FIRST = re.compile(r"^(\\d{1,2})[/-](\\d{1,2})-?/?(\\d{4})$")
DAY_FIRST_SLASH = re.compile(r"^(\\d{1,2})/(\\d{1,2})/(\\d{4})$")
DAY_FIRST_DASH = re.compile(r"^(\\d{1,2})-(\\d{1,2})-(\\d{4})$")


def parse(raw):
    cell = raw.strip()
    match = ISO.match(cell)
    if match:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
    else:
        match = DAY_FIRST_SLASH.match(cell) or DAY_FIRST_DASH.match(cell)
        if not match:
            return None
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    valid = []
    invalid = 0
    for raw in data[1:1 + n]:
        parsed = parse(raw)
        if parsed is None:
            invalid += 1
        else:
            valid.append(parsed)
    for date in sorted(valid):
        print(date)
    print(f"invalid={invalid}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def parse(raw):
    # TODO: return the ISO form of the date, or None when it cannot be parsed.
    # Remember DD/MM/YYYY and DD-MM-YYYY are day first.
    return None


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    valid = []
    invalid = 0
    for raw in data[1:1 + n]:
        parsed = parse(raw)
        if parsed is None:
            invalid += 1
        else:
            valid.append(parsed)
    for date in sorted(valid):
        print(date)
    print(f"invalid={invalid}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Month first: the American reading of DD/MM/YYYY.
        """import sys
import re

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
valid = []
invalid = 0
for raw in data[1:1 + n]:
    cell = raw.strip()
    m = re.match(r"^(\\d{4})-(\\d{1,2})-(\\d{1,2})$", cell)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(r"^(\\d{1,2})[/-](\\d{1,2})[/-](\\d{4})$", cell)
        if not m:
            invalid += 1
            continue
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        invalid += 1
        continue
    valid.append(f"{y:04d}-{mo:02d}-{d:02d}")
for date in sorted(valid):
    print(date)
print(f"invalid={invalid}")
""",
        # No range validation, so month 13 and day 32 sail through.
        """import sys
import re

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
valid = []
invalid = 0
for raw in data[1:1 + n]:
    cell = raw.strip()
    m = re.match(r"^(\\d{4})-(\\d{1,2})-(\\d{1,2})$", cell)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(r"^(\\d{1,2})[/-](\\d{1,2})[/-](\\d{4})$", cell)
        if not m:
            invalid += 1
            continue
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    valid.append(f"{y:04d}-{mo:02d}-{d:02d}")
for date in sorted(valid):
    print(date)
print(f"invalid={invalid}")
""",
        # Zero-padding forgotten, so the strings sort wrongly.
        """import sys
import re

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
valid = []
invalid = 0
for raw in data[1:1 + n]:
    cell = raw.strip()
    m = re.match(r"^(\\d{4})-(\\d{1,2})-(\\d{1,2})$", cell)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(r"^(\\d{1,2})[/-](\\d{1,2})[/-](\\d{4})$", cell)
        if not m:
            invalid += 1
            continue
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        invalid += 1
        continue
    valid.append(f"{y}-{mo}-{d}")
for date in sorted(valid):
    print(date)
print(f"invalid={invalid}")
""",
    ],
)

_problem(
    id="an-clean-latest-per-key",
    title="Keep the Latest Record per Customer",
    skill_id="data_cleaning",
    concept="duplicates",
    difficulty=5,
    minutes=25,
    summary="Collapse an append-only change log to the current state of each key.",
    statement=(
        "An append-only export contains every change ever made, so a customer "
        "appears once per update. The current state is the row with the latest "
        "timestamp for that customer; where two rows for one customer share a "
        "timestamp, the one that appears **later in the file** wins, because "
        "the file is in write order.\n\n"
        "Print the current state of each customer as `key value`, sorted by key "
        "ascending."
    ),
    input_format=(
        "Line 1: n. Next n lines: `key,timestamp,value` where timestamp is an "
        "ISO datetime that sorts correctly as a string, and value has no comma."
    ),
    output_format="One line per key, `key value`, sorted by key ascending.",
    constraints=["1 <= n <= 20000", "Keys and values contain no commas"],
    requirements=[
        "Group rows by key and keep only the latest timestamp",
        "Break a timestamp tie in favour of the row that appears later in the file",
        "Print 'key value' per line, sorted by key ascending",
        "Every key in the input appears exactly once in the output",
    ],
    examples=[
        {
            "stdin": "4\nc1,2024-01-01T10:00,leeds\nc2,2024-01-01T09:00,oslo\nc1,2024-02-01T08:00,bristol\nc2,2024-01-01T09:00,cardiff\n",
            "explanation": (
                "c1's later timestamp gives bristol. c2's two rows share a "
                "timestamp, so the later line wins: cardiff."
            ),
        }
    ],
    cases=[
        ("sample: an update and a tie", "4\nc1,2024-01-01T10:00,leeds\nc2,2024-01-01T09:00,oslo\nc1,2024-02-01T08:00,bristol\nc2,2024-01-01T09:00,cardiff\n", False),
        ("sample: one row per key", "2\na,2024-01-01T00:00,x\nb,2024-01-02T00:00,y\n", False),
        ("hidden: latest row comes first in the file", "3\nk,2024-05-05T00:00,new\nk,2024-01-01T00:00,old\nk,2024-03-03T00:00,middle\n", True),
        ("hidden: keys sort, not insertion order", "4\nz,2024-01-01T00:00,zz\nm,2024-01-01T00:00,mm\na,2024-01-01T00:00,aa\nm,2024-06-01T00:00,m2\n", True),
        ("hidden: single row", "1\nonly,2024-01-01T00:00,v\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    latest = {}
    for line in data[1:1 + n]:
        key, timestamp, value = line.strip().split(",")
        current = latest.get(key)
        if current is None or timestamp >= current[0]:
            latest[key] = (timestamp, value)
    for key in sorted(latest):
        print(f"{key} {latest[key][1]}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def current_state(rows):
    # TODO: return {key: value} keeping the latest timestamp per key, with a
    # tie going to the later row in the file.
    return {key: value for key, _timestamp, value in rows}


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = [tuple(line.strip().split(",")) for line in data[1:1 + n]]
    state = current_state(rows)
    for key in sorted(state):
        print(f"{key} {state[key]}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Keeps the first row seen for each key.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
latest = {}
for line in data[1:1 + n]:
    key, timestamp, value = line.strip().split(",")
    if key not in latest:
        latest[key] = value
for key in sorted(latest):
    print(f"{key} {latest[key]}")
""",
        # Strictly-greater comparison loses the tie-break rule.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
latest = {}
for line in data[1:1 + n]:
    key, timestamp, value = line.strip().split(",")
    current = latest.get(key)
    if current is None or timestamp > current[0]:
        latest[key] = (timestamp, value)
for key in sorted(latest):
    print(f"{key} {latest[key][1]}")
""",
        # Correct values, printed in insertion order rather than sorted.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
latest = {}
for line in data[1:1 + n]:
    key, timestamp, value = line.strip().split(",")
    current = latest.get(key)
    if current is None or timestamp >= current[0]:
        latest[key] = (timestamp, value)
for key in latest:
    print(f"{key} {latest[key][1]}")
""",
    ],
)

_problem(
    id="an-clean-null-aware-average",
    title="Average Readings Without Treating NULL as Zero",
    skill_id="data_cleaning",
    concept="missing values",
    difficulty=4,
    minutes=22,
    summary="Per-sensor averages where a null reading must be skipped, not counted as 0.",
    statement=(
        "Each row is one reading from one sensor, and a failed read is recorded "
        "as `null`. Counting a failed read as zero is the mistake this question "
        "exists to catch: it silently halves a sensor's average.\n\n"
        "For each sensor print `sensor average`, averaging only its non-null "
        "readings and rounding to two decimal places, sorted by sensor name. A "
        "sensor whose every reading is null has no average and must print "
        "`NA` in place of the number."
    ),
    input_format="Line 1: n. Next n lines: `sensor,reading` where reading is an integer or the literal `null`.",
    output_format="One line per sensor, `sensor average` (two decimals) or `sensor NA`, sorted by sensor name.",
    constraints=["1 <= n <= 20000", "-10000 <= reading <= 10000"],
    requirements=[
        "Skip null readings rather than treating them as zero",
        "Divide by the number of non-null readings, not by the number of rows",
        "Print NA for a sensor with no usable reading",
        "Sort the output by sensor name ascending",
    ],
    examples=[
        {
            "stdin": "5\ns1,10\ns1,null\ns1,20\ns2,null\ns2,null\n",
            "explanation": (
                "s1 has two usable readings averaging 15.00. Every s2 reading "
                "failed, so it prints NA."
            ),
        }
    ],
    cases=[
        ("sample: one sensor all null", "5\ns1,10\ns1,null\ns1,20\ns2,null\ns2,null\n", False),
        ("sample: no nulls", "3\na,4\na,6\nb,5\n", False),
        ("hidden: nulls change the divisor", "4\nx,10\nx,null\nx,null\nx,null\n", True),
        ("hidden: negative readings", "4\nn,-10\nn,-20\nn,null\nm,0\n", True),
        ("hidden: rounding to two places", "3\nr,1\nr,1\nr,2\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    totals = {}
    for line in data[1:1 + n]:
        sensor, reading = line.strip().split(",")
        total, count = totals.get(sensor, (0, 0))
        if reading != "null":
            total += int(reading)
            count += 1
        totals[sensor] = (total, count)
    for sensor in sorted(totals):
        total, count = totals[sensor]
        if count == 0:
            print(f"{sensor} NA")
        else:
            print(f"{sensor} {total / count:.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def average(readings):
    # TODO: average the non-null readings, or return None when there are none.
    return 0.0


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    grouped = {}
    for line in data[1:1 + n]:
        sensor, reading = line.strip().split(",")
        grouped.setdefault(sensor, []).append(reading)
    for sensor in sorted(grouped):
        value = average(grouped[sensor])
        print(f"{sensor} NA" if value is None else f"{sensor} {value:.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # null counted as zero.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
grouped = {}
for line in data[1:1 + n]:
    sensor, reading = line.strip().split(",")
    grouped.setdefault(sensor, []).append(0 if reading == "null" else int(reading))
for sensor in sorted(grouped):
    values = grouped[sensor]
    print(f"{sensor} {sum(values) / len(values):.2f}")
""",
        # Right numerator, wrong denominator: divides by every row.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
grouped = {}
for line in data[1:1 + n]:
    sensor, reading = line.strip().split(",")
    grouped.setdefault(sensor, []).append(reading)
for sensor in sorted(grouped):
    values = grouped[sensor]
    usable = [int(v) for v in values if v != "null"]
    if not usable:
        print(f"{sensor} NA")
    else:
        print(f"{sensor} {sum(usable) / len(values):.2f}")
""",
        # An all-null sensor prints 0.00 instead of NA.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
grouped = {}
for line in data[1:1 + n]:
    sensor, reading = line.strip().split(",")
    grouped.setdefault(sensor, []).append(reading)
for sensor in sorted(grouped):
    usable = [int(v) for v in grouped[sensor] if v != "null"]
    mean = sum(usable) / len(usable) if usable else 0.0
    print(f"{sensor} {mean:.2f}")
""",
    ],
)

_problem(
    id="an-clean-range-validation",
    title="Validate a Column Against Its Allowed Range",
    skill_id="data_cleaning",
    concept="data types",
    difficulty=3,
    minutes=20,
    summary="Flag the rows whose age or score falls outside the documented bounds.",
    statement=(
        "The data dictionary says `age` is between 0 and 120 inclusive and "
        "`score` is between 0 and 100 inclusive. A row is invalid when either "
        "value falls outside its range — the bounds themselves are valid.\n\n"
        "Print how many rows are valid, then the ids of the invalid rows in "
        "ascending numeric order, space separated on one line. When every row "
        "is valid, print `none` on that second line."
    ),
    input_format="Line 1: n. Next n lines: `id,age,score`, all integers.",
    output_format=(
        "Line 1: the count of valid rows.\nLine 2: the invalid ids ascending, "
        "space separated, or `none`."
    ),
    constraints=["1 <= n <= 20000", "1 <= id <= 1000000", "-1000 <= age, score <= 1000"],
    requirements=[
        "Treat the bounds as inclusive: age 0 and 120, score 0 and 100 are all valid",
        "A row is invalid when either column is out of range",
        "Print the valid count, then the invalid ids ascending",
        "Print 'none' when there are no invalid rows",
    ],
    examples=[
        {
            "stdin": "4\n7,30,90\n3,130,50\n9,40,101\n1,0,100\n",
            "explanation": (
                "Ids 7 and 1 are inside both ranges; id 3 has an impossible age "
                "and id 9 an impossible score, so they are listed ascending."
            ),
        }
    ],
    cases=[
        ("sample: one bad age, one bad score", "4\n7,30,90\n3,130,50\n9,40,101\n1,0,100\n", False),
        ("sample: all valid", "2\n5,10,10\n6,120,0\n", False),
        ("hidden: bounds are inclusive", "4\n1,0,0\n2,120,100\n3,-1,50\n4,50,-1\n", True),
        ("hidden: every row invalid", "3\n30,121,50\n20,50,101\n10,-5,-5\n", True),
        ("hidden: ids are sorted numerically not as text", "3\n100,200,50\n9,200,50\n50,10,10\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    valid = 0
    invalid = []
    for line in data[1:1 + n]:
        row_id, age, score = (int(x) for x in line.strip().split(","))
        if 0 <= age <= 120 and 0 <= score <= 100:
            valid += 1
        else:
            invalid.append(row_id)
    print(valid)
    print(" ".join(str(i) for i in sorted(invalid)) if invalid else "none")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def is_valid(age, score):
    # TODO: age must be 0..120 inclusive and score 0..100 inclusive.
    return True


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    valid = 0
    invalid = []
    for line in data[1:1 + n]:
        row_id, age, score = (int(x) for x in line.strip().split(","))
        if is_valid(age, score):
            valid += 1
        else:
            invalid.append(row_id)
    print(valid)
    print(" ".join(str(i) for i in sorted(invalid)) if invalid else "none")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Exclusive bounds reject the legal boundary values.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
valid = 0
invalid = []
for line in data[1:1 + n]:
    row_id, age, score = (int(x) for x in line.strip().split(","))
    if 0 < age < 120 and 0 < score < 100:
        valid += 1
    else:
        invalid.append(row_id)
print(valid)
print(" ".join(str(i) for i in sorted(invalid)) if invalid else "none")
""",
        # Only checks the age column.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
valid = 0
invalid = []
for line in data[1:1 + n]:
    row_id, age, score = (int(x) for x in line.strip().split(","))
    if 0 <= age <= 120:
        valid += 1
    else:
        invalid.append(row_id)
print(valid)
print(" ".join(str(i) for i in sorted(invalid)) if invalid else "none")
""",
        # Sorts the ids as text, so 100 comes before 9.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
valid = 0
invalid = []
for line in data[1:1 + n]:
    parts = line.strip().split(",")
    age, score = int(parts[1]), int(parts[2])
    if 0 <= age <= 120 and 0 <= score <= 100:
        valid += 1
    else:
        invalid.append(parts[0])
print(valid)
print(" ".join(sorted(invalid)) if invalid else "none")
""",
    ],
)

_problem(
    id="an-clean-currency-to-pence",
    title="Parse a Currency Column Into Pence",
    skill_id="data_cleaning",
    concept="type coercion",
    difficulty=6,
    minutes=28,
    summary="Thousands separators, accounting negatives and a dash for zero — totalled in integer pence.",
    statement=(
        "A finance export writes money as text: `£1,234.50`, `-£5.00`, and "
        "accounting-style `(£5.00)` which also means negative five pounds. A "
        "lone `-` means zero. There may be exactly two decimal places or none "
        "at all.\n\n"
        "Total the column and print the result in **integer pence**. Work in "
        "pence rather than floats: `0.1 + 0.2` is not `0.3` in binary floating "
        "point, and a penny of drift in a reconciliation is a real defect."
    ),
    input_format=(
        "Line 1: n. Next n lines: one money cell, possibly padded. Each cell is "
        "`£X`, `£X.YY`, optionally with a leading `-` or wrapped in "
        "parentheses, with `,` used as a thousands separator — or a lone `-`."
    ),
    output_format="One line: the total in pence, as an integer (which may be negative).",
    constraints=[
        "1 <= n <= 20000",
        "Every cell is well formed as described",
        "The total fits in a 64-bit integer",
    ],
    requirements=[
        "Strip the currency symbol and thousands separators before parsing",
        "Treat both -£X and (£X) as negative",
        "Treat a lone '-' as zero",
        "Accumulate in integer pence, not in floating point",
    ],
    examples=[
        {
            "stdin": "4\n£1,234.50\n(£5.00)\n-\n-£0.50\n",
            "explanation": (
                "123450 pence, minus 500, plus nothing, minus 50 gives 122900."
            ),
        }
    ],
    cases=[
        ("sample: separator, brackets and a dash", "4\n£1,234.50\n(£5.00)\n-\n-£0.50\n", False),
        ("sample: whole pounds", "3\n£10\n£2\n-£3\n", False),
        ("hidden: accounting negatives only", "3\n(£0.01)\n(£0.02)\n(£1,000.00)\n", True),
        ("hidden: totals to zero", "2\n£12.34\n(£12.34)\n", True),
        ("hidden: pennies that float arithmetic gets wrong", "3\n£0.10\n£0.20\n£0.01\n", True),
        # 1.29 + 2.73 is 4.0199999999999996 as a float, so int(total * 100)
        # reports 401p for what is really 402p.
        ("hidden: float drift loses a penny", "2\n£1.29\n£2.73\n", True),
        ("hidden: padded cells", "3\n  £1.05 \n\t-£0.05\n £1,000 \n", True),
    ],
    reference="""import sys


def to_pence(raw):
    cell = raw.strip()
    if cell == "-":
        return 0
    negative = False
    if cell.startswith("(") and cell.endswith(")"):
        negative = True
        cell = cell[1:-1]
    if cell.startswith("-"):
        negative = True
        cell = cell[1:]
    cell = cell.replace("£", "").replace(",", "").strip()
    if "." in cell:
        pounds, pence = cell.split(".")
        total = int(pounds) * 100 + int(pence)
    else:
        total = int(cell) * 100
    return -total if negative else total


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    print(sum(to_pence(line) for line in data[1:1 + n]))


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def to_pence(raw):
    # TODO: return the cell as an integer number of pence, honouring -£X,
    # (£X), thousands separators and the lone '-'.
    return 0


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    print(sum(to_pence(line) for line in data[1:1 + n]))


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Parentheses not treated as negative.
        """import sys


def to_pence(raw):
    cell = raw.strip().replace("(", "").replace(")", "")
    if cell == "-":
        return 0
    negative = cell.startswith("-")
    cell = cell.lstrip("-").replace("\\u00a3", "").replace(",", "")
    if "." in cell:
        pounds, pence = cell.split(".")
        total = int(pounds) * 100 + int(pence)
    else:
        total = int(cell) * 100
    return -total if negative else total


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
print(sum(to_pence(line) for line in data[1:1 + n]))
""",
        # Float accumulation, then a truncating conversion to pence.
        """import sys


def to_pounds(raw):
    cell = raw.strip()
    if cell == "-":
        return 0.0
    negative = False
    if cell.startswith("(") and cell.endswith(")"):
        negative = True
        cell = cell[1:-1]
    if cell.startswith("-"):
        negative = True
        cell = cell[1:]
    value = float(cell.replace("\\u00a3", "").replace(",", ""))
    return -value if negative else value


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
total = sum(to_pounds(line) for line in data[1:1 + n])
print(int(total * 100))
""",
        # Thousands separator left in, so £1,234.50 loses its thousands.
        """import sys


def to_pence(raw):
    cell = raw.strip()
    if cell == "-":
        return 0
    negative = False
    if cell.startswith("(") and cell.endswith(")"):
        negative = True
        cell = cell[1:-1]
    if cell.startswith("-"):
        negative = True
        cell = cell[1:]
    cell = cell.replace("\\u00a3", "")
    cell = cell.split(",")[-1]
    if "." in cell:
        pounds, pence = cell.split(".")
        total = int(pounds) * 100 + int(pence)
    else:
        total = int(cell) * 100
    return -total if negative else total


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
print(sum(to_pence(line) for line in data[1:1 + n]))
""",
    ],
)


# =========================================================================== #
#  exploratory_analysis                                                       #
# =========================================================================== #

_problem(
    id="an-eda-summary-stats",
    title="Summarise a Column",
    skill_id="exploratory_analysis",
    concept="distribution",
    difficulty=3,
    minutes=18,
    summary="Minimum, median and maximum — the three numbers to look at before anything else.",
    statement=(
        "Print the minimum, the median and the maximum of a column, in that "
        "order, each to two decimal places, space separated.\n\n"
        "The median of an even number of values is the average of the two "
        "middle values of the sorted list."
    ),
    input_format="Line 1: n. Line 2: n space-separated integers.",
    output_format="One line: min, median and max, each to two decimal places, space separated.",
    constraints=["1 <= n <= 20000", "-1000000 <= value <= 1000000"],
    requirements=[
        "Print the minimum, then the median, then the maximum",
        "Average the two middle values when n is even",
        "Print each number to exactly two decimal places",
    ],
    examples=[
        {
            "stdin": "4\n4 1 9 6\n",
            "explanation": "Sorted: 1 4 6 9. The middle two are 4 and 6, so the median is 5.00.",
        }
    ],
    cases=[
        ("sample: even count", "4\n4 1 9 6\n", False),
        ("sample: odd count", "5\n10 2 8 4 6\n", False),
        ("hidden: single value", "1\n7\n", True),
        ("hidden: negatives and a wide range", "6\n-100 -1 0 1 2 1000\n", True),
        ("hidden: mean differs from median", "5\n1 1 1 1 100\n", True),
        ("hidden: duplicates in the middle", "4\n5 5 5 100\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = sorted(int(x) for x in data[1:1 + n])
    mid = n // 2
    median = float(values[mid]) if n % 2 else (values[mid - 1] + values[mid]) / 2.0
    print(f"{values[0]:.2f} {median:.2f} {values[-1]:.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def summarise(values):
    # TODO: return (minimum, median, maximum) as floats.
    return 0.0, 0.0, 0.0


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    low, median, high = summarise(values)
    print(f"{low:.2f} {median:.2f} {high:.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Mean dressed up as the median.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = sorted(int(x) for x in data[1:1 + n])
print(f"{values[0]:.2f} {sum(values) / n:.2f} {values[-1]:.2f}")
""",
        # Upper middle value for an even count.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = sorted(int(x) for x in data[1:1 + n])
print(f"{values[0]:.2f} {float(values[n // 2]):.2f} {values[-1]:.2f}")
""",
        # Min and max taken from the unsorted input order.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
ordered = sorted(values)
mid = n // 2
median = float(ordered[mid]) if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2.0
print(f"{values[0]:.2f} {median:.2f} {values[-1]:.2f}")
""",
    ],
)

_problem(
    id="an-eda-group-revenue",
    title="Revenue by Category, Biggest First",
    skill_id="exploratory_analysis",
    concept="segmentation",
    difficulty=3,
    minutes=20,
    summary="Group, total, and rank — with an explicit tiebreak so the ordering is not luck.",
    statement=(
        "Group the rows by category and total the amounts. Print `category "
        "total` per line, ordered by total **descending**; where two categories "
        "tie on total, the one whose name sorts first alphabetically comes "
        "first. Print each total to two decimal places."
    ),
    input_format="Line 1: n. Next n lines: `category,amount` where amount has at most two decimal places.",
    output_format="One line per category: the name, a space, then the total to two decimal places.",
    constraints=["1 <= n <= 20000", "0 <= amount <= 100000", "Category names contain no commas"],
    requirements=[
        "Total the amounts per category",
        "Order by total descending, then by category name ascending",
        "Print each total to exactly two decimal places",
        "Every category in the input appears exactly once in the output",
    ],
    examples=[
        {
            "stdin": "4\nfurniture,320.00\naccessories,24.50\nfurniture,210.00\naccessories,89.99\n",
            "explanation": (
                "Furniture totals 530.00 and accessories 114.49, so furniture is "
                "printed first."
            ),
        }
    ],
    cases=[
        ("sample: two categories", "4\nfurniture,320.00\naccessories,24.50\nfurniture,210.00\naccessories,89.99\n", False),
        ("sample: single row", "1\nsolo,10.00\n", False),
        ("hidden: tie broken by name", "4\nzebra,50.00\nalpha,25.00\nalpha,25.00\nmid,10.00\n", True),
        ("hidden: alphabetical order is not total order", "3\naaa,1.00\nbbb,99.00\nccc,50.00\n", True),
        ("hidden: zero amounts still make a category", "3\nnil,0.00\nnil,0.00\nsome,0.01\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    totals = {}
    for line in data[1:1 + n]:
        category, amount = line.strip().rsplit(",", 1)
        totals[category] = totals.get(category, 0) + round(float(amount) * 100)
    for category, pence in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{category} {pence / 100:.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def ranked_totals(rows):
    # TODO: total the amounts per category and return [(category, total), ...]
    # ordered by total descending, then category name ascending.
    return []


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = [line.strip().rsplit(",", 1) for line in data[1:1 + n]]
    for category, total in ranked_totals(rows):
        print(f"{category} {total:.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Sorted by name rather than by total.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
totals = {}
for line in data[1:1 + n]:
    category, amount = line.strip().rsplit(",", 1)
    totals[category] = totals.get(category, 0.0) + float(amount)
for category in sorted(totals):
    print(f"{category} {totals[category]:.2f}")
""",
        # Descending totals but the tie broken by name descending.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
totals = {}
for line in data[1:1 + n]:
    category, amount = line.strip().rsplit(",", 1)
    totals[category] = totals.get(category, 0.0) + float(amount)
for category, total in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]), reverse=True):
    print(f"{category} {total:.2f}")
""",
        # Counts the rows instead of summing the amounts.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
totals = {}
for line in data[1:1 + n]:
    category, amount = line.strip().rsplit(",", 1)
    totals[category] = totals.get(category, 0) + 1
for category, total in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0])):
    print(f"{category} {float(total):.2f}")
""",
    ],
)

_problem(
    id="an-eda-pivot-table",
    title="Pivot Regions Against Months",
    skill_id="exploratory_analysis",
    concept="pivot",
    difficulty=6,
    minutes=28,
    summary="A rectangular pivot: every region gets a cell for every month, including the empty ones.",
    statement=(
        "Build a pivot of order counts with one row per region and one column "
        "per month.\n\n"
        "The first output line is `region` followed by every month that appears "
        "anywhere in the data, sorted ascending. Then one line per region, "
        "sorted by region name ascending, holding the region name followed by "
        "its count for each of those months **in the same column order** — and "
        "`0` where that region has nothing in that month. A pivot with ragged "
        "rows is not a pivot. Separate every field with a single space."
    ),
    input_format="Line 1: n. Next n lines: `region,month` where month is `YYYY-MM`.",
    output_format=(
        "Line 1: `region` then the sorted months. Then one line per region with "
        "its count per month, zero-filled."
    ),
    constraints=["1 <= n <= 20000", "Region names contain no commas or spaces"],
    requirements=[
        "Print a header row of the sorted distinct months, prefixed by 'region'",
        "Print one row per region, sorted by region name ascending",
        "Fill a region/month combination with 0 when it has no rows",
        "Keep the columns in the same order as the header",
    ],
    examples=[
        {
            "stdin": "4\nemea,2024-02\napac,2024-01\nemea,2024-01\nemea,2024-02\n",
            "explanation": (
                "Two months appear. apac has nothing in 2024-02, so that cell is "
                "0 rather than missing."
            ),
        }
    ],
    cases=[
        ("sample: one empty cell", "4\nemea,2024-02\napac,2024-01\nemea,2024-01\nemea,2024-02\n", False),
        ("sample: one region one month", "2\nsolo,2024-05\nsolo,2024-05\n", False),
        ("hidden: fully sparse grid", "3\na,2024-01\nb,2024-02\nc,2024-03\n", True),
        ("hidden: months sort, input order does not", "4\nr,2024-12\nr,2024-02\nq,2024-07\nq,2024-02\n", True),
        ("hidden: many rows in one cell", "5\nx,2024-01\nx,2024-01\nx,2024-01\ny,2024-01\nx,2024-02\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    counts = {}
    months = set()
    regions = set()
    for line in data[1:1 + n]:
        region, month = line.strip().split(",")
        counts[(region, month)] = counts.get((region, month), 0) + 1
        months.add(month)
        regions.add(region)
    ordered_months = sorted(months)
    print(" ".join(["region", *ordered_months]))
    for region in sorted(regions):
        cells = [str(counts.get((region, month), 0)) for month in ordered_months]
        print(" ".join([region, *cells]))


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def pivot(rows):
    # TODO: return (ordered_months, {(region, month): count}) so the grid below
    # can be printed with a zero in every empty cell.
    return [], {}


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = [tuple(line.strip().split(",")) for line in data[1:1 + n]]
    months, counts = pivot(rows)
    print(" ".join(["region", *months]))
    for region in sorted({region for region, _month in rows}):
        print(" ".join([region, *[str(counts.get((region, m), 0)) for m in months]]))


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Ragged rows: only the months that region actually has.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
counts = {}
months = set()
for line in data[1:1 + n]:
    region, month = line.strip().split(",")
    counts.setdefault(region, {})
    counts[region][month] = counts[region].get(month, 0) + 1
    months.add(month)
ordered = sorted(months)
print(" ".join(["region", *ordered]))
for region in sorted(counts):
    print(" ".join([region, *[str(v) for v in counts[region].values()]]))
""",
        # Months in first-seen order rather than sorted.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
counts = {}
months = []
regions = []
for line in data[1:1 + n]:
    region, month = line.strip().split(",")
    if month not in months:
        months.append(month)
    if region not in regions:
        regions.append(region)
    counts[(region, month)] = counts.get((region, month), 0) + 1
print(" ".join(["region", *months]))
for region in sorted(regions):
    print(" ".join([region, *[str(counts.get((region, m), 0)) for m in months]]))
""",
        # Marks presence instead of counting.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
seen = set()
months = set()
regions = set()
for line in data[1:1 + n]:
    region, month = line.strip().split(",")
    seen.add((region, month))
    months.add(month)
    regions.add(region)
ordered = sorted(months)
print(" ".join(["region", *ordered]))
for region in sorted(regions):
    print(" ".join([region, *["1" if (region, m) in seen else "0" for m in ordered]]))
""",
    ],
)

def _correlation_scale_stdin() -> str:
    """A full-size input for the correlation question.

    Every other case here is a handful of numbers, so nothing exercised the
    stated `n <= 20000` at all. Measured, at n = 20000 against a 10s limit:

    * the linear reference finishes in ~200ms;
    * recomputing the means with explicit Python loops inside the multiply loop
      times out, so that shape of quadratic is rejected;
    * recomputing them with `sum()` inside the loop still passes in ~3s. It is
      the same 4 * 10^8 additions, but `sum` runs them in C. Do not read this
      case as a complexity gate — it is not one, and this question states no
      complexity requirement to enforce. Rejecting that version would need a
      larger n than the declared constraint allows.

    `y = 2x` makes r exactly 1, so the expected value sits nowhere near a
    rounding boundary and no correct implementation can disagree at three
    decimal places because it summed in a different order. x stays within
    [-5000, 5000] so that y stays inside the declared [-10000, 10000].
    """
    n = 20000
    xs = [(i % 10001) - 5000 for i in range(n)]
    ys = [2 * x for x in xs]
    return f"{n}\n" + " ".join(map(str, xs)) + "\n" + " ".join(map(str, ys)) + "\n"


_problem(
    id="an-eda-correlation",
    title="Correlation Between Two Columns",
    skill_id="exploratory_analysis",
    concept="correlation",
    difficulty=7,
    minutes=30,
    summary="Pearson's r, with the degenerate zero-variance case reported rather than crashed.",
    statement=(
        "Compute the Pearson correlation coefficient between two columns and "
        "print it to three decimal places.\n\n"
        "`r` is the covariance of the two columns divided by the product of "
        "their standard deviations — equivalently\n\n"
        "    r = sum((x - mean_x) * (y - mean_y)) / sqrt(sum((x - mean_x)^2) * sum((y - mean_y)^2))\n\n"
        "When either column has zero variance (every value the same), `r` is "
        "undefined: print `undefined` instead of a number. Do not divide by "
        "zero, and do not skip the centring — the uncentred version of this "
        "formula is a different statistic that happens to look similar."
    ),
    input_format="Line 1: n. Line 2: n space-separated integers (x). Line 3: n space-separated integers (y).",
    output_format="One line: r to three decimal places, or the word `undefined`.",
    constraints=["1 <= n <= 20000", "-10000 <= x, y <= 10000"],
    requirements=[
        "Centre both columns on their means before multiplying",
        "Divide by the square root of the product of the centred sums of squares",
        "Print `undefined` when either column has zero variance",
        "Print r to exactly three decimal places otherwise",
    ],
    examples=[
        {
            "stdin": "4\n1 2 3 4\n2 4 6 8\n",
            "explanation": "y is exactly 2x, a perfect positive relationship, so r is 1.000.",
        }
    ],
    cases=[
        ("sample: perfectly correlated", "4\n1 2 3 4\n2 4 6 8\n", False),
        ("sample: perfectly anti-correlated", "4\n1 2 3 4\n8 6 4 2\n", False),
        ("hidden: constant column is undefined", "3\n5 5 5\n1 2 3\n", True),
        ("hidden: single observation is undefined", "1\n3\n9\n", True),
        ("hidden: weak positive relationship", "6\n1 2 3 4 5 6\n2 1 4 3 6 5\n", True),
        ("hidden: uncentred formula gives a different answer", "5\n10 11 12 13 14\n1 3 2 5 4\n", True),
        ("hidden: negative values", "4\n-2 -1 1 2\n4 1 1 4\n", True),
        ("hidden: scale — compute the means once", _correlation_scale_stdin(), True),
    ],
    reference="""import sys
import math


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    xs = [int(v) for v in data[1:1 + n]]
    ys = [int(v) for v in data[1 + n:1 + 2 * n]]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    dx = [x - mean_x for x in xs]
    dy = [y - mean_y for y in ys]
    sxx = sum(v * v for v in dx)
    syy = sum(v * v for v in dy)
    if sxx == 0 or syy == 0:
        print("undefined")
        return
    r = sum(a * b for a, b in zip(dx, dy)) / math.sqrt(sxx * syy)
    print(f"{r:.3f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def correlation(xs, ys):
    # TODO: return Pearson's r, or None when either column has zero variance.
    return 0.0


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    xs = [int(v) for v in data[1:1 + n]]
    ys = [int(v) for v in data[1 + n:1 + 2 * n]]
    r = correlation(xs, ys)
    print("undefined" if r is None else f"{r:.3f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Uncentred: cosine similarity, not correlation.
        """import sys
import math

data = sys.stdin.read().split()
n = int(data[0])
xs = [int(v) for v in data[1:1 + n]]
ys = [int(v) for v in data[1 + n:1 + 2 * n]]
sxx = sum(x * x for x in xs)
syy = sum(y * y for y in ys)
if sxx == 0 or syy == 0:
    print("undefined")
else:
    print(f"{sum(x * y for x, y in zip(xs, ys)) / math.sqrt(sxx * syy):.3f}")
""",
        # No zero-variance guard: crashes (or reports nan) on a constant column.
        """import sys
import math

data = sys.stdin.read().split()
n = int(data[0])
xs = [int(v) for v in data[1:1 + n]]
ys = [int(v) for v in data[1 + n:1 + 2 * n]]
mean_x = sum(xs) / n
mean_y = sum(ys) / n
dx = [x - mean_x for x in xs]
dy = [y - mean_y for y in ys]
r = sum(a * b for a, b in zip(dx, dy)) / math.sqrt(sum(v * v for v in dx) * sum(v * v for v in dy))
print(f"{r:.3f}")
""",
        # Covariance, unnormalised.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
xs = [int(v) for v in data[1:1 + n]]
ys = [int(v) for v in data[1 + n:1 + 2 * n]]
mean_x = sum(xs) / n
mean_y = sum(ys) / n
cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / n
print(f"{cov:.3f}")
""",
    ],
)

_problem(
    id="an-eda-top-share",
    title="How Much of Revenue the Top Three Products Are",
    skill_id="exploratory_analysis",
    concept="segmentation",
    difficulty=5,
    minutes=25,
    summary="Rank products, take the top three, and express their combined revenue as a share of the whole.",
    statement=(
        "Total revenue per product, then print the top three products by "
        "revenue — one per line as `product revenue` with the revenue to two "
        "decimal places, largest first, ties broken by product name ascending. "
        "If there are fewer than three products, print all of them.\n\n"
        "Then print a final line: those products' combined share of **total "
        "revenue across every product**, as a percentage to one decimal place, "
        "in the form `share=NN.N`."
    ),
    input_format="Line 1: n. Next n lines: `product,revenue` with at most two decimal places.",
    output_format="Up to three `product revenue` lines, then `share=NN.N`.",
    constraints=["1 <= n <= 20000", "0 < revenue <= 100000"],
    requirements=[
        "Total revenue per product before ranking",
        "Order by revenue descending, breaking ties by product name ascending",
        "Print at most three products",
        "The share denominator is total revenue across all products, not just the top three",
    ],
    examples=[
        {
            "stdin": "5\na,100.00\nb,50.00\nc,25.00\nd,25.00\na,100.00\n",
            "explanation": (
                "a totals 200, then b 50, then c and d tie on 25 so c wins the "
                "third slot. 275 of 300 is 91.7%."
            ),
        }
    ],
    cases=[
        ("sample: a tie for third place", "5\na,100.00\nb,50.00\nc,25.00\nd,25.00\na,100.00\n", False),
        ("sample: only two products", "2\nx,10.00\ny,90.00\n", False),
        ("hidden: single product is the whole business", "1\nonly,42.50\n", True),
        ("hidden: long tail below the top three", "6\np1,10.00\np2,9.00\np3,8.00\np4,7.00\np5,6.00\np6,5.00\n", True),
        ("hidden: repeated rows per product", "6\nq,1.00\nq,1.00\nq,1.00\nr,2.00\ns,2.00\nt,0.50\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    totals = {}
    for line in data[1:1 + n]:
        product, revenue = line.strip().rsplit(",", 1)
        totals[product] = totals.get(product, 0) + round(float(revenue) * 100)
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    top = ranked[:3]
    for product, pence in top:
        print(f"{product} {pence / 100:.2f}")
    overall = sum(totals.values())
    share = sum(pence for _product, pence in top) * 100.0 / overall
    print(f"share={share:.1f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def ranked_totals(rows):
    # TODO: total revenue per product and return [(product, total), ...] with
    # the biggest first, ties broken by product name ascending.
    return []


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = [line.strip().rsplit(",", 1) for line in data[1:1 + n]]
    ranked = ranked_totals(rows)
    top = ranked[:3]
    for product, total in top:
        print(f"{product} {total:.2f}")
    overall = sum(total for _product, total in ranked)
    print(f"share={sum(t for _p, t in top) * 100.0 / overall:.1f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Share of the top three within themselves: always 100%.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
totals = {}
for line in data[1:1 + n]:
    product, revenue = line.strip().rsplit(",", 1)
    totals[product] = totals.get(product, 0.0) + float(revenue)
ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
top = ranked[:3]
for product, total in top:
    print(f"{product} {total:.2f}")
denominator = sum(t for _p, t in top)
print(f"share={sum(t for _p, t in top) * 100.0 / denominator:.1f}")
""",
        # Ranks the raw rows instead of the per-product totals.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rows = []
for line in data[1:1 + n]:
    product, revenue = line.strip().rsplit(",", 1)
    rows.append((product, float(revenue)))
ranked = sorted(rows, key=lambda kv: (-kv[1], kv[0]))
top = ranked[:3]
for product, total in top:
    print(f"{product} {total:.2f}")
overall = sum(t for _p, t in rows)
print(f"share={sum(t for _p, t in top) * 100.0 / overall:.1f}")
""",
        # Ties broken by name descending.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
totals = {}
for line in data[1:1 + n]:
    product, revenue = line.strip().rsplit(",", 1)
    totals[product] = totals.get(product, 0.0) + float(revenue)
ranked = sorted(sorted(totals.items(), key=lambda kv: kv[0], reverse=True), key=lambda kv: -kv[1])
top = ranked[:3]
for product, total in top:
    print(f"{product} {total:.2f}")
overall = sum(totals.values())
print(f"share={sum(t for _p, t in top) * 100.0 / overall:.1f}")
""",
    ],
)

_problem(
    id="an-eda-cohort-retention",
    title="Cohort Retention From an Activity Log",
    skill_id="exploratory_analysis",
    concept="cohort",
    difficulty=7,
    minutes=32,
    summary="Assign each user to the cohort of their first active month, then measure who came back later.",
    statement=(
        "Each row says a user was active in a month. A user's **cohort** is the "
        "earliest month they appear in. A user is **retained** when they are "
        "also active in some month strictly later than their cohort month.\n\n"
        "For each cohort, print `month size retained pct` where `size` is the "
        "number of distinct users in the cohort, `retained` is how many of them "
        "were retained, and `pct` is `retained / size` as a percentage to one "
        "decimal place. Sort by cohort month ascending. Count **users**, not "
        "rows: a user active three times in one month is one user."
    ),
    input_format="Line 1: n. Next n lines: `user,month` where month is `YYYY-MM`. Rows may repeat.",
    output_format="One line per cohort month: `month size retained pct`, sorted by month ascending.",
    constraints=["1 <= n <= 20000", "User ids contain no commas"],
    requirements=[
        "A user's cohort is their earliest month, not their first row in the file",
        "Count distinct users per cohort, not rows",
        "A user is retained only if active in a strictly later month than their cohort",
        "Print the percentage to one decimal place, sorted by cohort month ascending",
    ],
    examples=[
        {
            "stdin": "5\nu1,2024-02\nu1,2024-01\nu2,2024-01\nu1,2024-03\nu3,2024-02\n",
            "explanation": (
                "u1's earliest month is 2024-01 even though it is the second "
                "row, and it returned later, so the 2024-01 cohort of two users "
                "retained one. u3 joined in 2024-02 and never came back."
            ),
        }
    ],
    cases=[
        ("sample: earliest month is not the first row", "5\nu1,2024-02\nu1,2024-01\nu2,2024-01\nu1,2024-03\nu3,2024-02\n", False),
        ("sample: nobody comes back", "2\na,2024-01\nb,2024-02\n", False),
        ("hidden: repeats within the cohort month are not retention", "4\nx,2024-01\nx,2024-01\nx,2024-01\ny,2024-01\n", True),
        ("hidden: everyone is retained", "4\np,2024-01\np,2024-02\nq,2024-01\nq,2024-05\n", True),
        ("hidden: several cohorts", "7\na,2024-01\na,2024-02\nb,2024-01\nc,2024-02\nc,2024-03\nd,2024-03\ne,2024-03\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    months_by_user = {}
    for line in data[1:1 + n]:
        user, month = line.strip().split(",")
        months_by_user.setdefault(user, set()).add(month)
    cohorts = {}
    for user, months in months_by_user.items():
        cohort = min(months)
        size, retained = cohorts.get(cohort, (0, 0))
        came_back = any(m > cohort for m in months)
        cohorts[cohort] = (size + 1, retained + (1 if came_back else 0))
    for month in sorted(cohorts):
        size, retained = cohorts[month]
        print(f"{month} {size} {retained} {retained * 100.0 / size:.1f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def cohorts(rows):
    # TODO: return {cohort_month: (size, retained)} where the cohort is each
    # user's earliest month and retained counts users active in a later month.
    return {}


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = [tuple(line.strip().split(",")) for line in data[1:1 + n]]
    table = cohorts(rows)
    for month in sorted(table):
        size, retained = table[month]
        print(f"{month} {size} {retained} {retained * 100.0 / size:.1f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Cohort taken from the first row seen rather than the earliest month.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
first = {}
months_by_user = {}
for line in data[1:1 + n]:
    user, month = line.strip().split(",")
    first.setdefault(user, month)
    months_by_user.setdefault(user, set()).add(month)
cohorts = {}
for user, cohort in first.items():
    size, retained = cohorts.get(cohort, (0, 0))
    came_back = any(m > cohort for m in months_by_user[user])
    cohorts[cohort] = (size + 1, retained + (1 if came_back else 0))
for month in sorted(cohorts):
    size, retained = cohorts[month]
    print(f"{month} {size} {retained} {retained * 100.0 / size:.1f}")
""",
        # Counts rows, so a user with three rows in one month looks like three.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rows = [tuple(line.strip().split(",")) for line in data[1:1 + n]]
months_by_user = {}
for user, month in rows:
    months_by_user.setdefault(user, set()).add(month)
cohorts = {}
for user, month in rows:
    cohort = min(months_by_user[user])
    size, retained = cohorts.get(cohort, (0, 0))
    came_back = any(m > cohort for m in months_by_user[user])
    cohorts[cohort] = (size + 1, retained + (1 if came_back else 0))
for month in sorted(cohorts):
    size, retained = cohorts[month]
    print(f"{month} {size} {retained} {retained * 100.0 / size:.1f}")
""",
        # Any second row counts as retention, even in the same month.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
seen = {}
for line in data[1:1 + n]:
    user, month = line.strip().split(",")
    seen.setdefault(user, []).append(month)
cohorts = {}
for user, months in seen.items():
    cohort = min(months)
    size, retained = cohorts.get(cohort, (0, 0))
    cohorts[cohort] = (size + 1, retained + (1 if len(months) > 1 else 0))
for month in sorted(cohorts):
    size, retained = cohorts[month]
    print(f"{month} {size} {retained} {retained * 100.0 / size:.1f}")
""",
    ],
)

_problem(
    id="an-eda-histogram",
    title="Bucket a Column Into a Histogram",
    skill_id="exploratory_analysis",
    concept="distribution",
    difficulty=5,
    minutes=25,
    summary="Fixed-width buckets, half-open on the right, with the empty buckets in the middle still printed.",
    statement=(
        "Bucket the values into fixed-width buckets of width `w`. Bucket `k` "
        "covers `[k*w, (k+1)*w)` — the lower bound is included and the upper "
        "bound is not, which is what stops a value being counted twice.\n\n"
        "Print one line per bucket from the bucket containing the smallest "
        "value to the bucket containing the largest, in ascending order, as "
        "`lo-hi count` where `lo` and `hi` are the bucket bounds. **Buckets in "
        "the middle with a count of zero are still printed** — a histogram with "
        "holes in it lies about the shape of the distribution."
    ),
    input_format="Line 1: n and w separated by a space. Line 2: n space-separated integers.",
    output_format="One line per bucket: `lo-hi count`.",
    constraints=["1 <= n <= 20000", "1 <= w <= 1000", "-1000000 <= value <= 1000000"],
    requirements=[
        "Buckets are half-open: [k*w, (k+1)*w)",
        "Cover every bucket from the minimum value's bucket to the maximum value's bucket",
        "Print zero-count buckets in the middle of the range",
        "Handle negative values, where the bucket index floors towards minus infinity",
    ],
    examples=[
        {
            "stdin": "5 10\n1 9 10 25 26\n",
            "explanation": (
                "Bucket 0 [0,10) holds 1 and 9; bucket 1 [10,20) holds 10; "
                "bucket 2 [20,30) holds 25 and 26. The 10 is in the second "
                "bucket, not the first, because the upper bound is exclusive."
            ),
        }
    ],
    cases=[
        ("sample: boundary value goes up a bucket", "5 10\n1 9 10 25 26\n", False),
        ("sample: one value", "1 5\n7\n", False),
        ("hidden: empty bucket in the middle", "3 10\n1 2 45\n", True),
        ("hidden: negative values floor downwards", "4 10\n-1 -10 -11 5\n", True),
        ("hidden: width one", "3 1\n3 4 4\n", True),
        ("hidden: everything in one bucket", "4 100\n10 20 30 99\n", True),
    ],
    reference="""import sys
import math


def main():
    data = sys.stdin.read().split()
    n, w = int(data[0]), int(data[1])
    values = [int(x) for x in data[2:2 + n]]
    counts = {}
    for value in values:
        k = math.floor(value / w)
        counts[k] = counts.get(k, 0) + 1
    low = math.floor(min(values) / w)
    high = math.floor(max(values) / w)
    for k in range(low, high + 1):
        print(f"{k * w}-{(k + 1) * w} {counts.get(k, 0)}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def bucket_index(value, w):
    # TODO: return the index k of the bucket [k*w, (k+1)*w) holding value,
    # flooring towards minus infinity for negatives.
    return 0


def main():
    data = sys.stdin.read().split()
    n, w = int(data[0]), int(data[1])
    values = [int(x) for x in data[2:2 + n]]
    counts = {}
    for value in values:
        k = bucket_index(value, w)
        counts[k] = counts.get(k, 0) + 1
    low = bucket_index(min(values), w)
    high = bucket_index(max(values), w)
    for k in range(low, high + 1):
        print(f"{k * w}-{(k + 1) * w} {counts.get(k, 0)}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Skips empty buckets, so the shape of the distribution is lost.
        """import sys
import math

data = sys.stdin.read().split()
n, w = int(data[0]), int(data[1])
values = [int(x) for x in data[2:2 + n]]
counts = {}
for value in values:
    k = math.floor(value / w)
    counts[k] = counts.get(k, 0) + 1
for k in sorted(counts):
    print(f"{k * w}-{(k + 1) * w} {counts[k]}")
""",
        # Integer division truncates towards zero, so -1 lands in bucket 0.
        """import sys

data = sys.stdin.read().split()
n, w = int(data[0]), int(data[1])
values = [int(x) for x in data[2:2 + n]]
counts = {}
for value in values:
    k = int(value / w)
    counts[k] = counts.get(k, 0) + 1
low = int(min(values) / w)
high = int(max(values) / w)
for k in range(low, high + 1):
    print(f"{k * w}-{(k + 1) * w} {counts.get(k, 0)}")
""",
        # Closed buckets: a value on the boundary is counted in both.
        """import sys
import math

data = sys.stdin.read().split()
n, w = int(data[0]), int(data[1])
values = [int(x) for x in data[2:2 + n]]
low = math.floor(min(values) / w)
high = math.floor(max(values) / w)
for k in range(low, high + 1):
    lo, hi = k * w, (k + 1) * w
    print(f"{lo}-{hi} {sum(1 for v in values if lo <= v <= hi)}")
""",
    ],
)

_problem(
    id="an-eda-percentile",
    title="Nearest-Rank Percentile",
    skill_id="exploratory_analysis",
    concept="distribution",
    difficulty=4,
    minutes=22,
    summary="One percentile, one stated convention — because the conventions disagree.",
    statement=(
        "Print the `p`-th percentile of a column using the **nearest-rank** "
        "convention: sort ascending into `v[0..n-1]`, take "
        "`rank = ceil(p / 100 * n)` clamped to 1..n, and answer `v[rank - 1]`.\n\n"
        "So the 50th percentile of `1 2 3 4` is `2`, not `2.5`: nearest-rank "
        "always returns a value that is actually in the data. `p = 0` answers "
        "the minimum."
    ),
    input_format="Line 1: n and p separated by a space. Line 2: n space-separated integers.",
    output_format="One line: the percentile value, as an integer.",
    constraints=["1 <= n <= 20000", "0 <= p <= 100", "-1000000 <= value <= 1000000"],
    requirements=[
        "Sort ascending and use rank = ceil(p / 100 * n), clamped to 1..n",
        "Return a value from the data — do not interpolate between two values",
        "p = 0 answers the minimum and p = 100 the maximum",
    ],
    examples=[
        {
            "stdin": "4 50\n4 1 3 2\n",
            "explanation": "Sorted: 1 2 3 4. ceil(0.5 * 4) is 2, so the answer is the 2nd value, 2.",
        }
    ],
    cases=[
        ("sample: median of an even count", "4 50\n4 1 3 2\n", False),
        ("sample: 90th percentile", "10 90\n1 2 3 4 5 6 7 8 9 10\n", False),
        ("hidden: p = 0 is the minimum", "5 0\n5 3 9 1 7\n", True),
        ("hidden: p = 100 is the maximum", "5 100\n5 3 9 1 7\n", True),
        ("hidden: single value", "1 37\n42\n", True),
        ("hidden: interpolation would answer differently", "4 25\n10 20 30 40\n", True),
        ("hidden: negatives", "6 50\n-6 -5 -4 -3 -2 -1\n", True),
    ],
    reference="""import sys
import math


def main():
    data = sys.stdin.read().split()
    n, p = int(data[0]), int(data[1])
    values = sorted(int(x) for x in data[2:2 + n])
    rank = min(max(math.ceil(p / 100 * n), 1), n)
    print(values[rank - 1])


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def percentile(values, p):
    # TODO: nearest-rank percentile: rank = ceil(p / 100 * n), clamped to 1..n.
    return 0


def main():
    data = sys.stdin.read().split()
    n, p = int(data[0]), int(data[1])
    values = [int(x) for x in data[2:2 + n]]
    print(percentile(values, p))


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Linear interpolation: answers a value that is not in the data.
        """import sys

data = sys.stdin.read().split()
n, p = int(data[0]), int(data[1])
values = sorted(int(x) for x in data[2:2 + n])
if n == 1:
    print(values[0])
else:
    pos = p / 100 * (n - 1)
    low = int(pos)
    high = min(low + 1, n - 1)
    frac = pos - low
    result = values[low] * (1 - frac) + values[high] * frac
    print(int(result) if float(result).is_integer() else result)
""",
        # Truncating index instead of ceiling.
        """import sys

data = sys.stdin.read().split()
n, p = int(data[0]), int(data[1])
values = sorted(int(x) for x in data[2:2 + n])
index = min(int(p / 100 * n), n - 1)
print(values[index])
""",
        # Forgets to sort.
        """import sys
import math

data = sys.stdin.read().split()
n, p = int(data[0]), int(data[1])
values = [int(x) for x in data[2:2 + n]]
rank = min(max(math.ceil(p / 100 * n), 1), n)
print(values[rank - 1])
""",
    ],
)

_problem(
    id="an-eda-moving-average",
    title="Rolling Average Over a Trailing Window",
    skill_id="exploratory_analysis",
    concept="distribution",
    difficulty=5,
    minutes=25,
    summary="A k-period trailing mean, with the first k-1 periods honestly reported as NA.",
    statement=(
        "Print a `k`-period **trailing** moving average: for each position, the "
        "mean of that value and the `k - 1` values before it, to two decimal "
        "places, one per line.\n\n"
        "The first `k - 1` positions do not have a full window. Averaging a "
        "partial window there invents a trend that is not in the data, so print "
        "`NA` for those positions instead."
    ),
    input_format="Line 1: n and k separated by a space. Line 2: n space-separated integers.",
    output_format="n lines: `NA` for each position without a full window, otherwise the average to two decimal places.",
    constraints=["1 <= k <= n <= 20000", "-100000 <= value <= 100000"],
    requirements=[
        "The window is trailing: it ends at the current position",
        "Print NA for the first k - 1 positions rather than averaging a partial window",
        "Print each average to exactly two decimal places",
        "k = 1 reproduces the input",
    ],
    examples=[
        {
            "stdin": "5 3\n10 20 30 40 50\n",
            "explanation": (
                "The first two positions have no full window. The third is the "
                "mean of 10, 20, 30 — 20.00."
            ),
        }
    ],
    cases=[
        ("sample: window of three", "5 3\n10 20 30 40 50\n", False),
        ("sample: window of one", "3 1\n5 6 7\n", False),
        ("hidden: window covers everything", "4 4\n1 2 3 4\n", True),
        ("hidden: negatives and rounding", "5 2\n-1 -2 3 -4 5\n", True),
        ("hidden: single value, single window", "1 1\n9\n", True),
        ("hidden: flat series", "4 2\n7 7 7 7\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split()
    n, k = int(data[0]), int(data[1])
    values = [int(x) for x in data[2:2 + n]]
    window = 0
    for index, value in enumerate(values):
        window += value
        if index >= k:
            window -= values[index - k]
        if index < k - 1:
            print("NA")
        else:
            print(f"{window / k:.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def rolling(values, k):
    # TODO: return a list holding None for the first k - 1 positions and the
    # trailing k-period mean thereafter.
    return [None] * len(values)


def main():
    data = sys.stdin.read().split()
    n, k = int(data[0]), int(data[1])
    values = [int(x) for x in data[2:2 + n]]
    for value in rolling(values, k):
        print("NA" if value is None else f"{value:.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Averages the partial window instead of reporting NA.
        """import sys

data = sys.stdin.read().split()
n, k = int(data[0]), int(data[1])
values = [int(x) for x in data[2:2 + n]]
for index in range(n):
    window = values[max(0, index - k + 1):index + 1]
    print(f"{sum(window) / len(window):.2f}")
""",
        # Centred window rather than trailing.
        """import sys

data = sys.stdin.read().split()
n, k = int(data[0]), int(data[1])
values = [int(x) for x in data[2:2 + n]]
half = k // 2
for index in range(n):
    start = index - half
    end = start + k
    if start < 0 or end > n:
        print("NA")
    else:
        print(f"{sum(values[start:end]) / k:.2f}")
""",
        # Window one period too long.
        """import sys

data = sys.stdin.read().split()
n, k = int(data[0]), int(data[1])
values = [int(x) for x in data[2:2 + n]]
for index in range(n):
    if index < k:
        print("NA")
    else:
        print(f"{sum(values[index - k:index + 1]) / (k + 1):.2f}")
""",
    ],
)

_problem(
    id="an-eda-conversion-rates",
    title="Conversion Rate by Channel",
    skill_id="exploratory_analysis",
    concept="segmentation",
    difficulty=5,
    minutes=25,
    summary="Rank channels by conversion rate, and refuse to invent a rate for a channel with no visits.",
    statement=(
        "For each channel print `channel rate`, where `rate` is "
        "`conversions / visits` to three decimal places.\n\n"
        "A channel with zero visits has **no** conversion rate: print `NA` for "
        "it rather than 0, and list those channels after all the rated ones, in "
        "alphabetical order. The rated channels come first, sorted by rate "
        "descending, ties broken by channel name ascending."
    ),
    input_format="Line 1: n. Next n lines: `channel,conversions,visits`, both integers. Rows for one channel may repeat and must be summed.",
    output_format="One line per channel: `channel rate` (three decimals) or `channel NA`.",
    constraints=["1 <= n <= 20000", "0 <= conversions <= visits <= 1000000 per row"],
    requirements=[
        "Sum conversions and visits per channel before dividing",
        "Print NA for a channel whose total visits are zero, rather than 0.000",
        "Sort rated channels by rate descending, then by name ascending",
        "List the NA channels after the rated ones, alphabetically",
    ],
    examples=[
        {
            "stdin": "4\nemail,5,100\nsocial,10,100\nemail,5,100\nprint,0,0\n",
            "explanation": (
                "email totals 10 of 200 (0.050), social 10 of 100 (0.100). "
                "print has no visits at all, so it is NA and comes last."
            ),
        }
    ],
    cases=[
        ("sample: a channel with no visits", "4\nemail,5,100\nsocial,10,100\nemail,5,100\nprint,0,0\n", False),
        ("sample: two rated channels", "2\na,1,4\nb,3,4\n", False),
        ("hidden: every channel unrated", "2\nx,0,0\ny,0,0\n", True),
        ("hidden: tie broken by name", "3\nzz,1,2\naa,1,2\nmm,2,2\n", True),
        ("hidden: rates aggregate across rows, not average of ratios", "3\nc,1,1\nc,0,99\nd,1,10\n", True),
        ("hidden: zero conversions is a real rate of 0.000", "2\np,0,10\nq,1,10\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    totals = {}
    for line in data[1:1 + n]:
        channel, conversions, visits = line.strip().split(",")
        conv, vis = totals.get(channel, (0, 0))
        totals[channel] = (conv + int(conversions), vis + int(visits))
    rated = [(c, v[0] / v[1]) for c, v in totals.items() if v[1] > 0]
    unrated = sorted(c for c, v in totals.items() if v[1] == 0)
    for channel, rate in sorted(rated, key=lambda kv: (-kv[1], kv[0])):
        print(f"{channel} {rate:.3f}")
    for channel in unrated:
        print(f"{channel} NA")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def rates(rows):
    # TODO: return (rated, unrated) where rated is [(channel, rate), ...] in
    # the required order and unrated is the alphabetical no-visit channels.
    return [], []


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = [line.strip().split(",") for line in data[1:1 + n]]
    rated, unrated = rates(rows)
    for channel, rate in rated:
        print(f"{channel} {rate:.3f}")
    for channel in unrated:
        print(f"{channel} NA")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Zero visits reported as a rate of zero.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
totals = {}
for line in data[1:1 + n]:
    channel, conversions, visits = line.strip().split(",")
    conv, vis = totals.get(channel, (0, 0))
    totals[channel] = (conv + int(conversions), vis + int(visits))
rows = [(c, (v[0] / v[1]) if v[1] else 0.0) for c, v in totals.items()]
for channel, rate in sorted(rows, key=lambda kv: (-kv[1], kv[0])):
    print(f"{channel} {rate:.3f}")
""",
        # Averages the per-row ratios instead of aggregating first.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
ratios = {}
zero = set()
for line in data[1:1 + n]:
    channel, conversions, visits = line.strip().split(",")
    if int(visits) == 0:
        zero.add(channel)
        continue
    ratios.setdefault(channel, []).append(int(conversions) / int(visits))
rated = [(c, sum(v) / len(v)) for c, v in ratios.items()]
for channel, rate in sorted(rated, key=lambda kv: (-kv[1], kv[0])):
    print(f"{channel} {rate:.3f}")
for channel in sorted(zero - set(ratios)):
    print(f"{channel} NA")
""",
        # NA channels printed first.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
totals = {}
for line in data[1:1 + n]:
    channel, conversions, visits = line.strip().split(",")
    conv, vis = totals.get(channel, (0, 0))
    totals[channel] = (conv + int(conversions), vis + int(visits))
for channel in sorted(c for c, v in totals.items() if v[1] == 0):
    print(f"{channel} NA")
rated = [(c, v[0] / v[1]) for c, v in totals.items() if v[1] > 0]
for channel, rate in sorted(rated, key=lambda kv: (-kv[1], kv[0])):
    print(f"{channel} {rate:.3f}")
""",
    ],
)

_problem(
    id="an-eda-weekday-profile",
    title="Which Weekday Sells Most",
    skill_id="exploratory_analysis",
    concept="segmentation",
    difficulty=6,
    minutes=28,
    summary="Derive the weekday from an ISO date without a library, then profile revenue by weekday.",
    statement=(
        "Profile revenue by day of the week. For each weekday that appears in "
        "the data, print `weekday total` with the total to two decimal places, "
        "ordered Monday first through Sunday — calendar order, not "
        "alphabetical, and not by size.\n\n"
        "Weekday names are `Mon Tue Wed Thu Fri Sat Sun`. You may compute the "
        "weekday however you like; `2024-01-01` was a Monday. Weekdays with no "
        "rows are omitted."
    ),
    input_format="Line 1: n. Next n lines: `YYYY-MM-DD,amount` with at most two decimal places.",
    output_format="One line per weekday present: the three-letter name, a space, then the total to two decimals.",
    constraints=[
        "1 <= n <= 20000",
        "Dates are between 2000-01-01 and 2099-12-31",
        "0 <= amount <= 100000",
    ],
    requirements=[
        "Total the amounts per weekday",
        "Output in calendar order from Mon to Sun, not alphabetical order",
        "Omit weekdays with no rows",
        "Print each total to exactly two decimal places",
    ],
    examples=[
        {
            "stdin": "3\n2024-01-01,10.00\n2024-01-02,5.00\n2024-01-08,1.50\n",
            "explanation": (
                "1 and 8 January 2024 were both Mondays, totalling 11.50, and "
                "2 January was a Tuesday."
            ),
        }
    ],
    cases=[
        ("sample: two Mondays and a Tuesday", "3\n2024-01-01,10.00\n2024-01-02,5.00\n2024-01-08,1.50\n", False),
        ("sample: a weekend", "2\n2024-01-06,2.00\n2024-01-07,3.00\n", False),
        ("hidden: a full week", "7\n2024-03-04,1.00\n2024-03-05,2.00\n2024-03-06,3.00\n2024-03-07,4.00\n2024-03-08,5.00\n2024-03-09,6.00\n2024-03-10,7.00\n", True),
        ("hidden: leap day", "2\n2024-02-29,8.00\n2023-02-28,1.00\n", True),
        ("hidden: only Sunday", "2\n2024-01-07,1.25\n2024-01-14,2.25\n", True),
        ("hidden: across a century boundary", "2\n2000-01-03,5.00\n2099-12-31,5.00\n", True),
    ],
    reference="""import sys
import datetime

NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    totals = {}
    for line in data[1:1 + n]:
        date_text, amount = line.strip().rsplit(",", 1)
        year, month, day = (int(part) for part in date_text.split("-"))
        weekday = datetime.date(year, month, day).weekday()
        totals[weekday] = totals.get(weekday, 0) + round(float(amount) * 100)
    for index, name in enumerate(NAMES):
        if index in totals:
            print(f"{name} {totals[index] / 100:.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys

NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def weekday_index(date_text):
    # TODO: return 0 for Monday through 6 for Sunday. 2024-01-01 was a Monday.
    return 0


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    totals = {}
    for line in data[1:1 + n]:
        date_text, amount = line.strip().rsplit(",", 1)
        index = weekday_index(date_text)
        totals[index] = totals.get(index, 0) + round(float(amount) * 100)
    for index, name in enumerate(NAMES):
        if index in totals:
            print(f"{name} {totals[index] / 100:.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Sunday-first indexing, so every label is shifted.
        """import sys
import datetime

NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
totals = {}
for line in data[1:1 + n]:
    date_text, amount = line.strip().rsplit(",", 1)
    y, m, d = (int(p) for p in date_text.split("-"))
    index = (datetime.date(y, m, d).weekday() + 1) % 7
    totals[index] = totals.get(index, 0) + round(float(amount) * 100)
for index, name in enumerate(NAMES):
    if index in totals:
        print(f"{name} {totals[index] / 100:.2f}")
""",
        # Alphabetical output order rather than calendar order.
        """import sys
import datetime

NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
totals = {}
for line in data[1:1 + n]:
    date_text, amount = line.strip().rsplit(",", 1)
    y, m, d = (int(p) for p in date_text.split("-"))
    name = NAMES[datetime.date(y, m, d).weekday()]
    totals[name] = totals.get(name, 0) + round(float(amount) * 100)
for name in sorted(totals):
    print(f"{name} {totals[name] / 100:.2f}")
""",
        # Counts rows instead of totalling revenue.
        """import sys
import datetime

NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
totals = {}
for line in data[1:1 + n]:
    date_text, amount = line.strip().rsplit(",", 1)
    y, m, d = (int(p) for p in date_text.split("-"))
    index = datetime.date(y, m, d).weekday()
    totals[index] = totals.get(index, 0) + 1
for index, name in enumerate(NAMES):
    if index in totals:
        print(f"{name} {float(totals[index]):.2f}")
""",
    ],
)


# =========================================================================== #
#  statistics_business                                                        #
# =========================================================================== #

_problem(
    id="an-stats-sample-sd",
    title="Sample Standard Deviation",
    skill_id="statistics_business",
    concept="variance",
    difficulty=4,
    minutes=22,
    summary="Divide by n-1, because a sample is not the population.",
    statement=(
        "Print the **sample** standard deviation of a column to four decimal "
        "places: the square root of `sum((x - mean)^2) / (n - 1)`.\n\n"
        "Dividing by `n` instead computes the population standard deviation, "
        "which understates the spread of a sample and is the wrong answer here. "
        "A single observation has no sample standard deviation at all — print "
        "`NA` for `n = 1`."
    ),
    input_format="Line 1: n. Line 2: n space-separated integers.",
    output_format="One line: the sample standard deviation to four decimal places, or `NA`.",
    constraints=["1 <= n <= 20000", "-100000 <= value <= 100000"],
    requirements=[
        "Divide the sum of squared deviations by n - 1, not by n",
        "Print NA when n is 1",
        "Print the result to exactly four decimal places",
        "A column of identical values has a standard deviation of 0",
    ],
    examples=[
        {
            "stdin": "4\n2 4 4 6\n",
            "explanation": (
                "The mean is 4 and the squared deviations total 8, so the "
                "sample variance is 8/3 and the standard deviation 1.6330."
            ),
        }
    ],
    cases=[
        ("sample: four values", "4\n2 4 4 6\n", False),
        ("sample: identical values", "3\n5 5 5\n", False),
        ("hidden: single value is NA", "1\n7\n", True),
        ("hidden: two values", "2\n0 10\n", True),
        ("hidden: negatives", "5\n-2 -4 -4 -6 -8\n", True),
        ("hidden: large spread", "6\n1 1 1 1 1 1000\n", True),
    ],
    reference="""import sys
import math


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    if n == 1:
        print("NA")
        return
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    print(f"{math.sqrt(variance):.4f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def sample_sd(values):
    # TODO: return the sample standard deviation (divide by n - 1), or None
    # when there is only one value.
    return 0.0


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    result = sample_sd(values)
    print("NA" if result is None else f"{result:.4f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Population standard deviation: divides by n.
        """import sys
import math

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
mean = sum(values) / n
variance = sum((v - mean) ** 2 for v in values) / n
print(f"{math.sqrt(variance):.4f}")
""",
        # Variance rather than its square root.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
if n == 1:
    print("NA")
else:
    mean = sum(values) / n
    print(f"{sum((v - mean) ** 2 for v in values) / (n - 1):.4f}")
""",
        # Mean absolute deviation.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
if n == 1:
    print("NA")
else:
    mean = sum(values) / n
    print(f"{sum(abs(v - mean) for v in values) / (n - 1):.4f}")
""",
    ],
)

_problem(
    id="an-stats-mean-vs-median",
    title="Mean, Median and Which Way the Data Skews",
    skill_id="statistics_business",
    concept="mean vs median",
    difficulty=4,
    minutes=22,
    summary="Report both centres and say which one the outliers are dragging.",
    statement=(
        "Print the mean and the median, each to two decimal places, then a "
        "label saying which way the distribution skews:\n\n"
        "* `right` when the mean is greater than the median (a few large values "
        "pulling the average up),\n"
        "* `left` when the mean is less than the median,\n"
        "* `symmetric` when they are equal.\n\n"
        "Compare them as exact values, and treat a difference smaller than "
        "`1e-9` as equal so that floating-point noise does not decide the "
        "label. Output the three fields space separated on one line."
    ),
    input_format="Line 1: n. Line 2: n space-separated integers.",
    output_format="One line: mean, median (both two decimals) and the label.",
    constraints=["1 <= n <= 20000", "-100000 <= value <= 100000"],
    requirements=[
        "Print the mean, then the median, then the label",
        "The median of an even count averages the two middle values",
        "Label 'right' when mean > median and 'left' when mean < median",
        "Treat a difference below 1e-9 as symmetric",
    ],
    examples=[
        {
            "stdin": "5\n1 1 1 1 100\n",
            "explanation": (
                "The median is 1.00 but one large value drags the mean to "
                "20.80, so the distribution is right-skewed."
            ),
        }
    ],
    cases=[
        ("sample: one big outlier", "5\n1 1 1 1 100\n", False),
        ("sample: symmetric", "4\n1 2 3 4\n", False),
        ("hidden: left skew", "5\n-100 1 1 1 1\n", True),
        ("hidden: single value is symmetric", "1\n5\n", True),
        ("hidden: even count, skew is small but real", "4\n1 2 3 5\n", True),
        # Mean 0.001 against a median of 0: a real right skew that disappears
        # if you compare the numbers only after rounding them for display.
        ("hidden: skew smaller than the printed precision", "1000\n" + " ".join(["0"] * 999 + ["1"]) + "\n", True),
        ("hidden: identical values", "3\n8 8 8\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = sorted(int(x) for x in data[1:1 + n])
    mean = sum(values) / n
    mid = n // 2
    median = float(values[mid]) if n % 2 else (values[mid - 1] + values[mid]) / 2.0
    if abs(mean - median) < 1e-9:
        label = "symmetric"
    elif mean > median:
        label = "right"
    else:
        label = "left"
    print(f"{mean:.2f} {median:.2f} {label}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def skew_label(mean, median):
    # TODO: 'right', 'left' or 'symmetric' (difference below 1e-9).
    return "symmetric"


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = sorted(int(x) for x in data[1:1 + n])
    mean = sum(values) / n
    mid = n // 2
    median = float(values[mid]) if n % 2 else (values[mid - 1] + values[mid]) / 2.0
    print(f"{mean:.2f} {median:.2f} {skew_label(mean, median)}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Compares the rounded strings, so a small real skew reads as symmetric.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = sorted(int(x) for x in data[1:1 + n])
mean = sum(values) / n
mid = n // 2
median = float(values[mid]) if n % 2 else (values[mid - 1] + values[mid]) / 2.0
if f"{mean:.2f}" == f"{median:.2f}":
    label = "symmetric"
elif mean > median:
    label = "right"
else:
    label = "left"
print(f"{mean:.2f} {median:.2f} {label}")
""",
        # Skew direction inverted.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = sorted(int(x) for x in data[1:1 + n])
mean = sum(values) / n
mid = n // 2
median = float(values[mid]) if n % 2 else (values[mid - 1] + values[mid]) / 2.0
if abs(mean - median) < 1e-9:
    label = "symmetric"
elif mean > median:
    label = "left"
else:
    label = "right"
print(f"{mean:.2f} {median:.2f} {label}")
""",
        # Median taken as the upper middle for an even count.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = sorted(int(x) for x in data[1:1 + n])
mean = sum(values) / n
median = float(values[n // 2])
if abs(mean - median) < 1e-9:
    label = "symmetric"
elif mean > median:
    label = "right"
else:
    label = "left"
print(f"{mean:.2f} {median:.2f} {label}")
""",
    ],
)

_problem(
    id="an-stats-confidence-interval",
    title="95% Confidence Interval for a Mean",
    skill_id="statistics_business",
    concept="confidence interval",
    difficulty=6,
    minutes=28,
    summary="A point estimate with its uncertainty attached, using the sample standard deviation.",
    statement=(
        "Print the lower and upper bound of a 95% confidence interval for the "
        "mean, each to three decimal places, space separated.\n\n"
        "Use `mean ± 1.96 * s / sqrt(n)`, where `s` is the **sample** standard "
        "deviation (dividing by `n - 1`). Use exactly `1.96`.\n\n"
        "With `n = 1` there is no sample standard deviation and therefore no "
        "interval: print `NA`."
    ),
    input_format="Line 1: n. Line 2: n space-separated integers.",
    output_format="One line: lower and upper bound to three decimal places, or `NA`.",
    constraints=["1 <= n <= 20000", "-100000 <= value <= 100000", "Use z = 1.96"],
    requirements=[
        "Use the sample standard deviation (n - 1 in the denominator)",
        "The standard error divides s by the square root of n",
        "Use z = 1.96 for the 95% interval",
        "Print NA when n is 1",
    ],
    examples=[
        {
            "stdin": "4\n2 4 4 6\n",
            "explanation": (
                "The mean is 4 and s is 1.63299, so the standard error is "
                "0.81650 and the interval is 4 ± 1.60033."
            ),
        }
    ],
    cases=[
        ("sample: four values", "4\n2 4 4 6\n", False),
        ("sample: identical values give a zero-width interval", "3\n5 5 5\n", False),
        ("hidden: n = 1 is NA", "1\n9\n", True),
        ("hidden: wide spread", "5\n0 10 20 30 40\n", True),
        ("hidden: negatives", "4\n-5 -10 -15 -20\n", True),
        ("hidden: larger sample narrows the interval", "10\n1 2 3 4 5 6 7 8 9 10\n", True),
    ],
    reference="""import sys
import math

Z = 1.96


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    if n == 1:
        print("NA")
        return
    mean = sum(values) / n
    s = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    margin = Z * s / math.sqrt(n)
    print(f"{mean - margin:.3f} {mean + margin:.3f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys

Z = 1.96


def interval(values):
    # TODO: return (lower, upper) from mean +/- Z * s / sqrt(n), or None when
    # there is only one value.
    return 0.0, 0.0


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    result = interval(values)
    if result is None:
        print("NA")
    else:
        print(f"{result[0]:.3f} {result[1]:.3f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Population standard deviation.
        """import sys
import math

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
if n == 1:
    print("NA")
else:
    mean = sum(values) / n
    s = math.sqrt(sum((v - mean) ** 2 for v in values) / n)
    margin = 1.96 * s / math.sqrt(n)
    print(f"{mean - margin:.3f} {mean + margin:.3f}")
""",
        # Forgets to divide by sqrt(n): uses the spread, not the standard error.
        """import sys
import math

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
if n == 1:
    print("NA")
else:
    mean = sum(values) / n
    s = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    margin = 1.96 * s
    print(f"{mean - margin:.3f} {mean + margin:.3f}")
""",
        # z = 2 instead of 1.96.
        """import sys
import math

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
if n == 1:
    print("NA")
else:
    mean = sum(values) / n
    s = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    margin = 2 * s / math.sqrt(n)
    print(f"{mean - margin:.3f} {mean + margin:.3f}")
""",
    ],
)

_problem(
    id="an-stats-ab-test",
    title="Is the A/B Test Result Significant?",
    skill_id="statistics_business",
    concept="a/b test",
    difficulty=7,
    minutes=32,
    summary="A pooled two-proportion z-test, and the decision it does or does not support.",
    statement=(
        "Two variants have `ca` conversions from `na` visitors and `cb` from "
        "`nb`. Test whether their conversion rates differ.\n\n"
        "Compute the pooled proportion `p = (ca + cb) / (na + nb)`, then\n\n"
        "    z = (pb - pa) / sqrt(p * (1 - p) * (1/na + 1/nb))\n\n"
        "where `pa = ca / na` and `pb = cb / nb`. Print `z` to three decimal "
        "places, a space, and then `significant` when `|z| > 1.96`, otherwise "
        "`not significant`.\n\n"
        "When the pooled proportion is 0 or 1 the denominator is zero and the "
        "test says nothing: print `undefined not significant`. A wider gap in "
        "the rates is not significance on its own — the sample sizes decide."
    ),
    input_format="One line: ca na cb nb, space separated.",
    output_format="One line: z to three decimal places (or `undefined`), a space, then the verdict.",
    constraints=[
        "1 <= na, nb <= 10000000",
        "0 <= ca <= na and 0 <= cb <= nb",
        "Use the pooled two-proportion formula and the 1.96 threshold",
    ],
    requirements=[
        "Pool the conversions across both variants for the standard error",
        "z is (pb - pa) divided by the pooled standard error, in that direction",
        "Declare significance only when the absolute value of z exceeds 1.96",
        "Report `undefined not significant` when the pooled proportion is 0 or 1",
    ],
    examples=[
        {
            "stdin": "100 1000 130 1000\n",
            "explanation": (
                "pa is 0.10 and pb 0.13. The pooled proportion is 0.115, so z "
                "is 2.117 — beyond 1.96, so the difference is significant."
            ),
        }
    ],
    cases=[
        ("sample: significant", "100 1000 130 1000\n", False),
        ("sample: same rates on small samples", "10 100 13 100\n", False),
        ("hidden: nobody converts anywhere", "0 500 0 500\n", True),
        ("hidden: everybody converts", "50 50 60 60\n", True),
        ("hidden: B is worse, so z is negative", "130 1000 100 1000\n", True),
        ("hidden: identical rates give z of zero", "50 500 100 1000\n", True),
        ("hidden: same gap, bigger samples become significant", "1000 10000 1300 10000\n", True),
    ],
    reference="""import sys
import math


def main():
    ca, na, cb, nb = (int(x) for x in sys.stdin.read().split()[:4])
    pooled = (ca + cb) / (na + nb)
    denominator = pooled * (1 - pooled) * (1 / na + 1 / nb)
    if denominator == 0:
        print("undefined not significant")
        return
    z = (cb / nb - ca / na) / math.sqrt(denominator)
    verdict = "significant" if abs(z) > 1.96 else "not significant"
    print(f"{z:.3f} {verdict}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def z_score(ca, na, cb, nb):
    # TODO: return the pooled two-proportion z, or None when the pooled
    # proportion leaves a zero denominator.
    return 0.0


def main():
    ca, na, cb, nb = (int(x) for x in sys.stdin.read().split()[:4])
    z = z_score(ca, na, cb, nb)
    if z is None:
        print("undefined not significant")
    else:
        print(f"{z:.3f} {'significant' if abs(z) > 1.96 else 'not significant'}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Unpooled standard error.
        """import sys
import math

ca, na, cb, nb = (int(x) for x in sys.stdin.read().split()[:4])
pa, pb = ca / na, cb / nb
se = math.sqrt(pa * (1 - pa) / na + pb * (1 - pb) / nb)
if se == 0:
    print("undefined not significant")
else:
    z = (pb - pa) / se
    print(f"{z:.3f} {'significant' if abs(z) > 1.96 else 'not significant'}")
""",
        # Sign flipped: reports the change as A minus B.
        """import sys
import math

ca, na, cb, nb = (int(x) for x in sys.stdin.read().split()[:4])
pooled = (ca + cb) / (na + nb)
denominator = pooled * (1 - pooled) * (1 / na + 1 / nb)
if denominator == 0:
    print("undefined not significant")
else:
    z = (ca / na - cb / nb) / math.sqrt(denominator)
    print(f"{z:.3f} {'significant' if abs(z) > 1.96 else 'not significant'}")
""",
        # Decides on the rate gap rather than on z.
        """import sys
import math

ca, na, cb, nb = (int(x) for x in sys.stdin.read().split()[:4])
pooled = (ca + cb) / (na + nb)
denominator = pooled * (1 - pooled) * (1 / na + 1 / nb)
if denominator == 0:
    print("undefined not significant")
else:
    z = (cb / nb - ca / na) / math.sqrt(denominator)
    gap = abs(cb / nb - ca / na)
    print(f"{z:.3f} {'significant' if gap > 0.02 else 'not significant'}")
""",
        # One-sided threshold on a two-sided question.
        """import sys
import math

ca, na, cb, nb = (int(x) for x in sys.stdin.read().split()[:4])
pooled = (ca + cb) / (na + nb)
denominator = pooled * (1 - pooled) * (1 / na + 1 / nb)
if denominator == 0:
    print("undefined not significant")
else:
    z = (cb / nb - ca / na) / math.sqrt(denominator)
    print(f"{z:.3f} {'significant' if z > 1.645 else 'not significant'}")
""",
    ],
)

_problem(
    id="an-stats-weighted-mean",
    title="Weighted Average Price",
    skill_id="statistics_business",
    concept="mean vs median",
    difficulty=4,
    minutes=20,
    summary="Weight by volume, because the unweighted average of prices answers a different question.",
    statement=(
        "Each row is a price and the number of units sold at it. Print the "
        "**volume-weighted** average price to four decimal places: "
        "`sum(price * units) / sum(units)`.\n\n"
        "The plain average of the prices is a different number and a different "
        "question — it tells you about your price list, not about what "
        "customers paid. When every weight is zero there is nothing to average: "
        "print `NA`."
    ),
    input_format="Line 1: n. Next n lines: `price,units` where price has at most two decimal places and units is a non-negative integer.",
    output_format="One line: the weighted mean to four decimal places, or `NA`.",
    constraints=["1 <= n <= 20000", "0 <= price <= 100000", "0 <= units <= 1000000"],
    requirements=[
        "Weight each price by its units",
        "Divide by the total units, not by the number of rows",
        "Print NA when the total weight is zero",
        "Print the result to exactly four decimal places",
    ],
    examples=[
        {
            "stdin": "2\n10.00,90\n100.00,10\n",
            "explanation": (
                "900 + 1000 is 1900 over 100 units, so 19.0000 — not the "
                "unweighted 55.0000."
            ),
        }
    ],
    cases=[
        ("sample: volume dominates", "2\n10.00,90\n100.00,10\n", False),
        ("sample: equal weights", "2\n10.00,5\n20.00,5\n", False),
        ("hidden: all weights zero", "2\n10.00,0\n20.00,0\n", True),
        ("hidden: one row carries every unit", "3\n5.00,0\n7.50,100\n9.00,0\n", True),
        ("hidden: rounding to four places", "2\n1.00,3\n2.00,4\n", True),
        ("hidden: a free line does not drag the average", "2\n0.00,0\n50.00,2\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    weighted = 0.0
    total_units = 0
    for line in data[1:1 + n]:
        price, units = line.strip().split(",")
        weighted += float(price) * int(units)
        total_units += int(units)
    if total_units == 0:
        print("NA")
        return
    print(f"{weighted / total_units:.4f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def weighted_mean(rows):
    # TODO: return sum(price * units) / sum(units), or None when no units sold.
    return 0.0


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = [line.strip().split(",") for line in data[1:1 + n]]
    result = weighted_mean(rows)
    print("NA" if result is None else f"{result:.4f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Unweighted average of the prices.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
prices = [float(line.strip().split(",")[0]) for line in data[1:1 + n]]
print(f"{sum(prices) / len(prices):.4f}")
""",
        # Divides by the row count instead of the total weight.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
weighted = 0.0
for line in data[1:1 + n]:
    price, units = line.strip().split(",")
    weighted += float(price) * int(units)
print(f"{weighted / n:.4f}")
""",
        # Zero total weight reported as 0.0000 rather than NA.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
weighted = 0.0
total = 0
for line in data[1:1 + n]:
    price, units = line.strip().split(",")
    weighted += float(price) * int(units)
    total += int(units)
print(f"{(weighted / total) if total else 0.0:.4f}")
""",
    ],
)

_problem(
    id="an-stats-sample-size",
    title="How Many Users the Test Needs",
    skill_id="statistics_business",
    concept="sampling",
    difficulty=5,
    minutes=24,
    summary="Round the required sample size up, because a fractional user cannot be recruited.",
    statement=(
        "Given a baseline conversion rate and a target margin of error, compute "
        "the sample size per variant:\n\n"
        "    n = ceil(1.96^2 * p * (1 - p) / e^2)\n\n"
        "with `z = 1.96` exactly. Always round **up**: rounding to nearest, or "
        "truncating, under-powers the test.\n\n"
        "Print the single integer."
    ),
    input_format="One line: p and e, space separated, each a decimal fraction between 0 and 1 exclusive.",
    output_format="One line: the required sample size as an integer.",
    constraints=[
        "0 < p < 1",
        "0 < e < 1",
        "p and e have at most six decimal places",
        "Use z = 1.96 exactly",
    ],
    requirements=[
        "Use the formula and the constant given, not a table lookup",
        "Round the result up to the next whole user",
        "Print a plain integer, with no decimal point",
    ],
    examples=[
        {
            "stdin": "0.5 0.05\n",
            "explanation": (
                "1.96^2 * 0.25 / 0.0025 is 384.16, and rounding up gives the "
                "familiar 385."
            ),
        }
    ],
    cases=[
        ("sample: the textbook 385", "0.5 0.05\n", False),
        ("sample: a rarer event", "0.1 0.02\n", False),
        ("hidden: exactly-integer result is not rounded up further", "0.5 0.098\n", True),
        ("hidden: very tight margin", "0.5 0.001\n", True),
        ("hidden: very rare event", "0.01 0.005\n", True),
        ("hidden: p near one", "0.99 0.01\n", True),
    ],
    reference="""import sys
import math

Z = 1.96


def main():
    p, e = (float(x) for x in sys.stdin.read().split()[:2])
    print(math.ceil(Z * Z * p * (1 - p) / (e * e)))


if __name__ == "__main__":
    main()
""",
    starter="""import sys

Z = 1.96


def sample_size(p, e):
    # TODO: return ceil(Z^2 * p * (1 - p) / e^2).
    return 0


def main():
    p, e = (float(x) for x in sys.stdin.read().split()[:2])
    print(sample_size(p, e))


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Rounds to nearest, under-powering the test.
        """import sys

p, e = (float(x) for x in sys.stdin.read().split()[:2])
print(round(1.96 * 1.96 * p * (1 - p) / (e * e)))
""",
        # Truncates.
        """import sys

p, e = (float(x) for x in sys.stdin.read().split()[:2])
print(int(1.96 * 1.96 * p * (1 - p) / (e * e)))
""",
        # z = 2, and e not squared.
        """import sys
import math

p, e = (float(x) for x in sys.stdin.read().split()[:2])
print(math.ceil(4 * p * (1 - p) / e))
""",
    ],
)

_problem(
    id="an-stats-uplift",
    title="Absolute and Relative Uplift",
    skill_id="statistics_business",
    concept="significance",
    difficulty=4,
    minutes=22,
    summary="Percentage points and percent are different units, and confusing them oversells a result.",
    statement=(
        "Two rates are given as decimal fractions: a baseline and a variant.\n\n"
        "Print the **absolute** uplift in percentage points to two decimal "
        "places, then the **relative** uplift as a percentage of the baseline "
        "to one decimal place, space separated. Going from 0.02 to 0.03 is "
        "`1.00` percentage points and `50.0` percent — reporting the second "
        "number as points is how a modest result gets oversold.\n\n"
        "When the baseline is 0 there is no relative uplift: print the absolute "
        "figure then `NA`."
    ),
    input_format="One line: baseline and variant, space separated decimal fractions.",
    output_format="One line: absolute uplift in points (two decimals), then relative uplift in percent (one decimal) or `NA`.",
    constraints=["0 <= baseline <= 1", "0 <= variant <= 1", "At most six decimal places each"],
    requirements=[
        "Absolute uplift is (variant - baseline) * 100, in percentage points",
        "Relative uplift is (variant - baseline) / baseline * 100",
        "Print NA for the relative uplift when the baseline is zero",
        "A decline is reported as a negative number, not an absolute value",
    ],
    examples=[
        {
            "stdin": "0.02 0.03\n",
            "explanation": "One percentage point of absolute uplift is a 50.0 percent relative gain.",
        }
    ],
    cases=[
        ("sample: modest absolute, large relative", "0.02 0.03\n", False),
        ("sample: a decline", "0.10 0.08\n", False),
        ("hidden: zero baseline", "0 0.05\n", True),
        ("hidden: no change", "0.25 0.25\n", True),
        ("hidden: variant drops to zero", "0.04 0\n", True),
        ("hidden: doubling a small rate", "0.001 0.002\n", True),
    ],
    reference="""import sys


def main():
    baseline, variant = (float(x) for x in sys.stdin.read().split()[:2])
    absolute = (variant - baseline) * 100
    if baseline == 0:
        print(f"{absolute:.2f} NA")
        return
    relative = (variant - baseline) / baseline * 100
    print(f"{absolute:.2f} {relative:.1f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def uplift(baseline, variant):
    # TODO: return (absolute_points, relative_percent), with relative None when
    # the baseline is zero.
    return 0.0, 0.0


def main():
    baseline, variant = (float(x) for x in sys.stdin.read().split()[:2])
    absolute, relative = uplift(baseline, variant)
    print(f"{absolute:.2f} NA" if relative is None else f"{absolute:.2f} {relative:.1f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Relative uplift measured against the variant.
        """import sys

baseline, variant = (float(x) for x in sys.stdin.read().split()[:2])
absolute = (variant - baseline) * 100
if variant == 0:
    print(f"{absolute:.2f} NA")
else:
    print(f"{absolute:.2f} {(variant - baseline) / variant * 100:.1f}")
""",
        # Absolute uplift reported as a fraction, not points.
        """import sys

baseline, variant = (float(x) for x in sys.stdin.read().split()[:2])
absolute = variant - baseline
if baseline == 0:
    print(f"{absolute:.2f} NA")
else:
    print(f"{absolute:.2f} {(variant - baseline) / baseline * 100:.1f}")
""",
        # Reports the magnitude, hiding a decline.
        """import sys

baseline, variant = (float(x) for x in sys.stdin.read().split()[:2])
absolute = abs(variant - baseline) * 100
if baseline == 0:
    print(f"{absolute:.2f} NA")
else:
    print(f"{absolute:.2f} {abs(variant - baseline) / baseline * 100:.1f}")
""",
    ],
)

_problem(
    id="an-stats-expected-value",
    title="Expected Value of a Scenario Model",
    skill_id="statistics_business",
    concept="sampling",
    difficulty=5,
    minutes=24,
    summary="Sum payoff times probability — after checking the probabilities are a distribution at all.",
    statement=(
        "Each row is a scenario: a payoff and its probability. Print the "
        "expected value — `sum(payoff * probability)` — to two decimal places."
        "\n\nFirst validate the input: the probabilities must sum to 1 within "
        "`1e-6`. If they do not, the model is not a distribution and the "
        "expected value is meaningless — print `invalid` instead of a number."
    ),
    input_format="Line 1: n. Next n lines: `payoff,probability` where payoff is a decimal and probability is a decimal fraction.",
    output_format="One line: the expected value to two decimal places, or `invalid`.",
    constraints=["1 <= n <= 20000", "-1000000 <= payoff <= 1000000", "0 <= probability <= 1"],
    requirements=[
        "Check the probabilities sum to 1 within a tolerance of 1e-6",
        "Print 'invalid' when they do not, rather than a number computed anyway",
        "Otherwise print the sum of payoff times probability to two decimal places",
        "Negative payoffs count against the expectation",
    ],
    examples=[
        {
            "stdin": "2\n100,0.25\n-20,0.75\n",
            "explanation": "25 minus 15 is 10.00, and the probabilities sum to exactly 1.",
        }
    ],
    cases=[
        ("sample: a gamble with a downside", "2\n100,0.25\n-20,0.75\n", False),
        ("sample: probabilities do not sum to one", "2\n100,0.25\n50,0.25\n", False),
        ("hidden: certainty", "1\n42.50,1\n", True),
        ("hidden: tolerance accepts rounding noise", "3\n10,0.333333\n10,0.333333\n10,0.333334\n", True),
        # Ten tenths sum to 0.9999999999999999 in binary floating point, so an
        # exact `== 1.0` check rejects a perfectly valid distribution.
        ("hidden: ten tenths are still a distribution", "10\n" + "".join(f"{i},0.1\n" for i in range(1, 11)), True),
        ("hidden: just outside the tolerance is invalid", "2\n10,0.5\n10,0.4999\n", True),
        ("hidden: every payoff negative", "2\n-100,0.5\n-50,0.5\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    total_probability = 0.0
    expected = 0.0
    for line in data[1:1 + n]:
        payoff, probability = line.strip().split(",")
        total_probability += float(probability)
        expected += float(payoff) * float(probability)
    if abs(total_probability - 1.0) > 1e-6:
        print("invalid")
        return
    print(f"{expected:.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def expected_value(rows):
    # TODO: return the expected value, or None when the probabilities do not
    # sum to 1 within 1e-6.
    return 0.0


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = [line.strip().split(",") for line in data[1:1 + n]]
    result = expected_value(rows)
    print("invalid" if result is None else f"{result:.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # No validation at all.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
expected = 0.0
for line in data[1:1 + n]:
    payoff, probability = line.strip().split(",")
    expected += float(payoff) * float(probability)
print(f"{expected:.2f}")
""",
        # Exact equality: rounding noise is rejected as invalid.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
total = 0.0
expected = 0.0
for line in data[1:1 + n]:
    payoff, probability = line.strip().split(",")
    total += float(probability)
    expected += float(payoff) * float(probability)
print(f"{expected:.2f}" if total == 1.0 else "invalid")
""",
        # Averages the payoffs, ignoring the probabilities.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
payoffs = []
total = 0.0
for line in data[1:1 + n]:
    payoff, probability = line.strip().split(",")
    payoffs.append(float(payoff))
    total += float(probability)
if abs(total - 1.0) > 1e-6:
    print("invalid")
else:
    print(f"{sum(payoffs) / len(payoffs):.2f}")
""",
    ],
)

_problem(
    id="an-stats-zscore-flags",
    title="Flag the Values More Than Two Sigma Out",
    skill_id="statistics_business",
    concept="variance",
    difficulty=5,
    minutes=24,
    summary="Standardise a column and count what sits beyond two population standard deviations.",
    statement=(
        "Standardise the column with the **population** standard deviation "
        "(dividing by `n`, because these values are the whole population, not a "
        "sample of it) and print how many values have `|z| > 2`.\n\n"
        "When the standard deviation is 0 every value equals the mean, so "
        "nothing is unusual and the answer is `0` — not a division by zero."
    ),
    input_format="Line 1: n. Line 2: n space-separated integers.",
    output_format="One line: the count of values with |z| greater than 2.",
    constraints=["1 <= n <= 20000", "-1000000 <= value <= 1000000", "Use the population standard deviation"],
    requirements=[
        "Use the population standard deviation, dividing by n",
        "Flag a value only when |z| is strictly greater than 2",
        "Print 0 when the standard deviation is zero",
        "Print a plain integer count",
    ],
    examples=[
        {
            "stdin": "5\n1 1 1 1 100\n",
            "explanation": (
                "The mean is 20.8 and the population sd 39.6, so the 100 sits "
                "at z = 2.00 — not strictly greater than 2, so nothing is "
                "flagged."
            ),
        }
    ],
    cases=[
        ("sample: exactly two sigma is not flagged", "5\n1 1 1 1 100\n", False),
        ("sample: nothing unusual", "4\n1 2 3 4\n", False),
        ("hidden: identical values", "3\n5 5 5\n", True),
        ("hidden: one clear outlier", "10\n1 1 1 1 1 1 1 1 1 100\n", True),
        ("hidden: single value", "1\n7\n", True),
        ("hidden: outliers on both sides", "10\n-100 1 1 1 1 1 1 1 1 100\n", True),
    ],
    reference="""import sys
import math


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    mean = sum(values) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / n)
    if sd == 0:
        print(0)
        return
    print(sum(1 for v in values if abs((v - mean) / sd) > 2))


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def unusual_count(values):
    # TODO: count values whose |z| exceeds 2, using the population sd.
    return 0


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    print(unusual_count(values))


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Sample standard deviation shifts every z, and crashes when n is 1.
        """import sys
import math

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
mean = sum(values) / n
sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
print(sum(1 for v in values if sd and abs((v - mean) / sd) > 2))
""",
        # `>=` flags the value sitting exactly on two sigma.
        """import sys
import math

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
mean = sum(values) / n
sd = math.sqrt(sum((v - mean) ** 2 for v in values) / n)
if sd == 0:
    print(0)
else:
    print(sum(1 for v in values if abs((v - mean) / sd) >= 2))
""",
        # Only looks for values above the mean.
        """import sys
import math

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
mean = sum(values) / n
sd = math.sqrt(sum((v - mean) ** 2 for v in values) / n)
if sd == 0:
    print(0)
else:
    print(sum(1 for v in values if (v - mean) / sd > 2))
""",
    ],
)

_problem(
    id="an-stats-segment-paradox",
    title="Does the Winner Survive Segmentation?",
    skill_id="statistics_business",
    concept="significance",
    difficulty=8,
    minutes=35,
    summary="Compare A and B overall and within every segment, and say when the two disagree.",
    statement=(
        "Each row gives one segment's results for both variants: `segment, ca, "
        "na, cb, nb`.\n\n"
        "Print the overall winner on the pooled totals — `A`, `B` or `tie` — "
        "then a space, then `consistent` when every segment's winner agrees "
        "with the overall winner, or `paradox` when at least one segment "
        "disagrees. Compare conversion rates, not raw conversion counts.\n\n"
        "A segment with zero visitors on either side has no winner and is "
        "ignored for the consistency check. A tie in a segment counts as "
        "agreeing with any overall verdict."
    ),
    input_format="Line 1: n. Next n lines: `segment,ca,na,cb,nb`, integers.",
    output_format="One line: the overall winner (`A`, `B` or `tie`), a space, then `consistent` or `paradox`.",
    constraints=[
        "1 <= n <= 20000",
        "0 <= ca <= na <= 1000000 and 0 <= cb <= nb <= 1000000",
        "Segment names contain no commas",
    ],
    requirements=[
        "Determine the overall winner from the pooled conversion rates, not the counts",
        "Determine each segment's winner from that segment's rates",
        "Report 'paradox' when any segment's winner contradicts the overall winner",
        "Ignore segments where either variant has no visitors, and treat a segment tie as agreeing",
    ],
    examples=[
        {
            "stdin": "2\nmobile,10,100,60,500\ndesktop,80,200,25,50\n",
            "explanation": (
                "Pooled, A converts 90/300 = 0.30 and B 85/550 = 0.155, so A "
                "wins overall — but B wins the mobile segment (0.12 against "
                "0.10), so the segments disagree."
            ),
        }
    ],
    cases=[
        ("sample: a segment disagrees", "2\nmobile,10,100,60,500\ndesktop,80,200,25,50\n", False),
        ("sample: everyone agrees", "2\ns1,10,100,20,100\ns2,5,100,15,100\n", False),
        ("hidden: overall tie", "2\nx,10,100,10,100\ny,20,100,20,100\n", True),
        ("hidden: segment with no visitors is ignored", "2\nreal,10,100,20,100\nempty,0,0,0,0\n", True),
        ("hidden: segment tie counts as agreement", "2\na,10,100,20,100\nb,5,50,5,50\n", True),
        ("hidden: counts and rates disagree", "1\nonly,10,10,20,100\n", True),
    ],
    reference="""import sys


def winner(ca, na, cb, nb):
    if na == 0 or nb == 0:
        return None
    pa, pb = ca / na, cb / nb
    if abs(pa - pb) < 1e-12:
        return "tie"
    return "A" if pa > pb else "B"


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    total = [0, 0, 0, 0]
    segments = []
    for line in data[1:1 + n]:
        parts = line.strip().split(",")
        ca, na, cb, nb = (int(x) for x in parts[1:5])
        total[0] += ca
        total[1] += na
        total[2] += cb
        total[3] += nb
        segments.append(winner(ca, na, cb, nb))
    overall = winner(*total) or "tie"
    consistent = all(
        result is None or result == "tie" or result == overall for result in segments
    )
    print(f"{overall} {'consistent' if consistent else 'paradox'}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def winner(ca, na, cb, nb):
    # TODO: 'A', 'B', 'tie', or None when either variant has no visitors.
    return "tie"


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    total = [0, 0, 0, 0]
    segments = []
    for line in data[1:1 + n]:
        parts = line.strip().split(",")
        ca, na, cb, nb = (int(x) for x in parts[1:5])
        total[0] += ca
        total[1] += na
        total[2] += cb
        total[3] += nb
        segments.append(winner(ca, na, cb, nb))
    overall = winner(*total) or "tie"
    consistent = all(r is None or r == "tie" or r == overall for r in segments)
    print(f"{overall} {'consistent' if consistent else 'paradox'}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Compares raw conversion counts rather than rates.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
total_a = total_b = 0
segments = []
for line in data[1:1 + n]:
    parts = line.strip().split(",")
    ca, na, cb, nb = (int(x) for x in parts[1:5])
    total_a += ca
    total_b += cb
    if ca == cb:
        segments.append("tie")
    else:
        segments.append("A" if ca > cb else "B")
overall = "tie" if total_a == total_b else ("A" if total_a > total_b else "B")
consistent = all(r == "tie" or r == overall for r in segments)
print(f"{overall} {'consistent' if consistent else 'paradox'}")
""",
        # A segment tie is treated as a disagreement.
        """import sys


def winner(ca, na, cb, nb):
    if na == 0 or nb == 0:
        return None
    pa, pb = ca / na, cb / nb
    if abs(pa - pb) < 1e-12:
        return "tie"
    return "A" if pa > pb else "B"


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
total = [0, 0, 0, 0]
segments = []
for line in data[1:1 + n]:
    parts = line.strip().split(",")
    ca, na, cb, nb = (int(x) for x in parts[1:5])
    total[0] += ca
    total[1] += na
    total[2] += cb
    total[3] += nb
    segments.append(winner(ca, na, cb, nb))
overall = winner(*total) or "tie"
consistent = all(r == overall for r in segments if r is not None)
print(f"{overall} {'consistent' if consistent else 'paradox'}")
""",
        # Averages the segment rates instead of pooling the totals.
        """import sys


def winner(ca, na, cb, nb):
    if na == 0 or nb == 0:
        return None
    pa, pb = ca / na, cb / nb
    if abs(pa - pb) < 1e-12:
        return "tie"
    return "A" if pa > pb else "B"


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rates_a = []
rates_b = []
segments = []
for line in data[1:1 + n]:
    parts = line.strip().split(",")
    ca, na, cb, nb = (int(x) for x in parts[1:5])
    if na and nb:
        rates_a.append(ca / na)
        rates_b.append(cb / nb)
    segments.append(winner(ca, na, cb, nb))
if not rates_a:
    overall = "tie"
else:
    mean_a = sum(rates_a) / len(rates_a)
    mean_b = sum(rates_b) / len(rates_b)
    overall = "tie" if abs(mean_a - mean_b) < 1e-12 else ("A" if mean_a > mean_b else "B")
consistent = all(r is None or r == "tie" or r == overall for r in segments)
print(f"{overall} {'consistent' if consistent else 'paradox'}")
""",
    ],
)


# =========================================================================== #
#  data_visualization                                                         #
#                                                                             #
#  A chart cannot be graded by looking at it, so each of these grades the      #
#  *decision* behind the chart — the scaling, the encoding, the tick step,     #
#  the bucketing — as text. That is the part a learner gets wrong, and it is   #
#  checkable.                                                                 #
# =========================================================================== #

_problem(
    id="an-viz-bar-chart",
    title="Render a Bar Chart in Text",
    skill_id="data_visualization",
    concept="encoding",
    difficulty=4,
    minutes=22,
    summary="Scale bars against the largest value so the lengths encode the data proportionally.",
    statement=(
        "Draw a horizontal bar chart. Each bar is `#` repeated "
        "`round(value / max_value * 20)` times, so the longest bar is 20 "
        "characters and every other bar is proportional to it. Use Python's "
        "`round`, which rounds a `.5` to the nearest even number.\n\n"
        "Print one line per row in input order, formatted as `label|bar`. A "
        "value of 0 produces an empty bar (`label|`). When the maximum value is "
        "0 every bar is empty."
    ),
    input_format="Line 1: n. Next n lines: `label,value` where value is a non-negative integer.",
    output_format="One line per row: the label, a `|`, then the bar.",
    constraints=["1 <= n <= 2000", "0 <= value <= 1000000", "Labels contain no commas"],
    requirements=[
        "Scale every bar against the largest value in the data, not against a fixed constant",
        "The longest bar is exactly 20 characters",
        "Preserve input order",
        "Handle a maximum of 0 without dividing by zero",
    ],
    examples=[
        {
            "stdin": "3\nemea,100\napac,50\namer,0\n",
            "explanation": (
                "100 is the maximum so it fills 20 characters, 50 gets 10, and "
                "0 gets none."
            ),
        }
    ],
    cases=[
        ("sample: full, half and empty bars", "3\nemea,100\napac,50\namer,0\n", False),
        ("sample: a single row", "1\nsolo,7\n", False),
        ("hidden: every value zero", "2\na,0\nb,0\n", True),
        ("hidden: rounding, not truncation", "2\nbig,40\nsmall,3\n", True),
        ("hidden: values far above 20", "3\nx,1000000\ny,500000\nz,1\n", True),
        ("hidden: input order is preserved", "3\nlast,1\nmiddle,2\nfirst,3\n", True),
    ],
    reference="""import sys

WIDTH = 20


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = []
    for line in data[1:1 + n]:
        label, value = line.strip().rsplit(",", 1)
        rows.append((label, int(value)))
    largest = max(value for _label, value in rows)
    for label, value in rows:
        length = 0 if largest == 0 else round(value / largest * WIDTH)
        print(f"{label}|{'#' * length}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys

WIDTH = 20


def bar_length(value, largest):
    # TODO: return round(value / largest * WIDTH), and 0 when largest is 0.
    return 0


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = []
    for line in data[1:1 + n]:
        label, value = line.strip().rsplit(",", 1)
        rows.append((label, int(value)))
    largest = max(value for _label, value in rows)
    for label, value in rows:
        print(f"{label}|{'#' * bar_length(value, largest)}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Unscaled: the bar is the raw value.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    label, value = line.strip().rsplit(",", 1)
    print(f"{label}|{'#' * min(int(value), 20)}")
""",
        # Truncates instead of rounding.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rows = []
for line in data[1:1 + n]:
    label, value = line.strip().rsplit(",", 1)
    rows.append((label, int(value)))
largest = max(v for _l, v in rows) or 1
for label, value in rows:
    print(f"{label}|{'#' * int(value / largest * 20)}")
""",
        # Sorts the rows, silently reordering the chart.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rows = []
for line in data[1:1 + n]:
    label, value = line.strip().rsplit(",", 1)
    rows.append((label, int(value)))
largest = max(v for _l, v in rows)
for label, value in sorted(rows, key=lambda kv: -kv[1]):
    length = 0 if largest == 0 else round(value / largest * 20)
    print(f"{label}|{'#' * length}")
""",
    ],
)

_problem(
    id="an-viz-tick-step",
    title="Choose a Readable Axis Tick Step",
    skill_id="data_visualization",
    concept="axis truncation",
    difficulty=6,
    minutes=28,
    summary="Pick the tick step from the 1-2-5 family so the axis has at most five ticks.",
    statement=(
        "Choose an axis tick step from the `1, 2, 5 × 10^k` family — so "
        "..., 0.5 is not allowed here, only integers: 1, 2, 5, 10, 20, 50, 100 "
        "and so on.\n\n"
        "Pick the **smallest** such step for which `ceil(max_value / step)` is "
        "at most 5, so the axis never carries more than five ticks. Then print "
        "the step and the top tick, `step top`, where the top tick is "
        "`ceil(max_value / step) * step` — the first tick at or above the "
        "largest value.\n\n"
        "When the maximum value is 0 the answer is `1 0`."
    ),
    input_format="Line 1: n. Line 2: n space-separated non-negative integers.",
    output_format="One line: the step and the top tick, space separated.",
    constraints=["1 <= n <= 20000", "0 <= value <= 1000000000"],
    requirements=[
        "Only 1, 2 and 5 times a power of ten are candidate steps",
        "Choose the smallest candidate giving at most five ticks",
        "The top tick is the first multiple of the step at or above the maximum",
        "A maximum of 0 gives step 1 and top tick 0",
    ],
    examples=[
        {
            "stdin": "3\n7 3 9\n",
            "explanation": (
                "A step of 1 needs 9 ticks and 2 needs 5 — which is allowed — "
                "so the step is 2 and the top tick 10."
            ),
        }
    ],
    cases=[
        ("sample: step of two", "3\n7 3 9\n", False),
        ("sample: exact multiple needs no extra tick", "2\n10 5\n", False),
        ("hidden: maximum of zero", "2\n0 0\n", True),
        ("hidden: maximum of one", "1\n1\n", True),
        ("hidden: five is a valid step", "1\n23\n", True),
        ("hidden: large values step up a power of ten", "2\n1 999999999\n", True),
        ("hidden: exactly five ticks is allowed", "1\n5\n", True),
        # A step of 1 would need six ticks, which the rule does not allow.
        ("hidden: six ticks is one too many", "1\n6\n", True),
    ],
    reference="""import sys
import math


def steps():
    power = 1
    while True:
        for base in (1, 2, 5):
            yield base * power
        power *= 10


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    largest = max(values)
    if largest == 0:
        print("1 0")
        return
    for step in steps():
        ticks = math.ceil(largest / step)
        if ticks <= 5:
            print(f"{step} {ticks * step}")
            return


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def axis(largest):
    # TODO: return (step, top_tick) using the smallest 1/2/5 * 10^k step that
    # gives at most five ticks.
    return 1, largest


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    step, top = axis(max(values))
    print(f"{step} {top}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Powers of ten only: no 2 or 5, so the step is often too coarse.
        """import sys
import math

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
largest = max(values)
if largest == 0:
    print("1 0")
else:
    step = 1
    while math.ceil(largest / step) > 5:
        step *= 10
    print(f"{step} {math.ceil(largest / step) * step}")
""",
        # Allows six ticks, so it picks a finer step than the rule permits.
        """import sys
import math


def steps():
    power = 1
    while True:
        for base in (1, 2, 5):
            yield base * power
        power *= 10


data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
largest = max(values)
if largest == 0:
    print("1 0")
else:
    for step in steps():
        ticks = math.ceil(largest / step)
        if ticks <= 6:
            print(f"{step} {ticks * step}")
            break
""",
        # Top tick truncated below the largest value, so a bar leaves the axis.
        """import sys
import math


def steps():
    power = 1
    while True:
        for base in (1, 2, 5):
            yield base * power
        power *= 10


data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
largest = max(values)
if largest == 0:
    print("1 0")
else:
    for step in steps():
        if math.ceil(largest / step) <= 5:
            print(f"{step} {largest // step * step}")
            break
""",
    ],
)

_problem(
    id="an-viz-percent-stacked",
    title="Normalise a Stacked Bar to Percentages",
    skill_id="data_visualization",
    concept="encoding",
    difficulty=4,
    minutes=22,
    summary="Each row becomes its own 100%, and a row that totals zero is reported as such.",
    statement=(
        "A stacked bar chart compares composition, so each bar is normalised to "
        "100% of **its own** row total — not of the largest row and not of the "
        "grand total.\n\n"
        "For each row print `label a_pct b_pct`, each percentage to one decimal "
        "place. A row whose two values are both 0 has no composition: print "
        "`label NA NA`."
    ),
    input_format="Line 1: n. Next n lines: `label,a,b` with non-negative integers.",
    output_format="One line per row in input order: the label and the two percentages, or NA NA.",
    constraints=["1 <= n <= 20000", "0 <= a, b <= 1000000"],
    requirements=[
        "Normalise each row against its own total",
        "Print each percentage to one decimal place",
        "Print 'NA NA' for a row whose total is zero",
        "Keep the rows in input order",
    ],
    examples=[
        {
            "stdin": "2\nq1,30,70\nq2,1,1\n",
            "explanation": "q1 splits 30.0/70.0 and q2 splits 50.0/50.0, each of its own total.",
        }
    ],
    cases=[
        ("sample: two compositions", "2\nq1,30,70\nq2,1,1\n", False),
        ("sample: rows of very different sizes", "2\nbig,900,100\nsmall,9,1\n", False),
        ("hidden: empty row", "2\nreal,1,3\nempty,0,0\n", True),
        ("hidden: one side is zero", "2\nall_a,5,0\nall_b,0,5\n", True),
        ("hidden: thirds round to one decimal", "1\nthirds,1,2\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    for line in data[1:1 + n]:
        label, a, b = line.strip().rsplit(",", 2)
        total = int(a) + int(b)
        if total == 0:
            print(f"{label} NA NA")
        else:
            print(f"{label} {int(a) * 100.0 / total:.1f} {int(b) * 100.0 / total:.1f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def shares(a, b):
    # TODO: return (a_pct, b_pct) of the row total, or None when it is zero.
    return 0.0, 0.0


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    for line in data[1:1 + n]:
        label, a, b = line.strip().rsplit(",", 2)
        result = shares(int(a), int(b))
        if result is None:
            print(f"{label} NA NA")
        else:
            print(f"{label} {result[0]:.1f} {result[1]:.1f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Normalised against the grand total across every row.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rows = []
grand = 0
for line in data[1:1 + n]:
    label, a, b = line.strip().rsplit(",", 2)
    rows.append((label, int(a), int(b)))
    grand += int(a) + int(b)
for label, a, b in rows:
    if grand == 0:
        print(f"{label} NA NA")
    else:
        print(f"{label} {a * 100.0 / grand:.1f} {b * 100.0 / grand:.1f}")
""",
        # Zero row printed as 0.0 0.0, implying a composition that is not there.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    label, a, b = line.strip().rsplit(",", 2)
    total = int(a) + int(b)
    if total == 0:
        print(f"{label} 0.0 0.0")
    else:
        print(f"{label} {int(a) * 100.0 / total:.1f} {int(b) * 100.0 / total:.1f}")
""",
        # Fractions rather than percentages.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    label, a, b = line.strip().rsplit(",", 2)
    total = int(a) + int(b)
    if total == 0:
        print(f"{label} NA NA")
    else:
        print(f"{label} {int(a) / total:.1f} {int(b) / total:.1f}")
""",
    ],
)

_problem(
    id="an-viz-truncated-axis",
    title="Detect a Misleading Truncated Axis",
    skill_id="data_visualization",
    concept="axis truncation",
    difficulty=6,
    minutes=28,
    summary="Quantify how much a non-zero baseline exaggerates the difference between two bars.",
    statement=(
        "A bar chart with a non-zero baseline exaggerates differences: the bar "
        "*lengths* stop encoding the values.\n\n"
        "Given a baseline and two values, print the honest ratio (larger over "
        "smaller, using the values themselves) and the drawn ratio (using "
        "`value - baseline` for each bar), each to two decimal places, then a "
        "verdict: `misleading` when the drawn ratio is more than 1.5 times the "
        "honest ratio, otherwise `ok`.\n\n"
        "The baseline is never above either value. If the smaller value equals "
        "the baseline the drawn ratio is infinite: print `inf` in its place and "
        "the verdict `misleading`. If the smaller value is 0 the honest ratio is "
        "undefined: print `NA NA ok`."
    ),
    input_format="One line: baseline, value1, value2 — three non-negative integers, space separated.",
    output_format="One line: the honest ratio, the drawn ratio and the verdict.",
    constraints=[
        "0 <= baseline <= min(value1, value2)",
        "0 <= value1, value2 <= 1000000",
        "The 1.5 factor is the threshold",
    ],
    requirements=[
        "The honest ratio uses the values as they are",
        "The drawn ratio uses each value minus the baseline",
        "Report 'misleading' when the drawn ratio exceeds 1.5 times the honest ratio",
        "Handle the smaller value equalling the baseline, and a smaller value of 0",
    ],
    examples=[
        {
            "stdin": "90 100 95\n",
            "explanation": (
                "100 against 95 is a ratio of 1.05, but drawn from a baseline of "
                "90 the bars are 10 and 5 — a ratio of 2.00, so the chart is "
                "misleading."
            ),
        }
    ],
    cases=[
        ("sample: classic truncation", "90 100 95\n", False),
        ("sample: honest zero baseline", "0 100 95\n", False),
        ("hidden: smaller value sits on the baseline", "95 100 95\n", True),
        ("hidden: smaller value is zero", "0 100 0\n", True),
        ("hidden: equal values", "5 20 20\n", True),
        ("hidden: mild truncation stays ok", "1 100 95\n", True),
        # Drawn ratio 2.25 against an honest ratio of 2.00: above 1.5 in
        # absolute terms, but not an exaggeration of what the data says.
        ("hidden: a big honest ratio is not exaggeration", "10 100 50\n", True),
    ],
    reference="""import sys


def main():
    baseline, first, second = (int(x) for x in sys.stdin.read().split()[:3])
    larger, smaller = max(first, second), min(first, second)
    if smaller == 0:
        print("NA NA ok")
        return
    honest = larger / smaller
    drawn_smaller = smaller - baseline
    if drawn_smaller == 0:
        print(f"{honest:.2f} inf misleading")
        return
    drawn = (larger - baseline) / drawn_smaller
    verdict = "misleading" if drawn > 1.5 * honest else "ok"
    print(f"{honest:.2f} {drawn:.2f} {verdict}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def assess(baseline, first, second):
    # TODO: return (honest_ratio, drawn_ratio, verdict) following the rules,
    # using None for a ratio that does not exist.
    return None, None, "ok"


def main():
    baseline, first, second = (int(x) for x in sys.stdin.read().split()[:3])
    honest, drawn, verdict = assess(baseline, first, second)
    honest_text = "NA" if honest is None else f"{honest:.2f}"
    drawn_text = "NA" if drawn is None else (drawn if isinstance(drawn, str) else f"{drawn:.2f}")
    print(f"{honest_text} {drawn_text} {verdict}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Ignores the baseline entirely: never finds a truncated axis.
        """import sys

baseline, first, second = (int(x) for x in sys.stdin.read().split()[:3])
larger, smaller = max(first, second), min(first, second)
if smaller == 0:
    print("NA NA ok")
else:
    honest = larger / smaller
    print(f"{honest:.2f} {honest:.2f} ok")
""",
        # Compares the drawn ratio against a fixed 1.5 rather than against the
        # honest ratio.
        """import sys

baseline, first, second = (int(x) for x in sys.stdin.read().split()[:3])
larger, smaller = max(first, second), min(first, second)
if smaller == 0:
    print("NA NA ok")
elif smaller - baseline == 0:
    print(f"{larger / smaller:.2f} inf misleading")
else:
    honest = larger / smaller
    drawn = (larger - baseline) / (smaller - baseline)
    print(f"{honest:.2f} {drawn:.2f} {'misleading' if drawn > 1.5 else 'ok'}")
""",
        # Subtracts the baseline from the numerator only.
        """import sys

baseline, first, second = (int(x) for x in sys.stdin.read().split()[:3])
larger, smaller = max(first, second), min(first, second)
if smaller == 0:
    print("NA NA ok")
else:
    honest = larger / smaller
    drawn = (larger - baseline) / smaller
    print(f"{honest:.2f} {drawn:.2f} {'misleading' if drawn > 1.5 * honest else 'ok'}")
""",
    ],
)

_problem(
    id="an-viz-compact-labels",
    title="Format Axis Labels Compactly",
    skill_id="data_visualization",
    concept="annotation",
    difficulty=5,
    minutes=24,
    summary="1200 becomes 1.2k — with the exact rules for the boundaries and the trailing zero.",
    statement=(
        "Format each value as a compact axis label:\n\n"
        "* below 1000: the integer as it is (`999`),\n"
        "* 1000 up to but not including 1000000: thousands with one decimal "
        "place and a `k` suffix (`1.2k`),\n"
        "* 1000000 and above: millions with one decimal place and an `M` suffix "
        "(`3.4M`).\n\n"
        "Round the decimal to one place, and **drop a trailing `.0`**: 2000 is "
        "`2k`, not `2.0k`. Negative values keep their sign: -1500 is `-1.5k`. "
        "Print one label per line."
    ),
    input_format="Line 1: n. Next n lines: one integer.",
    output_format="One label per line.",
    constraints=["1 <= n <= 20000", "-1000000000 <= value <= 1000000000"],
    requirements=[
        "Below 1000 in magnitude, print the integer unchanged",
        "Use k for thousands and M for millions, with at most one decimal place",
        "Drop a trailing .0 so 2000 is '2k'",
        "Keep the minus sign for negative values",
    ],
    examples=[
        {
            "stdin": "4\n999\n1200\n2000\n3400000\n",
            "explanation": "999 is below the threshold, 1200 is 1.2k, 2000 loses its .0, and 3.4M is millions.",
        }
    ],
    cases=[
        ("sample: one of each rule", "4\n999\n1200\n2000\n3400000\n", False),
        ("sample: zero and one", "2\n0\n1\n", False),
        ("hidden: exact boundaries", "3\n1000\n999999\n1000000\n", True),
        ("hidden: negatives", "3\n-1500\n-999\n-2000000\n", True),
        ("hidden: rounding up a decimal", "2\n1250\n1949\n", True),
        ("hidden: rounding lands on a whole number", "2\n1999\n1049\n", True),
    ],
    reference="""import sys


def compact(value):
    magnitude = abs(value)
    if magnitude < 1000:
        return str(value)
    if magnitude < 1000000:
        scaled, suffix = value / 1000.0, "k"
    else:
        scaled, suffix = value / 1000000.0, "M"
    text = f"{scaled:.1f}"
    if text.endswith(".0"):
        text = text[:-2]
    return text + suffix


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    for line in data[1:1 + n]:
        print(compact(int(line.strip())))


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def compact(value):
    # TODO: return the compact label, following the k/M rules and dropping a
    # trailing '.0'.
    return str(value)


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    for line in data[1:1 + n]:
        print(compact(int(line.strip())))


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Keeps the trailing .0.
        """import sys


def compact(value):
    magnitude = abs(value)
    if magnitude < 1000:
        return str(value)
    if magnitude < 1000000:
        return f"{value / 1000.0:.1f}k"
    return f"{value / 1000000.0:.1f}M"


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    print(compact(int(line.strip())))
""",
        # Boundary off by one: 1000 prints as 1000 rather than 1k.
        """import sys


def compact(value):
    magnitude = abs(value)
    if magnitude <= 1000:
        return str(value)
    if magnitude <= 1000000:
        text = f"{value / 1000.0:.1f}"
    else:
        text = f"{value / 1000000.0:.1f}"
    if text.endswith(".0"):
        text = text[:-2]
    return text + ("k" if magnitude <= 1000000 else "M")


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    print(compact(int(line.strip())))
""",
        # Truncates instead of rounding, so 1949 reads as 1.9k... and 1999 too.
        """import sys


def compact(value):
    magnitude = abs(value)
    if magnitude < 1000:
        return str(value)
    if magnitude < 1000000:
        scaled, suffix = value / 1000.0, "k"
    else:
        scaled, suffix = value / 1000000.0, "M"
    truncated = int(scaled * 10) / 10.0
    text = f"{truncated:.1f}"
    if text.endswith(".0"):
        text = text[:-2]
    return text + suffix


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    print(compact(int(line.strip())))
""",
    ],
)

_problem(
    id="an-viz-other-bucket",
    title="Collapse the Long Tail Into 'Other'",
    skill_id="data_visualization",
    concept="chart choice",
    difficulty=5,
    minutes=25,
    summary="Categories below a share threshold become one Other slice, which always sorts last.",
    statement=(
        "A chart with thirty slices communicates nothing, so categories worth "
        "less than `t` percent of the total are merged into a single `Other`.\n\n"
        "Total the values per category, then print `category value` for each "
        "category whose share of the overall total is **at least** `t` percent, "
        "ordered by value descending with ties broken by category name "
        "ascending. If anything was merged, print `Other <merged total>` as the "
        "**last** line, whatever its size — Other is a residual, not a "
        "competitor, so it never sorts into the ranking."
    ),
    input_format="Line 1: n and t, space separated (t is an integer percentage). Next n lines: `category,value`, non-negative integers.",
    output_format="Ranked `category value` lines, then `Other total` when anything was merged.",
    constraints=["1 <= n <= 20000", "0 <= t <= 100", "0 <= value <= 1000000"],
    requirements=[
        "Total values per category before comparing shares",
        "Keep a category when its share is at least t percent",
        "Order the kept categories by value descending, then by name ascending",
        "Print Other last, and omit it entirely when nothing was merged",
    ],
    examples=[
        {
            "stdin": "4 10\na,50\nb,40\nc,5\nd,5\n",
            "explanation": (
                "The total is 100, so c and d at 5% each are merged into Other "
                "with 10, printed after a and b."
            ),
        }
    ],
    cases=[
        ("sample: two small categories merged", "4 10\na,50\nb,40\nc,5\nd,5\n", False),
        ("sample: nothing merged", "2 10\na,50\nb,50\n", False),
        ("hidden: Other is bigger than a kept category", "4 30\nbig,40\nsmall,30\nt1,15\nt2,15\n", True),
        ("hidden: threshold zero keeps everything", "3 0\na,1\nb,0\nc,2\n", True),
        ("hidden: everything merged", "3 60\na,34\nb,33\nc,33\n", True),
        ("hidden: repeated rows and a tie", "5 10\nz,20\na,20\nz,10\nq,1\nr,1\n", True),
        ("hidden: total of zero", "2 10\na,0\nb,0\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    header = data[0].split()
    n, threshold = int(header[0]), int(header[1])
    totals = {}
    for line in data[1:1 + n]:
        category, value = line.strip().rsplit(",", 1)
        totals[category] = totals.get(category, 0) + int(value)
    overall = sum(totals.values())
    kept = []
    other = 0
    for category, value in totals.items():
        share = 0.0 if overall == 0 else value * 100.0 / overall
        if share >= threshold:
            kept.append((category, value))
        else:
            other += value
    for category, value in sorted(kept, key=lambda kv: (-kv[1], kv[0])):
        print(f"{category} {value}")
    if len(kept) != len(totals):
        print(f"Other {other}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def split_tail(totals, threshold):
    # TODO: return (kept, other_total, merged_any) where kept is ordered by
    # value descending then name ascending.
    return list(totals.items()), 0, False


def main():
    data = sys.stdin.read().split("\\n")
    header = data[0].split()
    n, threshold = int(header[0]), int(header[1])
    totals = {}
    for line in data[1:1 + n]:
        category, value = line.strip().rsplit(",", 1)
        totals[category] = totals.get(category, 0) + int(value)
    kept, other, merged = split_tail(totals, threshold)
    for category, value in kept:
        print(f"{category} {value}")
    if merged:
        print(f"Other {other}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Other sorted into the ranking by size.
        """import sys

data = sys.stdin.read().split("\\n")
header = data[0].split()
n, threshold = int(header[0]), int(header[1])
totals = {}
for line in data[1:1 + n]:
    category, value = line.strip().rsplit(",", 1)
    totals[category] = totals.get(category, 0) + int(value)
overall = sum(totals.values())
kept = []
other = 0
merged = False
for category, value in totals.items():
    share = 0.0 if overall == 0 else value * 100.0 / overall
    if share >= threshold:
        kept.append((category, value))
    else:
        other += value
        merged = True
if merged:
    kept.append(("Other", other))
for category, value in sorted(kept, key=lambda kv: (-kv[1], kv[0])):
    print(f"{category} {value}")
""",
        # Strictly-greater threshold drops a category sitting exactly on it.
        """import sys

data = sys.stdin.read().split("\\n")
header = data[0].split()
n, threshold = int(header[0]), int(header[1])
totals = {}
for line in data[1:1 + n]:
    category, value = line.strip().rsplit(",", 1)
    totals[category] = totals.get(category, 0) + int(value)
overall = sum(totals.values()) or 1
kept = []
other = 0
for category, value in totals.items():
    if value * 100.0 / overall > threshold:
        kept.append((category, value))
    else:
        other += value
for category, value in sorted(kept, key=lambda kv: (-kv[1], kv[0])):
    print(f"{category} {value}")
if len(kept) != len(totals):
    print(f"Other {other}")
""",
        # Prints Other even when nothing was merged.
        """import sys

data = sys.stdin.read().split("\\n")
header = data[0].split()
n, threshold = int(header[0]), int(header[1])
totals = {}
for line in data[1:1 + n]:
    category, value = line.strip().rsplit(",", 1)
    totals[category] = totals.get(category, 0) + int(value)
overall = sum(totals.values())
kept = []
other = 0
for category, value in totals.items():
    share = 0.0 if overall == 0 else value * 100.0 / overall
    if share >= threshold:
        kept.append((category, value))
    else:
        other += value
for category, value in sorted(kept, key=lambda kv: (-kv[1], kv[0])):
    print(f"{category} {value}")
print(f"Other {other}")
""",
    ],
)

_problem(
    id="an-viz-sparkline",
    title="Draw a Sparkline",
    skill_id="data_visualization",
    concept="encoding",
    difficulty=5,
    minutes=25,
    summary="Map a series onto eight levels between its own minimum and maximum.",
    statement=(
        "Render a series as a sparkline using the eight levels "
        "`_.-~=+*#` (index 0 is the lowest).\n\n"
        "Each value maps to level "
        "`round((value - minimum) / (maximum - minimum) * 7)`. When every value "
        "is identical there is no range to scale against and every level is 0, "
        "so the sparkline is all `_`.\n\n"
        "Print the sparkline as a single line with no separators."
    ),
    input_format="Line 1: n. Line 2: n space-separated integers.",
    output_format="One line: n characters from `_.-~=+*#`.",
    constraints=["1 <= n <= 20000", "-1000000 <= value <= 1000000"],
    requirements=[
        "Scale against the series' own minimum and maximum",
        "Use round(), giving eight levels from 0 to 7",
        "A flat series renders as all underscores",
        "Print the characters with no separator",
    ],
    examples=[
        {
            "stdin": "5\n1 2 3 4 5\n",
            "explanation": (
                "1 maps to level 0 and 5 to level 7; the values between land on "
                "levels 2, 4 and 5."
            ),
        }
    ],
    cases=[
        ("sample: a rising series", "5\n1 2 3 4 5\n", False),
        ("sample: two values", "2\n10 20\n", False),
        ("hidden: flat series", "4\n7 7 7 7\n", True),
        ("hidden: single value", "1\n5\n", True),
        ("hidden: negatives shift the baseline", "4\n-10 0 10 -10\n", True),
        ("hidden: one spike", "5\n1 1 1 1 100\n", True),
    ],
    reference="""import sys

LEVELS = "_.-~=+*#"


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    low, high = min(values), max(values)
    span = high - low
    out = []
    for value in values:
        level = 0 if span == 0 else round((value - low) / span * 7)
        out.append(LEVELS[level])
    print("".join(out))


if __name__ == "__main__":
    main()
""",
    starter="""import sys

LEVELS = "_.-~=+*#"


def level_of(value, low, high):
    # TODO: return round((value - low) / (high - low) * 7), or 0 when the
    # series is flat.
    return 0


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    low, high = min(values), max(values)
    print("".join(LEVELS[level_of(v, low, high)] for v in values))


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Scales from zero rather than from the series minimum.
        """import sys

LEVELS = "_.-~=+*#"

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
high = max(values)
out = []
for value in values:
    level = 0 if high == 0 else round(value / high * 7)
    out.append(LEVELS[max(0, min(7, level))])
print("".join(out))
""",
        # Truncates, so the levels sit one low across the middle of the range.
        """import sys

LEVELS = "_.-~=+*#"

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
low, high = min(values), max(values)
span = high - low
out = []
for value in values:
    level = 0 if span == 0 else int((value - low) / span * 7)
    out.append(LEVELS[level])
print("".join(out))
""",
        # Eight buckets by index, so the maximum falls off the end.
        """import sys

LEVELS = "_.-~=+*#"

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
low, high = min(values), max(values)
span = high - low
out = []
for value in values:
    level = 0 if span == 0 else min(int((value - low) / span * 8), 7)
    out.append(LEVELS[level])
print("".join(out))
""",
    ],
)

_problem(
    id="an-viz-chart-choice",
    title="Pick the Right Chart for the Question",
    skill_id="data_visualization",
    concept="chart choice",
    difficulty=4,
    minutes=20,
    summary="Apply the chart-selection rules in order, so the choice is reproducible rather than a matter of taste.",
    statement=(
        "Choose a chart type from an explicit rule set. For each request you "
        "are given three fields: whether the x axis is time (`time` or "
        "`category`), how many series there are, and how many categories.\n\n"
        "Apply these rules **in order** and print the first that matches:\n\n"
        "1. x axis is time and there is exactly one series -> `line`\n"
        "2. x axis is time and there are two or more series -> `multi-line`\n"
        "3. more than 12 categories -> `bar` (a pie with 13 slices is "
        "unreadable)\n"
        "4. exactly one series and 12 or fewer categories -> `bar`\n"
        "5. otherwise -> `grouped-bar`\n\n"
        "Print one choice per line, in input order."
    ),
    input_format="Line 1: n. Next n lines: `axis,series,categories` where axis is `time` or `category`.",
    output_format="One chart name per line.",
    constraints=["1 <= n <= 20000", "1 <= series <= 100", "1 <= categories <= 10000"],
    requirements=[
        "Apply the rules in the stated order",
        "A time axis decides the chart before the category count is considered",
        "More than 12 categories never produces a grouped bar",
        "Print one answer per request, in input order",
    ],
    examples=[
        {
            "stdin": "3\ntime,1,24\ncategory,3,5\ncategory,1,4\n",
            "explanation": (
                "The first is a time series with one line. The second has "
                "several series over few categories, so grouped bars. The third "
                "is a single series over few categories: a bar chart."
            ),
        }
    ],
    cases=[
        ("sample: one of each branch", "3\ntime,1,24\ncategory,3,5\ncategory,1,4\n", False),
        ("sample: several series over time", "1\ntime,4,12\n", False),
        ("hidden: many categories force a bar", "2\ncategory,5,13\ncategory,5,12\n", True),
        ("hidden: the 12 boundary", "2\ncategory,1,12\ncategory,1,13\n", True),
        ("hidden: time beats the category count", "2\ntime,1,5000\ntime,9,5000\n", True),
        ("hidden: single series, single category", "1\ncategory,1,1\n", True),
    ],
    reference="""import sys


def choose(axis, series, categories):
    if axis == "time" and series == 1:
        return "line"
    if axis == "time":
        return "multi-line"
    if categories > 12:
        return "bar"
    if series == 1:
        return "bar"
    return "grouped-bar"


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    for line in data[1:1 + n]:
        axis, series, categories = line.strip().split(",")
        print(choose(axis, int(series), int(categories)))


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def choose(axis, series, categories):
    # TODO: apply the five rules in order and return the chart name.
    return "bar"


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    for line in data[1:1 + n]:
        axis, series, categories = line.strip().split(",")
        print(choose(axis, int(series), int(categories)))


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Category count checked before the time axis, reordering the rules.
        """import sys


def choose(axis, series, categories):
    if categories > 12:
        return "bar"
    if axis == "time" and series == 1:
        return "line"
    if axis == "time":
        return "multi-line"
    if series == 1:
        return "bar"
    return "grouped-bar"


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    axis, series, categories = line.strip().split(",")
    print(choose(axis, int(series), int(categories)))
""",
        # Boundary wrong: 12 categories treated as too many.
        """import sys


def choose(axis, series, categories):
    if axis == "time" and series == 1:
        return "line"
    if axis == "time":
        return "multi-line"
    if categories >= 12:
        return "bar"
    if series == 1:
        return "bar"
    return "grouped-bar"


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    axis, series, categories = line.strip().split(",")
    print(choose(axis, int(series), int(categories)))
""",
        # Multi-series time charts collapsed to a single line.
        """import sys


def choose(axis, series, categories):
    if axis == "time":
        return "line"
    if categories > 12 or series == 1:
        return "bar"
    return "grouped-bar"


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    axis, series, categories = line.strip().split(",")
    print(choose(axis, int(series), int(categories)))
""",
    ],
)

_problem(
    id="an-viz-colour-bins",
    title="Assign Choropleth Colour Bins",
    skill_id="data_visualization",
    concept="colour scales",
    difficulty=6,
    minutes=28,
    summary="Quantile bins, so each colour holds a similar number of regions rather than an equal value range.",
    statement=(
        "Assign each region to one of five colour bins by **quantile**, so the "
        "bins hold similar numbers of regions. Equal-width bins would give one "
        "colour to almost everything whenever the data is skewed.\n\n"
        "Sort the values ascending. Using the nearest-rank convention, the "
        "cut-points are the 20th, 40th, 60th and 80th percentiles: "
        "`rank = ceil(p / 100 * n)` clamped to 1..n, value `v[rank - 1]`. A "
        "region's bin is the number of cut-points its value is **strictly "
        "greater** than, so bins run from 0 to 4.\n\n"
        "Print `region bin` per line in input order."
    ),
    input_format="Line 1: n. Next n lines: `region,value` with integer values.",
    output_format="One line per region in input order: the name, a space, then the bin 0-4.",
    constraints=["1 <= n <= 20000", "-1000000 <= value <= 1000000"],
    requirements=[
        "Use nearest-rank quantiles at 20, 40, 60 and 80 percent",
        "A value's bin counts the cut-points it is strictly greater than",
        "Preserve input order in the output",
        "Ties get the same bin",
    ],
    examples=[
        {
            "stdin": "5\na,10\nb,20\nc,30\nd,40\ne,50\n",
            "explanation": (
                "The cut-points are 10, 20, 30 and 40, so each region lands in "
                "its own bin from 0 to 4."
            ),
        }
    ],
    cases=[
        ("sample: five evenly spread regions", "5\na,10\nb,20\nc,30\nd,40\ne,50\n", False),
        ("sample: one region", "1\nsolo,7\n", False),
        ("hidden: skewed data spreads across bins", "6\na,1\nb,1\nc,1\nd,1\ne,1\nf,1000\n", True),
        # Equal-width bins would put a, b, c and d all in bin 0 because one
        # large value stretches the range; quantile bins separate them.
        ("hidden: quantiles are not equal widths", "5\na,1\nb,2\nc,3\nd,4\ne,100\n", True),
        ("hidden: all identical", "4\na,5\nb,5\nc,5\nd,5\n", True),
        ("hidden: negatives", "5\na,-50\nb,-40\nc,-30\nd,-20\ne,-10\n", True),
        ("hidden: input order preserved", "5\ne,50\nd,40\nc,30\nb,20\na,10\n", True),
    ],
    reference="""import sys
import math


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = []
    for line in data[1:1 + n]:
        region, value = line.strip().rsplit(",", 1)
        rows.append((region, int(value)))
    ordered = sorted(value for _region, value in rows)
    cuts = []
    for p in (20, 40, 60, 80):
        rank = min(max(math.ceil(p / 100 * n), 1), n)
        cuts.append(ordered[rank - 1])
    for region, value in rows:
        print(f"{region} {sum(1 for cut in cuts if value > cut)}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def cut_points(values):
    # TODO: return the four nearest-rank quantiles at 20, 40, 60 and 80 percent.
    return [0, 0, 0, 0]


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = []
    for line in data[1:1 + n]:
        region, value = line.strip().rsplit(",", 1)
        rows.append((region, int(value)))
    cuts = cut_points([value for _region, value in rows])
    for region, value in rows:
        print(f"{region} {sum(1 for cut in cuts if value > cut)}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Equal-width bins: skewed data collapses into one colour.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rows = []
for line in data[1:1 + n]:
    region, value = line.strip().rsplit(",", 1)
    rows.append((region, int(value)))
low = min(v for _r, v in rows)
high = max(v for _r, v in rows)
span = high - low
for region, value in rows:
    bin_index = 0 if span == 0 else min(int((value - low) / span * 5), 4)
    print(f"{region} {bin_index}")
""",
        # `>=` instead of `>`, so a value sitting on a cut-point jumps a bin.
        """import sys
import math

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rows = []
for line in data[1:1 + n]:
    region, value = line.strip().rsplit(",", 1)
    rows.append((region, int(value)))
ordered = sorted(v for _r, v in rows)
cuts = []
for p in (20, 40, 60, 80):
    rank = min(max(math.ceil(p / 100 * n), 1), n)
    cuts.append(ordered[rank - 1])
for region, value in rows:
    print(f"{region} {sum(1 for cut in cuts if value >= cut)}")
""",
        # Output sorted by value, losing the input order the caller relies on.
        """import sys
import math

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rows = []
for line in data[1:1 + n]:
    region, value = line.strip().rsplit(",", 1)
    rows.append((region, int(value)))
ordered = sorted(v for _r, v in rows)
cuts = []
for p in (20, 40, 60, 80):
    rank = min(max(math.ceil(p / 100 * n), 1), n)
    cuts.append(ordered[rank - 1])
for region, value in sorted(rows, key=lambda kv: kv[1]):
    print(f"{region} {sum(1 for cut in cuts if value > cut)}")
""",
    ],
)

_problem(
    id="an-viz-annotate-extremes",
    title="Annotate Only the Points Worth Annotating",
    skill_id="data_visualization",
    concept="annotation",
    difficulty=5,
    minutes=24,
    summary="Label the peak, the trough and the biggest movement — and nothing else.",
    statement=(
        "Annotating every point is the same as annotating none, so label "
        "exactly three things on a time series:\n\n"
        "* `peak <index> <value>` — the maximum; on a tie, the **earliest** "
        "index wins.\n"
        "* `trough <index> <value>` — the minimum, same tie rule.\n"
        "* `jump <index> <delta>` — the largest absolute change from the "
        "previous point, where `index` is the later point and `delta` is the "
        "signed change. On a tie the earliest such index wins.\n\n"
        "Indexes are 1-based. Print the three lines in that order. A series of "
        "one point has no change: print `jump none` for the third line."
    ),
    input_format="Line 1: n. Line 2: n space-separated integers.",
    output_format="Three lines: the peak, the trough, and the jump (or `jump none`).",
    constraints=["1 <= n <= 20000", "-1000000 <= value <= 1000000"],
    requirements=[
        "Break ties on the peak and trough by the earliest index",
        "The jump is the largest change in absolute size, reported with its sign",
        "Index the jump by the later of the two points, 1-based",
        "Print 'jump none' when there is only one point",
    ],
    examples=[
        {
            "stdin": "5\n10 12 4 5 12\n",
            "explanation": (
                "12 is the maximum and appears first at index 2. The minimum is "
                "4 at index 3, and the biggest move is the -8 into it."
            ),
        }
    ],
    cases=[
        ("sample: tied peak takes the earlier index", "5\n10 12 4 5 12\n", False),
        ("sample: rising series", "4\n1 2 3 10\n", False),
        ("hidden: single point", "1\n5\n", True),
        ("hidden: flat series", "4\n7 7 7 7\n", True),
        ("hidden: biggest jump is upward and late", "5\n5 4 3 2 100\n", True),
        ("hidden: tied jumps take the earlier index", "5\n0 10 0 10 0\n", True),
        ("hidden: negatives", "4\n-1 -50 -2 -3\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    peak_index = min(range(n), key=lambda i: (-values[i], i))
    trough_index = min(range(n), key=lambda i: (values[i], i))
    print(f"peak {peak_index + 1} {values[peak_index]}")
    print(f"trough {trough_index + 1} {values[trough_index]}")
    if n == 1:
        print("jump none")
        return
    best = 1
    for i in range(1, n):
        if abs(values[i] - values[i - 1]) > abs(values[best] - values[best - 1]):
            best = i
    print(f"jump {best + 1} {values[best] - values[best - 1]}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def annotations(values):
    # TODO: return the three annotation lines described in the statement.
    return ["peak 1 0", "trough 1 0", "jump none"]


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    for line in annotations(values):
        print(line)


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Ties on the peak resolved to the last index.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
peak_index = max(range(n), key=lambda i: (values[i], i))
trough_index = min(range(n), key=lambda i: (values[i], i))
print(f"peak {peak_index + 1} {values[peak_index]}")
print(f"trough {trough_index + 1} {values[trough_index]}")
if n == 1:
    print("jump none")
else:
    best = 1
    for i in range(1, n):
        if abs(values[i] - values[i - 1]) > abs(values[best] - values[best - 1]):
            best = i
    print(f"jump {best + 1} {values[best] - values[best - 1]}")
""",
        # Largest signed change rather than largest absolute change.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
peak_index = min(range(n), key=lambda i: (-values[i], i))
trough_index = min(range(n), key=lambda i: (values[i], i))
print(f"peak {peak_index + 1} {values[peak_index]}")
print(f"trough {trough_index + 1} {values[trough_index]}")
if n == 1:
    print("jump none")
else:
    best = 1
    for i in range(1, n):
        if values[i] - values[i - 1] > values[best] - values[best - 1]:
            best = i
    print(f"jump {best + 1} {values[best] - values[best - 1]}")
""",
        # Reports the jump magnitude, dropping the sign.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
peak_index = min(range(n), key=lambda i: (-values[i], i))
trough_index = min(range(n), key=lambda i: (values[i], i))
print(f"peak {peak_index + 1} {values[peak_index]}")
print(f"trough {trough_index + 1} {values[trough_index]}")
if n == 1:
    print("jump none")
else:
    best = 1
    for i in range(1, n):
        if abs(values[i] - values[i - 1]) > abs(values[best] - values[best - 1]):
            best = i
    print(f"jump {best + 1} {abs(values[best] - values[best - 1])}")
""",
    ],
)


# =========================================================================== #
#  dashboard_design                                                           #
# =========================================================================== #

_problem(
    id="an-dash-kpi-delta",
    title="KPI Tile With a Period-over-Period Delta",
    skill_id="dashboard_design",
    concept="kpi",
    difficulty=4,
    minutes=22,
    summary="A number on its own is not a KPI; it needs the comparison and the direction.",
    statement=(
        "Render a KPI tile as `value delta pct direction`:\n\n"
        "* `value` — the current period's value, as given.\n"
        "* `delta` — current minus previous.\n"
        "* `pct` — the change as a percentage of the previous value, to one "
        "decimal place. When the previous value is 0 there is no percentage: "
        "print `NA`.\n"
        "* `direction` — `up`, `down` or `flat`.\n\n"
        "All four fields on one line, space separated. `direction` follows the "
        "delta, not the percentage."
    ),
    input_format="One line: current and previous, two integers, space separated.",
    output_format="One line: value, delta, pct (or NA) and direction.",
    constraints=["-1000000000 <= current, previous <= 1000000000"],
    requirements=[
        "delta is current minus previous, keeping its sign",
        "pct is delta as a percentage of previous, to one decimal place",
        "Print NA for pct when previous is zero, rather than 0.0 or a crash",
        "direction is up, down or flat according to the sign of the delta",
    ],
    examples=[
        {
            "stdin": "120 100\n",
            "explanation": "Up 20 on 100, which is 20.0 percent.",
        }
    ],
    cases=[
        ("sample: growth", "120 100\n", False),
        ("sample: decline", "80 100\n", False),
        ("hidden: no previous value", "50 0\n", True),
        ("hidden: flat", "100 100\n", True),
        ("hidden: previous was negative", "0 -50\n", True),
        ("hidden: both zero", "0 0\n", True),
    ],
    reference="""import sys


def main():
    current, previous = (int(x) for x in sys.stdin.read().split()[:2])
    delta = current - previous
    if delta > 0:
        direction = "up"
    elif delta < 0:
        direction = "down"
    else:
        direction = "flat"
    if previous == 0:
        print(f"{current} {delta} NA {direction}")
        return
    print(f"{current} {delta} {delta * 100.0 / previous:.1f} {direction}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def tile(current, previous):
    # TODO: return (value, delta, pct_or_None, direction).
    return current, 0, None, "flat"


def main():
    current, previous = (int(x) for x in sys.stdin.read().split()[:2])
    value, delta, pct, direction = tile(current, previous)
    pct_text = "NA" if pct is None else f"{pct:.1f}"
    print(f"{value} {delta} {pct_text} {direction}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Percentage of the current value instead of the previous one.
        """import sys

current, previous = (int(x) for x in sys.stdin.read().split()[:2])
delta = current - previous
direction = "up" if delta > 0 else ("down" if delta < 0 else "flat")
if current == 0:
    print(f"{current} {delta} NA {direction}")
else:
    print(f"{current} {delta} {delta * 100.0 / current:.1f} {direction}")
""",
        # Zero previous reported as a 0.0 percent change.
        """import sys

current, previous = (int(x) for x in sys.stdin.read().split()[:2])
delta = current - previous
direction = "up" if delta > 0 else ("down" if delta < 0 else "flat")
pct = 0.0 if previous == 0 else delta * 100.0 / previous
print(f"{current} {delta} {pct:.1f} {direction}")
""",
        # Direction taken from the sign of the percentage, which inverts when
        # the previous value was negative.
        """import sys

current, previous = (int(x) for x in sys.stdin.read().split()[:2])
delta = current - previous
if previous == 0:
    direction = "up" if delta > 0 else ("down" if delta < 0 else "flat")
    print(f"{current} {delta} NA {direction}")
else:
    pct = delta * 100.0 / previous
    direction = "up" if pct > 0 else ("down" if pct < 0 else "flat")
    print(f"{current} {delta} {pct:.1f} {direction}")
""",
    ],
)

_problem(
    id="an-dash-rag-status",
    title="Traffic-Light a Set of Metrics",
    skill_id="dashboard_design",
    concept="kpi",
    difficulty=4,
    minutes=20,
    summary="Thresholds that work for both higher-is-better and lower-is-better metrics.",
    statement=(
        "Assign each metric a red/amber/green status against its target.\n\n"
        "For a metric where **higher is better** (`up`): `green` when the value "
        "is at or above target, `amber` when it is at or above 90% of target, "
        "`red` otherwise.\n\n"
        "For a metric where **lower is better** (`down` — cost, latency, churn): "
        "`green` when the value is at or below target, `amber` when it is at or "
        "below 110% of target, `red` otherwise. Reusing the higher-is-better "
        "rule here would paint a rising cost green.\n\n"
        "Print `name status` per line, in input order."
    ),
    input_format="Line 1: n. Next n lines: `name,direction,value,target` where direction is `up` or `down` and value and target are decimals.",
    output_format="One line per metric: the name and its status.",
    constraints=["1 <= n <= 20000", "0 <= value, target <= 1000000", "target may be 0"],
    requirements=[
        "Apply the up rule and the down rule separately",
        "Boundaries are inclusive: exactly on target is green",
        "The amber band is 90% of target for up metrics and 110% for down metrics",
        "Preserve input order",
    ],
    examples=[
        {
            "stdin": "3\nrevenue,up,95,100\ncost,down,105,100\nchurn,down,120,100\n",
            "explanation": (
                "95 is within 10% below the revenue target, so amber. A cost 5% "
                "over target is amber; 20% over is red."
            ),
        }
    ],
    cases=[
        ("sample: one of each status", "3\nrevenue,up,95,100\ncost,down,105,100\nchurn,down,120,100\n", False),
        ("sample: exactly on target", "2\na,up,100,100\nb,down,100,100\n", False),
        ("hidden: the amber boundaries exactly", "2\na,up,90,100\nb,down,110,100\n", True),
        ("hidden: just outside the amber band", "2\na,up,89.9,100\nb,down,110.1,100\n", True),
        ("hidden: a target of zero", "2\na,up,0,0\nb,down,1,0\n", True),
        ("hidden: down metric far under target is green", "1\nlatency,down,1,500\n", True),
    ],
    reference="""import sys


def status(direction, value, target):
    if direction == "up":
        if value >= target:
            return "green"
        if value >= 0.9 * target:
            return "amber"
        return "red"
    if value <= target:
        return "green"
    if value <= 1.1 * target:
        return "amber"
    return "red"


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    for line in data[1:1 + n]:
        name, direction, value, target = line.strip().split(",")
        print(f"{name} {status(direction, float(value), float(target))}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def status(direction, value, target):
    # TODO: return 'green', 'amber' or 'red', honouring the direction.
    return "green"


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    for line in data[1:1 + n]:
        name, direction, value, target = line.strip().split(",")
        print(f"{name} {status(direction, float(value), float(target))}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # One rule for both directions: a cost over target reads green.
        """import sys


def status(direction, value, target):
    if value >= target:
        return "green"
    if value >= 0.9 * target:
        return "amber"
    return "red"


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    name, direction, value, target = line.strip().split(",")
    print(f"{name} {status(direction, float(value), float(target))}")
""",
        # Exclusive boundaries: exactly on target is not green.
        """import sys


def status(direction, value, target):
    if direction == "up":
        if value > target:
            return "green"
        if value > 0.9 * target:
            return "amber"
        return "red"
    if value < target:
        return "green"
    if value < 1.1 * target:
        return "amber"
    return "red"


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    name, direction, value, target = line.strip().split(",")
    print(f"{name} {status(direction, float(value), float(target))}")
""",
        # The down band widened to 90% instead of 110%.
        """import sys


def status(direction, value, target):
    if direction == "up":
        if value >= target:
            return "green"
        if value >= 0.9 * target:
            return "amber"
        return "red"
    if value <= target:
        return "green"
    if value <= 0.9 * target:
        return "amber"
    return "red"


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    name, direction, value, target = line.strip().split(",")
    print(f"{name} {status(direction, float(value), float(target))}")
""",
    ],
)

_problem(
    id="an-dash-tile-order",
    title="Order the Tiles on the Dashboard",
    skill_id="dashboard_design",
    concept="dashboard layout",
    difficulty=4,
    minutes=20,
    summary="Rank tiles by a priority score with a deterministic tiebreak, so the layout is stable.",
    statement=(
        "A tile's priority score is `impact * audience_weight`. Print the tile "
        "names in descending score order, one per line.\n\n"
        "Two tiles with the same score must come out in a **stable, defined** "
        "order or the dashboard reshuffles itself between refreshes, so break a "
        "tie by tile name ascending."
    ),
    input_format="Line 1: n. Next n lines: `name,impact,audience_weight` — integers.",
    output_format="One tile name per line, highest score first.",
    constraints=["1 <= n <= 20000", "0 <= impact <= 1000", "0 <= audience_weight <= 1000"],
    requirements=[
        "Score each tile as impact times audience_weight",
        "Sort by score descending",
        "Break ties by tile name ascending",
        "Print only the names, one per line",
    ],
    examples=[
        {
            "stdin": "3\nrevenue,5,4\nchurn,10,2\nnps,1,1\n",
            "explanation": (
                "revenue and churn both score 20, so the alphabetically earlier "
                "churn comes first, and nps scores 1."
            ),
        }
    ],
    cases=[
        ("sample: a tie broken by name", "3\nrevenue,5,4\nchurn,10,2\nnps,1,1\n", False),
        ("sample: distinct scores", "2\nbig,10,10\nsmall,1,1\n", False),
        ("hidden: zero-score tiles still appear", "3\na,0,5\nb,0,0\nc,1,1\n", True),
        ("hidden: every score identical", "3\nzz,2,3\nmm,3,2\naa,6,1\n", True),
        ("hidden: score, not impact, decides", "2\nwide,1,1000\ntall,100,1\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    tiles = []
    for line in data[1:1 + n]:
        name, impact, weight = line.strip().split(",")
        tiles.append((name, int(impact) * int(weight)))
    for name, _score in sorted(tiles, key=lambda kv: (-kv[1], kv[0])):
        print(name)


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def ordered_tiles(tiles):
    # TODO: return the tile names ordered by score descending, then name
    # ascending. `tiles` is [(name, impact, weight), ...].
    return [name for name, _impact, _weight in tiles]


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    tiles = []
    for line in data[1:1 + n]:
        name, impact, weight = line.strip().split(",")
        tiles.append((name, int(impact), int(weight)))
    for name in ordered_tiles(tiles):
        print(name)


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Ranks by impact alone, ignoring the audience weight.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
tiles = []
for line in data[1:1 + n]:
    name, impact, weight = line.strip().split(",")
    tiles.append((name, int(impact)))
for name, _score in sorted(tiles, key=lambda kv: (-kv[1], kv[0])):
    print(name)
""",
        # Tie broken by name descending.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
tiles = []
for line in data[1:1 + n]:
    name, impact, weight = line.strip().split(",")
    tiles.append((name, int(impact) * int(weight)))
for name, _score in sorted(sorted(tiles, reverse=True), key=lambda kv: -kv[1]):
    print(name)
""",
        # Ascending scores.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
tiles = []
for line in data[1:1 + n]:
    name, impact, weight = line.strip().split(",")
    tiles.append((name, int(impact) * int(weight)))
for name, _score in sorted(tiles, key=lambda kv: (kv[1], kv[0])):
    print(name)
""",
    ],
)

_problem(
    id="an-dash-drilldown-path",
    title="Resolve a Drill-Down Path",
    skill_id="dashboard_design",
    concept="drill-down",
    difficulty=5,
    minutes=25,
    summary="Walk a parent hierarchy from a node up to the root, and refuse to loop forever.",
    statement=(
        "A dashboard hierarchy is given as `child,parent` pairs; a node whose "
        "parent is `-` is a root.\n\n"
        "For the queried node, print the drill-down path from the **root down to "
        "the node**, joined with ` > `.\n\n"
        "The data may be broken. If a node's parent does not exist in the "
        "hierarchy print `broken`, and if following parents revisits a node "
        "print `cycle` — do not loop forever. If the queried node itself is not "
        "in the hierarchy, print `unknown`."
    ),
    input_format="Line 1: n. Next n lines: `child,parent`. Last line: the queried node.",
    output_format="One line: the path root-first joined by ` > `, or `unknown`, `broken`, or `cycle`.",
    constraints=["1 <= n <= 20000", "Node names contain no commas", "Each child appears at most once"],
    requirements=[
        "Print the path from the root down to the queried node",
        "Print 'unknown' when the queried node is not a child in the hierarchy",
        "Print 'broken' when a parent is not itself in the hierarchy",
        "Detect a cycle and print 'cycle' rather than looping",
    ],
    examples=[
        {
            "stdin": "3\ncity,region\nregion,country\ncountry,-\ncity\n",
            "explanation": "Walking up from city gives region then country, printed root-first.",
        }
    ],
    cases=[
        ("sample: three levels", "3\ncity,region\nregion,country\ncountry,-\ncity\n", False),
        ("sample: the root itself", "2\nregion,country\ncountry,-\ncountry\n", False),
        ("hidden: unknown node", "2\na,b\nb,-\nz\n", True),
        ("hidden: missing parent", "2\na,b\nb,ghost\na\n", True),
        ("hidden: a cycle", "2\na,b\nb,a\na\n", True),
        ("hidden: a longer chain", "4\nd,c\nc,b\nb,a\na,-\nd\n", True),
        ("hidden: self-parent is a cycle", "1\nx,x\nx\n", True),
    ],
    reference="""import sys


def main():
    lines = sys.stdin.read().split("\\n")
    n = int(lines[0].strip())
    parents = {}
    for line in lines[1:1 + n]:
        child, parent = line.strip().split(",")
        parents[child] = parent
    query = lines[1 + n].strip()
    if query not in parents:
        print("unknown")
        return
    path = [query]
    seen = {query}
    current = query
    while True:
        parent = parents[current]
        if parent == "-":
            break
        if parent in seen:
            print("cycle")
            return
        if parent not in parents:
            print("broken")
            return
        path.append(parent)
        seen.add(parent)
        current = parent
    print(" > ".join(reversed(path)))


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def resolve(parents, query):
    # TODO: return the root-first path as a list, or the string 'unknown',
    # 'broken' or 'cycle'.
    return "unknown"


def main():
    lines = sys.stdin.read().split("\\n")
    n = int(lines[0].strip())
    parents = {}
    for line in lines[1:1 + n]:
        child, parent = line.strip().split(",")
        parents[child] = parent
    result = resolve(parents, lines[1 + n].strip())
    print(result if isinstance(result, str) else " > ".join(result))


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Path printed leaf-first.
        """import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0].strip())
parents = {}
for line in lines[1:1 + n]:
    child, parent = line.strip().split(",")
    parents[child] = parent
query = lines[1 + n].strip()
if query not in parents:
    print("unknown")
else:
    path = [query]
    seen = {query}
    current = query
    ok = True
    while True:
        parent = parents[current]
        if parent == "-":
            break
        if parent in seen:
            print("cycle")
            ok = False
            break
        if parent not in parents:
            print("broken")
            ok = False
            break
        path.append(parent)
        seen.add(parent)
        current = parent
    if ok:
        print(" > ".join(path))
""",
        # A missing parent is silently treated as a root.
        """import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0].strip())
parents = {}
for line in lines[1:1 + n]:
    child, parent = line.strip().split(",")
    parents[child] = parent
query = lines[1 + n].strip()
if query not in parents:
    print("unknown")
else:
    path = [query]
    seen = {query}
    current = query
    cycled = False
    while current in parents and parents[current] != "-":
        parent = parents[current]
        if parent in seen:
            print("cycle")
            cycled = True
            break
        path.append(parent)
        seen.add(parent)
        current = parent
    if not cycled:
        print(" > ".join(reversed(path)))
""",
        # Depth-limited instead of cycle-detecting, so a cycle prints a path.
        """import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0].strip())
parents = {}
for line in lines[1:1 + n]:
    child, parent = line.strip().split(",")
    parents[child] = parent
query = lines[1 + n].strip()
if query not in parents:
    print("unknown")
else:
    path = [query]
    current = query
    for _step in range(3):
        parent = parents.get(current, "-")
        if parent == "-":
            break
        path.append(parent)
        current = parent
    print(" > ".join(reversed(path)))
""",
    ],
)

_problem(
    id="an-dash-kpi-tiles",
    title="Compute the Four Tiles From Raw Rows",
    skill_id="dashboard_design",
    concept="kpi",
    difficulty=5,
    minutes=25,
    summary="Total, average order value, conversion rate and order count — from one pass over the rows.",
    statement=(
        "Each row is a session: whether it converted (`1` or `0`) and the order "
        "value (0 when it did not convert).\n\n"
        "Print four lines:\n\n"
        "* `revenue <total>` to two decimal places,\n"
        "* `orders <count>` — the number of converting sessions,\n"
        "* `aov <value>` to two decimal places — revenue divided by **orders**, "
        "not by sessions, or `NA` when there are no orders,\n"
        "* `cvr <rate>` to three decimal places — orders divided by sessions.\n\n"
        "Dividing revenue by sessions instead of orders is the classic wrong "
        "average order value, and it always understates it."
    ),
    input_format="Line 1: n. Next n lines: `converted,value` where converted is 0 or 1 and value is a decimal.",
    output_format="Four lines: revenue, orders, aov and cvr.",
    constraints=["1 <= n <= 20000", "0 <= value <= 1000000"],
    requirements=[
        "revenue totals every row's value",
        "orders counts only converting sessions",
        "aov divides revenue by orders, and is NA when there are no orders",
        "cvr divides orders by the number of sessions",
    ],
    examples=[
        {
            "stdin": "4\n1,100.00\n0,0.00\n1,50.00\n0,0.00\n",
            "explanation": (
                "150.00 of revenue over 2 orders is an AOV of 75.00, and 2 of 4 "
                "sessions converted."
            ),
        }
    ],
    cases=[
        ("sample: half the sessions convert", "4\n1,100.00\n0,0.00\n1,50.00\n0,0.00\n", False),
        ("sample: everyone converts", "2\n1,10.00\n1,20.00\n", False),
        ("hidden: nobody converts", "3\n0,0.00\n0,0.00\n0,0.00\n", True),
        ("hidden: a single session", "1\n1,42.42\n", True),
        ("hidden: a converting session worth zero", "2\n1,0.00\n0,0.00\n", True),
        ("hidden: rate rounds to three places", "3\n1,9.00\n0,0.00\n0,0.00\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    revenue = 0.0
    orders = 0
    for line in data[1:1 + n]:
        converted, value = line.strip().split(",")
        revenue += float(value)
        orders += int(converted)
    print(f"revenue {revenue:.2f}")
    print(f"orders {orders}")
    print("aov NA" if orders == 0 else f"aov {revenue / orders:.2f}")
    print(f"cvr {orders / n:.3f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def tiles(rows):
    # TODO: return (revenue, orders, aov_or_None, cvr).
    return 0.0, 0, None, 0.0


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = [line.strip().split(",") for line in data[1:1 + n]]
    revenue, orders, aov, cvr = tiles(rows)
    print(f"revenue {revenue:.2f}")
    print(f"orders {orders}")
    print("aov NA" if aov is None else f"aov {aov:.2f}")
    print(f"cvr {cvr:.3f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # AOV over sessions rather than over orders.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
revenue = 0.0
orders = 0
for line in data[1:1 + n]:
    converted, value = line.strip().split(",")
    revenue += float(value)
    orders += int(converted)
print(f"revenue {revenue:.2f}")
print(f"orders {orders}")
print(f"aov {revenue / n:.2f}")
print(f"cvr {orders / n:.3f}")
""",
        # Counts non-zero values as orders, so a free order goes missing.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
revenue = 0.0
orders = 0
for line in data[1:1 + n]:
    converted, value = line.strip().split(",")
    revenue += float(value)
    if float(value) > 0:
        orders += 1
print(f"revenue {revenue:.2f}")
print(f"orders {orders}")
print("aov NA" if orders == 0 else f"aov {revenue / orders:.2f}")
print(f"cvr {orders / n:.3f}")
""",
        # Zero orders reported as an AOV of 0.00.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
revenue = 0.0
orders = 0
for line in data[1:1 + n]:
    converted, value = line.strip().split(",")
    revenue += float(value)
    orders += int(converted)
print(f"revenue {revenue:.2f}")
print(f"orders {orders}")
print(f"aov {(revenue / orders) if orders else 0.0:.2f}")
print(f"cvr {orders / n:.3f}")
""",
    ],
)

_problem(
    id="an-dash-filters",
    title="Apply the Dashboard Filters",
    skill_id="dashboard_design",
    concept="drill-down",
    difficulty=5,
    minutes=25,
    summary="Every filter must hold at once, and a filter naming a missing field matches nothing.",
    statement=(
        "Rows are `key=value` pairs. A filter is also a set of `key=value` "
        "pairs, and a row matches only when **every** filter pair is present on "
        "the row with that exact value. A filter naming a field the row does "
        "not have does not match — a missing field is not a wildcard.\n\n"
        "Print the number of matching rows, then their ids in input order on "
        "one space-separated line, or `none` when nothing matches. Each row's "
        "first field is always `id`."
    ),
    input_format=(
        "Line 1: n. Next n lines: a row as `key=value` pairs separated by "
        "semicolons, starting with `id=...`. Last line: the filter as "
        "`key=value` pairs separated by semicolons, or `-` for no filter."
    ),
    output_format="Line 1: the match count. Line 2: matching ids space separated, or `none`.",
    constraints=["1 <= n <= 20000", "Keys and values contain no `=` or `;`"],
    requirements=[
        "A row matches only when every filter pair matches",
        "A filter key missing from the row means the row does not match",
        "An empty filter matches every row",
        "Print the count, then the ids in input order, or 'none'",
    ],
    examples=[
        {
            "stdin": "3\nid=1;region=emea;tier=gold\nid=2;region=emea;tier=silver\nid=3;region=apac\nregion=emea;tier=gold\n",
            "explanation": (
                "Only row 1 matches both pairs. Row 3 has no tier at all, so it "
                "cannot match a tier filter."
            ),
        }
    ],
    cases=[
        ("sample: two pairs, one match", "3\nid=1;region=emea;tier=gold\nid=2;region=emea;tier=silver\nid=3;region=apac\nregion=emea;tier=gold\n", False),
        ("sample: no filter matches everything", "2\nid=1;region=emea\nid=2;region=apac\n-\n", False),
        ("hidden: nothing matches", "2\nid=1;region=emea\nid=2;region=apac\nregion=latam\n", True),
        ("hidden: missing field is not a wildcard", "2\nid=1;region=emea\nid=2;region=emea;tier=gold\ntier=gold\n", True),
        ("hidden: values are case sensitive", "2\nid=1;region=EMEA\nid=2;region=emea\nregion=emea\n", True),
        ("hidden: input order is preserved", "3\nid=9;x=1\nid=5;x=1\nid=7;x=1\nx=1\n", True),
    ],
    reference="""import sys


def parse(text):
    pairs = {}
    for chunk in text.split(";"):
        if not chunk:
            continue
        key, _sep, value = chunk.partition("=")
        pairs[key] = value
    return pairs


def main():
    lines = sys.stdin.read().split("\\n")
    n = int(lines[0].strip())
    rows = [parse(line.strip()) for line in lines[1:1 + n]]
    filter_text = lines[1 + n].strip()
    conditions = {} if filter_text == "-" else parse(filter_text)
    matches = [
        row["id"]
        for row in rows
        if all(row.get(key) == value for key, value in conditions.items())
    ]
    print(len(matches))
    print(" ".join(matches) if matches else "none")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def parse(text):
    pairs = {}
    for chunk in text.split(";"):
        if not chunk:
            continue
        key, _sep, value = chunk.partition("=")
        pairs[key] = value
    return pairs


def matches(row, conditions):
    # TODO: True only when every condition matches a field on the row.
    return True


def main():
    lines = sys.stdin.read().split("\\n")
    n = int(lines[0].strip())
    rows = [parse(line.strip()) for line in lines[1:1 + n]]
    filter_text = lines[1 + n].strip()
    conditions = {} if filter_text == "-" else parse(filter_text)
    found = [row["id"] for row in rows if matches(row, conditions)]
    print(len(found))
    print(" ".join(found) if found else "none")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # OR instead of AND.
        """import sys


def parse(text):
    pairs = {}
    for chunk in text.split(";"):
        if not chunk:
            continue
        key, _sep, value = chunk.partition("=")
        pairs[key] = value
    return pairs


lines = sys.stdin.read().split("\\n")
n = int(lines[0].strip())
rows = [parse(line.strip()) for line in lines[1:1 + n]]
filter_text = lines[1 + n].strip()
conditions = {} if filter_text == "-" else parse(filter_text)
found = [
    row["id"]
    for row in rows
    if not conditions or any(row.get(k) == v for k, v in conditions.items())
]
print(len(found))
print(" ".join(found) if found else "none")
""",
        # A missing field is treated as a wildcard.
        """import sys


def parse(text):
    pairs = {}
    for chunk in text.split(";"):
        if not chunk:
            continue
        key, _sep, value = chunk.partition("=")
        pairs[key] = value
    return pairs


lines = sys.stdin.read().split("\\n")
n = int(lines[0].strip())
rows = [parse(line.strip()) for line in lines[1:1 + n]]
filter_text = lines[1 + n].strip()
conditions = {} if filter_text == "-" else parse(filter_text)
found = [
    row["id"]
    for row in rows
    if all(key not in row or row[key] == value for key, value in conditions.items())
]
print(len(found))
print(" ".join(found) if found else "none")
""",
        # Case-insensitive matching, which merges genuinely different values.
        """import sys


def parse(text):
    pairs = {}
    for chunk in text.split(";"):
        if not chunk:
            continue
        key, _sep, value = chunk.partition("=")
        pairs[key] = value
    return pairs


lines = sys.stdin.read().split("\\n")
n = int(lines[0].strip())
rows = [parse(line.strip()) for line in lines[1:1 + n]]
filter_text = lines[1 + n].strip()
conditions = {} if filter_text == "-" else parse(filter_text)
found = [
    row["id"]
    for row in rows
    if all(
        key in row and row[key].lower() == value.lower()
        for key, value in conditions.items()
    )
]
print(len(found))
print(" ".join(found) if found else "none")
""",
    ],
)

_problem(
    id="an-dash-breach-alert",
    title="Alert Only on a Sustained Breach",
    skill_id="dashboard_design",
    concept="kpi",
    difficulty=6,
    minutes=28,
    summary="Fire when k consecutive readings breach the threshold, so a single spike does not page anyone.",
    statement=(
        "A metric breaches when its value is **strictly greater** than the "
        "threshold. Alerting on one breach makes the dashboard cry wolf, so the "
        "alert only fires once `k` consecutive readings have breached.\n\n"
        "Print the 1-based index of the reading that **completes** the first run "
        "of `k` consecutive breaches, or `no alert` if that never happens. A "
        "single reading at or below the threshold resets the run."
    ),
    input_format="Line 1: n, threshold and k, space separated. Line 2: n space-separated integers.",
    output_format="One line: the 1-based index that completes the first qualifying run, or `no alert`.",
    constraints=["1 <= k <= n <= 20000", "-1000000 <= threshold, value <= 1000000"],
    requirements=[
        "A breach is strictly greater than the threshold",
        "The run must be k consecutive breaches, reset by any non-breach",
        "Report the index that completes the run, not where the run started",
        "Print 'no alert' when no run reaches length k",
    ],
    examples=[
        {
            "stdin": "6 100 3\n120 130 90 140 150 160\n",
            "explanation": (
                "The first two breaches are broken by the 90. The run then "
                "restarts and completes at the sixth reading."
            ),
        }
    ],
    cases=[
        ("sample: a reset then a full run", "6 100 3\n120 130 90 140 150 160\n", False),
        ("sample: one spike is not an alert", "4 100 2\n150 10 10 150\n", False),
        ("hidden: equal to the threshold is not a breach", "3 100 2\n100 100 100\n", True),
        ("hidden: k of one fires immediately", "3 5 1\n1 9 1\n", True),
        ("hidden: run completes on the last reading", "4 0 4\n1 1 1 1\n", True),
        ("hidden: never breaches", "3 1000 2\n1 2 3\n", True),
        ("hidden: two runs, the earlier one wins", "7 10 2\n11 12 1 11 12 13 14\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split()
    n, threshold, k = int(data[0]), int(data[1]), int(data[2])
    values = [int(x) for x in data[3:3 + n]]
    run = 0
    for index, value in enumerate(values, start=1):
        if value > threshold:
            run += 1
            if run == k:
                print(index)
                return
        else:
            run = 0
    print("no alert")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def first_alert(values, threshold, k):
    # TODO: return the 1-based index completing the first run of k consecutive
    # breaches, or None.
    return None


def main():
    data = sys.stdin.read().split()
    n, threshold, k = int(data[0]), int(data[1]), int(data[2])
    values = [int(x) for x in data[3:3 + n]]
    result = first_alert(values, threshold, k)
    print("no alert" if result is None else result)


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Counts total breaches rather than consecutive ones.
        """import sys

data = sys.stdin.read().split()
n, threshold, k = int(data[0]), int(data[1]), int(data[2])
values = [int(x) for x in data[3:3 + n]]
seen = 0
for index, value in enumerate(values, start=1):
    if value > threshold:
        seen += 1
        if seen == k:
            print(index)
            break
else:
    print("no alert")
""",
        # `>=` treats a reading exactly on the threshold as a breach.
        """import sys

data = sys.stdin.read().split()
n, threshold, k = int(data[0]), int(data[1]), int(data[2])
values = [int(x) for x in data[3:3 + n]]
run = 0
for index, value in enumerate(values, start=1):
    if value >= threshold:
        run += 1
        if run == k:
            print(index)
            break
    else:
        run = 0
else:
    print("no alert")
""",
        # Reports where the run started.
        """import sys

data = sys.stdin.read().split()
n, threshold, k = int(data[0]), int(data[1]), int(data[2])
values = [int(x) for x in data[3:3 + n]]
run = 0
for index, value in enumerate(values, start=1):
    if value > threshold:
        run += 1
        if run == k:
            print(index - k + 1)
            break
    else:
        run = 0
else:
    print("no alert")
""",
    ],
)

_problem(
    id="an-dash-audience-format",
    title="Format a Number for Its Audience",
    skill_id="dashboard_design",
    concept="audience",
    difficulty=4,
    minutes=20,
    summary="Currency, percentage and count each have their own presentation rules.",
    statement=(
        "Format each metric according to its type:\n\n"
        "* `currency`: `£` then the value with **thousands separators** and two "
        "decimal places (`£1,234.50`),\n"
        "* `percent`: the value multiplied by 100, one decimal place, then `%` "
        "(`0.1234` becomes `12.3%`),\n"
        "* `count`: the value rounded to the nearest whole number, with "
        "thousands separators and no decimal point (`1,235`).\n\n"
        "Rounding a count to the nearest whole number uses Python's `round`. "
        "Print one formatted value per line, in input order."
    ),
    input_format="Line 1: n. Next n lines: `type,value` where type is currency, percent or count.",
    output_format="One formatted value per line.",
    constraints=["1 <= n <= 20000", "-1000000000 <= value <= 1000000000"],
    requirements=[
        "Currency uses a £ sign, thousands separators and exactly two decimals",
        "Percent multiplies by 100 and shows one decimal place with a % sign",
        "Count rounds to a whole number and uses thousands separators",
        "Keep the input order",
    ],
    examples=[
        {
            "stdin": "3\ncurrency,1234.5\npercent,0.1234\ncount,1234.6\n",
            "explanation": "Each type is presented in the shape its audience expects.",
        }
    ],
    cases=[
        ("sample: one of each type", "3\ncurrency,1234.5\npercent,0.1234\ncount,1234.6\n", False),
        ("sample: small values", "3\ncurrency,0.5\npercent,0.005\ncount,0.4\n", False),
        ("hidden: negatives", "3\ncurrency,-1234.5\npercent,-0.5\ncount,-1500.5\n", True),
        ("hidden: millions need two separators", "2\ncurrency,1234567.89\ncount,7654321\n", True),
        ("hidden: percent above one", "2\npercent,1\npercent,2.5\n", True),
        ("hidden: rounding a half", "2\ncount,2.5\ncount,3.5\n", True),
    ],
    reference="""import sys


def format_value(kind, value):
    if kind == "currency":
        return f"\\u00a3{value:,.2f}"
    if kind == "percent":
        return f"{value * 100:.1f}%"
    return f"{round(value):,}"


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    for line in data[1:1 + n]:
        kind, value = line.strip().split(",")
        print(format_value(kind, float(value)))


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def format_value(kind, value):
    # TODO: currency, percent and count each have their own rule.
    return str(value)


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    for line in data[1:1 + n]:
        kind, value = line.strip().split(",")
        print(format_value(kind, float(value)))


if __name__ == "__main__":
    main()
""",
    wrong=[
        # No thousands separators.
        """import sys


def format_value(kind, value):
    if kind == "currency":
        return f"\\u00a3{value:.2f}"
    if kind == "percent":
        return f"{value * 100:.1f}%"
    return f"{round(value)}"


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    kind, value = line.strip().split(",")
    print(format_value(kind, float(value)))
""",
        # Percent not multiplied by 100.
        """import sys


def format_value(kind, value):
    if kind == "currency":
        return f"\\u00a3{value:,.2f}"
    if kind == "percent":
        return f"{value:.1f}%"
    return f"{round(value):,}"


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    kind, value = line.strip().split(",")
    print(format_value(kind, float(value)))
""",
        # Count truncated rather than rounded.
        """import sys


def format_value(kind, value):
    if kind == "currency":
        return f"\\u00a3{value:,.2f}"
    if kind == "percent":
        return f"{value * 100:.1f}%"
    return f"{int(value):,}"


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    kind, value = line.strip().split(",")
    print(format_value(kind, float(value)))
""",
    ],
)

_problem(
    id="an-dash-trend-verdict",
    title="Summarise a Trend for a Tile",
    skill_id="dashboard_design",
    concept="narrative",
    difficulty=5,
    minutes=24,
    summary="Compare the two halves of a series rather than its endpoints, so one noisy day cannot flip the verdict.",
    statement=(
        "Judge a series' trend by comparing the mean of its **second half** "
        "against the mean of its **first half**, which is robust to a single "
        "noisy reading in a way that comparing the first and last values is "
        "not.\n\n"
        "With an odd number of readings the middle reading belongs to neither "
        "half. Print the change as a percentage of the first-half mean to one "
        "decimal place, a space, and then `improving` when the change exceeds "
        "+5%, `declining` when it is below -5%, or `stable` in between "
        "(inclusive on both ends).\n\n"
        "When there is only one reading, or the first-half mean is 0, print "
        "`NA stable`."
    ),
    input_format="Line 1: n. Line 2: n space-separated integers, oldest first.",
    output_format="One line: the percentage change (or NA), a space, then the verdict.",
    constraints=["1 <= n <= 20000", "-1000000 <= value <= 1000000", "The ±5% band is inclusive"],
    requirements=[
        "Compare the mean of the second half against the mean of the first half",
        "Exclude the middle reading when n is odd",
        "The stable band is -5% to +5% inclusive",
        "Print 'NA stable' when there is one reading or the first-half mean is zero",
    ],
    examples=[
        {
            "stdin": "6\n10 10 10 20 20 20\n",
            "explanation": "The second half averages 20 against 10, a 100.0 percent improvement.",
        }
    ],
    cases=[
        ("sample: clear improvement", "6\n10 10 10 20 20 20\n", False),
        ("sample: a single spike does not flip a flat series", "5\n10 10 10 10 40\n", False),
        ("hidden: single reading", "1\n5\n", True),
        ("hidden: first half averages zero", "4\n0 0 5 5\n", True),
        ("hidden: exactly five percent is stable", "4\n100 100 105 105\n", True),
        ("hidden: decline", "4\n100 100 50 50\n", True),
        ("hidden: odd length ignores the middle", "3\n10 1000 20\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    if n < 2:
        print("NA stable")
        return
    half = n // 2
    first = values[:half]
    second = values[n - half:]
    first_mean = sum(first) / len(first)
    second_mean = sum(second) / len(second)
    if first_mean == 0:
        print("NA stable")
        return
    change = (second_mean - first_mean) * 100.0 / first_mean
    if change > 5:
        verdict = "improving"
    elif change < -5:
        verdict = "declining"
    else:
        verdict = "stable"
    print(f"{change:.1f} {verdict}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def trend(values):
    # TODO: return (change_pct_or_None, verdict) comparing the second half's
    # mean against the first half's.
    return None, "stable"


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    change, verdict = trend(values)
    print(f"NA {verdict}" if change is None else f"{change:.1f} {verdict}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Compares the endpoints, so one noisy final reading decides.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
if n < 2 or values[0] == 0:
    print("NA stable")
else:
    change = (values[-1] - values[0]) * 100.0 / values[0]
    verdict = "improving" if change > 5 else ("declining" if change < -5 else "stable")
    print(f"{change:.1f} {verdict}")
""",
        # Includes the middle reading in both halves.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
if n < 2:
    print("NA stable")
else:
    half = (n + 1) // 2
    first = values[:half]
    second = values[n - half:]
    first_mean = sum(first) / len(first)
    if first_mean == 0:
        print("NA stable")
    else:
        change = (sum(second) / len(second) - first_mean) * 100.0 / first_mean
        verdict = "improving" if change > 5 else ("declining" if change < -5 else "stable")
        print(f"{change:.1f} {verdict}")
""",
        # Exclusive band edges: exactly 5% reads as improving.
        """import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
if n < 2:
    print("NA stable")
else:
    half = n // 2
    first = values[:half]
    second = values[n - half:]
    first_mean = sum(first) / len(first)
    if first_mean == 0:
        print("NA stable")
    else:
        change = (sum(second) / len(second) - first_mean) * 100.0 / first_mean
        verdict = "improving" if change >= 5 else ("declining" if change <= -5 else "stable")
        print(f"{change:.1f} {verdict}")
""",
    ],
)

_problem(
    id="an-dash-narrative",
    title="Write the Dashboard's One-Line Story",
    skill_id="dashboard_design",
    concept="narrative",
    difficulty=6,
    minutes=28,
    summary="Name the biggest mover in percentage terms, not the biggest number.",
    statement=(
        "Every dashboard needs one sentence saying what changed. The biggest "
        "*mover* is the category with the largest change **relative to its own "
        "previous value** — a category that went from 2 to 4 moved more than "
        "one that went from 1000 to 1100, even though the second changed by "
        "more units.\n\n"
        "Print exactly one line:\n\n"
        "    <category> <direction> <pct>% (<previous> to <current>)\n\n"
        "where `direction` is `rose` or `fell`, and `pct` is the absolute "
        "relative change to one decimal place. Categories whose previous value "
        "is 0 have no relative change and are ignored. Ties on the relative "
        "change go to the category whose name sorts first. If no category "
        "qualifies, or every qualifying category is unchanged, print "
        "`no significant change`."
    ),
    input_format="Line 1: n. Next n lines: `category,previous,current` — integers.",
    output_format="One line: the narrative sentence, or `no significant change`.",
    constraints=["1 <= n <= 20000", "0 <= previous, current <= 1000000000"],
    requirements=[
        "Rank movers by change relative to their own previous value",
        "Ignore categories whose previous value is zero",
        "Break ties by category name ascending",
        "Print 'no significant change' when nothing qualifies or nothing moved",
    ],
    examples=[
        {
            "stdin": "2\nsmall,2,4\nbig,1000,1100\n",
            "explanation": (
                "small doubled — a 100.0% move — while big only moved 10%, so "
                "small is the story even though it is the smaller number."
            ),
        }
    ],
    cases=[
        ("sample: relative beats absolute", "2\nsmall,2,4\nbig,1000,1100\n", False),
        ("sample: a decline is the story", "2\na,100,50\nb,100,110\n", False),
        ("hidden: previous of zero is ignored", "2\nnew,0,500\nsteady,100,120\n", True),
        ("hidden: nothing changed", "2\na,100,100\nb,50,50\n", True),
        ("hidden: every previous is zero", "2\na,0,10\nb,0,20\n", True),
        ("hidden: tie broken by name", "2\nzz,100,200\naa,50,100\n", True),
        ("hidden: a category falling to zero", "2\ngone,80,0\nsteady,100,101\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    best = None
    for line in data[1:1 + n]:
        category, previous, current = line.strip().split(",")
        previous, current = int(previous), int(current)
        if previous == 0 or current == previous:
            continue
        change = abs(current - previous) * 100.0 / previous
        key = (-change, category)
        if best is None or key < best[0]:
            best = (key, category, previous, current, change)
    if best is None:
        print("no significant change")
        return
    _key, category, previous, current, change = best
    direction = "rose" if current > previous else "fell"
    print(f"{category} {direction} {change:.1f}% ({previous} to {current})")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def biggest_mover(rows):
    # TODO: return (category, previous, current, change_pct) for the largest
    # relative move, or None.
    return None


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = []
    for line in data[1:1 + n]:
        category, previous, current = line.strip().split(",")
        rows.append((category, int(previous), int(current)))
    result = biggest_mover(rows)
    if result is None:
        print("no significant change")
    else:
        category, previous, current, change = result
        direction = "rose" if current > previous else "fell"
        print(f"{category} {direction} {change:.1f}% ({previous} to {current})")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Ranks by absolute unit change.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
best = None
for line in data[1:1 + n]:
    category, previous, current = line.strip().split(",")
    previous, current = int(previous), int(current)
    if previous == 0 or current == previous:
        continue
    units = abs(current - previous)
    key = (-units, category)
    if best is None or key < best[0]:
        best = (key, category, previous, current, units * 100.0 / previous)
if best is None:
    print("no significant change")
else:
    _key, category, previous, current, change = best
    direction = "rose" if current > previous else "fell"
    print(f"{category} {direction} {change:.1f}% ({previous} to {current})")
""",
        # Includes a previous of zero, which is an infinite relative change.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
best = None
for line in data[1:1 + n]:
    category, previous, current = line.strip().split(",")
    previous, current = int(previous), int(current)
    if current == previous:
        continue
    change = abs(current - previous) * 100.0 / previous if previous else float("inf")
    key = (-change, category)
    if best is None or key < best[0]:
        best = (key, category, previous, current, change)
if best is None:
    print("no significant change")
else:
    _key, category, previous, current, change = best
    direction = "rose" if current > previous else "fell"
    print(f"{category} {direction} {change:.1f}% ({previous} to {current})")
""",
        # Only looks for increases, so a collapse is never the story.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
best = None
for line in data[1:1 + n]:
    category, previous, current = line.strip().split(",")
    previous, current = int(previous), int(current)
    if previous == 0 or current <= previous:
        continue
    change = (current - previous) * 100.0 / previous
    key = (-change, category)
    if best is None or key < best[0]:
        best = (key, category, previous, current, change)
if best is None:
    print("no significant change")
else:
    _key, category, previous, current, change = best
    print(f"{category} rose {change:.1f}% ({previous} to {current})")
""",
    ],
)


# =========================================================================== #
#  spreadsheet_modeling                                                       #
#                                                                             #
#  Spreadsheet skill is formula semantics, not the UI: what a lookup does when #
#  the key is missing, what an absolute reference means when a formula is      #
#  filled, and whether a model's arithmetic survives an edge case. Each of     #
#  these implements the semantics of a formula, which is checkable.            #
# =========================================================================== #

_problem(
    id="an-sheet-exact-lookup",
    title="VLOOKUP With an Exact Match",
    skill_id="spreadsheet_modeling",
    concept="lookup",
    difficulty=3,
    minutes=20,
    summary="Look each key up in the table and return #N/A when it is genuinely not there.",
    statement=(
        "Build a lookup table from the reference rows, then answer each query.\n\n"
        "Print the matching value, or `#N/A` when the key is not in the table. "
        "Matching is **exact**, including case: `Gold` does not match `gold`. "
        "When a key appears more than once in the reference rows the **first** "
        "one wins, which is what a real lookup does.\n\n"
        "Answering 0 for a missing key is the mistake this question exists to "
        "catch: it silently turns a data problem into a plausible-looking total."
    ),
    input_format=(
        "Line 1: n. Next n lines: `key,value` reference rows. Then a line with "
        "m, then m lines each holding one query key."
    ),
    output_format="One line per query: the value, or `#N/A`.",
    constraints=["1 <= n <= 20000", "1 <= m <= 20000", "Keys and values contain no commas"],
    requirements=[
        "Match keys exactly, including case",
        "Return the first matching row when a key is duplicated",
        "Print #N/A for a key that is not in the table, rather than 0 or a blank",
        "Answer the queries in order",
    ],
    examples=[
        {
            "stdin": "3\ngold,0.2\nsilver,0.1\ngold,0.9\n3\ngold\nbronze\nGold\n",
            "explanation": (
                "gold resolves to the first row, 0.2. bronze is absent and Gold "
                "differs in case, so both are #N/A."
            ),
        }
    ],
    cases=[
        ("sample: duplicate key and a case mismatch", "3\ngold,0.2\nsilver,0.1\ngold,0.9\n3\ngold\nbronze\nGold\n", False),
        ("sample: straightforward hits", "2\na,1\nb,2\n2\nb\na\n", False),
        ("hidden: everything misses", "2\na,1\nb,2\n2\nc\nd\n", True),
        ("hidden: single row table", "1\nonly,42\n2\nonly\nother\n", True),
        ("hidden: values may look numeric or not", "2\nx,0\ny,text\n2\nx\ny\n", True),
    ],
    reference="""import sys


def main():
    lines = sys.stdin.read().split("\\n")
    n = int(lines[0].strip())
    table = {}
    for line in lines[1:1 + n]:
        key, value = line.strip().split(",")
        if key not in table:
            table[key] = value
    m = int(lines[1 + n].strip())
    for line in lines[2 + n:2 + n + m]:
        print(table.get(line.strip(), "#N/A"))


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def build_table(rows):
    # TODO: return {key: value} keeping the first occurrence of each key.
    return {}


def main():
    lines = sys.stdin.read().split("\\n")
    n = int(lines[0].strip())
    rows = [line.strip().split(",") for line in lines[1:1 + n]]
    table = build_table(rows)
    m = int(lines[1 + n].strip())
    for line in lines[2 + n:2 + n + m]:
        print(table.get(line.strip(), "#N/A"))


if __name__ == "__main__":
    main()
""",
    wrong=[
        # A miss becomes 0, which quietly poisons any downstream total.
        """import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0].strip())
table = {}
for line in lines[1:1 + n]:
    key, value = line.strip().split(",")
    table.setdefault(key, value)
m = int(lines[1 + n].strip())
for line in lines[2 + n:2 + n + m]:
    print(table.get(line.strip(), "0"))
""",
        # Last duplicate wins.
        """import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0].strip())
table = {}
for line in lines[1:1 + n]:
    key, value = line.strip().split(",")
    table[key] = value
m = int(lines[1 + n].strip())
for line in lines[2 + n:2 + n + m]:
    print(table.get(line.strip(), "#N/A"))
""",
        # Case-insensitive matching.
        """import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0].strip())
table = {}
for line in lines[1:1 + n]:
    key, value = line.strip().split(",")
    table.setdefault(key.lower(), value)
m = int(lines[1 + n].strip())
for line in lines[2 + n:2 + n + m]:
    print(table.get(line.strip().lower(), "#N/A"))
""",
    ],
)

_problem(
    id="an-sheet-sumif",
    title="SUMIF With a Comparison Criterion",
    skill_id="spreadsheet_modeling",
    concept="formulas",
    difficulty=4,
    minutes=22,
    summary="Sum the rows that satisfy a criterion expressed as an operator and a value.",
    statement=(
        "Sum the `value` column over the rows matching a criterion.\n\n"
        "The criterion is an operator and a number: one of `>`, `>=`, `<`, "
        "`<=`, `=`, `<>` applied to each row's `key` column. Print the sum to "
        "two decimal places; a criterion nothing matches sums to `0.00`, not to "
        "blank."
    ),
    input_format=(
        "Line 1: n. Line 2: the operator and the comparison number, space "
        "separated. Next n lines: `key,value` where key is an integer and value "
        "is a decimal."
    ),
    output_format="One line: the sum to two decimal places.",
    constraints=[
        "1 <= n <= 20000",
        "-1000000 <= key <= 1000000",
        "0 <= value <= 1000000",
        "The operator is one of > >= < <= = <>",
    ],
    requirements=[
        "Apply the operator exactly, including the inclusive forms",
        "Sum the value column, not the key column",
        "Print 0.00 when nothing matches",
        "Print the sum to exactly two decimal places",
    ],
    examples=[
        {
            "stdin": "4\n>= 10\n5,1.00\n10,2.00\n15,4.00\n10,8.00\n",
            "explanation": "The three rows with a key of at least 10 total 14.00.",
        }
    ],
    cases=[
        ("sample: inclusive greater-than", "4\n>= 10\n5,1.00\n10,2.00\n15,4.00\n10,8.00\n", False),
        ("sample: not-equal", "3\n<> 5\n5,1.00\n6,2.00\n7,4.00\n", False),
        ("hidden: nothing matches", "2\n> 100\n1,1.00\n2,2.00\n", True),
        ("hidden: strict versus inclusive", "3\n> 10\n10,1.00\n11,2.00\n9,4.00\n", True),
        ("hidden: equality", "3\n= 7\n7,1.50\n7,2.50\n8,9.00\n", True),
        ("hidden: negative keys and <=", "3\n<= -1\n-1,1.00\n-2,2.00\n0,4.00\n", True),
    ],
    reference="""import sys


def matches(operator, key, target):
    if operator == ">":
        return key > target
    if operator == ">=":
        return key >= target
    if operator == "<":
        return key < target
    if operator == "<=":
        return key <= target
    if operator == "=":
        return key == target
    return key != target


def main():
    lines = sys.stdin.read().split("\\n")
    n = int(lines[0].strip())
    operator, target_text = lines[1].split()
    target = int(target_text)
    total = 0.0
    for line in lines[2:2 + n]:
        key, value = line.strip().split(",")
        if matches(operator, int(key), target):
            total += float(value)
    print(f"{total:.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def matches(operator, key, target):
    # TODO: apply the operator (> >= < <= = <>) to key and target.
    return True


def main():
    lines = sys.stdin.read().split("\\n")
    n = int(lines[0].strip())
    operator, target_text = lines[1].split()
    target = int(target_text)
    total = 0.0
    for line in lines[2:2 + n]:
        key, value = line.strip().split(",")
        if matches(operator, int(key), target):
            total += float(value)
    print(f"{total:.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Inclusive and strict comparisons swapped.
        """import sys


def matches(operator, key, target):
    if operator == ">":
        return key >= target
    if operator == ">=":
        return key > target
    if operator == "<":
        return key <= target
    if operator == "<=":
        return key < target
    if operator == "=":
        return key == target
    return key != target


lines = sys.stdin.read().split("\\n")
n = int(lines[0].strip())
operator, target_text = lines[1].split()
target = int(target_text)
total = 0.0
for line in lines[2:2 + n]:
    key, value = line.strip().split(",")
    if matches(operator, int(key), target):
        total += float(value)
print(f"{total:.2f}")
""",
        # Sums the key column.
        """import sys


def matches(operator, key, target):
    return {
        ">": key > target,
        ">=": key >= target,
        "<": key < target,
        "<=": key <= target,
        "=": key == target,
        "<>": key != target,
    }[operator]


lines = sys.stdin.read().split("\\n")
n = int(lines[0].strip())
operator, target_text = lines[1].split()
target = int(target_text)
total = 0.0
for line in lines[2:2 + n]:
    key, value = line.strip().split(",")
    if matches(operator, int(key), target):
        total += int(key)
print(f"{total:.2f}")
""",
        # `<>` treated as equality.
        """import sys


def matches(operator, key, target):
    if operator == ">":
        return key > target
    if operator == ">=":
        return key >= target
    if operator == "<":
        return key < target
    if operator == "<=":
        return key <= target
    return key == target


lines = sys.stdin.read().split("\\n")
n = int(lines[0].strip())
operator, target_text = lines[1].split()
target = int(target_text)
total = 0.0
for line in lines[2:2 + n]:
    key, value = line.strip().split(",")
    if matches(operator, int(key), target):
        total += float(value)
print(f"{total:.2f}")
""",
    ],
)

_problem(
    id="an-sheet-pivot-two-keys",
    title="Pivot on Two Keys",
    skill_id="spreadsheet_modeling",
    concept="pivot table",
    difficulty=5,
    minutes=24,
    summary="Sum by (row key, column key) and print only the combinations that exist.",
    statement=(
        "Sum the amounts by the pair `(row, column)` and print `row column "
        "total` per line with the total to two decimal places.\n\n"
        "Sort by row ascending and then by column ascending. Print only the "
        "combinations that appear in the data — unlike a rectangular chart, a "
        "pivot listing does not invent empty cells here."
    ),
    input_format="Line 1: n. Next n lines: `row,column,amount`.",
    output_format="One line per existing combination: row, column and total to two decimals.",
    constraints=["1 <= n <= 20000", "0 <= amount <= 1000000", "Keys contain no commas"],
    requirements=[
        "Group by the pair of keys, not by either key alone",
        "Sort by row ascending, then by column ascending",
        "Print only the combinations present in the data",
        "Print each total to exactly two decimal places",
    ],
    examples=[
        {
            "stdin": "3\nemea,gold,100.00\nemea,gold,50.00\napac,silver,25.00\n",
            "explanation": "The two emea/gold rows combine to 150.00, and apac/silver stands alone.",
        }
    ],
    cases=[
        ("sample: two combinations", "3\nemea,gold,100.00\nemea,gold,50.00\napac,silver,25.00\n", False),
        ("sample: one row key, two column keys", "2\nr,a,1.00\nr,b,2.00\n", False),
        ("hidden: sorted output, unsorted input", "4\nz,b,1.00\na,b,1.00\nz,a,1.00\na,a,1.00\n", True),
        ("hidden: single row", "1\nx,y,9.99\n", True),
        ("hidden: same column key under different rows", "3\nr1,c,1.00\nr2,c,2.00\nr1,c,3.00\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    totals = {}
    for line in data[1:1 + n]:
        row, column, amount = line.strip().rsplit(",", 2)
        key = (row, column)
        totals[key] = totals.get(key, 0) + round(float(amount) * 100)
    for (row, column) in sorted(totals):
        print(f"{row} {column} {totals[(row, column)] / 100:.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def pivot(rows):
    # TODO: return {(row, column): total} summed over the rows.
    return {}


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    rows = [line.strip().rsplit(",", 2) for line in data[1:1 + n]]
    totals = pivot(rows)
    for key in sorted(totals):
        print(f"{key[0]} {key[1]} {totals[key]:.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Groups by the row key only, collapsing the columns together.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
totals = {}
columns = {}
for line in data[1:1 + n]:
    row, column, amount = line.strip().rsplit(",", 2)
    totals[row] = totals.get(row, 0.0) + float(amount)
    columns[row] = column
for row in sorted(totals):
    print(f"{row} {columns[row]} {totals[row]:.2f}")
""",
        # Sorted by column first.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
totals = {}
for line in data[1:1 + n]:
    row, column, amount = line.strip().rsplit(",", 2)
    key = (row, column)
    totals[key] = totals.get(key, 0.0) + float(amount)
for key in sorted(totals, key=lambda k: (k[1], k[0])):
    print(f"{key[0]} {key[1]} {totals[key]:.2f}")
""",
        # No aggregation: one line per input row.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
rows = []
for line in data[1:1 + n]:
    row, column, amount = line.strip().rsplit(",", 2)
    rows.append((row, column, float(amount)))
for row, column, amount in sorted(rows):
    print(f"{row} {column} {amount:.2f}")
""",
    ],
)

_problem(
    id="an-sheet-running-total",
    title="Add a Running Total Column",
    skill_id="spreadsheet_modeling",
    concept="absolute reference",
    difficulty=3,
    minutes=18,
    summary="The cumulative column every spreadsheet model has, and its percent-of-total sibling.",
    statement=(
        "For each row print `value running_total pct` where `running_total` is "
        "the cumulative sum up to and including that row and `pct` is the "
        "running total as a percentage of the **grand total** to one decimal "
        "place — the anchored, absolute reference that does not move as the "
        "formula is filled down.\n\n"
        "Print the values and running totals to two decimal places. When the "
        "grand total is 0, print `NA` for every percentage."
    ),
    input_format="Line 1: n. Next n lines: one decimal value.",
    output_format="One line per row: the value, the running total, and the percentage or NA.",
    constraints=["1 <= n <= 20000", "-1000000 <= value <= 1000000"],
    requirements=[
        "The running total accumulates in input order",
        "The percentage denominator is the grand total, the same for every row",
        "Print NA for the percentages when the grand total is zero",
        "Two decimal places for money, one for the percentage",
    ],
    examples=[
        {
            "stdin": "3\n25.00\n25.00\n50.00\n",
            "explanation": "The running total reaches 100.00, so the shares are 25.0, 50.0 and 100.0 percent.",
        }
    ],
    cases=[
        ("sample: quarters of a hundred", "3\n25.00\n25.00\n50.00\n", False),
        ("sample: a single row", "1\n7.50\n", False),
        ("hidden: grand total of zero", "2\n10.00\n-10.00\n", True),
        ("hidden: negatives in the middle", "3\n10.00\n-5.00\n15.00\n", True),
        ("hidden: thirds round to one decimal", "3\n1.00\n1.00\n1.00\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    values = [float(line.strip()) for line in data[1:1 + n]]
    grand = sum(values)
    running = 0.0
    for value in values:
        running += value
        if grand == 0:
            print(f"{value:.2f} {running:.2f} NA")
        else:
            print(f"{value:.2f} {running:.2f} {running * 100.0 / grand:.1f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def rows_with_running_total(values):
    # TODO: yield (value, running_total, pct_or_None) per row.
    return [(v, v, None) for v in values]


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    values = [float(line.strip()) for line in data[1:1 + n]]
    for value, running, pct in rows_with_running_total(values):
        pct_text = "NA" if pct is None else f"{pct:.1f}"
        print(f"{value:.2f} {running:.2f} {pct_text}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Percentage of the running total so far: always 100%.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
values = [float(line.strip()) for line in data[1:1 + n]]
running = 0.0
for value in values:
    running += value
    if running == 0:
        print(f"{value:.2f} {running:.2f} NA")
    else:
        print(f"{value:.2f} {running:.2f} {running * 100.0 / running:.1f}")
""",
        # The row's own share rather than the cumulative share.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
values = [float(line.strip()) for line in data[1:1 + n]]
grand = sum(values)
running = 0.0
for value in values:
    running += value
    if grand == 0:
        print(f"{value:.2f} {running:.2f} NA")
    else:
        print(f"{value:.2f} {running:.2f} {value * 100.0 / grand:.1f}")
""",
        # Running total excludes the current row.
        """import sys

data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
values = [float(line.strip()) for line in data[1:1 + n]]
grand = sum(values)
running = 0.0
for value in values:
    if grand == 0:
        print(f"{value:.2f} {running:.2f} NA")
    else:
        print(f"{value:.2f} {running:.2f} {running * 100.0 / grand:.1f}")
    running += value
""",
    ],
)

_problem(
    id="an-sheet-tiered-commission",
    title="Tiered Commission, Not a Cliff",
    skill_id="spreadsheet_modeling",
    concept="formulas",
    difficulty=6,
    minutes=28,
    summary="Each band's rate applies only to the portion of sales inside that band.",
    statement=(
        "Commission is tiered: `10%` on the first 10,000, `15%` on the portion "
        "from 10,000 to 50,000, and `20%` on everything above 50,000.\n\n"
        "Only the **portion** inside each band earns that band's rate. Applying "
        "the top rate to the whole amount — a cliff — overpays every seller who "
        "crosses a threshold, and it is the single most common spreadsheet "
        "modelling error.\n\n"
        "Print the commission for each sales figure to two decimal places, one "
        "per line."
    ),
    input_format="Line 1: n. Next n lines: one sales figure, a decimal, non-negative.",
    output_format="One commission per line, to two decimal places.",
    constraints=[
        "1 <= n <= 20000",
        "0 <= sales <= 100000000",
        "Bands: 10% to 10000, 15% from 10000 to 50000, 20% above 50000",
    ],
    requirements=[
        "Apply each rate only to the portion of sales inside that band",
        "A figure exactly on a threshold earns nothing from the band above it",
        "Zero sales earn zero commission",
        "Print each commission to exactly two decimal places",
    ],
    examples=[
        {
            "stdin": "2\n10000\n60000\n",
            "explanation": (
                "10,000 earns 1,000.00. 60,000 earns 1,000 + 6,000 + 2,000 = "
                "9,000.00, not 20% of the whole 60,000."
            ),
        }
    ],
    cases=[
        ("sample: on the first threshold and above the second", "2\n10000\n60000\n", False),
        ("sample: inside the middle band", "1\n20000\n", False),
        ("hidden: zero sales", "1\n0\n", True),
        ("hidden: exactly on the upper threshold", "1\n50000\n", True),
        ("hidden: a penny over a threshold", "2\n10000.01\n50000.01\n", True),
        ("hidden: a very large figure", "1\n100000000\n", True),
    ],
    reference="""import sys


def commission(sales):
    total = 0.0
    total += min(sales, 10000) * 0.10
    if sales > 10000:
        total += (min(sales, 50000) - 10000) * 0.15
    if sales > 50000:
        total += (sales - 50000) * 0.20
    return total


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    for line in data[1:1 + n]:
        print(f"{commission(float(line.strip())):.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def commission(sales):
    # TODO: 10% on the first 10000, 15% on 10000-50000, 20% above 50000, each
    # applied only to the portion inside the band.
    return 0.0


def main():
    data = sys.stdin.read().split("\\n")
    n = int(data[0].strip())
    for line in data[1:1 + n]:
        print(f"{commission(float(line.strip())):.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # The cliff: one rate applied to the whole amount.
        """import sys


def commission(sales):
    if sales > 50000:
        return sales * 0.20
    if sales > 10000:
        return sales * 0.15
    return sales * 0.10


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    print(f"{commission(float(line.strip())):.2f}")
""",
        # Thresholds inclusive on the wrong side.
        """import sys


def commission(sales):
    total = min(sales, 10000) * 0.10
    if sales >= 10000:
        total += (min(sales, 50000) - 10000) * 0.15
    if sales >= 50000:
        total += (sales - 50000) * 0.20
    return total + (0.15 if sales == 10000 else 0.0)


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    print(f"{commission(float(line.strip())):.2f}")
""",
        # Top band measured from zero, double counting the lower bands.
        """import sys


def commission(sales):
    total = min(sales, 10000) * 0.10
    if sales > 10000:
        total += (min(sales, 50000) - 10000) * 0.15
    if sales > 50000:
        total += sales * 0.20
    return total


data = sys.stdin.read().split("\\n")
n = int(data[0].strip())
for line in data[1:1 + n]:
    print(f"{commission(float(line.strip())):.2f}")
""",
    ],
)

_problem(
    id="an-sheet-loan-payment",
    title="Monthly Payment on a Loan",
    skill_id="spreadsheet_modeling",
    concept="formulas",
    difficulty=6,
    minutes=28,
    summary="The PMT formula, including the zero-interest case the formula divides by zero on.",
    statement=(
        "Compute the level monthly payment on a loan:\n\n"
        "    payment = P * r / (1 - (1 + r)^-n)\n\n"
        "where `P` is the principal, `n` the number of monthly payments, and "
        "`r` the **monthly** rate — the annual percentage rate divided by 12 and "
        "by 100. Dividing by 12 is not optional: using the annual rate as the "
        "monthly one overstates the payment enormously.\n\n"
        "When the annual rate is 0 the formula divides by zero, and the answer "
        "is simply `P / n`. Print the payment to two decimal places."
    ),
    input_format="One line: P, annual_rate_percent and n, space separated. P and the rate are decimals, n is an integer.",
    output_format="One line: the monthly payment to two decimal places.",
    constraints=["0 < P <= 100000000", "0 <= annual rate <= 100", "1 <= n <= 600"],
    requirements=[
        "Convert the annual percentage rate to a monthly fraction",
        "Use the level-payment formula given",
        "Handle a zero rate as P / n rather than dividing by zero",
        "Print the payment to exactly two decimal places",
    ],
    examples=[
        {
            "stdin": "10000 12 12\n",
            "explanation": (
                "A 12% annual rate is 1% a month, so twelve payments of 888.49 "
                "repay 10,000."
            ),
        }
    ],
    cases=[
        ("sample: one year at 12 percent", "10000 12 12\n", False),
        ("sample: interest free", "1200 0 12\n", False),
        ("hidden: a single payment", "500 6 1\n", True),
        ("hidden: a long mortgage", "250000 4.5 360\n", True),
        ("hidden: zero rate over many months", "6000 0 600\n", True),
        ("hidden: a high rate", "1000 100 24\n", True),
    ],
    reference="""import sys


def main():
    parts = sys.stdin.read().split()
    principal = float(parts[0])
    annual = float(parts[1])
    months = int(parts[2])
    rate = annual / 100.0 / 12.0
    if rate == 0:
        print(f"{principal / months:.2f}")
        return
    payment = principal * rate / (1 - (1 + rate) ** -months)
    print(f"{payment:.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def payment(principal, annual_percent, months):
    # TODO: convert the annual percentage to a monthly rate and apply the
    # level-payment formula, handling a zero rate.
    return 0.0


def main():
    parts = sys.stdin.read().split()
    print(f"{payment(float(parts[0]), float(parts[1]), int(parts[2])):.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Annual rate used as the monthly rate.
        """import sys

parts = sys.stdin.read().split()
principal = float(parts[0])
annual = float(parts[1])
months = int(parts[2])
rate = annual / 100.0
if rate == 0:
    print(f"{principal / months:.2f}")
else:
    print(f"{principal * rate / (1 - (1 + rate) ** -months):.2f}")
""",
        # Simple interest spread over the term.
        """import sys

parts = sys.stdin.read().split()
principal = float(parts[0])
annual = float(parts[1])
months = int(parts[2])
total = principal * (1 + annual / 100.0 * months / 12.0)
print(f"{total / months:.2f}")
""",
        # Sign error in the exponent.
        """import sys

parts = sys.stdin.read().split()
principal = float(parts[0])
annual = float(parts[1])
months = int(parts[2])
rate = annual / 100.0 / 12.0
if rate == 0:
    print(f"{principal / months:.2f}")
else:
    print(f"{principal * rate / (1 - (1 + rate) ** months):.2f}")
""",
    ],
)

_problem(
    id="an-sheet-growth-scenario",
    title="Project Revenue Under a Growth Scenario",
    skill_id="spreadsheet_modeling",
    concept="scenario model",
    difficulty=5,
    minutes=25,
    summary="Compound the growth year on year instead of adding it to the base each time.",
    statement=(
        "A model starts from `units * price` in year 1 and grows by `g` percent "
        "**compounding** each year, so year `k`'s revenue is "
        "`units * price * (1 + g/100)^(k-1)`.\n\n"
        "Adding the same absolute increment every year is linear growth, not "
        "compound growth, and the two diverge quickly.\n\n"
        "Print `year revenue` for years 1 to `y`, one per line, with the "
        "revenue to two decimal places. Negative growth is allowed."
    ),
    input_format="One line: units, price, growth_percent and y, space separated. units and y are integers; price and growth are decimals.",
    output_format="One line per year: the year number and its revenue to two decimal places.",
    constraints=["0 <= units <= 1000000", "0 <= price <= 100000", "-100 <= growth <= 100", "1 <= y <= 50"],
    requirements=[
        "Year 1 is units * price with no growth applied",
        "Growth compounds on the previous year, not on the base",
        "Print every year from 1 to y",
        "Print each revenue to exactly two decimal places",
    ],
    examples=[
        {
            "stdin": "100 10 10 3\n",
            "explanation": (
                "1000.00, then 1100.00, then 1210.00 — the third year grows on "
                "the second, not on the first."
            ),
        }
    ],
    cases=[
        ("sample: ten percent for three years", "100 10 10 3\n", False),
        ("sample: no growth", "10 5 0 2\n", False),
        ("hidden: decline", "100 10 -50 3\n", True),
        ("hidden: a single year", "7 3 25 1\n", True),
        ("hidden: zero base", "0 10 10 3\n", True),
        ("hidden: long horizon compounds far above linear", "1 100 20 10\n", True),
    ],
    reference="""import sys


def main():
    parts = sys.stdin.read().split()
    units = int(parts[0])
    price = float(parts[1])
    growth = float(parts[2])
    years = int(parts[3])
    base = units * price
    for year in range(1, years + 1):
        print(f"{year} {base * (1 + growth / 100.0) ** (year - 1):.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def revenue(base, growth, year):
    # TODO: return the year's revenue, compounding growth from year 1.
    return base


def main():
    parts = sys.stdin.read().split()
    base = int(parts[0]) * float(parts[1])
    growth = float(parts[2])
    years = int(parts[3])
    for year in range(1, years + 1):
        print(f"{year} {revenue(base, growth, year):.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Linear growth: the same increment every year.
        """import sys

parts = sys.stdin.read().split()
base = int(parts[0]) * float(parts[1])
growth = float(parts[2])
years = int(parts[3])
increment = base * growth / 100.0
for year in range(1, years + 1):
    print(f"{year} {base + increment * (year - 1):.2f}")
""",
        # Growth applied in year 1 as well.
        """import sys

parts = sys.stdin.read().split()
base = int(parts[0]) * float(parts[1])
growth = float(parts[2])
years = int(parts[3])
for year in range(1, years + 1):
    print(f"{year} {base * (1 + growth / 100.0) ** year:.2f}")
""",
        # Growth treated as a fraction rather than a percentage.
        """import sys

parts = sys.stdin.read().split()
base = int(parts[0]) * float(parts[1])
growth = float(parts[2])
years = int(parts[3])
for year in range(1, years + 1):
    print(f"{year} {base * (1 + growth) ** (year - 1):.2f}")
""",
    ],
)

_problem(
    id="an-sheet-break-even",
    title="Break-Even Units",
    skill_id="spreadsheet_modeling",
    concept="scenario model",
    difficulty=5,
    minutes=24,
    summary="Round the answer up, and say 'never' when the contribution margin is not positive.",
    statement=(
        "Break-even is the number of whole units at which contribution covers "
        "fixed costs: `ceil(fixed / (price - variable))`.\n\n"
        "Round **up** — a fractional unit does not cover the gap. If the price "
        "is at or below the variable cost, every extra unit loses money and no "
        "volume ever breaks even: print `never`. If fixed costs are 0 the answer "
        "is `0`."
    ),
    input_format="One line: fixed, price and variable, space separated decimals.",
    output_format="One line: the break-even unit count as an integer, or `never`.",
    constraints=["0 <= fixed <= 100000000", "0 <= price, variable <= 100000"],
    requirements=[
        "Contribution per unit is price minus variable cost",
        "Print 'never' when the contribution is zero or negative",
        "Round the unit count up",
        "Zero fixed costs break even at 0 units",
    ],
    examples=[
        {
            "stdin": "1000 25 15\n",
            "explanation": "Each unit contributes 10, so 100 units cover the 1,000 of fixed costs.",
        }
    ],
    cases=[
        ("sample: a clean hundred", "1000 25 15\n", False),
        ("sample: price below cost", "1000 10 15\n", False),
        ("hidden: price equals variable cost", "1000 15 15\n", True),
        ("hidden: fractional result rounds up", "1000 25 14.9\n", True),
        ("hidden: no fixed costs", "0 10 5\n", True),
        ("hidden: a tiny margin needs a lot of volume", "100 10.01 10\n", True),
    ],
    reference="""import sys
import math


def main():
    fixed, price, variable = (float(x) for x in sys.stdin.read().split()[:3])
    contribution = price - variable
    if contribution <= 0:
        print("never")
        return
    print(math.ceil(fixed / contribution))


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def break_even(fixed, price, variable):
    # TODO: return the whole unit count, or None when it never breaks even.
    return 0


def main():
    fixed, price, variable = (float(x) for x in sys.stdin.read().split()[:3])
    result = break_even(fixed, price, variable)
    print("never" if result is None else result)


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Truncates, so the answer is one unit short of break-even.
        """import sys

fixed, price, variable = (float(x) for x in sys.stdin.read().split()[:3])
contribution = price - variable
if contribution <= 0:
    print("never")
else:
    print(int(fixed / contribution))
""",
        # Divides by the price, ignoring the variable cost.
        """import sys
import math

fixed, price, variable = (float(x) for x in sys.stdin.read().split()[:3])
if price <= 0:
    print("never")
else:
    print(math.ceil(fixed / price))
""",
        # A zero contribution is treated as breaking even immediately.
        """import sys
import math

fixed, price, variable = (float(x) for x in sys.stdin.read().split()[:3])
contribution = price - variable
if contribution < 0:
    print("never")
elif contribution == 0:
    print(0)
else:
    print(math.ceil(fixed / contribution))
""",
    ],
)

_problem(
    id="an-sheet-cagr",
    title="Compound Annual Growth Rate",
    skill_id="spreadsheet_modeling",
    concept="scenario model",
    difficulty=5,
    minutes=24,
    summary="The geometric growth rate, not the average of the yearly changes.",
    statement=(
        "Print the compound annual growth rate as a percentage to two decimal "
        "places:\n\n"
        "    CAGR = ((end / begin)^(1 / years) - 1) * 100\n\n"
        "The average of the yearly percentage changes is a different — and "
        "always larger or equal — number, which is why CAGR is what gets "
        "reported.\n\n"
        "When `begin` is 0 there is no growth rate: print `NA`. A decline gives "
        "a negative rate."
    ),
    input_format="One line: begin, end and years, space separated. begin and end are decimals, years is an integer.",
    output_format="One line: the CAGR percentage to two decimal places, or `NA`.",
    constraints=["0 <= begin <= 1000000000", "0 <= end <= 1000000000", "1 <= years <= 100"],
    requirements=[
        "Use the geometric formula, not the mean of the yearly changes",
        "Express the answer as a percentage to two decimal places",
        "Print NA when the beginning value is zero",
        "A decline produces a negative percentage",
    ],
    examples=[
        {
            "stdin": "100 121 2\n",
            "explanation": "Growing from 100 to 121 over two years is 10.00% a year compounded.",
        }
    ],
    cases=[
        ("sample: ten percent a year", "100 121 2\n", False),
        ("sample: one year", "100 150 1\n", False),
        ("hidden: zero beginning value", "0 100 3\n", True),
        ("hidden: a decline", "200 100 2\n", True),
        ("hidden: no change", "100 100 5\n", True),
        ("hidden: falling to zero", "100 0 4\n", True),
        ("hidden: a long horizon", "1000 8000 30\n", True),
    ],
    reference="""import sys


def main():
    parts = sys.stdin.read().split()
    begin, end = float(parts[0]), float(parts[1])
    years = int(parts[2])
    if begin == 0:
        print("NA")
        return
    print(f"{((end / begin) ** (1.0 / years) - 1) * 100:.2f}")


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def cagr(begin, end, years):
    # TODO: return the compound annual growth rate as a percentage, or None
    # when begin is zero.
    return 0.0


def main():
    parts = sys.stdin.read().split()
    result = cagr(float(parts[0]), float(parts[1]), int(parts[2]))
    print("NA" if result is None else f"{result:.2f}")


if __name__ == "__main__":
    main()
""",
    wrong=[
        # Total growth spread evenly: the simple average, not the compound rate.
        """import sys

parts = sys.stdin.read().split()
begin, end = float(parts[0]), float(parts[1])
years = int(parts[2])
if begin == 0:
    print("NA")
else:
    print(f"{(end - begin) / begin * 100 / years:.2f}")
""",
        # Forgets to subtract one, so 10% growth reports as 110%.
        """import sys

parts = sys.stdin.read().split()
begin, end = float(parts[0]), float(parts[1])
years = int(parts[2])
if begin == 0:
    print("NA")
else:
    print(f"{(end / begin) ** (1.0 / years) * 100:.2f}")
""",
        # Uses years - 1 periods, which is off by one for every horizon.
        """import sys

parts = sys.stdin.read().split()
begin, end = float(parts[0]), float(parts[1])
years = int(parts[2])
if begin == 0:
    print("NA")
elif years == 1:
    print(f"{(end / begin - 1) * 100:.2f}")
else:
    print(f"{((end / begin) ** (1.0 / (years - 1)) - 1) * 100:.2f}")
""",
    ],
)

_problem(
    id="an-sheet-absolute-reference",
    title="Fill a Formula Down and Across",
    skill_id="spreadsheet_modeling",
    concept="absolute reference",
    difficulty=5,
    minutes=25,
    summary="A grid where the row header, the column header and one anchored cell all matter.",
    statement=(
        "Build the grid a spreadsheet produces from `=B$1 * $A2 * $C$1` filled "
        "down and across: cell `(i, j)` is "
        "`row_header[i] * column_header[j] * factor`, where `factor` is the "
        "anchored cell used by every formula.\n\n"
        "Print one line per row: the row's values in column order, space "
        "separated, each an integer. Mixing the anchors up transposes the grid "
        "or drops the factor, which is exactly what a mis-anchored fill does."
    ),
    input_format=(
        "Line 1: rows, cols and factor, space separated integers.\n"
        "Line 2: `rows` space-separated integers — the row headers.\n"
        "Line 3: `cols` space-separated integers — the column headers."
    ),
    output_format="One line per row: the row's cell values, space separated.",
    constraints=["1 <= rows, cols <= 500", "-1000 <= header, factor <= 1000"],
    requirements=[
        "Cell (i, j) multiplies the i-th row header by the j-th column header",
        "Every cell also multiplies by the single anchored factor",
        "Print rows in order, and columns in order within a row",
        "Values are integers with no decimal point",
    ],
    examples=[
        {
            "stdin": "2 3 2\n1 10\n1 2 3\n",
            "explanation": (
                "The first row is 1*1*2, 1*2*2, 1*3*2; the second scales all of "
                "it by 10."
            ),
        }
    ],
    cases=[
        ("sample: two by three", "2 3 2\n1 10\n1 2 3\n", False),
        ("sample: single cell", "1 1 5\n3\n7\n", False),
        ("hidden: factor of one", "2 2 1\n2 3\n4 5\n", True),
        ("hidden: a zero factor blanks the grid", "2 2 0\n1 2\n3 4\n", True),
        ("hidden: negatives", "2 2 -1\n-1 2\n3 -4\n", True),
        ("hidden: the grid is not square, so a transpose is visible", "3 1 1\n1 2 3\n5\n", True),
    ],
    reference="""import sys


def main():
    data = sys.stdin.read().split("\\n")
    rows, cols, factor = (int(x) for x in data[0].split()[:3])
    row_headers = [int(x) for x in data[1].split()[:rows]]
    col_headers = [int(x) for x in data[2].split()[:cols]]
    for row_value in row_headers:
        print(" ".join(str(row_value * col_value * factor) for col_value in col_headers))


if __name__ == "__main__":
    main()
""",
    starter="""import sys


def grid(row_headers, col_headers, factor):
    # TODO: return a list of rows, each a list of row_header * col_header *
    # factor.
    return [[0] * len(col_headers) for _ in row_headers]


def main():
    data = sys.stdin.read().split("\\n")
    rows, cols, factor = (int(x) for x in data[0].split()[:3])
    row_headers = [int(x) for x in data[1].split()[:rows]]
    col_headers = [int(x) for x in data[2].split()[:cols]]
    for line in grid(row_headers, col_headers, factor):
        print(" ".join(str(value) for value in line))


if __name__ == "__main__":
    main()
""",
    wrong=[
        # The factor was not anchored, so it drops out of the formula.
        """import sys

data = sys.stdin.read().split("\\n")
rows, cols, factor = (int(x) for x in data[0].split()[:3])
row_headers = [int(x) for x in data[1].split()[:rows]]
col_headers = [int(x) for x in data[2].split()[:cols]]
for row_value in row_headers:
    print(" ".join(str(row_value * col_value) for col_value in col_headers))
""",
        # Rows and columns swapped: the classic mis-anchored fill.
        """import sys

data = sys.stdin.read().split("\\n")
rows, cols, factor = (int(x) for x in data[0].split()[:3])
row_headers = [int(x) for x in data[1].split()[:rows]]
col_headers = [int(x) for x in data[2].split()[:cols]]
for col_value in col_headers:
    print(" ".join(str(row_value * col_value * factor) for row_value in row_headers))
""",
        # Row header anchored to the first row, so every row is identical.
        """import sys

data = sys.stdin.read().split("\\n")
rows, cols, factor = (int(x) for x in data[0].split()[:3])
row_headers = [int(x) for x in data[1].split()[:rows]]
col_headers = [int(x) for x in data[2].split()[:cols]]
for _row_value in row_headers:
    print(" ".join(str(row_headers[0] * col_value * factor) for col_value in col_headers))
""",
    ],
)

ANALYTICS_SKILL_COUNTS: dict[str, int] = {}
for _module in ANALYTICS_MODULES:
    ANALYTICS_SKILL_COUNTS[_module["skill_id"]] = (
        ANALYTICS_SKILL_COUNTS.get(_module["skill_id"], 0) + 1
    )

# Ten per skill is the authoring target for this path; fewer means the bank is
# unfinished, and finding that out at import time beats finding it in the UI.
for _skill, _count in ANALYTICS_SKILL_COUNTS.items():
    if _count < 10:
        raise AnalyticsAuthoringError(f"{_skill} has only {_count} questions; ten are required")
