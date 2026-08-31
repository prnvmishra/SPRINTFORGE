"""Blind 75 problems, batch 2.

Split across files so the catalogue can grow without one unreadable module.
Each entry follows the contract in `docs/curriculum_authoring.md`: an `io`
spec drives starter generation for every language, `reference` derives the
expected outputs, and `wrong` solutions must be rejected by the case bank.

Batch 2 covers linked lists, intervals, binary search and bit manipulation.

Adapting function-signature problems to stdin/stdout
----------------------------------------------------
*Linked lists.* One serialisation is shared by every list problem in this
batch: line 1 is the node count ``n``, line 2 is the ``n`` values from head to
tail. There is no pointer structure in the input, so the learner allocates
nodes and links them; that is the skill being examined, and it stays tractable
in C (a struct plus ``malloc``). Lists that must be printed use the *sequence
format* below. ``linked-list-cycle-entry`` cannot use values at all — a cyclic
list is unprintable — so it ships the pointer table itself (``next[i]``, with
``-1`` for null) and asks for the index of the cycle entry.

*Sequence output.* Generated starters return a single integer, so any problem
whose answer is a list states its output as ``m`` on the first line followed by
the ``m`` values, and its cases are matched on tokens rather than on exact
layout. The count prefix keeps the empty answer unambiguous ("0").

*Intervals.* Interval sets arrive as three lines — ``n``, the ``n`` starts, the
``n`` ends — which is expressible in the declarative ``io`` spec (two arrays of
length ``n``) where a flat list of pairs is not.

*Bit width.* Every bit problem states its width. The 32-bit unsigned inputs are
declared as 64-bit reads because 4294967295 does not fit a C/Java ``int``, and
``add-without-plus`` masks to 32 bits and sign-corrects in the reference so
Python's arbitrary-precision integers agree with C, C++, Java and JavaScript.
"""

from __future__ import annotations

import random
from typing import Any

# --------------------------------------------------------------------------- #
#  Deterministic input generation                                             #
# --------------------------------------------------------------------------- #


def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def _list_case(seed: int, n: int, lo: int, hi: int) -> str:
    """`n` then n random values: the shared linked-list serialisation."""
    rng = _rng(seed)
    values = [rng.randint(lo, hi) for _ in range(n)]
    return f"{n}\n{' '.join(map(str, values))}\n"


def _sorted_list_case(seed: int, n: int, lo: int, hi: int) -> str:
    rng = _rng(seed)
    values = sorted(rng.randint(lo, hi) for _ in range(n))
    return f"{n}\n{' '.join(map(str, values))}\n"


def _two_sorted_lists_case(seed: int, n: int, m: int) -> str:
    rng = _rng(seed)
    a = sorted(rng.randint(-10**9, 10**9) for _ in range(n))
    b = sorted(rng.randint(-10**9, 10**9) for _ in range(m))
    return (
        f"{n}\n{' '.join(map(str, a))}\n"
        f"{m}\n{' '.join(map(str, b))}\n"
    )


def _k_lists_case(seed: int, k: int, total: int) -> str:
    """k sorted lists holding `total` nodes between them, flattened.

    Line 1 is ``k m`` where m is the number of integers that follow; each list
    contributes its length and then its values, so m == total + k.
    """
    rng = _rng(seed)
    sizes = [total // k] * k
    for i in range(total - sum(sizes)):
        sizes[i] += 1
    flat: list[int] = []
    for size in sizes:
        values = sorted(rng.randint(-10**9, 10**9) for _ in range(size))
        flat.append(size)
        flat.extend(values)
    return f"{k} {len(flat)}\n{' '.join(map(str, flat))}\n"


def _cycle_case(seed: int, n: int, entry: int | None) -> str:
    """A chain 0 -> 1 -> ... -> n-1 whose tail points at `entry` (or null)."""
    _rng(seed)  # keep the seed contract even though the shape is fixed
    nxt = [i + 1 for i in range(n)]
    nxt[n - 1] = -1 if entry is None else entry
    return f"{n}\n{' '.join(map(str, nxt))}\n"


def _intervals_case(seed: int, n: int, span: int, length: int, extra: str = "") -> str:
    rng = _rng(seed)
    pairs = []
    for _ in range(n):
        start = rng.randint(0, span)
        pairs.append((start, start + rng.randint(0, length)))
    rng.shuffle(pairs)
    starts = " ".join(str(s) for s, _ in pairs)
    ends = " ".join(str(e) for _, e in pairs)
    tail = f"{extra}\n" if extra else ""
    return f"{n}\n{starts}\n{ends}\n{tail}"


def _disjoint_intervals_case(seed: int, n: int) -> str:
    """n intervals that never overlap, shuffled.

    A pairwise O(n^2) conflict check cannot short-circuit here, which is what
    separates it from the linear-time sweep.
    """
    rng = _rng(seed)
    pairs = []
    cursor = 0
    for _ in range(n):
        start = cursor + rng.randint(0, 3)
        end = start + rng.randint(0, 4)
        pairs.append((start, end))
        cursor = end + 1
    rng.shuffle(pairs)
    starts = " ".join(str(s) for s, _ in pairs)
    ends = " ".join(str(e) for _, e in pairs)
    return f"{n}\n{starts}\n{ends}\n"


def _sorted_array_case(seed: int, n: int, target: int, lo: int, hi: int) -> str:
    rng = _rng(seed)
    values = sorted(rng.randint(lo, hi) for _ in range(n))
    return f"{n} {target}\n{' '.join(map(str, values))}\n"


def _koko_case(seed: int, n: int, h: int, hi: int) -> str:
    rng = _rng(seed)
    piles = [rng.randint(1, hi) for _ in range(n)]
    return f"{n} {h}\n{' '.join(map(str, piles))}\n"


def _missing_number_case(seed: int, n: int) -> str:
    rng = _rng(seed)
    values = list(range(n + 1))
    values.pop(rng.randrange(n + 1))
    rng.shuffle(values)
    return f"{n}\n{' '.join(map(str, values))}\n"


# Shared wording, so the six list problems describe the same serialisation.
_LIST_INPUT = (
    "Line 1: n, the number of nodes.\n"
    "Line 2: n space-separated node values, from head to tail. The line is "
    "empty when n = 0."
)
_LIST_BUILD = (
    "The list arrives as text, not as a pointer structure: read the values, "
    "allocate your own nodes and link them together, then work on that "
    "structure. Building and relinking the list is the skill being tested."
)
_SEQ_OUTPUT = (
    "Line 1: m, the number of values in the resulting list.\n"
    "Line 2: the m values separated by single spaces, from head to tail. "
    "Print nothing on line 2 when m = 0. Whitespace layout is not graded."
)
_PAIR_OUTPUT = (
    "Line 1: m, the number of intervals in the answer.\n"
    "Then m lines, each holding the start and the end of one interval, in "
    "increasing order of start. Whitespace layout is not graded."
)


# --------------------------------------------------------------------------- #
#  01 · Reverse a linked list                                                 #
# --------------------------------------------------------------------------- #

REVERSE_LINKED_LIST = {
    "slug": "reverse-linked-list",
    "skill_id": "dsa_arrays",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Reverse a Linked List",
    "statement": (
        "Reverse a singly linked list and report the reversed sequence.\n\n"
        + _LIST_BUILD
        + "\n\nReverse the links themselves rather than only the printed "
        "order: walk the list once, pointing each node at its predecessor."
    ),
    "constraints": [
        "0 <= n <= 200000",
        "-1000000000 <= value <= 1000000000",
        "An O(n) single pass with O(1) extra pointers is expected",
        "The empty list is a valid input and its answer is the empty list",
    ],
    "input_format": _LIST_INPUT,
    "output_format": _SEQ_OUTPUT,
    "examples": [
        {
            "stdin": "5\n1 2 3 4 5\n",
            "stdout": "5\n5 4 3 2 1",
            "explanation": "Head 1 becomes the tail, so the sequence is printed back to front.",
        },
        {
            "stdin": "0\n\n",
            "stdout": "0",
            "explanation": "There are no nodes, so m is 0 and the value line is empty.",
        },
    ],
    "criteria": [
        "Build a real node structure instead of only reversing the input tokens",
        "Handle n = 0 and n = 1 without crashing",
        "Reverse in one pass, not by repeated removal from the tail",
    ],
    "io": {
        "mode": "tokens",
        "function": "reverse_list",
        "todo": "build the list, reverse it, then print m and the reversed values (replace the single-value print in main)",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "values", "type": "long", "count": "n"},
        ],
        "args": ["values"],
        "returns": "int",
    },
    "reference": """
import sys


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    head = None
    for value in values:
        head = (value, head)
    out = []
    node = head
    while node is not None:
        out.append(node[0])
        node = node[1]
    print(len(out))
    print(' '.join(map(str, out)))


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: five nodes", "stdin": "5\n1 2 3 4 5\n", "hidden": False, "match": "tokens"},
        {"name": "sample: empty list", "stdin": "0\n\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: single node", "stdin": "1\n-7\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: two nodes", "stdin": "2\n9 4\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: all identical", "stdin": "4\n5 5 5 5\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: already descending", "stdin": "3\n1000000000 0 -1000000000\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: scale", "stdin": _list_case(101, 200000, -10**9, 10**9), "hidden": True, "match": "tokens"},
    ],
    "wrong": [
        # Prints the list unchanged.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); values = [int(x) for x in data[1:1+n]]
print(n)
print(' '.join(map(str, values)))
""".lstrip(),
        # Loses the original head: the classic "prev starts at head" bug.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); values = [int(x) for x in data[1:1+n]]
out = values[:0:-1]
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
        # Sorts descending, which matches the sample but not an unsorted list.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); values = [int(x) for x in data[1:1+n]]
out = sorted(values, reverse=True)
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  02 · Detect a cycle in a linked list                                       #
# --------------------------------------------------------------------------- #

LINKED_LIST_CYCLE = {
    "slug": "linked-list-cycle-entry",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Detect Cycle in a Linked List",
    "statement": (
        "A cyclic list cannot be printed, so this problem ships the pointer "
        "table instead of the values. Node i has a single successor next[i], "
        "where -1 means null. Node 0 is the head.\n\n"
        "Allocate n nodes, link node i to node next[i], then start at the head "
        "and decide whether following the links ever revisits a node. Print "
        "the index of the first node that lies on the cycle — the node the "
        "walk arrives at twice — or -1 when the list ends at null.\n\n"
        "Your traversal must terminate on every input: a loop that simply "
        "follows next until it reaches -1 never returns on a cyclic list."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1 <= next[i] <= n - 1, and next[i] != i is not guaranteed",
        "Node 0 is the head; nodes unreachable from the head do not matter",
        "O(n) time is expected, and O(1) extra space is possible with two pointers",
    ],
    "input_format": (
        "Line 1: n, the number of nodes.\n"
        "Line 2: n space-separated integers, where the i-th is next[i] "
        "(-1 for null)."
    ),
    "output_format": (
        "A single integer: the index of the node where the cycle begins, or -1 "
        "if the list has no cycle."
    ),
    "examples": [
        {
            "stdin": "4\n1 2 3 1\n",
            "stdout": "1",
            "explanation": "0 -> 1 -> 2 -> 3 -> 1, so the walk re-enters the cycle at node 1.",
        },
        {
            "stdin": "3\n1 2 -1\n",
            "stdout": "-1",
            "explanation": "The chain 0 -> 1 -> 2 ends at null, so there is no cycle.",
        },
    ],
    "criteria": [
        "Terminate on cyclic input rather than looping forever",
        "Report the cycle entry index, not merely whether a cycle exists",
        "Handle a self-loop and a cycle that starts at the head",
    ],
    "io": {
        "mode": "tokens",
        "function": "cycle_entry",
        "todo": "return the index where the cycle begins, or -1 if the list has no cycle",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "next_index", "type": "int", "count": "n"},
        ],
        "args": ["next_index"],
        "returns": "int",
    },
    "reference": """
import sys


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    nxt = [int(x) for x in data[1:1 + n]]
    seen = [False] * n
    node = 0
    while node != -1 and not seen[node]:
        seen[node] = True
        node = nxt[node]
    print(node)


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: cycle at node 1", "stdin": "4\n1 2 3 1\n", "hidden": False},
        {"name": "sample: no cycle", "stdin": "3\n1 2 -1\n", "hidden": False},
        {"name": "hidden: single node null", "stdin": "1\n-1\n", "hidden": True},
        {"name": "hidden: self loop at head", "stdin": "1\n0\n", "hidden": True},
        {"name": "hidden: whole list is the cycle", "stdin": "5\n1 2 3 4 0\n", "hidden": True},
        {"name": "hidden: cycle at the tail only", "stdin": "3\n1 2 2\n", "hidden": True},
        # The last node is not on the walk in either of these, so answering with
        # next[n-1] is caught.
        {"name": "hidden: last node unreachable, cycle earlier", "stdin": "5\n1 2 3 1 -1\n", "hidden": True},
        {"name": "hidden: last node points back but the walk ends", "stdin": "4\n1 2 -1 0\n", "hidden": True},
        {"name": "hidden: scale with mid cycle", "stdin": _cycle_case(211, 200000, 100000), "hidden": True},
        {"name": "hidden: scale without cycle", "stdin": _cycle_case(212, 200000, None), "hidden": True},
    ],
    "wrong": [
        # Follows next until null: never terminates on a cyclic list.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); nxt = [int(x) for x in data[1:1+n]]
node = 0
while nxt[node] != -1:
    node = nxt[node]
print(-1)
""".lstrip(),
        # Answers the yes/no question instead of the entry index.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); nxt = [int(x) for x in data[1:1+n]]
seen = [False] * n
node = 0
while node != -1 and not seen[node]:
    seen[node] = True
    node = nxt[node]
print(1 if node != -1 else 0)
""".lstrip(),
        # Assumes the cycle is entered from the last node.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); nxt = [int(x) for x in data[1:1+n]]
print(nxt[n-1])
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  03 · Merge two sorted lists                                                #
# --------------------------------------------------------------------------- #

MERGE_TWO_LISTS = {
    "slug": "merge-two-sorted-lists",
    "skill_id": "dsa_arrays",
    "difficulty": 3,
    "estimated_minutes": 25,
    "title": "Merge Two Sorted Lists",
    "statement": (
        "Two singly linked lists are given, each sorted in non-decreasing "
        "order. Splice them into one sorted list and report it.\n\n"
        + _LIST_BUILD
        + "\n\nEvery node of both inputs appears in the output: equal values "
        "are kept, not collapsed."
    ),
    "constraints": [
        "0 <= n, m <= 100000",
        "-1000000000 <= value <= 1000000000",
        "Both input lists are already sorted in non-decreasing order",
        "Either list may be empty",
        "An O(n + m) merge is expected",
    ],
    "input_format": (
        "Line 1: n, the length of the first list.\n"
        "Line 2: the n values of the first list, head to tail.\n"
        "Line 3: m, the length of the second list.\n"
        "Line 4: the m values of the second list, head to tail.\n"
        "A length line of 0 is followed by an empty value line."
    ),
    "output_format": _SEQ_OUTPUT,
    "examples": [
        {
            "stdin": "3\n1 2 4\n3\n1 3 4\n",
            "stdout": "6\n1 1 2 3 4 4",
            "explanation": "Both 1s and both 4s survive: the merge keeps duplicates.",
        },
        {
            "stdin": "0\n\n2\n-5 7\n",
            "stdout": "2\n-5 7",
            "explanation": "The first list is empty, so the answer is the second list unchanged.",
        },
    ],
    "criteria": [
        "Keep duplicate values instead of deduplicating",
        "Append the remaining tail once one list is exhausted",
        "Handle either list being empty",
    ],
    "io": {
        "mode": "tokens",
        "function": "merge_two_lists",
        "todo": "merge the two lists, then print m and the merged values (replace the single-value print in main)",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "first", "type": "long", "count": "n"},
            {"name": "m", "type": "int"},
            {"name": "second", "type": "long", "count": "m"},
        ],
        "args": ["first", "second"],
        "returns": "int",
    },
    "reference": """
import sys


def main():
    data = sys.stdin.read().split()
    pos = 0
    n = int(data[pos]); pos += 1
    first = [int(x) for x in data[pos:pos + n]]; pos += n
    m = int(data[pos]); pos += 1
    second = [int(x) for x in data[pos:pos + m]]; pos += m
    out = []
    i = j = 0
    while i < n and j < m:
        if first[i] <= second[j]:
            out.append(first[i]); i += 1
        else:
            out.append(second[j]); j += 1
    out.extend(first[i:])
    out.extend(second[j:])
    print(len(out))
    print(' '.join(map(str, out)))


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: interleaved", "stdin": "3\n1 2 4\n3\n1 3 4\n", "hidden": False, "match": "tokens"},
        {"name": "sample: first empty", "stdin": "0\n\n2\n-5 7\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: both empty", "stdin": "0\n\n0\n\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: disjoint ranges", "stdin": "3\n1 2 3\n3\n8 9 10\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: all identical", "stdin": "3\n2 2 2\n2\n2 2\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: second empty", "stdin": "2\n4 6\n0\n\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: long tail on one side", "stdin": "1\n-1000000000\n4\n-5 0 5 1000000000\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: scale",
            "stdin": _two_sorted_lists_case(103, 100000, 100000),
            "hidden": True,
            "match": "tokens",
        },
    ],
    "wrong": [
        # Never appends the leftover tail of the longer list.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
a = [int(x) for x in data[pos:pos+n]]; pos += n
m = int(data[pos]); pos += 1
b = [int(x) for x in data[pos:pos+m]]; pos += m
out = []
i = j = 0
while i < n and j < m:
    if a[i] <= b[j]:
        out.append(a[i]); i += 1
    else:
        out.append(b[j]); j += 1
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
        # Deduplicates equal values.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
a = [int(x) for x in data[pos:pos+n]]; pos += n
m = int(data[pos]); pos += 1
b = [int(x) for x in data[pos:pos+m]]; pos += m
out = sorted(set(a) | set(b))
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
        # Concatenates without merging.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
a = [int(x) for x in data[pos:pos+n]]; pos += n
m = int(data[pos]); pos += 1
b = [int(x) for x in data[pos:pos+m]]; pos += m
out = a + b
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  04 · Merge k sorted lists                                                  #
# --------------------------------------------------------------------------- #

MERGE_K_LISTS = {
    "slug": "merge-k-sorted-lists",
    "skill_id": "dsa_arrays",
    "difficulty": 7,
    "estimated_minutes": 40,
    "title": "Merge K Sorted Lists",
    "statement": (
        "k singly linked lists are given, each sorted in non-decreasing "
        "order. Merge all of them into one sorted list and report it.\n\n"
        + _LIST_BUILD
        + "\n\nThe lists are flattened into a single token stream: each list "
        "contributes its length followed by that many values, and the header "
        "states how many integers follow so the stream can be split in any "
        "language, including C.\n\n"
        "Scanning every list head for each output node costs O(total * k) and "
        "will not finish the largest case; use a heap, or merge the lists "
        "pairwise in rounds."
    ),
    "constraints": [
        "1 <= k <= 1000",
        "0 <= total number of nodes <= 200000",
        "-1000000000 <= value <= 1000000000",
        "Each list is sorted in non-decreasing order and may be empty",
        "O(total log k) is expected; O(total * k) times out on the largest case",
    ],
    "input_format": (
        "Line 1: k and m separated by a space, where m is the number of "
        "integers that follow.\n"
        "Then m integers: for each of the k lists in turn, its length "
        "followed by its values, head to tail. The integers may be spread "
        "over any number of lines."
    ),
    "output_format": _SEQ_OUTPUT,
    "examples": [
        {
            "stdin": "3 9\n3 1 4 5\n0\n3 1 3 4\n",
            "stdout": "6\n1 1 3 4 4 5",
            "explanation": (
                "The three lists are [1,4,5], [] and [1,3,4]; m = 9 counts the three "
                "length tokens plus the six values."
            ),
        },
        {
            "stdin": "2 4\n1 -8\n1 -8\n",
            "stdout": "2\n-8 -8",
            "explanation": "Two single-node lists holding equal values; both nodes appear.",
        },
    ],
    "criteria": [
        "Handle empty lists, including every list being empty",
        "Keep duplicates across lists",
        "Beat O(total * k): the scale case rejects repeated scanning of all heads",
    ],
    "io": {
        "mode": "tokens",
        "function": "merge_k_lists",
        "todo": "split the stream into k lists, merge them, then print m and the merged values (replace the single-value print in main)",
        "reads": [
            {"name": "k", "type": "int"},
            {"name": "m", "type": "int"},
            {"name": "stream", "type": "long", "count": "m"},
        ],
        "args": ["stream", "k"],
        "returns": "int",
    },
    "reference": """
import sys
import heapq


def main():
    data = sys.stdin.read().split()
    k = int(data[0])
    m = int(data[1])
    stream = [int(x) for x in data[2:2 + m]]
    lists = []
    pos = 0
    for _ in range(k):
        size = stream[pos]; pos += 1
        lists.append(stream[pos:pos + size]); pos += size
    out = list(heapq.merge(*lists))
    print(len(out))
    print(' '.join(map(str, out)))


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: three lists", "stdin": "3 9\n3 1 4 5\n0\n3 1 3 4\n", "hidden": False, "match": "tokens"},
        {"name": "sample: equal singletons", "stdin": "2 4\n1 -8\n1 -8\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: every list empty", "stdin": "3 3\n0 0 0\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: single list", "stdin": "1 4\n3 -1 0 1\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: all identical values", "stdin": "3 9\n2 7 7\n2 7 7\n2 7 7\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: blocks that must interleave",
            "stdin": "3 12\n3 1 2 3\n3 4 5 6\n3 0 7 8\n",
            "hidden": True,
            "match": "tokens",
        },
        {"name": "hidden: extremes", "stdin": "2 6\n2 -1000000000 1000000000\n2 0 0\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: scale",
            "stdin": _k_lists_case(107, 1000, 200000),
            "hidden": True,
            "match": "tokens",
        },
    ],
    "wrong": [
        # Concatenates the lists without merging them.
        """
import sys
data = sys.stdin.read().split()
k = int(data[0]); m = int(data[1])
stream = [int(x) for x in data[2:2+m]]
out = []
pos = 0
for _ in range(k):
    size = stream[pos]; pos += 1
    out.extend(stream[pos:pos+size]); pos += size
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
        # Correct, but rescans all k heads per output node: O(total * k).
        """
import sys
data = sys.stdin.read().split()
k = int(data[0]); m = int(data[1])
stream = [int(x) for x in data[2:2+m]]
lists = []
pos = 0
for _ in range(k):
    size = stream[pos]; pos += 1
    lists.append(stream[pos:pos+size]); pos += size
heads = [0] * k
out = []
total = sum(len(x) for x in lists)
for _ in range(total):
    best = -1
    for i in range(k):
        if heads[i] < len(lists[i]) and (best == -1 or lists[i][heads[i]] < lists[best][heads[best]]):
            best = i
    out.append(lists[best][heads[best]])
    heads[best] += 1
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
        # Sorts inside each list but concatenates the lists in input order.
        """
import sys
data = sys.stdin.read().split()
k = int(data[0]); m = int(data[1])
stream = [int(x) for x in data[2:2+m]]
out = []
pos = 0
for _ in range(k):
    size = stream[pos]; pos += 1
    out.extend(sorted(stream[pos:pos+size])); pos += size
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  05 · Remove the nth node from the end                                      #
# --------------------------------------------------------------------------- #

REMOVE_NTH_FROM_END = {
    "slug": "remove-nth-from-end",
    "skill_id": "dsa_arrays",
    "difficulty": 4,
    "estimated_minutes": 25,
    "title": "Remove Nth Node From End of List",
    "statement": (
        "Remove the k-th node counted from the end of a singly linked list "
        "(k = 1 is the last node) and report the list that remains.\n\n"
        + _LIST_BUILD
        + "\n\nk = n removes the head, so the node you delete may have no "
        "predecessor. The intended solution keeps two pointers k apart and "
        "makes a single pass."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "1 <= k <= n",
        "-1000000000 <= value <= 1000000000",
        "One pass is expected; the answer has exactly n - 1 nodes",
    ],
    "input_format": _LIST_INPUT + "\nLine 3: k.",
    "output_format": _SEQ_OUTPUT,
    "examples": [
        {
            "stdin": "5\n1 2 3 4 5\n2\n",
            "stdout": "4\n1 2 3 5",
            "explanation": "The 2nd node from the end is the value 4, so it is removed.",
        },
        {
            "stdin": "3\n7 8 9\n3\n",
            "stdout": "2\n8 9",
            "explanation": "k equals n, so the head is deleted and the new head is 8.",
        },
    ],
    "criteria": [
        "Delete the head correctly when k = n",
        "Delete the tail correctly when k = 1",
        "Handle n = 1, where the result is the empty list",
    ],
    "io": {
        "mode": "tokens",
        "function": "remove_nth_from_end",
        "todo": "delete the k-th node from the end, then print m and the remaining values (replace the single-value print in main)",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "values", "type": "long", "count": "n"},
            {"name": "k", "type": "int"},
        ],
        "args": ["values", "k"],
        "returns": "int",
    },
    "reference": """
import sys


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    k = int(data[1 + n])
    target = n - k
    out = [v for i, v in enumerate(values) if i != target]
    print(len(out))
    print(' '.join(map(str, out)))


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: middle node", "stdin": "5\n1 2 3 4 5\n2\n", "hidden": False, "match": "tokens"},
        {"name": "sample: remove head", "stdin": "3\n7 8 9\n3\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: single node", "stdin": "1\n42\n1\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: remove tail", "stdin": "4\n1 2 3 4\n1\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: two nodes remove head", "stdin": "2\n5 6\n2\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: all identical", "stdin": "4\n3 3 3 3\n3\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: scale",
            "stdin": _list_case(109, 200000, -10**9, 10**9).rstrip("\n") + "\n99999\n",
            "hidden": True,
            "match": "tokens",
        },
    ],
    "wrong": [
        # Counts from the front instead of from the end.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); values = [int(x) for x in data[1:1+n]]
k = int(data[1+n])
out = [v for i, v in enumerate(values) if i != k - 1]
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
        # Off by one from the end: deletes n - k - 1.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); values = [int(x) for x in data[1:1+n]]
k = int(data[1+n])
target = n - k - 1
out = [v for i, v in enumerate(values) if i != target]
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
        # Two-pointer walk that cannot delete the head, so it drops the wrong node.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); values = [int(x) for x in data[1:1+n]]
k = int(data[1+n])
target = n - k
if target == 0:
    target = 1
out = [v for i, v in enumerate(values) if i != target]
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  06 · Reorder list                                                          #
# --------------------------------------------------------------------------- #

REORDER_LIST = {
    "slug": "reorder-linked-list",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 35,
    "title": "Reorder List",
    "statement": (
        "Reorder a singly linked list L0, L1, ..., Ln-1 into\n"
        "L0, Ln-1, L1, Ln-2, L2, ... — the first node, then the last, then "
        "the second, then the second to last, and so on.\n\n"
        + _LIST_BUILD
        + "\n\nEvery node appears exactly once, so an odd-length list keeps "
        "its middle node in the middle. The intended solution finds the "
        "midpoint, reverses the second half and interleaves the two halves in "
        "O(n) time."
    ),
    "constraints": [
        "0 <= n <= 200000",
        "-1000000000 <= value <= 1000000000",
        "The output has exactly n values: no node is duplicated or dropped",
        "O(n) time is expected",
    ],
    "input_format": _LIST_INPUT,
    "output_format": _SEQ_OUTPUT,
    "examples": [
        {
            "stdin": "4\n1 2 3 4\n",
            "stdout": "4\n1 4 2 3",
            "explanation": "Taking from the front and the back alternately: 1, 4, 2, 3.",
        },
        {
            "stdin": "5\n1 2 3 4 5\n",
            "stdout": "5\n1 5 2 4 3",
            "explanation": "Odd length: the middle value 3 is emitted once, at the end.",
        },
    ],
    "criteria": [
        "Emit each node exactly once, including the middle of an odd-length list",
        "Handle n = 0, 1 and 2",
        "Run in O(n) time rather than repeatedly walking to the tail",
    ],
    "io": {
        "mode": "tokens",
        "function": "reorder_list",
        "todo": "reorder the list front-to-back alternately, then print m and the values (replace the single-value print in main)",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "values", "type": "long", "count": "n"},
        ],
        "args": ["values"],
        "returns": "int",
    },
    "reference": """
import sys


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    values = [int(x) for x in data[1:1 + n]]
    out = []
    left, right = 0, n - 1
    while left < right:
        out.append(values[left])
        out.append(values[right])
        left += 1
        right -= 1
    if left == right:
        out.append(values[left])
    print(len(out))
    print(' '.join(map(str, out)))


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: even length", "stdin": "4\n1 2 3 4\n", "hidden": False, "match": "tokens"},
        {"name": "sample: odd length", "stdin": "5\n1 2 3 4 5\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: empty list", "stdin": "0\n\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: single node", "stdin": "1\n-4\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: two nodes", "stdin": "2\n1 2\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: three nodes", "stdin": "3\n1 2 3\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: all identical", "stdin": "5\n6 6 6 6 6\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: scale", "stdin": _list_case(113, 200000, -10**9, 10**9), "hidden": True, "match": "tokens"},
    ],
    "wrong": [
        # Splits at n // 2 and reverses, duplicating the middle on odd lengths.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); values = [int(x) for x in data[1:1+n]]
half = n // 2
first = values[:half + (n % 2)]
second = values[half:][::-1]
out = []
for i in range(max(len(first), len(second))):
    if i < len(first):
        out.append(first[i])
    if i < len(second):
        out.append(second[i])
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
        # Interleaves with the second half in its original order.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); values = [int(x) for x in data[1:1+n]]
half = (n + 1) // 2
first = values[:half]
second = values[half:]
out = []
for i in range(half):
    out.append(first[i])
    if i < len(second):
        out.append(second[i])
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
        # Just reverses the list.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); values = [int(x) for x in data[1:1+n]]
out = values[::-1]
print(len(out))
print(' '.join(map(str, out)))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  07 · Insert interval                                                       #
# --------------------------------------------------------------------------- #

_INTERVAL_INPUT = (
    "Line 1: n, the number of intervals.\n"
    "Line 2: the n start values.\n"
    "Line 3: the n end values, where end[i] belongs to start[i].\n"
    "A count of 0 is followed by two empty lines."
)

INSERT_INTERVAL = {
    "slug": "insert-interval",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Insert Interval",
    "statement": (
        "You are given n closed intervals, already sorted by start and "
        "pairwise non-overlapping, plus one new interval. Insert the new "
        "interval and merge whatever it touches, then report the resulting "
        "set.\n\n"
        "Intervals are closed: [1, 3] and [3, 6] share the point 3 and "
        "therefore merge into [1, 6].\n\n"
        "Print the answer sorted by increasing start; that order is part of "
        "the specification, so any other order is wrong."
    ),
    "constraints": [
        "0 <= n <= 200000",
        "0 <= start[i] <= end[i] <= 1000000000",
        "The given intervals are sorted by start and do not overlap each other",
        "0 <= s <= e <= 1000000000 for the new interval",
        "O(n) is expected: one pass, no re-sorting",
    ],
    "input_format": _INTERVAL_INPUT + "\nLine 4: s and e, the new interval.",
    "output_format": _PAIR_OUTPUT,
    "examples": [
        {
            "stdin": "2\n1 6\n3 9\n2 5\n",
            "stdout": "2\n1 5\n6 9",
            "explanation": "The new interval [2,5] overlaps [1,3], which grows to [1,5]; [6,9] starts after 5 and is untouched.",
        },
        {
            "stdin": "2\n1 5\n2 7\n8 9\n",
            "stdout": "3\n1 2\n5 7\n8 9",
            "explanation": "The new interval [8,9] lies after every existing one, so it is appended.",
        },
    ],
    "criteria": [
        "Merge intervals that only touch at an endpoint",
        "Insert correctly when the new interval is before all, after all, or covers all",
        "Handle n = 0",
    ],
    "io": {
        "mode": "tokens",
        "function": "insert_interval",
        "todo": "insert and merge the new interval, then print m and the m resulting intervals (replace the single-value print in main)",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "starts", "type": "long", "count": "n"},
            {"name": "ends", "type": "long", "count": "n"},
            {"name": "s", "type": "long"},
            {"name": "e", "type": "long"},
        ],
        "args": ["starts", "ends", "s", "e"],
        "returns": "int",
    },
    "reference": """
import sys


def main():
    data = sys.stdin.read().split()
    pos = 0
    n = int(data[pos]); pos += 1
    starts = [int(x) for x in data[pos:pos + n]]; pos += n
    ends = [int(x) for x in data[pos:pos + n]]; pos += n
    s = int(data[pos]); pos += 1
    e = int(data[pos]); pos += 1
    out = []
    i = 0
    while i < n and ends[i] < s:
        out.append((starts[i], ends[i]))
        i += 1
    while i < n and starts[i] <= e:
        s = min(s, starts[i])
        e = max(e, ends[i])
        i += 1
    out.append((s, e))
    while i < n:
        out.append((starts[i], ends[i]))
        i += 1
    lines = [str(len(out))]
    for a, b in out:
        lines.append(str(a) + ' ' + str(b))
    print('\\n'.join(lines))


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: merges a run", "stdin": "2\n1 6\n3 9\n2 5\n", "hidden": False, "match": "tokens"},
        {"name": "sample: appended at the end", "stdin": "2\n1 5\n2 7\n8 9\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: no intervals", "stdin": "0\n\n\n4 6\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: touching endpoints only", "stdin": "2\n1 4\n2 6\n4 4\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: before everything", "stdin": "2\n5 9\n6 10\n0 1\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: swallows all", "stdin": "3\n1 4 7\n2 5 8\n0 100\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: zero-length new interval inside a gap", "stdin": "2\n1 10\n3 12\n11 11\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: scale",
            "stdin": (
                "200000\n"
                + " ".join(str(i * 10) for i in range(200000))
                + "\n"
                + " ".join(str(i * 10 + 4) for i in range(200000))
                + "\n5 1999000\n"
            ),
            "hidden": True,
            "match": "tokens",
        },
    ],
    "wrong": [
        # Strict comparisons, so intervals that merely touch are not merged.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
s = int(data[pos]); pos += 1
e = int(data[pos]); pos += 1
out = []
i = 0
while i < n and ends[i] <= s:
    out.append((starts[i], ends[i])); i += 1
while i < n and starts[i] < e:
    s = min(s, starts[i]); e = max(e, ends[i]); i += 1
out.append((s, e))
while i < n:
    out.append((starts[i], ends[i])); i += 1
print(len(out))
for a, b in out:
    print(a, b)
""".lstrip(),
        # Appends the new interval and sorts, but never merges.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
s = int(data[pos]); pos += 1
e = int(data[pos]); pos += 1
out = sorted(list(zip(starts, ends)) + [(s, e)])
print(len(out))
for a, b in out:
    print(a, b)
""".lstrip(),
        # Drops the new interval when it overlaps nothing.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
s = int(data[pos]); pos += 1
e = int(data[pos]); pos += 1
out = []
merged = False
for i in range(n):
    if starts[i] <= e and ends[i] >= s:
        s = min(s, starts[i]); e = max(e, ends[i]); merged = True
    elif ends[i] < s:
        out.append((starts[i], ends[i]))
    else:
        if merged:
            out.append((s, e)); merged = False
        out.append((starts[i], ends[i]))
if merged:
    out.append((s, e))
out.sort()
print(len(out))
for a, b in out:
    print(a, b)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  08 · Merge intervals                                                       #
# --------------------------------------------------------------------------- #

MERGE_INTERVALS = {
    "slug": "merge-intervals",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Merge Intervals",
    "statement": (
        "Given n closed intervals in arbitrary order, merge every group that "
        "overlaps and report the resulting set.\n\n"
        "Intervals are closed, so [1, 4] and [4, 5] merge into [1, 5]. One "
        "interval may sit entirely inside another.\n\n"
        "Print the answer sorted by increasing start; that order is part of "
        "the specification."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "0 <= start[i] <= end[i] <= 1000000000",
        "The input is not sorted",
        "O(n log n) is expected",
    ],
    "input_format": _INTERVAL_INPUT,
    "output_format": _PAIR_OUTPUT,
    "examples": [
        {
            "stdin": "4\n1 2 8 15\n3 6 10 18\n",
            "stdout": "3\n1 6\n8 10\n15 18",
            "explanation": "[1,3] and [2,6] overlap and merge; the other two are separate.",
        },
        {
            "stdin": "2\n1 4\n4 5\n",
            "stdout": "1\n1 5",
            "explanation": "The intervals touch at 4, and closed intervals that touch are merged.",
        },
    ],
    "criteria": [
        "Sort first: the input order is arbitrary",
        "Merge intervals that only touch at an endpoint",
        "Keep an interval nested inside another from shrinking the merged end",
    ],
    "io": {
        "mode": "tokens",
        "function": "merge_intervals",
        "todo": "merge the overlapping intervals, then print m and the m merged intervals (replace the single-value print in main)",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "starts", "type": "long", "count": "n"},
            {"name": "ends", "type": "long", "count": "n"},
        ],
        "args": ["starts", "ends"],
        "returns": "int",
    },
    "reference": """
import sys


def main():
    data = sys.stdin.read().split()
    pos = 0
    n = int(data[pos]); pos += 1
    starts = [int(x) for x in data[pos:pos + n]]; pos += n
    ends = [int(x) for x in data[pos:pos + n]]; pos += n
    pairs = sorted(zip(starts, ends))
    out = []
    for start, end in pairs:
        if out and start <= out[-1][1]:
            if end > out[-1][1]:
                out[-1] = (out[-1][0], end)
        else:
            out.append((start, end))
    lines = [str(len(out))]
    for a, b in out:
        lines.append(str(a) + ' ' + str(b))
    print('\\n'.join(lines))


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: one merge", "stdin": "4\n1 2 8 15\n3 6 10 18\n", "hidden": False, "match": "tokens"},
        {"name": "sample: touching", "stdin": "2\n1 4\n4 5\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: single interval", "stdin": "1\n7\n7\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: nested interval", "stdin": "2\n1 2\n10 3\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: unsorted input", "stdin": "3\n9 1 5\n12 3 7\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: all identical", "stdin": "4\n2 2 2 2\n5 5 5 5\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: chain of touches", "stdin": "4\n1 2 3 4\n2 3 4 5\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: scale",
            "stdin": _intervals_case(127, 200000, 10**9, 3000),
            "hidden": True,
            "match": "tokens",
        },
    ],
    "wrong": [
        # Assumes the input is already sorted by start.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
out = []
for start, end in zip(starts, ends):
    if out and start <= out[-1][1]:
        out[-1] = (out[-1][0], max(out[-1][1], end))
    else:
        out.append((start, end))
print(len(out))
for a, b in out:
    print(a, b)
""".lstrip(),
        # Uses a strict comparison, so touching intervals are not merged.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
pairs = sorted(zip(starts, ends))
out = []
for start, end in pairs:
    if out and start < out[-1][1]:
        out[-1] = (out[-1][0], max(out[-1][1], end))
    else:
        out.append((start, end))
print(len(out))
for a, b in out:
    print(a, b)
""".lstrip(),
        # Overwrites the running end, so a nested interval shrinks the merge.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
pairs = sorted(zip(starts, ends))
out = []
for start, end in pairs:
    if out and start <= out[-1][1]:
        out[-1] = (out[-1][0], end)
    else:
        out.append((start, end))
print(len(out))
for a, b in out:
    print(a, b)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  09 · Non-overlapping intervals                                             #
# --------------------------------------------------------------------------- #

NON_OVERLAPPING = {
    "slug": "min-intervals-to-remove",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 35,
    "title": "Non-overlapping Intervals",
    "statement": (
        "Given n intervals, remove as few of them as possible so that none of "
        "the survivors overlap. Report how many you removed.\n\n"
        "Intervals are half-open here: [1, 2] and [2, 3] do not overlap, "
        "because the first ends exactly where the second begins.\n\n"
        "The greedy that works keeps the interval with the earliest end "
        "whenever there is a conflict; keeping the earliest start instead is "
        "a tempting rule that gives the wrong answer."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= start[i] <= end[i] <= 1000000000",
        "The input is not sorted",
        "O(n log n) is expected",
    ],
    "input_format": _INTERVAL_INPUT,
    "output_format": "A single integer: the minimum number of intervals to remove.",
    "examples": [
        {
            "stdin": "4\n1 2 3 1\n2 3 4 3\n",
            "stdout": "1",
            "explanation": "Removing [1,3] leaves [1,2], [2,3] and [3,4], which only touch.",
        },
        {
            "stdin": "3\n1 1 1\n2 2 2\n",
            "stdout": "2",
            "explanation": "Three copies of the same interval: keep one, remove two.",
        },
    ],
    "criteria": [
        "Treat touching endpoints as non-overlapping",
        "Use the earliest-end greedy, not the earliest-start one",
        "Handle n = 1 and intervals that are all identical",
    ],
    "io": {
        "mode": "tokens",
        "function": "min_intervals_to_remove",
        "todo": "return the minimum number of intervals to remove so none overlap",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "starts", "type": "long", "count": "n"},
            {"name": "ends", "type": "long", "count": "n"},
        ],
        "args": ["starts", "ends"],
        "returns": "int",
    },
    "reference": """
import sys


def main():
    data = sys.stdin.read().split()
    pos = 0
    n = int(data[pos]); pos += 1
    starts = [int(x) for x in data[pos:pos + n]]; pos += n
    ends = [int(x) for x in data[pos:pos + n]]; pos += n
    pairs = sorted(zip(ends, starts))
    kept = 0
    last_end = None
    for end, start in pairs:
        if last_end is None or start >= last_end:
            kept += 1
            last_end = end
    print(n - kept)


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: one removal", "stdin": "4\n1 2 3 1\n2 3 4 3\n", "hidden": False},
        {"name": "sample: identical intervals", "stdin": "3\n1 1 1\n2 2 2\n", "hidden": False},
        {"name": "hidden: single interval", "stdin": "1\n5\n9\n", "hidden": True},
        {"name": "hidden: already disjoint", "stdin": "3\n1 10 20\n5 15 25\n", "hidden": True},
        {"name": "hidden: earliest-start greedy fails", "stdin": "3\n1 2 3\n100 3 4\n", "hidden": True},
        {"name": "hidden: touching chain", "stdin": "4\n0 1 2 3\n1 2 3 4\n", "hidden": True},
        {"name": "hidden: negative coordinates", "stdin": "3\n-10 -5 -1\n-6 0 3\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": _intervals_case(131, 200000, 10**9, 4000),
            "hidden": True,
        },
    ],
    "wrong": [
        # Greedy on start instead of end.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
pairs = sorted(zip(starts, ends))
kept = 0
last_end = None
for start, end in pairs:
    if last_end is None or start >= last_end:
        kept += 1
        last_end = end
print(n - kept)
""".lstrip(),
        # Treats touching endpoints as an overlap.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
pairs = sorted(zip(ends, starts))
kept = 0
last_end = None
for end, start in pairs:
    if last_end is None or start > last_end:
        kept += 1
        last_end = end
print(n - kept)
""".lstrip(),
        # Counts intervals that overlap their predecessor by start order.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
pairs = sorted(zip(starts, ends))
removed = 0
for i in range(1, n):
    if pairs[i][0] < pairs[i-1][1]:
        removed += 1
print(removed)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  10 · Meeting rooms (can one person attend all?)                            #
# --------------------------------------------------------------------------- #

CAN_ATTEND_ALL = {
    "slug": "can-attend-all-meetings",
    "skill_id": "dsa_arrays",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Meeting Rooms",
    "statement": (
        "One person has n meetings in their calendar. Decide whether they can "
        "attend every one of them, that is, whether no two meetings "
        "overlap.\n\n"
        "Meetings are half-open: a meeting ending at 10 and another starting "
        "at 10 are attendable, because the first is over when the second "
        "begins.\n\n"
        "Print 1 if every meeting can be attended and 0 otherwise. The "
        "calendar is not sorted, and comparing every pair is too slow for the "
        "largest input."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "0 <= start[i] <= end[i] <= 1000000000",
        "The input is not sorted",
        "O(n log n) is expected; an O(n^2) pairwise check times out",
    ],
    "input_format": _INTERVAL_INPUT,
    "output_format": "A single integer: 1 if all meetings can be attended, otherwise 0.",
    "examples": [
        {
            "stdin": "3\n0 5 15\n30 10 20\n",
            "stdout": "0",
            "explanation": "[0,30] overlaps [5,10], so the person cannot attend both.",
        },
        {
            "stdin": "2\n7 13\n13 20\n",
            "stdout": "1",
            "explanation": "The first ends exactly when the second starts, which is allowed.",
        },
    ],
    "criteria": [
        "Treat touching endpoints as attendable",
        "Sort the calendar first: the input order is arbitrary",
        "Avoid the O(n^2) pairwise comparison",
    ],
    "io": {
        "mode": "tokens",
        "function": "can_attend_all",
        "todo": "return 1 if no two meetings overlap, otherwise 0",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "starts", "type": "long", "count": "n"},
            {"name": "ends", "type": "long", "count": "n"},
        ],
        "args": ["starts", "ends"],
        "returns": "int",
    },
    "reference": """
import sys


def main():
    data = sys.stdin.read().split()
    pos = 0
    n = int(data[pos]); pos += 1
    starts = [int(x) for x in data[pos:pos + n]]; pos += n
    ends = [int(x) for x in data[pos:pos + n]]; pos += n
    pairs = sorted(zip(starts, ends))
    for i in range(1, n):
        if pairs[i][0] < pairs[i - 1][1]:
            print(0)
            return
    print(1)


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: overlapping", "stdin": "3\n0 5 15\n30 10 20\n", "hidden": False},
        {"name": "sample: touching", "stdin": "2\n7 13\n13 20\n", "hidden": False},
        {"name": "hidden: single meeting", "stdin": "1\n0\n1000000000\n", "hidden": True},
        {"name": "hidden: unsorted but attendable", "stdin": "3\n20 0 10\n25 5 15\n", "hidden": True},
        {"name": "hidden: unsorted and overlapping", "stdin": "3\n20 0 12\n25 5 22\n", "hidden": True},
        {"name": "hidden: identical meetings", "stdin": "2\n4 4\n9 9\n", "hidden": True},
        {"name": "hidden: zero-length meeting inside another", "stdin": "2\n1 3\n10 3\n", "hidden": True},
        {
            "name": "hidden: scale, all disjoint",
            "stdin": _disjoint_intervals_case(137, 200000),
            "hidden": True,
        },
        {
            "name": "hidden: scale, heavy overlap",
            "stdin": _intervals_case(139, 200000, 10**9, 5000),
            "hidden": True,
        },
    ],
    "wrong": [
        # Rejects meetings that merely touch.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
pairs = sorted(zip(starts, ends))
ok = 1
for i in range(1, n):
    if pairs[i][0] <= pairs[i-1][1]:
        ok = 0
print(ok)
""".lstrip(),
        # Assumes the calendar arrives sorted.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
ok = 1
for i in range(1, n):
    if starts[i] < ends[i-1]:
        ok = 0
print(ok)
""".lstrip(),
        # Correct but quadratic: cannot finish the disjoint scale case.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
ok = 1
for i in range(n):
    for j in range(i + 1, n):
        if starts[i] < ends[j] and starts[j] < ends[i]:
            ok = 0
            break
    if ok == 0:
        break
print(ok)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  11 · Meeting rooms II                                                      #
# --------------------------------------------------------------------------- #
# Deliberately distinct from the existing `min-platforms`: meetings are
# half-open (a room frees at the instant a meeting ends, so [1,2] and [2,3]
# share one room) whereas platforms are closed (a train departing at the minute
# another arrives still blocks the platform). The two problems disagree on
# every touching-endpoint case, which is exactly the edge this one drills.

MIN_MEETING_ROOMS = {
    "slug": "min-meeting-rooms",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 35,
    "title": "Meeting Rooms II",
    "statement": (
        "n meetings must be scheduled into rooms. A room holds one meeting at "
        "a time. Find the smallest number of rooms that lets every meeting "
        "happen at its stated time.\n\n"
        "Meetings are half-open: a room is free again at the instant its "
        "meeting ends, so a meeting [1, 2] and a meeting [2, 3] can share one "
        "room. (This is what separates the problem from the platform variant, "
        "where a departure at the same minute still blocks the platform.)\n\n"
        "Equivalently: report the largest number of meetings that are running "
        "at the same instant."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "0 <= start[i] <= end[i] <= 1000000000",
        "The input is not sorted",
        "A meeting ending at time t frees its room for a meeting starting at t",
        "O(n log n) is expected; an O(n^2) sweep times out",
    ],
    "input_format": _INTERVAL_INPUT,
    "output_format": "A single integer: the minimum number of rooms required.",
    "examples": [
        {
            "stdin": "3\n0 5 15\n30 10 20\n",
            "stdout": "2",
            "explanation": "[0,30] runs alongside [5,10] and later alongside [15,20], never three at once.",
        },
        {
            "stdin": "3\n1 2 3\n2 3 4\n",
            "stdout": "1",
            "explanation": "Each meeting ends exactly when the next begins, so one room suffices.",
        },
    ],
    "criteria": [
        "Free the room at the end instant, so touching meetings share a room",
        "Do not assume the input is sorted",
        "Use an O(n log n) sweep rather than comparing every pair",
    ],
    "io": {
        "mode": "tokens",
        "function": "min_meeting_rooms",
        "todo": "return the minimum number of rooms required",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "starts", "type": "long", "count": "n"},
            {"name": "ends", "type": "long", "count": "n"},
        ],
        "args": ["starts", "ends"],
        "returns": "int",
    },
    "reference": """
import sys


def main():
    data = sys.stdin.read().split()
    pos = 0
    n = int(data[pos]); pos += 1
    starts = sorted(int(x) for x in data[pos:pos + n]); pos += n
    ends = sorted(int(x) for x in data[pos:pos + n]); pos += n
    i = j = 0
    current = best = 0
    while i < n and j < n:
        if starts[i] < ends[j]:
            current += 1
            if current > best:
                best = current
            i += 1
        else:
            current -= 1
            j += 1
    print(best)


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: two rooms", "stdin": "3\n0 5 15\n30 10 20\n", "hidden": False},
        {"name": "sample: touching meetings", "stdin": "3\n1 2 3\n2 3 4\n", "hidden": False},
        {"name": "hidden: single meeting", "stdin": "1\n3\n9\n", "hidden": True},
        {"name": "hidden: all identical", "stdin": "5\n0 0 0 0 0\n1 1 1 1 1\n", "hidden": True},
        {"name": "hidden: unsorted nesting", "stdin": "4\n30 0 10 20\n40 100 15 25\n", "hidden": True},
        {"name": "hidden: zero-length meeting beside a real one", "stdin": "2\n5 5\n5 9\n", "hidden": True},
        {"name": "hidden: chain of touches", "stdin": "4\n0 10 20 30\n10 20 30 40\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": _intervals_case(149, 200000, 1400000, 5000),
            "hidden": True,
        },
    ],
    "wrong": [
        # Closed-interval semantics: the platform rule, wrong for meetings.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = sorted(int(x) for x in data[pos:pos+n]); pos += n
ends = sorted(int(x) for x in data[pos:pos+n]); pos += n
i = j = 0
cur = best = 0
while i < n:
    if starts[i] <= ends[j]:
        cur += 1
        best = max(best, cur)
        i += 1
    else:
        cur -= 1
        j += 1
print(best)
""".lstrip(),
        # Counts overlaps against the input order instead of sorting.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
i = j = 0
cur = best = 0
while i < n:
    if starts[i] < ends[j]:
        cur += 1
        best = max(best, cur)
        i += 1
    else:
        cur -= 1
        j += 1
print(best)
""".lstrip(),
        # Correct but quadratic: times out on the scale case.
        """
import sys
data = sys.stdin.read().split()
pos = 0
n = int(data[pos]); pos += 1
starts = [int(x) for x in data[pos:pos+n]]; pos += n
ends = [int(x) for x in data[pos:pos+n]]; pos += n
best = 0
for i in range(n):
    cur = 0
    for j in range(n):
        if starts[j] <= starts[i] < ends[j]:
            cur += 1
    best = max(best, cur)
print(best)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  12 · Koko eating bananas (binary search on the answer)                     #
# --------------------------------------------------------------------------- #

KOKO = {
    "slug": "koko-eating-bananas",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 35,
    "title": "Koko Eating Bananas (Binary Search on the Answer)",
    "statement": (
        "There are n piles of bananas and h hours before the guards return. "
        "Choosing an eating speed of k bananas per hour, each hour Koko picks "
        "one pile and eats k bananas from it; if the pile holds fewer than k, "
        "she eats the whole pile and still spends the full hour on it. So a "
        "pile of size p costs ceil(p / k) hours.\n\n"
        "Find the smallest integer speed k that finishes every pile within h "
        "hours.\n\n"
        "The answer is not found by scanning speeds upwards — it can be as "
        "large as 10^9. Binary search on the speed: the predicate 'k hours "
        "suffice' is monotone, so the search space halves each step."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "n <= h <= 1000000000",
        "1 <= piles[i] <= 1000000000",
        "The total number of bananas reaches 2 * 10^14, so accumulate hours in "
        "long long (C/C++) or long (Java)",
        "O(n log(max pile)) is expected; scanning k from 1 upwards times out",
    ],
    "input_format": (
        "Line 1: n and h separated by a space.\nLine 2: n pile sizes."
    ),
    "output_format": "A single integer: the minimum eating speed.",
    "examples": [
        {
            "stdin": "4 8\n3 6 7 11\n",
            "stdout": "4",
            "explanation": "At k = 4 the piles cost 1 + 2 + 2 + 3 = 8 hours; k = 3 needs 10.",
        },
        {
            "stdin": "3 3\n30 11 23\n",
            "stdout": "30",
            "explanation": "With one hour per pile the speed must cover the largest pile.",
        },
    ],
    "criteria": [
        "Round hours up: a partial pile still costs a whole hour",
        "Search the whole range up to the largest pile",
        "Use binary search rather than a linear scan over speeds",
    ],
    "io": {
        "mode": "tokens",
        "function": "min_eating_speed",
        "todo": "return the smallest eating speed that clears every pile within h hours",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "h", "type": "long"},
            {"name": "piles", "type": "long", "count": "n"},
        ],
        "args": ["piles", "h"],
        "returns": "long",
    },
    "reference": """
import sys


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    h = int(data[1])
    piles = [int(x) for x in data[2:2 + n]]
    lo, hi = 1, max(piles)
    while lo < hi:
        mid = (lo + hi) // 2
        hours = 0
        for p in piles:
            hours += (p + mid - 1) // mid
            if hours > h:
                break
        if hours <= h:
            hi = mid
        else:
            lo = mid + 1
    print(lo)


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: eight hours", "stdin": "4 8\n3 6 7 11\n", "hidden": False},
        {"name": "sample: one hour per pile", "stdin": "3 3\n30 11 23\n", "hidden": False},
        {"name": "hidden: single pile, ample time", "stdin": "1 1000000000\n1000000000\n", "hidden": True},
        # The pile is not exactly 10^9: a hidden expected output that also
        # appears in the constraints text would leak through the payload check.
        {"name": "hidden: single pile, one hour", "stdin": "1 1\n999999937\n", "hidden": True},
        {"name": "hidden: all identical piles", "stdin": "4 4\n5 5 5 5\n", "hidden": True},
        {"name": "hidden: exact division boundary", "stdin": "2 4\n8 8\n", "hidden": True},
        {"name": "hidden: unit piles", "stdin": "5 5\n1 1 1 1 1\n", "hidden": True},
        {
            "name": "hidden: scale, answer is the max pile",
            "stdin": _koko_case(151, 200000, 200000, 10**9),
            "hidden": True,
        },
        {
            "name": "hidden: scale, generous hours",
            "stdin": _koko_case(157, 200000, 1000000000, 10**9),
            "hidden": True,
        },
    ],
    "wrong": [
        # Upper bound from the average rather than the largest pile.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); h = int(data[1])
piles = [int(x) for x in data[2:2+n]]
lo, hi = 1, sum(piles) // h + 1
while lo < hi:
    mid = (lo + hi) // 2
    hours = sum((p + mid - 1) // mid for p in piles)
    if hours <= h:
        hi = mid
    else:
        lo = mid + 1
print(lo)
""".lstrip(),
        # Floor division: forgets that a partial pile costs a whole hour.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); h = int(data[1])
piles = [int(x) for x in data[2:2+n]]
lo, hi = 1, max(piles)
while lo < hi:
    mid = (lo + hi) // 2
    hours = sum(p // mid for p in piles)
    if hours <= h:
        hi = mid
    else:
        lo = mid + 1
print(lo)
""".lstrip(),
        # Correct but linear in the answer: dies once the speed is large.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); h = int(data[1])
piles = [int(x) for x in data[2:2+n]]
k = 1
while True:
    hours = 0
    for p in piles:
        hours += (p + k - 1) // k
        if hours > h:
            break
    if hours <= h:
        print(k)
        break
    k += 1
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  13 · First and last position of a value                                    #
# --------------------------------------------------------------------------- #

FIRST_LAST_POSITION = {
    "slug": "first-last-position",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Find First and Last Position of Element in Sorted Array",
    "statement": (
        "Given an array of n integers sorted in non-decreasing order and a "
        "target value, report the first and the last index (0-based) at which "
        "the target occurs.\n\n"
        "Print '-1 -1' when the target is absent. Duplicates are common, and "
        "the array may consist of a single repeated value.\n\n"
        "Two binary searches — one for the lower bound and one for the upper "
        "bound — give O(log n); scanning for the ends does not."
    ),
    "constraints": [
        "0 <= n <= 200000",
        "-1000000000 <= arr[i] <= 1000000000, sorted non-decreasing",
        "-1000000000 <= target <= 1000000000",
        "O(log n) is expected",
    ],
    "input_format": (
        "Line 1: n and target separated by a space.\n"
        "Line 2: the n sorted values. The line is empty when n = 0."
    ),
    "output_format": (
        "Two integers separated by a space: the first and the last index of "
        "the target, or '-1 -1' if it does not occur. Whitespace layout is "
        "not graded."
    ),
    "examples": [
        {
            "stdin": "6 8\n5 7 7 8 8 10\n",
            "stdout": "3 4",
            "explanation": "The value 8 occupies indices 3 and 4.",
        },
        {
            "stdin": "6 6\n5 7 7 8 8 10\n",
            "stdout": "-1 -1",
            "explanation": "6 never occurs, even though it lies between two present values.",
        },
    ],
    "criteria": [
        "Report '-1 -1' for an absent target instead of an insertion point",
        "Return the extreme indices when the value is repeated",
        "Handle n = 0 and an array of one repeated value",
    ],
    "io": {
        "mode": "tokens",
        "function": "search_range",
        "todo": "find the first and last index of the target, then print both (replace the single-value print in main)",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "target", "type": "long"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr", "target"],
        "returns": "int",
    },
    "reference": """
import sys
import bisect


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    target = int(data[1])
    arr = [int(x) for x in data[2:2 + n]]
    left = bisect.bisect_left(arr, target)
    if left == n or arr[left] != target:
        print(-1, -1)
        return
    right = bisect.bisect_right(arr, target) - 1
    print(left, right)


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: repeated target", "stdin": "6 8\n5 7 7 8 8 10\n", "hidden": False, "match": "tokens"},
        {"name": "sample: absent target", "stdin": "6 6\n5 7 7 8 8 10\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: empty array", "stdin": "0 3\n\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: target at the start", "stdin": "4 1\n1 1 2 3\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: target at the end", "stdin": "4 3\n1 2 3 3\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: all identical and equal to target", "stdin": "5 7\n7 7 7 7 7\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: target below everything", "stdin": "3 -5\n0 1 2\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: target above everything", "stdin": "3 99\n0 1 2\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: negatives", "stdin": "5 -3\n-9 -3 -3 -1 4\n", "hidden": True, "match": "tokens"},
        {
            "name": "hidden: scale",
            "stdin": _sorted_array_case(163, 200000, 500, -1000, 1000),
            "hidden": True,
            "match": "tokens",
        },
    ],
    "wrong": [
        # Uses the lower bound for both ends.
        """
import sys
import bisect
data = sys.stdin.read().split()
n = int(data[0]); target = int(data[1])
arr = [int(x) for x in data[2:2+n]]
left = bisect.bisect_left(arr, target)
if left == n or arr[left] != target:
    print(-1, -1)
else:
    print(left, left)
""".lstrip(),
        # Never checks that the target is present, so it prints insertion points.
        """
import sys
import bisect
data = sys.stdin.read().split()
n = int(data[0]); target = int(data[1])
arr = [int(x) for x in data[2:2+n]]
print(bisect.bisect_left(arr, target), bisect.bisect_right(arr, target) - 1)
""".lstrip(),
        # Finds some occurrence and reports it as both ends.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); target = int(data[1])
arr = [int(x) for x in data[2:2+n]]
lo, hi = 0, n - 1
found = -1
while lo <= hi:
    mid = (lo + hi) // 2
    if arr[mid] == target:
        found = mid
        break
    if arr[mid] < target:
        lo = mid + 1
    else:
        hi = mid - 1
print(found, found)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  14 · Sum of two integers without + or -                                    #
# --------------------------------------------------------------------------- #

ADD_WITHOUT_PLUS = {
    "slug": "add-without-plus",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 30,
    "title": "Sum of Two Integers Without + or -",
    "statement": (
        "Read two signed integers a and b and print a + b, computed without "
        "the + and - operators. Use XOR for the bit-wise sum and AND shifted "
        "left by one for the carry, repeating until there is no carry left.\n\n"
        "Both operands and the result are 32-bit signed values, and negatives "
        "are represented in two's complement. In Python the integers are "
        "arbitrary precision, so the carry loop never terminates unless you "
        "mask to 32 bits on every step and then convert a result above "
        "2^31 - 1 back to its negative value. In C, C++, Java and JavaScript "
        "the width is already 32 bits for the relevant operators, so the "
        "conversion is where the languages differ, not the algorithm."
    ),
    "constraints": [
        "-1000000000 <= a, b <= 1000000000",
        "The result always fits in a 32-bit signed integer",
        "The + and - operators are not needed; the intended solution is "
        "XOR plus a shifted AND carry",
        "Mask to 32 bits and sign-correct so every language agrees",
    ],
    "input_format": "A single line with a and b separated by a space.",
    "output_format": "A single integer: a + b.",
    "examples": [
        {
            "stdin": "2 3\n",
            "stdout": "5",
            "explanation": "2 XOR 3 = 1 with carry 2; adding the carry gives 5.",
        },
        {
            "stdin": "-7 3\n",
            "stdout": "-4",
            "explanation": "A negative operand: after masking, the 32-bit pattern is above 2^31 and must be read back as -4.",
        },
    ],
    "criteria": [
        "Correct for two negatives, mixed signs and zeros",
        "Terminate: the carry loop must be bounded to 32 bits",
        "Sign-correct the masked result rather than printing a large positive",
    ],
    "io": {
        "mode": "tokens",
        "function": "add_without_plus",
        "todo": "return a + b using only bit-wise operations",
        "reads": [
            {"name": "a", "type": "int"},
            {"name": "b", "type": "int"},
        ],
        "args": ["a", "b"],
        "returns": "int",
    },
    "reference": """
import sys

MASK = 0xFFFFFFFF
SIGN = 0x80000000


def main():
    data = sys.stdin.read().split()
    a = int(data[0]) & MASK
    b = int(data[1]) & MASK
    while b:
        carry = (a & b) << 1
        a = (a ^ b) & MASK
        b = carry & MASK
    print(a if a < SIGN else a - 0x100000000)


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: two positives", "stdin": "2 3\n", "hidden": False},
        {"name": "sample: mixed signs", "stdin": "-7 3\n", "hidden": False},
        {"name": "hidden: both zero", "stdin": "0 0\n", "hidden": True},
        {"name": "hidden: two negatives", "stdin": "-12 -30\n", "hidden": True},
        {"name": "hidden: cancels to zero", "stdin": "1000000000 -1000000000\n", "hidden": True},
        {"name": "hidden: maximum positives", "stdin": "1000000000 1000000000\n", "hidden": True},
        {"name": "hidden: minimum negatives", "stdin": "-1000000000 -1000000000\n", "hidden": True},
        {"name": "hidden: carry chain", "stdin": "65535 1\n", "hidden": True},
        {"name": "hidden: negative result", "stdin": "5 -9\n", "hidden": True},
        {"name": "hidden: zero plus negative", "stdin": "0 -1\n", "hidden": True},
    ],
    "wrong": [
        # Unmasked carry loop: never terminates once an operand is negative.
        """
import sys
data = sys.stdin.read().split()
a = int(data[0]); b = int(data[1])
while b:
    carry = (a & b) << 1
    a = a ^ b
    b = carry
print(a)
""".lstrip(),
        # XOR only: forgets the carry entirely.
        """
import sys
data = sys.stdin.read().split()
a = int(data[0]); b = int(data[1])
print(a ^ b)
""".lstrip(),
        # Masks but never sign-corrects, so negative results print as huge positives.
        """
import sys
data = sys.stdin.read().split()
MASK = 0xFFFFFFFF
a = int(data[0]) & MASK
b = int(data[1]) & MASK
while b:
    carry = (a & b) << 1
    a = (a ^ b) & MASK
    b = carry & MASK
print(a)
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  15 · Number of 1 bits                                                      #
# --------------------------------------------------------------------------- #

NUMBER_OF_ONE_BITS = {
    "slug": "count-set-bits-32",
    "skill_id": "dsa_arrays",
    "difficulty": 3,
    "estimated_minutes": 15,
    "title": "Number of 1 Bits",
    "statement": (
        "Read one 32-bit unsigned integer and print how many of its 32 bits "
        "are 1 (its Hamming weight).\n\n"
        "The value can be as large as 4294967295, which does not fit in a "
        "signed 32-bit int, so read it into a 64-bit type and mask it to the "
        "low 32 bits before counting. Every bit of the 32-bit width counts, "
        "including the top one."
    ),
    "constraints": [
        "0 <= x <= 4294967295 (2^32 - 1)",
        "x does not fit in a signed 32-bit int: read it as long long (C/C++) "
        "or long (Java)",
        "All 32 bits are counted, not just the low 16",
    ],
    "input_format": "A single line containing x.",
    "output_format": "A single integer: the number of bits of x that are 1.",
    "examples": [
        {
            "stdin": "11\n",
            "stdout": "3",
            "explanation": "11 is 1011 in binary, which holds three 1 bits.",
        },
        {
            "stdin": "4294967295\n",
            "stdout": "32",
            "explanation": "Every bit of the 32-bit width is set.",
        },
    ],
    "criteria": [
        "Count bits, not decimal digits",
        "Count all 32 bits, including those above bit 15",
        "Handle x = 0",
    ],
    "io": {
        "mode": "tokens",
        "function": "count_set_bits",
        "todo": "return how many of the 32 bits of x are 1",
        "reads": [{"name": "x", "type": "long"}],
        "args": ["x"],
        "returns": "int",
    },
    "reference": """
import sys


def main():
    x = int(sys.stdin.read().split()[0]) & 0xFFFFFFFF
    count = 0
    while x:
        x &= x - 1
        count += 1
    print(count)


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: eleven", "stdin": "11\n", "hidden": False},
        {"name": "sample: all bits set", "stdin": "4294967295\n", "hidden": False},
        {"name": "hidden: zero", "stdin": "0\n", "hidden": True},
        {"name": "hidden: one", "stdin": "1\n", "hidden": True},
        {"name": "hidden: only the top bit", "stdin": "2147483648\n", "hidden": True},
        {"name": "hidden: alternating bits", "stdin": "2863311530\n", "hidden": True},
        {"name": "hidden: high half only", "stdin": "4294901760\n", "hidden": True},
        {"name": "hidden: low half only", "stdin": "65535\n", "hidden": True},
        {"name": "hidden: power of two boundary", "stdin": "128\n", "hidden": True},
    ],
    "wrong": [
        # Counts odd decimal digits instead of bits.
        """
import sys
x = int(sys.stdin.read().split()[0])
count = 0
while x:
    count += x % 2
    x //= 10
print(count)
""".lstrip(),
        # Only inspects the low 16 bits.
        """
import sys
x = int(sys.stdin.read().split()[0]) & 0xFFFF
print(bin(x).count('1'))
""".lstrip(),
        # Reports the bit length rather than the popcount.
        """
import sys
x = int(sys.stdin.read().split()[0]) & 0xFFFFFFFF
print(x.bit_length())
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  16 · Counting bits                                                         #
# --------------------------------------------------------------------------- #

COUNTING_BITS = {
    "slug": "counting-bits",
    "skill_id": "dsa_arrays",
    "difficulty": 4,
    "estimated_minutes": 25,
    "title": "Counting Bits",
    "statement": (
        "Given n, print the Hamming weight of every integer from 0 to n "
        "inclusive — that is n + 1 numbers, starting with the weight of 0.\n\n"
        "Recomputing each weight from scratch works, but the intended "
        "solution reuses earlier answers: the weight of i is the weight of "
        "i >> 1 plus the lowest bit of i."
    ),
    "constraints": [
        "0 <= n <= 200000",
        "The output holds exactly n + 1 numbers, the first of which is 0",
        "O(n) is expected",
    ],
    "input_format": "A single line containing n.",
    "output_format": (
        "n + 1 integers: the Hamming weight of 0, 1, ..., n in that order, "
        "separated by whitespace. Whitespace layout is not graded."
    ),
    "examples": [
        {
            "stdin": "5\n",
            "stdout": "0 1 1 2 1 2",
            "explanation": "Weights of 0..5: 0, 1, 1, 2, 1, 2 — six numbers for n = 5.",
        },
        {
            "stdin": "0\n",
            "stdout": "0",
            "explanation": "Only the weight of 0 is printed, and it is 0.",
        },
    ],
    "criteria": [
        "Print n + 1 numbers, including the entry for 0",
        "Handle n = 0",
        "Reuse previous results rather than recounting bits per number",
    ],
    "io": {
        "mode": "tokens",
        "function": "counting_bits",
        "todo": "compute the Hamming weight of 0..n, then print all n + 1 values (replace the single-value print in main)",
        "reads": [{"name": "n", "type": "int"}],
        "args": ["n"],
        "returns": "int",
    },
    "reference": """
import sys


def main():
    n = int(sys.stdin.read().split()[0])
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        dp[i] = dp[i >> 1] + (i & 1)
    sys.stdout.write(' '.join(map(str, dp)))
    sys.stdout.write('\\n')


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: n = 5", "stdin": "5\n", "hidden": False, "match": "tokens"},
        {"name": "sample: n = 0", "stdin": "0\n", "hidden": False, "match": "tokens"},
        {"name": "hidden: n = 1", "stdin": "1\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: n = 2", "stdin": "2\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: crosses a power of two", "stdin": "16\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: just below a power of two", "stdin": "15\n", "hidden": True, "match": "tokens"},
        {"name": "hidden: scale", "stdin": "200000\n", "hidden": True, "match": "tokens"},
    ],
    "wrong": [
        # Prints only n values, dropping the entry for 0.
        """
import sys
n = int(sys.stdin.read().split()[0])
dp = [0] * (n + 1)
for i in range(1, n + 1):
    dp[i] = dp[i >> 1] + (i & 1)
print(' '.join(map(str, dp[1:])))
""".lstrip(),
        # Forgets the low bit of i in the recurrence.
        """
import sys
n = int(sys.stdin.read().split()[0])
dp = [0] * (n + 1)
for i in range(1, n + 1):
    dp[i] = dp[i >> 1] + 1
print(' '.join(map(str, dp)))
""".lstrip(),
        # Off by one the other way: weights of 1..n+1.
        """
import sys
n = int(sys.stdin.read().split()[0])
print(' '.join(str(bin(i).count('1')) for i in range(1, n + 2)))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  17 · Missing number                                                        #
# --------------------------------------------------------------------------- #

MISSING_NUMBER = {
    "slug": "missing-number",
    "skill_id": "dsa_arrays",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Missing Number",
    "statement": (
        "An array holds n distinct integers drawn from the range 0..n, so "
        "exactly one value of that range is absent. Find it.\n\n"
        "The array is not sorted. Two O(n) solutions exist: XOR every value "
        "together with every index of 0..n, or subtract the sum of the array "
        "from n(n + 1) / 2."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "The n values are distinct and all lie in 0..n",
        "The array is not sorted",
        "n(n + 1) / 2 reaches 2 * 10^10, which overflows a 32-bit int: use "
        "long long (C/C++) or long (Java) if you take the sum route",
        "O(n) time is expected",
    ],
    "input_format": "Line 1: n.\nLine 2: the n values.",
    "output_format": "A single integer: the missing value.",
    "examples": [
        {
            "stdin": "3\n3 0 1\n",
            "stdout": "2",
            "explanation": "The range is 0..3 and 2 is the value not present.",
        },
        {
            "stdin": "2\n0 1\n",
            "stdout": "2",
            "explanation": "Nothing is missing from the front, so the absent value is n itself.",
        },
    ],
    "criteria": [
        "Handle the missing value being 0 or n",
        "Do not assume the array is sorted",
        "Avoid 32-bit overflow if you use the sum formula",
    ],
    "io": {
        "mode": "tokens",
        "function": "missing_number",
        "todo": "return the value of 0..n that is absent from the array",
        "reads": [
            {"name": "n", "type": "int"},
            {"name": "arr", "type": "long", "count": "n"},
        ],
        "args": ["arr"],
        "returns": "int",
    },
    "reference": """
import sys


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    arr = [int(x) for x in data[1:1 + n]]
    total = n * (n + 1) // 2
    print(total - sum(arr))


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: middle missing", "stdin": "3\n3 0 1\n", "hidden": False},
        {"name": "sample: n missing", "stdin": "2\n0 1\n", "hidden": False},
        {"name": "hidden: single value, zero missing", "stdin": "1\n1\n", "hidden": True},
        {"name": "hidden: single value, one missing", "stdin": "1\n0\n", "hidden": True},
        {"name": "hidden: zero missing, unsorted", "stdin": "4\n2 4 1 3\n", "hidden": True},
        {"name": "hidden: sorted with a late gap", "stdin": "5\n0 1 2 3 5\n", "hidden": True},
        {"name": "hidden: unsorted with an early gap", "stdin": "5\n5 3 4 1 2\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": _missing_number_case(167, 200000),
            "hidden": True,
        },
    ],
    "wrong": [
        # Walks the unsorted array looking for arr[i] != i.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
answer = n
for i in range(n):
    if arr[i] != i:
        answer = i
        break
print(answer)
""".lstrip(),
        # XOR that forgets to fold in n itself.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
acc = 0
for i in range(n):
    acc ^= i ^ arr[i]
print(acc)
""".lstrip(),
        # Uses n(n-1)/2 as the expected total.
        """
import sys
data = sys.stdin.read().split()
n = int(data[0]); arr = [int(x) for x in data[1:1+n]]
print(n * (n - 1) // 2 - sum(arr))
""".lstrip(),
    ],
}


# --------------------------------------------------------------------------- #
#  18 · Reverse bits                                                          #
# --------------------------------------------------------------------------- #

REVERSE_BITS = {
    "slug": "reverse-bits-32",
    "skill_id": "dsa_arrays",
    "difficulty": 4,
    "estimated_minutes": 25,
    "title": "Reverse Bits",
    "statement": (
        "Read a 32-bit unsigned integer and print the value obtained by "
        "reversing the order of its 32 bits: bit 0 becomes bit 31, bit 1 "
        "becomes bit 30, and so on.\n\n"
        "The width is exactly 32, so leading zeros matter — reversing the "
        "printable binary digits of a small number is not the same operation. "
        "The result is also unsigned and can exceed 2^31 - 1, so hold both "
        "the input and the output in a 64-bit type and mask to 32 bits."
    ),
    "constraints": [
        "0 <= x <= 4294967295 (2^32 - 1)",
        "The answer is unsigned and can reach 4294967295, so it does not fit "
        "a signed 32-bit int: use long long (C/C++) or long (Java)",
        "Exactly 32 bits are reversed, including leading zeros",
    ],
    "input_format": "A single line containing x.",
    "output_format": "A single integer: the 32-bit reversal of x.",
    "examples": [
        {
            "stdin": "1\n",
            "stdout": "2147483648",
            "explanation": "Bit 0 is the only bit set, and it moves to bit 31, giving 2^31.",
        },
        {
            "stdin": "43261596\n",
            "stdout": "964176192",
            "explanation": "00000010100101000001111010011100 reversed is 00111001011110000010100101000000.",
        },
    ],
    "criteria": [
        "Reverse exactly 32 bits, so leading zeros are preserved as trailing zeros",
        "Print the result as an unsigned value, never negative",
        "Handle x = 0 and x = 2^32 - 1",
    ],
    "io": {
        "mode": "tokens",
        "function": "reverse_bits",
        "todo": "return the value formed by reversing the 32 bits of x",
        "reads": [{"name": "x", "type": "long"}],
        "args": ["x"],
        "returns": "long",
    },
    "reference": """
import sys


def main():
    x = int(sys.stdin.read().split()[0]) & 0xFFFFFFFF
    result = 0
    for _ in range(32):
        result = (result << 1) | (x & 1)
        x >>= 1
    print(result)


main()
""".lstrip(),
    "inputs": [
        {"name": "sample: lowest bit", "stdin": "1\n", "hidden": False},
        {"name": "sample: leetcode value", "stdin": "43261596\n", "hidden": False},
        {"name": "hidden: zero", "stdin": "0\n", "hidden": True},
        # Not 2^32 - 1 itself: its own reversal is the string quoted in the
        # constraints, and a hidden expected output must not appear there.
        {"name": "hidden: all bits but the lowest", "stdin": "4294967294\n", "hidden": True},
        {"name": "hidden: only the top bit", "stdin": "2147483648\n", "hidden": True},
        {"name": "hidden: alternating bits", "stdin": "2863311530\n", "hidden": True},
        {"name": "hidden: palindromic pattern", "stdin": "4278255360\n", "hidden": True},
        {"name": "hidden: low half only", "stdin": "65535\n", "hidden": True},
    ],
    "wrong": [
        # Reverses only 16 bits.
        """
import sys
x = int(sys.stdin.read().split()[0]) & 0xFFFFFFFF
result = 0
for _ in range(16):
    result = (result << 1) | (x & 1)
    x >>= 1
print(result)
""".lstrip(),
        # Reverses the printable binary digits, losing the leading zeros.
        """
import sys
x = int(sys.stdin.read().split()[0]) & 0xFFFFFFFF
print(int(bin(x)[2:][::-1] or '0', 2))
""".lstrip(),
        # Reverses the decimal digits.
        """
import sys
x = int(sys.stdin.read().split()[0])
print(int(str(x)[::-1]))
""".lstrip(),
    ],
}


PROBLEMS: list[dict[str, Any]] = [
    REVERSE_LINKED_LIST,
    LINKED_LIST_CYCLE,
    MERGE_TWO_LISTS,
    MERGE_K_LISTS,
    REMOVE_NTH_FROM_END,
    REORDER_LIST,
    INSERT_INTERVAL,
    MERGE_INTERVALS,
    NON_OVERLAPPING,
    CAN_ATTEND_ALL,
    MIN_MEETING_ROOMS,
    KOKO,
    FIRST_LAST_POSITION,
    ADD_WITHOUT_PLUS,
    NUMBER_OF_ONE_BITS,
    COUNTING_BITS,
    MISSING_NUMBER,
    REVERSE_BITS,
]
