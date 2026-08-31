"""C++ fundamentals: the problems a learner should meet before Blind 75.

The shared progression comes from :mod:`app.data.curriculum_basics_kit`, which
also supplies the three problems C and C++ share and nobody else gets:
`pointer-stride` (pointer arithmetic), `dynamic-filter` (storage whose size is
not known up front) and `top-scorer` (a record type). The problem defined here,
`minmax-refs`, is the one that is specifically about C++ references.

Every problem restricts itself to ``languages: ["cpp"]``.
"""

from __future__ import annotations

import random
from typing import Any

from app.data.curriculum_basics_kit import (
    COMMON_TASKS,
    DYNAMIC_FILTER,
    POINTER_STRIDE,
    TOP_SCORER,
    materialise,
)

_SKILL = "cpp_basics"


def _values(seed: int, count: int, lo: int, hi: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.randint(lo, hi) for _ in range(count)]


# --------------------------------------------------------------------------- #
#  References: returning two answers from one function                        #
# --------------------------------------------------------------------------- #

MINMAX_REFS: dict[str, Any] = {
    "key": "minmax-refs",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Smallest and Largest, Through References",
    "statement": (
        "Read n values and print the smallest and the largest on one line, "
        "smallest first.\n\n"
        "A function can only return one value, but it can write to as many as "
        "you hand it a reference to. Write a helper like\n\n"
        "    void findMinMax(const std::vector<long long>& v, long long& lo, "
        "long long& hi);\n\n"
        "and have it assign through `lo` and `hi`. Because they are references "
        "and not copies, the caller sees the values change. Note the "
        "`const&` on the vector: passing it by value would copy 200000 "
        "elements for no reason.\n\n"
        "Seed both from the first element, not from 0: an all-negative array "
        "has no non-negative maximum."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= a[i] <= 1000000000",
        "Print the minimum first",
        "When n = 1 the minimum and the maximum are the same value",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": "One line: two space-separated integers, the minimum then the maximum.",
    "examples": [
        {
            "stdin": "5\n3 1 4 1 5\n",
            "stdout": "1 5",
            "explanation": "The smallest value is 1 and the largest is 5.",
        },
        {
            "stdin": "3\n-7 -2 -9\n",
            "stdout": "-9 -2",
            "explanation": (
                "Every value is negative, so an accumulator seeded with 0 would "
                "wrongly report 0 as the maximum."
            ),
        },
    ],
    "criteria": [
        "Return both answers through reference parameters rather than two passes",
        "Seed from the first element, so an all-negative array works",
        "Print the minimum first",
    ],
    "io": {
        "mode": "tokens",
        "function": "print_min_max",
        "todo": "print the smallest value then the largest value of arr",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr"],
        "returns": "void",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    low = values[0]
    high = values[0]
    for value in values[1:]:
        if value < low:
            low = value
        if value > high:
            high = value
    print(low, high)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: mixed", "stdin": "5\n3 1 4 1 5\n", "hidden": False, "match": "tokens"},
        {"name": "sample: all negative", "stdin": "3\n-7 -2 -9\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: single element", "stdin": "1\n-6\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: all identical", "stdin": "4\n8 8 8 8\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: sorted ascending", "stdin": "4\n1 2 3 4\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: extremes", "stdin": "3\n-1000000000 0 1000000000\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: scale",
            "stdin": "200000\n" + " ".join(map(str, _values(91, 200000, -1000000000, 1000000000))) + "\n",
            "hidden": True,
            "match": "tokens",
        },
    ],
    "wrong": [
        # Right values, wrong order.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
v = [int(x) for x in d[1:1 + n]]
print(max(v), min(v))
""".lstrip(),
        # Seeds both accumulators with 0.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
lo = 0
hi = 0
for x in d[1:1 + n]:
    value = int(x)
    if value < lo:
        lo = value
    if value > hi:
        hi = value
print(lo, hi)
""".lstrip(),
        # Uses the first and last elements, assuming the input is sorted.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
v = [int(x) for x in d[1:1 + n]]
print(v[0], v[-1])
""".lstrip(),
    ],
}


PROBLEMS: list[dict[str, Any]] = materialise(
    list(COMMON_TASKS) + [TOP_SCORER, POINTER_STRIDE, DYNAMIC_FILTER, MINMAX_REFS],
    prefix="basics-cpp",
    language="cpp",
    skill_id=_SKILL,
    notes={
        "sum-two": [
            "std::cin >> a >> b reads both values; declare them long long"
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
            "std::reverse(s.begin(), s.end()) from <algorithm>, or two indices "
            "walking inwards"
        ],
        "count-vowels": ["Range over the string: for (char ch : s)"],
        "second-largest": ["Two long long variables are enough; no sort required"],
        "matrix-transpose": [
            "A flat std::vector<long long> indexed i * c + j avoids a vector of "
            "vectors"
        ],
        "max-row-sum": ["Declare the row total long long and seed the best with the first row"],
        "top-scorer": [
            "Define a struct (or class) Student { long long id; long long score; } "
            "and build a std::vector of them"
        ],
        "pointer-stride": [
            "const long long* p = arr.data(); advancing p by s moves s elements, "
            "not s bytes"
        ],
        "dynamic-filter": [
            "std::vector::push_back grows the buffer for you; reserve() if you "
            "want to size it exactly"
        ],
    },
)
