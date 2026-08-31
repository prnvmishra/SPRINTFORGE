"""Blind 75 problems, batch 1.

Split across files so the catalogue can grow without one unreadable module.
Each entry follows the contract in `docs/curriculum_authoring.md`: an `io`
spec drives starter generation for every language, `reference` derives the
expected outputs, and `wrong` solutions must be rejected by the case bank.

Adapting Blind 75 to a stdin/stdout judge
-----------------------------------------
The originals are function-signature problems whose answers are arrays,
strings or lists of lists. This judge compares one stream of text, so each
answer is serialised rather than reduced to a scalar:

* a sequence answer prints its length on line 1 and its values on line 2
  (Product of Array Except Self, Search in Rotated Sorted Array), following
  the convention the linked-list problems in batch 2 established, and is
  graded with ``match: "tokens"`` so whitespace layout never punishes a
  correct solution. The count prefix is what makes the empty answer
  unambiguous;
* a set answer prints a count and then one element per line, under an
  ordering the statement *mandates* so the answer is unique: 3Sum sorts each
  triplet and then sorts the triplets, and Group Anagrams sorts each group
  and then orders the groups by their first word. No correct solution can be
  punished for the order it happened to discover things in;
* Encode and Decode Strings has no canonical stdout for the encode half — the
  encoding is the learner's own choice — so the wire format is fixed and the
  decode half is judged, printing the recovered list exactly, including empty
  strings and payloads that contain the delimiter;
* a scalar stays a scalar where that is genuinely the answer: a count
  (Palindromic Substrings), a boolean, a maximum, or the length of a
  substring that is not itself unique (Minimum Window Substring, Longest
  Palindromic Substring).

Every output shape is spelled out in `input_format` / `output_format` and
demonstrated by at least two worked examples.
"""

from __future__ import annotations

import random
from typing import Any


# --------------------------------------------------------------------------- #
#  Deterministic input generation                                             #
# --------------------------------------------------------------------------- #


def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def _numbers(seed: int, n: int, lo: int, hi: int) -> list[int]:
    rng = _rng(seed)
    return [rng.randint(lo, hi) for _ in range(n)]


def _array_case(seed: int, n: int, lo: int, hi: int) -> str:
    return f"{n}\n{' '.join(map(str, _numbers(seed, n, lo, hi)))}\n"


def _distinct_case(seed: int, n: int, lo: int, hi: int) -> str:
    rng = _rng(seed)
    values = rng.sample(range(lo, hi), n)
    return f"{n}\n{' '.join(map(str, values))}\n"


def _two_sum_scale(seed: int, n: int) -> str:
    """One odd value plus n-1 distinct evens, so exactly one pair is valid.

    The target is odd, so any valid pair must use the single odd element; the
    evens are distinct, so its complement is unique. The pair sits at the very
    end of the array, which is what makes an O(n^2) scan pay full price.
    """
    rng = _rng(seed)
    evens = rng.sample(range(-499_999_998, 499_999_999, 2), n - 1)
    odd = 1
    partner = evens.pop()
    target = odd + partner
    values = evens + [odd, partner]
    return f"{n} {target}\n{' '.join(map(str, values))}\n"


def _product_except_self_scale(seed: int, n: int, zero_at: int | None = None) -> str:
    """A long array whose except-self products stay inside signed 64 bits.

    Mostly +/-1 with four larger factors, so the total product is around 10^12:
    comfortably past 32 bits (the answer really does need `long`) and nowhere
    near the 9.2 * 10^18 ceiling.
    """
    rng = _rng(seed)
    values = [rng.choice([-1, 1]) for _ in range(n)]
    for factor in (1000, -997, 991, -1009):
        values[rng.randrange(n)] = factor
    if zero_at is not None:
        values[zero_at] = 0
    return f"{n}\n{' '.join(map(str, values))}\n"


def _product_scale(seed: int, n: int) -> str:
    """Bounded magnitudes with a zero every 15 slots.

    The zeros keep every contiguous product inside signed 64 bits (9^14 is
    about 2.3e13) while leaving long runs of negatives for the min/max pair to
    handle.
    """
    rng = _rng(seed)
    values = []
    for index in range(n):
        if index % 15 == 14:
            values.append(0)
        else:
            v = rng.randint(-9, 9)
            values.append(v if v != 0 else 3)
    return f"{n}\n{' '.join(map(str, values))}\n"


def _rotated_case(seed: int, n: int, shift: int) -> str:
    rng = _rng(seed)
    values = sorted(rng.sample(range(-1_000_000_000, 1_000_000_000), n))
    rotated = values[shift:] + values[:shift]
    return rotated


def _rotated_min_scale(seed: int, n: int, shift: int) -> str:
    rotated = _rotated_case(seed, n, shift)
    return f"{n}\n{' '.join(map(str, rotated))}\n"


def _rotated_search_scale(seed: int, n: int, shift: int, q: int) -> str:
    """A rotated array of even values plus q queries, half of them guaranteed misses.

    Odd targets cannot occur in an all-even array, so half the queries force a
    scan-per-query solution to walk the whole array before giving up.
    """
    rng = _rng(seed)
    values = sorted(rng.sample(range(-500_000_000, 500_000_000, 2), n))
    rotated = values[shift:] + values[:shift]
    targets = []
    for i in range(q):
        if i % 2:
            targets.append(rotated[rng.randrange(n)])
        else:
            targets.append(rng.randrange(-499_999_999, 499_999_999, 2))
    return (
        f"{n} {q}\n"
        f"{' '.join(map(str, rotated))}\n"
        f"{' '.join(map(str, targets))}\n"
    )


def _random_string(seed: int, length: int, alphabet: str) -> str:
    rng = _rng(seed)
    return "".join(rng.choice(alphabet) for _ in range(length))


def _words_case(seed: int, count: int, word_length: int) -> str:
    """Many small anagram groups rather than a handful of huge ones.

    Each word is a shuffle of one of `count // 8` random letter multisets, so
    the answer has thousands of groups of a few words each — which exercises
    the ordering of the groups, not just the grouping itself.
    """
    rng = _rng(seed)
    bases = [
        "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(word_length))
        for _ in range(max(1, count // 8))
    ]
    words = []
    for _ in range(count):
        letters = list(rng.choice(bases))
        rng.shuffle(letters)
        words.append("".join(letters))
    return " ".join(words) + "\n"


def _brackets_case(seed: int, pairs: int) -> str:
    rng = _rng(seed)
    openers = "([{"
    closers = {"(": ")", "[": "]", "{": "}"}
    stack: list[str] = []
    out: list[str] = []
    for _ in range(pairs * 2):
        if stack and (len(stack) > 40 or rng.random() < 0.5):
            out.append(closers[stack.pop()])
        else:
            ch = rng.choice(openers)
            stack.append(ch)
            out.append(ch)
    while stack:
        out.append(closers[stack.pop()])
    return "".join(out) + "\n"


def _encoded_case(seed: int, count: int) -> str:
    """A length-prefixed blob whose payloads contain '#', digits and spaces."""
    rng = _rng(seed)
    alphabet = "ab#3 xy0"
    parts = []
    for index in range(count):
        if index % 17 == 0:
            payload = ""
        else:
            payload = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 90)))
        parts.append(f"{len(payload)}#{payload}")
    return "".join(parts) + "\n"


# --------------------------------------------------------------------------- #
#  01 · Two Sum                                                               #
# --------------------------------------------------------------------------- #

TWO_SUM = {
    "slug": "two-sum",
    "skill_id": "dsa_arrays",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Two Sum",
    "statement": (
        "Given an array of n integers and a target value, find the two "
        "different positions whose values add up to the target.\n\n"
        "Exactly one such pair exists in every input. Print both 0-based "
        "indices, smaller first, so the answer is unique.\n\n"
        "An element may not be paired with itself: the two positions must be "
        "different, even when the same value appears twice."
    ),
    "constraints": [
        "2 <= n <= 200000",
        "-1000000000 <= arr[i] <= 1000000000",
        "-2000000000 <= target <= 2000000000, which is outside the range of a "
        "32-bit int: use long long in C/C++ and long in Java for the target "
        "and for every sum you compute",
        "Exactly one valid pair exists",
        "An O(n) hash-map pass is expected; O(n^2) times out on hidden cases",
    ],
    "input_format": (
        "Line 1: n and target, separated by a space.\n"
        "Line 2: n space-separated integers."
    ),
    "output_format": (
        "A single line with the two 0-based indices of the pair, smaller index "
        "first, separated by a space. Whitespace layout is not graded."
    ),
    "examples": [
        {
            "stdin": "4 9\n2 7 11 15\n",
            "stdout": "0 1",
            "explanation": "arr[0] + arr[1] = 2 + 7 = 9, and 0 is printed before 1.",
        },
        {
            "stdin": "3 6\n3 2 4\n",
            "stdout": "1 2",
            "explanation": (
                "3 cannot be paired with itself, so the pair is arr[1] + arr[2] = 2 + 4."
            ),
        },
    ],
    "criteria": [
        "Print the smaller index first",
        "Never pair an element with itself",
        "Handle repeated values, where the same number occupies two positions",
        "Use a hash map for an O(n) single pass",
    ],
    "io": {
        "mode": "tokens",
        "function": "two_sum",
        "todo": (
            "find the unique pair summing to target and print both 0-based indices, "
            "smaller first (replace the single-value print in main)"
        ),
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "target", "type": "long"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr", "target"],
        "returns": "int",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    target = int(data[1])
    seen = {}
    for index in range(n):
        value = int(data[2 + index])
        need = target - value
        if need in seen:
            print(seen[need], index)
            return
        if value not in seen:
            seen[value] = index

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: 2 7 11 15", "stdin": "4 9\n2 7 11 15\n", "hidden": False, "match": "tokens"},
        {"name": "sample: no self pairing", "stdin": "3 6\n3 2 4\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: two equal values", "stdin": "2 6\n3 3\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: negatives", "stdin": "5 -8\n-3 4 -5 9 -1\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: pair at the end", "stdin": "6 30\n1 2 3 4 11 19\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: large magnitudes",
            "stdin": "3 2000000000\n1000000000 5 1000000000\n",
            "hidden": True,
            "match": "tokens",
        },
        {
            "name": "hidden: duplicates before the pair",
            "stdin": "5 7\n5 5 5 2 5\n",
            "hidden": True,
            "match": "tokens",
        },
        {"name": "hidden: scale", "stdin": _two_sum_scale(101, 200000), "hidden": True, "match": "tokens"},
    ],
    "wrong": [
        # O(n^2) brute force: right answer, cannot finish the scale case.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); target = int(data[1])
arr = [int(x) for x in data[2:2+n]]
for i in range(n):
    for j in range(i + 1, n):
        if arr[i] + arr[j] == target:
            print(i, j)
            sys.exit(0)
""".lstrip(),
        # Allows an element to pair with itself (3 + 3 when only one 3 exists).
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); target = int(data[1])
arr = [int(x) for x in data[2:2+n]]
values = {}
for i, v in enumerate(arr):
    values.setdefault(v, i)
for i, v in enumerate(arr):
    if target - v in values:
        print(i, values[target - v])
        break
""".lstrip(),
        # Prints the pair in the order it was discovered, so the larger index leads.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); target = int(data[1])
arr = [int(x) for x in data[2:2+n]]
seen = {}
for i, v in enumerate(arr):
    if target - v in seen:
        print(i, seen[target - v])
        break
    seen.setdefault(v, i)
""".lstrip(),
        # Sorts first, so the reported indices refer to the sorted copy.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); target = int(data[1])
arr = sorted(int(x) for x in data[2:2+n])
lo, hi = 0, n - 1
while lo < hi:
    s = arr[lo] + arr[hi]
    if s == target:
        print(lo, hi)
        break
    if s < target:
        lo += 1
    else:
        hi -= 1
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  02 · Contains Duplicate                                                    #
# --------------------------------------------------------------------------- #

CONTAINS_DUPLICATE = {
    "slug": "contains-duplicate",
    "skill_id": "dsa_arrays",
    "difficulty": 2,
    "estimated_minutes": 15,
    "title": "Contains Duplicate",
    "statement": (
        "Given an array of n integers, decide whether any value appears at "
        "least twice.\n\n"
        "Print 1 if some value is repeated and 0 if every value is distinct."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= arr[i] <= 1000000000",
        "The input is not sorted",
        "An O(n) hash set (or an O(n log n) sort) is expected; O(n^2) times out",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": "A single integer: 1 if a duplicate exists, otherwise 0.",
    "examples": [
        {
            "stdin": "4\n1 2 3 1\n",
            "stdout": "1",
            "explanation": "The value 1 appears at index 0 and index 3.",
        },
        {
            "stdin": "4\n1 2 3 4\n",
            "stdout": "0",
            "explanation": "Every value is distinct, so the answer is 0.",
        },
    ],
    "criteria": [
        "Print exactly 1 or 0",
        "Do not assume the array is sorted",
        "Handle n = 1, which can never contain a duplicate",
    ],
    "io": {
        "mode": "tokens",
        "function": "contains_duplicate",
        "todo": "return 1 if any value appears at least twice, otherwise 0",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr"],
        "returns": "int",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    arr = data[1:1 + n]
    print(1 if len(set(arr)) != n else 0)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: has duplicate", "stdin": "4\n1 2 3 1\n", "hidden": False},
        {"name": "sample: all distinct", "stdin": "4\n1 2 3 4\n", "hidden": False},
        {"name": "hidden: single element", "stdin": "1\n7\n", "hidden": True},
        {"name": "hidden: two zeros", "stdin": "2\n0 0\n", "hidden": True},
        {"name": "hidden: duplicate far apart", "stdin": "6\n5 1 2 3 4 5\n", "hidden": True},
        {"name": "hidden: negatives repeat", "stdin": "5\n-3 -1 -2 -3 0\n", "hidden": True},
        {"name": "hidden: all identical", "stdin": "5\n9 9 9 9 9\n", "hidden": True},
        # All distinct, so an O(n^2) scan never short-circuits.
        {"name": "hidden: scale", "stdin": _distinct_case(211, 200000, -10**9, 10**9), "hidden": True},
    ],
    "wrong": [
        # O(n^2) pairwise comparison.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
found = 0
for i in range(n):
    for j in range(i + 1, n):
        if arr[i] == arr[j]:
            found = 1
            break
    if found:
        break
print(found)
""".lstrip(),
        # Only compares neighbours, without sorting first.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
print(1 if any(arr[i] == arr[i+1] for i in range(n - 1)) else 0)
""".lstrip(),
        # Compares sums instead of membership: zeros (and cancelling values) slip through.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
print(1 if sum(arr) != sum(set(arr)) else 0)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  03 · Product of Array Except Self                                          #
# --------------------------------------------------------------------------- #

PRODUCT_EXCEPT_SELF = {
    "slug": "product-except-self",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Product of Array Except Self",
    "statement": (
        "For each position i, let out[i] be the product of every element of "
        "the array except arr[i]. The product of an empty set of elements is "
        "1, so for n = 1 the answer is the single value 1.\n\n"
        "Print the whole out array.\n\n"
        "Division is not available: the array may contain zeros, and dividing "
        "the total product by arr[i] breaks the moment one does."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= arr[i] <= 1000000000",
        "Zeros are common in the hidden cases, including inputs with two zeros",
        "It is guaranteed that |out[i]| <= 10^15: far past what a 32-bit int "
        "holds, so use long long in C/C++ and long in Java, and comfortably "
        "inside the exact integer range of every supported language",
        "An O(n) prefix/suffix pass with O(1) extra space beyond the answer is "
        "expected; O(n^2) times out on hidden cases",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": (
        "Line 1: n, the number of values in the answer.\n"
        "Line 2: out[0] .. out[n-1] separated by single spaces. Whitespace "
        "layout is not graded."
    ),
    "examples": [
        {
            "stdin": "4\n1 2 3 4\n",
            "stdout": "4\n24 12 8 6",
            "explanation": (
                "out[0] = 2*3*4 = 24, out[1] = 1*3*4 = 12, out[2] = 1*2*4 = 8 and "
                "out[3] = 1*2*3 = 6."
            ),
        },
        {
            "stdin": "4\n-1 1 0 -3\n",
            "stdout": "4\n0 0 3 0",
            "explanation": (
                "Every product except the one at the zero itself contains that zero, "
                "and out[2] = -1 * 1 * -3 = 3."
            ),
        },
    ],
    "criteria": [
        "Handle one zero, and handle two or more zeros (every output is then 0)",
        "Never divide by an element",
        "Print 1 for the single-element array",
        "Run in O(n) with prefix and suffix products",
    ],
    "io": {
        "mode": "tokens",
        "function": "product_except_self",
        "todo": (
            "compute the except-self product for every position, then print n and the "
            "n values (replace the single-value print in main)"
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
    arr = [int(x) for x in data[1:1 + n]]
    out = [1] * n
    prefix = 1
    for i in range(n):
        out[i] = prefix
        prefix *= arr[i]
    suffix = 1
    for i in range(n - 1, -1, -1):
        out[i] *= suffix
        suffix *= arr[i]
    print(n)
    print(' '.join(map(str, out)))

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: 1 2 3 4", "stdin": "4\n1 2 3 4\n", "hidden": False, "match": "tokens"},
        {"name": "sample: one zero", "stdin": "4\n-1 1 0 -3\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: single element", "stdin": "1\n5\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: two zeros", "stdin": "5\n2 0 4 0 6\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: all negative", "stdin": "4\n-2 -3 -4 -5\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: mixed signs", "stdin": "3\n-1 1 1\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: needs 64 bits",
            "stdin": "3\n1000000 -1000000 999999\n",
            "hidden": True,
            "match": "tokens",
        },
        {"name": "hidden: scale", "stdin": _product_except_self_scale(307, 200000), "hidden": True, "match": "tokens"},
        {
            "name": "hidden: scale with a zero",
            "stdin": _product_except_self_scale(311, 200000, zero_at=98_765),
            "hidden": True,
            "match": "tokens",
        },
    ],
    "wrong": [
        # Divides the total product by each element: wrong wherever a zero sits
        # (and it crashes outright on the division by zero).
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
total = 1
for v in arr:
    total *= v
out = [total // v for v in arr]
print(n)
print(' '.join(map(str, out)))
""".lstrip(),
        # Special-cases a single zero but still gets two zeros wrong: it divides
        # the product of the non-zero elements, so every position looks non-zero.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
zeros = arr.count(0)
product = 1
for v in arr:
    if v != 0:
        product *= v
out = []
for v in arr:
    if v == 0:
        out.append(product)
    elif zeros:
        out.append(0)
    else:
        out.append(product // v)
print(n)
print(' '.join(map(str, out)))
""".lstrip(),
        # Off-by-one: the prefix includes arr[i] itself.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
out = [1] * n
prefix = 1
for i in range(n):
    prefix *= arr[i]
    out[i] = prefix
suffix = 1
for i in range(n - 1, -1, -1):
    out[i] *= suffix
    suffix *= arr[i]
print(n)
print(' '.join(map(str, out)))
""".lstrip(),
        # O(n^2): correct but cannot finish the scale case.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
out = []
for i in range(n):
    p = 1
    for j in range(n):
        if i != j:
            p *= arr[j]
    out.append(p)
print(n)
print(' '.join(map(str, out)))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  04 · Maximum Product Subarray                                              #
# --------------------------------------------------------------------------- #

MAX_PRODUCT_SUBARRAY = {
    "slug": "max-product-subarray",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Maximum Product Subarray",
    "statement": (
        "Given an array of n integers, find the largest product obtainable "
        "from a contiguous, non-empty subarray.\n\n"
        "Negative values make this different from the maximum-sum version: the "
        "smallest (most negative) running product matters, because one more "
        "negative factor turns it into the largest."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-9 <= arr[i] <= 9",
        "Zeros appear regularly, and it is guaranteed that the product of "
        "every contiguous subarray fits in a signed 64-bit integer",
        "Answers reach roughly 2 * 10^13, so a 32-bit int silently wraps: use "
        "long long in C/C++ and long in Java",
        "An O(n) scan is expected; O(n^2) times out on hidden cases",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": "A single integer: the maximum product of a contiguous non-empty subarray.",
    "examples": [
        {
            "stdin": "4\n2 3 -2 4\n",
            "stdout": "6",
            "explanation": "The subarray [2, 3] has product 6; including -2 would make it negative.",
        },
        {
            "stdin": "3\n-2 0 -1\n",
            "stdout": "0",
            "explanation": "Every non-empty subarray with a non-zero product is negative, so 0 wins.",
        },
    ],
    "criteria": [
        "Track both the running maximum and the running minimum",
        "Reset correctly at a zero without ever returning an empty-subarray product",
        "Handle an array of a single negative value",
        "Run in O(n)",
    ],
    "io": {
        "mode": "tokens",
        "function": "max_product_subarray",
        "todo": "return the largest product of a contiguous non-empty subarray",
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
    best = cur_max = cur_min = arr[0]
    for value in arr[1:]:
        candidates = (value, cur_max * value, cur_min * value)
        cur_max = max(candidates)
        cur_min = min(candidates)
        if cur_max > best:
            best = cur_max
    print(best)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: 2 3 -2 4", "stdin": "4\n2 3 -2 4\n", "hidden": False},
        {"name": "sample: zero wins", "stdin": "3\n-2 0 -1\n", "hidden": False},
        {"name": "hidden: single negative", "stdin": "1\n-4\n", "hidden": True},
        {"name": "hidden: two negatives", "stdin": "2\n-2 -3\n", "hidden": True},
        {"name": "hidden: odd count of negatives", "stdin": "5\n-1 -2 -3 -4 -5\n", "hidden": True},
        {"name": "hidden: zeros split runs", "stdin": "7\n-2 3 0 4 -1 -5 0\n", "hidden": True},
        {"name": "hidden: all zeros", "stdin": "4\n0 0 0 0\n", "hidden": True},
        {"name": "hidden: negative then zero", "stdin": "2\n-3 0\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _product_scale(401, 200000), "hidden": True},
    ],
    "wrong": [
        # Kadane on products, tracking only the maximum: loses the sign flip.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
best = cur = arr[0]
for v in arr[1:]:
    cur = max(v, cur * v)
    best = max(best, cur)
print(best)
""".lstrip(),
        # Restarts at each zero but drops the "just this element" option, so a
        # lone zero between negatives is never considered as the answer.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
best = None
cur_max = cur_min = 1
for v in arr:
    if v == 0:
        cur_max = cur_min = 1
        continue
    a, b = cur_max * v, cur_min * v
    cur_max = max(v, a, b)
    cur_min = min(v, a, b)
    best = cur_max if best is None else max(best, cur_max)
print(best if best is not None else 0)
""".lstrip(),
        # O(n^2): correct, far too slow at n = 200000.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
best = arr[0]
for i in range(n):
    p = 1
    for j in range(i, n):
        p *= arr[j]
        if p > best:
            best = p
print(best)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  05 · Find Minimum in Rotated Sorted Array                                  #
# --------------------------------------------------------------------------- #

FIND_MIN_ROTATED = {
    "slug": "find-min-rotated",
    "skill_id": "dsa_arrays",
    "difficulty": 4,
    "estimated_minutes": 25,
    "title": "Find Minimum in Rotated Sorted Array",
    "statement": (
        "An array of n distinct integers was sorted in increasing order and "
        "then rotated left some number of times (possibly zero). Given the "
        "rotated array, print its minimum element.\n\n"
        "A rotation of zero is allowed, so the array may already be sorted."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= arr[i] <= 1000000000",
        "All values are distinct",
        "The array is a rotation of a strictly increasing array",
        "An O(log n) binary search is expected",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": "A single integer: the smallest value in the array.",
    "examples": [
        {
            "stdin": "5\n3 4 5 1 2\n",
            "stdout": "1",
            "explanation": "The array [1,2,3,4,5] was rotated left twice; the minimum is 1.",
        },
        {
            "stdin": "4\n1 2 3 4\n",
            "stdout": "1",
            "explanation": "Rotation by zero: the array is already sorted, so the first value wins.",
        },
    ],
    "criteria": [
        "Handle a rotation of zero, where the array is already sorted",
        "Handle n = 1",
        "Handle the pivot at the last position",
        "Use binary search rather than a full scan",
    ],
    "io": {
        "mode": "tokens",
        "function": "find_min_rotated",
        "todo": "return the smallest value of the rotated sorted array",
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
    lo, hi = 0, n - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] > arr[hi]:
            lo = mid + 1
        else:
            hi = mid
    print(arr[lo])

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: rotated twice", "stdin": "5\n3 4 5 1 2\n", "hidden": False},
        {"name": "sample: not rotated", "stdin": "4\n1 2 3 4\n", "hidden": False},
        {"name": "hidden: single element", "stdin": "1\n-9\n", "hidden": True},
        {"name": "hidden: pivot at the end", "stdin": "5\n2 3 4 5 1\n", "hidden": True},
        {"name": "hidden: pivot at index 1", "stdin": "5\n5 1 2 3 4\n", "hidden": True},
        {"name": "hidden: negatives", "stdin": "6\n0 1 2 -7 -5 -3\n", "hidden": True},
        {"name": "hidden: two elements rotated", "stdin": "2\n2 1\n", "hidden": True},
        {"name": "hidden: scale rotated", "stdin": _rotated_min_scale(503, 200000, 137_000), "hidden": True},
        {"name": "hidden: scale unrotated", "stdin": _rotated_min_scale(509, 200000, 0), "hidden": True},
    ],
    "wrong": [
        # Assumes a rotation actually happened.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
ans = arr[-1]
for i in range(1, n):
    if arr[i] < arr[i-1]:
        ans = arr[i]
        break
print(ans)
""".lstrip(),
        # Only looks at the two ends.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
print(min(arr[0], arr[-1]))
""".lstrip(),
        # Binary search compared against arr[lo] instead of arr[hi].
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
lo, hi = 0, n - 1
while lo < hi:
    mid = (lo + hi) // 2
    if arr[mid] >= arr[lo]:
        lo = mid + 1
    else:
        hi = mid
print(arr[lo])
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  06 · Search in Rotated Sorted Array                                        #
# --------------------------------------------------------------------------- #

SEARCH_ROTATED = {
    "slug": "search-rotated",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Search in Rotated Sorted Array",
    "statement": (
        "An array of n distinct integers was sorted in increasing order and "
        "then rotated left some number of times (possibly zero). You are then "
        "given q targets to look up in that same array.\n\n"
        "For each target print the 0-based index where it sits, or -1 if it is "
        "absent. Because all values are distinct, each index is unique.\n\n"
        "The queries are what make the complexity matter: with q as large as n, "
        "scanning the array once per query is far too slow, so each lookup has "
        "to be a binary search that copes with the rotation."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "1 <= q <= 100000",
        "-1000000000 <= arr[i] <= 1000000000",
        "-2000000000 <= target <= 2000000000, which does not fit in a 32-bit "
        "int: read targets as long long in C/C++ and long in Java",
        "All array values are distinct; targets may repeat and may be absent",
        "O(log n) per query is expected; O(n) per query times out on the "
        "hidden scale case",
    ],
    "input_format": (
        "Line 1: n and q, separated by a space.\n"
        "Line 2: n space-separated integers, the rotated array.\n"
        "Line 3: q space-separated targets."
    ),
    "output_format": (
        "Line 1: q, the number of answers.\n"
        "Line 2: the q answers separated by single spaces, in query order; "
        "each is a 0-based index or -1. Whitespace layout is not graded."
    ),
    "examples": [
        {
            "stdin": "7 2\n4 5 6 7 0 1 2\n0 3\n",
            "stdout": "2\n4 -1",
            "explanation": "0 sits at index 4; 3 does not occur, so its answer is -1.",
        },
        {
            "stdin": "5 3\n10 20 30 40 50\n50 10 30\n",
            "stdout": "3\n4 0 2",
            "explanation": "The rotation is zero here, so the array is plainly sorted.",
        },
    ],
    "criteria": [
        "Answer -1 when the target is absent",
        "Work when the rotation is zero",
        "Find a target sitting exactly at the pivot or at either end",
        "Binary search per query; a scan per query will not finish",
    ],
    "io": {
        "mode": "tokens",
        "function": "search_rotated",
        "todo": (
            "answer every target with its 0-based index or -1, then print q and the q "
            "answers (replace the single-value print in main)"
        ),
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "q", "type": "int"},
            {"name": "arr", "type": "long", "count": "n"},
            {"name": "targets", "type": "long", "count": "q"},
        ],
        "args": ["arr", "targets"],
        "returns": "int",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    q = int(data[1])
    arr = [int(x) for x in data[2:2 + n]]
    targets = [int(x) for x in data[2 + n:2 + n + q]]
    out = []
    for target in targets:
        lo, hi = 0, n - 1
        found = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if arr[mid] == target:
                found = mid
                break
            if arr[lo] <= arr[mid]:
                if arr[lo] <= target < arr[mid]:
                    hi = mid - 1
                else:
                    lo = mid + 1
            else:
                if arr[mid] < target <= arr[hi]:
                    lo = mid + 1
                else:
                    hi = mid - 1
        out.append(found)
    print(q)
    print(' '.join(map(str, out)))

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: hit and miss", "stdin": "7 2\n4 5 6 7 0 1 2\n0 3\n", "hidden": False, "match": "tokens"},
        {"name": "sample: not rotated", "stdin": "5 3\n10 20 30 40 50\n50 10 30\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: single element", "stdin": "1 2\n5\n5 -5\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: pivot and both ends",
            "stdin": "6 3\n4 5 6 1 2 3\n1 3 4\n",
            "hidden": True,
            "match": "tokens",
        },
        {"name": "hidden: every value present", "stdin": "5 5\n30 40 50 10 20\n10 20 30 40 50\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: all absent", "stdin": "4 3\n7 8 5 6\n1 2 9\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: negatives", "stdin": "5 2\n-3 -1 -9 -8 -7\n-7 -3\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: repeated queries", "stdin": "3 4\n2 3 1\n1 1 1 1\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: out of range targets", "stdin": "3 2\n4 5 1\n2000000000 -2000000000\n", "hidden": True, "match": "tokens"},
        # 100000 lookups into a 200000-element array: a scan per query is 10^10
        # element comparisons, which no language finishes inside the limit.
        {"name": "hidden: scale", "stdin": _rotated_search_scale(601, 200000, 61_237, 100000), "hidden": True, "match": "tokens"},
    ],
    "wrong": [
        # Plain binary search that ignores the rotation.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); q = int(data[1])
arr = [int(x) for x in data[2:2+n]]
targets = [int(x) for x in data[2+n:2+n+q]]
out = []
for target in targets:
    lo, hi = 0, n - 1
    ans = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            ans = mid
            break
        if arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    out.append(ans)
print(q)
print(' '.join(map(str, out)))
""".lstrip(),
        # Boundary bug: the sorted-half test uses a strict < , so a target sitting
        # exactly on the low end of the sorted half is discarded.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); q = int(data[1])
arr = [int(x) for x in data[2:2+n]]
targets = [int(x) for x in data[2+n:2+n+q]]
out = []
for target in targets:
    lo, hi = 0, n - 1
    ans = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            ans = mid
            break
        if arr[lo] <= arr[mid]:
            if arr[lo] < target < arr[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:
            if arr[mid] < target < arr[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    out.append(ans)
print(q)
print(' '.join(map(str, out)))
""".lstrip(),
        # Correct, but scans the array once per query.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); q = int(data[1])
arr = [int(x) for x in data[2:2+n]]
targets = [int(x) for x in data[2+n:2+n+q]]
out = []
for target in targets:
    ans = -1
    for i in range(n):
        if arr[i] == target:
            ans = i
            break
    out.append(ans)
print(q)
print(' '.join(map(str, out)))
""".lstrip(),
        # Reports presence rather than the index.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); q = int(data[1])
arr = [int(x) for x in data[2:2+n]]
targets = [int(x) for x in data[2+n:2+n+q]]
present = set(arr)
out = [1 if t in present else -1 for t in targets]
print(q)
print(' '.join(map(str, out)))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  07 · 3Sum                                                                  #
# --------------------------------------------------------------------------- #

THREE_SUM = {
    "slug": "three-sum",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 40,
    "title": "3Sum",
    "statement": (
        "Given an array of n integers, list every distinct triplet of values "
        "that sums to zero.\n\n"
        "Triplets are compared by value, not by position: (-1, 0, 1) and "
        "(0, -1, 1) are the same triplet and appear once. A value may be used "
        "as many times as it occurs in the array, so (0, 0, 0) qualifies only "
        "if at least three zeros are present.\n\n"
        "The set of triplets is unique but the order you find them in is not, "
        "so the output is canonical: write each triplet in non-decreasing "
        "order, and list the triplets in ascending order of their first value, "
        "then second, then third. Any correct solution that sorts its answer "
        "this way prints exactly the same thing."
    ),
    "constraints": [
        "1 <= n <= 1500",
        "-100000 <= arr[i] <= 100000",
        "Duplicate values are common; each distinct value-triplet is listed once",
        "An O(n^2) sort-and-two-pointer solution is expected; O(n^3) times out",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": (
        "Line 1: t, the number of distinct triplets.\n"
        "Then t lines, each holding one triplet's three values in "
        "non-decreasing order, separated by spaces. The triplets themselves "
        "are in ascending lexicographic order. Print no triplet lines when "
        "t = 0. Whitespace layout is not graded."
    ),
    "examples": [
        {
            "stdin": "6\n-1 0 1 2 -1 -4\n",
            "stdout": "2\n-1 -1 2\n-1 0 1",
            "explanation": (
                "Two triplets sum to zero. (-1,-1,2) comes first because its second "
                "value, -1, is smaller than the 0 of (-1,0,1)."
            ),
        },
        {
            "stdin": "4\n0 0 0 0\n",
            "stdout": "1\n0 0 0",
            "explanation": "(0,0,0) is available because four zeros are present, and it is listed once.",
        },
    ],
    "criteria": [
        "List each distinct value-triplet exactly once despite duplicates",
        "Require three actual occurrences before listing (0,0,0)",
        "Print 0 and nothing else when no triplet exists",
        "Emit triplets sorted internally and lexicographically between themselves",
        "Sort and use two pointers rather than three nested loops",
    ],
    "io": {
        "mode": "tokens",
        "function": "three_sum",
        "todo": (
            "collect the distinct zero-sum triplets, then print t and one canonical "
            "triplet per line (replace the single-value print in main)"
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
    arr = sorted(int(x) for x in data[1:1 + n])
    out = []
    i = 0
    while i < n - 2:
        if i > 0 and arr[i] == arr[i - 1]:
            i += 1
            continue
        lo, hi = i + 1, n - 1
        while lo < hi:
            s = arr[i] + arr[lo] + arr[hi]
            if s < 0:
                lo += 1
            elif s > 0:
                hi -= 1
            else:
                out.append((arr[i], arr[lo], arr[hi]))
                lo += 1
                while lo < hi and arr[lo] == arr[lo - 1]:
                    lo += 1
                hi -= 1
                while lo < hi and arr[hi] == arr[hi + 1]:
                    hi -= 1
        i += 1
    lines = [str(len(out))]
    lines += [f"{a} {b} {c}" for a, b, c in out]
    sys.stdout.write('\n'.join(lines) + '\n')

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: classic", "stdin": "6\n-1 0 1 2 -1 -4\n", "hidden": False, "match": "tokens"},
        {"name": "sample: four zeros", "stdin": "4\n0 0 0 0\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: too few elements", "stdin": "2\n1 -1\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: only two zeros", "stdin": "4\n0 0 5 7\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: no triplet", "stdin": "5\n1 2 3 4 5\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: all negative", "stdin": "5\n-5 -4 -3 -2 -1\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: heavy duplicates", "stdin": "9\n-2 -2 -2 1 1 1 4 4 4\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: many distinct triplets",
            "stdin": "10\n-5 -4 -3 -2 -1 0 1 2 3 5\n",
            "hidden": True,
            "match": "tokens",
        },
        {"name": "hidden: scale", "stdin": _array_case(701, 1500, -50000, 50000), "hidden": True, "match": "tokens"},
    ],
    "wrong": [
        # O(n^3) over distinct values: right answer, far too slow.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
found = set()
for i in range(n):
    for j in range(i+1, n):
        for k in range(j+1, n):
            if arr[i] + arr[j] + arr[k] == 0:
                found.add(tuple(sorted((arr[i], arr[j], arr[k]))))
out = sorted(found)
print(len(out))
for a, b, c in out:
    print(a, b, c)
""".lstrip(),
        # Lists index triplets, so duplicate values produce duplicate lines.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = sorted(int(x) for x in data[1:1+n])
out = []
for i in range(n - 2):
    lo, hi = i + 1, n - 1
    while lo < hi:
        s = arr[i] + arr[lo] + arr[hi]
        if s < 0:
            lo += 1
        elif s > 0:
            hi -= 1
        else:
            out.append((arr[i], arr[lo], arr[hi]))
            lo += 1
            hi -= 1
print(len(out))
for a, b, c in out:
    print(a, b, c)
""".lstrip(),
        # Uses a value set, so it invents (0,0,0) and other repeats the array
        # cannot actually supply.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
values = sorted(set(arr))
present = set(values)
out = []
m = len(values)
for i in range(m):
    for j in range(i, m):
        need = -(values[i] + values[j])
        if need in present and need >= values[j]:
            out.append((values[i], values[j], need))
out.sort()
print(len(out))
for a, b, c in out:
    print(a, b, c)
""".lstrip(),
        # Correct triplets, but emitted in discovery order rather than sorted,
        # so the lines come out in the wrong sequence.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = sorted(int(x) for x in data[1:1+n])
out = []
i = 0
while i < n - 2:
    if i > 0 and arr[i] == arr[i-1]:
        i += 1
        continue
    lo, hi = i + 1, n - 1
    while lo < hi:
        s = arr[i] + arr[lo] + arr[hi]
        if s < 0:
            lo += 1
        elif s > 0:
            hi -= 1
        else:
            out.append((arr[i], arr[hi], arr[lo]))
            lo += 1
            while lo < hi and arr[lo] == arr[lo-1]:
                lo += 1
            hi -= 1
            while lo < hi and arr[hi] == arr[hi+1]:
                hi -= 1
    i += 1
print(len(out))
for a, b, c in out:
    print(a, b, c)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  08 · Container With Most Water                                             #
# --------------------------------------------------------------------------- #

CONTAINER_WATER = {
    "slug": "container-most-water",
    "skill_id": "dsa_arrays",
    "difficulty": 4,
    "estimated_minutes": 25,
    "title": "Container With Most Water",
    "statement": (
        "n vertical lines stand on the x-axis; line i runs from (i, 0) to "
        "(i, height[i]). Choosing two lines i < j, the water they hold is "
        "(j - i) * min(height[i], height[j]).\n\n"
        "Print the largest amount of water any pair of lines can hold."
    ),
    "constraints": [
        "2 <= n <= 200000",
        "0 <= height[i] <= 1000000000",
        "The answer reaches about 2 * 10^14 and does not fit in a 32-bit int: "
        "use long long in C/C++ and long in Java",
        "An O(n) two-pointer sweep is expected; O(n^2) times out",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated heights.",
    "output_format": "A single integer: the maximum water the container can hold.",
    "examples": [
        {
            "stdin": "9\n1 8 6 2 5 4 8 3 7\n",
            "stdout": "49",
            "explanation": "Lines at indices 1 and 8 give (8 - 1) * min(8, 7) = 49.",
        },
        {
            "stdin": "2\n1 1\n",
            "stdout": "1",
            "explanation": "The only pair spans width 1 at height 1.",
        },
    ],
    "criteria": [
        "Use the width between indices, not the number of lines spanned",
        "Handle zero heights, which hold no water",
        "Move the pointer at the shorter line",
        "Run in O(n)",
    ],
    "io": {
        "mode": "tokens",
        "function": "max_water",
        "todo": "return the maximum water two lines can hold",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "height", "type": "long", "count": "n"},
        ],
        "args": ["height"],
        "returns": "long",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    height = [int(x) for x in data[1:1 + n]]
    lo, hi = 0, n - 1
    best = 0
    while lo < hi:
        left, right = height[lo], height[hi]
        area = (hi - lo) * (left if left < right else right)
        if area > best:
            best = area
        if left < right:
            lo += 1
        else:
            hi -= 1
    print(best)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: classic", "stdin": "9\n1 8 6 2 5 4 8 3 7\n", "hidden": False},
        {"name": "sample: two lines", "stdin": "2\n1 1\n", "hidden": False},
        {"name": "hidden: all zeros", "stdin": "4\n0 0 0 0\n", "hidden": True},
        {"name": "hidden: increasing", "stdin": "5\n1 2 3 4 5\n", "hidden": True},
        {"name": "hidden: decreasing", "stdin": "5\n5 4 3 2 1\n", "hidden": True},
        {"name": "hidden: tall ends", "stdin": "6\n9 1 1 1 1 9\n", "hidden": True},
        # The heights avoid round powers of ten so the expected output cannot
        # coincide with a number quoted in the published constraints.
        {"name": "hidden: tall middle", "stdin": "5\n1 999999937 999999937 1 1\n", "hidden": True},
        {"name": "hidden: large magnitudes", "stdin": "3\n1000000000 0 1000000000\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _array_case(809, 200000, 0, 10**9), "hidden": True},
    ],
    "wrong": [
        # O(n^2) over all pairs.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); h = [int(x) for x in data[1:1+n]]
best = 0
for i in range(n):
    for j in range(i+1, n):
        area = (j - i) * min(h[i], h[j])
        if area > best:
            best = area
print(best)
""".lstrip(),
        # Moves the taller pointer, which can step over the best pair.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); h = [int(x) for x in data[1:1+n]]
lo, hi = 0, n - 1
best = 0
while lo < hi:
    best = max(best, (hi - lo) * min(h[lo], h[hi]))
    if h[lo] > h[hi]:
        lo += 1
    else:
        hi -= 1
print(best)
""".lstrip(),
        # Off-by-one width: counts the lines instead of the gap.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); h = [int(x) for x in data[1:1+n]]
lo, hi = 0, n - 1
best = 0
while lo < hi:
    best = max(best, (hi - lo + 1) * min(h[lo], h[hi]))
    if h[lo] < h[hi]:
        lo += 1
    else:
        hi -= 1
print(best)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  09 · Best Time to Buy and Sell Stock                                       #
# --------------------------------------------------------------------------- #

BEST_TIME_STOCK = {
    "slug": "best-time-stock",
    "skill_id": "dsa_arrays",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Best Time to Buy and Sell Stock",
    "statement": (
        "prices[i] is the price of one share on day i. You may buy on one day "
        "and sell on a strictly later day, at most once.\n\n"
        "Print the maximum profit achievable, or 0 if no pair of days yields a "
        "profit (you are allowed to simply not trade)."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "0 <= prices[i] <= 1000000000",
        "You must buy before you sell; selling on the buy day is not allowed",
        "Profit fits comfortably in 64 bits; use long long in C/C++ and long "
        "in Java for the price values themselves",
        "An O(n) scan is expected; O(n^2) times out",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated prices.",
    "output_format": "A single integer: the maximum profit, or 0 if no profitable trade exists.",
    "examples": [
        {
            "stdin": "6\n7 1 5 3 6 4\n",
            "stdout": "5",
            "explanation": "Buy at 1 on day 1 and sell at 6 on day 4 for a profit of 5.",
        },
        {
            "stdin": "5\n7 6 4 3 1\n",
            "stdout": "0",
            "explanation": "Prices only fall, so the best move is not to trade at all.",
        },
    ],
    "criteria": [
        "Never sell before buying",
        "Print 0 rather than a negative profit",
        "Handle n = 1",
        "Run in O(n)",
    ],
    "io": {
        "mode": "tokens",
        "function": "max_profit",
        "todo": "return the maximum profit from one buy followed by one later sell",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "prices", "type": "long", "count": "n"},
        ],
        "args": ["prices"],
        "returns": "long",
    },
    "reference": r"""
import sys

def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    prices = [int(x) for x in data[1:1 + n]]
    best = 0
    cheapest = prices[0]
    for price in prices[1:]:
        if price - cheapest > best:
            best = price - cheapest
        if price < cheapest:
            cheapest = price
    print(best)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: profitable", "stdin": "6\n7 1 5 3 6 4\n", "hidden": False},
        {"name": "sample: falling prices", "stdin": "5\n7 6 4 3 1\n", "hidden": False},
        {"name": "hidden: single day", "stdin": "1\n5\n", "hidden": True},
        {"name": "hidden: flat prices", "stdin": "4\n3 3 3 3\n", "hidden": True},
        {"name": "hidden: minimum after maximum", "stdin": "4\n9 1 2 0\n", "hidden": True},
        {"name": "hidden: rise then crash", "stdin": "6\n1 9 1 2 1 1\n", "hidden": True},
        {"name": "hidden: large magnitudes", "stdin": "3\n5 999999937 1\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _array_case(907, 200000, 0, 10**9), "hidden": True},
    ],
    "wrong": [
        # Ignores the order of the days.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); p = [int(x) for x in data[1:1+n]]
print(max(p) - min(p))
""".lstrip(),
        # Forgets that not trading is allowed, so it can print a negative profit.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); p = [int(x) for x in data[1:1+n]]
best = -10**18
cheapest = p[0]
for price in p[1:]:
    best = max(best, price - cheapest)
    cheapest = min(cheapest, price)
print(best if n > 1 else 0)
""".lstrip(),
        # O(n^2) over every buy/sell pair.
        r"""
import sys
data = sys.stdin.read().split()
n = int(data[0]); p = [int(x) for x in data[1:1+n]]
best = 0
for i in range(n):
    for j in range(i+1, n):
        if p[j] - p[i] > best:
            best = p[j] - p[i]
print(best)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  10 · Longest Repeating Character Replacement                               #
# --------------------------------------------------------------------------- #

CHAR_REPLACEMENT = {
    "slug": "longest-repeat-char-replacement",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 35,
    "title": "Longest Repeating Character Replacement",
    "statement": (
        "You are given a string s of uppercase letters and an integer k. You "
        "may change at most k characters of s, each to any uppercase letter.\n\n"
        "Print the length of the longest substring that can be made to consist "
        "of a single repeated character using at most k changes."
    ),
    "constraints": [
        "1 <= |s| <= 200000",
        "s contains only the characters A-Z",
        "0 <= k <= |s|",
        "An O(26n) or O(n) sliding window is expected; O(n^2) times out",
    ],
    "input_format": (
        "A single line containing s, then a space, then k. "
        "s itself never contains a space."
    ),
    "output_format": "A single integer: the length of the longest achievable run.",
    "examples": [
        {
            "stdin": "ABAB 2\n",
            "stdout": "4",
            "explanation": "Change both A's to B (or both B's to A) to get a run of 4.",
        },
        {
            "stdin": "AABABBA 1\n",
            "stdout": "4",
            "explanation": 'Changing the middle A gives "BBBB" inside the string, a run of 4.',
        },
    ],
    "criteria": [
        "Handle k = 0, where the answer is the longest existing run",
        "Handle k >= |s|, where the whole string can be made uniform",
        "Do not assume the most frequent character overall is the right one",
        "Use a sliding window rather than testing every substring",
    ],
    "io": {
        "mode": "line",
        "function": "longest_replacement",
        "todo": (
            "parse the line as the string s followed by a space and k, then return "
            "the longest run achievable with at most k replacements"
        ),
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": r"""
import sys

def main():
    line = sys.stdin.readline().rstrip('\n')
    s, _, k_text = line.rpartition(' ')
    k = int(k_text)
    counts = [0] * 26
    best = 0
    max_count = 0
    start = 0
    for end, ch in enumerate(s):
        index = ord(ch) - 65
        counts[index] += 1
        if counts[index] > max_count:
            max_count = counts[index]
        while (end - start + 1) - max_count > k:
            counts[ord(s[start]) - 65] -= 1
            start += 1
            max_count = max(counts)
        if end - start + 1 > best:
            best = end - start + 1
    print(best)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: ABAB k=2", "stdin": "ABAB 2\n", "hidden": False},
        {"name": "sample: AABABBA k=1", "stdin": "AABABBA 1\n", "hidden": False},
        {"name": "hidden: k = 0", "stdin": "AABBBCC 0\n", "hidden": True},
        {"name": "hidden: single character", "stdin": "A 0\n", "hidden": True},
        {"name": "hidden: k covers everything", "stdin": "ABCDE 5\n", "hidden": True},
        {"name": "hidden: frequent letter is spread out", "stdin": "AABBAA 0\n", "hidden": True},
        {"name": "hidden: all identical", "stdin": "AAAAAA 2\n", "hidden": True},
        {"name": "hidden: best run at the end", "stdin": "ABCDEBBBB 1\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": _random_string(1009, 200000, "ABCDE") + " 3000\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Global heuristic: most frequent letter overall plus k.
        r"""
import sys
from collections import Counter
line = sys.stdin.readline().rstrip('\n')
s, _, k_text = line.rpartition(' ')
k = int(k_text)
counts = Counter(s)
top = max(counts.values()) if counts else 0
print(min(len(s), top + k))
""".lstrip(),
        # Restarts the window instead of shrinking it from the left.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
s, _, k_text = line.rpartition(' ')
k = int(k_text)
best = 0
start = 0
counts = {}
max_count = 0
for end, ch in enumerate(s):
    counts[ch] = counts.get(ch, 0) + 1
    max_count = max(max_count, counts[ch])
    if (end - start + 1) - max_count > k:
        start = end
        counts = {ch: 1}
        max_count = 1
    best = max(best, end - start + 1)
print(best)
""".lstrip(),
        # O(n^2) over every substring.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
s, _, k_text = line.rpartition(' ')
k = int(k_text)
n = len(s)
best = 0
for i in range(n):
    counts = [0] * 26
    top = 0
    for j in range(i, n):
        idx = ord(s[j]) - 65
        counts[idx] += 1
        if counts[idx] > top:
            top = counts[idx]
        if (j - i + 1) - top <= k and j - i + 1 > best:
            best = j - i + 1
print(best)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  11 · Minimum Window Substring                                              #
# --------------------------------------------------------------------------- #

MIN_WINDOW = {
    "slug": "min-window-substring",
    "skill_id": "dsa_arrays",
    "difficulty": 7,
    "estimated_minutes": 45,
    "title": "Minimum Window Substring",
    "statement": (
        "Given strings s and t, find the shortest contiguous substring of s "
        "that contains every character of t, counting multiplicities: if t is "
        '"aab", the window must contain at least two a\'s and one b.\n\n'
        "The shortest window itself is not unique, but its length is, so print "
        "the length. Print 0 when no window exists."
    ),
    "constraints": [
        "1 <= |s| <= 200000",
        "1 <= |t| <= 1000",
        "s and t contain only ASCII letters (a-z and A-Z); case matters",
        "Character multiplicities in t must be respected",
        "An O(|s| + |t|) sliding window is expected; O(|s|^2) times out",
    ],
    "input_format": (
        "A single line containing s, then a space, then t. "
        "Neither string contains a space."
    ),
    "output_format": "A single integer: the length of the shortest valid window, or 0 if none exists.",
    "examples": [
        {
            "stdin": "ADOBECODEBANC ABC\n",
            "stdout": "4",
            "explanation": '"BANC" is the shortest window containing A, B and C.',
        },
        {
            "stdin": "aa aa\n",
            "stdout": "2",
            "explanation": "Two a's are required, so the whole string is the smallest window.",
        },
    ],
    "criteria": [
        "Respect repeated characters in t rather than treating it as a set",
        "Print 0 when s cannot cover t",
        "Shrink the window from the left once it is valid",
        "Run in linear time over s",
    ],
    "io": {
        "mode": "line",
        "function": "min_window_length",
        "todo": (
            "parse the line as s followed by a space and t, then return the length "
            "of the shortest substring of s covering all of t (0 if none)"
        ),
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": r"""
import sys
from collections import Counter

def main():
    line = sys.stdin.readline().rstrip('\n')
    s, _, t = line.partition(' ')
    if not t or len(t) > len(s):
        print(0)
        return
    need = Counter(t)
    missing = len(need)
    have = {}
    best = len(s) + 1
    start = 0
    for end, ch in enumerate(s):
        if ch in need:
            have[ch] = have.get(ch, 0) + 1
            if have[ch] == need[ch]:
                missing -= 1
        while missing == 0:
            if end - start + 1 < best:
                best = end - start + 1
            left = s[start]
            if left in need:
                have[left] -= 1
                if have[left] < need[left]:
                    missing += 1
            start += 1
    print(0 if best > len(s) else best)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: ADOBECODEBANC", "stdin": "ADOBECODEBANC ABC\n", "hidden": False},
        {"name": "sample: repeated letters", "stdin": "aa aa\n", "hidden": False},
        {"name": "hidden: no window", "stdin": "a b\n", "hidden": True},
        {"name": "hidden: t longer than s", "stdin": "a aa\n", "hidden": True},
        {"name": "hidden: single character match", "stdin": "abc b\n", "hidden": True},
        {"name": "hidden: case sensitivity", "stdin": "aA A\n", "hidden": True},
        {"name": "hidden: multiplicity matters", "stdin": "abcabd aab\n", "hidden": True},
        {"name": "hidden: window at the very end", "stdin": "xxxxxxab ab\n", "hidden": True},
        {"name": "hidden: whole string needed", "stdin": "abcde edcba\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": _random_string(1103, 200000, "abcde") + " abcdeabcde\n",
            "hidden": True,
        },
        # The only 'z' is the last character, so every window that covers t must
        # reach the end of s. A per-start rescan therefore costs O(|s|^2) here,
        # where the previous case lets it bail out after a handful of characters.
        {
            "name": "hidden: scale with one rare character",
            "stdin": _random_string(1107, 199999, "abcd") + "z abcdz\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Treats t as a set, ignoring multiplicities.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
s, _, t = line.partition(' ')
need = set(t)
have = {}
missing = len(need)
best = len(s) + 1
start = 0
for end, ch in enumerate(s):
    if ch in need:
        have[ch] = have.get(ch, 0) + 1
        if have[ch] == 1:
            missing -= 1
    while missing == 0:
        best = min(best, end - start + 1)
        left = s[start]
        if left in need:
            have[left] -= 1
            if have[left] == 0:
                missing += 1
        start += 1
print(0 if best > len(s) else best)
""".lstrip(),
        # Finds a valid window but never shrinks it from the left.
        r"""
import sys
from collections import Counter
line = sys.stdin.readline().rstrip('\n')
s, _, t = line.partition(' ')
need = Counter(t)
have = Counter()
missing = len(need)
best = len(s) + 1
start = 0
for end, ch in enumerate(s):
    if ch in need:
        have[ch] += 1
        if have[ch] == need[ch]:
            missing -= 1
    if missing == 0:
        best = min(best, end - start + 1)
print(0 if best > len(s) else best)
""".lstrip(),
        # O(|s|^2) over every window.
        r"""
import sys
from collections import Counter
line = sys.stdin.readline().rstrip('\n')
s, _, t = line.partition(' ')
need = Counter(t)
n = len(s)
best = 0
for i in range(n):
    have = Counter()
    for j in range(i, n):
        have[s[j]] += 1
        if all(have[c] >= need[c] for c in need):
            if best == 0 or j - i + 1 < best:
                best = j - i + 1
            break
print(best)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  12 · Valid Anagram                                                         #
# --------------------------------------------------------------------------- #

VALID_ANAGRAM = {
    "slug": "valid-anagram",
    "skill_id": "dsa_arrays",
    "difficulty": 2,
    "estimated_minutes": 15,
    "title": "Valid Anagram",
    "statement": (
        "Two strings are anagrams when one is a rearrangement of the other: "
        "the same characters with the same multiplicities.\n\n"
        "Given s and t, print 1 if t is an anagram of s and 0 otherwise."
    ),
    "constraints": [
        "1 <= |s| <= 200000",
        "1 <= |t| <= 200000",
        "Both strings contain only lowercase letters a-z",
        "An O(n) count of 26 letters is expected",
    ],
    "input_format": (
        "A single line containing s, then a space, then t. "
        "Neither string contains a space."
    ),
    "output_format": "A single integer: 1 if t is an anagram of s, otherwise 0.",
    "examples": [
        {
            "stdin": "anagram nagaram\n",
            "stdout": "1",
            "explanation": "Both strings use the same letters the same number of times.",
        },
        {
            "stdin": "rat car\n",
            "stdout": "0",
            "explanation": '"car" contains a c, which "rat" does not.',
        },
    ],
    "criteria": [
        "Compare multiplicities, not just which letters appear",
        "Return 0 immediately when the lengths differ",
        "Run in O(|s| + |t|)",
    ],
    "io": {
        "mode": "line",
        "function": "is_anagram",
        "todo": (
            "parse the line as s followed by a space and t, then return 1 if t is an "
            "anagram of s, otherwise 0"
        ),
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": r"""
import sys

def main():
    line = sys.stdin.readline().rstrip('\n')
    s, _, t = line.partition(' ')
    if len(s) != len(t):
        print(0)
        return
    counts = [0] * 26
    for ch in s:
        counts[ord(ch) - 97] += 1
    for ch in t:
        counts[ord(ch) - 97] -= 1
    print(0 if any(counts) else 1)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: anagram", "stdin": "anagram nagaram\n", "hidden": False},
        {"name": "sample: not an anagram", "stdin": "rat car\n", "hidden": False},
        {"name": "hidden: same letters different counts", "stdin": "aacc ccac\n", "hidden": True},
        {"name": "hidden: different lengths", "stdin": "ab abb\n", "hidden": True},
        {"name": "hidden: single letters equal", "stdin": "a a\n", "hidden": True},
        {"name": "hidden: single letters differ", "stdin": "a b\n", "hidden": True},
        {"name": "hidden: equal letter sums", "stdin": "ad bc\n", "hidden": True},
        {"name": "hidden: identical strings", "stdin": "listen listen\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": (
                lambda base: base
                + " "
                + "".join(_rng(1213).sample(base, len(base)))
                + "\n"
            )(_random_string(1201, 200000, "abcdefghijklmnopqrstuvwxyz")),
            "hidden": True,
        },
    ],
    "wrong": [
        # Compares the sets of letters, ignoring how often each occurs.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
s, _, t = line.partition(' ')
print(1 if set(s) == set(t) else 0)
""".lstrip(),
        # Compares the sums of the character codes.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
s, _, t = line.partition(' ')
print(1 if sum(map(ord, s)) == sum(map(ord, t)) else 0)
""".lstrip(),
        # Checks only that every letter of t occurs somewhere in s.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
s, _, t = line.partition(' ')
print(1 if len(s) == len(t) and all(c in s for c in t) else 0)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  13 · Group Anagrams                                                        #
# --------------------------------------------------------------------------- #

GROUP_ANAGRAMS = {
    "slug": "group-anagrams",
    "skill_id": "dsa_arrays",
    "difficulty": 4,
    "estimated_minutes": 30,
    "title": "Group Anagrams",
    "statement": (
        "Given a list of words, partition them into groups so that two words "
        "share a group exactly when they are anagrams of each other. Every "
        "input word belongs to exactly one group, and a word repeated in the "
        "input appears that many times in its group.\n\n"
        "The partition is unique but the order of the groups, and of the words "
        "inside them, is not. The output is therefore canonical: sort the "
        "words inside each group into ascending alphabetical order, then order "
        "the groups by their first word. Two anagram groups can never begin "
        "with the same word, so that ordering is total and any correct "
        "solution prints exactly the same thing."
    ),
    "constraints": [
        "1 <= number of words <= 20000",
        "1 <= length of each word <= 100",
        "Total input length <= 200000 characters",
        "Words contain only lowercase letters a-z",
        "Duplicate words may appear; they stay in the same group and are listed "
        "once per occurrence",
    ],
    "input_format": "A single line of words separated by single spaces.",
    "output_format": (
        "Line 1: g, the number of groups.\n"
        "Then g lines, each holding k (the size of that group) followed by the "
        "k words in ascending order, all separated by spaces. The groups are "
        "ordered by their first word. Whitespace layout is not graded."
    ),
    "examples": [
        {
            "stdin": "eat tea tan ate nat bat\n",
            "stdout": "3\n3 ate eat tea\n1 bat\n2 nat tan",
            "explanation": (
                "The three groups sort internally to [ate, eat, tea], [bat] and "
                '[nat, tan]. Their first words are "ate", "bat" and "nat", so the '
                "groups appear in that order, each preceded by its size."
            ),
        },
        {
            "stdin": "abc cba bca xyz\n",
            "stdout": "2\n3 abc bca cba\n1 xyz",
            "explanation": (
                "The first three words are mutual anagrams and sort to abc, bca, cba; "
                'xyz stands alone and follows because "abc" < "xyz".'
            ),
        },
    ],
    "criteria": [
        "Group by letter multiset, not by length or by the set of letters used",
        "Keep duplicate words as separate entries within one group",
        "Sort inside each group, then order the groups by their first word",
        "Print each group's size before its words",
    ],
    "io": {
        "mode": "line",
        "function": "group_anagrams",
        "todo": (
            "split the line on spaces, group the anagrams, then print g and one "
            "canonical group per line (replace the single-value print in main)"
        ),
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": r"""
import sys

def main():
    line = sys.stdin.readline().rstrip('\n')
    words = line.split()
    groups = {}
    for word in words:
        key = ''.join(sorted(word))
        groups.setdefault(key, []).append(word)
    ordered = []
    for members in groups.values():
        members.sort()
        ordered.append(members)
    ordered.sort(key=lambda members: members[0])
    out = [str(len(ordered))]
    for members in ordered:
        out.append(str(len(members)) + ' ' + ' '.join(members))
    sys.stdout.write('\n'.join(out) + '\n')

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: six words", "stdin": "eat tea tan ate nat bat\n", "hidden": False, "match": "tokens"},
        {"name": "sample: two groups", "stdin": "abc cba bca xyz\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: single word", "stdin": "a\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: duplicates", "stdin": "ab ab ab\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: same letters different counts",
            "stdin": "aab abb aba\n",
            "hidden": True,
            "match": "tokens",
        },
        {"name": "hidden: equal code sums", "stdin": "abc aad\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: same length no anagrams", "stdin": "abcd efgh ijkl\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: all one group",
            "stdin": "abc bac cab acb bca cba\n",
            "hidden": True,
            "match": "tokens",
        },
        # The groups here do not arrive in first-word order, so a solution that
        # emits them in encounter order is caught.
        {"name": "hidden: groups out of order", "stdin": "zz yy zz aa yy\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: scale", "stdin": _words_case(1301, 20000, 10), "hidden": True, "match": "tokens"},
    ],
    "wrong": [
        # Keys on the sum of character codes: "abc" and "aad" collide.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
words = line.split()
groups = {}
for w in words:
    groups.setdefault(sum(map(ord, w)), []).append(w)
ordered = sorted((sorted(v) for v in groups.values()), key=lambda m: m[0])
print(len(ordered))
for members in ordered:
    print(len(members), ' '.join(members))
""".lstrip(),
        # Keys on the set of distinct letters, losing multiplicities.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
words = line.split()
groups = {}
for w in words:
    groups.setdefault(frozenset(w), []).append(w)
ordered = sorted((sorted(v) for v in groups.values()), key=lambda m: m[0])
print(len(ordered))
for members in ordered:
    print(len(members), ' '.join(members))
""".lstrip(),
        # Correct grouping, but the groups keep their encounter order.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
words = line.split()
groups = {}
for w in words:
    groups.setdefault(''.join(sorted(w)), []).append(w)
print(len(groups))
for members in groups.values():
    members.sort()
    print(len(members), ' '.join(members))
""".lstrip(),
        # Collapses duplicate words, so the group sizes are too small.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
words = line.split()
groups = {}
for w in words:
    groups.setdefault(''.join(sorted(w)), set()).add(w)
ordered = sorted((sorted(v) for v in groups.values()), key=lambda m: m[0])
print(len(ordered))
for members in ordered:
    print(len(members), ' '.join(members))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  14 · Valid Parentheses                                                     #
# --------------------------------------------------------------------------- #

VALID_PARENTHESES = {
    "slug": "valid-parentheses",
    "skill_id": "dsa_arrays",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Valid Parentheses",
    "statement": (
        "A bracket string is valid when every opening bracket is closed by the "
        "matching kind of bracket, in the correct order, and no closing "
        "bracket appears without a matching opener.\n\n"
        "Print 1 if the given string is valid and 0 otherwise. The empty "
        "string is valid."
    ),
    "constraints": [
        "0 <= |s| <= 200000",
        "s contains only the characters ( ) [ ] { }",
        "The input line may be empty, which counts as valid",
        "An O(n) stack pass is expected",
    ],
    "input_format": "A single line containing s. The line may be empty.",
    "output_format": "A single integer: 1 if the bracket string is valid, otherwise 0.",
    "examples": [
        {
            "stdin": "()[]{}\n",
            "stdout": "1",
            "explanation": "Each pair opens and closes immediately, in matching kinds.",
        },
        {
            "stdin": "([)]\n",
            "stdout": "0",
            "explanation": "The brackets interleave, so the closing order is wrong.",
        },
    ],
    "criteria": [
        "Reject mismatched kinds such as ([)]",
        "Reject a closing bracket that arrives with nothing open",
        "Reject leftover open brackets at the end",
        "Accept the empty line",
    ],
    "io": {
        "mode": "line",
        "function": "is_valid_brackets",
        "todo": "return 1 if the bracket string is valid, otherwise 0",
        "reads": [{"name": "s", "type": "string"}],
        "args": ["s"],
        "returns": "int",
    },
    "reference": r"""
import sys

def main():
    s = sys.stdin.readline().rstrip('\n')
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    for ch in s:
        if ch in '([{':
            stack.append(ch)
        else:
            if not stack or stack.pop() != pairs[ch]:
                print(0)
                return
    print(1 if not stack else 0)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: valid", "stdin": "()[]{}\n", "hidden": False},
        {"name": "sample: interleaved", "stdin": "([)]\n", "hidden": False},
        {"name": "hidden: empty line", "stdin": "\n", "hidden": True},
        {"name": "hidden: closing first", "stdin": ")(\n", "hidden": True},
        {"name": "hidden: unclosed openers", "stdin": "(((\n", "hidden": True},
        {"name": "hidden: nested valid", "stdin": "{[()()]}\n", "hidden": True},
        {"name": "hidden: single closer", "stdin": "]\n", "hidden": True},
        {"name": "hidden: wrong kind at the end", "stdin": "([]{)\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _brackets_case(1409, 100000), "hidden": True},
    ],
    "wrong": [
        # Counts brackets without tracking order.
        r"""
import sys
s = sys.stdin.readline().rstrip('\n')
ok = (s.count('(') == s.count(')') and s.count('[') == s.count(']')
      and s.count('{') == s.count('}'))
print(1 if ok else 0)
""".lstrip(),
        # Never checks for leftover openers at the end.
        r"""
import sys
s = sys.stdin.readline().rstrip('\n')
pairs = {')': '(', ']': '[', '}': '{'}
stack = []
ok = 1
for ch in s:
    if ch in '([{':
        stack.append(ch)
    else:
        if not stack or stack.pop() != pairs[ch]:
            ok = 0
            break
print(ok)
""".lstrip(),
        # Ignores stack underflow: a closing bracket with nothing open is skipped
        # instead of rejected.
        r"""
import sys
s = sys.stdin.readline().rstrip('\n')
pairs = {')': '(', ']': '[', '}': '{'}
stack = []
ok = 1
for ch in s:
    if ch in '([{':
        stack.append(ch)
    elif stack and stack.pop() != pairs[ch]:
        ok = 0
        break
print(1 if ok and not stack else 0)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  15 · Valid Palindrome                                                      #
# --------------------------------------------------------------------------- #

VALID_PALINDROME = {
    "slug": "valid-palindrome",
    "skill_id": "dsa_arrays",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Valid Palindrome",
    "statement": (
        "A phrase is a palindrome when, after removing every character that is "
        "not a letter or a digit and converting the remaining letters to lower "
        "case, it reads the same forwards and backwards.\n\n"
        "Print 1 if the given line is a palindrome and 0 otherwise. A line "
        "with no letters or digits at all is a palindrome."
    ),
    "constraints": [
        "0 <= |s| <= 200000",
        "s may contain spaces, punctuation, digits and letters of both cases",
        "Digits count as content: 'a1a' is a palindrome, 'a1b' is not",
        "An O(n) two-pointer scan is expected",
    ],
    "input_format": "A single line containing s. The line may be empty and may contain spaces.",
    "output_format": "A single integer: 1 if s is a palindrome under the rules above, otherwise 0.",
    "examples": [
        {
            "stdin": "A man, a plan, a canal: Panama\n",
            "stdout": "1",
            "explanation": 'Stripped and lower-cased this is "amanaplanacanalpanama", a palindrome.',
        },
        {
            "stdin": "race a car\n",
            "stdout": "0",
            "explanation": '"raceacar" reversed is "racaecar", which differs.',
        },
    ],
    "criteria": [
        "Ignore punctuation and spaces but keep digits",
        "Compare case-insensitively",
        "Treat a line with no alphanumeric characters as a palindrome",
        "Run in O(n)",
    ],
    "io": {
        "mode": "line",
        "function": "is_palindrome",
        "todo": "return 1 if s reads the same both ways ignoring case and non-alphanumerics",
        "reads": [{"name": "s", "type": "string"}],
        "args": ["s"],
        "returns": "int",
    },
    "reference": r"""
import sys

def main():
    s = sys.stdin.readline().rstrip('\n')
    lo, hi = 0, len(s) - 1
    while lo < hi:
        while lo < hi and not s[lo].isalnum():
            lo += 1
        while lo < hi and not s[hi].isalnum():
            hi -= 1
        if s[lo].lower() != s[hi].lower():
            print(0)
            return
        lo += 1
        hi -= 1
    print(1)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: canal panama", "stdin": "A man, a plan, a canal: Panama\n", "hidden": False},
        {"name": "sample: race a car", "stdin": "race a car\n", "hidden": False},
        {"name": "hidden: empty line", "stdin": "\n", "hidden": True},
        {"name": "hidden: punctuation only", "stdin": ".,;:!?\n", "hidden": True},
        {"name": "hidden: digits palindrome", "stdin": "a1a\n", "hidden": True},
        # Letters alone read the same both ways; the digit is what breaks it, so
        # a solution that filters with isalpha instead of isalnum answers 1 here.
        {"name": "hidden: digits break it", "stdin": "1aa\n", "hidden": True},
        {"name": "hidden: case only", "stdin": "Aa\n", "hidden": True},
        {"name": "hidden: single character", "stdin": "z\n", "hidden": True},
        {"name": "hidden: digits dropped by isalpha", "stdin": "a1b2a\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": (
                lambda half: half + half[::-1] + "\n"
            )(_random_string(1511, 100000, "abcXYZ .,!0123")),
            "hidden": True,
        },
    ],
    "wrong": [
        # Forgets to normalise case.
        r"""
import sys
s = sys.stdin.readline().rstrip('\n')
kept = [c for c in s if c.isalnum()]
print(1 if kept == kept[::-1] else 0)
""".lstrip(),
        # Compares the raw line, punctuation and all.
        r"""
import sys
s = sys.stdin.readline().rstrip('\n').lower()
print(1 if s == s[::-1] else 0)
""".lstrip(),
        # Keeps letters only, silently dropping digits.
        r"""
import sys
s = sys.stdin.readline().rstrip('\n')
kept = [c.lower() for c in s if c.isalpha()]
print(1 if kept == kept[::-1] else 0)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  16 · Longest Palindromic Substring                                         #
# --------------------------------------------------------------------------- #

LONGEST_PALINDROME = {
    "slug": "longest-palindrome-length",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 35,
    "title": "Longest Palindromic Substring",
    "statement": (
        "Given a string s, find its longest contiguous palindromic substring.\n\n"
        "Several different substrings can tie for longest, so the substring "
        "itself is not a well-defined answer — its length is. Print the length "
        "of the longest palindromic substring, which is the same number for "
        "every correct solution. For an empty line the answer is 0."
    ),
    "constraints": [
        "0 <= |s| <= 3000",
        "s contains lowercase letters a-z",
        "Both odd-length and even-length palindromes must be considered",
        "An O(n^2) expand-around-centre solution is fast enough here",
    ],
    "input_format": "A single line containing s. The line may be empty.",
    "output_format": "A single integer: the length of the longest palindromic substring.",
    "examples": [
        {
            "stdin": "babad\n",
            "stdout": "3",
            "explanation": '"bab" and "aba" both have length 3, and the length is what is printed.',
        },
        {
            "stdin": "cbbd\n",
            "stdout": "2",
            "explanation": '"bb" is the longest palindrome, of even length 2.',
        },
    ],
    "criteria": [
        "Consider even-length centres as well as odd-length ones",
        "Return 0 for an empty line and 1 for a string with no repeats",
        "Do not confuse the longest palindrome with the longest common substring "
        "between s and its reverse",
    ],
    "io": {
        "mode": "line",
        "function": "longest_palindrome_length",
        "todo": "return the length of the longest palindromic substring of s",
        "reads": [{"name": "s", "type": "string"}],
        "args": ["s"],
        "returns": "int",
    },
    "reference": r"""
import sys

def main():
    s = sys.stdin.readline().rstrip('\n')
    n = len(s)
    best = 0
    for centre in range(n):
        lo, hi = centre, centre
        while lo >= 0 and hi < n and s[lo] == s[hi]:
            lo -= 1
            hi += 1
        if hi - lo - 1 > best:
            best = hi - lo - 1
        lo, hi = centre, centre + 1
        while lo >= 0 and hi < n and s[lo] == s[hi]:
            lo -= 1
            hi += 1
        if hi - lo - 1 > best:
            best = hi - lo - 1
    print(best)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: babad", "stdin": "babad\n", "hidden": False},
        {"name": "sample: cbbd", "stdin": "cbbd\n", "hidden": False},
        {"name": "hidden: empty line", "stdin": "\n", "hidden": True},
        {"name": "hidden: single character", "stdin": "a\n", "hidden": True},
        {"name": "hidden: no repeats", "stdin": "abcdefg\n", "hidden": True},
        {"name": "hidden: even palindrome only", "stdin": "abba\n", "hidden": True},
        {"name": "hidden: reverse-substring trap", "stdin": "abacdfgdcaba\n", "hidden": True},
        {"name": "hidden: whole string", "stdin": "aaaaa\n", "hidden": True},
        {"name": "hidden: palindrome at the end", "stdin": "xyzracecar\n", "hidden": True},
        {"name": "hidden: scale all equal", "stdin": "a" * 3000 + "\n", "hidden": True},
        {
            "name": "hidden: scale random",
            "stdin": _random_string(1601, 3000, "abc") + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Only expands odd-length centres.
        r"""
import sys
s = sys.stdin.readline().rstrip('\n')
n = len(s)
best = 0 if n == 0 else 1
for c in range(n):
    lo, hi = c, c
    while lo >= 0 and hi < n and s[lo] == s[hi]:
        lo -= 1
        hi += 1
    best = max(best, hi - lo - 1)
print(best)
""".lstrip(),
        # Longest common substring with the reverse: fails on abacdfgdcaba.
        r"""
import sys
s = sys.stdin.readline().rstrip('\n')
r = s[::-1]
n = len(s)
best = 0
prev = [0] * (n + 1)
for i in range(1, n + 1):
    cur = [0] * (n + 1)
    for j in range(1, n + 1):
        if s[i-1] == r[j-1]:
            cur[j] = prev[j-1] + 1
            if cur[j] > best:
                best = cur[j]
    prev = cur
print(best)
""".lstrip(),
        # Off-by-one on the expansion bounds: reports two characters too many.
        r"""
import sys
s = sys.stdin.readline().rstrip('\n')
n = len(s)
best = 0
for c in range(n):
    lo, hi = c, c
    while lo >= 0 and hi < n and s[lo] == s[hi]:
        lo -= 1
        hi += 1
    best = max(best, hi - lo)
    lo, hi = c, c + 1
    while lo >= 0 and hi < n and s[lo] == s[hi]:
        lo -= 1
        hi += 1
    best = max(best, hi - lo)
print(best)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  17 · Palindromic Substrings                                                #
# --------------------------------------------------------------------------- #

COUNT_PALINDROMES = {
    "slug": "count-palindromic-substrings",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Palindromic Substrings",
    "statement": (
        "Count how many substrings of s are palindromes.\n\n"
        "Substrings are counted by position, not by content: in \"aaa\" the "
        'substrings "a", "a", "a", "aa", "aa" and "aaa" give a total of 6, '
        'even though only three distinct strings appear. Every single '
        "character is a palindrome."
    ),
    "constraints": [
        "0 <= |s| <= 3000",
        "s contains lowercase letters a-z",
        "The count reaches about 4.5 million, which fits in a 32-bit int, but "
        "the generated starters use 64-bit values throughout",
        "An O(n^2) expand-around-centre solution is fast enough here",
    ],
    "input_format": "A single line containing s. The line may be empty.",
    "output_format": "A single integer: the number of palindromic substrings, counted by position.",
    "examples": [
        {
            "stdin": "abc\n",
            "stdout": "3",
            "explanation": 'Only the single characters "a", "b" and "c" are palindromes.',
        },
        {
            "stdin": "aaa\n",
            "stdout": "6",
            "explanation": 'Three single characters, two occurrences of "aa" and one "aaa".',
        },
    ],
    "criteria": [
        "Count occurrences, not distinct palindromes",
        "Count even-length palindromes as well as odd-length ones",
        "Return 0 for an empty line",
    ],
    "io": {
        "mode": "line",
        "function": "count_palindromic_substrings",
        "todo": "return how many substrings of s are palindromes, counted by position",
        "reads": [{"name": "s", "type": "string"}],
        "args": ["s"],
        "returns": "long",
    },
    "reference": r"""
import sys

def main():
    s = sys.stdin.readline().rstrip('\n')
    n = len(s)
    total = 0
    for centre in range(n):
        lo, hi = centre, centre
        while lo >= 0 and hi < n and s[lo] == s[hi]:
            total += 1
            lo -= 1
            hi += 1
        lo, hi = centre, centre + 1
        while lo >= 0 and hi < n and s[lo] == s[hi]:
            total += 1
            lo -= 1
            hi += 1
    print(total)

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: abc", "stdin": "abc\n", "hidden": False},
        {"name": "sample: aaa", "stdin": "aaa\n", "hidden": False},
        {"name": "hidden: empty line", "stdin": "\n", "hidden": True},
        {"name": "hidden: single character", "stdin": "z\n", "hidden": True},
        {"name": "hidden: even palindrome", "stdin": "abba\n", "hidden": True},
        {"name": "hidden: repeated pairs", "stdin": "aabaa\n", "hidden": True},
        {"name": "hidden: no repeats", "stdin": "abcdef\n", "hidden": True},
        {"name": "hidden: scale all equal", "stdin": "a" * 3000 + "\n", "hidden": True},
        {
            "name": "hidden: scale random",
            "stdin": _random_string(1709, 3000, "ab") + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Counts distinct palindromic strings rather than occurrences.
        r"""
import sys
s = sys.stdin.readline().rstrip('\n')
n = len(s)
found = set()
for c in range(n):
    lo, hi = c, c
    while lo >= 0 and hi < n and s[lo] == s[hi]:
        found.add(s[lo:hi+1])
        lo -= 1
        hi += 1
    lo, hi = c, c + 1
    while lo >= 0 and hi < n and s[lo] == s[hi]:
        found.add(s[lo:hi+1])
        lo -= 1
        hi += 1
print(len(found))
""".lstrip(),
        # Misses even-length palindromes.
        r"""
import sys
s = sys.stdin.readline().rstrip('\n')
n = len(s)
total = 0
for c in range(n):
    lo, hi = c, c
    while lo >= 0 and hi < n and s[lo] == s[hi]:
        total += 1
        lo -= 1
        hi += 1
print(total)
""".lstrip(),
        # Counts single characters plus equal adjacent pairs only.
        r"""
import sys
s = sys.stdin.readline().rstrip('\n')
n = len(s)
print(n + sum(1 for i in range(n - 1) if s[i] == s[i+1]))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  18 · Encode and Decode Strings                                             #
# --------------------------------------------------------------------------- #

DECODE_STRINGS = {
    "slug": "decode-encoded-strings",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Encode and Decode Strings",
    "statement": (
        "The original exercise asks for a pair of functions: encode(list) -> "
        "string and decode(string) -> list, such that decoding an encoded list "
        "returns exactly the original list. The encoding is your own choice, "
        "so there is no single correct stdout for the encode half — which is "
        "why this version fixes the wire format and judges the decode half, "
        "the part that actually has to be exact.\n\n"
        "stdin is a list that has already been encoded with the length-prefix "
        "scheme: each string is written as its length in decimal, then a '#', "
        "then exactly that many characters, and the pieces are concatenated "
        'with nothing between them. So ["ab", "", "c#d"] becomes '
        '"2#ab0#3#c#d".\n\n'
        "Recover the original list and print it: the number of strings, then "
        "each string on its own line, exactly as it was. Empty strings are "
        "real elements and print as empty lines; payloads may contain '#', "
        "digits and spaces, and the length prefix is the only thing that says "
        "where a string ends.\n\n"
        "The empty line encodes the empty list, so the answer is 0 and nothing "
        "else."
    ),
    "constraints": [
        "0 <= length of the encoded line <= 200000",
        "Payload characters are printable ASCII other than newline, and may "
        "include '#', digits and spaces",
        "Strings may be empty, and an empty list is possible",
        "The length prefix has no fixed width: it may be 0, or three digits",
        "Because the payloads carry their own spaces, the strings must be "
        "reproduced character for character, one per line",
    ],
    "input_format": (
        "A single line: the encoded blob. Each element is <length>#<payload> "
        "with the payload being exactly <length> characters. The line may be "
        "empty."
    ),
    "output_format": (
        "Line 1: m, the number of strings in the decoded list.\n"
        "Then m lines, each holding one recovered string exactly as it was, in "
        "the original order. An empty string prints as an empty line. Print "
        "only the 0 when the list is empty."
    ),
    "examples": [
        {
            "stdin": "2#ab0#3#c#d\n",
            "stdout": "3\nab\n\nc#d",
            "explanation": (
                'The list is ["ab", "", "c#d"]. The second element is the empty '
                "string, which is why line 3 of the output is blank, and the '#' "
                'inside "c#d" is payload rather than a separator.'
            ),
        },
        {
            "stdin": "1#a\n",
            "stdout": "1\na",
            "explanation": 'The list is ["a"]: one string, printed on the line after the count.',
        },
    ],
    "criteria": [
        "Use the length prefix to slice the payload; never split on '#'",
        "Preserve empty strings, which still occupy a line in the output",
        "Handle payloads that contain '#', digits and spaces",
        "Handle the empty line as the empty list",
    ],
    "io": {
        "mode": "line",
        "function": "decode_strings",
        "todo": (
            "decode the length-prefixed line into a list of strings, then print m and "
            "the m strings one per line (replace the single-value print in main)"
        ),
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "long",
    },
    "reference": r"""
import sys

def main():
    line = sys.stdin.readline().rstrip('\n')
    pos = 0
    out = []
    n = len(line)
    while pos < n:
        hash_at = line.index('#', pos)
        length = int(line[pos:hash_at])
        out.append(line[hash_at + 1:hash_at + 1 + length])
        pos = hash_at + 1 + length
    sys.stdout.write(str(len(out)) + '\n')
    for value in out:
        sys.stdout.write(value + '\n')

main()
""".lstrip(),
    "inputs": [
        {"name": "sample: three strings", "stdin": "2#ab0#3#c#d\n", "hidden": False},
        {"name": "sample: one string", "stdin": "1#a\n", "hidden": False},
        {"name": "hidden: empty line", "stdin": "\n", "hidden": True},
        {"name": "hidden: single empty string", "stdin": "0#\n", "hidden": True},
        {"name": "hidden: several empty strings", "stdin": "0#0#0#\n", "hidden": True},
        {"name": "hidden: payload is all hashes", "stdin": "3####\n", "hidden": True},
        {"name": "hidden: digits in payload", "stdin": "3#1235#hello\n", "hidden": True},
        {"name": "hidden: spaces in payload", "stdin": "5#a b c\n", "hidden": True},
        {"name": "hidden: multi-digit length", "stdin": "12#abcdefghijkl\n", "hidden": True},
        {"name": "hidden: empty then hashes", "stdin": "0#1##2###\n", "hidden": True},
        {"name": "hidden: empty string last", "stdin": "1#a0#\n", "hidden": True},
        # The payload " a " is padded on both sides, so trimming it is wrong.
        {"name": "hidden: padded payload", "stdin": "3# a 0#\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _encoded_case(1801, 4000), "hidden": True},
    ],
    "wrong": [
        # Splits on '#', which destroys payloads containing the delimiter.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
parts = line.split('#')
strings = []
i = 0
while i + 1 < len(parts):
    strings.append(parts[i + 1])
    i += 2
print(len(strings))
for s in strings:
    print(s)
""".lstrip(),
        # Drops empty strings, so both the count and the lines are short.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
pos = 0
out = []
n = len(line)
while pos < n:
    h = line.index('#', pos)
    length = int(line[pos:h])
    payload = line[h + 1:h + 1 + length]
    pos = h + 1 + length
    if length == 0:
        continue
    out.append(payload)
print(len(out))
for s in out:
    print(s)
""".lstrip(),
        # Assumes the length prefix is a single digit.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
pos = 0
out = []
n = len(line)
while pos < n:
    length = int(line[pos])
    out.append(line[pos + 2:pos + 2 + length])
    pos = pos + 2 + length
print(len(out))
for s in out:
    print(s)
""".lstrip(),
        # Strips whitespace from each recovered string, which is fine until a
        # payload legitimately begins or ends with a space.
        r"""
import sys
line = sys.stdin.readline().rstrip('\n')
pos = 0
out = []
n = len(line)
while pos < n:
    h = line.index('#', pos)
    length = int(line[pos:h])
    out.append(line[h + 1:h + 1 + length].strip())
    pos = h + 1 + length
print(len(out))
for s in out:
    print(s)
""".lstrip(),
    ],
}


PROBLEMS: list[dict[str, Any]] = [
    TWO_SUM,
    CONTAINS_DUPLICATE,
    PRODUCT_EXCEPT_SELF,
    MAX_PRODUCT_SUBARRAY,
    FIND_MIN_ROTATED,
    SEARCH_ROTATED,
    THREE_SUM,
    CONTAINER_WATER,
    BEST_TIME_STOCK,
    CHAR_REPLACEMENT,
    MIN_WINDOW,
    VALID_ANAGRAM,
    GROUP_ANAGRAMS,
    VALID_PARENTHESES,
    VALID_PALINDROME,
    LONGEST_PALINDROME,
    COUNT_PALINDROMES,
    DECODE_STRINGS,
]
