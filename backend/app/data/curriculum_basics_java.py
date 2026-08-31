"""Java fundamentals: the problems a learner should meet before Blind 75.

The shared progression (printing, types, operators, conditionals, loops,
functions, strings, arrays, matrices) comes from
:mod:`app.data.curriculum_basics_kit`, along with the record-modelling problem
(`top-scorer`) that Java expresses as a class with fields. The three problems
defined here are the Java-flavoured ones: `String.split`, character
classification, and building an `ArrayList` whose size is not known up front.

Every problem restricts itself to ``languages: ["java"]``.
"""

from __future__ import annotations

import random
from typing import Any

from app.data.curriculum_basics_kit import COMMON_TASKS, TOP_SCORER, materialise

_SKILL = "java_basics"


def _values(seed: int, count: int, lo: int, hi: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.randint(lo, hi) for _ in range(count)]


def _words(seed: int, count: int) -> str:
    rng = random.Random(seed)
    words = [
        "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(1, 9)))
        for _ in range(count)
    ]
    return " ".join(words) + "\n"


def _mixed_case(seed: int, length: int) -> str:
    rng = random.Random(seed)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!"
    return "".join(rng.choice(alphabet) for _ in range(length)) + "\n"


# --------------------------------------------------------------------------- #
#  Strings: splitting                                                         #
# --------------------------------------------------------------------------- #

REVERSE_WORDS: dict[str, Any] = {
    "key": "reverse-words",
    "difficulty": 3,
    "estimated_minutes": 18,
    "title": "Reverse the Word Order",
    "statement": (
        "Read one line of text and print its words in reverse order, separated "
        "by single spaces. The words themselves are not reversed.\n\n"
        "`the quick brown fox` becomes `fox brown quick the`. Split the line "
        "on spaces, walk the resulting array backwards, and join with a single "
        "space — a `StringBuilder` is the right way to accumulate the answer, "
        "because repeatedly using `+=` on a String allocates a new String every "
        "time and turns a linear job into a quadratic one at 200000 "
        "characters."
    ),
    "constraints": [
        "1 <= length of the line <= 200000",
        "Words are lower-case and upper-case letters and digits",
        "Words are separated by exactly one space; there is no leading or "
        "trailing whitespace",
        "Build the output with StringBuilder, not repeated String concatenation",
    ],
    "input_format": "Line 1: the text, words separated by single spaces.",
    "output_format": "One line: the same words in reverse order, single-spaced.",
    "examples": [
        {
            "stdin": "the quick brown fox\n",
            "stdout": "fox brown quick the",
            "explanation": (
                "The four words are emitted last to first; each word keeps its own "
                "spelling."
            ),
        },
        {
            "stdin": "abc\n",
            "stdout": "abc",
            "explanation": "A single word reversed in order is itself.",
        },
    ],
    "criteria": [
        "Reverse the order of the words, not the characters",
        "Separate the output with single spaces and no trailing space",
        "Handle a line with only one word",
    ],
    "io": {
        "mode": "line",
        "function": "print_words_reversed",
        "todo": "print the words of s in reverse order, separated by single spaces",
        "reads": [{"name": "s", "type": "string"}],
        "args": ["s"],
        "returns": "void",
    },
    "reference": r"""
import sys

def main():
    s = sys.stdin.readline().rstrip("\n")
    sys.stdout.write(" ".join(reversed(s.split(" "))) + "\n")

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: four words", "stdin": "the quick brown fox\n", "hidden": False},
        {"name": "sample: single word", "stdin": "abc\n", "hidden": False},
        {"name": "hidden: two words", "stdin": "hello world\n", "hidden": True},
        {"name": "hidden: repeated word", "stdin": "a a b a\n", "hidden": True},
        {"name": "hidden: digits in words", "stdin": "x1 y22 z333\n", "hidden": True},
        {"name": "hidden: palindromic order", "stdin": "ab cd ab\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _words(81, 30000), "hidden": True},
    ],
    "wrong": [
        # Reverses the characters, which also reverses each word.
        "import sys\nprint(sys.stdin.readline().rstrip('\\n')[::-1])\n",
        # Leaves the order alone.
        "import sys\nprint(sys.stdin.readline().rstrip('\\n'))\n",
        # Reverses every word in place but keeps the word order.
        r"""
import sys
s = sys.stdin.readline().rstrip("\n")
print(" ".join(w[::-1] for w in s.split(" ")))
""".lstrip(),
        # Sorts the words instead of reversing them.
        r"""
import sys
s = sys.stdin.readline().rstrip("\n")
print(" ".join(sorted(s.split(" "), reverse=True)))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  Strings: character classification                                          #
# --------------------------------------------------------------------------- #

CASE_COUNTS: dict[str, Any] = {
    "key": "case-counts",
    "difficulty": 2,
    "estimated_minutes": 15,
    "title": "Count Upper and Lower Case Letters",
    "statement": (
        "Read one line of text and print two numbers on one line: how many of "
        "its characters are upper-case letters, then how many are lower-case "
        "letters.\n\n"
        "Digits, spaces and punctuation count as neither. `Character."
        "isUpperCase(c)` and `Character.isLowerCase(c)` answer the question "
        "directly; comparing against 'A' and 'Z' by hand works too, as long as "
        "you remember that the characters between 'Z' and 'a' in ASCII are "
        "punctuation, not letters."
    ),
    "constraints": [
        "1 <= length of the line <= 200000",
        "The line contains printable ASCII characters and may include spaces",
        "Only ASCII letters count; digits, spaces and punctuation count as neither",
    ],
    "input_format": "Line 1: the text to scan.",
    "output_format": "One line: two space-separated integers, the upper-case count then the lower-case count.",
    "examples": [
        {
            "stdin": "Hello World 42!\n",
            "stdout": "2 8",
            "explanation": (
                "H and W are upper case; ello and orld are the eight lower-case "
                "letters. The space, the digits and the '!' count as neither."
            ),
        },
        {
            "stdin": "[]{}^_`|~\n",
            "stdout": "0 0",
            "explanation": (
                "These characters all sit between 'Z' and 'a' or after 'z' in ASCII, "
                "so a naive range check that only excludes digits would miscount "
                "them."
            ),
        },
    ],
    "criteria": [
        "Print the upper-case count first",
        "Count only letters; digits, spaces and punctuation count as neither",
        "Scan the whole line",
    ],
    "io": {
        "mode": "line",
        "function": "print_case_counts",
        "todo": "print the number of upper-case letters then the number of lower-case letters",
        "reads": [{"name": "s", "type": "string"}],
        "args": ["s"],
        "returns": "void",
    },
    "reference": r"""
import sys

def main():
    s = sys.stdin.readline().rstrip("\n")
    upper = sum(1 for ch in s if "A" <= ch <= "Z")
    lower = sum(1 for ch in s if "a" <= ch <= "z")
    print(upper, lower)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: mixed", "stdin": "Hello World 42!\n", "hidden": False, "match": "tokens"},
        {"name": "sample: punctuation between the ranges", "stdin": "[]{}^_`|~\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: all upper", "stdin": "ABCDEF\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: all lower", "stdin": "abcdef\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: digits only", "stdin": "1234567890\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: single space-separated letters", "stdin": "a B c D\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: scale", "stdin": _mixed_case(82, 200000), "hidden": True, "match": "tokens"},
    ],
    "wrong": [
        # Right counts, wrong order.
        r"""
import sys
s = sys.stdin.readline().rstrip("\n")
print(sum(1 for c in s if "a" <= c <= "z"), sum(1 for c in s if "A" <= c <= "Z"))
""".lstrip(),
        # Treats everything that is not upper case as lower case.
        r"""
import sys
s = sys.stdin.readline().rstrip("\n")
upper = sum(1 for c in s if "A" <= c <= "Z")
print(upper, len(s) - upper)
""".lstrip(),
        # Counts non-digits as letters, so punctuation is miscounted.
        r"""
import sys
s = sys.stdin.readline().rstrip("\n")
upper = sum(1 for c in s if "A" <= c <= "Z")
lower = sum(1 for c in s if not c.isdigit() and c != " " and not ("A" <= c <= "Z"))
print(upper, lower)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  ArrayList: a collection whose size is not known up front                   #
# --------------------------------------------------------------------------- #

DISTINCT_IN_ORDER: dict[str, Any] = {
    "key": "distinct-in-order",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Distinct Values in First-Appearance Order",
    "statement": (
        "Read n values and print how many distinct values there are, then "
        "those distinct values on the next line in the order they first "
        "appeared.\n\n"
        "You cannot size a plain `long[]` for the answer before you have "
        "scanned the input, which is what `ArrayList<Long>` is for: `add` as "
        "you discover a new value, and let it grow. A `HashSet` answers 'have "
        "I seen this?' in constant time; the list is what preserves the order "
        "the set throws away. Using only the list and scanning it for each "
        "input value is O(n^2) and will not finish the largest case."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= a[i] <= 1000000000",
        "Report first-appearance order, not sorted order",
        "An O(n^2) membership scan times out; use a HashSet alongside the list",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": (
        "Line 1: the number of distinct values.\n"
        "Line 2: the distinct values, space-separated, in first-appearance order."
    ),
    "examples": [
        {
            "stdin": "7\n4 1 4 2 1 5 4\n",
            "stdout": "4\n4 1 2 5",
            "explanation": (
                "4, 1, 2 and 5 are the distinct values; 4 leads because it appeared "
                "first, so the output is not sorted."
            ),
        },
        {
            "stdin": "3\n9 9 9\n",
            "stdout": "1\n9",
            "explanation": "Only one distinct value, printed once.",
        },
    ],
    "criteria": [
        "Print the count before the values",
        "Preserve first-appearance order",
        "Stay linear: use a hash set for the membership test",
    ],
    "io": {
        "mode": "tokens",
        "function": "print_distinct",
        "todo": (
            "print the number of distinct values in arr, then those values in "
            "first-appearance order"
        ),
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
    seen = set()
    order = []
    for token in data[1:1 + n]:
        value = int(token)
        if value not in seen:
            seen.add(value)
            order.append(value)
    sys.stdout.write(f"{len(order)}\n" + " ".join(map(str, order)) + "\n")

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: four distinct", "stdin": "7\n4 1 4 2 1 5 4\n", "hidden": False, "match": "tokens"},
        {"name": "sample: one distinct", "stdin": "3\n9 9 9\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: already distinct", "stdin": "4\n3 1 4 2\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: single element", "stdin": "1\n-5\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: negatives and zero", "stdin": "6\n0 -1 0 -1 -2 0\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: descending input", "stdin": "5\n5 4 3 2 1\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: scale, punishes an O(n^2) scan",
            "stdin": "200000\n" + " ".join(map(str, _values(83, 200000, -1000000000, 1000000000))) + "\n",
            "hidden": True,
            "match": "tokens",
        },
    ],
    "wrong": [
        # Sorted order rather than first-appearance order.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
values = sorted(set(int(x) for x in d[1:1 + n]))
print(len(values))
print(" ".join(map(str, values)))
""".lstrip(),
        # Omits the count line.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
seen = set(); order = []
for t in d[1:1 + n]:
    v = int(t)
    if v not in seen:
        seen.add(v); order.append(v)
print(" ".join(map(str, order)))
""".lstrip(),
        # Only drops values equal to their immediate predecessor.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
order = []
for t in d[1:1 + n]:
    v = int(t)
    if not order or order[-1] != v:
        order.append(v)
print(len(order))
print(" ".join(map(str, order)))
""".lstrip(),
        # Quadratic membership scan: right answer, cannot finish the scale case.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
order = []
for t in d[1:1 + n]:
    v = int(t)
    found = False
    for u in order:
        if u == v:
            found = True
            break
    if not found:
        order.append(v)
print(len(order))
print(" ".join(map(str, order)))
""".lstrip(),
    ],
}


PROBLEMS: list[dict[str, Any]] = materialise(
    list(COMMON_TASKS) + [TOP_SCORER, REVERSE_WORDS, CASE_COUNTS, DISTINCT_IN_ORDER],
    prefix="basics-java",
    language="java",
    skill_id=_SKILL,
    notes={
        "sum-two": [
            "Everything lives inside class Main; the entry point is "
            "public static void main(String[] args)"
        ],
        "truncated-mean": [
            "Java's / already truncates toward zero for ints, so the sum is the "
            "part to get right: declare it long"
        ],
        "bitwise-trio": ["Use &, | and ^, not && and ||"],
        "leap-year": ["An if/else if/else chain reads well here"],
        "multiples-sum": ["for (int i = 1; i < n; i++) is the loop; the total must be long"],
        "fibonacci": ["Write it as a static method that returns long"],
        "reverse-string": [
            "new StringBuilder(s).reverse().toString() does it; a char loop with "
            "+= on a String is quadratic"
        ],
        "count-vowels": ["s.charAt(i) reads one character; there is no need to split"],
        "second-largest": ["Two long variables are enough; no sorting required"],
        "matrix-transpose": [
            "Read the values into a flat long[] and index i * c + j, or use a "
            "long[r][c]"
        ],
        "max-row-sum": ["Declare the row total as long, and seed the best with the first row"],
        "top-scorer": [
            "Define a small Student class (or a record) with an id and a score, "
            "build an array of them, then pick the winner"
        ],
    },
)
