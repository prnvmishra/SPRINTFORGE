"""C fundamentals: the problems a learner should meet before Blind 75.

The shared progression comes from :mod:`app.data.curriculum_basics_kit`, along
with `pointer-stride` (pointer arithmetic), `dynamic-filter` (malloc/free for a
result whose size is not known up front) and `top-scorer` (a struct that pairs
two fields). The problem defined here, `sort-three`, is the classic
swap-through-pointers exercise.

Every problem restricts itself to ``languages: ["c"]``, so no pointer problem
is ever restated for Python.
"""

from __future__ import annotations

from typing import Any

from app.data.curriculum_basics_kit import (
    COMMON_TASKS,
    DYNAMIC_FILTER,
    POINTER_STRIDE,
    TOP_SCORER,
    materialise,
)

_SKILL = "c_basics"


# --------------------------------------------------------------------------- #
#  Pointers: swapping through them                                            #
# --------------------------------------------------------------------------- #

SORT_THREE: dict[str, Any] = {
    "key": "sort-three",
    "difficulty": 2,
    "estimated_minutes": 18,
    "title": "Order Three Values by Swapping Through Pointers",
    "statement": (
        "Read three integers and print them in ascending order on one line.\n\n"
        "The point is not the sorting, which is three comparisons; the point is "
        "the swap. C passes arguments by value, so a function that takes "
        "`long long x, long long y` and exchanges them changes nothing the "
        "caller can see. Write\n\n"
        "    void swap_values(long long* x, long long* y);\n\n"
        "and call it as `swap_values(&a, &b)`. Inside, `*x` and `*y` are the "
        "caller's own variables, and assigning through them is what makes the "
        "exchange stick. Three conditional swaps put a, b and c in order."
    ),
    "constraints": [
        "-4000000000 <= a, b, c <= 4000000000, so use a 64-bit type",
        "Values may repeat",
        "Print all three values on one line, ascending",
    ],
    "input_format": "Line 1: three space-separated integers a, b and c.",
    "output_format": "One line: the three values in ascending order, space-separated.",
    "examples": [
        {
            "stdin": "3 1 2\n",
            "stdout": "1 2 3",
            "explanation": (
                "Swapping a with b gives 1 3 2, then swapping the last two gives "
                "1 2 3."
            ),
        },
        {
            "stdin": "5 5 4\n",
            "stdout": "4 5 5",
            "explanation": (
                "Repeated values are fine; only the 4 has to move to the front."
            ),
        },
    ],
    "criteria": [
        "Swap through pointers, so the exchange is visible to the caller",
        "Handle repeated values",
        "Print ascending order, all three on one line",
    ],
    "io": {
        "mode": "tokens",
        "function": "print_sorted_three",
        "todo": "print a, b and c in ascending order, swapping through pointers",
        "reads": [
            {"name": "a", "type": "long"},
            {"name": "b", "type": "long"},
            {"name": "c", "type": "long"},
        ],
        "args": ["a", "b", "c"],
        "returns": "void",
    },
    "reference": r"""
import sys

def main():
    values = [int(x) for x in sys.stdin.read().split()[:3]]
    values.sort()
    print(values[0], values[1], values[2])

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: 3 1 2", "stdin": "3 1 2\n", "hidden": False, "match": "tokens"},
        {"name": "sample: repeated values", "stdin": "5 5 4\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: already sorted", "stdin": "1 2 3\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: descending", "stdin": "9 5 1\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: all equal", "stdin": "7 7 7\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: negatives", "stdin": "-1 -9 -5\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: middle is smallest", "stdin": "4 -8 4\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: beyond 32 bits", "stdin": "4000000000 -4000000000 0\n", "hidden": True, "match": "tokens"},
    ],
    "wrong": [
        # Prints the input unchanged.
        r"""
import sys
v = [int(x) for x in sys.stdin.read().split()[:3]]
print(v[0], v[1], v[2])
""".lstrip(),
        # Descending.
        r"""
import sys
v = sorted((int(x) for x in sys.stdin.read().split()[:3]), reverse=True)
print(v[0], v[1], v[2])
""".lstrip(),
        # Only the first pair is ordered, which is what happens when the swap
        # function takes its arguments by value for the remaining comparisons.
        r"""
import sys
v = [int(x) for x in sys.stdin.read().split()[:3]]
if v[0] > v[1]:
    v[0], v[1] = v[1], v[0]
print(v[0], v[1], v[2])
""".lstrip(),
        # Prints min, max, middle.
        r"""
import sys
v = sorted(int(x) for x in sys.stdin.read().split()[:3])
print(v[0], v[2], v[1])
""".lstrip(),
    ],
}


PROBLEMS: list[dict[str, Any]] = materialise(
    list(COMMON_TASKS) + [TOP_SCORER, POINTER_STRIDE, DYNAMIC_FILTER, SORT_THREE],
    prefix="basics-c",
    language="c",
    skill_id=_SKILL,
    notes={
        "sum-two": [
            'scanf("%lld %lld", &a, &b) reads both values; print with %lld'
        ],
        "truncated-mean": [
            "Integer division on long long already truncates toward zero, so the "
            "job is to hold the sum in a long long"
        ],
        "bitwise-trio": ["Use &, | and ^, not && and ||"],
        "leap-year": ["An if/else if/else chain or one boolean expression both work"],
        "multiples-sum": ["for (int i = 1; i < n; i++), with the total declared long long"],
        "fibonacci": ["Write a function returning long long and call it from main"],
        "reverse-string": [
            "strlen(s) gives the length; two indices walking inwards reverse it "
            "without allocating"
        ],
        "count-vowels": ["Walk the char array until the terminating '\\0'"],
        "second-largest": ["Two long long variables are enough; no sorting required"],
        "matrix-transpose": [
            "The grid arrives as one flat block, so value (i, j) is grid[i * c + j]"
        ],
        "max-row-sum": ["Declare the row total long long and seed the best with the first row"],
        "top-scorer": [
            "Define a struct Student { long long id; long long score; } and build "
            "an array of them with malloc"
        ],
        "pointer-stride": [
            "const long long* p = arr; p += s advances s elements, not s bytes"
        ],
        "dynamic-filter": [
            "malloc a buffer of at most n values (or count first and allocate "
            "exactly), then free it"
        ],
    },
)
