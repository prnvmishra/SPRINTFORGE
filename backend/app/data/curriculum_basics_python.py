"""Python fundamentals: the problems a learner should meet before Blind 75.

The shared progression (printing, types, operators, conditionals, loops,
functions, strings, arrays, matrices) comes from
:mod:`app.data.curriculum_basics_kit`; the four problems defined here are the
ones that only make sense in Python — slicing, comprehensions, dicts and list
rotation.

Every problem restricts itself to ``languages: ["python"]``, so none of them is
expanded into the other four languages.
"""

from __future__ import annotations

import random
from typing import Any

from app.data.curriculum_basics_kit import COMMON_TASKS, materialise

_SKILL = "python_basics"


def _values(seed: int, count: int, lo: int, hi: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.randint(lo, hi) for _ in range(count)]


def _text(seed: int, length: int, alphabet: str) -> str:
    rng = random.Random(seed)
    return "".join(rng.choice(alphabet) for _ in range(length)) + "\n"


# --------------------------------------------------------------------------- #
#  Slicing                                                                    #
# --------------------------------------------------------------------------- #

SLICE_HALVES: dict[str, Any] = {
    "key": "slice-halves",
    "difficulty": 2,
    "estimated_minutes": 15,
    "title": "Split a String by Index Parity",
    "statement": (
        "Read one line of text. Print its characters at even indices on the "
        "first line, then its characters at odd indices on the second.\n\n"
        "Indices are 0-based, so `abcdef` gives `ace` and then `bdf`. This is "
        "one slice each: `s[::2]` and `s[1::2]`. Writing it as two loops also "
        "works, but the slice is the idiom worth knowing, and the extended "
        "slice syntax `start:stop:step` is what makes it a one-liner."
    ),
    "constraints": [
        "1 <= length of the line <= 200000",
        "The line contains printable ASCII characters and may include spaces",
        "Indices are 0-based, so the first character is 'even'",
        "The second line is empty when the input has only one character",
    ],
    "input_format": "Line 1: the text to split.",
    "output_format": (
        "Line 1: the characters at even indices.\n"
        "Line 2: the characters at odd indices (possibly empty)."
    ),
    "examples": [
        {
            "stdin": "abcdef\n",
            "stdout": "ace\nbdf",
            "explanation": (
                "Indices 0, 2, 4 hold a, c, e; indices 1, 3, 5 hold b, d, f."
            ),
        },
        {
            "stdin": "hello world\n",
            "stdout": "hlowrd\nel ol",
            "explanation": (
                "The space sits at index 5, an odd index, so it belongs to the "
                "second line — spaces are characters like any other."
            ),
        },
    ],
    "criteria": [
        "Treat index 0 as even",
        "Print the even-index characters first",
        "Keep spaces, which are ordinary characters here",
    ],
    "io": {
        "mode": "line",
        "function": "print_halves",
        "todo": "print s[::2] on one line and s[1::2] on the next",
        "reads": [{"name": "s", "type": "string"}],
        "args": ["s"],
        "returns": "void",
    },
    "reference": r"""
import sys

def main():
    s = sys.stdin.readline().rstrip("\n")
    sys.stdout.write(s[::2] + "\n" + s[1::2] + "\n")

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: abcdef", "stdin": "abcdef\n", "hidden": False},
        {"name": "sample: with a space", "stdin": "hello world\n", "hidden": False},
        {"name": "hidden: single character", "stdin": "q\n", "hidden": True},
        {"name": "hidden: two characters", "stdin": "ab\n", "hidden": True},
        {"name": "hidden: digits", "stdin": "1234567\n", "hidden": True},
        {"name": "hidden: repeated character", "stdin": "aaaa\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _text(71, 200000, "abcdefgh xyz"), "hidden": True},
    ],
    "wrong": [
        # Halves the string by position instead of by index parity.
        r"""
import sys
s = sys.stdin.readline().rstrip("\n")
mid = (len(s) + 1) // 2
print(s[:mid])
print(s[mid:])
""".lstrip(),
        # Right slices, wrong order.
        r"""
import sys
s = sys.stdin.readline().rstrip("\n")
print(s[1::2])
print(s[::2])
""".lstrip(),
        # Treats index 1 as the first "even" index.
        r"""
import sys
s = sys.stdin.readline().rstrip("\n")
print(s[1::2])
print(s[2::2])
""".lstrip(),
        # Prints the whole line twice.
        r"""
import sys
s = sys.stdin.readline().rstrip("\n")
print(s)
print(s)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  Comprehensions                                                             #
# --------------------------------------------------------------------------- #

SQUARES_OF_EVENS: dict[str, Any] = {
    "key": "squares-of-evens",
    "difficulty": 2,
    "estimated_minutes": 15,
    "title": "Sum of Squares of the Even Values",
    "statement": (
        "Read n values and print the sum of the squares of the even ones.\n\n"
        "Two things at once: filter to the even values, then map each to its "
        "square. A comprehension says both in one line — "
        "`sum(v * v for v in arr if v % 2 == 0)`.\n\n"
        "Careful with negatives: -4 is even, and in Python `-4 % 2` is 0, but "
        "testing `v % 2 == 1` for oddness is a trap in either direction. "
        "Squares are non-negative, so the sign of the input never reaches the "
        "answer."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= a[i] <= 1000000000",
        "The answer reaches 2 * 10^23, which Python's ints handle exactly",
        "0 is even",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": "A single integer: the sum of the squares of the even values.",
    "examples": [
        {
            "stdin": "5\n1 2 3 4 5\n",
            "stdout": "20",
            "explanation": "The even values are 2 and 4, giving 4 + 16 = 20.",
        },
        {
            "stdin": "4\n-2 -3 0 7\n",
            "stdout": "4",
            "explanation": (
                "-2 and 0 are even. (-2)^2 + 0^2 = 4, so the negative input still "
                "contributes a positive square."
            ),
        },
    ],
    "criteria": [
        "Include negative even values, and 0",
        "Square after filtering, not before",
        "Print 0 when no value is even",
    ],
    "io": {
        "mode": "tokens",
        "function": "sum_even_squares",
        "todo": "return the sum of v * v over the even values v of arr",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr"],
        "returns": "long",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    arr = [int(x) for x in data[1:1 + n]]
    print(sum(v * v for v in arr if v % 2 == 0))

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: 1..5", "stdin": "5\n1 2 3 4 5\n", "hidden": False},
        {"name": "sample: negatives and zero", "stdin": "4\n-2 -3 0 7\n", "hidden": False},
        {"name": "hidden: no even values", "stdin": "3\n1 3 5\n", "hidden": True},
        {"name": "hidden: all even", "stdin": "3\n2 4 6\n", "hidden": True},
        {"name": "hidden: only negative odds", "stdin": "3\n-1 -3 -5\n", "hidden": True},
        {"name": "hidden: single zero", "stdin": "1\n0\n", "hidden": True},
        {
            "name": "hidden: scale with large magnitudes",
            "stdin": "200000\n" + " ".join(map(str, _values(72, 200000, -1000000000, 1000000000))) + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Squares everything.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
print(sum(int(x) ** 2 for x in d[1:1 + n]))
""".lstrip(),
        # Sums the even values without squaring.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
print(sum(v for v in (int(x) for x in d[1:1 + n]) if v % 2 == 0))
""".lstrip(),
        # Filters to the odd values instead of the even ones.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
print(sum(v * v for v in (int(x) for x in d[1:1 + n]) if v % 2 != 0))
""".lstrip(),
        # Counts instead of summing.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
print(sum(1 for x in d[1:1 + n] if int(x) % 2 == 0))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  Dictionaries                                                               #
# --------------------------------------------------------------------------- #

MODE_VALUE: dict[str, Any] = {
    "key": "mode-value",
    "difficulty": 3,
    "estimated_minutes": 18,
    "title": "Most Frequent Value",
    "statement": (
        "Read n values and print the one that occurs most often. If several "
        "values tie for the highest count, print the smallest of them.\n\n"
        "A dict from value to count is the natural tool: one pass to build it, "
        "one pass over its items to pick the winner. `dict.get(v, 0) + 1` or "
        "`collections.Counter` both do the counting; the tie rule is what you "
        "have to get right yourself, because iterating a dict gives you "
        "insertion order, not sorted order."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= a[i] <= 1000000000",
        "On a tie, print the smallest value with the maximum count",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": "A single integer: the most frequent value.",
    "examples": [
        {
            "stdin": "7\n4 1 2 4 2 4 1\n",
            "stdout": "4",
            "explanation": "4 occurs three times, more than 1 (twice) or 2 (twice).",
        },
        {
            "stdin": "4\n9 3 9 3\n",
            "stdout": "3",
            "explanation": (
                "9 and 3 both occur twice. The smaller value wins, so 3 is printed "
                "even though 9 was seen first."
            ),
        },
    ],
    "criteria": [
        "Break ties by the smallest value, not by insertion order",
        "Print the value itself, not its count",
        "Handle negative values and n = 1",
    ],
    "io": {
        "mode": "tokens",
        "function": "mode_value",
        "todo": "return the most frequent value, breaking ties by the smallest value",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr"],
        "returns": "long",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    counts = {}
    for token in data[1:1 + n]:
        value = int(token)
        counts[value] = counts.get(value, 0) + 1
    best_value = None
    best_count = -1
    for value, count in counts.items():
        if count > best_count or (count == best_count and value < best_value):
            best_value = value
            best_count = count
    print(best_value)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: clear winner", "stdin": "7\n4 1 2 4 2 4 1\n", "hidden": False},
        {"name": "sample: tie picks the smaller", "stdin": "4\n9 3 9 3\n", "hidden": False},
        {"name": "hidden: single element", "stdin": "1\n-8\n", "hidden": True},
        {"name": "hidden: all distinct, smallest wins", "stdin": "4\n5 2 9 7\n", "hidden": True},
        {"name": "hidden: negatives tie", "stdin": "4\n-1 -5 -1 -5\n", "hidden": True},
        {"name": "hidden: winner appears last", "stdin": "5\n1 2 3 3 3\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": "200000\n" + " ".join(map(str, _values(73, 200000, -50, 50))) + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # max() over the dict keeps whichever key it met first on a tie.
        r"""
import sys
from collections import Counter
d = sys.stdin.buffer.read().split()
n = int(d[0])
counts = Counter(int(x) for x in d[1:1 + n])
print(max(counts, key=counts.get))
""".lstrip(),
        # Prints the count rather than the value.
        r"""
import sys
from collections import Counter
d = sys.stdin.buffer.read().split()
n = int(d[0])
counts = Counter(int(x) for x in d[1:1 + n])
print(max(counts.values()))
""".lstrip(),
        # Breaks ties towards the larger value.
        r"""
import sys
from collections import Counter
d = sys.stdin.buffer.read().split()
n = int(d[0])
counts = Counter(int(x) for x in d[1:1 + n])
best = None
for value, count in sorted(counts.items()):
    if best is None or count >= counts[best]:
        best = value
print(best)
""".lstrip(),
        # Prints the smallest value, ignoring frequency.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
print(min(int(x) for x in d[1:1 + n]))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  Lists                                                                      #
# --------------------------------------------------------------------------- #

ROTATE_LEFT: dict[str, Any] = {
    "key": "rotate-left",
    "difficulty": 3,
    "estimated_minutes": 18,
    "title": "Rotate a List Left by k",
    "statement": (
        "Read n values and a shift k, then print the list rotated left by k "
        "positions: the element that was at index k comes first.\n\n"
        "k may be larger than n, so reduce it modulo n before slicing — "
        "rotating a 3-element list by 10 is the same as rotating it by 1. Two "
        "slices and a concatenation do the whole job: `arr[k:] + arr[:k]`."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "0 <= k <= 1000000000",
        "-1000000000 <= a[i] <= 1000000000",
        "k may exceed n; reduce it modulo n",
    ],
    "input_format": "Line 1: n and k.\nLine 2: n space-separated integers.",
    "output_format": "One line: the n rotated values, space-separated.",
    "examples": [
        {
            "stdin": "5 2\n1 2 3 4 5\n",
            "stdout": "3 4 5 1 2",
            "explanation": (
                "Rotating left by 2 moves the first two values to the back, so "
                "index 2 (the value 3) leads."
            ),
        },
        {
            "stdin": "3 10\n7 8 9\n",
            "stdout": "8 9 7",
            "explanation": (
                "10 mod 3 is 1, so this is a rotation by 1. Slicing with k = 10 "
                "directly would print the list unchanged."
            ),
        },
    ],
    "criteria": [
        "Reduce k modulo n before rotating",
        "Rotate left, so early elements move to the end",
        "Print all n values on one line",
    ],
    "io": {
        "mode": "tokens",
        "function": "print_rotated",
        "todo": "print arr rotated left by k positions (k may exceed n)",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "k", "type": "long"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr", "k"],
        "returns": "void",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    k = int(data[1]) % n
    arr = [x.decode() for x in data[2:2 + n]]
    sys.stdout.write(" ".join(arr[k:] + arr[:k]) + "\n")

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: rotate by 2", "stdin": "5 2\n1 2 3 4 5\n", "hidden": False, "match": "tokens"},
        {"name": "sample: k exceeds n", "stdin": "3 10\n7 8 9\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: k = 0", "stdin": "4 0\n61 72 83 94\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: k = n", "stdin": "4 4\n61 72 83 94\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: single element", "stdin": "1 7\n-3\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: negatives", "stdin": "5 3\n-1 -2 -3 -4 -5\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: scale",
            "stdin": "200000 123457\n"
            + " ".join(map(str, _values(74, 200000, -1000000000, 1000000000)))
            + "\n",
            "hidden": True,
            "match": "tokens",
        },
    ],
    "wrong": [
        # Forgets to reduce k, so a large k silently rotates by nothing.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0]); k = int(d[1])
arr = [x.decode() for x in d[2:2 + n]]
print(" ".join(arr[k:] + arr[:k]))
""".lstrip(),
        # Rotates right instead of left.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0]); k = int(d[1]) % n
arr = [x.decode() for x in d[2:2 + n]]
print(" ".join(arr[n - k:] + arr[:n - k]))
""".lstrip(),
        # Reverses the list.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
arr = [x.decode() for x in d[2:2 + n]]
print(" ".join(reversed(arr)))
""".lstrip(),
    ],
}


PROBLEMS: list[dict[str, Any]] = materialise(
    list(COMMON_TASKS) + [SLICE_HALVES, SQUARES_OF_EVENS, MODE_VALUE, ROTATE_LEFT],
    prefix="basics-py",
    language="python",
    skill_id=_SKILL,
    notes={
        "sum-two": ["Read the line with input() or sys.stdin, and split() it"],
        "truncated-mean": [
            "Python's // floors, so -11 // 4 is -3; truncate with int(a / b) on "
            "small values or by dividing the magnitude and reapplying the sign"
        ],
        "bitwise-trio": ["Use &, | and ^, not the keywords and/or"],
        "leap-year": ["An if/elif/else chain or one boolean expression both work"],
        "multiples-sum": ["A for loop over range(1, n) is the straightforward reading"],
        "fibonacci": ["Define a function with def and return from it"],
        "reverse-string": ["s[::-1] reverses a string in one slice"],
        "count-vowels": ["Iterate the string directly: for ch in s"],
        "second-largest": ["A set() removes duplicates, but handle the one-value case"],
        "matrix-transpose": [
            "Reading the values as one flat list and indexing i * c + j avoids "
            "building a list of lists"
        ],
        "max-row-sum": ["sum() over a slice gives one row's total"],
    },
)
