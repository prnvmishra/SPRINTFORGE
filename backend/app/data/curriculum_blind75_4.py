"""Blind 75 problems, batch 4.

Split across files so the catalogue can grow without one unreadable module.
Each entry follows the contract in `docs/curriculum_authoring.md`: an `io`
spec drives starter generation for every language, `reference` derives the
expected outputs, and `wrong` solutions must be rejected by the case bank.

Batch 4 covers dynamic programming, graphs and matrix manipulation. Because
this platform judges stdin to stdout rather than a function signature, the
Blind 75 statements are re-specified here with explicit serialisations:

*Graphs* — line 1 holds ``n m`` (vertices labelled ``1..n`` and edge count),
line 2 holds the ``m`` edge sources and line 3 the ``m`` edge targets, so that
edge ``i`` is ``src[i] -> dst[i]``. The two parallel lines are used instead of
one edge per line because the declarative ``io`` spec (and therefore the
generated C starter, which must name the length of every array it receives)
can only express arrays whose length is a single input variable. Parsing is
whitespace-insensitive, so a learner may still think of it as an edge list.
Every graph problem states whether it is directed and whether it may be
disconnected.

*Matrix* — line 1 holds ``r c``, followed by the ``r * c`` values in
row-major order. The count is not on stdin: it is derivable from r and c, and
a redundant token there silently shifts the input of anyone who computes it
themselves. Starters get it from the ``value`` field of a derived read.
"""

from __future__ import annotations

import random
from typing import Any


# --------------------------------------------------------------------------- #
#  Deterministic case generators                                              #
# --------------------------------------------------------------------------- #


def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def _array_case(seed: int, n: int, lo: int, hi: int, header: str = "") -> str:
    rng = _rng(seed)
    values = [rng.randint(lo, hi) for _ in range(n)]
    first = f"{n} {header}".strip()
    return f"{first}\n{' '.join(map(str, values))}\n"


def _string_case(seed: int, length: int, alphabet: str) -> str:
    rng = _rng(seed)
    return "".join(rng.choice(alphabet) for _ in range(length))


def _undirected_graph_case(
    seed: int, n: int, extra_edges: int, components: int = 1
) -> str:
    """Connected-per-component random simple graph, 1-indexed, no self-loops."""
    rng = _rng(seed)
    labels = list(range(1, n + 1))
    rng.shuffle(labels)
    blocks: list[list[int]] = [[] for _ in range(components)]
    for index, label in enumerate(labels):
        blocks[index % components].append(label)

    edges: set[tuple[int, int]] = set()
    for block in blocks:
        for i in range(1, len(block)):
            u, v = block[i], block[rng.randrange(i)]
            edges.add((min(u, v), max(u, v)))
    attempts = 0
    while len(edges) < sum(max(len(b) - 1, 0) for b in blocks) + extra_edges:
        attempts += 1
        if attempts > extra_edges * 20 + 100:
            break
        block = blocks[rng.randrange(components)]
        if len(block) < 2:
            continue
        u = block[rng.randrange(len(block))]
        v = block[rng.randrange(len(block))]
        if u != v:
            edges.add((min(u, v), max(u, v)))

    ordered = sorted(edges)
    rng.shuffle(ordered)
    srcs = " ".join(str(u) for u, _ in ordered)
    dsts = " ".join(str(v) for _, v in ordered)
    return f"{n} {len(ordered)}\n{srcs}\n{dsts}\n"


def _dag_case(seed: int, n: int, m: int) -> str:
    """Random directed acyclic graph over a hidden topological permutation."""
    rng = _rng(seed)
    order = list(range(1, n + 1))
    rng.shuffle(order)
    edges: set[tuple[int, int]] = set()
    guard = 0
    while len(edges) < m and guard < m * 20:
        guard += 1
        i = rng.randrange(n)
        j = rng.randrange(n)
        if i == j:
            continue
        lo, hi = (i, j) if i < j else (j, i)
        edges.add((order[lo], order[hi]))
    ordered = sorted(edges)
    rng.shuffle(ordered)
    srcs = " ".join(str(u) for u, _ in ordered)
    dsts = " ".join(str(v) for _, v in ordered)
    return f"{n} {len(ordered)}\n{srcs}\n{dsts}\n"


def _grid_case(seed: int, rows: int, cols: int, lo: int, hi: int) -> str:
    rng = _rng(seed)
    values = [str(rng.randint(lo, hi)) for _ in range(rows * cols)]
    lines = [
        " ".join(values[r * cols : (r + 1) * cols]) for r in range(rows)
    ]
    return f"{rows} {cols}\n" + "\n".join(lines) + "\n"


def _uniform_grid_case(rows: int, cols: int, value: int) -> str:
    line = " ".join([str(value)] * cols)
    return f"{rows} {cols}\n" + "\n".join([line] * rows) + "\n"


def _path_graph_case(n: int) -> str:
    srcs = " ".join(str(i) for i in range(1, n))
    dsts = " ".join(str(i + 1) for i in range(1, n))
    return f"{n} {n - 1}\n{srcs}\n{dsts}\n"


def _cycle_graph_case(n: int) -> str:
    """Directed chain 1->2->...->n plus the back edge n->1, i.e. one big cycle."""
    srcs = [str(i) for i in range(1, n)] + [str(n)]
    dsts = [str(i + 1) for i in range(1, n)] + ["1"]
    return f"{n} {n}\n{' '.join(srcs)}\n{' '.join(dsts)}\n"


def _alien_case(seed: int, count: int, max_len: int = 8) -> str:
    """Word list that really is sorted under a hidden random letter order."""
    rng = _rng(seed)
    alphabet = list("abcdefghijklmnopqrstuvwxyz")
    rng.shuffle(alphabet)
    rank = {ch: i for i, ch in enumerate(alphabet)}
    words = []
    for _ in range(count):
        length = rng.randint(1, max_len)
        words.append("".join(rng.choice(alphabet) for _ in range(length)))
    words = sorted(set(words), key=lambda w: [rank[ch] for ch in w])
    return " ".join(words) + "\n"


def _matrix_text(rows: list[list[int]]) -> str:
    r = len(rows)
    c = len(rows[0]) if r else 0
    body = "\n".join(" ".join(str(v) for v in row) for row in rows)
    return f"{r} {c} {r * c}\n{body}\n"


# --------------------------------------------------------------------------- #
#  01 · Climbing Stairs                                                       #
# --------------------------------------------------------------------------- #

CLIMBING_STAIRS = {
    "slug": "b75-climbing-stairs",
    "skill_id": "dsa_arrays",
    "difficulty": 2,
    "estimated_minutes": 15,
    "title": "Climbing Stairs",
    "statement": (
        "You are climbing a staircase of n steps. Each move takes you up "
        "either one step or two steps.\n\n"
        "Count the number of distinct ordered sequences of moves that land "
        "exactly on step n."
    ),
    "constraints": [
        "1 <= n <= 80",
        "The largest answer exceeds 3 * 10^16, so it does not fit in a 32-bit "
        "int: use long long in C/C++ and long in Java",
        "An O(n) bottom-up recurrence is expected; naive recursion without "
        "memoisation times out on the hidden cases",
    ],
    "input_format": "A single integer n.",
    "output_format": "A single integer: the number of distinct climbing sequences.",
    "examples": [
        {
            "stdin": "2\n",
            "stdout": "2",
            "explanation": "Either 1+1 or a single 2-step move.",
        },
        {
            "stdin": "3\n",
            "stdout": "3",
            "explanation": "1+1+1, 1+2 and 2+1.",
        },
    ],
    "criteria": [
        "Return 1 for n = 1",
        "Produce an exact 64-bit answer for n = 80 without overflow",
        "Run in O(n) time using O(1) extra space",
    ],
    "io": {
        "mode": "tokens",
        "function": "climbing_stairs",
        "todo": "return the number of distinct ways to climb n steps using 1- or 2-step moves",
        "reads": [{"name": "n", "type": "int"}],
        "args": ["n"],
        "returns": "long",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    n = int(sys.stdin.read().split()[0])\n"
        "    a, b = 1, 1\n"
        "    for _ in range(n):\n"
        "        a, b = b, a + b\n"
        "    print(a)\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: n = 2", "stdin": "2\n", "hidden": False},
        {"name": "sample: n = 3", "stdin": "3\n", "hidden": False},
        {"name": "hidden: n = 1", "stdin": "1\n", "hidden": True},
        {"name": "hidden: n = 10", "stdin": "10\n", "hidden": True},
        {"name": "hidden: n = 45 (overflows 32-bit later)", "stdin": "45\n", "hidden": True},
        {"name": "hidden: n = 64", "stdin": "64\n", "hidden": True},
        # Scale case: exponential recursion cannot finish 80 steps.
        {"name": "hidden: scale n = 80", "stdin": "80\n", "hidden": True},
    ],
    "wrong": [
        # Off-by-one: computes ways(n - 1).
        (
            "import sys\n"
            "n = int(sys.stdin.read().split()[0])\n"
            "a, b = 1, 1\n"
            "for _ in range(n - 1):\n"
            "    a, b = b, a + b\n"
            "print(a)\n"
        ),
        # Confuses 'ways' with 'steps'.
        ("import sys\nprint(int(sys.stdin.read().split()[0]))\n"),
        # Correct but exponential: dies on n = 80.
        (
            "import sys\n"
            "sys.setrecursionlimit(10000)\n"
            "def f(k):\n"
            "    if k <= 2:\n"
            "        return max(k, 1)\n"
            "    return f(k - 1) + f(k - 2)\n"
            "print(f(int(sys.stdin.read().split()[0])))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  02 · Coin Change                                                           #
# --------------------------------------------------------------------------- #

COIN_CHANGE = {
    "slug": "b75-coin-change",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Coin Change",
    "statement": (
        "You have an unlimited supply of coins of n distinct denominations. "
        "Make up an amount using the fewest coins possible.\n\n"
        "Print the minimum number of coins, or -1 if the amount cannot be "
        "made at all. The coin system is arbitrary: greedily taking the "
        "largest coin that fits is not correct here."
    ),
    "constraints": [
        "1 <= n <= 12",
        "0 <= amount <= 100000",
        "1 <= coin value <= 10000, all values distinct",
        "An O(n * amount) dynamic program is expected; a memoisation-free "
        "search times out",
    ],
    "input_format": (
        "Line 1: n and amount separated by a space.\n"
        "Line 2: n space-separated coin denominations."
    ),
    "output_format": "A single integer: the minimum number of coins, or -1 if impossible.",
    "examples": [
        {
            "stdin": "3 11\n1 2 5\n",
            "stdout": "3",
            "explanation": "11 = 5 + 5 + 1 uses three coins, and nothing does it in two.",
        },
        {
            "stdin": "3 6\n1 3 4\n",
            "stdout": "2",
            "explanation": (
                "6 = 3 + 3. Greedily taking 4 first forces 4 + 1 + 1, which is three coins, "
                "so this coin system defeats the greedy method."
            ),
        },
    ],
    "criteria": [
        "Print -1 when the amount cannot be formed",
        "Print 0 when the amount is 0",
        "Do not use a greedy largest-coin-first strategy",
        "Handle amount = 100000 inside the time limit",
    ],
    "io": {
        "mode": "tokens",
        "function": "coin_change",
        "todo": "return the fewest coins summing to amount, or -1 if impossible",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "amount", "type": "int"},
            {"name": "coins", "type": "long", "count": "n"},
        ],
        "args": ["coins", "amount"],
        "returns": "long",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.read().split()\n"
        "    n = int(data[0]); amount = int(data[1])\n"
        "    coins = [int(x) for x in data[2:2 + n]]\n"
        "    inf = amount + 1\n"
        "    dp = [0] + [inf] * amount\n"
        "    for value in range(1, amount + 1):\n"
        "        best = inf\n"
        "        for coin in coins:\n"
        "            if coin <= value and dp[value - coin] + 1 < best:\n"
        "                best = dp[value - coin] + 1\n"
        "        dp[value] = best\n"
        "    print(-1 if dp[amount] >= inf else dp[amount])\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: canonical coins", "stdin": "3 11\n1 2 5\n", "hidden": False},
        {"name": "sample: non-canonical coins", "stdin": "3 6\n1 3 4\n", "hidden": False},
        {"name": "hidden: amount zero", "stdin": "2 0\n2 5\n", "hidden": True},
        {"name": "hidden: impossible", "stdin": "1 7\n3\n", "hidden": True},
        {"name": "hidden: single coin exact", "stdin": "1 9\n3\n", "hidden": True},
        # Greedy takes 25+1*5 = 6 coins; optimal is 20+20+20+... -> 3 coins.
        {"name": "hidden: greedy trap", "stdin": "3 60\n1 20 25\n", "hidden": True},
        {"name": "hidden: large coins only", "stdin": "2 100000\n9999 10000\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": "12 100000\n7 11 13 23 41 97 151 373 691 1013 4001 9973\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Greedy largest-first: right on canonical systems, wrong on {1,3,4}.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); amount = int(data[1])\n"
            "coins = sorted((int(x) for x in data[2:2+n]), reverse=True)\n"
            "rem = amount; used = 0\n"
            "for c in coins:\n"
            "    used += rem // c\n"
            "    rem %= c\n"
            "print(used if rem == 0 else -1)\n"
        ),
        # Returns 0 instead of -1 for an impossible amount.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); amount = int(data[1])\n"
            "coins = [int(x) for x in data[2:2+n]]\n"
            "inf = amount + 1\n"
            "dp = [0] + [inf] * amount\n"
            "for v in range(1, amount + 1):\n"
            "    for c in coins:\n"
            "        if c <= v and dp[v-c] + 1 < dp[v]:\n"
            "            dp[v] = dp[v-c] + 1\n"
            "print(0 if dp[amount] >= inf else dp[amount])\n"
        ),
        # Exponential search without memoisation.
        (
            "import sys\n"
            "sys.setrecursionlimit(300000)\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); amount = int(data[1])\n"
            "coins = [int(x) for x in data[2:2+n]]\n"
            "def f(rem):\n"
            "    if rem == 0:\n"
            "        return 0\n"
            "    best = 10**9\n"
            "    for c in coins:\n"
            "        if c <= rem:\n"
            "            best = min(best, f(rem - c) + 1)\n"
            "    return best\n"
            "res = f(amount)\n"
            "print(-1 if res >= 10**9 else res)\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  03 · Longest Increasing Subsequence                                        #
# --------------------------------------------------------------------------- #

LIS = {
    "slug": "b75-longest-increasing-subsequence",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 35,
    "title": "Longest Increasing Subsequence",
    "statement": (
        "Given an array of n integers, return the length of the longest "
        "strictly increasing subsequence.\n\n"
        "A subsequence keeps the original order but may skip elements. "
        "Equal values may not both appear in the subsequence, because the "
        "increase must be strict."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= arr[i] <= 1000000000",
        "The O(n^2) dynamic program times out; an O(n log n) patience / "
        "binary-search solution is required",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": "A single integer: the length of the longest strictly increasing subsequence.",
    "examples": [
        {
            "stdin": "8\n10 9 2 5 3 7 101 18\n",
            "stdout": "4",
            "explanation": "2, 3, 7, 18 (or 2, 3, 7, 101) has length 4.",
        },
        {
            "stdin": "5\n7 7 7 7 7\n",
            "stdout": "1",
            "explanation": "All values are equal, and equal values cannot both be used.",
        },
    ],
    "criteria": [
        "Require a strict increase, so repeated values count once",
        "Handle n = 1",
        "Run in O(n log n) so that n = 200000 finishes inside the limit",
    ],
    "io": {
        "mode": "tokens",
        "function": "longest_increasing_subsequence",
        "todo": "return the length of the longest strictly increasing subsequence",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "from bisect import bisect_left\n"
        "def main():\n"
        "    data = sys.stdin.read().split()\n"
        "    n = int(data[0])\n"
        "    arr = [int(x) for x in data[1:1 + n]]\n"
        "    tails = []\n"
        "    for value in arr:\n"
        "        pos = bisect_left(tails, value)\n"
        "        if pos == len(tails):\n"
        "            tails.append(value)\n"
        "        else:\n"
        "            tails[pos] = value\n"
        "    print(len(tails))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: mixed", "stdin": "8\n10 9 2 5 3 7 101 18\n", "hidden": False},
        {"name": "sample: all equal", "stdin": "5\n7 7 7 7 7\n", "hidden": False},
        {"name": "hidden: single element", "stdin": "1\n-5\n", "hidden": True},
        {"name": "hidden: strictly decreasing", "stdin": "5\n9 7 5 3 1\n", "hidden": True},
        {"name": "hidden: already increasing", "stdin": "6\n1 2 3 4 5 6\n", "hidden": True},
        # Non-contiguous answer: a longest-run solution reports 2 instead of 4.
        {"name": "hidden: non-contiguous", "stdin": "7\n1 9 2 9 3 9 4\n", "hidden": True},
        {"name": "hidden: plateaus", "stdin": "8\n1 1 2 2 3 3 4 4\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _array_case(101, 200000, -10**9, 10**9), "hidden": True},
    ],
    "wrong": [
        # Longest contiguous increasing run.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); arr = [int(x) for x in data[1:1+n]]\n"
            "best = cur = 1\n"
            "for i in range(1, n):\n"
            "    cur = cur + 1 if arr[i] > arr[i-1] else 1\n"
            "    best = max(best, cur)\n"
            "print(best)\n"
        ),
        # Non-decreasing instead of strictly increasing.
        (
            "import sys\n"
            "from bisect import bisect_right\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); arr = [int(x) for x in data[1:1+n]]\n"
            "tails = []\n"
            "for v in arr:\n"
            "    p = bisect_right(tails, v)\n"
            "    if p == len(tails):\n"
            "        tails.append(v)\n"
            "    else:\n"
            "        tails[p] = v\n"
            "print(len(tails))\n"
        ),
        # Correct but quadratic: cannot finish n = 200000.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); arr = [int(x) for x in data[1:1+n]]\n"
            "dp = [1] * n\n"
            "for i in range(n):\n"
            "    for j in range(i):\n"
            "        if arr[j] < arr[i] and dp[j] + 1 > dp[i]:\n"
            "            dp[i] = dp[j] + 1\n"
            "print(max(dp))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  04 · Longest Common Subsequence                                            #
# --------------------------------------------------------------------------- #

LCS = {
    "slug": "b75-longest-common-subsequence",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 35,
    "title": "Longest Common Subsequence",
    "statement": (
        "Given two strings, return the length of their longest common "
        "subsequence.\n\n"
        "A subsequence keeps relative order but need not be contiguous, so "
        "the answer is at least as large as the longest common substring and "
        "usually larger."
    ),
    "constraints": [
        "1 <= |s|, |t| <= 1000",
        "Both strings contain lowercase English letters only and no spaces",
        "An O(|s| * |t|) dynamic program is expected; exponential recursion "
        "times out",
    ],
    "input_format": "A single line containing s and t separated by one space.",
    "output_format": "A single integer: the length of the longest common subsequence.",
    "examples": [
        {
            "stdin": "abcde ace\n",
            "stdout": "3",
            "explanation": '"ace" appears in order inside "abcde", so the answer is 3.',
        },
        {
            "stdin": "abc abc\n",
            "stdout": "3",
            "explanation": "Identical strings share their whole length.",
        },
    ],
    "criteria": [
        "Return 0 when the strings share no character",
        "Allow gaps: the subsequence need not be contiguous",
        "Finish 1000 x 1000 inside the time limit",
    ],
    "io": {
        "mode": "line",
        "function": "longest_common_subsequence",
        "todo": "split the line into two strings and return the length of their longest common subsequence",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    parts = sys.stdin.readline().split()\n"
        "    s = parts[0] if len(parts) > 0 else ''\n"
        "    t = parts[1] if len(parts) > 1 else ''\n"
        "    prev = [0] * (len(t) + 1)\n"
        "    for a in s:\n"
        "        cur = [0] * (len(t) + 1)\n"
        "        for j, b in enumerate(t, start=1):\n"
        "            cur[j] = prev[j - 1] + 1 if a == b else max(prev[j], cur[j - 1])\n"
        "        prev = cur\n"
        "    print(prev[len(t)])\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: abcde ace", "stdin": "abcde ace\n", "hidden": False},
        {"name": "sample: identical", "stdin": "abc abc\n", "hidden": False},
        {"name": "hidden: disjoint alphabets", "stdin": "abc def\n", "hidden": True},
        {"name": "hidden: single characters", "stdin": "a a\n", "hidden": True},
        # Substring solutions answer 1 here; the subsequence answer is 3.
        {"name": "hidden: gaps required", "stdin": "axbycz abc\n", "hidden": True},
        # Multiset intersection answers 3; order forbids it.
        {"name": "hidden: reversed", "stdin": "abc cba\n", "hidden": True},
        {"name": "hidden: repeated letters", "stdin": "aaaa aa\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": _string_case(211, 1000, "abcd") + " " + _string_case(212, 1000, "abcd") + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Longest common *substring*.
        (
            "import sys\n"
            "parts = sys.stdin.readline().split()\n"
            "s = parts[0] if parts else ''\n"
            "t = parts[1] if len(parts) > 1 else ''\n"
            "best = 0\n"
            "prev = [0] * (len(t) + 1)\n"
            "for a in s:\n"
            "    cur = [0] * (len(t) + 1)\n"
            "    for j, b in enumerate(t, start=1):\n"
            "        if a == b:\n"
            "            cur[j] = prev[j-1] + 1\n"
            "            best = max(best, cur[j])\n"
            "    prev = cur\n"
            "print(best)\n"
        ),
        # Multiset intersection: ignores ordering entirely.
        (
            "import sys\n"
            "from collections import Counter\n"
            "parts = sys.stdin.readline().split()\n"
            "s = parts[0] if parts else ''\n"
            "t = parts[1] if len(parts) > 1 else ''\n"
            "cs, ct = Counter(s), Counter(t)\n"
            "print(sum(min(cs[ch], ct[ch]) for ch in cs))\n"
        ),
        # Correct but exponential.
        (
            "import sys\n"
            "sys.setrecursionlimit(100000)\n"
            "parts = sys.stdin.readline().split()\n"
            "s = parts[0] if parts else ''\n"
            "t = parts[1] if len(parts) > 1 else ''\n"
            "def f(i, j):\n"
            "    if i == len(s) or j == len(t):\n"
            "        return 0\n"
            "    if s[i] == t[j]:\n"
            "        return 1 + f(i+1, j+1)\n"
            "    return max(f(i+1, j), f(i, j+1))\n"
            "print(f(0, 0))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  05 · Word Break                                                            #
# --------------------------------------------------------------------------- #

WORD_BREAK = {
    "slug": "b75-word-break",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 35,
    "title": "Word Break",
    "statement": (
        "Given a string s and a dictionary of words, decide whether s can be "
        "cut into a sequence of one or more dictionary words. A word may be "
        "reused any number of times.\n\n"
        "Print 1 if such a segmentation exists and 0 otherwise. The empty "
        "string is segmentable by the empty sequence, so it prints 1."
    ),
    "constraints": [
        "The whole input is one line: the first token is s, every later token "
        "is a dictionary word",
        "0 <= |s| <= 2000, 0 <= number of dictionary words <= 1000",
        "All tokens are lowercase English letters, so whitespace is the only "
        "delimiter and no word can contain a space",
        "An empty line means s is empty and the dictionary is empty; print 1",
        "Backtracking without memoisation is exponential and times out",
    ],
    "input_format": (
        "A single line. Token 1 is s; the remaining tokens (possibly none) "
        "are the dictionary words."
    ),
    "output_format": "A single integer: 1 if s can be segmented, otherwise 0.",
    "examples": [
        {
            "stdin": "leetcode leet code\n",
            "stdout": "1",
            "explanation": '"leetcode" splits as "leet" + "code", both in the dictionary.',
        },
        {
            "stdin": "catsandog cats dog sand and cat\n",
            "stdout": "0",
            "explanation": (
                'Every prefix chain stalls: "cats"+"and" leaves "og", and "cat"+"sand" '
                'leaves "og" as well, so no segmentation exists.'
            ),
        },
    ],
    "criteria": [
        "Print 1 for an empty line",
        "Print 0 when the dictionary is empty and s is not",
        "Allow words to be reused",
        "Use memoisation or a DP table so the exponential case finishes",
    ],
    "io": {
        "mode": "line",
        "function": "word_break",
        "todo": "split the line into s and the dictionary, then return 1 if s can be segmented else 0",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    parts = sys.stdin.readline().split()\n"
        "    if not parts:\n"
        "        print(1)\n"
        "        return\n"
        "    s = parts[0]\n"
        "    words = set(parts[1:])\n"
        "    lengths = sorted({len(w) for w in words})\n"
        "    n = len(s)\n"
        "    dp = [False] * (n + 1)\n"
        "    dp[0] = True\n"
        "    for i in range(1, n + 1):\n"
        "        for length in lengths:\n"
        "            if length > i:\n"
        "                break\n"
        "            if dp[i - length] and s[i - length:i] in words:\n"
        "                dp[i] = True\n"
        "                break\n"
        "    print(1 if dp[n] else 0)\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: leetcode", "stdin": "leetcode leet code\n", "hidden": False},
        {"name": "sample: catsandog", "stdin": "catsandog cats dog sand and cat\n", "hidden": False},
        {"name": "hidden: empty line", "stdin": "\n", "hidden": True},
        {"name": "hidden: empty dictionary", "stdin": "abc\n", "hidden": True},
        {"name": "hidden: word reuse", "stdin": "aaaaaa a aa\n", "hidden": True},
        # A greedy longest-match takes "app" then stalls; "ap"+"pl"+"e" works.
        {"name": "hidden: greedy trap", "stdin": "apple app ap pl e\n", "hidden": True},
        {"name": "hidden: exact match", "stdin": "solo solo\n", "hidden": True},
        {
            "name": "hidden: scale (exponential trap)",
            "stdin": (
                "a" * 1600
                + "b "
                + " ".join("a" * k for k in range(1, 11))
                + "\n"
            ),
            "hidden": True,
        },
    ],
    "wrong": [
        # Greedy longest match from the left.
        (
            "import sys\n"
            "parts = sys.stdin.readline().split()\n"
            "if not parts:\n"
            "    print(1)\n"
            "else:\n"
            "    s = parts[0]; words = set(parts[1:])\n"
            "    i = 0; ok = True\n"
            "    while i < len(s):\n"
            "        hit = 0\n"
            "        for j in range(len(s), i, -1):\n"
            "            if s[i:j] in words:\n"
            "                hit = j - i\n"
            "                break\n"
            "        if hit == 0:\n"
            "            ok = False\n"
            "            break\n"
            "        i += hit\n"
            "    print(1 if ok else 0)\n"
        ),
        # Checks only that every character appears in some word.
        (
            "import sys\n"
            "parts = sys.stdin.readline().split()\n"
            "if not parts:\n"
            "    print(1)\n"
            "else:\n"
            "    s = parts[0]; letters = set(''.join(parts[1:]))\n"
            "    print(1 if all(ch in letters for ch in s) else 0)\n"
        ),
        # Correct but exponential backtracking.
        (
            "import sys\n"
            "sys.setrecursionlimit(100000)\n"
            "parts = sys.stdin.readline().split()\n"
            "if not parts:\n"
            "    print(1)\n"
            "else:\n"
            "    s = parts[0]; words = set(parts[1:])\n"
            "    def f(i):\n"
            "        if i == len(s):\n"
            "            return True\n"
            "        for j in range(i + 1, len(s) + 1):\n"
            "            if s[i:j] in words and f(j):\n"
            "                return True\n"
            "        return False\n"
            "    print(1 if f(0) else 0)\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  06 · Combination Sum IV                                                    #
# --------------------------------------------------------------------------- #

COMBINATION_SUM_IV = {
    "slug": "b75-combination-sum-iv",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 30,
    "title": "Combination Sum IV",
    "statement": (
        "Given n distinct positive integers and a target, count the number of "
        "ordered sequences of those integers that add up to the target. Each "
        "value may be used any number of times.\n\n"
        "Order matters: with values 1 and 2 and target 3, the sequences "
        "(1,1,1), (1,2) and (2,1) are three different answers."
    ),
    "constraints": [
        "1 <= n <= 20",
        "0 <= target <= 60",
        "1 <= value <= 1000, all values distinct",
        "The count can reach 2^59 (about 5.8 * 10^17), which does not fit in "
        "a 32-bit int: use long long in C/C++ and long in Java",
        "The target is capped at 60 precisely so the exact count stays inside "
        "64 bits",
    ],
    "input_format": (
        "Line 1: n and target separated by a space.\n"
        "Line 2: n space-separated distinct positive integers."
    ),
    "output_format": "A single integer: the number of ordered sequences summing to target.",
    "examples": [
        {
            "stdin": "3 4\n1 2 3\n",
            "stdout": "7",
            "explanation": (
                "(1,1,1,1), (1,1,2), (1,2,1), (2,1,1), (2,2), (1,3) and (3,1) — seven "
                "ordered sequences."
            ),
        },
        {
            "stdin": "1 3\n9\n",
            "stdout": "0",
            "explanation": "9 is larger than the target, so nothing sums to 3.",
        },
    ],
    "criteria": [
        "Count ordered sequences, not unordered multisets",
        "Print 1 when target is 0 (the empty sequence)",
        "Use 64-bit arithmetic so the largest case is exact",
    ],
    "io": {
        "mode": "tokens",
        "function": "combination_sum_iv",
        "todo": "return the number of ordered sequences of nums that sum to target",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "target", "type": "int"},
            {"name": "nums", "type": "long", "count": "n"},
        ],
        "args": ["nums", "target"],
        "returns": "long",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.read().split()\n"
        "    n = int(data[0]); target = int(data[1])\n"
        "    nums = [int(x) for x in data[2:2 + n]]\n"
        "    dp = [0] * (target + 1)\n"
        "    dp[0] = 1\n"
        "    for total in range(1, target + 1):\n"
        "        acc = 0\n"
        "        for value in nums:\n"
        "            if value <= total:\n"
        "                acc += dp[total - value]\n"
        "        dp[total] = acc\n"
        "    print(dp[target])\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: 1 2 3 target 4", "stdin": "3 4\n1 2 3\n", "hidden": False},
        {"name": "sample: unreachable", "stdin": "1 3\n9\n", "hidden": False},
        {"name": "hidden: target zero", "stdin": "2 0\n3 5\n", "hidden": True},
        {"name": "hidden: single value divides", "stdin": "1 12\n4\n", "hidden": True},
        # Order-insensitive solutions answer 4 here instead of 13.
        {"name": "hidden: order matters", "stdin": "2 6\n1 2\n", "hidden": True},
        {"name": "hidden: no small value", "stdin": "3 7\n5 6 7\n", "hidden": True},
        {"name": "hidden: 64-bit scale", "stdin": "3 60\n1 2 3\n", "hidden": True},
        {
            "name": "hidden: scale wide alphabet",
            "stdin": "20 60\n" + " ".join(str(v) for v in range(1, 21)) + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Loops in the other order: counts unordered combinations.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); target = int(data[1])\n"
            "nums = [int(x) for x in data[2:2+n]]\n"
            "dp = [0] * (target + 1)\n"
            "dp[0] = 1\n"
            "for v in nums:\n"
            "    for total in range(v, target + 1):\n"
            "        dp[total] += dp[total - v]\n"
            "print(dp[target])\n"
        ),
        # dp[0] left at 0, so every count collapses.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); target = int(data[1])\n"
            "nums = [int(x) for x in data[2:2+n]]\n"
            "dp = [0] * (target + 1)\n"
            "for v in nums:\n"
            "    if v <= target:\n"
            "        dp[v] = 1\n"
            "for total in range(1, target + 1):\n"
            "    for v in nums:\n"
            "        if v < total:\n"
            "            dp[total] += dp[total - v]\n"
            "print(dp[target])\n"
        ),
        # Correct but memoisation-free: the 64-bit scale case never finishes.
        (
            "import sys\n"
            "sys.setrecursionlimit(100000)\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); target = int(data[1])\n"
            "nums = [int(x) for x in data[2:2+n]]\n"
            "def f(rem):\n"
            "    if rem == 0:\n"
            "        return 1\n"
            "    return sum(f(rem - v) for v in nums if v <= rem)\n"
            "print(f(target))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  07 · House Robber                                                          #
# --------------------------------------------------------------------------- #

HOUSE_ROBBER = {
    "slug": "b75-house-robber",
    "skill_id": "dsa_arrays",
    "difficulty": 4,
    "estimated_minutes": 25,
    "title": "House Robber",
    "statement": (
        "n houses stand in a row, the i-th holding nums[i] pounds. You may "
        "not rob two adjacent houses.\n\n"
        "Return the largest total you can take."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "0 <= nums[i] <= 1000000000",
        "The total can reach 10^14, so it does not fit in a 32-bit int: use "
        "long long in C/C++ and long in Java",
        "An O(n) pass is expected",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated non-negative integers.",
    "output_format": "A single integer: the maximum total that can be robbed.",
    "examples": [
        {
            "stdin": "4\n1 2 3 1\n",
            "stdout": "4",
            "explanation": "Rob houses 1 and 3 for 1 + 3 = 4.",
        },
        {
            "stdin": "5\n2 7 9 3 1\n",
            "stdout": "12",
            "explanation": "Rob 2 + 9 + 1 = 12; taking 7 and 3 only yields 10.",
        },
    ],
    "criteria": [
        "Handle n = 1 and n = 2",
        "Never take two adjacent houses",
        "Use 64-bit accumulation at the maximum scale",
    ],
    "io": {
        "mode": "tokens",
        "function": "house_robber",
        "todo": "return the maximum total from non-adjacent houses",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "nums", "type": "long", "count": "n"},
        ],
        "args": ["nums"],
        "returns": "long",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.read().split()\n"
        "    n = int(data[0])\n"
        "    nums = [int(x) for x in data[1:1 + n]]\n"
        "    take = 0\n"
        "    skip = 0\n"
        "    for value in nums:\n"
        "        take, skip = skip + value, max(skip, take)\n"
        "    print(max(take, skip))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: 1 2 3 1", "stdin": "4\n1 2 3 1\n", "hidden": False},
        {"name": "sample: 2 7 9 3 1", "stdin": "5\n2 7 9 3 1\n", "hidden": False},
        {"name": "hidden: single house", "stdin": "1\n17\n", "hidden": True},
        {"name": "hidden: two houses", "stdin": "2\n5 4\n", "hidden": True},
        {"name": "hidden: all zeros", "stdin": "4\n0 0 0 0\n", "hidden": True},
        # Alternating-parity solutions answer 8 here; the optimum is 10.
        {"name": "hidden: skip two", "stdin": "5\n5 1 1 1 5\n", "hidden": True},
        {"name": "hidden: large values", "stdin": "3\n1000000000 1 1000000000\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _array_case(303, 200000, 0, 10**9), "hidden": True},
    ],
    "wrong": [
        # Best of the even-indexed and odd-indexed totals.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); nums = [int(x) for x in data[1:1+n]]\n"
            "print(max(sum(nums[0::2]), sum(nums[1::2])))\n"
        ),
        # Greedy: take a house whenever the previous one was skipped.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); nums = [int(x) for x in data[1:1+n]]\n"
            "total = 0; prev = False\n"
            "for v in nums:\n"
            "    if not prev and v > 0:\n"
            "        total += v; prev = True\n"
            "    else:\n"
            "        prev = False\n"
            "print(total)\n"
        ),
        # Exponential recursion.
        (
            "import sys\n"
            "sys.setrecursionlimit(300000)\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); nums = [int(x) for x in data[1:1+n]]\n"
            "def f(i):\n"
            "    if i >= n:\n"
            "        return 0\n"
            "    return max(nums[i] + f(i + 2), f(i + 1))\n"
            "print(f(0))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  08 · House Robber II                                                       #
# --------------------------------------------------------------------------- #

HOUSE_ROBBER_II = {
    "slug": "b75-house-robber-circular",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "House Robber II",
    "statement": (
        "The same n houses are now arranged in a circle, so house n is "
        "adjacent to house 1 as well as to house n-1.\n\n"
        "You still may not rob two adjacent houses. Return the largest total. "
        "The wrap-around is the whole difficulty: the first and last houses "
        "can never both be robbed."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "0 <= nums[i] <= 1000000000",
        "The total can reach 10^14, so use long long in C/C++ and long in Java",
        "n = 1 is a single house adjacent only to itself; the answer is nums[0]",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated non-negative integers.",
    "output_format": "A single integer: the maximum total that can be robbed on the circle.",
    "examples": [
        {
            "stdin": "3\n2 3 2\n",
            "stdout": "3",
            "explanation": "Houses 1 and 3 are adjacent on the circle, so 2 + 2 is illegal; take 3.",
        },
        {
            "stdin": "4\n1 2 3 1\n",
            "stdout": "4",
            "explanation": "Rob houses 1 and 3 for 4; the circle does not bite here.",
        },
    ],
    "criteria": [
        "Never rob both the first and the last house",
        "Handle n = 1 and n = 2 correctly",
        "Run in O(n) with 64-bit accumulation",
    ],
    "io": {
        "mode": "tokens",
        "function": "house_robber_circular",
        "todo": "return the maximum total from non-adjacent houses arranged in a circle",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "nums", "type": "long", "count": "n"},
        ],
        "args": ["nums"],
        "returns": "long",
    },
    "reference": (
        "import sys\n"
        "def line(values):\n"
        "    take = 0\n"
        "    skip = 0\n"
        "    for value in values:\n"
        "        take, skip = skip + value, max(skip, take)\n"
        "    return max(take, skip)\n"
        "def main():\n"
        "    data = sys.stdin.read().split()\n"
        "    n = int(data[0])\n"
        "    nums = [int(x) for x in data[1:1 + n]]\n"
        "    if n == 1:\n"
        "        print(nums[0])\n"
        "        return\n"
        "    print(max(line(nums[:-1]), line(nums[1:])))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: 2 3 2", "stdin": "3\n2 3 2\n", "hidden": False},
        {"name": "sample: 1 2 3 1", "stdin": "4\n1 2 3 1\n", "hidden": False},
        {"name": "hidden: single house", "stdin": "1\n42\n", "hidden": True},
        {"name": "hidden: two houses", "stdin": "2\n9 3\n", "hidden": True},
        # The linear answer 10 is illegal on a circle; the correct answer is 6.
        {"name": "hidden: wrap-around trap", "stdin": "5\n5 1 6 1 5\n", "hidden": True},
        {"name": "hidden: all equal", "stdin": "6\n4 4 4 4 4 4\n", "hidden": True},
        {"name": "hidden: last is largest", "stdin": "4\n2 1 1 9\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _array_case(404, 200000, 0, 10**9), "hidden": True},
    ],
    "wrong": [
        # Forgets the circle entirely.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); nums = [int(x) for x in data[1:1+n]]\n"
            "take = skip = 0\n"
            "for v in nums:\n"
            "    take, skip = skip + v, max(skip, take)\n"
            "print(max(take, skip))\n"
        ),
        # Always drops the last house instead of trying both windows.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); nums = [int(x) for x in data[1:1+n]]\n"
            "def line(vals):\n"
            "    take = skip = 0\n"
            "    for v in vals:\n"
            "        take, skip = skip + v, max(skip, take)\n"
            "    return max(take, skip)\n"
            "print(nums[0] if n == 1 else line(nums[:-1]))\n"
        ),
        # Crashes / misreports on n = 1 because it slices an empty list.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); nums = [int(x) for x in data[1:1+n]]\n"
            "def line(vals):\n"
            "    take = skip = 0\n"
            "    for v in vals:\n"
            "        take, skip = skip + v, max(skip, take)\n"
            "    return max(take, skip)\n"
            "print(max(line(nums[:-1]), line(nums[1:])))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  09 · Decode Ways                                                           #
# --------------------------------------------------------------------------- #

DECODE_WAYS = {
    "slug": "b75-decode-ways",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Decode Ways",
    "statement": (
        "Letters were encoded as numbers with A = 1 through Z = 26 and then "
        "concatenated without separators. Given the digit string, count the "
        "decodings back into letters.\n\n"
        "A group of one digit must be 1..9 and a group of two digits must be "
        "10..26, so a leading zero never starts a group. If no decoding "
        "exists the answer is 0, and an empty line also prints 0."
    ),
    "constraints": [
        "0 <= |s| <= 80, and s contains digits only",
        "The largest answer exceeds 3 * 10^16, so it does not fit in a 32-bit "
        "int: use long long in C/C++ and long in Java",
        "|s| is capped at 80 so the exact count always fits in 64 bits",
        "An empty line prints 0",
    ],
    "input_format": "A single line containing the digit string s. The line may be empty.",
    "output_format": "A single integer: the number of valid decodings.",
    "examples": [
        {
            "stdin": "226\n",
            "stdout": "3",
            "explanation": '"2 2 6" (BBF), "22 6" (VF) and "2 26" (BZ).',
        },
        {
            "stdin": "06\n",
            "stdout": "0",
            "explanation": "No group may start with 0, and 06 is not a valid two-digit group.",
        },
    ],
    "criteria": [
        "Print 0 for an empty line and for any string that cannot be decoded",
        "Treat a leading zero in a group as invalid, including inside the string",
        "Accept two-digit groups only in the range 10..26",
        "Use 64-bit arithmetic for the longest inputs",
    ],
    "io": {
        "mode": "line",
        "function": "decode_ways",
        "todo": "return the number of ways to decode the digit string using A=1..Z=26",
        "reads": [{"name": "s", "type": "string"}],
        "args": ["s"],
        "returns": "long",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    s = sys.stdin.readline().strip()\n"
        "    if not s:\n"
        "        print(0)\n"
        "        return\n"
        "    n = len(s)\n"
        "    prev2 = 1\n"
        "    prev1 = 1 if s[0] != '0' else 0\n"
        "    for i in range(1, n):\n"
        "        cur = 0\n"
        "        if s[i] != '0':\n"
        "            cur += prev1\n"
        "        two = int(s[i - 1:i + 1])\n"
        "        if 10 <= two <= 26:\n"
        "            cur += prev2\n"
        "        prev2, prev1 = prev1, cur\n"
        "    print(prev1)\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: 226", "stdin": "226\n", "hidden": False},
        {"name": "sample: 06", "stdin": "06\n", "hidden": False},
        {"name": "hidden: empty line", "stdin": "\n", "hidden": True},
        {"name": "hidden: single zero", "stdin": "0\n", "hidden": True},
        {"name": "hidden: trailing zero pair", "stdin": "10\n", "hidden": True},
        # 100 is undecodable: the middle 0 cannot join either neighbour legally.
        {"name": "hidden: interior zero", "stdin": "100\n", "hidden": True},
        {"name": "hidden: 27 is not a letter", "stdin": "27\n", "hidden": True},
        {"name": "hidden: zeros absorbed", "stdin": "2101\n", "hidden": True},
        {"name": "hidden: ten ones", "stdin": "1111111111\n", "hidden": True},
        {"name": "hidden: maximal 64-bit", "stdin": "1" * 80 + "\n", "hidden": True},
        {
            "name": "hidden: scale mixed digits",
            "stdin": _string_case(505, 80, "1212121226") + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Plain Fibonacci: ignores zeros and the 26 ceiling.
        (
            "import sys\n"
            "s = sys.stdin.readline().strip()\n"
            "if not s:\n"
            "    print(0)\n"
            "else:\n"
            "    a, b = 1, 1\n"
            "    for _ in range(len(s) - 1):\n"
            "        a, b = b, a + b\n"
            "    print(b)\n"
        ),
        # Accepts any two-digit group, so 27..99 are wrongly counted.
        (
            "import sys\n"
            "s = sys.stdin.readline().strip()\n"
            "if not s:\n"
            "    print(0)\n"
            "else:\n"
            "    n = len(s); prev2, prev1 = 1, (1 if s[0] != '0' else 0)\n"
            "    for i in range(1, n):\n"
            "        cur = prev1 if s[i] != '0' else 0\n"
            "        cur += prev2\n"
            "        prev2, prev1 = prev1, cur\n"
            "    print(prev1)\n"
        ),
        # Forgets that a group may not start with 0 in the middle of the string.
        (
            "import sys\n"
            "s = sys.stdin.readline().strip()\n"
            "if not s:\n"
            "    print(0)\n"
            "else:\n"
            "    n = len(s); prev2, prev1 = 1, 1\n"
            "    for i in range(1, n):\n"
            "        cur = prev1\n"
            "        two = int(s[i-1:i+1])\n"
            "        if 10 <= two <= 26:\n"
            "            cur += prev2\n"
            "        prev2, prev1 = prev1, cur\n"
            "    print(prev1)\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  10 · Unique Paths                                                          #
# --------------------------------------------------------------------------- #

UNIQUE_PATHS = {
    "slug": "b75-unique-paths",
    "skill_id": "dsa_arrays",
    "difficulty": 4,
    "estimated_minutes": 25,
    "title": "Unique Paths",
    "statement": (
        "A robot starts in the top-left cell of an m by n grid and must reach "
        "the bottom-right cell, moving only right or down.\n\n"
        "Count the distinct paths."
    ),
    "constraints": [
        "1 <= m, n <= 25",
        "The answer for m = n = 25 is 1052049481860, which does not fit in a "
        "32-bit int: use long long in C/C++ and long in Java",
        "m and n are capped at 25 so the exact count stays inside 64 bits",
        "Enumerating paths one by one is exponential and times out",
    ],
    "input_format": "A single line: m and n separated by a space.",
    "output_format": "A single integer: the number of distinct paths.",
    "examples": [
        {
            "stdin": "3 7\n",
            "stdout": "28",
            "explanation": "Choose which 2 of the 8 moves go down: C(8,2) = 28.",
        },
        {
            "stdin": "3 2\n",
            "stdout": "3",
            "explanation": "Right-Down-Down, Down-Right-Down and Down-Down-Right.",
        },
    ],
    "criteria": [
        "Return 1 when either dimension is 1",
        "Produce an exact 64-bit answer for 25 by 25",
        "Use dynamic programming or a binomial coefficient, not path enumeration",
    ],
    "io": {
        "mode": "tokens",
        "function": "unique_paths",
        "todo": "return the number of right/down paths across an m by n grid",
        "reads": [
            {"name": "m", "type": "int"},
            {"name": "n", "type": "int"},
        ],
        "args": ["m", "n"],
        "returns": "long",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.read().split()\n"
        "    m, n = int(data[0]), int(data[1])\n"
        "    row = [1] * n\n"
        "    for _ in range(1, m):\n"
        "        for j in range(1, n):\n"
        "            row[j] += row[j - 1]\n"
        "    print(row[n - 1])\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: 3 x 7", "stdin": "3 7\n", "hidden": False},
        {"name": "sample: 3 x 2", "stdin": "3 2\n", "hidden": False},
        {"name": "hidden: 1 x 1", "stdin": "1 1\n", "hidden": True},
        {"name": "hidden: single row", "stdin": "1 25\n", "hidden": True},
        {"name": "hidden: single column", "stdin": "25 1\n", "hidden": True},
        {"name": "hidden: square 10", "stdin": "10 10\n", "hidden": True},
        {"name": "hidden: asymmetric", "stdin": "23 7\n", "hidden": True},
        # Scale: 1052049481860 paths, so enumeration cannot finish.
        {"name": "hidden: scale 25 x 25", "stdin": "25 25\n", "hidden": True},
    ],
    "wrong": [
        # Multiplies the dimensions.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "print(int(data[0]) * int(data[1]))\n"
        ),
        # Off-by-one in the binomial coefficient.
        (
            "import sys\n"
            "from math import comb\n"
            "data = sys.stdin.read().split()\n"
            "m, n = int(data[0]), int(data[1])\n"
            "print(comb(m + n, m))\n"
        ),
        # Enumerates every path.
        (
            "import sys\n"
            "sys.setrecursionlimit(100000)\n"
            "data = sys.stdin.read().split()\n"
            "m, n = int(data[0]), int(data[1])\n"
            "def f(i, j):\n"
            "    if i == m - 1 or j == n - 1:\n"
            "        return 1\n"
            "    return f(i + 1, j) + f(i, j + 1)\n"
            "print(f(0, 0))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  11 · Jump Game                                                             #
# --------------------------------------------------------------------------- #

JUMP_GAME = {
    "slug": "b75-jump-game",
    "skill_id": "dsa_arrays",
    "difficulty": 4,
    "estimated_minutes": 25,
    "title": "Jump Game",
    "statement": (
        "You start at index 0 of an array of n non-negative integers. From "
        "index i you may jump forward to any index in i+1 .. i+nums[i].\n\n"
        "Print 1 if the last index is reachable and 0 otherwise. A 0 in the "
        "array only blocks you if you are forced to stand on it."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "0 <= nums[i] <= 100000",
        "A single O(n) furthest-reach pass is expected; branching over every "
        "possible jump is exponential and times out",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated non-negative integers.",
    "output_format": "A single integer: 1 if the last index is reachable, otherwise 0.",
    "examples": [
        {
            "stdin": "5\n2 3 1 1 4\n",
            "stdout": "1",
            "explanation": "Jump 0 -> 1 (step 1), then 1 -> 4 (step 3).",
        },
        {
            "stdin": "5\n3 2 1 0 4\n",
            "stdout": "0",
            "explanation": "Every route lands on index 3, which holds 0, so index 4 is unreachable.",
        },
    ],
    "criteria": [
        "Print 1 for n = 1, where you already stand on the last index",
        "A zero at the last index does not block anything",
        "Do not assume a single step is always enough",
        "Run in O(n)",
    ],
    "io": {
        "mode": "tokens",
        "function": "jump_game",
        "todo": "return 1 if the last index is reachable from index 0, otherwise 0",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "nums", "type": "long", "count": "n"},
        ],
        "args": ["nums"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.read().split()\n"
        "    n = int(data[0])\n"
        "    nums = [int(x) for x in data[1:1 + n]]\n"
        "    reach = 0\n"
        "    for i in range(n):\n"
        "        if i > reach:\n"
        "            print(0)\n"
        "            return\n"
        "        if i + nums[i] > reach:\n"
        "            reach = i + nums[i]\n"
        "    print(1)\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: reachable", "stdin": "5\n2 3 1 1 4\n", "hidden": False},
        {"name": "sample: blocked", "stdin": "5\n3 2 1 0 4\n", "hidden": False},
        {"name": "hidden: single index", "stdin": "1\n0\n", "hidden": True},
        {"name": "hidden: zero at the end", "stdin": "3\n2 1 0\n", "hidden": True},
        # A one-step-lookahead solution says 0 here; a long first jump wins.
        {"name": "hidden: jump over a zero", "stdin": "4\n3 0 0 1\n", "hidden": True},
        {"name": "hidden: immediate stop", "stdin": "2\n0 1\n", "hidden": True},
        {"name": "hidden: all ones", "stdin": "6\n1 1 1 1 1 1\n", "hidden": True},
        {
            "name": "hidden: scale reachable",
            "stdin": "200000\n" + " ".join(["2"] * 199999 + ["0"]) + "\n",
            "hidden": True,
        },
        {
            "name": "hidden: scale blocked",
            "stdin": "200000\n"
            + " ".join(["1"] * 100000 + ["0"] + ["1"] * 99999)
            + "\n",
            "hidden": True,
        },
        # Every index offers two jumps, and all of them dead-end against the
        # wall of zeros. A branching search explores ~Fibonacci(59) routes here
        # while the furthest-reach scan answers in 62 steps.
        {
            "name": "hidden: branching dead end",
            "stdin": "62\n" + " ".join(["2"] * 59 + ["0", "0", "0"]) + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Declares failure as soon as any zero appears before the end.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); nums = [int(x) for x in data[1:1+n]]\n"
            "print(0 if any(v == 0 for v in nums[:-1]) else 1)\n"
        ),
        # Only ever steps one index forward.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); nums = [int(x) for x in data[1:1+n]]\n"
            "i = 0\n"
            "while i < n - 1 and nums[i] > 0:\n"
            "    i += 1\n"
            "print(1 if i == n - 1 else 0)\n"
        ),
        # Correct but branches over every jump length.
        (
            "import sys\n"
            "sys.setrecursionlimit(300000)\n"
            "data = sys.stdin.read().split()\n"
            "n = int(data[0]); nums = [int(x) for x in data[1:1+n]]\n"
            "def f(i):\n"
            "    if i >= n - 1:\n"
            "        return True\n"
            "    for step in range(1, nums[i] + 1):\n"
            "        if f(i + step):\n"
            "            return True\n"
            "    return False\n"
            "print(1 if f(0) else 0)\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  12 · Course Schedule                                                       #
# --------------------------------------------------------------------------- #

COURSE_SCHEDULE = {
    "slug": "b75-course-schedule",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 35,
    "title": "Course Schedule",
    "statement": (
        "There are n courses labelled 1..n. A prerequisite pair (u, v) means "
        "course u must be taken before course v, i.e. a directed edge u -> v.\n\n"
        "Print 1 if some order lets you finish every course, and 0 if the "
        "prerequisites contain a cycle.\n\n"
        "The graph is DIRECTED, may be disconnected, may contain duplicate "
        "edges and may contain a self-loop (which is immediately impossible). "
        "The prerequisite chain can be 100000 courses long, so a recursive "
        "depth-first search will overflow the stack: use an iterative "
        "algorithm such as Kahn's."
    ),
    "constraints": [
        "1 <= n <= 100000",
        "0 <= m <= 200000",
        "1 <= u, v <= n; self-loops and duplicate edges are possible",
        "The graph may be disconnected, so every vertex must be accounted for",
        "Solve iteratively: a hidden case is a single chain of 100000 courses",
    ],
    "input_format": (
        "Line 1: n and m separated by a space.\n"
        "Line 2: m integers, the source (prerequisite) of each edge.\n"
        "Line 3: m integers, the target of each edge.\n"
        "Edge i runs from the i-th value on line 2 to the i-th value on line 3. "
        "When m is 0 lines 2 and 3 are empty or absent."
    ),
    "output_format": "A single integer: 1 if every course can be finished, otherwise 0.",
    "examples": [
        {
            "stdin": "4 4\n1 1 2 3\n2 3 4 4\n",
            "stdout": "1",
            "explanation": (
                "Edges 1->2, 1->3, 2->4, 3->4 form a diamond. It is acyclic even though "
                "course 4 is reached twice, so the answer is 1."
            ),
        },
        {
            "stdin": "2 2\n1 2\n2 1\n",
            "stdout": "0",
            "explanation": "1->2 and 2->1 form a cycle, so neither course can be started.",
        },
    ],
    "criteria": [
        "Treat a node reached twice along different paths as fine, not as a cycle",
        "Detect a cycle that lies in a component unreachable from vertex 1",
        "Reject a self-loop",
        "Work iteratively so a 100000-long chain does not overflow the stack",
    ],
    "io": {
        "mode": "tokens",
        "function": "course_schedule",
        "todo": "return 1 if the directed prerequisite graph is acyclic, otherwise 0",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "m", "type": "int"},
            {"name": "src", "type": "int", "count": "m"},
            {"name": "dst", "type": "int", "count": "m"},
        ],
        "args": ["n", "src", "dst"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.buffer.read().split()\n"
        "    n = int(data[0]); m = int(data[1])\n"
        "    head = [-1] * (n + 1)\n"
        "    nxt = [-1] * m\n"
        "    to = [0] * m\n"
        "    indeg = [0] * (n + 1)\n"
        "    for i in range(m):\n"
        "        u = int(data[2 + i]); v = int(data[2 + m + i])\n"
        "        to[i] = v\n"
        "        nxt[i] = head[u]\n"
        "        head[u] = i\n"
        "        indeg[v] += 1\n"
        "    stack = [v for v in range(1, n + 1) if indeg[v] == 0]\n"
        "    seen = 0\n"
        "    while stack:\n"
        "        u = stack.pop()\n"
        "        seen += 1\n"
        "        edge = head[u]\n"
        "        while edge != -1:\n"
        "            v = to[edge]\n"
        "            indeg[v] -= 1\n"
        "            if indeg[v] == 0:\n"
        "                stack.append(v)\n"
        "            edge = nxt[edge]\n"
        "    print(1 if seen == n else 0)\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: diamond", "stdin": "4 4\n1 1 2 3\n2 3 4 4\n", "hidden": False},
        {"name": "sample: two-cycle", "stdin": "2 2\n1 2\n2 1\n", "hidden": False},
        {"name": "hidden: no edges", "stdin": "3 0\n\n\n", "hidden": True},
        {"name": "hidden: single course", "stdin": "1 0\n\n\n", "hidden": True},
        {"name": "hidden: self-loop", "stdin": "3 1\n2\n2\n", "hidden": True},
        {"name": "hidden: duplicate edges", "stdin": "3 3\n1 1 2\n2 2 3\n", "hidden": True},
        # The cycle sits in a component that vertex 1 cannot reach.
        {
            "name": "hidden: disconnected cycle",
            "stdin": "5 4\n1 2 4 5\n2 3 5 4\n",
            "hidden": True,
        },
        # Two independent sources feeding one sink: not a cycle.
        {"name": "hidden: shared sink", "stdin": "3 2\n1 3\n2 2\n", "hidden": True},
        {"name": "hidden: deep chain (stack trap)", "stdin": _path_graph_case(100000), "hidden": True},
        {"name": "hidden: scale acyclic", "stdin": _dag_case(601, 100000, 200000), "hidden": True},
        {"name": "hidden: scale with a cycle", "stdin": _cycle_graph_case(100000), "hidden": True},
    ],
    "wrong": [
        # Marks any already-visited node as a cycle: fails on the diamond.
        (
            "import sys\n"
            "sys.setrecursionlimit(300000)\n"
            "data = sys.stdin.buffer.read().split()\n"
            "n = int(data[0]); m = int(data[1])\n"
            "adj = [[] for _ in range(n + 1)]\n"
            "for i in range(m):\n"
            "    adj[int(data[2+i])].append(int(data[2+m+i]))\n"
            "visited = [False] * (n + 1)\n"
            "ok = True\n"
            "for start in range(1, n + 1):\n"
            "    if visited[start]:\n"
            "        continue\n"
            "    stack = [start]\n"
            "    while stack:\n"
            "        u = stack.pop()\n"
            "        if visited[u]:\n"
            "            ok = False\n"
            "            break\n"
            "        visited[u] = True\n"
            "        for v in adj[u]:\n"
            "            stack.append(v)\n"
            "    if not ok:\n"
            "        break\n"
            "print(1 if ok else 0)\n"
        ),
        # Treats the edges as undirected and calls any cycle impossible.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "n = int(data[0]); m = int(data[1])\n"
            "parent = list(range(n + 1))\n"
            "def find(x):\n"
            "    while parent[x] != x:\n"
            "        parent[x] = parent[parent[x]]\n"
            "        x = parent[x]\n"
            "    return x\n"
            "ok = True\n"
            "for i in range(m):\n"
            "    a = find(int(data[2+i])); b = find(int(data[2+m+i]))\n"
            "    if a == b:\n"
            "        ok = False\n"
            "        break\n"
            "    parent[a] = b\n"
            "print(1 if ok else 0)\n"
        ),
        # Only checks that *some* course has no prerequisite.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "n = int(data[0]); m = int(data[1])\n"
            "indeg = [0] * (n + 1)\n"
            "for i in range(m):\n"
            "    indeg[int(data[2+m+i])] += 1\n"
            "print(1 if any(indeg[v] == 0 for v in range(1, n + 1)) else 0)\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  13 · Pacific Atlantic Water Flow                                           #
# --------------------------------------------------------------------------- #

PACIFIC_ATLANTIC = {
    "slug": "b75-pacific-atlantic-water-flow",
    "skill_id": "dsa_arrays",
    "difficulty": 7,
    "estimated_minutes": 45,
    "title": "Pacific Atlantic Water Flow",
    "statement": (
        "An r by c grid of heights is bordered by the Pacific along the top "
        "and left edges and by the Atlantic along the bottom and right "
        "edges.\n\n"
        "Rain on a cell flows to a side-adjacent neighbour whose height is "
        "less than or equal to the current height, and off the grid when it "
        "leaves an edge. Count the cells from which water can reach BOTH "
        "oceans.\n\n"
        "Flooding outwards from every cell in turn is too slow; flood inwards "
        "from each ocean instead. The grid can hold 90000 cells, so use an "
        "explicit stack or queue rather than recursion."
    ),
    "constraints": [
        "1 <= r, c <= 300",
        "0 <= height <= 1000000",
        "Plateaus are common: movement onto an equal height is allowed, so "
        "flat regions drain to both oceans",
        "An O(r * c) double flood fill is expected; a per-cell search is "
        "O((r * c)^2) and times out",
    ],
    "input_format": (
        "Line 1: r and c.\n"
        "Then r * c integers in row-major order (r rows of c values)."
    ),
    "output_format": "A single integer: the number of cells that can drain to both oceans.",
    "examples": [
        {
            "stdin": "3 3\n1 2 3\n8 9 4\n7 6 5\n",
            "stdout": "9",
            "explanation": (
                "The spiral of increasing heights lets every cell walk downhill to both the "
                "top-left region and the bottom-right region, so all 9 cells qualify."
            ),
        },
        {
            "stdin": "2 2\n1 2\n3 4\n",
            "stdout": "3",
            "explanation": (
                "Cell (0,0) drains to the Pacific but must climb to reach the Atlantic, so "
                "only the other three cells reach both."
            ),
        },
    ],
    "criteria": [
        "Allow movement between equal heights",
        "Treat top and left as one ocean, bottom and right as the other",
        "Count a 1 by 1 grid as 1, since it touches both oceans",
        "Run in O(r * c) iteratively",
    ],
    "io": {
        "mode": "tokens",
        "function": "pacific_atlantic",
        "todo": "return the number of cells that can drain to both the Pacific and the Atlantic",
        "reads": [
            {"name": "r", "type": "int"},
            {"name": "c", "type": "int"},
            {"name": "k", "type": "int", "value": "r * c"},
            {"name": "grid", "type": "int", "count": "k"},
        ],
        "args": ["grid", "r", "c"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.buffer.read().split()\n"
        "    r = int(data[0]); c = int(data[1]); k = r * c\n"
        "    grid = [int(x) for x in data[2:2 + k]]\n"
        "    def flood(starts):\n"
        "        seen = bytearray(r * c)\n"
        "        stack = []\n"
        "        for cell in starts:\n"
        "            if not seen[cell]:\n"
        "                seen[cell] = 1\n"
        "                stack.append(cell)\n"
        "        while stack:\n"
        "            cell = stack.pop()\n"
        "            i, j = divmod(cell, c)\n"
        "            height = grid[cell]\n"
        "            for ni, nj in ((i-1, j), (i+1, j), (i, j-1), (i, j+1)):\n"
        "                if 0 <= ni < r and 0 <= nj < c:\n"
        "                    nb = ni * c + nj\n"
        "                    if not seen[nb] and grid[nb] >= height:\n"
        "                        seen[nb] = 1\n"
        "                        stack.append(nb)\n"
        "        return seen\n"
        "    pacific = flood(\n"
        "        [j for j in range(c)] + [i * c for i in range(r)]\n"
        "    )\n"
        "    atlantic = flood(\n"
        "        [(r - 1) * c + j for j in range(c)] + [i * c + c - 1 for i in range(r)]\n"
        "    )\n"
        "    print(sum(1 for cell in range(r * c) if pacific[cell] and atlantic[cell]))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: spiral", "stdin": "3 3\n1 2 3\n8 9 4\n7 6 5\n", "hidden": False},
        {"name": "sample: 2 x 2", "stdin": "2 2\n1 2\n3 4\n", "hidden": False},
        {"name": "hidden: single cell", "stdin": "1 1\n5\n", "hidden": True},
        # All heights equal: only a solution that allows flat moves gets 25.
        {"name": "hidden: plateau", "stdin": _uniform_grid_case(5, 5, 7), "hidden": True},
        {"name": "hidden: single row", "stdin": "1 5\n3 1 4 1 5\n", "hidden": True},
        {"name": "hidden: single column", "stdin": "5 1\n3 1 4 1 5\n", "hidden": True},
        # A ridge across the middle: left/right oceans see different halves.
        {
            "name": "hidden: leetcode example",
            "stdin": (
                "5 5\n"
                "1 2 2 3 5\n"
                "3 2 3 4 4\n"
                "2 4 5 3 1\n"
                "6 7 1 4 5\n"
                "5 1 1 2 4\n"
            ),
            "hidden": True,
        },
        {"name": "hidden: descending rows", "stdin": _grid_case(701, 12, 12, 0, 3), "hidden": True},
        {"name": "hidden: scale", "stdin": _grid_case(702, 300, 300, 0, 60), "hidden": True},
        {"name": "hidden: scale plateau", "stdin": _uniform_grid_case(300, 300, 42), "hidden": True},
    ],
    "wrong": [
        # Requires a strict descent, so plateaus never drain.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "r = int(data[0]); c = int(data[1]); k = r * c\n"
            "grid = [int(x) for x in data[2:2+k]]\n"
            "def flood(starts):\n"
            "    seen = bytearray(r*c)\n"
            "    stack = []\n"
            "    for cell in starts:\n"
            "        if not seen[cell]:\n"
            "            seen[cell] = 1; stack.append(cell)\n"
            "    while stack:\n"
            "        cell = stack.pop(); i, j = divmod(cell, c); h = grid[cell]\n"
            "        for ni, nj in ((i-1,j),(i+1,j),(i,j-1),(i,j+1)):\n"
            "            if 0 <= ni < r and 0 <= nj < c:\n"
            "                nb = ni*c+nj\n"
            "                if not seen[nb] and grid[nb] > h:\n"
            "                    seen[nb] = 1; stack.append(nb)\n"
            "    return seen\n"
            "p = flood([j for j in range(c)] + [i*c for i in range(r)])\n"
            "a = flood([(r-1)*c+j for j in range(c)] + [i*c+c-1 for i in range(r)])\n"
            "print(sum(1 for cell in range(r*c) if p[cell] and a[cell]))\n"
        ),
        # Uses top vs bottom as the two oceans, forgetting the side edges.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "r = int(data[0]); c = int(data[1]); k = r * c\n"
            "grid = [int(x) for x in data[2:2+k]]\n"
            "def flood(starts):\n"
            "    seen = bytearray(r*c)\n"
            "    stack = []\n"
            "    for cell in starts:\n"
            "        if not seen[cell]:\n"
            "            seen[cell] = 1; stack.append(cell)\n"
            "    while stack:\n"
            "        cell = stack.pop(); i, j = divmod(cell, c); h = grid[cell]\n"
            "        for ni, nj in ((i-1,j),(i+1,j),(i,j-1),(i,j+1)):\n"
            "            if 0 <= ni < r and 0 <= nj < c:\n"
            "                nb = ni*c+nj\n"
            "                if not seen[nb] and grid[nb] >= h:\n"
            "                    seen[nb] = 1; stack.append(nb)\n"
            "    return seen\n"
            "p = flood([j for j in range(c)])\n"
            "a = flood([(r-1)*c+j for j in range(c)])\n"
            "print(sum(1 for cell in range(r*c) if p[cell] and a[cell]))\n"
        ),
        # Correct but floods outwards from every cell: O((r*c)^2).
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "r = int(data[0]); c = int(data[1]); k = r * c\n"
            "grid = [int(x) for x in data[2:2+k]]\n"
            "total = 0\n"
            "for start in range(r*c):\n"
            "    seen = bytearray(r*c)\n"
            "    seen[start] = 1\n"
            "    stack = [start]\n"
            "    pac = atl = False\n"
            "    while stack:\n"
            "        cell = stack.pop(); i, j = divmod(cell, c); h = grid[cell]\n"
            "        if i == 0 or j == 0:\n"
            "            pac = True\n"
            "        if i == r-1 or j == c-1:\n"
            "            atl = True\n"
            "        for ni, nj in ((i-1,j),(i+1,j),(i,j-1),(i,j+1)):\n"
            "            if 0 <= ni < r and 0 <= nj < c:\n"
            "                nb = ni*c+nj\n"
            "                if not seen[nb] and grid[nb] <= h:\n"
            "                    seen[nb] = 1; stack.append(nb)\n"
            "    if pac and atl:\n"
            "        total += 1\n"
            "print(total)\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  14 · Number of Islands                                                     #
# --------------------------------------------------------------------------- #

NUMBER_OF_ISLANDS = {
    "slug": "b75-number-of-islands",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 35,
    "title": "Number of Islands",
    "statement": (
        "A grid holds 1 for land and 0 for water. An island is a maximal "
        "group of land cells connected horizontally or vertically — diagonal "
        "contact does NOT join two islands.\n\n"
        "Count the islands. The grid may be empty (r = c = 0), in which case "
        "the answer is 0. A hidden case is 400 by 400 solid land, so a "
        "recursive flood fill overflows the stack: keep an explicit stack or "
        "queue."
    ),
    "constraints": [
        "0 <= r, c <= 500, and r * c <= 250000",
        "Every grid value is 0 or 1",
        "Diagonally touching land cells are separate islands",
        "Solve iteratively: the largest island can contain 160000 cells",
    ],
    "input_format": (
        "Line 1: r and c.\n"
        "Then r * c values, each 0 or 1, in row-major order. When r * c is 0 no "
        "values follow."
    ),
    "output_format": "A single integer: the number of islands.",
    "examples": [
        {
            "stdin": "4 5\n1 1 0 0 0\n1 1 0 0 0\n0 0 1 0 0\n0 0 0 1 1\n",
            "stdout": "3",
            "explanation": (
                "The 2x2 block, the lone cell in row 3, and the pair in row 4 are three "
                "islands. The lone cell touches the pair only diagonally, which does not count."
            ),
        },
        {
            "stdin": "2 2\n1 0\n0 1\n",
            "stdout": "2",
            "explanation": (
                "The two land cells touch only at a corner, so they are two islands. A "
                "solution that also walks diagonals would answer 1."
            ),
        },
    ],
    "criteria": [
        "Use 4-directional connectivity only",
        "Print 0 for an empty grid and for an all-water grid",
        "Count a full grid of land as exactly 1",
        "Flood fill iteratively so 160000 connected cells do not overflow the stack",
    ],
    "io": {
        "mode": "tokens",
        "function": "number_of_islands",
        "todo": "return the number of 4-connected groups of 1s in the grid",
        "reads": [
            {"name": "r", "type": "int"},
            {"name": "c", "type": "int"},
            {"name": "k", "type": "int", "value": "r * c"},
            {"name": "grid", "type": "int", "count": "k"},
        ],
        "args": ["grid", "r", "c"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.buffer.read().split()\n"
        "    r = int(data[0]); c = int(data[1]); k = r * c\n"
        "    grid = bytearray(int(x) for x in data[2:2 + k])\n"
        "    islands = 0\n"
        "    for start in range(r * c):\n"
        "        if not grid[start]:\n"
        "            continue\n"
        "        islands += 1\n"
        "        grid[start] = 0\n"
        "        stack = [start]\n"
        "        while stack:\n"
        "            cell = stack.pop()\n"
        "            i, j = divmod(cell, c)\n"
        "            if i > 0 and grid[cell - c]:\n"
        "                grid[cell - c] = 0\n"
        "                stack.append(cell - c)\n"
        "            if i + 1 < r and grid[cell + c]:\n"
        "                grid[cell + c] = 0\n"
        "                stack.append(cell + c)\n"
        "            if j > 0 and grid[cell - 1]:\n"
        "                grid[cell - 1] = 0\n"
        "                stack.append(cell - 1)\n"
        "            if j + 1 < c and grid[cell + 1]:\n"
        "                grid[cell + 1] = 0\n"
        "                stack.append(cell + 1)\n"
        "    print(islands)\n"
        "main()\n"
    ),
    "inputs": [
        {
            "name": "sample: three islands",
            "stdin": "4 5\n1 1 0 0 0\n1 1 0 0 0\n0 0 1 0 0\n0 0 0 1 1\n",
            "hidden": False,
        },
        {"name": "sample: diagonal touch", "stdin": "2 2\n1 0\n0 1\n", "hidden": False},
        {"name": "hidden: empty grid", "stdin": "0 0\n", "hidden": True},
        {"name": "hidden: all water", "stdin": _uniform_grid_case(3, 4, 0), "hidden": True},
        {"name": "hidden: all land", "stdin": _uniform_grid_case(3, 4, 1), "hidden": True},
        {"name": "hidden: single cell land", "stdin": "1 1\n1\n", "hidden": True},
        # A checkerboard maximises the diagonal-connectivity discrepancy.
        {
            "name": "hidden: checkerboard",
            "stdin": "4 4\n1 0 1 0\n0 1 0 1\n1 0 1 0\n0 1 0 1\n",
            "hidden": True,
        },
        # One U-shaped island: its two arms have no land above or to the left,
        # so a solution without a real flood fill counts it twice.
        {"name": "hidden: u-shaped island", "stdin": "2 3\n1 0 1\n1 1 1\n", "hidden": True},
        {"name": "hidden: single row", "stdin": "1 7\n1 0 1 1 0 0 1\n", "hidden": True},
        {"name": "hidden: single column", "stdin": "7 1\n1 0 1 1 0 0 1\n", "hidden": True},
        # 160000 land cells in one island: recursion dies here.
        {"name": "hidden: solid 400 x 400 (stack trap)", "stdin": _uniform_grid_case(400, 400, 1), "hidden": True},
        {"name": "hidden: scale random", "stdin": _grid_case(801, 500, 500, 0, 1), "hidden": True},
    ],
    "wrong": [
        # Counts land cells instead of components.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "k = int(data[0]) * int(data[1])\n"
            "print(sum(int(x) for x in data[2:2+k]))\n"
        ),
        # Walks the eight neighbours, merging diagonally touching islands.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "r = int(data[0]); c = int(data[1]); k = r * c\n"
            "grid = bytearray(int(x) for x in data[2:2+k])\n"
            "islands = 0\n"
            "for start in range(r*c):\n"
            "    if not grid[start]:\n"
            "        continue\n"
            "    islands += 1\n"
            "    grid[start] = 0\n"
            "    stack = [start]\n"
            "    while stack:\n"
            "        cell = stack.pop(); i, j = divmod(cell, c)\n"
            "        for di in (-1, 0, 1):\n"
            "            for dj in (-1, 0, 1):\n"
            "                ni, nj = i+di, j+dj\n"
            "                if 0 <= ni < r and 0 <= nj < c:\n"
            "                    nb = ni*c+nj\n"
            "                    if grid[nb]:\n"
            "                        grid[nb] = 0; stack.append(nb)\n"
            "print(islands)\n"
        ),
        # Single pass with no flood fill or union: counts every land cell that
        # has no land above or to its left, which double-counts a U shape.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "r = int(data[0]); c = int(data[1]); k = r * c\n"
            "grid = [int(x) for x in data[2:2+k]]\n"
            "islands = 0\n"
            "for i in range(r):\n"
            "    for j in range(c):\n"
            "        if not grid[i*c+j]:\n"
            "            continue\n"
            "        up = i > 0 and grid[(i-1)*c+j]\n"
            "        left = j > 0 and grid[i*c+j-1]\n"
            "        if not up and not left:\n"
            "            islands += 1\n"
            "print(islands)\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  15 · Longest Consecutive Sequence                                          #
# --------------------------------------------------------------------------- #

LONGEST_CONSECUTIVE = {
    "slug": "b75-longest-consecutive-sequence",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Longest Consecutive Sequence",
    "statement": (
        "Given an unsorted array of n integers, return the length of the "
        "longest run of consecutive integers present in the array.\n\n"
        "The values need not be adjacent in the array, and duplicates do not "
        "lengthen a run: 1 2 2 3 contains the run 1 2 3 of length 3."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= arr[i] <= 1000000000",
        "Duplicates are common",
        "An O(n) hash-set walk or an O(n log n) sort is expected; scanning the "
        "array once per value is quadratic and times out",
    ],
    "input_format": "Line 1: n.\nLine 2: n space-separated integers.",
    "output_format": "A single integer: the length of the longest consecutive run.",
    "examples": [
        {
            "stdin": "6\n100 4 200 1 3 2\n",
            "stdout": "4",
            "explanation": "1, 2, 3, 4 are all present, so the answer is 4.",
        },
        {
            "stdin": "4\n1 2 2 3\n",
            "stdout": "3",
            "explanation": "The repeated 2 does not extend the run 1, 2, 3.",
        },
    ],
    "criteria": [
        "Ignore duplicates rather than counting them as steps",
        "Handle n = 1",
        "Handle negative values and runs crossing zero",
        "Finish n = 200000 inside the time limit",
    ],
    "io": {
        "mode": "tokens",
        "function": "longest_consecutive",
        "todo": "return the length of the longest run of consecutive integers in arr",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.buffer.read().split()\n"
        "    n = int(data[0])\n"
        "    values = set(int(x) for x in data[1:1 + n])\n"
        "    best = 0\n"
        "    for value in values:\n"
        "        if value - 1 in values:\n"
        "            continue\n"
        "        length = 1\n"
        "        while value + length in values:\n"
        "            length += 1\n"
        "        if length > best:\n"
        "            best = length\n"
        "    print(best)\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: 100 4 200 1 3 2", "stdin": "6\n100 4 200 1 3 2\n", "hidden": False},
        {"name": "sample: duplicate inside run", "stdin": "4\n1 2 2 3\n", "hidden": False},
        {"name": "hidden: single value", "stdin": "1\n-9\n", "hidden": True},
        {"name": "hidden: all identical", "stdin": "5\n8 8 8 8 8\n", "hidden": True},
        {"name": "hidden: crosses zero", "stdin": "5\n-2 0 -1 1 5\n", "hidden": True},
        {"name": "hidden: no run", "stdin": "4\n10 20 30 40\n", "hidden": True},
        # The run is present but scattered, so an in-order scan reports 1.
        {"name": "hidden: reverse order", "stdin": "5\n5 4 3 2 1\n", "hidden": True},
        {"name": "hidden: extremes", "stdin": "3\n1000000000 999999999 -1000000000\n", "hidden": True},
        # Dense values: the run is long and duplicates abound.
        {"name": "hidden: scale dense", "stdin": _array_case(901, 200000, 1, 150000), "hidden": True},
        {"name": "hidden: scale sparse", "stdin": _array_case(902, 200000, -10**9, 10**9), "hidden": True},
    ],
    "wrong": [
        # Sorts but lets duplicates extend the run.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "n = int(data[0]); arr = sorted(int(x) for x in data[1:1+n])\n"
            "best = cur = 1\n"
            "for i in range(1, n):\n"
            "    if arr[i] == arr[i-1] + 1 or arr[i] == arr[i-1]:\n"
            "        cur += 1\n"
            "    else:\n"
            "        cur = 1\n"
            "    best = max(best, cur)\n"
            "print(best)\n"
        ),
        # Longest consecutive run in the array's own order.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "n = int(data[0]); arr = [int(x) for x in data[1:1+n]]\n"
            "best = cur = 1\n"
            "for i in range(1, n):\n"
            "    cur = cur + 1 if arr[i] == arr[i-1] + 1 else 1\n"
            "    best = max(best, cur)\n"
            "print(best)\n"
        ),
        # Correct but uses list membership: quadratic, dies on the scale cases.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "n = int(data[0]); arr = [int(x) for x in data[1:1+n]]\n"
            "best = 0\n"
            "for v in arr:\n"
            "    if v - 1 in arr:\n"
            "        continue\n"
            "    length = 1\n"
            "    while v + length in arr:\n"
            "        length += 1\n"
            "    best = max(best, length)\n"
            "print(best)\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  16 · Alien Dictionary                                                      #
# --------------------------------------------------------------------------- #

ALIEN_DICTIONARY = {
    "slug": "b75-alien-dictionary",
    "skill_id": "dsa_arrays",
    "difficulty": 8,
    "estimated_minutes": 50,
    "title": "Alien Dictionary",
    "statement": (
        "You are given words from an alien dictionary, listed in that "
        "language's sorted order. Recover the alphabet.\n\n"
        "Many orders can be consistent with the same word list, so string "
        "comparison would punish a correct answer. This problem therefore "
        "asks for exactly one of them: print the LEXICOGRAPHICALLY SMALLEST "
        "valid order, comparing the letters by their ordinary English order. "
        "Break every tie by taking the smallest available letter next.\n\n"
        "Print INVALID if no order is consistent — either because the "
        "constraints form a cycle, or because a word is followed by a strict "
        "prefix of itself (a sorted list can never place 'abc' before 'ab').\n\n"
        "Every letter that appears in any word must appear exactly once in the "
        "output, including letters that no comparison constrains."
    ),
    "constraints": [
        "1 <= number of words <= 20000, all on one line",
        "1 <= word length <= 20, lowercase English letters only",
        "The output contains each distinct letter of the input exactly once",
        "Only adjacent word pairs carry information",
        "Ties must be broken towards the smallest letter, so a plain "
        "topological sort is not enough",
    ],
    "input_format": "A single line of space-separated words in alien sorted order.",
    "output_format": (
        "One line: the lexicographically smallest valid alphabet as a string "
        "with no separators, or INVALID."
    ),
    "examples": [
        {
            "stdin": "wrt wrf er ett rftt\n",
            "stdout": "wertf",
            "explanation": (
                "wrt before wrf gives t<f; wrf before er gives w<e; er before ett gives "
                "r<t; ett before rftt gives e<r. Only wertf satisfies all four."
            ),
        },
        {
            "stdin": "ba bc\n",
            "stdout": "abc",
            "explanation": (
                "The only constraint is a<c, and b is unconstrained. Several orders work; "
                "abc is the smallest, so a topological sort that emitted bac would be wrong."
            ),
        },
        {
            "stdin": "abc ab\n",
            "stdout": "INVALID",
            "explanation": "A sorted list cannot place a word before its own prefix.",
        },
    ],
    "criteria": [
        "Print the lexicographically smallest valid order, not any valid order",
        "Print INVALID for a cyclic constraint set",
        "Print INVALID when a word precedes a strict prefix of itself",
        "Include unconstrained letters in the output",
        "Compare only adjacent word pairs, and only up to their first difference",
    ],
    "io": {
        "mode": "line",
        "function": "alien_order",
        "todo": "return 0 after printing the smallest valid alphabet, or INVALID (see the statement)",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "import heapq\n"
        "def main():\n"
        "    words = sys.stdin.readline().split()\n"
        "    letters = set()\n"
        "    for word in words:\n"
        "        letters.update(word)\n"
        "    adj = {ch: set() for ch in letters}\n"
        "    indeg = {ch: 0 for ch in letters}\n"
        "    for first, second in zip(words, words[1:]):\n"
        "        differed = False\n"
        "        for a, b in zip(first, second):\n"
        "            if a != b:\n"
        "                if b not in adj[a]:\n"
        "                    adj[a].add(b)\n"
        "                    indeg[b] += 1\n"
        "                differed = True\n"
        "                break\n"
        "        if not differed and len(first) > len(second):\n"
        "            print('INVALID')\n"
        "            return\n"
        "    heap = sorted(ch for ch in letters if indeg[ch] == 0)\n"
        "    heapq.heapify(heap)\n"
        "    order = []\n"
        "    while heap:\n"
        "        ch = heapq.heappop(heap)\n"
        "        order.append(ch)\n"
        "        for nb in sorted(adj[ch]):\n"
        "            indeg[nb] -= 1\n"
        "            if indeg[nb] == 0:\n"
        "                heapq.heappush(heap, nb)\n"
        "    if len(order) != len(letters):\n"
        "        print('INVALID')\n"
        "    else:\n"
        "        print(''.join(order))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: wrt wrf er ett rftt", "stdin": "wrt wrf er ett rftt\n", "hidden": False},
        {"name": "sample: tie broken smallest", "stdin": "ba bc\n", "hidden": False},
        {"name": "sample: prefix violation", "stdin": "abc ab\n", "hidden": False},
        {"name": "hidden: single word", "stdin": "zyx\n", "hidden": True},
        {"name": "hidden: repeated word", "stdin": "ab ab\n", "hidden": True},
        {"name": "hidden: prefix in order is fine", "stdin": "ab abc\n", "hidden": True},
        # The cycle case is deliberately visible: its expected output is the word
        # INVALID, which the statement has to name anyway, so hiding it would be
        # a leak dressed up as a hidden case.
        {"name": "sample: direct cycle", "stdin": "a b a\n", "hidden": False},
        {"name": "hidden: three-word chain", "stdin": "ab bc ca\n", "hidden": True},
        # Two independent chains: the smallest order interleaves them.
        {"name": "hidden: interleaved chains", "stdin": "za zb ya yc\n", "hidden": True},
        # Every letter is unconstrained, so the answer is plain English order.
        {"name": "hidden: no constraints", "stdin": "q\n", "hidden": True},
        {"name": "hidden: full alphabet chain", "stdin": _alien_case(1001, 200), "hidden": True},
        {"name": "hidden: scale", "stdin": _alien_case(1002, 20000, 20), "hidden": True},
    ],
    "wrong": [
        # Any topological order (stack based), not the smallest.
        (
            "import sys\n"
            "words = sys.stdin.readline().split()\n"
            "letters = set()\n"
            "for w in words:\n"
            "    letters.update(w)\n"
            "adj = {ch: set() for ch in letters}\n"
            "indeg = {ch: 0 for ch in letters}\n"
            "bad = False\n"
            "for x, y in zip(words, words[1:]):\n"
            "    differed = False\n"
            "    for a, b in zip(x, y):\n"
            "        if a != b:\n"
            "            if b not in adj[a]:\n"
            "                adj[a].add(b); indeg[b] += 1\n"
            "            differed = True\n"
            "            break\n"
            "    if not differed and len(x) > len(y):\n"
            "        bad = True\n"
            "if bad:\n"
            "    print('INVALID')\n"
            "else:\n"
            "    stack = sorted(ch for ch in letters if indeg[ch] == 0)\n"
            "    order = []\n"
            "    while stack:\n"
            "        ch = stack.pop()\n"
            "        order.append(ch)\n"
            "        for nb in sorted(adj[ch]):\n"
            "            indeg[nb] -= 1\n"
            "            if indeg[nb] == 0:\n"
            "                stack.append(nb)\n"
            "    print(''.join(order) if len(order) == len(letters) else 'INVALID')\n"
        ),
        # Forgets the prefix rule.
        (
            "import sys\n"
            "import heapq\n"
            "words = sys.stdin.readline().split()\n"
            "letters = set()\n"
            "for w in words:\n"
            "    letters.update(w)\n"
            "adj = {ch: set() for ch in letters}\n"
            "indeg = {ch: 0 for ch in letters}\n"
            "for x, y in zip(words, words[1:]):\n"
            "    for a, b in zip(x, y):\n"
            "        if a != b:\n"
            "            if b not in adj[a]:\n"
            "                adj[a].add(b); indeg[b] += 1\n"
            "            break\n"
            "heap = sorted(ch for ch in letters if indeg[ch] == 0)\n"
            "heapq.heapify(heap)\n"
            "order = []\n"
            "while heap:\n"
            "    ch = heapq.heappop(heap)\n"
            "    order.append(ch)\n"
            "    for nb in sorted(adj[ch]):\n"
            "        indeg[nb] -= 1\n"
            "        if indeg[nb] == 0:\n"
            "            heapq.heappush(heap, nb)\n"
            "print(''.join(order) if len(order) == len(letters) else 'INVALID')\n"
        ),
        # Drops letters that appear in no constraint.
        (
            "import sys\n"
            "import heapq\n"
            "words = sys.stdin.readline().split()\n"
            "adj = {}\n"
            "indeg = {}\n"
            "def touch(ch):\n"
            "    adj.setdefault(ch, set()); indeg.setdefault(ch, 0)\n"
            "bad = False\n"
            "for x, y in zip(words, words[1:]):\n"
            "    differed = False\n"
            "    for a, b in zip(x, y):\n"
            "        if a != b:\n"
            "            touch(a); touch(b)\n"
            "            if b not in adj[a]:\n"
            "                adj[a].add(b); indeg[b] += 1\n"
            "            differed = True\n"
            "            break\n"
            "    if not differed and len(x) > len(y):\n"
            "        bad = True\n"
            "if bad:\n"
            "    print('INVALID')\n"
            "else:\n"
            "    heap = sorted(ch for ch in adj if indeg[ch] == 0)\n"
            "    heapq.heapify(heap)\n"
            "    order = []\n"
            "    while heap:\n"
            "        ch = heapq.heappop(heap)\n"
            "        order.append(ch)\n"
            "        for nb in sorted(adj[ch]):\n"
            "            indeg[nb] -= 1\n"
            "            if indeg[nb] == 0:\n"
            "                heapq.heappush(heap, nb)\n"
            "    print(''.join(order) if len(order) == len(adj) else 'INVALID')\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  17 · Number of Connected Components in an Undirected Graph                 #
# --------------------------------------------------------------------------- #

CONNECTED_COMPONENTS = {
    "slug": "b75-connected-components",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Number of Connected Components in an Undirected Graph",
    "statement": (
        "Given an UNDIRECTED graph on n vertices labelled 1..n, count its "
        "connected components.\n\n"
        "An isolated vertex is a component of its own, so a graph with no "
        "edges has n components. The edge list may contain duplicate edges "
        "and self-loops, neither of which changes the answer — n - m is "
        "therefore not the answer.\n\n"
        "A hidden case is a single path through 100000 vertices, so traverse "
        "iteratively or use union-find rather than recursion."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "0 <= m <= 200000",
        "1 <= u, v <= n; self-loops and duplicate edges are possible",
        "Solve iteratively or with union-find: a path of 100000 vertices "
        "overflows a recursive traversal",
    ],
    "input_format": (
        "Line 1: n and m separated by a space.\n"
        "Line 2: m integers, one endpoint of each edge.\n"
        "Line 3: m integers, the other endpoint of each edge.\n"
        "Edge i joins the i-th value on line 2 to the i-th value on line 3. "
        "When m is 0 lines 2 and 3 are empty or absent."
    ),
    "output_format": "A single integer: the number of connected components.",
    "examples": [
        {
            "stdin": "5 3\n1 2 4\n2 3 5\n",
            "stdout": "2",
            "explanation": "1-2-3 is one component and 4-5 is the other.",
        },
        {
            "stdin": "4 0\n\n\n",
            "stdout": "4",
            "explanation": "With no edges every vertex is its own component.",
        },
    ],
    "criteria": [
        "Count isolated vertices as components",
        "Stay correct when the same edge is listed twice or a self-loop appears",
        "Traverse iteratively so a 100000-vertex path is safe",
        "Run in near-linear time at n = m = 200000",
    ],
    "io": {
        "mode": "tokens",
        "function": "connected_components",
        "todo": "return the number of connected components of the undirected graph",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "m", "type": "int"},
            {"name": "src", "type": "int", "count": "m"},
            {"name": "dst", "type": "int", "count": "m"},
        ],
        "args": ["n", "src", "dst"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.buffer.read().split()\n"
        "    n = int(data[0]); m = int(data[1])\n"
        "    parent = list(range(n + 1))\n"
        "    def find(x):\n"
        "        while parent[x] != x:\n"
        "            parent[x] = parent[parent[x]]\n"
        "            x = parent[x]\n"
        "        return x\n"
        "    components = n\n"
        "    for i in range(m):\n"
        "        a = find(int(data[2 + i]))\n"
        "        b = find(int(data[2 + m + i]))\n"
        "        if a != b:\n"
        "            parent[a] = b\n"
        "            components -= 1\n"
        "    print(components)\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: two components", "stdin": "5 3\n1 2 4\n2 3 5\n", "hidden": False},
        {"name": "sample: no edges", "stdin": "4 0\n\n\n", "hidden": False},
        {"name": "hidden: single vertex", "stdin": "1 0\n\n\n", "hidden": True},
        {"name": "hidden: self-loop only", "stdin": "3 1\n2\n2\n", "hidden": True},
        # n - m = 1 here but the answer is 2: duplicates and a cycle.
        {
            "name": "hidden: duplicates and a cycle",
            "stdin": "5 4\n1 1 2 3\n2 2 3 1\n",
            "hidden": True,
        },
        {"name": "hidden: fully connected", "stdin": "4 3\n1 2 3\n2 3 4\n", "hidden": True},
        {"name": "hidden: deep path (stack trap)", "stdin": _path_graph_case(100000), "hidden": True},
        {
            "name": "hidden: scale seven components",
            "stdin": _undirected_graph_case(1101, 200000, 20000, components=7),
            "hidden": True,
        },
        {
            "name": "hidden: scale dense single component",
            "stdin": _undirected_graph_case(1102, 100000, 100000, components=1),
            "hidden": True,
        },
    ],
    "wrong": [
        # n - m, which duplicates, self-loops and cycles break.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "print(int(data[0]) - int(data[1]))\n"
        ),
        # Counts components only among vertices that appear in an edge.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "n = int(data[0]); m = int(data[1])\n"
            "parent = list(range(n + 1))\n"
            "seen = set()\n"
            "def find(x):\n"
            "    while parent[x] != x:\n"
            "        parent[x] = parent[parent[x]]\n"
            "        x = parent[x]\n"
            "    return x\n"
            "for i in range(m):\n"
            "    u = int(data[2+i]); v = int(data[2+m+i])\n"
            "    seen.add(u); seen.add(v)\n"
            "    a, b = find(u), find(v)\n"
            "    if a != b:\n"
            "        parent[a] = b\n"
            "print(len({find(x) for x in seen}))\n"
        ),
        # Deduplicates edges and drops self-loops, then assumes every remaining
        # edge merges two components — a cycle breaks that assumption.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "n = int(data[0]); m = int(data[1])\n"
            "edges = set()\n"
            "for i in range(m):\n"
            "    u = int(data[2+i]); v = int(data[2+m+i])\n"
            "    if u != v:\n"
            "        edges.add((min(u, v), max(u, v)))\n"
            "print(n - len(edges))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  18 · Set Matrix Zeroes                                                     #
# --------------------------------------------------------------------------- #

SET_MATRIX_ZEROES = {
    "slug": "b75-set-matrix-zeroes",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Set Matrix Zeroes",
    "statement": (
        "Given an r by c matrix, if a cell holds 0 then its entire row and "
        "column become 0. Print the resulting matrix.\n\n"
        "Only the zeroes present in the ORIGINAL matrix trigger this: a cell "
        "blanked by the rule must not blank further rows and columns. The "
        "intended solution edits the matrix in place, recording which rows "
        "and columns to clear before writing anything.\n\n"
        "Note that stdout cannot show whether you allocated a second matrix, "
        "so the in-place requirement is on your honour; the graded property "
        "is the output."
    ),
    "constraints": [
        "1 <= r, c <= 200",
        "-1000 <= value <= 1000",
        "Cascading is wrong: use the zeroes of the input only",
        "Do the marking pass before the writing pass",
    ],
    "input_format": (
        "Line 1: r and c.\n"
        "Then r * c integers in row-major order (r rows of c values)."
    ),
    "output_format": (
        "r lines, each with c space-separated integers: the transformed matrix."
    ),
    "examples": [
        {
            "stdin": "3 3\n1 1 1\n1 0 1\n1 1 1\n",
            "stdout": "1 0 1\n0 0 0\n1 0 1",
            "explanation": "The single 0 at (1,1) clears row 1 and column 1.",
        },
        {
            "stdin": "2 3\n0 1 2\n3 4 5\n",
            "stdout": "0 0 0\n0 4 5",
            "explanation": (
                "The 0 at (0,0) clears row 0 and column 0. Cell (1,0) becomes 0 but must "
                "not then clear row 1, so 4 and 5 survive."
            ),
        },
    ],
    "criteria": [
        "Use only the zeroes of the input matrix, never the ones you write",
        "Handle a 1 by 1 matrix and a matrix with no zeroes",
        "Print exactly r lines of c space-separated values",
        "Transform in place, using O(r + c) or O(1) extra space",
    ],
    "io": {
        "mode": "tokens",
        "function": "set_matrix_zeroes",
        "todo": "print r lines of c values after zeroing the row and column of every original zero",
        "reads": [
            {"name": "r", "type": "int"},
            {"name": "c", "type": "int"},
            {"name": "k", "type": "int", "value": "r * c"},
            {"name": "grid", "type": "int", "count": "k"},
        ],
        "args": ["grid", "r", "c"],
        "returns": "void",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.buffer.read().split()\n"
        "    r = int(data[0]); c = int(data[1]); k = r * c\n"
        "    grid = [int(x) for x in data[2:2 + k]]\n"
        "    zero_rows = set()\n"
        "    zero_cols = set()\n"
        "    for i in range(r):\n"
        "        base = i * c\n"
        "        for j in range(c):\n"
        "            if grid[base + j] == 0:\n"
        "                zero_rows.add(i)\n"
        "                zero_cols.add(j)\n"
        "    out = []\n"
        "    for i in range(r):\n"
        "        base = i * c\n"
        "        if i in zero_rows:\n"
        "            row = ['0'] * c\n"
        "        else:\n"
        "            row = [\n"
        "                '0' if j in zero_cols else str(grid[base + j])\n"
        "                for j in range(c)\n"
        "            ]\n"
        "        out.append(' '.join(row))\n"
        "    sys.stdout.write('\\n'.join(out) + '\\n')\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: centre zero", "stdin": "3 3\n1 1 1\n1 0 1\n1 1 1\n", "hidden": False},
        {"name": "sample: corner zero", "stdin": "2 3\n0 1 2\n3 4 5\n", "hidden": False},
        {"name": "hidden: no zeroes", "stdin": "2 2\n1 2\n3 4\n", "hidden": True},
        {"name": "hidden: single cell zero", "stdin": "1 1\n0\n", "hidden": True},
        {"name": "hidden: single cell non-zero", "stdin": "1 1\n7\n", "hidden": True},
        {"name": "hidden: all zeroes", "stdin": _uniform_grid_case(3, 3, 0), "hidden": True},
        # A cascading solution wipes the whole matrix here.
        {
            "name": "hidden: cascade trap",
            "stdin": "3 3\n1 0 3\n4 5 6\n7 8 9\n",
            "hidden": True,
        },
        {"name": "hidden: single row", "stdin": "1 5\n1 2 0 4 5\n", "hidden": True},
        {"name": "hidden: single column", "stdin": "5 1\n1 2 0 4 5\n", "hidden": True},
        {"name": "hidden: negatives", "stdin": "2 3\n-1 -2 0\n-4 -5 -6\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _grid_case(1201, 200, 200, -3, 3), "hidden": True},
        {
            "name": "hidden: scale sparse zeroes",
            "stdin": _grid_case(1202, 200, 200, 1, 400),
            "hidden": True,
        },
    ],
    "wrong": [
        # Cascades: zeroes written by the rule trigger more clearing.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "r = int(data[0]); c = int(data[1]); k = r * c\n"
            "grid = [int(x) for x in data[2:2+k]]\n"
            "for i in range(r):\n"
            "    for j in range(c):\n"
            "        if grid[i*c+j] == 0:\n"
            "            for jj in range(c):\n"
            "                grid[i*c+jj] = 0\n"
            "            for ii in range(r):\n"
            "                grid[ii*c+j] = 0\n"
            "out = []\n"
            "for i in range(r):\n"
            "    out.append(' '.join(str(grid[i*c+j]) for j in range(c)))\n"
            "sys.stdout.write('\\n'.join(out) + '\\n')\n"
        ),
        # Clears rows but forgets columns.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "r = int(data[0]); c = int(data[1]); k = r * c\n"
            "grid = [int(x) for x in data[2:2+k]]\n"
            "rows = {i for i in range(r) if any(grid[i*c+j] == 0 for j in range(c))}\n"
            "out = []\n"
            "for i in range(r):\n"
            "    if i in rows:\n"
            "        out.append(' '.join(['0'] * c))\n"
            "    else:\n"
            "        out.append(' '.join(str(grid[i*c+j]) for j in range(c)))\n"
            "sys.stdout.write('\\n'.join(out) + '\\n')\n"
        ),
        # Echoes the matrix unchanged.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "r = int(data[0]); c = int(data[1]); k = r * c\n"
            "grid = [int(x) for x in data[2:2+k]]\n"
            "out = [' '.join(str(grid[i*c+j]) for j in range(c)) for i in range(r)]\n"
            "sys.stdout.write('\\n'.join(out) + '\\n')\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  19 · Spiral Matrix                                                         #
# --------------------------------------------------------------------------- #

SPIRAL_MATRIX = {
    "slug": "b75-spiral-matrix",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Spiral Matrix",
    "statement": (
        "Print every value of an r by c matrix in spiral order: left to right "
        "along the top row, down the right column, right to left along the "
        "bottom row, up the left column, then inwards and repeat.\n\n"
        "The last layer of a spiral is the usual bug: when it is a single row "
        "or a single column, walking it twice duplicates values."
    ),
    "constraints": [
        "1 <= r, c <= 100",
        "-1000000 <= value <= 1000000",
        "The output holds exactly r * c values, each printed once",
    ],
    "input_format": (
        "Line 1: r and c.\n"
        "Then r * c integers in row-major order (r rows of c values)."
    ),
    "output_format": "One line: the r * c values in spiral order, space-separated.",
    "examples": [
        {
            "stdin": "3 3\n1 2 3\n4 5 6\n7 8 9\n",
            "stdout": "1 2 3 6 9 8 7 4 5",
            "explanation": "Around the border clockwise, then the centre cell 5.",
        },
        {
            "stdin": "3 4\n1 2 3 4\n5 6 7 8\n9 10 11 12\n",
            "stdout": "1 2 3 4 8 12 11 10 9 5 6 7",
            "explanation": (
                "After the border, the remaining layer is the single row 6 7, walked left "
                "to right once — not once in each direction."
            ),
        },
    ],
    "criteria": [
        "Emit each value exactly once, including for a 1 by n and an n by 1 matrix",
        "Handle an odd centre cell",
        "Print the values on one line separated by single spaces",
    ],
    "io": {
        "mode": "tokens",
        "function": "spiral_matrix",
        "todo": "print the r * c values in spiral order on one line",
        "reads": [
            {"name": "r", "type": "int"},
            {"name": "c", "type": "int"},
            {"name": "k", "type": "int", "value": "r * c"},
            {"name": "grid", "type": "int", "count": "k"},
        ],
        "args": ["grid", "r", "c"],
        # The answer is a sequence, not a number: a scalar return type here
        # would hand the learner a signature the task cannot satisfy.
        "returns": "void",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.buffer.read().split()\n"
        "    r = int(data[0]); c = int(data[1]); k = r * c\n"
        "    grid = [int(x) for x in data[2:2 + k]]\n"
        "    top, bottom, left, right = 0, r - 1, 0, c - 1\n"
        "    out = []\n"
        "    while top <= bottom and left <= right:\n"
        "        for j in range(left, right + 1):\n"
        "            out.append(grid[top * c + j])\n"
        "        for i in range(top + 1, bottom + 1):\n"
        "            out.append(grid[i * c + right])\n"
        "        if top < bottom and left < right:\n"
        "            for j in range(right - 1, left - 1, -1):\n"
        "                out.append(grid[bottom * c + j])\n"
        "            for i in range(bottom - 1, top, -1):\n"
        "                out.append(grid[i * c + left])\n"
        "        top += 1\n"
        "        bottom -= 1\n"
        "        left += 1\n"
        "        right -= 1\n"
        "    print(' '.join(str(v) for v in out))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: 3 x 3", "stdin": "3 3\n1 2 3\n4 5 6\n7 8 9\n", "hidden": False},
        {
            "name": "sample: 3 x 4",
            "stdin": "3 4\n1 2 3 4\n5 6 7 8\n9 10 11 12\n",
            "hidden": False,
        },
        {"name": "hidden: single cell", "stdin": "1 1\n42\n", "hidden": True},
        {"name": "hidden: single row", "stdin": "1 5\n1 2 3 4 5\n", "hidden": True},
        {"name": "hidden: single column", "stdin": "5 1\n1 2 3 4 5\n", "hidden": True},
        {"name": "hidden: 2 x 2", "stdin": "2 2\n1 2\n3 4\n", "hidden": True},
        # Tall matrix: the innermost layer is a single column.
        {"name": "hidden: 4 x 3", "stdin": "4 3\n1 2 3\n4 5 6\n7 8 9\n10 11 12\n", "hidden": True},
        {"name": "hidden: 5 x 5 negatives", "stdin": _grid_case(1301, 5, 5, -1000, 1000), "hidden": True},
        {"name": "hidden: scale 100 x 100", "stdin": _grid_case(1302, 100, 100, -10**6, 10**6), "hidden": True},
        {"name": "hidden: scale 1 x 100", "stdin": _grid_case(1303, 1, 100, -10**6, 10**6), "hidden": True},
        {"name": "hidden: scale 100 x 1", "stdin": _grid_case(1304, 100, 1, -10**6, 10**6), "hidden": True},
    ],
    "wrong": [
        # Row-major order.
        (
            "import sys\n"
            "data = sys.stdin.read().split()\n"
            "k = int(data[0]) * int(data[1])\n"
            "print(' '.join(data[2:2+k]))\n"
        ),
        # Walks the final single row / column twice.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "r = int(data[0]); c = int(data[1]); k = r * c\n"
            "grid = [int(x) for x in data[2:2+k]]\n"
            "top, bottom, left, right = 0, r-1, 0, c-1\n"
            "out = []\n"
            "while top <= bottom and left <= right:\n"
            "    for j in range(left, right+1):\n"
            "        out.append(grid[top*c+j])\n"
            "    for i in range(top+1, bottom+1):\n"
            "        out.append(grid[i*c+right])\n"
            "    for j in range(right-1, left-1, -1):\n"
            "        out.append(grid[bottom*c+j])\n"
            "    for i in range(bottom-1, top, -1):\n"
            "        out.append(grid[i*c+left])\n"
            "    top += 1; bottom -= 1; left += 1; right -= 1\n"
            "print(' '.join(str(v) for v in out))\n"
        ),
        # Spirals anticlockwise.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "r = int(data[0]); c = int(data[1]); k = r * c\n"
            "grid = [int(x) for x in data[2:2+k]]\n"
            "top, bottom, left, right = 0, r-1, 0, c-1\n"
            "out = []\n"
            "while top <= bottom and left <= right:\n"
            "    for i in range(top, bottom+1):\n"
            "        out.append(grid[i*c+left])\n"
            "    for j in range(left+1, right+1):\n"
            "        out.append(grid[bottom*c+j])\n"
            "    if top < bottom and left < right:\n"
            "        for i in range(bottom-1, top-1, -1):\n"
            "            out.append(grid[i*c+right])\n"
            "        for j in range(right-1, left, -1):\n"
            "            out.append(grid[top*c+j])\n"
            "    top += 1; bottom -= 1; left += 1; right -= 1\n"
            "print(' '.join(str(v) for v in out))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  20 · Rotate Image                                                          #
# --------------------------------------------------------------------------- #

ROTATE_IMAGE = {
    "slug": "b75-rotate-image",
    "skill_id": "dsa_arrays",
    "difficulty": 4,
    "estimated_minutes": 25,
    "title": "Rotate Image",
    "statement": (
        "Rotate an n by n matrix by 90 degrees CLOCKWISE and print the "
        "result. The value at row i, column j moves to row j, column "
        "n-1-i.\n\n"
        "The intended solution rotates in place — transpose, then reverse "
        "each row — rather than allocating a second matrix. stdout cannot "
        "prove that, so the in-place requirement is on your honour; the "
        "graded property is the output."
    ),
    "constraints": [
        "1 <= n <= 200, and the matrix is square, so r = c = n",
        "-1000000 <= value <= 1000000",
        "Clockwise, not anticlockwise",
        "Rotate in place, using O(1) extra space beyond the matrix",
    ],
    "input_format": (
        "Line 1: r and c, where r = c = n.\n"
        "Then n * n integers in row-major order (n rows of n values)."
    ),
    "output_format": "n lines, each with n space-separated integers: the rotated matrix.",
    "examples": [
        {
            "stdin": "3 3\n1 2 3\n4 5 6\n7 8 9\n",
            "stdout": "7 4 1\n8 5 2\n9 6 3",
            "explanation": "The first column bottom-to-top (7 4 1) becomes the first row.",
        },
        {
            "stdin": "2 2\n1 2\n3 4\n",
            "stdout": "3 1\n4 2",
            "explanation": (
                "Clockwise sends 1 to the top right and 3 to the top left. Anticlockwise "
                "would print 2 4 / 1 3 instead."
            ),
        },
    ],
    "criteria": [
        "Rotate clockwise, not anticlockwise",
        "Handle n = 1 and even and odd n",
        "Print exactly n lines of n space-separated values",
        "Rotate in place rather than building a second matrix",
    ],
    "io": {
        "mode": "tokens",
        "function": "rotate_image",
        "todo": "print the n lines of the matrix rotated 90 degrees clockwise",
        "reads": [
            {"name": "r", "type": "int"},
            {"name": "c", "type": "int"},
            {"name": "k", "type": "int", "value": "r * c"},
            {"name": "grid", "type": "int", "count": "k"},
        ],
        "args": ["grid", "r", "c"],
        "returns": "void",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    data = sys.stdin.buffer.read().split()\n"
        "    n = int(data[0]); k = n * n\n"
        "    grid = [int(x) for x in data[2:2 + k]]\n"
        "    out = []\n"
        "    for i in range(n):\n"
        "        row = [str(grid[(n - 1 - j) * n + i]) for j in range(n)]\n"
        "        out.append(' '.join(row))\n"
        "    sys.stdout.write('\\n'.join(out) + '\\n')\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: 3 x 3", "stdin": "3 3\n1 2 3\n4 5 6\n7 8 9\n", "hidden": False},
        {"name": "sample: 2 x 2", "stdin": "2 2\n1 2\n3 4\n", "hidden": False},
        {"name": "hidden: single cell", "stdin": "1 1\n-5\n", "hidden": True},
        {
            "name": "hidden: 4 x 4",
            "stdin": "4 4\n1 2 3 4\n5 6 7 8\n9 10 11 12\n13 14 15 16\n",
            "hidden": True,
        },
        {"name": "hidden: all identical", "stdin": _uniform_grid_case(4, 4, 9), "hidden": True},
        # Symmetric under transpose, so a transpose-only solution slips through
        # everywhere except a case like this one being asymmetric.
        {"name": "hidden: 5 x 5 random", "stdin": _grid_case(1401, 5, 5, -1000, 1000), "hidden": True},
        {"name": "hidden: negatives", "stdin": "2 2\n-1 -2\n-3 -4\n", "hidden": True},
        {"name": "hidden: scale 200 x 200", "stdin": _grid_case(1402, 200, 200, -10**6, 10**6), "hidden": True},
    ],
    "wrong": [
        # Anticlockwise.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "n = int(data[0]); k = n * n\n"
            "grid = [int(x) for x in data[2:2+k]]\n"
            "out = []\n"
            "for i in range(n):\n"
            "    out.append(' '.join(str(grid[j*n + (n-1-i)]) for j in range(n)))\n"
            "sys.stdout.write('\\n'.join(out) + '\\n')\n"
        ),
        # Transpose only, forgetting to reverse the rows.
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "n = int(data[0]); k = n * n\n"
            "grid = [int(x) for x in data[2:2+k]]\n"
            "out = []\n"
            "for i in range(n):\n"
            "    out.append(' '.join(str(grid[j*n + i]) for j in range(n)))\n"
            "sys.stdout.write('\\n'.join(out) + '\\n')\n"
        ),
        # Reverses the row order only (a vertical flip).
        (
            "import sys\n"
            "data = sys.stdin.buffer.read().split()\n"
            "n = int(data[0]); k = n * n\n"
            "grid = [int(x) for x in data[2:2+k]]\n"
            "out = []\n"
            "for i in range(n-1, -1, -1):\n"
            "    out.append(' '.join(str(grid[i*n + j]) for j in range(n)))\n"
            "sys.stdout.write('\\n'.join(out) + '\\n')\n"
        ),
    ],
}


PROBLEMS: list[dict[str, Any]] = [
    CLIMBING_STAIRS,
    COIN_CHANGE,
    LIS,
    LCS,
    WORD_BREAK,
    COMBINATION_SUM_IV,
    HOUSE_ROBBER,
    HOUSE_ROBBER_II,
    DECODE_WAYS,
    UNIQUE_PATHS,
    JUMP_GAME,
    COURSE_SCHEDULE,
    PACIFIC_ATLANTIC,
    NUMBER_OF_ISLANDS,
    LONGEST_CONSECUTIVE,
    ALIEN_DICTIONARY,
    CONNECTED_COMPONENTS,
    SET_MATRIX_ZEROES,
    SPIRAL_MATRIX,
    ROTATE_IMAGE,
]
