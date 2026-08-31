"""Competitive-programming problem set (stdin/stdout, LeetCode-style judging).

Authoring contract
------------------
The full contract, including every required key and the language-specific traps
(integer width, Java I/O and time limits), lives in
``backend/docs/curriculum_authoring.md``. Read it before adding a problem.

Expected outputs are never written by hand. Each problem carries:

* ``reference``  — a correct Python solution, the single source of truth.
* ``inputs``     — visible and hidden stdin payloads, including seeded large
                   cases that a hardcoded answer cannot survive.
* ``wrong``      — plausible-but-broken solutions.
* ``io``         — a declarative description of the stdin shape, from which
                   :mod:`app.data.curriculum_starters` generates the starter
                   code for all five supported languages.

``scripts/build_test_cases.py`` runs the reference over every input to *generate*
``expected_stdout``, then asserts that (a) the reference passes the generated
suite and (b) every wrong solution fails at least one case. A problem that
cannot satisfy both is a build failure, so "any code passes everything" is
structurally impossible rather than a matter of review diligence.

Nothing in this module is imported at request time for grading; it is data.
"""

from __future__ import annotations

import random
from typing import Any

# --------------------------------------------------------------------------- #
#  Deterministic input generation                                             #
# --------------------------------------------------------------------------- #
# Seeded so the suite is reproducible: the same commit always grades the same
# way, while the values remain large and irregular enough to defeat lookup
# tables keyed on the sample cases.


def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def _array_case(seed: int, n: int, lo: int, hi: int, extra: str = "") -> str:
    rng = _rng(seed)
    values = [rng.randint(lo, hi) for _ in range(n)]
    header = f"{n} {extra}".strip()
    return f"{header}\n{' '.join(map(str, values))}\n"


def _platform_scale_case(seed: int, n: int) -> str:
    """Large unsorted timetable with heavy but not total overlap."""
    rng = _rng(seed)
    pairs = []
    for _ in range(n):
        start = rng.randint(0, 1_400_000)
        pairs.append((start, start + rng.randint(0, 5_000)))
    rng.shuffle(pairs)
    arrivals = " ".join(str(a) for a, _ in pairs)
    departures = " ".join(str(d) for _, d in pairs)
    return f"{n}\n{arrivals}\n{departures}\n"


def _random_string(seed: int, length: int, alphabet: str) -> str:
    rng = _rng(seed)
    return "".join(rng.choice(alphabet) for _ in range(length))


# --------------------------------------------------------------------------- #
#  01 · Maximum subarray sum                                                  #
# --------------------------------------------------------------------------- #

MAX_SUBARRAY = {
    "slug": "max-subarray-sum",
    "skill_id": "dsa_arrays",
    "difficulty": 4,
    "estimated_minutes": 25,
    "title": "Maximum Subarray Sum",
    "statement": (
        "Given an array of n integers, find the largest sum obtainable from a "
        "contiguous, non-empty subarray.\n\n"
        "The array may be entirely negative, in which case the answer is the "
        "single largest element."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= arr[i] <= 1000000000",
        "The answer can reach 2 * 10^14, so it does not fit in a 32-bit int: "
        "use long long in C/C++ and long in Java",
        "Time limit favours an O(n) scan; O(n^2) will time out on hidden cases",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": "A single integer: the maximum subarray sum.",
    "examples": [
        {
            "stdin": "9\n-2 1 -3 4 -1 2 1 -5 4\n",
            "stdout": "6",
            "explanation": "The subarray [4, -1, 2, 1] sums to 6.",
        },
        {
            "stdin": "5\n-8 -3 -6 -2 -5\n",
            "stdout": "-2",
            "explanation": "All values are negative, so the best is the single largest element.",
        },
    ],
    "criteria": [
        "Handle an all-negative array without returning 0",
        "Handle n = 1",
        "Run in O(n) time and O(1) extra space",
    ],
    "io": {
        "mode": "tokens",
        "function": "max_subarray_sum",
        "todo": "return the largest sum of a contiguous non-empty subarray",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr"],
        "returns": "long",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.read().split()\n"
        "    n = int(data[0])\n"
        "    arr = [int(x) for x in data[1:1 + n]]\n"
        "    best = cur = arr[0]\n"
        "    for value in arr[1:]:\n"
        "        cur = max(value, cur + value)\n"
        "        best = max(best, cur)\n"
        "    print(best)\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: mixed signs", "stdin": "9\n-2 1 -3 4 -1 2 1 -5 4\n", "hidden": False},
        {"name": "sample: all negative", "stdin": "5\n-8 -3 -6 -2 -5\n", "hidden": False},
        {"name": "hidden: single element", "stdin": "1\n-7\n", "hidden": True},
        {"name": "hidden: all positive", "stdin": "4\n2 3 1 5\n", "hidden": True},
        {"name": "hidden: zeros and negatives", "stdin": "6\n0 -1 0 -2 0 -3\n", "hidden": True},
        {"name": "hidden: large magnitudes", "stdin": "3\n1000000000 -1 1000000000\n", "hidden": True},
        # Scale case: quadratic solutions cannot finish this inside the limit.
        {"name": "hidden: scale", "stdin": _array_case(11, 200000, -10**9, 10**9), "hidden": True},
    ],
    "wrong": [
        # Returns 0 for an all-negative array (the classic off-by-initialisation bug).
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); arr = [int(x) for x in data[1:1+n]]\n"
            "best = 0; cur = 0\n"
            "for v in arr:\n"
            "    cur = max(0, cur + v); best = max(best, cur)\n"
            "print(best)\n"
        ),
        # Hardcodes the visible samples.
        (
            "import sys\n"
            "data = sys.stdin.read().strip()\n"
            "print(6 if data.startswith('9') else -2)\n"
        ),
        # Sums the whole array instead of the best subarray.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); arr = [int(x) for x in data[1:1+n]]\n"
            "print(sum(arr))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  02 · Longest substring without repeating characters                        #
# --------------------------------------------------------------------------- #

LONGEST_UNIQUE = {
    "slug": "longest-unique-substring",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Longest Substring Without Repeating Characters",
    "statement": (
        "Given a string s, return the length of the longest contiguous "
        "substring that contains no repeated character.\n\n"
        "The string may be empty, in which case the answer is 0."
    ),
    "constraints": [
        "0 <= |s| <= 200000",
        "s contains printable ASCII characters without whitespace",
        "An O(n) sliding window is expected",
    ],
    "input_format": "A single line containing s. The line may be empty.",
    "output_format": "A single integer: the length of the longest substring with all distinct characters.",
    "examples": [
        {"stdin": "abcabcbb\n", "stdout": "3", "explanation": '"abc" has length 3.'},
        {"stdin": "bbbbb\n", "stdout": "1", "explanation": 'Only "b" is distinct.'},
    ],
    "criteria": [
        "Return 0 for an empty input line",
        "Handle a string where every character is identical",
        "Use a sliding window rather than checking every substring",
    ],
    "io": {
        "mode": "line",
        "function": "longest_unique",
        "todo": "return the length of the longest substring with no repeated character",
        "reads": [{"name": "s", "type": "string"}],
        "args": ["s"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    s = sys.stdin.readline().rstrip('\\n')\n"
        "    last = {}\n"
        "    best = 0\n"
        "    start = 0\n"
        "    for index, ch in enumerate(s):\n"
        "        if ch in last and last[ch] >= start:\n"
        "            start = last[ch] + 1\n"
        "        last[ch] = index\n"
        "        best = max(best, index - start + 1)\n"
        "    print(best)\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: abcabcbb", "stdin": "abcabcbb\n", "hidden": False},
        {"name": "sample: repeated char", "stdin": "bbbbb\n", "hidden": False},
        {"name": "hidden: empty line", "stdin": "\n", "hidden": True},
        {"name": "hidden: all distinct", "stdin": "abcdefg\n", "hidden": True},
        {"name": "hidden: pattern pwwkew", "stdin": "pwwkew\n", "hidden": True},
        {"name": "hidden: symbols", "stdin": "a!a!!b#b#c\n", "hidden": True},
        # These two repeat a character *inside* the window rather than at its
        # edge. Solutions that clear the window on a repeat, instead of moving
        # the start past the previous occurrence, undercount here and nowhere
        # else in this suite.
        {"name": "hidden: repeat inside window", "stdin": "abac\n", "hidden": True},
        {"name": "hidden: dvdf", "stdin": "dvdf\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": _random_string(23, 200000, "abcdefghijklmnopqrstuvwxyz") + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Counts distinct characters overall instead of a contiguous window.
        ("import sys\ns = sys.stdin.readline().rstrip('\\n')\nprint(len(set(s)))\n"),
        # Resets the window to 1 on a repeat, losing the correct start position.
        (
            "import sys\n"
            "s = sys.stdin.readline().rstrip('\\n')\n"
            "best = cur = 0\n"
            "seen = set()\n"
            "for ch in s:\n"
            "    if ch in seen:\n"
            "        seen = {ch}; cur = 1\n"
            "    else:\n"
            "        seen.add(ch); cur += 1\n"
            "    best = max(best, cur)\n"
            "print(best)\n"
        ),
        # Hardcodes the samples.
        ("import sys\ns = sys.stdin.readline().strip()\nprint(3 if s.startswith('abc') else 1)\n"),
    ],
}


# --------------------------------------------------------------------------- #
#  03 · Minimum platforms                                                     #
# --------------------------------------------------------------------------- #

MIN_PLATFORMS = {
    "slug": "min-platforms",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 35,
    "title": "Minimum Number of Platforms",
    "statement": (
        "A station receives n trains. Train i arrives at arr[i] and departs at "
        "dep[i], both as minutes past midnight. A platform can hold one train "
        "at a time, and a train that departs at exactly the minute another "
        "arrives still occupies the platform for that minute.\n\n"
        "Find the minimum number of platforms needed so that no train waits."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "0 <= arr[i] <= dep[i] <= 1440000",
        "Arrival and departure lists are not sorted",
    ],
    "input_format": (
        "Line 1: n.\nLine 2: n arrival times.\nLine 3: n departure times."
    ),
    "output_format": "A single integer: the minimum number of platforms required.",
    "examples": [
        {
            "stdin": "6\n900 940 950 1100 1500 1800\n910 1200 1120 1130 1900 2000\n",
            "stdout": "3",
            "explanation": "Between 950 and 1120 three trains are present at once.",
        },
        {
            "stdin": "2\n100 200\n100 200\n",
            "stdout": "1",
            "explanation": "Each train arrives and departs in the same minute, one after the other.",
        },
    ],
    "criteria": [
        "Treat a departure at the same minute as an arrival as overlapping",
        "Do not assume the input is sorted",
        "Use an O(n log n) sweep rather than comparing every pair",
    ],
    "io": {
        "mode": "tokens",
        "function": "min_platforms",
        "todo": "return the minimum number of platforms required",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "arrivals", "type": "long", "count": "n"},
            {"name": "departures", "type": "long", "count": "n"},
        ],
        "args": ["arrivals", "departures"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.read().split()\n"
        "    n = int(data[0])\n"
        "    arr = sorted(int(x) for x in data[1:1 + n])\n"
        "    dep = sorted(int(x) for x in data[1 + n:1 + 2 * n])\n"
        "    i = j = 0\n"
        "    current = best = 0\n"
        "    while i < n:\n"
        "        if arr[i] <= dep[j]:\n"
        "            current += 1\n"
        "            best = max(best, current)\n"
        "            i += 1\n"
        "        else:\n"
        "            current -= 1\n"
        "            j += 1\n"
        "    print(best)\n"
        "main()\n"
    ),
    "inputs": [
        {
            "name": "sample: six trains",
            "stdin": "6\n900 940 950 1100 1500 1800\n910 1200 1120 1130 1900 2000\n",
            "hidden": False,
        },
        {"name": "sample: same minute", "stdin": "2\n100 200\n100 200\n", "hidden": False},
        {"name": "hidden: single train", "stdin": "1\n500\n600\n", "hidden": True},
        {"name": "hidden: all overlap", "stdin": "4\n0 0 0 0\n10 10 10 10\n", "hidden": True},
        {"name": "hidden: unsorted input", "stdin": "3\n300 100 200\n400 150 250\n", "hidden": True},
        {"name": "hidden: no overlap", "stdin": "3\n0 100 200\n50 150 250\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _platform_scale_case(31, 200000), "hidden": True},
    ],
    "wrong": [
        # Off-by-one on simultaneous arrival/departure (uses < instead of <=).
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0])\n"
            "arr = sorted(int(x) for x in data[1:1+n])\n"
            "dep = sorted(int(x) for x in data[1+n:1+2*n])\n"
            "i=j=0; cur=best=0\n"
            "while i < n:\n"
            "    if arr[i] < dep[j]:\n"
            "        cur+=1; best=max(best,cur); i+=1\n"
            "    else:\n"
            "        cur-=1; j+=1\n"
            "print(best)\n"
        ),
        # Assumes the input arrives sorted.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0])\n"
            "arr = [int(x) for x in data[1:1+n]]\n"
            "dep = [int(x) for x in data[1+n:1+2*n]]\n"
            "i=j=0; cur=best=0\n"
            "while i < n:\n"
            "    if arr[i] <= dep[j]:\n"
            "        cur+=1; best=max(best,cur); i+=1\n"
            "    else:\n"
            "        cur-=1; j+=1\n"
            "print(best)\n"
        ),
        # Returns n, which is right only when everything overlaps.
        ("import sys\ndata = sys.stdin.read().split()\nprint(int(data[0]))\n"),
    ],
}


# --------------------------------------------------------------------------- #
#  04 · Count pairs with a given difference                                   #
# --------------------------------------------------------------------------- #

PAIRS_WITH_DIFF = {
    "slug": "pairs-with-difference",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Count Distinct Pairs With a Given Difference",
    "statement": (
        "Given an array of n integers and a target d, count the number of "
        "distinct value pairs (a, b) with a - b == d.\n\n"
        "Pairs are counted by value, not by index: if a value appears many "
        "times, the pair it forms is still counted once. When d is 0, count "
        "each value that appears at least twice."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "0 <= d <= 1000000000",
        "-1000000000 <= arr[i] <= 1000000000",
        "Duplicate values are common in the hidden cases",
    ],
    "input_format": "Line 1: n and d separated by a space.\nLine 2: n space-separated integers.",
    "output_format": "A single integer: the number of distinct pairs.",
    "examples": [
        {
            "stdin": "5 2\n1 5 3 4 2\n",
            "stdout": "3",
            "explanation": "(3,1), (4,2) and (5,3) differ by 2.",
        },
        {
            "stdin": "6 0\n1 1 2 2 3 4\n",
            "stdout": "2",
            "explanation": "Only 1 and 2 appear more than once.",
        },
    ],
    "criteria": [
        "Count pairs by value, so duplicates never inflate the answer",
        "Handle d = 0 as 'values occurring at least twice'",
        "Use a set or map rather than comparing every pair",
    ],
    "io": {
        "mode": "tokens",
        "function": "count_pairs",
        "todo": "return the number of distinct value pairs (a, b) with a - b == d",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "d", "type": "long"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr", "d"],
        "returns": "long",
    },
    "reference": (
        "import sys\n"
        "from collections import Counter\n"
        "def main():\n"
        "    data = sys.stdin.read().split()\n"
        "    n, d = int(data[0]), int(data[1])\n"
        "    arr = [int(x) for x in data[2:2 + n]]\n"
        "    counts = Counter(arr)\n"
        "    if d == 0:\n"
        "        print(sum(1 for value in counts.values() if value >= 2))\n"
        "        return\n"
        "    print(sum(1 for value in counts if value + d in counts))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: d = 2", "stdin": "5 2\n1 5 3 4 2\n", "hidden": False},
        {"name": "sample: d = 0", "stdin": "6 0\n1 1 2 2 3 4\n", "hidden": False},
        {"name": "hidden: no pairs", "stdin": "4 100\n1 2 3 4\n", "hidden": True},
        {"name": "hidden: heavy duplicates", "stdin": "8 1\n1 1 1 2 2 2 3 3\n", "hidden": True},
        {"name": "hidden: negatives", "stdin": "5 3\n-5 -2 0 1 -8\n", "hidden": True},
        {"name": "hidden: single element", "stdin": "1 0\n42\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": _array_case(47, 200000, -100000, 100000, extra="7"),
            "hidden": True,
        },
    ],
    "wrong": [
        # Counts index pairs, so duplicates inflate the total.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n, d = int(data[0]), int(data[1])\n"
            "arr = [int(x) for x in data[2:2+n]]\n"
            "s = set(arr)\n"
            "print(sum(1 for v in arr if v + d in s))\n"
        ),
        # Ignores the d = 0 rule and counts every distinct value.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n, d = int(data[0]), int(data[1])\n"
            "arr = [int(x) for x in data[2:2+n]]\n"
            "s = set(arr)\n"
            "print(sum(1 for v in s if v + d in s))\n"
        ),
        # O(n^2) brute force: correct but cannot finish the scale case.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n, d = int(data[0]), int(data[1])\n"
            "arr = sorted(set(int(x) for x in data[2:2+n]))\n"
            "count = 0\n"
            "for i in range(len(arr)):\n"
            "    for j in range(len(arr)):\n"
            "        if arr[i] - arr[j] == d and (d != 0 or i != j):\n"
            "            count += 1\n"
            "print(count if d != 0 else 0)\n"
        ),
    ],
}


CP_PROBLEMS: list[dict[str, Any]] = [
    MAX_SUBARRAY,
    LONGEST_UNIQUE,
    MIN_PLATFORMS,
    PAIRS_WITH_DIFF,
]
