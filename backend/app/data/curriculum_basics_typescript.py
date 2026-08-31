"""TypeScript basics: twelve judged problems about the type system itself.

Why these problems exist
------------------------
Adding TypeScript by re-labelling the JavaScript catalogue would teach nothing:
the point of TypeScript is the part that disappears at runtime. So each question
here is chosen because a *type* feature is the natural way to solve it —
annotations, interfaces, type aliases, unions of string literals, optional and
default parameters, tuples, generics, `unknown` narrowing, enums, discriminated
unions, user-defined type guards, and `keyof`-indexed access — and each one is
still graded the only honest way: by compiling and running the learner's program
against stdin/stdout cases in the real judge.

The judge type-checks under `--strict` (see
`app/services/code_execution_service.py`), so a type error is a failed
submission. That is deliberate and it is what makes these problems worth doing:
`classify` cannot reach `.length` on an `unknown` without narrowing it first, and
no amount of correct-looking runtime logic will get past the compiler.

The authoring contract, enforced at import time by `_problem`
-------------------------------------------------------------
* `oracle` is a correct **Python** program and is the only source of expected
  output: every case's `expected_stdout` and every worked example's `stdout` is
  derived by running it. Nothing is hand-typed, so nothing can go stale. Python
  is used rather than the TypeScript reference because deriving expectations at
  import time must not require a Node toolchain — but the two are proven to
  agree, case for case, by `scripts/verify_typescript.py`.
* `reference` is a correct TypeScript program. It never reaches a client.
* `wrong` holds TypeScript programs a learner plausibly writes that are subtly
  incorrect. `scripts/verify_typescript.py` proves each one is rejected by at
  least one declared case.
* `starter` plumbs I/O, type-checks, and leaves the logic to a `TODO`. It must
  fail the suite; the verification script proves that too.
* Every question declares at least one visible and at least one hidden case, and
  the import refuses a question whose cases all expect the same output — a
  suite a hardcoded constant could satisfy grades nothing.

`reference` and `wrong` are stored in `REFERENCE_SOLUTIONS` / `WRONG_SOLUTIONS`,
keyed by module id, and never on the module dict, so there is no path by which a
solution can be served.
"""

from __future__ import annotations

import io
import sys
from typing import Any

TYPESCRIPT_BASICS_MODULES: list[dict[str, Any]] = []

#: module id -> the correct TypeScript program. Never served.
REFERENCE_SOLUTIONS: dict[str, str] = {}

#: module id -> TypeScript programs that must be rejected. Never served.
WRONG_SOLUTIONS: dict[str, list[str]] = {}

SKILL_ID = "typescript_basics"


class TypeScriptAuthoringError(RuntimeError):
    """A question cannot grade honestly, so it must not be importable."""


def _run_oracle(source: str, stdin_text: str) -> str:
    """Run the Python oracle against `stdin_text` and return its stdout."""
    stdout = io.StringIO()
    original_stdin, original_stdout = sys.stdin, sys.stdout
    sys.stdin, sys.stdout = io.StringIO(stdin_text), stdout
    try:
        exec(compile(source, "<typescript-oracle>", "exec"), {"__name__": "__main__"})
    finally:
        sys.stdin, sys.stdout = original_stdin, original_stdout
    return stdout.getvalue().strip()


def _problem(
    *,
    slug: str,
    title: str,
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
    oracle: str,
    reference: str,
    starter: str,
    wrong: list[str],
) -> dict[str, Any]:
    module_id = f"ts-basics-{slug}"
    if not wrong:
        raise TypeScriptAuthoringError(
            f"{module_id}: a question with no wrong answer proves nothing"
        )
    if "TODO" not in starter:
        raise TypeScriptAuthoringError(f"{module_id}: the starter must leave a TODO")
    if not any(hidden for _, _, hidden in cases):
        raise TypeScriptAuthoringError(
            f"{module_id}: no hidden case, so Submit gates nothing"
        )
    if not any(not hidden for _, _, hidden in cases):
        raise TypeScriptAuthoringError(
            f"{module_id}: no visible case for the learner to Run"
        )

    test_cases: list[dict[str, Any]] = []
    for name, stdin_text, hidden in cases:
        expected = _run_oracle(oracle, stdin_text)
        if not expected:
            raise TypeScriptAuthoringError(
                f"{module_id}: case '{name}' expects no output, which grades nothing"
            )
        test_cases.append(
            {
                "name": name,
                "stdin": stdin_text,
                "expected_stdout": expected,
                "hidden": hidden,
            }
        )

    # A suite whose every case expects the same string is passed by `console.log`
    # of that string. Discrimination is a property of the cases, not of goodwill.
    if len({case["expected_stdout"] for case in test_cases}) < 2:
        raise TypeScriptAuthoringError(
            f"{module_id}: every case expects the same output, so a hardcoded "
            "constant would pass. Add a case that distinguishes it."
        )

    worked = [
        {
            "stdin": example["stdin"],
            "stdout": _run_oracle(oracle, example["stdin"]),
            "explanation": example["explanation"],
        }
        for example in examples
    ]
    if not worked or not all(entry["explanation"].strip() for entry in worked):
        raise TypeScriptAuthoringError(
            f"{module_id}: every worked example needs an explanation"
        )

    module: dict[str, Any] = {
        "id": module_id,
        "title": title,
        "kind": "challenge",
        "practice_layer": "language",
        "track": "webdev",
        "skill_id": SKILL_ID,
        "technology": "TypeScript",
        "language": "typescript",
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

    REFERENCE_SOLUTIONS[module_id] = reference
    WRONG_SOLUTIONS[module_id] = list(wrong)
    TYPESCRIPT_BASICS_MODULES.append(module)
    return module


# Shared stdin plumbing. Every starter and solution reads stdin explicitly and
# with explicit types: under `--strict` an unannotated parameter is an error, and
# a learner should not spend their first TypeScript exercise fighting the
# compiler over I/O they did not write.
_READ_LINES = (
    'const rawInput: string = require("fs").readFileSync(0, "utf8");\n'
    'const lines: string[] = rawInput.split("\\n");\n'
)
_READ_TOKENS = (
    'const tokens: string[] = require("fs")\n'
    '  .readFileSync(0, "utf8")\n'
    "  .split(/\\s+/)\n"
    "  .filter((token: string) => token.length > 0);\n"
)


# =========================================================================== #
#  1. Type annotations                                                        #
# =========================================================================== #

_problem(
    slug="annotate-totals",
    title="Annotate a Totals Function",
    concept="type annotations",
    difficulty=2,
    minutes=15,
    summary="Write your first annotated function: take an array of numbers and report their total and their average to two decimal places.",
    statement=(
        "TypeScript adds nothing at runtime. What it adds is a promise about the "
        "shape of your data, written next to the code that depends on it.\n\n"
        "Implement `summarise(values: number[]): string`. It returns the total of "
        "the values, a single space, then the mean formatted to exactly two "
        "decimal places (`toFixed(2)`).\n\n"
        "The annotations are not decoration: the judge type-checks your file under "
        "`--strict`, so returning a number where the signature promises a string "
        "is a failed submission, not a warning."
    ),
    input_format=(
        "Line 1: n, the count of values.\nLine 2: n space-separated integers."
    ),
    output_format=(
        "One line: the total, a space, then the mean with exactly two decimal "
        "places."
    ),
    constraints=[
        "1 <= n <= 20000",
        "-1000000000 <= values[i] <= 1000000000",
        "Every mean in the test data is exact at two decimal places, so no "
        "rounding convention can change the answer",
    ],
    requirements=[
        "Annotate the parameter as number[] and the return type as string",
        "Print the total and the mean separated by one space",
        "Format the mean with exactly two decimal places, including trailing zeros",
        "Handle negative values and a single value",
    ],
    examples=[
        {
            "stdin": "5\n1 2 3 4 5\n",
            "explanation": "The five values total 15 and their mean is 3, printed as `3.00` because two decimal places are always shown.",
        },
        {
            "stdin": "4\n10 20 30 41\n",
            "explanation": "The total is 101 and 101 / 4 is 25.25, which already has two decimal places.",
        },
    ],
    cases=[
        ("sample: consecutive values", "5\n1 2 3 4 5\n", False),
        ("sample: fractional mean", "4\n10 20 30 41\n", False),
        ("hidden: single negative value", "1\n-7\n", True),
        ("hidden: mean with a half", "8\n4 8 12 16 20 12 14 14\n", True),
        ("hidden: large values", "2\n1000000000 1000000000\n", True),
        ("hidden: all negative", "3\n-1 -2 -3\n", True),
    ],
    oracle="""import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
total = sum(values)
mean = total / n
print(f"{total} {mean:.2f}")
""",
    reference="""function summarise(values: number[]): string {
  let total = 0;
  for (const value of values) {
    total += value;
  }
  const mean: number = total / values.length;
  return `${total} ${mean.toFixed(2)}`;
}

"""
    + _READ_TOKENS
    + """const n: number = Number(tokens[0]);
const values: number[] = tokens.slice(1, 1 + n).map(Number);
console.log(summarise(values));
""",
    starter="""function summarise(values: number[]): string {
  // TODO: return the total, a space, then the mean with two decimal places
  return "";
}

"""
    + _READ_TOKENS
    + """const n: number = Number(tokens[0]);
const values: number[] = tokens.slice(1, 1 + n).map(Number);
console.log(summarise(values));
""",
    wrong=[
        # Truncates the mean instead of formatting it.
        """function summarise(values: number[]): string {
  let total = 0;
  for (const value of values) {
    total += value;
  }
  return `${total} ${Math.floor(total / values.length)}`;
}

"""
        + _READ_TOKENS
        + """const n: number = Number(tokens[0]);
const values: number[] = tokens.slice(1, 1 + n).map(Number);
console.log(summarise(values));
""",
        # Forgets toFixed, so trailing zeros vanish.
        """function summarise(values: number[]): string {
  let total = 0;
  for (const value of values) {
    total += value;
  }
  return `${total} ${total / values.length}`;
}

"""
        + _READ_TOKENS
        + """const n: number = Number(tokens[0]);
const values: number[] = tokens.slice(1, 1 + n).map(Number);
console.log(summarise(values));
""",
        # Sums magnitudes, which is right until a value is negative.
        """function summarise(values: number[]): string {
  let total = 0;
  for (const value of values) {
    total += Math.abs(value);
  }
  return `${total} ${(total / values.length).toFixed(2)}`;
}

"""
        + _READ_TOKENS
        + """const n: number = Number(tokens[0]);
const values: number[] = tokens.slice(1, 1 + n).map(Number);
console.log(summarise(values));
""",
    ],
)


# =========================================================================== #
#  2. Interfaces                                                              #
# =========================================================================== #

_ORDER_PLUMBING = (
    _READ_LINES
    + """const orderCount: number = Number(lines[0]);
const orderLines: OrderLine[] = [];
for (let i = 1; i <= orderCount; i++) {
  const parts: string[] = lines[i].trim().split(/\\s+/);
  orderLines.push({
    sku: parts[0],
    qty: Number(parts[1]),
    unitPriceCents: Number(parts[2]),
  });
}
summarise(orderLines);
"""
)

_problem(
    slug="interface-order-lines",
    title="Describe an Order Line with an Interface",
    concept="interfaces",
    difficulty=3,
    minutes=20,
    summary="An interface names the shape your function expects. Use one to total an order and find its biggest line.",
    statement=(
        "An `interface` gives a name to the shape of an object, so a function can "
        "say what it needs instead of hoping the caller passes the right bag of "
        "properties.\n\n"
        "`OrderLine` is already declared for you and the input is already parsed "
        "into `OrderLine[]`. Implement `summarise(lines: OrderLine[]): void` so it "
        "prints two lines: the order's total revenue in cents, then the SKU of the "
        "single line with the highest revenue.\n\n"
        "A line's revenue is `qty * unitPriceCents`. If two lines tie on revenue, "
        "report the SKU that comes first alphabetically."
    ),
    input_format=(
        "Line 1: n, the number of order lines.\n"
        "Next n lines: a SKU (letters, no spaces), the quantity, and the unit "
        "price in cents, separated by spaces."
    ),
    output_format=(
        "Line 1: the total revenue in cents.\nLine 2: the SKU of the "
        "highest-revenue line, breaking ties alphabetically."
    ),
    constraints=[
        "1 <= n <= 20000",
        "0 <= qty <= 100000",
        "0 <= unitPriceCents <= 10000000",
        "A SKU is a non-empty string of lowercase letters",
    ],
    requirements=[
        "Type the parameter as OrderLine[] and the return type as void",
        "Compute each line's revenue as qty * unitPriceCents",
        "Print the total revenue on the first line",
        "Print the winning SKU on the second line, breaking ties alphabetically",
    ],
    examples=[
        {
            "stdin": "3\nwidget 2 500\nbolt 10 30\nnut 1 1200\n",
            "explanation": "Revenues are 1000, 300 and 1200, totalling 2500. `nut` is the largest at 1200.",
        },
        {
            "stdin": "2\nzeta 2 100\nalpha 1 200\n",
            "explanation": "Both lines earn 200, so the tie is broken alphabetically and `alpha` wins.",
        },
    ],
    cases=[
        ("sample: three lines", "3\nwidget 2 500\nbolt 10 30\nnut 1 1200\n", False),
        ("sample: alphabetical tie-break", "2\nzeta 2 100\nalpha 1 200\n", False),
        ("hidden: single line", "1\nsolo 1 1\n", True),
        ("hidden: a zero-quantity line", "2\nfree 0 999\npaid 3 100\n", True),
        ("hidden: large revenue", "2\na 1000 1000000\nb 1 1\n", True),
        ("hidden: three-way tie", "3\nmid 1 5\ncap 5 1\nzip 1 5\n", True),
    ],
    oracle="""import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0])
total = 0
best_revenue = -1
best_sku = ""
for index in range(1, n + 1):
    sku, qty, price = lines[index].split()
    revenue = int(qty) * int(price)
    total += revenue
    if revenue > best_revenue or (revenue == best_revenue and sku < best_sku):
        best_revenue = revenue
        best_sku = sku
print(total)
print(best_sku)
""",
    reference="""interface OrderLine {
  sku: string;
  qty: number;
  unitPriceCents: number;
}

function summarise(lines: OrderLine[]): void {
  let total = 0;
  let bestRevenue = -1;
  let bestSku = "";
  for (const line of lines) {
    const revenue: number = line.qty * line.unitPriceCents;
    total += revenue;
    if (revenue > bestRevenue || (revenue === bestRevenue && line.sku < bestSku)) {
      bestRevenue = revenue;
      bestSku = line.sku;
    }
  }
  console.log(total);
  console.log(bestSku);
}

"""
    + _ORDER_PLUMBING,
    starter="""interface OrderLine {
  sku: string;
  qty: number;
  unitPriceCents: number;
}

function summarise(lines: OrderLine[]): void {
  // TODO: print the total revenue, then the highest-revenue SKU
  console.log(0);
  console.log("");
}

"""
    + _ORDER_PLUMBING,
    wrong=[
        # Forgets that a line has a quantity.
        """interface OrderLine {
  sku: string;
  qty: number;
  unitPriceCents: number;
}

function summarise(lines: OrderLine[]): void {
  let total = 0;
  let bestRevenue = -1;
  let bestSku = "";
  for (const line of lines) {
    const revenue: number = line.unitPriceCents;
    total += revenue;
    if (revenue > bestRevenue) {
      bestRevenue = revenue;
      bestSku = line.sku;
    }
  }
  console.log(total);
  console.log(bestSku);
}

"""
        + _ORDER_PLUMBING,
        # Keeps the first line seen on a tie instead of the alphabetical winner.
        """interface OrderLine {
  sku: string;
  qty: number;
  unitPriceCents: number;
}

function summarise(lines: OrderLine[]): void {
  let total = 0;
  let bestRevenue = -1;
  let bestSku = "";
  for (const line of lines) {
    const revenue: number = line.qty * line.unitPriceCents;
    total += revenue;
    if (revenue > bestRevenue) {
      bestRevenue = revenue;
      bestSku = line.sku;
    }
  }
  console.log(total);
  console.log(bestSku);
}

"""
        + _ORDER_PLUMBING,
        # Reports the winning revenue instead of the winning SKU.
        """interface OrderLine {
  sku: string;
  qty: number;
  unitPriceCents: number;
}

function summarise(lines: OrderLine[]): void {
  let total = 0;
  let bestRevenue = -1;
  for (const line of lines) {
    const revenue: number = line.qty * line.unitPriceCents;
    total += revenue;
    if (revenue > bestRevenue) {
      bestRevenue = revenue;
    }
  }
  console.log(total);
  console.log(bestRevenue);
}

"""
        + _ORDER_PLUMBING,
    ],
)


# =========================================================================== #
#  3. Union of string literal types                                           #
# =========================================================================== #

_STATUS_PLUMBING = (
    _READ_LINES
    + """const statusCount: number = Number(lines[0]);
const statusTokens: string[] = [];
for (let i = 1; i <= statusCount; i++) {
  statusTokens.push((lines[i] ?? "").trim());
}
tally(statusTokens);
"""
)

_problem(
    slug="union-status-tally",
    title="Count Ticket Statuses with a Literal Union",
    concept="union and literal types",
    difficulty=3,
    minutes=20,
    summary="Model a fixed set of statuses as a union of string literals, and count how many tokens are not statuses at all.",
    statement=(
        "A status is not any string — it is one of exactly three strings. "
        "TypeScript can say that: `type Status = \"todo\" | \"doing\" | \"done\"`. "
        "A union of string literals is the difference between a typo being caught "
        "and a typo becoming a silent fourth status.\n\n"
        "Implement `tally(tokens: string[]): void`. It prints one line counting "
        "each status and everything that was not a status:\n\n"
        "`todo=<a> doing=<b> done=<c> invalid=<d>`\n\n"
        "Matching is **exact**: `Done` and `DONE` are not statuses, they are "
        "invalid. Narrow a `string` to a `Status` before you use it as one."
    ),
    input_format=(
        "Line 1: n, the number of tokens.\n"
        "Next n lines: one token per line. A token may be any text, including an "
        "empty line."
    ),
    output_format=(
        'One line, exactly: `todo=<a> doing=<b> done=<c> invalid=<d>`.'
    ),
    constraints=[
        "1 <= n <= 20000",
        "A token never contains a space",
        "Comparison is case-sensitive: only the exact strings todo, doing and "
        "done count as statuses",
    ],
    requirements=[
        "Declare Status as a union of the three string literals",
        "Count matches case-sensitively",
        "Count every non-status token as invalid",
        "Print the four counts in the order todo, doing, done, invalid",
    ],
    examples=[
        {
            "stdin": "5\ntodo\ndone\ndoing\ndone\ntodo\n",
            "explanation": "Two `todo`, one `doing` and two `done`, with nothing left over.",
        },
        {
            "stdin": "3\nDone\nDONE\nblocked\n",
            "explanation": "Matching is case-sensitive, so `Done` and `DONE` are not statuses; all three tokens are invalid.",
        },
    ],
    cases=[
        ("sample: a mixed backlog", "5\ntodo\ndone\ndoing\ndone\ntodo\n", False),
        ("sample: wrong case is invalid", "3\nDone\nDONE\nblocked\n", False),
        ("hidden: one token", "1\ndoing\n", True),
        ("hidden: all done", "4\ndone\ndone\ndone\ndone\n", True),
        ("hidden: unknown statuses mixed in", "6\ntodo\narchived\ndone\ncancelled\ndoing\ntodo\n", True),
        ("hidden: an empty line counts as invalid", "2\n\ndone\n", True),
    ],
    oracle="""import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0])
counts = {"todo": 0, "doing": 0, "done": 0}
invalid = 0
for index in range(1, n + 1):
    token = (lines[index] if index < len(lines) else "").strip()
    if token in counts:
        counts[token] += 1
    else:
        invalid += 1
print(
    f"todo={counts['todo']} doing={counts['doing']} "
    f"done={counts['done']} invalid={invalid}"
)
""",
    reference="""type Status = "todo" | "doing" | "done";

function isStatus(token: string): token is Status {
  return token === "todo" || token === "doing" || token === "done";
}

function tally(tokens: string[]): void {
  const counts: Record<Status, number> = { todo: 0, doing: 0, done: 0 };
  let invalid = 0;
  for (const token of tokens) {
    if (isStatus(token)) {
      counts[token] += 1;
    } else {
      invalid += 1;
    }
  }
  console.log(
    `todo=${counts.todo} doing=${counts.doing} done=${counts.done} invalid=${invalid}`,
  );
}

"""
    + _STATUS_PLUMBING,
    starter="""type Status = "todo" | "doing" | "done";

function tally(tokens: string[]): void {
  // TODO: count each Status exactly, and count everything else as invalid
  console.log("todo=0 doing=0 done=0 invalid=0");
}

"""
    + _STATUS_PLUMBING,
    wrong=[
        # Lowercases first, which quietly accepts the typos the union exists to reject.
        """type Status = "todo" | "doing" | "done";

function tally(tokens: string[]): void {
  const counts: Record<Status, number> = { todo: 0, doing: 0, done: 0 };
  let invalid = 0;
  for (const token of tokens) {
    const lower = token.toLowerCase();
    if (lower === "todo" || lower === "doing" || lower === "done") {
      counts[lower as Status] += 1;
    } else {
      invalid += 1;
    }
  }
  console.log(
    `todo=${counts.todo} doing=${counts.doing} done=${counts.done} invalid=${invalid}`,
  );
}

"""
        + _STATUS_PLUMBING,
        # Treats anything unrecognised as the default status.
        """type Status = "todo" | "doing" | "done";

function tally(tokens: string[]): void {
  const counts: Record<Status, number> = { todo: 0, doing: 0, done: 0 };
  for (const token of tokens) {
    if (token === "doing" || token === "done") {
      counts[token] += 1;
    } else {
      counts.todo += 1;
    }
  }
  console.log(
    `todo=${counts.todo} doing=${counts.doing} done=${counts.done} invalid=0`,
  );
}

"""
        + _STATUS_PLUMBING,
        # Counts correctly but reports the statuses in the wrong order.
        """type Status = "todo" | "doing" | "done";

function tally(tokens: string[]): void {
  const counts: Record<Status, number> = { todo: 0, doing: 0, done: 0 };
  let invalid = 0;
  for (const token of tokens) {
    if (token === "todo" || token === "doing" || token === "done") {
      counts[token] += 1;
    } else {
      invalid += 1;
    }
  }
  console.log(
    `todo=${counts.done} doing=${counts.doing} done=${counts.todo} invalid=${invalid}`,
  );
}

"""
        + _STATUS_PLUMBING,
    ],
)


# =========================================================================== #
#  4. Optional and default parameters                                         #
# =========================================================================== #

_PRICE_PLUMBING = (
    _READ_LINES
    + """const priceCount: number = Number(lines[0]);
const output: string[] = [];
for (let i = 1; i <= priceCount; i++) {
  const parts: string[] = lines[i].trim().split(/\\s+/);
  const amount: number = Number(parts[0]);
  if (parts.length === 1) {
    output.push(formatPrice(amount));
  } else if (parts.length === 2) {
    output.push(formatPrice(amount, parts[1]));
  } else {
    output.push(formatPrice(amount, parts[1], Number(parts[2])));
  }
}
console.log(output.join("\\n"));
"""
)

_problem(
    slug="optional-default-params",
    title="A Price Formatter with Defaults and an Optional",
    concept="optional and default parameters",
    difficulty=3,
    minutes=20,
    summary="Write one function that three different call sites use, with a defaulted currency and a genuinely optional precision.",
    statement=(
        "A default parameter (`currency: string = \"USD\"`) and an optional one "
        "(`decimals?: number`) look similar and behave differently. A default "
        "fills itself in; an optional is `number | undefined` and you must decide "
        "what `undefined` means.\n\n"
        "Implement `formatPrice(amount: number, currency: string = \"USD\", "
        "decimals?: number): string`. It returns the currency, a space, then the "
        "amount with `decimals` decimal places — defaulting to 2 when `decimals` "
        "was not supplied.\n\n"
        "The trap: `decimals` can legitimately be `0`, and `0` is falsy. `decimals "
        "|| 2` looks right and silently formats yen to two decimal places forever."
    ),
    input_format=(
        "Line 1: n, the number of prices.\n"
        "Next n lines: an amount on its own, or an amount and a currency code, or "
        "an amount, a currency code and a decimal-place count."
    ),
    output_format="n lines, one formatted price per input line.",
    constraints=[
        "1 <= n <= 5000",
        "0 <= decimals <= 6",
        "Every amount is exact at the requested number of decimal places, so no "
        "rounding convention can change the answer",
    ],
    requirements=[
        "Default currency to USD when the caller omits it",
        "Default to 2 decimal places when decimals is undefined",
        "Respect a decimals value of 0 rather than treating it as missing",
        "Use toFixed so trailing zeros are printed",
    ],
    examples=[
        {
            "stdin": "3\n12.5\n7 EUR\n3.125 GBP 3\n",
            "explanation": "The first line supplies neither currency nor precision, so it becomes `USD 12.50`. The second defaults only the precision. The third supplies all three.",
        },
        {
            "stdin": "2\n0\n9 JPY 0\n",
            "explanation": "`9 JPY 0` asks for zero decimal places, so the answer is `JPY 9` — a formatter that treats 0 as missing prints `JPY 9.00` instead.",
        },
    ],
    cases=[
        ("sample: all three call shapes", "3\n12.5\n7 EUR\n3.125 GBP 3\n", False),
        ("sample: zero decimal places", "2\n0\n9 JPY 0\n", False),
        ("hidden: one decimal place", "1\n1234.5 INR 1\n", True),
        ("hidden: a negative amount", "1\n-2.25\n", True),
        ("hidden: four decimal places", "1\n100 USD 4\n", True),
        ("hidden: currency without precision", "2\n0.5 CHF 1\n80 AUD\n", True),
    ],
    oracle="""import sys
from decimal import Decimal

lines = sys.stdin.read().split("\\n")
n = int(lines[0])
out = []
for index in range(1, n + 1):
    parts = lines[index].split()
    amount = Decimal(parts[0])
    currency = parts[1] if len(parts) > 1 else "USD"
    decimals = int(parts[2]) if len(parts) > 2 else 2
    out.append(f"{currency} {amount:.{decimals}f}")
print("\\n".join(out))
""",
    reference="""function formatPrice(
  amount: number,
  currency: string = "USD",
  decimals?: number,
): string {
  const places: number = decimals ?? 2;
  return `${currency} ${amount.toFixed(places)}`;
}

"""
    + _PRICE_PLUMBING,
    starter="""function formatPrice(
  amount: number,
  currency: string = "USD",
  decimals?: number,
): string {
  // TODO: return "<currency> <amount with `decimals` places, default 2>"
  return "";
}

"""
    + _PRICE_PLUMBING,
    wrong=[
        # `|| 2` throws away a legitimate 0.
        """function formatPrice(
  amount: number,
  currency: string = "USD",
  decimals?: number,
): string {
  return `${currency} ${amount.toFixed(decimals || 2)}`;
}

"""
        + _PRICE_PLUMBING,
        # Wrong default currency.
        """function formatPrice(
  amount: number,
  currency: string = "EUR",
  decimals?: number,
): string {
  return `${currency} ${amount.toFixed(decimals ?? 2)}`;
}

"""
        + _PRICE_PLUMBING,
        # Treats a missing precision as zero rather than two.
        """function formatPrice(
  amount: number,
  currency: string = "USD",
  decimals?: number,
): string {
  return `${currency} ${amount.toFixed(decimals ?? 0)}`;
}

"""
        + _PRICE_PLUMBING,
    ],
)


# =========================================================================== #
#  5. Arrays and tuples                                                       #
# =========================================================================== #

_BOUNDS_PLUMBING = (
    _READ_TOKENS
    + """const boundsCount: number = Number(tokens[0]);
const boundsValues: number[] = tokens.slice(1, 1 + boundsCount).map(Number);
const [low, high] = bounds(boundsValues);
console.log(`${low} ${high} ${high - low}`);
"""
)

_problem(
    slug="tuple-bounds",
    title="Return a Fixed-Length Pair as a Tuple",
    concept="arrays and tuples",
    difficulty=3,
    minutes=20,
    summary="An array of unknown length and a pair of exactly two numbers are different types. Return the pair.",
    statement=(
        "`number[]` is any number of numbers. `[number, number]` is exactly two, "
        "in a known order — a tuple. When a function returns a pair, saying so "
        "lets the caller destructure it and lets the compiler catch the day "
        "someone returns three values.\n\n"
        "Implement `bounds(values: number[]): [number, number]`, returning the "
        "smallest value then the largest. The provided plumbing destructures your "
        "tuple and prints `<min> <max> <max - min>`.\n\n"
        "Do not start your running minimum at `0`: an array can be entirely "
        "negative."
    ),
    input_format=(
        "Line 1: n, the count of values.\nLine 2: n space-separated integers."
    ),
    output_format=(
        "One line: the minimum, the maximum, and the difference between them, "
        "separated by single spaces."
    ),
    constraints=[
        "1 <= n <= 20000",
        "-1000000000 <= values[i] <= 1000000000",
        "The span can reach 2000000000, which is fine in a TypeScript number",
    ],
    requirements=[
        "Annotate the return type as the tuple [number, number]",
        "Return the minimum first and the maximum second",
        "Work when every value is negative",
        "Work when n is 1, where the span is 0",
    ],
    examples=[
        {
            "stdin": "5\n3 1 4 1 5\n",
            "explanation": "The smallest value is 1 and the largest is 5, so the span is 4.",
        },
        {
            "stdin": "3\n-5 -2 -9\n",
            "explanation": "Every value is negative. A minimum seeded with 0 would wrongly report 0 here.",
        },
    ],
    cases=[
        ("sample: mixed values", "5\n3 1 4 1 5\n", False),
        ("sample: all negative", "3\n-5 -2 -9\n", False),
        ("hidden: single value", "1\n42\n", True),
        ("hidden: every value identical", "4\n7 7 7 7\n", True),
        ("hidden: extremes", "2\n-1000000000 1000000000\n", True),
        ("hidden: crosses zero", "6\n0 -1 5 5 -1 0\n", True),
    ],
    oracle="""import sys

data = sys.stdin.read().split()
n = int(data[0])
values = [int(x) for x in data[1:1 + n]]
low = min(values)
high = max(values)
print(f"{low} {high} {high - low}")
""",
    reference="""function bounds(values: number[]): [number, number] {
  let low: number = values[0];
  let high: number = values[0];
  for (const value of values) {
    if (value < low) {
      low = value;
    }
    if (value > high) {
      high = value;
    }
  }
  return [low, high];
}

"""
    + _BOUNDS_PLUMBING,
    starter="""function bounds(values: number[]): [number, number] {
  // TODO: return [smallest, largest]
  return [0, 0];
}

"""
    + _BOUNDS_PLUMBING,
    wrong=[
        # Seeds the extremes at zero.
        """function bounds(values: number[]): [number, number] {
  let low = 0;
  let high = 0;
  for (const value of values) {
    if (value < low) {
      low = value;
    }
    if (value > high) {
      high = value;
    }
  }
  return [low, high];
}

"""
        + _BOUNDS_PLUMBING,
        # Right values, wrong tuple order — which is exactly what a tuple type is for.
        """function bounds(values: number[]): [number, number] {
  let low: number = values[0];
  let high: number = values[0];
  for (const value of values) {
    if (value < low) {
      low = value;
    }
    if (value > high) {
      high = value;
    }
  }
  return [high, low];
}

"""
        + _BOUNDS_PLUMBING,
        # Uses only the first and last value, as if the input were sorted.
        """function bounds(values: number[]): [number, number] {
  return [values[0], values[values.length - 1]];
}

"""
        + _BOUNDS_PLUMBING,
    ],
)


# =========================================================================== #
#  6. Generics                                                                #
# =========================================================================== #

_DEDUPE_PLUMBING = (
    _READ_LINES
    + """const dedupeCount: number = Number(lines[0]);
const items: string[] = (lines[1] ?? "")
  .split(/\\s+/)
  .filter((token: string) => token.length > 0)
  .slice(0, dedupeCount);
const unique: string[] = dedupe(items);
console.log(unique.length > 0 ? unique.join(" ") : "empty");
"""
)

_problem(
    slug="generic-dedupe",
    title="Write dedupe Once, for Any Element Type",
    concept="generics",
    difficulty=4,
    minutes=25,
    summary="A generic type parameter lets one function serve every element type without falling back to any.",
    statement=(
        "You could write `dedupe(items: string[]): string[]`, and then write it "
        "again for numbers, and again for orders. Or you could write it once with a "
        "type parameter: `dedupe<T>(items: T[]): T[]`. The caller's element type "
        "flows through and comes back out, which `any[]` would throw away.\n\n"
        "Implement `dedupe<T>(items: T[]): T[]`, keeping the **first** occurrence "
        "of each distinct item and preserving input order. Do not sort, and do not "
        "only remove neighbouring duplicates.\n\n"
        "The plumbing prints your result space-separated, or `empty` when there is "
        "nothing left."
    ),
    input_format=(
        "Line 1: n, the number of items.\n"
        "Line 2: n space-separated tokens (this line is empty when n is 0)."
    ),
    output_format=(
        "One line: the deduplicated tokens in their original order, separated by "
        "single spaces, or `empty` if there are none."
    ),
    constraints=[
        "0 <= n <= 20000",
        "A token is a non-empty string without spaces",
    ],
    requirements=[
        "Declare a type parameter T rather than using any",
        "Keep the first occurrence of each distinct item",
        "Preserve the original order",
        "Remove duplicates that are not adjacent",
    ],
    examples=[
        {
            "stdin": "6\nb a b c a a\n",
            "explanation": "First occurrences, in order, are `b`, `a` and `c`. Sorting would print `a b c` and adjacent-only removal would print `b a b c a`.",
        },
        {
            "stdin": "3\na b a\n",
            "explanation": "The repeat of `a` is not adjacent to the first one, so an adjacent-only filter would wrongly keep it.",
        },
    ],
    cases=[
        ("sample: repeats out of order", "6\nb a b c a a\n", False),
        ("sample: non-adjacent repeat", "3\na b a\n", False),
        ("hidden: every item identical", "4\nx x x x\n", True),
        ("hidden: no items at all", "0\n\n", True),
        ("hidden: already unique, reverse alphabetical", "5\ne d c b a\n", True),
        ("hidden: interleaved repeats", "7\nq w q e q w r\n", True),
    ],
    oracle="""import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0])
items = (lines[1] if len(lines) > 1 else "").split()[:n]
seen = set()
unique = []
for item in items:
    if item not in seen:
        seen.add(item)
        unique.append(item)
print(" ".join(unique) if unique else "empty")
""",
    reference="""function dedupe<T>(items: T[]): T[] {
  const seen = new Set<T>();
  const unique: T[] = [];
  for (const item of items) {
    if (!seen.has(item)) {
      seen.add(item);
      unique.push(item);
    }
  }
  return unique;
}

"""
    + _DEDUPE_PLUMBING,
    starter="""function dedupe<T>(items: T[]): T[] {
  // TODO: return the items with later duplicates removed, order preserved
  return items;
}

"""
    + _DEDUPE_PLUMBING,
    wrong=[
        # Deduplicates, then destroys the ordering the question asked for.
        """function dedupe<T>(items: T[]): T[] {
  const unique: T[] = Array.from(new Set<T>(items));
  unique.sort();
  return unique;
}

"""
        + _DEDUPE_PLUMBING,
        # Only collapses runs of neighbours.
        """function dedupe<T>(items: T[]): T[] {
  const unique: T[] = [];
  for (let i = 0; i < items.length; i++) {
    if (i === 0 || items[i] !== items[i - 1]) {
      unique.push(items[i]);
    }
  }
  return unique;
}

"""
        + _DEDUPE_PLUMBING,
        # Keeps the last occurrence instead of the first.
        """function dedupe<T>(items: T[]): T[] {
  return items.filter((item: T, index: number) => items.lastIndexOf(item) === index);
}

"""
        + _DEDUPE_PLUMBING,
    ],
)


# =========================================================================== #
#  7. unknown vs any                                                          #
# =========================================================================== #

_UNKNOWN_PLUMBING = (
    _READ_LINES
    + """const unknownCount: number = Number(lines[0]);
const parsed: unknown[] = [];
for (let i = 1; i <= unknownCount; i++) {
  const token: string = (lines[i] ?? "").trim();
  parsed.push(/^-?\\d+$/.test(token) ? Number(token) : token);
}
classify(parsed);
"""
)

_problem(
    slug="unknown-narrowing",
    title="Narrow unknown Before You Use It",
    concept="unknown vs any",
    difficulty=4,
    minutes=25,
    summary="`any` lets you add a string to a number. `unknown` makes you check first — and the check is the answer.",
    statement=(
        "`any` and `unknown` both mean \"I don't know what this is\". The "
        "difference is what the compiler lets you do next: with `any`, anything, "
        "including adding a string to a running total; with `unknown`, nothing "
        "until you have narrowed it.\n\n"
        "You are given `unknown[]`, where each element is either a `number` (the "
        "line parsed as an integer) or a `string` (it did not). Implement "
        "`classify(values: unknown[]): void` so it prints:\n\n"
        "`numeric=<sum of the numbers> text=<total character count of the strings>`\n\n"
        "Reaching `.length` on an `unknown` is a compile error, and the judge "
        "type-checks. Narrow with `typeof` and the sum is honest by construction."
    ),
    input_format=(
        "Line 1: n, the number of tokens.\n"
        "Next n lines: one token per line, which may be an integer, arbitrary "
        "text, or empty."
    ),
    output_format="One line, exactly: `numeric=<sum> text=<characters>`.",
    constraints=[
        "1 <= n <= 20000",
        "A numeric token is a plain decimal integer, optionally signed",
        "Anything else — including `NaN`, `12abc` and an empty line — is text",
        "The sum of the numeric tokens fits comfortably in a TypeScript number",
    ],
    requirements=[
        "Narrow each unknown with typeof before using it",
        "Add numbers to the numeric total",
        "Add each string's character count (not 1 per string) to the text total",
        "Do not fall back to any",
    ],
    examples=[
        {
            "stdin": "4\n12\nabc\n-5\nNaN\n",
            "explanation": "`12` and `-5` parse as integers and sum to 7. `abc` and `NaN` do not, so they are text worth three characters each, six in total.",
        },
        {
            "stdin": "3\nhello\nworld\n!\n",
            "explanation": "Nothing parses as an integer, so the numeric total is 0 and the text total is 5 + 5 + 1 = 11 characters.",
        },
    ],
    cases=[
        ("sample: numbers and words", "4\n12\nabc\n-5\nNaN\n", False),
        ("sample: text only", "3\nhello\nworld\n!\n", False),
        ("hidden: numbers only", "3\n1\n2\n3\n", True),
        ("hidden: zero and a single character", "2\n0\nx\n", True),
        ("hidden: a token that only starts numeric", "5\n100\n12abc\n7\n\nzz\n", True),
        ("hidden: one large number", "1\n999999999\n", True),
    ],
    oracle="""import re
import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0])
numeric = 0
characters = 0
for index in range(1, n + 1):
    token = (lines[index] if index < len(lines) else "").strip()
    if re.fullmatch(r"-?\\d+", token):
        numeric += int(token)
    else:
        characters += len(token)
print(f"numeric={numeric} text={characters}")
""",
    reference="""function classify(values: unknown[]): void {
  let numeric = 0;
  let text = 0;
  for (const value of values) {
    if (typeof value === "number") {
      numeric += value;
    } else if (typeof value === "string") {
      text += value.length;
    }
  }
  console.log(`numeric=${numeric} text=${text}`);
}

"""
    + _UNKNOWN_PLUMBING,
    starter="""function classify(values: unknown[]): void {
  // TODO: narrow each value with typeof, then total the numbers and the characters
  console.log("numeric=0 text=0");
}

"""
    + _UNKNOWN_PLUMBING,
    wrong=[
        # Escapes to `any`, so `+=` silently concatenates instead of adding.
        """function classify(values: unknown[]): void {
  let numeric: any = 0;
  let text = 0;
  for (const value of values) {
    const loose: any = value;
    if (typeof loose === "number") {
      numeric += loose;
    } else {
      numeric += loose;
      text += 1;
    }
  }
  console.log(`numeric=${numeric} text=${text}`);
}

"""
        + _UNKNOWN_PLUMBING,
        # Counts text items rather than characters.
        """function classify(values: unknown[]): void {
  let numeric = 0;
  let text = 0;
  for (const value of values) {
    if (typeof value === "number") {
      numeric += value;
    } else {
      text += 1;
    }
  }
  console.log(`numeric=${numeric} text=${text}`);
}

"""
        + _UNKNOWN_PLUMBING,
        # Coerces everything to a number, so text disappears entirely.
        """function classify(values: unknown[]): void {
  let numeric = 0;
  for (const value of values) {
    numeric += Number(value) || 0;
  }
  console.log(`numeric=${numeric} text=0`);
}

"""
        + _UNKNOWN_PLUMBING,
    ],
)


# =========================================================================== #
#  8. Enums                                                                   #
# =========================================================================== #

_WEEKDAY_PLUMBING = (
    _READ_LINES
    + """const dayCount: number = Number(lines[0]);
const described: string[] = [];
for (let i = 1; i <= dayCount; i++) {
  described.push(describe(Number(lines[i].trim()) as Weekday));
}
console.log(described.join("\\n"));
"""
)

_problem(
    slug="enum-weekday",
    title="Name the Day with an Enum",
    concept="enums",
    difficulty=3,
    minutes=20,
    summary="An enum turns a magic number on the wire into a name in your code.",
    statement=(
        "Schedulers send days as integers. `5` means nothing on its own; "
        "`Weekday.Saturday` means something. An `enum` gives those integers names "
        "and gives you one place to look when the convention is wrong.\n\n"
        "`Weekday` is declared for you with Monday as 0 through Sunday as 6. "
        "Implement `describe(day: Weekday): string`, returning the day's name, a "
        "space, then `weekend` for Saturday and Sunday or `weekday` for the rest."
    ),
    input_format=(
        "Line 1: n, the number of days.\nNext n lines: one integer from 0 to 6."
    ),
    output_format=(
        "n lines, each `<Name> weekday` or `<Name> weekend`. Names are "
        "capitalised as in the enum: Monday, Tuesday, Wednesday, Thursday, "
        "Friday, Saturday, Sunday."
    ),
    constraints=[
        "1 <= n <= 20000",
        "Monday is 0 and Sunday is 6",
        "Saturday and Sunday are the weekend",
    ],
    requirements=[
        "Type the parameter as Weekday, not number",
        "Return the capitalised day name",
        "Classify both Saturday and Sunday as weekend",
        "Classify Monday through Friday as weekday",
    ],
    examples=[
        {
            "stdin": "3\n0\n5\n6\n",
            "explanation": "0 is Monday (a weekday), 5 is Saturday and 6 is Sunday (both weekend).",
        },
        {
            "stdin": "2\n3\n4\n",
            "explanation": "3 is Thursday and 4 is Friday. Friday is still a weekday.",
        },
    ],
    cases=[
        ("sample: a weekday and both weekend days", "3\n0\n5\n6\n", False),
        ("sample: late in the week", "2\n3\n4\n", False),
        ("hidden: Sunday alone", "1\n6\n", True),
        ("hidden: the whole week in order", "7\n0\n1\n2\n3\n4\n5\n6\n", True),
        ("hidden: Saturday twice", "2\n5\n5\n", True),
        ("hidden: Monday alone", "1\n0\n", True),
    ],
    oracle="""import sys

NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

lines = sys.stdin.read().split("\\n")
n = int(lines[0])
out = []
for index in range(1, n + 1):
    day = int(lines[index].strip())
    kind = "weekend" if day >= 5 else "weekday"
    out.append(f"{NAMES[day]} {kind}")
print("\\n".join(out))
""",
    reference="""enum Weekday {
  Monday = 0,
  Tuesday = 1,
  Wednesday = 2,
  Thursday = 3,
  Friday = 4,
  Saturday = 5,
  Sunday = 6,
}

function describe(day: Weekday): string {
  const isWeekend: boolean = day === Weekday.Saturday || day === Weekday.Sunday;
  return `${Weekday[day]} ${isWeekend ? "weekend" : "weekday"}`;
}

"""
    + _WEEKDAY_PLUMBING,
    starter="""enum Weekday {
  Monday = 0,
  Tuesday = 1,
  Wednesday = 2,
  Thursday = 3,
  Friday = 4,
  Saturday = 5,
  Sunday = 6,
}

function describe(day: Weekday): string {
  // TODO: return "<Name> weekend" for Saturday and Sunday, "<Name> weekday" otherwise
  return "";
}

"""
    + _WEEKDAY_PLUMBING,
    wrong=[
        # Only Sunday counts as the weekend.
        """enum Weekday {
  Monday = 0,
  Tuesday = 1,
  Wednesday = 2,
  Thursday = 3,
  Friday = 4,
  Saturday = 5,
  Sunday = 6,
}

function describe(day: Weekday): string {
  const isWeekend: boolean = day === Weekday.Sunday;
  return `${Weekday[day]} ${isWeekend ? "weekend" : "weekday"}`;
}

"""
        + _WEEKDAY_PLUMBING,
        # Assumes the week starts on Sunday, so every name is shifted.
        """enum Weekday {
  Monday = 0,
  Tuesday = 1,
  Wednesday = 2,
  Thursday = 3,
  Friday = 4,
  Saturday = 5,
  Sunday = 6,
}

const SHIFTED: string[] = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
];

function describe(day: Weekday): string {
  const isWeekend: boolean = day === Weekday.Saturday || day === Weekday.Sunday;
  return `${SHIFTED[day]} ${isWeekend ? "weekend" : "weekday"}`;
}

"""
        + _WEEKDAY_PLUMBING,
        # Prints the enum's numeric value instead of its name.
        """enum Weekday {
  Monday = 0,
  Tuesday = 1,
  Wednesday = 2,
  Thursday = 3,
  Friday = 4,
  Saturday = 5,
  Sunday = 6,
}

function describe(day: Weekday): string {
  const isWeekend: boolean = day === Weekday.Saturday || day === Weekday.Sunday;
  return `${day} ${isWeekend ? "weekend" : "weekday"}`;
}

"""
        + _WEEKDAY_PLUMBING,
    ],
)


# =========================================================================== #
#  9. Typed object manipulation                                               #
# =========================================================================== #

_TALLY_PLUMBING = (
    _READ_LINES
    + """const rowCount: number = Number(lines[0]);
const rows: ScoreRow[] = [];
for (let i = 1; i <= rowCount; i++) {
  const parts: string[] = lines[i].trim().split(/\\s+/);
  rows.push({ team: parts[0], points: Number(parts[1]) });
}
for (const line of standings(rows)) {
  console.log(line);
}
"""
)

_problem(
    slug="record-standings",
    title="Build a League Table with Record<string, number>",
    concept="typed object manipulation",
    difficulty=4,
    minutes=25,
    summary="Accumulate scores into a typed lookup, then sort into a stable, fully specified order.",
    statement=(
        "`Record<string, number>` is how you say \"an object used as a lookup from "
        "team name to points\" — more precise than `object` and more honest than "
        "`any`.\n\n"
        "Implement `standings(rows: ScoreRow[]): string[]`. Each row awards points "
        "to a team, and a team may appear on several rows, so points **accumulate**. "
        "Return one string per team, `\"<team> <total>\"`, sorted by total points "
        "descending; teams on equal points are ordered by name ascending.\n\n"
        "The tie-break is not a detail. `Array.prototype.sort` is stable, so "
        "leaving it out silently returns insertion order and passes any test that "
        "never has a tie."
    ),
    input_format=(
        "Line 1: n, the number of score rows.\n"
        "Next n lines: a team name (no spaces) and an integer point award."
    ),
    output_format=(
        "One line per distinct team: the team name, a space, then its total "
        "points. Ordered by points descending, then by name ascending."
    ),
    constraints=[
        "1 <= n <= 20000",
        "-1000000 <= points <= 1000000",
        "A team name is a non-empty string of lowercase letters",
    ],
    requirements=[
        "Accumulate repeated rows for the same team rather than overwriting",
        "Sort by total points descending",
        "Break ties by team name ascending",
        "Return one formatted string per distinct team",
    ],
    examples=[
        {
            "stdin": "3\nred 5\nblue 7\nred 2\n",
            "explanation": "`red` accumulates to 7, tying with `blue`, so the tie-break puts `blue` first alphabetically.",
        },
        {
            "stdin": "3\nteal 1\nteal 2\nteal 3\n",
            "explanation": "One team on three rows totals 6 — overwriting instead of accumulating would report 3.",
        },
    ],
    cases=[
        ("sample: a tie on points", "3\nred 5\nblue 7\nred 2\n", False),
        ("sample: repeated rows accumulate", "3\nteal 1\nteal 2\nteal 3\n", False),
        ("hidden: one team, zero points", "1\nsolo 0\n", True),
        ("hidden: negative totals", "2\nxray -5\nyank -1\n", True),
        ("hidden: four-way tie", "4\ndelta 1\ncharlie 1\nbravo 1\nalpha 1\n", True),
        ("hidden: clear ordering", "3\nlow 1\nhigh 9\nmid 5\n", True),
    ],
    oracle="""import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0])
totals: dict[str, int] = {}
for index in range(1, n + 1):
    team, points = lines[index].split()
    totals[team] = totals.get(team, 0) + int(points)
for team, total in sorted(totals.items(), key=lambda item: (-item[1], item[0])):
    print(f"{team} {total}")
""",
    reference="""interface ScoreRow {
  team: string;
  points: number;
}

function standings(rows: ScoreRow[]): string[] {
  const totals: Record<string, number> = {};
  for (const row of rows) {
    totals[row.team] = (totals[row.team] ?? 0) + row.points;
  }
  const entries: [string, number][] = Object.entries(totals);
  entries.sort((left: [string, number], right: [string, number]) => {
    if (right[1] !== left[1]) {
      return right[1] - left[1];
    }
    return left[0] < right[0] ? -1 : left[0] > right[0] ? 1 : 0;
  });
  return entries.map((entry: [string, number]) => `${entry[0]} ${entry[1]}`);
}

"""
    + _TALLY_PLUMBING,
    starter="""interface ScoreRow {
  team: string;
  points: number;
}

function standings(rows: ScoreRow[]): string[] {
  // TODO: accumulate points per team, then sort by points desc, name asc
  return [];
}

"""
    + _TALLY_PLUMBING,
    wrong=[
        # Overwrites instead of accumulating.
        """interface ScoreRow {
  team: string;
  points: number;
}

function standings(rows: ScoreRow[]): string[] {
  const totals: Record<string, number> = {};
  for (const row of rows) {
    totals[row.team] = row.points;
  }
  const entries: [string, number][] = Object.entries(totals);
  entries.sort((left: [string, number], right: [string, number]) => {
    if (right[1] !== left[1]) {
      return right[1] - left[1];
    }
    return left[0] < right[0] ? -1 : left[0] > right[0] ? 1 : 0;
  });
  return entries.map((entry: [string, number]) => `${entry[0]} ${entry[1]}`);
}

"""
        + _TALLY_PLUMBING,
        # No tie-break, so ties fall back to insertion order.
        """interface ScoreRow {
  team: string;
  points: number;
}

function standings(rows: ScoreRow[]): string[] {
  const totals: Record<string, number> = {};
  for (const row of rows) {
    totals[row.team] = (totals[row.team] ?? 0) + row.points;
  }
  const entries: [string, number][] = Object.entries(totals);
  entries.sort(
    (left: [string, number], right: [string, number]) => right[1] - left[1],
  );
  return entries.map((entry: [string, number]) => `${entry[0]} ${entry[1]}`);
}

"""
        + _TALLY_PLUMBING,
        # Sorts the wrong way round.
        """interface ScoreRow {
  team: string;
  points: number;
}

function standings(rows: ScoreRow[]): string[] {
  const totals: Record<string, number> = {};
  for (const row of rows) {
    totals[row.team] = (totals[row.team] ?? 0) + row.points;
  }
  const entries: [string, number][] = Object.entries(totals);
  entries.sort((left: [string, number], right: [string, number]) => {
    if (left[1] !== right[1]) {
      return left[1] - right[1];
    }
    return left[0] < right[0] ? -1 : left[0] > right[0] ? 1 : 0;
  });
  return entries.map((entry: [string, number]) => `${entry[0]} ${entry[1]}`);
}

"""
        + _TALLY_PLUMBING,
    ],
)


# =========================================================================== #
#  10. Discriminated unions                                                   #
# =========================================================================== #

_SHAPE_PLUMBING = (
    _READ_LINES
    + """const shapeCount: number = Number(lines[0]);
const shapes: Shape[] = [];
for (let i = 1; i <= shapeCount; i++) {
  const parts: string[] = lines[i].trim().split(/\\s+/);
  if (parts[0] === "rect") {
    shapes.push({ kind: "rect", width: Number(parts[1]), height: Number(parts[2]) });
  } else if (parts[0] === "square") {
    shapes.push({ kind: "square", side: Number(parts[1]) });
  } else {
    shapes.push({ kind: "triangle", base: Number(parts[1]), height: Number(parts[2]) });
  }
}
let totalArea = 0;
for (const shape of shapes) {
  totalArea += area(shape);
}
console.log(totalArea.toFixed(1));
"""
)

_problem(
    slug="discriminated-shapes",
    title="Total the Area of a Discriminated Union",
    concept="discriminated unions",
    difficulty=5,
    minutes=25,
    summary="A shared literal `kind` field turns a union into something the compiler can take apart for you.",
    statement=(
        "A `Shape` is a rectangle, a square or a right triangle, and each carries "
        "different measurements. Give every member a literal `kind` field and the "
        "union becomes *discriminated*: inside `case \"square\":` the compiler "
        "already knows `shape.side` exists and `shape.width` does not.\n\n"
        "The `Shape` type is declared for you. Implement `area(shape: Shape): "
        "number`:\n\n"
        "* `rect` — `width * height`\n"
        "* `square` — `side * side`\n"
        "* `triangle` — a right triangle, so `base * height / 2`\n\n"
        "The plumbing totals your areas and prints the total with exactly one "
        "decimal place."
    ),
    input_format=(
        "Line 1: n, the number of shapes.\n"
        "Next n lines: `rect <width> <height>`, `square <side>`, or "
        "`triangle <base> <height>`."
    ),
    output_format=(
        "One line: the total area with exactly one decimal place. Every total in "
        "the test data is an exact multiple of 0.5."
    ),
    constraints=[
        "1 <= n <= 20000",
        "0 <= every measurement <= 100000",
        "A triangle's base times its height is always even, so the total is an "
        "exact multiple of 0.5 and no rounding convention can change the answer",
    ],
    requirements=[
        "Switch on the kind field rather than checking which properties exist",
        "Halve the triangle's base times height",
        "Compute a square's area as side squared, not four times the side",
        "Print the total with exactly one decimal place",
    ],
    examples=[
        {
            "stdin": "3\nrect 2 3\nsquare 3\ntriangle 3 5\n",
            "explanation": "6 for the rectangle, 9 for the square and 7.5 for the triangle, totalling 22.5.",
        },
        {
            "stdin": "1\nsquare 10\n",
            "explanation": "A single square of side 10 has area 100, printed as `100.0` because one decimal place is always shown.",
        },
    ],
    cases=[
        ("sample: one of each shape", "3\nrect 2 3\nsquare 3\ntriangle 3 5\n", False),
        ("sample: a square alone", "1\nsquare 10\n", False),
        ("hidden: smallest triangle", "1\ntriangle 1 1\n", True),
        ("hidden: large rectangle", "2\nrect 1000 1000\ntriangle 2 2\n", True),
        ("hidden: two odd triangles sum to a whole", "4\ntriangle 3 3\ntriangle 3 3\nsquare 1\nrect 1 1\n", True),
        ("hidden: a degenerate rectangle", "1\nrect 0 5\n", True),
    ],
    oracle="""import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0])
total = 0.0
for index in range(1, n + 1):
    parts = lines[index].split()
    if parts[0] == "rect":
        total += int(parts[1]) * int(parts[2])
    elif parts[0] == "square":
        total += int(parts[1]) ** 2
    else:
        total += int(parts[1]) * int(parts[2]) / 2
print(f"{total:.1f}")
""",
    reference="""type Shape =
  | { kind: "rect"; width: number; height: number }
  | { kind: "square"; side: number }
  | { kind: "triangle"; base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "rect":
      return shape.width * shape.height;
    case "square":
      return shape.side * shape.side;
    case "triangle":
      return (shape.base * shape.height) / 2;
  }
}

"""
    + _SHAPE_PLUMBING,
    starter="""type Shape =
  | { kind: "rect"; width: number; height: number }
  | { kind: "square"; side: number }
  | { kind: "triangle"; base: number; height: number };

function area(shape: Shape): number {
  // TODO: switch on shape.kind and return the area of each shape
  return 0;
}

"""
    + _SHAPE_PLUMBING,
    wrong=[
        # Forgets that a triangle is half its bounding rectangle.
        """type Shape =
  | { kind: "rect"; width: number; height: number }
  | { kind: "square"; side: number }
  | { kind: "triangle"; base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "rect":
      return shape.width * shape.height;
    case "square":
      return shape.side * shape.side;
    case "triangle":
      return shape.base * shape.height;
  }
}

"""
        + _SHAPE_PLUMBING,
        # Confuses a square's area with its perimeter.
        """type Shape =
  | { kind: "rect"; width: number; height: number }
  | { kind: "square"; side: number }
  | { kind: "triangle"; base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "rect":
      return shape.width * shape.height;
    case "square":
      return 4 * shape.side;
    case "triangle":
      return (shape.base * shape.height) / 2;
  }
}

"""
        + _SHAPE_PLUMBING,
        # Truncates each area to an integer before totalling.
        """type Shape =
  | { kind: "rect"; width: number; height: number }
  | { kind: "square"; side: number }
  | { kind: "triangle"; base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "rect":
      return shape.width * shape.height;
    case "square":
      return shape.side * shape.side;
    case "triangle":
      return Math.floor((shape.base * shape.height) / 2);
  }
}

"""
        + _SHAPE_PLUMBING,
    ],
)


# =========================================================================== #
#  11. User-defined type guards                                               #
# =========================================================================== #

_GUARD_PLUMBING = (
    _READ_LINES
    + """const recordCount: number = Number(lines[0]);
const candidates: Candidate[] = [];
for (let i = 1; i <= recordCount; i++) {
  const parts: string[] = lines[i].trim().split(/\\s+/);
  const ageToken: string = parts.length > 1 ? parts[1] : "-";
  candidates.push({
    name: parts[0] ?? "",
    age: /^-?\\d+$/.test(ageToken) ? Number(ageToken) : ageToken,
  });
}

const users: User[] = candidates.filter(isUser);
if (users.length === 0) {
  console.log("valid=0 avgAge=none");
} else {
  let totalAge = 0;
  for (const user of users) {
    totalAge += user.age;
  }
  console.log(`valid=${users.length} avgAge=${Math.floor(totalAge / users.length)}`);
}
"""
)

_problem(
    slug="type-guard-users",
    title="A Type Guard That Makes filter Return User[]",
    concept="type guards",
    difficulty=5,
    minutes=30,
    summary="A `value is User` predicate is the one place you are allowed to teach the compiler something it cannot work out.",
    statement=(
        "A boolean-returning validator tells you a record is fine. A *type "
        "predicate* — `function isUser(value: Candidate): value is User` — tells "
        "the compiler too, which is why `candidates.filter(isUser)` comes back as "
        "`User[]` instead of `Candidate[]`.\n\n"
        "A `Candidate` has a `name: string` and an `age: unknown` (the raw token, "
        "parsed to a number only when it looked like an integer). Implement "
        "`isUser` so a candidate qualifies when:\n\n"
        "* its `name` is neither empty nor the placeholder `-`, and\n"
        "* its `age` is a number that is a non-negative integer.\n\n"
        "The plumbing then prints `valid=<count> avgAge=<mean>`, where the mean is "
        "the total age of the valid users divided by how many there are, rounded "
        "**down**. With no valid users it prints `valid=0 avgAge=none`."
    ),
    input_format=(
        "Line 1: n, the number of records.\n"
        "Next n lines: a name and an age token, separated by a space. A `-` in "
        "either position means the field is missing, and the age token may be "
        "any text."
    ),
    output_format=(
        "One line: `valid=<count> avgAge=<floored mean>`, or "
        "`valid=0 avgAge=none` when no record qualifies."
    ),
    constraints=[
        "1 <= n <= 20000",
        "A name never contains a space",
        "An age token is arbitrary text; only a plain decimal integer of zero or "
        "more qualifies",
    ],
    requirements=[
        "Write isUser as a type predicate returning `value is User`",
        "Reject a missing or placeholder name",
        "Reject a non-numeric age and a negative age",
        "Reject an age that is not a whole number, such as 3.5",
        "Accept an age of exactly 0",
        "Divide by the number of valid users and round down",
    ],
    examples=[
        {
            "stdin": "4\nada 36\nbob -1\ncy x\ndee -\n",
            "explanation": "Only `ada` qualifies: `bob`'s age is negative, `cy`'s is not a number and `dee`'s is missing. One valid user of age 36.",
        },
        {
            "stdin": "4\np 1\nq 2\nr 3\ns 4\n",
            "explanation": "Four valid users totalling 10, and 10 / 4 is 2.5 — rounded down to 2. Rounding to nearest would wrongly say 3.",
        },
    ],
    cases=[
        ("sample: three ways to be invalid", "4\nada 36\nbob -1\ncy x\ndee -\n", False),
        ("sample: the mean rounds down", "4\np 1\nq 2\nr 3\ns 4\n", False),
        ("hidden: nothing qualifies", "2\n- 5\nx -\n", True),
        ("hidden: an age of zero is valid", "1\nsolo 0\n", True),
        ("hidden: a non-integer mean", "3\na 10\nb 21\nc 30\n", True),
        ("hidden: negatives filtered out", "3\nm 100\nn -5\no 50\n", True),
        # A guard written as `Number(value.age) >= 0` agrees with the correct one
        # on every token above, because a word coerces to NaN and NaN fails the
        # comparison. A fractional age is the token that separates them.
        ("hidden: a fractional age is not a whole number", "3\nada 36\neve 3.5\nfay 4\n", True),
    ],
    oracle="""import math
import re
import sys

lines = sys.stdin.read().split("\\n")
n = int(lines[0])
ages = []
for index in range(1, n + 1):
    parts = lines[index].split()
    name = parts[0] if parts else ""
    age_token = parts[1] if len(parts) > 1 else "-"
    if name in ("", "-"):
        continue
    if not re.fullmatch(r"-?\\d+", age_token):
        continue
    age = int(age_token)
    if age < 0:
        continue
    ages.append(age)
if not ages:
    print("valid=0 avgAge=none")
else:
    print(f"valid={len(ages)} avgAge={math.floor(sum(ages) / len(ages))}")
""",
    reference="""interface Candidate {
  name: string;
  age: unknown;
}

interface User {
  name: string;
  age: number;
}

function isUser(value: Candidate): value is User {
  if (value.name === "" || value.name === "-") {
    return false;
  }
  return (
    typeof value.age === "number" &&
    Number.isInteger(value.age) &&
    value.age >= 0
  );
}

"""
    + _GUARD_PLUMBING,
    starter="""interface Candidate {
  name: string;
  age: unknown;
}

interface User {
  name: string;
  age: number;
}

function isUser(value: Candidate): value is User {
  // TODO: accept only a real name plus a non-negative integer age
  return typeof value.age === "number";
}

"""
    + _GUARD_PLUMBING,
    wrong=[
        # Accepts negative ages.
        """interface Candidate {
  name: string;
  age: unknown;
}

interface User {
  name: string;
  age: number;
}

function isUser(value: Candidate): value is User {
  if (value.name === "" || value.name === "-") {
    return false;
  }
  return typeof value.age === "number" && Number.isInteger(value.age);
}

"""
        + _GUARD_PLUMBING,
        # Accepts a placeholder name.
        """interface Candidate {
  name: string;
  age: unknown;
}

interface User {
  name: string;
  age: number;
}

function isUser(value: Candidate): value is User {
  return (
    typeof value.age === "number" &&
    Number.isInteger(value.age) &&
    value.age >= 0
  );
}

"""
        + _GUARD_PLUMBING,
        # Accepts any age token by coercing it, so text becomes NaN-free nonsense.
        """interface Candidate {
  name: string;
  age: unknown;
}

interface User {
  name: string;
  age: number;
}

function isUser(value: Candidate): value is User {
  if (value.name === "" || value.name === "-") {
    return false;
  }
  return Number(value.age) >= 0;
}

"""
        + _GUARD_PLUMBING,
    ],
)


# =========================================================================== #
#  12. keyof and indexed access                                               #
# =========================================================================== #

_PLUCK_PLUMBING = (
    _READ_LINES
    + """function isField(token: string): token is keyof Person {
  return token === "name" || token === "city" || token === "role";
}

const field: string = lines[0].trim();
const personCount: number = Number(lines[1]);
const people: Person[] = [];
for (let i = 2; i < 2 + personCount; i++) {
  const parts: string[] = lines[i].trim().split(/\\s+/);
  people.push({ name: parts[0], city: parts[1], role: parts[2] });
}

if (!isField(field)) {
  console.log("unknown field");
} else {
  console.log(pluck(people, field).join(", "));
}
"""
)

_problem(
    slug="keyof-pluck",
    title="Pluck a Column with keyof and Indexed Access",
    concept="keyof and indexed access types",
    difficulty=5,
    minutes=30,
    summary="`K extends keyof Person` and `Person[K]` let one function read any field and still return the right type.",
    statement=(
        "A function that reads \"some field\" off an object is where types usually "
        "collapse into `any`. They do not have to. Constrain the field to "
        "`K extends keyof Person` and give the return type as `Person[K][]`: the "
        "compiler then rejects `pluck(people, \"salary\")` at the call site, and "
        "the result is typed by whichever field you asked for.\n\n"
        "Implement `pluck<K extends keyof Person>(people: Person[], field: K): "
        "Person[K][]`, returning that field's value from every person in input "
        "order. Keep duplicates and do not sort.\n\n"
        "The plumbing prints your values joined by a comma and a space."
    ),
    input_format=(
        "Line 1: the field to read — `name`, `city` or `role`.\n"
        "Line 2: n, the number of people.\n"
        "Next n lines: a name, a city and a role, separated by spaces."
    ),
    output_format=(
        "One line: the chosen field's values in input order, joined by a comma "
        "and a space."
    ),
    constraints=[
        "1 <= n <= 20000",
        "The field on line 1 is always name, city or role",
        "Every value is a non-empty string without spaces",
    ],
    requirements=[
        "Constrain the field parameter with K extends keyof Person",
        "Return Person[K][] rather than string[] or any[]",
        "Preserve input order",
        "Keep duplicate values",
    ],
    examples=[
        {
            "stdin": "city\n3\nada london engineer\nbob berlin designer\ncy cairo analyst\n",
            "explanation": "The `city` field is read from each person in order, giving `london, berlin, cairo`.",
        },
        {
            "stdin": "city\n2\nada lisbon engineer\nbob lisbon designer\n",
            "explanation": "Both people share a city. The answer keeps the duplicate — this is a column, not a set.",
        },
    ],
    cases=[
        ("sample: read the city column", "city\n3\nada london engineer\nbob berlin designer\ncy cairo analyst\n", False),
        ("sample: duplicates are kept", "city\n2\nada lisbon engineer\nbob lisbon designer\n", False),
        ("hidden: read the role column", "role\n1\nsolo tokyo founder\n", True),
        ("hidden: names stay in input order", "name\n4\nzoe oslo lead\nyan riga intern\nxu kiev intern\nwren bonn lead\n", True),
        ("hidden: two people, one field", "name\n2\nada paris engineer\nbob paris designer\n", True),
        ("hidden: repeated roles", "role\n3\na x intern\nb y lead\nc z intern\n", True),
    ],
    oracle="""import sys

lines = sys.stdin.read().split("\\n")
field = lines[0].strip()
n = int(lines[1])
index_of = {"name": 0, "city": 1, "role": 2}
values = []
for index in range(2, 2 + n):
    parts = lines[index].split()
    values.append(parts[index_of[field]])
print(", ".join(values))
""",
    reference="""interface Person {
  name: string;
  city: string;
  role: string;
}

function pluck<K extends keyof Person>(people: Person[], field: K): Person[K][] {
  return people.map((person: Person) => person[field]);
}

"""
    + _PLUCK_PLUMBING,
    starter="""interface Person {
  name: string;
  city: string;
  role: string;
}

function pluck<K extends keyof Person>(people: Person[], field: K): Person[K][] {
  // TODO: return the chosen field's value for every person, in input order
  return [];
}

"""
    + _PLUCK_PLUMBING,
    wrong=[
        # Ignores the field and always reads the name.
        """interface Person {
  name: string;
  city: string;
  role: string;
}

function pluck<K extends keyof Person>(people: Person[], field: K): Person[K][] {
  return people.map((person: Person) => person.name) as Person[K][];
}

"""
        + _PLUCK_PLUMBING,
        # Deduplicates a column that was asked for verbatim.
        """interface Person {
  name: string;
  city: string;
  role: string;
}

function pluck<K extends keyof Person>(people: Person[], field: K): Person[K][] {
  const values: Person[K][] = people.map((person: Person) => person[field]);
  return Array.from(new Set<Person[K]>(values));
}

"""
        + _PLUCK_PLUMBING,
        # Sorts, losing the input order the question specified.
        """interface Person {
  name: string;
  city: string;
  role: string;
}

function pluck<K extends keyof Person>(people: Person[], field: K): Person[K][] {
  const values: Person[K][] = people.map((person: Person) => person[field]);
  values.sort();
  return values;
}

"""
        + _PLUCK_PLUMBING,
    ],
)


if len(TYPESCRIPT_BASICS_MODULES) != 12:
    raise TypeScriptAuthoringError(
        f"expected 12 TypeScript basics problems, built "
        f"{len(TYPESCRIPT_BASICS_MODULES)}"
    )
