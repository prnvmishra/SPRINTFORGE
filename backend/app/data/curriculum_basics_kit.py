"""Task templates shared by the language-fundamentals problem sets.

The four fundamentals files (`curriculum_basics_c`, `_cpp`, `_java`,
`_python`) teach the same progression — printing and variables, types and
casting, operators, conditionals, loops, functions, strings, 1-D arrays, 2-D
matrices — because that progression is the same in every language. What differs
is the language the learner writes it in and the idiom they are told to reach
for.

So the *task* is defined once here (statement, `io` spec, reference solution,
case bank, wrong solutions) and :func:`materialise` stamps it out per language
with its own slug, skill and language restriction. A per-language `notes` map
appends the idiom hints that actually differ ("use a `for` loop over
`s.length()`", "use a list comprehension").

This is deliberately not a five-language expansion: every problem built here
carries a `languages` list of exactly one language, so the C pointer tasks
never appear in Python and the Java `ArrayList` task never appears in C.

Each template's `key` becomes the slug suffix. See
`docs/curriculum_authoring.md` for the contract every emitted dict must meet.
"""

from __future__ import annotations

import random
from typing import Any


# --------------------------------------------------------------------------- #
#  Deterministic case generation                                              #
# --------------------------------------------------------------------------- #


def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def _array_case(seed: int, n: int, lo: int, hi: int) -> str:
    rng = _rng(seed)
    values = [rng.randint(lo, hi) for _ in range(n)]
    return f"{n}\n{' '.join(map(str, values))}\n"


def _grid_case(seed: int, r: int, c: int, lo: int, hi: int) -> str:
    rng = _rng(seed)
    rows = [
        " ".join(str(rng.randint(lo, hi)) for _ in range(c)) for _ in range(r)
    ]
    return f"{r} {c}\n" + "\n".join(rows) + "\n"


def _text_case(seed: int, length: int, alphabet: str) -> str:
    rng = _rng(seed)
    return "".join(rng.choice(alphabet) for _ in range(length)) + "\n"


def _values(seed: int, count: int, lo: int, hi: int) -> list[int]:
    rng = _rng(seed)
    return [rng.randint(lo, hi) for _ in range(count)]


def _words_case(seed: int, count: int) -> str:
    rng = _rng(seed)
    words = [
        "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(rng.randint(1, 8)))
        for _ in range(count)
    ]
    return " ".join(words) + "\n"


# --------------------------------------------------------------------------- #
#  01 · Printing and variables                                                #
# --------------------------------------------------------------------------- #

SUM_TWO: dict[str, Any] = {
    "key": "sum-two",
    "difficulty": 1,
    "estimated_minutes": 8,
    "title": "Read Two Numbers and Print Their Sum",
    "statement": (
        "Your first program in this language: read two integers from standard "
        "input, store them in variables, and print their sum.\n\n"
        "This is the whole shape of every problem that follows — read input, "
        "compute, print exactly one answer and nothing else. No prompts, no "
        '"Enter a number:", no trailing text.'
    ),
    "constraints": [
        "-4000000000 <= a, b <= 4000000000",
        "The sum can exceed the range of a 32-bit int, so use a 64-bit type",
    ],
    "input_format": "Line 1: two space-separated integers a and b.",
    "output_format": "A single integer: a + b.",
    "examples": [
        {
            "stdin": "2 3\n",
            "stdout": "5",
            "explanation": "2 + 3 = 5. Only the number is printed.",
        },
        {
            "stdin": "-7 4\n",
            "stdout": "-3",
            "explanation": "Negative inputs are ordinary; -7 + 4 = -3.",
        },
    ],
    "criteria": [
        "Print only the sum, with no prompt text",
        "Use a 64-bit integer type so large inputs do not wrap",
    ],
    "io": {
        "mode": "tokens",
        "function": "add_two",
        "todo": "return a + b",
        "reads": [
            {"name": "a", "type": "long"},
            {"name": "b", "type": "long"},
        ],
        "args": ["a", "b"],
        "returns": "long",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.read().split()
    print(int(data[0]) + int(data[1]))

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: 2 3", "stdin": "2 3\n", "hidden": False},
        {"name": "sample: negative first", "stdin": "-7 4\n", "hidden": False},
        {"name": "hidden: both zero", "stdin": "0 0\n", "hidden": True},
        {"name": "hidden: both negative", "stdin": "-5 -6\n", "hidden": True},
        {"name": "hidden: overflows 32 bits", "stdin": "4000000000 4000000000\n", "hidden": True},
        {"name": "hidden: cancels to zero", "stdin": "1000000000 -1000000000\n", "hidden": True},
    ],
    "wrong": [
        # Subtracts instead of adding.
        "import sys\nd = sys.stdin.read().split()\nprint(int(d[0]) - int(d[1]))\n",
        # Multiplies: agrees with no case here.
        "import sys\nd = sys.stdin.read().split()\nprint(int(d[0]) * int(d[1]))\n",
        # Echoes the first number.
        "import sys\nd = sys.stdin.read().split()\nprint(int(d[0]))\n",
        # A hardcoded answer, which is exactly what the case bank exists to reject.
        "print(5)\n",
    ],
}


# --------------------------------------------------------------------------- #
#  02 · Types and casting                                                     #
# --------------------------------------------------------------------------- #

TRUNCATED_MEAN: dict[str, Any] = {
    "key": "truncated-mean",
    "difficulty": 2,
    "estimated_minutes": 15,
    "title": "Integer Mean, Truncated Toward Zero",
    "statement": (
        "Read n integers and print their mean, truncated toward zero.\n\n"
        "Truncating toward zero means the fractional part is dropped and the "
        "sign is kept: a mean of 2.7 prints 2 and a mean of -2.7 prints -2. "
        "That is what integer division does in C, C++ and Java, and it is "
        "*not* what it does in Python, where -11 // 4 is -3. Getting this "
        "right is the point of the exercise: the sum must be held in a 64-bit "
        "type and the division must round the way the statement says, not the "
        "way your language's operator happens to."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= a[i] <= 1000000000",
        "The sum reaches 2 * 10^14, so it needs a 64-bit type",
        "Truncate toward zero, not toward negative infinity",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": "A single integer: the mean truncated toward zero.",
    "examples": [
        {
            "stdin": "3\n1 2 4\n",
            "stdout": "2",
            "explanation": "The sum is 7 and 7 / 3 is 2.33..., which truncates to 2.",
        },
        {
            "stdin": "4\n-1 -2 -3 -5\n",
            "stdout": "-2",
            "explanation": (
                "The sum is -11 and -11 / 4 is -2.75. Truncating toward zero gives "
                "-2; flooring would wrongly give -3."
            ),
        },
    ],
    "criteria": [
        "Accumulate the sum in a 64-bit integer",
        "Truncate toward zero, so a negative mean keeps the larger value",
        "Handle n = 1",
    ],
    "io": {
        "mode": "tokens",
        "function": "truncated_mean",
        "todo": "return the mean of the array, truncated toward zero",
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
    total = sum(int(x) for x in data[1:1 + n])
    magnitude = abs(total) // n
    print(magnitude if total >= 0 else -magnitude)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: positive", "stdin": "3\n1 2 4\n", "hidden": False},
        {"name": "sample: negative truncates up", "stdin": "4\n-1 -2 -3 -5\n", "hidden": False},
        {"name": "hidden: exact division", "stdin": "2\n5 5\n", "hidden": True},
        {"name": "hidden: single negative", "stdin": "1\n-7\n", "hidden": True},
        {"name": "hidden: small negative mean", "stdin": "5\n-10 3 4 -1 2\n", "hidden": True},
        {
            "name": "hidden: needs 64 bits",
            "stdin": "3\n1000000000 999999998 1000000000\n",
            "hidden": True,
        },
        {"name": "hidden: scale", "stdin": _array_case(11, 200000, -1000000000, 1000000000), "hidden": True},
    ],
    "wrong": [
        # Floor division: correct for positives, off by one for a negative mean.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
print(sum(int(x) for x in d[1:1 + n]) // n)
""".lstrip(),
        # Prints the sum rather than the mean.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
print(sum(int(x) for x in d[1:1 + n]))
""".lstrip(),
        # Loses the sign.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
print(abs(sum(int(x) for x in d[1:1 + n])) // n)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  03 · Operators                                                             #
# --------------------------------------------------------------------------- #

BITWISE_TRIO: dict[str, Any] = {
    "key": "bitwise-trio",
    "difficulty": 2,
    "estimated_minutes": 12,
    "title": "Bitwise AND, OR and XOR",
    "statement": (
        "Read two non-negative integers a and b and print three values on one "
        "line: a AND b, a OR b, a XOR b, in that order.\n\n"
        "These are the bit-level operators (`&`, `|`, `^`) rather than the "
        "logical ones (`&&`, `||`). Mixing the two up is one of the classic "
        "beginner bugs, and here the answer tells you immediately: 12 & 10 is "
        "8, while `12 && 10` would be 1."
    ),
    "constraints": [
        "0 <= a, b <= 1000000000",
        "Print the three results in the order AND, OR, XOR",
    ],
    "input_format": "Line 1: two space-separated integers a and b.",
    "output_format": "One line with three space-separated integers: a&b, a|b, a^b.",
    "examples": [
        {
            "stdin": "12 10\n",
            "stdout": "8 14 6",
            "explanation": (
                "1100 & 1010 = 1000 = 8; 1100 | 1010 = 1110 = 14; "
                "1100 ^ 1010 = 0110 = 6."
            ),
        },
        {
            "stdin": "7 8\n",
            "stdout": "0 15 15",
            "explanation": (
                "0111 and 1000 share no bits, so AND is 0 and OR and XOR both "
                "set all four low bits."
            ),
        },
    ],
    "criteria": [
        "Use the bitwise operators, not the logical ones",
        "Print all three results on one line, in the order given",
    ],
    "io": {
        "mode": "tokens",
        "function": "print_bitwise",
        "todo": "print a & b, a | b and a ^ b separated by spaces",
        "reads": [
            {"name": "a", "type": "long"},
            {"name": "b", "type": "long"},
        ],
        "args": ["a", "b"],
        "returns": "void",
    },
    "reference": r"""
import sys

def main():
    a, b = (int(x) for x in sys.stdin.read().split()[:2])
    print(a & b, a | b, a ^ b)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: 12 10", "stdin": "12 10\n", "hidden": False, "match": "tokens"},
        {"name": "sample: disjoint bits", "stdin": "7 8\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: both zero", "stdin": "0 0\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: identical", "stdin": "1 1\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: one is zero", "stdin": "0 999\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: large", "stdin": "1000000000 123456789\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: subset bits", "stdin": "255 128\n", "hidden": True, "match": "tokens"},
    ],
    "wrong": [
        # Right values, wrong order.
        "import sys\na, b = (int(x) for x in sys.stdin.read().split()[:2])\nprint(a | b, a & b, a ^ b)\n",
        # Logical operators instead of bitwise.
        "import sys\na, b = (int(x) for x in sys.stdin.read().split()[:2])\nprint(int(bool(a and b)), int(bool(a or b)), a ^ b)\n",
        # XOR replaced by a subtraction that agrees on the first sample only.
        "import sys\na, b = (int(x) for x in sys.stdin.read().split()[:2])\nprint(a & b, a | b, abs(a - b))\n",
    ],
}


# --------------------------------------------------------------------------- #
#  04 · Conditionals                                                          #
# --------------------------------------------------------------------------- #

LEAP_YEAR: dict[str, Any] = {
    "key": "leap-year",
    "difficulty": 2,
    "estimated_minutes": 12,
    "title": "Leap Year",
    "statement": (
        "Read a year and print 1 if it is a leap year, otherwise 0.\n\n"
        "A year is a leap year when it is divisible by 4, except that years "
        "divisible by 100 are not, except that years divisible by 400 are. "
        "1900 is therefore not a leap year and 2000 is. Both exceptions are "
        "tested, so a rule that stops at the first one will not pass."
    ),
    "constraints": [
        "1 <= year <= 1000000",
        "Print exactly 1 or 0",
    ],
    "input_format": "Line 1: a single integer, the year.",
    "output_format": "A single integer: 1 for a leap year, 0 otherwise.",
    "examples": [
        {
            "stdin": "2024\n",
            "stdout": "1",
            "explanation": "2024 is divisible by 4 and not by 100, so it is a leap year.",
        },
        {
            "stdin": "1900\n",
            "stdout": "0",
            "explanation": (
                "1900 is divisible by 4 and by 100 but not by 400, so it is not a "
                "leap year."
            ),
        },
    ],
    "criteria": [
        "Apply all three rules, including the divisible-by-400 exception",
        "Print exactly 1 or 0, not true/false",
    ],
    "io": {
        "mode": "tokens",
        "function": "is_leap_year",
        "todo": "return 1 if year is a leap year, otherwise 0",
        "reads": [{"name": "year", "type": "int"}],
        "args": ["year"],
        "returns": "int",
    },
    "reference": r"""
import sys

def main():
    year = int(sys.stdin.read().split()[0])
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    print(1 if leap else 0)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: 2024", "stdin": "2024\n", "hidden": False},
        {"name": "sample: 1900", "stdin": "1900\n", "hidden": False},
        {"name": "hidden: 2000 (divisible by 400)", "stdin": "2000\n", "hidden": True},
        {"name": "hidden: 2023 (not divisible by 4)", "stdin": "2023\n", "hidden": True},
        {"name": "hidden: 2100 (century, not leap)", "stdin": "2100\n", "hidden": True},
        {"name": "hidden: 1600 (century, leap)", "stdin": "1600\n", "hidden": True},
        {"name": "hidden: year 4", "stdin": "4\n", "hidden": True},
    ],
    "wrong": [
        # Only the divisible-by-4 rule.
        "import sys\ny = int(sys.stdin.read().split()[0])\nprint(1 if y % 4 == 0 else 0)\n",
        # Stops at the century exception, so 2000 and 1600 are wrong.
        "import sys\ny = int(sys.stdin.read().split()[0])\nprint(1 if y % 4 == 0 and y % 100 != 0 else 0)\n",
        # Only multiples of 400.
        "import sys\ny = int(sys.stdin.read().split()[0])\nprint(1 if y % 400 == 0 else 0)\n",
        # A constant.
        "print(1)\n",
    ],
}


# --------------------------------------------------------------------------- #
#  05 · Loops                                                                 #
# --------------------------------------------------------------------------- #

MULTIPLES_SUM: dict[str, Any] = {
    "key": "multiples-sum",
    "difficulty": 2,
    "estimated_minutes": 15,
    "title": "Sum of Multiples of 3 or 5",
    "statement": (
        "Read n and print the sum of every integer from 1 up to but *not "
        "including* n that is divisible by 3 or by 5.\n\n"
        "Two traps live here. The bound is exclusive, so n itself never "
        "counts. And a number divisible by both 3 and 5 — 15, 30, 45 — must "
        "be counted once, not twice; adding the multiples of 3 to the "
        "multiples of 5 double-counts them."
    ),
    "constraints": [
        "1 <= n <= 1000000",
        "The answer reaches about 2.3 * 10^11, so it needs a 64-bit type",
        "A single loop up to n is fast enough",
    ],
    "input_format": "Line 1: a single integer n.",
    "output_format": "A single integer: the sum described above.",
    "examples": [
        {
            "stdin": "10\n",
            "stdout": "23",
            "explanation": "3 + 5 + 6 + 9 = 23. 10 itself is excluded.",
        },
        {
            "stdin": "16\n",
            "stdout": "60",
            "explanation": (
                "3 + 5 + 6 + 9 + 10 + 12 + 15 = 60. 15 is divisible by both 3 and 5 "
                "but is added only once."
            ),
        },
    ],
    "criteria": [
        "Exclude n itself",
        "Count a multiple of 15 exactly once",
        "Accumulate in a 64-bit integer",
    ],
    "io": {
        "mode": "tokens",
        "function": "sum_multiples",
        "todo": "return the sum of the values below n divisible by 3 or 5",
        "reads": [{"name": "n", "type": "int"}],
        "args": ["n"],
        "returns": "long",
    },
    "reference": r"""
import sys

def main():
    n = int(sys.stdin.read().split()[0])
    total = 0
    for value in range(1, n):
        if value % 3 == 0 or value % 5 == 0:
            total += value
    print(total)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: n = 10", "stdin": "10\n", "hidden": False},
        {"name": "sample: n = 16", "stdin": "16\n", "hidden": False},
        {"name": "hidden: n = 1 (empty range)", "stdin": "1\n", "hidden": True},
        {"name": "hidden: n = 15 excludes 15", "stdin": "15\n", "hidden": True},
        {"name": "hidden: n = 17 includes 15", "stdin": "17\n", "hidden": True},
        {"name": "hidden: n = 1000", "stdin": "1000\n", "hidden": True},
        {"name": "hidden: scale, needs 64 bits", "stdin": "1000000\n", "hidden": True},
    ],
    "wrong": [
        # Inclusive bound.
        r"""
import sys
n = int(sys.stdin.read().split()[0])
print(sum(v for v in range(1, n + 1) if v % 3 == 0 or v % 5 == 0))
""".lstrip(),
        # Double counts the multiples of 15.
        r"""
import sys
n = int(sys.stdin.read().split()[0])
print(sum(v for v in range(1, n) if v % 3 == 0) + sum(v for v in range(1, n) if v % 5 == 0))
""".lstrip(),
        # Multiples of 3 only.
        r"""
import sys
n = int(sys.stdin.read().split()[0])
print(sum(v for v in range(1, n) if v % 3 == 0))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  06 · Functions                                                             #
# --------------------------------------------------------------------------- #

FIBONACCI: dict[str, Any] = {
    "key": "fibonacci",
    "difficulty": 3,
    "estimated_minutes": 18,
    "title": "Nth Fibonacci Number",
    "statement": (
        "Read n and print the nth Fibonacci number, where F(1) = 1, "
        "F(2) = 1 and F(k) = F(k-1) + F(k-2).\n\n"
        "Write it as a function that takes n and returns the value, then call "
        "that function from your input-reading code — the separation between "
        "'read the input' and 'compute the answer' is the habit this problem "
        "is really teaching.\n\n"
        "Note the indexing: F(1) and F(2) are both 1, so F(7) is 13, not 8. "
        "Note also that the naive doubly-recursive version makes about F(n) "
        "calls, which for n = 90 is more calls than there are seconds in the "
        "age of the universe. Iterate, or memoise."
    ),
    "constraints": [
        "1 <= n <= 90",
        "F(1) = F(2) = 1",
        "F(90) fits in a signed 64-bit integer but overflows a 32-bit one",
    ],
    "input_format": "Line 1: a single integer n.",
    "output_format": "A single integer: F(n).",
    "examples": [
        {
            "stdin": "1\n",
            "stdout": "1",
            "explanation": "F(1) is defined as 1.",
        },
        {
            "stdin": "7\n",
            "stdout": "13",
            "explanation": "The sequence runs 1, 1, 2, 3, 5, 8, 13, so F(7) = 13.",
        },
    ],
    "criteria": [
        "Use the 1-based indexing given, so F(2) = 1",
        "Return the answer from a function rather than printing inside it",
        "Use a 64-bit type; F(90) overflows 32 bits",
        "Do not use naive double recursion — it cannot finish n = 90",
    ],
    "io": {
        "mode": "tokens",
        "function": "fibonacci",
        "todo": "return the nth Fibonacci number, with F(1) = F(2) = 1",
        "reads": [{"name": "n", "type": "int"}],
        "args": ["n"],
        "returns": "long",
    },
    "reference": r"""
import sys

def fibonacci(n):
    a, b = 1, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return a

def main():
    print(fibonacci(int(sys.stdin.read().split()[0])))

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: n = 1", "stdin": "1\n", "hidden": False},
        {"name": "sample: n = 7", "stdin": "7\n", "hidden": False},
        {"name": "hidden: n = 2", "stdin": "2\n", "hidden": True},
        {"name": "hidden: n = 10", "stdin": "10\n", "hidden": True},
        {"name": "hidden: n = 50", "stdin": "50\n", "hidden": True},
        {"name": "hidden: n = 90 overflows 32 bits", "stdin": "90\n", "hidden": True},
    ],
    "wrong": [
        # Off by one: iterates n-1 times from the 0, 1 seed, so it prints F(n-1).
        r"""
import sys
n = int(sys.stdin.read().split()[0])
a, b = 0, 1
for _ in range(n - 1):
    a, b = b, a + b
print(a)
""".lstrip(),
        # Naive recursion: correct, but cannot finish n = 90.
        r"""
import sys
def fib(n):
    if n <= 2:
        return 1
    return fib(n - 1) + fib(n - 2)
print(fib(int(sys.stdin.read().split()[0])))
""".lstrip(),
        # Echoes n.
        "import sys\nprint(int(sys.stdin.read().split()[0]))\n",
    ],
}


# --------------------------------------------------------------------------- #
#  07 · Strings                                                               #
# --------------------------------------------------------------------------- #

REVERSE_STRING: dict[str, Any] = {
    "key": "reverse-string",
    "difficulty": 2,
    "estimated_minutes": 15,
    "title": "Reverse a String",
    "statement": (
        "Read one line of text and print it with its characters in reverse "
        "order.\n\n"
        "Characters, not words: `ab cd` becomes `dc ba`. The line may contain "
        "spaces, digits and punctuation, and it is read in full — you cannot "
        "stop at the first space."
    ),
    "constraints": [
        "1 <= length of the line <= 200000",
        "The line contains printable ASCII characters and may include spaces",
        "The line has no leading or trailing whitespace",
    ],
    "input_format": "Line 1: the text to reverse.",
    "output_format": "One line: the same characters in reverse order.",
    "examples": [
        {
            "stdin": "hello\n",
            "stdout": "olleh",
            "explanation": "The five characters are emitted last to first.",
        },
        {
            "stdin": "ab cd\n",
            "stdout": "dc ba",
            "explanation": (
                "Every character moves, including the space, so the word order "
                "appears to flip as a side effect of reversing characters."
            ),
        },
    ],
    "criteria": [
        "Reverse characters, not words",
        "Read the whole line, including spaces",
        "Print no extra whitespace",
    ],
    "io": {
        "mode": "line",
        "function": "print_reversed",
        "todo": "print the characters of s in reverse order",
        "reads": [{"name": "s", "type": "string"}],
        "args": ["s"],
        "returns": "void",
    },
    "reference": r"""
import sys

def main():
    s = sys.stdin.readline().rstrip("\n")
    print(s[::-1])

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: hello", "stdin": "hello\n", "hidden": False},
        {"name": "sample: two words", "stdin": "ab cd\n", "hidden": False},
        {"name": "hidden: single character", "stdin": "z\n", "hidden": True},
        {"name": "hidden: palindrome", "stdin": "racecar\n", "hidden": True},
        {"name": "hidden: digits and punctuation", "stdin": "a1b2, c3!\n", "hidden": True},
        {"name": "hidden: repeated spaces", "stdin": "a  b   c\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": _text_case(21, 200000, "abcdefghij klmnop"),
            "hidden": True,
        },
    ],
    "wrong": [
        # Prints the line unchanged: passes the palindrome case only.
        "import sys\nprint(sys.stdin.readline().rstrip('\\n'))\n",
        # Reverses the word order instead of the characters.
        "import sys\nprint(' '.join(reversed(sys.stdin.readline().rstrip('\\n').split(' '))))\n",
        # Sorts the characters.
        "import sys\nprint(''.join(sorted(sys.stdin.readline().rstrip('\\n'))))\n",
    ],
}


COUNT_VOWELS: dict[str, Any] = {
    "key": "count-vowels",
    "difficulty": 2,
    "estimated_minutes": 15,
    "title": "Count Vowels",
    "statement": (
        "Read one line of text and print how many of its characters are "
        "vowels.\n\n"
        "The vowels are a, e, i, o and u, in either case: `A` counts and `E` "
        "counts. `y` does not. Everything else — consonants, spaces, digits, "
        "punctuation — is ignored."
    ),
    "constraints": [
        "1 <= length of the line <= 200000",
        "The line contains printable ASCII characters and may include spaces",
        "Both upper and lower case vowels count; 'y' is not a vowel",
    ],
    "input_format": "Line 1: the text to scan.",
    "output_format": "A single integer: the number of vowels.",
    "examples": [
        {
            "stdin": "Education\n",
            "stdout": "5",
            "explanation": "E, u, a, i and o are vowels; d, c, t and n are not.",
        },
        {
            "stdin": "rhythm myths\n",
            "stdout": "0",
            "explanation": "There is no a, e, i, o or u here — 'y' is not counted.",
        },
    ],
    "criteria": [
        "Count both upper and lower case vowels",
        "Do not count 'y'",
        "Walk the whole line, spaces included",
    ],
    "io": {
        "mode": "line",
        "function": "count_vowels",
        "todo": "return the number of vowels (aeiou, either case) in s",
        "reads": [{"name": "s", "type": "string"}],
        "args": ["s"],
        "returns": "int",
    },
    "reference": r"""
import sys

def main():
    s = sys.stdin.readline().rstrip("\n")
    print(sum(1 for ch in s if ch in "aeiouAEIOU"))

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: Education", "stdin": "Education\n", "hidden": False},
        {"name": "sample: no vowels", "stdin": "rhythm myths\n", "hidden": False},
        {"name": "hidden: all vowels both cases", "stdin": "AEIOU aeiou\n", "hidden": True},
        {"name": "hidden: y is not a vowel", "stdin": "yyy y\n", "hidden": True},
        {"name": "hidden: single vowel", "stdin": "a\n", "hidden": True},
        {"name": "hidden: digits and punctuation", "stdin": "a1e2i3o4u5!\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": _text_case(22, 200000, "aeiouAEIOUbcdfgxyz "),
            "hidden": True,
        },
    ],
    "wrong": [
        # Lower case only.
        "import sys\nprint(sum(1 for c in sys.stdin.readline().rstrip('\\n') if c in 'aeiou'))\n",
        # Counts 'y' as a vowel.
        "import sys\nprint(sum(1 for c in sys.stdin.readline().rstrip('\\n') if c in 'aeiouyAEIOUY'))\n",
        # Counts everything that is not a vowel.
        "import sys\nprint(sum(1 for c in sys.stdin.readline().rstrip('\\n') if c not in 'aeiouAEIOU'))\n",
        # Constant.
        "print(5)\n",
    ],
}


# --------------------------------------------------------------------------- #
#  08 · 1-D arrays                                                            #
# --------------------------------------------------------------------------- #

SECOND_LARGEST: dict[str, Any] = {
    "key": "second-largest",
    "difficulty": 3,
    "estimated_minutes": 18,
    "title": "Second Largest Distinct Value",
    "statement": (
        "Read n values into an array and print the second largest *distinct* "
        "value. If the array holds only one distinct value, print that "
        "value.\n\n"
        "Distinct is the whole difficulty. In `3 1 4 4 5` the largest is 5 and "
        "the second largest distinct value is 4 — sorting and taking the "
        "second-from-last element would give 4 here by luck, but gives 4 again "
        "for `5 5 4`, where the answer is 4, and gives 7 for `7 7 7 7`, where "
        "sorting hands you 7 for the wrong reason. Track the two best distinct "
        "values in one pass instead."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= a[i] <= 1000000000",
        "If every value is equal, print that value",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": "A single integer: the second largest distinct value.",
    "examples": [
        {
            "stdin": "5\n3 1 4 4 5\n",
            "stdout": "4",
            "explanation": (
                "The distinct values are 1, 3, 4, 5; the largest is 5 and the second "
                "largest is 4."
            ),
        },
        {
            "stdin": "4\n7 7 7 7\n",
            "stdout": "7",
            "explanation": "There is only one distinct value, so it is printed.",
        },
    ],
    "criteria": [
        "Ignore duplicates when choosing the second largest",
        "Handle n = 1 and an array of identical values without crashing",
        "One pass over the array is enough",
    ],
    "io": {
        "mode": "tokens",
        "function": "second_largest",
        "todo": (
            "return the second largest distinct value, or the only value when the "
            "array has just one distinct value"
        ),
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
    best = None
    second = None
    for token in data[1:1 + n]:
        value = int(token)
        if best is None or value > best:
            if best is not None:
                second = best
            best = value
        elif value != best and (second is None or value > second):
            second = value
    print(best if second is None else second)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: duplicates in the middle", "stdin": "5\n3 1 4 4 5\n", "hidden": False},
        {"name": "sample: all identical", "stdin": "4\n7 7 7 7\n", "hidden": False},
        {"name": "hidden: two values", "stdin": "2\n1 2\n", "hidden": True},
        {"name": "hidden: duplicated maximum", "stdin": "5\n5 5 4 1 1\n", "hidden": True},
        {"name": "hidden: negatives", "stdin": "4\n-1 -2 -2 -5\n", "hidden": True},
        {"name": "hidden: single element", "stdin": "1\n9\n", "hidden": True},
        {"name": "hidden: maximum at the end", "stdin": "6\n1 2 3 4 5 6\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _array_case(31, 200000, -1000000000, 1000000000), "hidden": True},
    ],
    "wrong": [
        # Second from last after sorting: wrong whenever the maximum repeats.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
arr = sorted(int(x) for x in d[1:1 + n])
print(arr[-2] if n >= 2 else arr[-1])
""".lstrip(),
        # Deduplicates but crashes on a single distinct value.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
print(sorted(set(int(x) for x in d[1:1 + n]))[-2])
""".lstrip(),
        # Prints the maximum.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
print(max(int(x) for x in d[1:1 + n]))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  09 · 2-D arrays and matrices                                               #
# --------------------------------------------------------------------------- #

MATRIX_TRANSPOSE: dict[str, Any] = {
    "key": "matrix-transpose",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Transpose a Matrix",
    "statement": (
        "Read an r x c matrix and print its transpose: a c x r matrix whose "
        "row i is column i of the input.\n\n"
        "Only r and c are given; the r * c values follow, row by row. The "
        "matrix is not necessarily square, so the output has a different shape "
        "from the input and an in-place swap of a[i][j] with a[j][i] will not "
        "work."
    ),
    "constraints": [
        "1 <= r, c <= 300",
        "-1000000000 <= a[i][j] <= 1000000000",
        "The output has c rows of r values",
    ],
    "input_format": (
        "Line 1: r and c.\n"
        "Then r lines of c space-separated integers (the values may also be "
        "read as one stream of r * c numbers)."
    ),
    "output_format": "c lines of r space-separated integers: the transpose.",
    "examples": [
        {
            "stdin": "2 3\n1 2 3\n4 5 6\n",
            "stdout": "1 4\n2 5\n3 6",
            "explanation": (
                "Column 0 of the input is (1, 4), which becomes row 0 of the output; "
                "the 2 x 3 input transposes to a 3 x 2 output."
            ),
        },
        {
            "stdin": "1 1\n-5\n",
            "stdout": "-5",
            "explanation": "A 1 x 1 matrix is its own transpose.",
        },
    ],
    "criteria": [
        "Handle non-square matrices, where the output shape differs from the input",
        "Emit c rows of r values",
        "Index the flat input correctly: value (i, j) sits at i * c + j",
    ],
    "io": {
        "mode": "tokens",
        "function": "print_transpose",
        "todo": "print the c x r transpose of the r x c matrix held in grid",
        "reads": [
            {"name": "r", "type": "int"},
            {"name": "c", "type": "int"},
            {"name": "k", "type": "int", "value": "r * c"},
            {"name": "grid", "type": "long", "count": "k"},
        ],
        "args": ["grid", "r", "c"],
        "returns": "void",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    r = int(data[0])
    c = int(data[1])
    grid = [int(x) for x in data[2:2 + r * c]]
    out = []
    for j in range(c):
        out.append(" ".join(str(grid[i * c + j]) for i in range(r)))
    sys.stdout.write("\n".join(out) + "\n")

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: 2 x 3", "stdin": "2 3\n1 2 3\n4 5 6\n", "hidden": False, "match": "tokens"},
        {"name": "sample: 1 x 1", "stdin": "1 1\n-5\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: 3 x 2", "stdin": "3 2\n1 2\n3 4\n5 6\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: 3 x 3 not symmetric",
            "stdin": "3 3\n1 2 3\n4 5 6\n7 8 9\n",
            "hidden": True,
            "match": "tokens",
        },
        {"name": "hidden: single row", "stdin": "1 4\n1 -2 3 -4\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: single column", "stdin": "4 1\n1 -2 3 -4\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: scale 200 x 300",
            "stdin": _grid_case(41, 200, 300, -1000000000, 1000000000),
            "hidden": True,
            "match": "tokens",
        },
    ],
    "wrong": [
        # Echoes the matrix.
        r"""
import sys
d = sys.stdin.buffer.read().split()
r = int(d[0]); c = int(d[1])
g = [int(x) for x in d[2:2 + r * c]]
for i in range(r):
    print(" ".join(str(g[i * c + j]) for j in range(c)))
""".lstrip(),
        # Assumes a square matrix, so it reads out of range or emits the wrong shape.
        r"""
import sys
d = sys.stdin.buffer.read().split()
r = int(d[0]); c = int(d[1])
g = [int(x) for x in d[2:2 + r * c]]
for i in range(r):
    print(" ".join(str(g[j * r + i]) for j in range(c)))
""".lstrip(),
        # Transposes, but emits each output row reversed.
        r"""
import sys
d = sys.stdin.buffer.read().split()
r = int(d[0]); c = int(d[1])
g = [int(x) for x in d[2:2 + r * c]]
for j in range(c):
    print(" ".join(str(g[i * c + j]) for i in range(r - 1, -1, -1)))
""".lstrip(),
    ],
}


MAX_ROW_SUM: dict[str, Any] = {
    "key": "max-row-sum",
    "difficulty": 3,
    "estimated_minutes": 18,
    "title": "Largest Row Sum",
    "statement": (
        "Read an r x c matrix and print the largest sum of any single row.\n\n"
        "Rows, not columns and not the whole matrix. Values may be negative, "
        "so the answer can be negative and starting an accumulator at 0 is a "
        "bug."
    ),
    "constraints": [
        "1 <= r, c <= 300",
        "-1000000000 <= a[i][j] <= 1000000000",
        "A row sum reaches 3 * 10^11, so it needs a 64-bit type",
    ],
    "input_format": (
        "Line 1: r and c.\n"
        "Then r lines of c space-separated integers (the values may also be "
        "read as one stream of r * c numbers)."
    ),
    "output_format": "A single integer: the largest row sum.",
    "examples": [
        {
            "stdin": "2 3\n1 2 3\n-4 5 6\n",
            "stdout": "7",
            "explanation": "The row sums are 6 and 7, so the answer is 7.",
        },
        {
            "stdin": "2 2\n-5 -6\n-1 -2\n",
            "stdout": "-3",
            "explanation": (
                "Both rows are negative; the largest sum is -3, so an accumulator "
                "initialised to 0 would wrongly answer 0."
            ),
        },
    ],
    "criteria": [
        "Compare row sums, not columns or individual values",
        "Handle an all-negative matrix, where the answer is negative",
        "Accumulate in a 64-bit integer",
    ],
    "io": {
        "mode": "tokens",
        "function": "max_row_sum",
        "todo": "return the largest sum of any row of the r x c matrix in grid",
        "reads": [
            {"name": "r", "type": "int"},
            {"name": "c", "type": "int"},
            {"name": "k", "type": "int", "value": "r * c"},
            {"name": "grid", "type": "long", "count": "k"},
        ],
        "args": ["grid", "r", "c"],
        "returns": "long",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    r = int(data[0])
    c = int(data[1])
    grid = [int(x) for x in data[2:2 + r * c]]
    best = None
    for i in range(r):
        total = sum(grid[i * c:i * c + c])
        if best is None or total > best:
            best = total
    print(best)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: mixed signs", "stdin": "2 3\n1 2 3\n-4 5 6\n", "hidden": False},
        {"name": "sample: all negative", "stdin": "2 2\n-5 -6\n-1 -2\n", "hidden": False},
        {"name": "hidden: 1 x 1", "stdin": "1 1\n-5\n", "hidden": True},
        {
            "name": "hidden: best column is not the best row",
            "stdin": "2 2\n10 -20\n9 -1\n",
            "hidden": True,
        },
        {"name": "hidden: single column", "stdin": "3 1\n-7\n-2\n-9\n", "hidden": True},
        {"name": "hidden: best row is the first", "stdin": "3 3\n9 9 9\n1 1 1\n2 2 2\n", "hidden": True},
        {
            "name": "hidden: scale 300 x 300",
            "stdin": _grid_case(42, 300, 300, -1000000000, 1000000000),
            "hidden": True,
        },
    ],
    "wrong": [
        # Largest column sum.
        r"""
import sys
d = sys.stdin.buffer.read().split()
r = int(d[0]); c = int(d[1])
g = [int(x) for x in d[2:2 + r * c]]
print(max(sum(g[i * c + j] for i in range(r)) for j in range(c)))
""".lstrip(),
        # Largest single element.
        r"""
import sys
d = sys.stdin.buffer.read().split()
r = int(d[0]); c = int(d[1])
print(max(int(x) for x in d[2:2 + r * c]))
""".lstrip(),
        # Accumulator starts at 0, so an all-negative matrix answers 0.
        r"""
import sys
d = sys.stdin.buffer.read().split()
r = int(d[0]); c = int(d[1])
g = [int(x) for x in d[2:2 + r * c]]
best = 0
for i in range(r):
    total = sum(g[i * c:i * c + c])
    if total > best:
        best = total
print(best)
""".lstrip(),
        # Sums the whole matrix.
        r"""
import sys
d = sys.stdin.buffer.read().split()
r = int(d[0]); c = int(d[1])
print(sum(int(x) for x in d[2:2 + r * c]))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  10 · Records: structs (C), classes (C++/Java), used to model a row of data #
# --------------------------------------------------------------------------- #

TOP_SCORER: dict[str, Any] = {
    "key": "top-scorer",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Top Scorer",
    "statement": (
        "n students each have an id and a score. Print the id of the student "
        "with the highest score; if several tie, print the smallest such id.\n\n"
        "The ids arrive on one line and the scores on the next, so student i "
        "is the pair (ids[i], scores[i]). Model that pairing explicitly with "
        "the record type your language gives you rather than juggling two "
        "loose arrays — that is the point of the exercise."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "1 <= id <= 1000000000, and the ids are distinct",
        "-1000000000 <= score <= 1000000000",
        "On a tie, the smallest id wins",
    ],
    "input_format": (
        "Line 1: n.\n"
        "Line 2: n space-separated ids.\n"
        "Line 3: n space-separated scores."
    ),
    "output_format": "A single integer: the id of the top scorer.",
    "examples": [
        {
            "stdin": "3\n101 102 103\n50 90 90\n",
            "stdout": "102",
            "explanation": (
                "Students 102 and 103 tie on 90, so the smaller id, 102, is printed."
            ),
        },
        {
            "stdin": "3\n300 100 200\n5 5 1\n",
            "stdout": "100",
            "explanation": (
                "300 and 100 tie on 5. The smallest id wins even though it appears "
                "second, so 'first seen wins' is not the rule."
            ),
        },
    ],
    "criteria": [
        "Print the id, not the score and not the index",
        "Break ties by smallest id, independent of input order",
        "Handle negative scores and n = 1",
    ],
    "io": {
        "mode": "tokens",
        "function": "top_scorer",
        "todo": (
            "return the id whose score is highest, breaking ties by the smaller id"
        ),
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "ids", "type": "long", "count": "n"},
            {"name": "scores", "type": "long", "count": "n"},
        ],
        "args": ["ids", "scores"],
        "returns": "long",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    ids = [int(x) for x in data[1:1 + n]]
    scores = [int(x) for x in data[1 + n:1 + 2 * n]]
    best_id = ids[0]
    best_score = scores[0]
    for index in range(1, n):
        score = scores[index]
        student = ids[index]
        if score > best_score or (score == best_score and student < best_id):
            best_score = score
            best_id = student
    print(best_id)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: tie on 90", "stdin": "3\n101 102 103\n50 90 90\n", "hidden": False},
        {"name": "sample: smaller id appears later", "stdin": "3\n300 100 200\n5 5 1\n", "hidden": False},
        {"name": "hidden: single student", "stdin": "1\n7\n0\n", "hidden": True},
        {"name": "hidden: negative scores", "stdin": "3\n5 6 7\n-9 -2 -30\n", "hidden": True},
        {"name": "hidden: all tied", "stdin": "4\n9 4 6 2\n3 3 3 3\n", "hidden": True},
        {"name": "hidden: winner is last", "stdin": "4\n1 2 3 4\n1 2 3 4\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": (
                "200000\n"
                + " ".join(str(i + 1) for i in range(200000))
                + "\n"
                + " ".join(map(str, _values(51, 200000, -1000, 1000)))
                + "\n"
            ),
            "hidden": True,
        },
    ],
    "wrong": [
        # Last maximum wins, so a tie picks the largest id.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
ids = [int(x) for x in d[1:1 + n]]
sc = [int(x) for x in d[1 + n:1 + 2 * n]]
best = 0
for i in range(n):
    if sc[i] >= sc[best]:
        best = i
print(ids[best])
""".lstrip(),
        # Prints the score instead of the id.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
sc = [int(x) for x in d[1 + n:1 + 2 * n]]
print(max(sc))
""".lstrip(),
        # Prints the index of the winner.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
sc = [int(x) for x in d[1 + n:1 + 2 * n]]
print(sc.index(max(sc)))
""".lstrip(),
        # Smallest id overall, ignoring the scores.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
print(min(int(x) for x in d[1:1 + n]))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  11 · Pointers and memory (C and C++ only)                                  #
# --------------------------------------------------------------------------- #

POINTER_STRIDE: dict[str, Any] = {
    "key": "pointer-stride",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Walk an Array With a Pointer",
    "statement": (
        "Read n values and a stride s, then print the sum of every sth "
        "element starting at the first: a[0] + a[s] + a[2s] + ... for as long "
        "as the index stays inside the array.\n\n"
        "Do it with a pointer rather than an index: take `const long long* p = "
        "arr`, add `s` to it each step, and stop before it runs past "
        "`arr + n`. Adding 1 to a `long long*` advances it by eight bytes, not "
        "one — pointer arithmetic counts elements, which is exactly why this "
        "works and why comparing pointers is a legitimate way to find the end."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "1 <= s <= n",
        "-1000000000 <= a[i] <= 1000000000",
        "The sum reaches 2 * 10^14, so it needs a 64-bit type",
        "Never dereference a pointer at or past arr + n",
    ],
    "input_format": "Line 1: n and s.\nLine 2: n space-separated integers.",
    "output_format": "A single integer: the strided sum.",
    "examples": [
        {
            "stdin": "5 2\n1 2 3 4 5\n",
            "stdout": "9",
            "explanation": (
                "Indices 0, 2 and 4 are visited: 1 + 3 + 5 = 9. Index 6 would be "
                "past the end, so the walk stops."
            ),
        },
        {
            "stdin": "4 1\n1 2 3 4\n",
            "stdout": "10",
            "explanation": "A stride of 1 visits every element, giving the whole sum.",
        },
    ],
    "criteria": [
        "Start at the first element, not at index s",
        "Stop before reading past the end of the array",
        "Accumulate in a 64-bit integer",
    ],
    "io": {
        "mode": "tokens",
        "function": "strided_sum",
        "todo": "return arr[0] + arr[s] + arr[2*s] + ... while the index is below n",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "s", "type": "int"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr", "s"],
        "returns": "long",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    s = int(data[1])
    arr = data[2:2 + n]
    total = 0
    index = 0
    while index < n:
        total += int(arr[index])
        index += s
    print(total)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: stride 2", "stdin": "5 2\n1 2 3 4 5\n", "hidden": False},
        {"name": "sample: stride 1", "stdin": "4 1\n1 2 3 4\n", "hidden": False},
        {"name": "hidden: stride equals n", "stdin": "4 4\n7 1 1 1\n", "hidden": True},
        {"name": "hidden: single element", "stdin": "1 1\n-6\n", "hidden": True},
        {"name": "hidden: negatives", "stdin": "6 3\n-1 5 5 -2 5 5\n", "hidden": True},
        {"name": "hidden: stride just over half", "stdin": "5 3\n1 1 1 1 9\n", "hidden": True},
        {
            "name": "hidden: scale, needs 64 bits",
            "stdin": "200000 1\n" + " ".join(["1000000000"] * 200000) + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Sums the whole array, ignoring the stride.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0])
print(sum(int(x) for x in d[2:2 + n]))
""".lstrip(),
        # Starts at index s instead of 0.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0]); s = int(d[1])
arr = [int(x) for x in d[2:2 + n]]
total = 0
i = s
while i < n:
    total += arr[i]
    i += s
print(total)
""".lstrip(),
        # Assumes the walk must finish on the last element, so it adds it again.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0]); s = int(d[1])
arr = [int(x) for x in d[2:2 + n]]
total = 0
i = 0
while i < n:
    total += arr[i]
    i += s
total += arr[n - 1]
print(total)
""".lstrip(),
        # Divides instead of striding: right count of terms, wrong terms.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0]); s = int(d[1])
arr = [int(x) for x in d[2:2 + n]]
print(sum(arr[:(n + s - 1) // s]))
""".lstrip(),
    ],
}


DYNAMIC_FILTER: dict[str, Any] = {
    "key": "dynamic-filter",
    "difficulty": 3,
    "estimated_minutes": 22,
    "title": "Filter Into a Second Buffer",
    "statement": (
        "Read n values and a threshold x. Print how many values are strictly "
        "greater than x, then those values on the next line, in their original "
        "order.\n\n"
        "You do not know the answer's size until you have looked, which is the "
        "situation dynamic storage exists for: count first and allocate "
        "exactly, or grow as you go. If nothing qualifies, print 0 and leave "
        "the second line empty. Whatever you allocate, release it."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= a[i], x <= 1000000000",
        "Strictly greater than x: a value equal to x is excluded",
        "Preserve the input order of the kept values",
    ],
    "input_format": "Line 1: n and x.\nLine 2: n space-separated integers.",
    "output_format": (
        "Line 1: the count of values greater than x.\n"
        "Line 2: those values, space-separated, in input order (an empty line "
        "when the count is 0)."
    ),
    "examples": [
        {
            "stdin": "5 2\n1 5 2 7 3\n",
            "stdout": "3\n5 7 3",
            "explanation": (
                "5, 7 and 3 exceed 2. The 2 itself is not kept, because the test is "
                "strict."
            ),
        },
        {
            "stdin": "3 10\n1 2 3\n",
            "stdout": "0",
            "explanation": "Nothing exceeds 10, so the count is 0 and no values follow.",
        },
    ],
    "criteria": [
        "Print the count before the values",
        "Exclude values equal to x",
        "Keep the input order",
        "Free anything you allocate",
    ],
    "io": {
        "mode": "tokens",
        "function": "print_greater",
        "todo": "print how many values exceed x, then those values in input order",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "x", "type": "long"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr", "x"],
        "returns": "void",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    x = int(data[1])
    kept = [int(t) for t in data[2:2 + n] if int(t) > x]
    out = [str(len(kept))]
    if kept:
        out.append(" ".join(map(str, kept)))
    sys.stdout.write("\n".join(out) + "\n")

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: three kept", "stdin": "5 2\n1 5 2 7 3\n", "hidden": False, "match": "tokens"},
        {"name": "sample: none kept", "stdin": "3 10\n1 2 3\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: all kept", "stdin": "4 0\n1 2 3 4\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: equality excluded", "stdin": "4 3\n3 3 4 3\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: negative threshold", "stdin": "5 -3\n-5 -3 -2 0 -9\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: single element kept", "stdin": "1 -1\n0\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: scale",
            "stdin": "200000 0\n" + " ".join(map(str, _values(61, 200000, -1000, 1000))) + "\n",
            "hidden": True,
            "match": "tokens",
        },
    ],
    "wrong": [
        # Uses >= instead of >.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0]); x = int(d[1])
kept = [int(t) for t in d[2:2 + n] if int(t) >= x]
print(len(kept))
if kept:
    print(" ".join(map(str, kept)))
""".lstrip(),
        # Omits the count line.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0]); x = int(d[1])
kept = [int(t) for t in d[2:2 + n] if int(t) > x]
if kept:
    print(" ".join(map(str, kept)))
""".lstrip(),
        # Sorts the kept values instead of preserving input order.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0]); x = int(d[1])
kept = sorted(int(t) for t in d[2:2 + n] if int(t) > x)
print(len(kept))
if kept:
    print(" ".join(map(str, kept)))
""".lstrip(),
        # Prints only the count.
        r"""
import sys
d = sys.stdin.buffer.read().split()
n = int(d[0]); x = int(d[1])
print(sum(1 for t in d[2:2 + n] if int(t) > x))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  Materialisation                                                            #
# --------------------------------------------------------------------------- #

COMMON_TASKS: tuple[dict[str, Any], ...] = (
    SUM_TWO,
    TRUNCATED_MEAN,
    BITWISE_TRIO,
    LEAP_YEAR,
    MULTIPLES_SUM,
    FIBONACCI,
    REVERSE_STRING,
    COUNT_VOWELS,
    SECOND_LARGEST,
    MATRIX_TRANSPOSE,
    MAX_ROW_SUM,
)


def materialise(
    tasks: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    *,
    prefix: str,
    language: str,
    skill_id: str,
    notes: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """Stamp task templates out as problems for one language.

    ``prefix`` becomes the slug prefix (``basics-c`` -> ``basics-c-sum-two``),
    ``language`` is the single language the problem is offered in, and ``notes``
    maps a task key to extra pass criteria phrased in that language's idiom.
    """
    notes = notes or {}
    problems: list[dict[str, Any]] = []
    for task in tasks:
        problem = {key: value for key, value in task.items() if key != "key"}
        problem["slug"] = f"{prefix}-{task['key']}"
        problem["skill_id"] = skill_id
        problem["languages"] = [language]
        problem["criteria"] = list(task["criteria"]) + list(notes.get(task["key"], []))
        problems.append(problem)
    return problems
