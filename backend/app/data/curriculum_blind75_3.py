"""Blind 75 problems, batch 3: trees, tries, heaps and backtracking.

Split across files so the catalogue can grow without one unreadable module.
Each entry follows the contract in `docs/curriculum_authoring.md`: an `io`
spec drives starter generation for every language, `reference` derives the
expected outputs, and `wrong` solutions must be rejected by the case bank.

Conventions used throughout this batch
--------------------------------------
Every problem in this batch reads **exactly one line** of stdin. That is a
deliberate consequence of the starter generator: ``io.mode = "line"`` hands the
learner the whole payload as a string in all five languages, so no learner has
to fight a starter that only reads part of its input. Multi-part payloads are
therefore packed onto that line with ``|`` separating the sections.

*Tree serialisation* — a tree is a level-order (breadth-first) list of tokens
with the literal ``null`` marking a missing child. Trailing ``null`` tokens are
omitted. The empty tree is the single token ``null``. The same format is used
for every tree problem, for input and for output, so a tree printed by one
problem could be fed to another. Learners parse the tokens and build their own
node structure; that is part of the exercise, and the format is deliberately
flat enough to be built with plain arrays in C.

*Command streams* — the stateful design problems (trie, word dictionary,
median stream) are re-specified as an operation count followed by that many
operations, all on one line, separated by ``;``. Only query operations print,
one line each.
"""

from __future__ import annotations

import random
from typing import Any

# --------------------------------------------------------------------------- #
#  Deterministic input generation                                             #
# --------------------------------------------------------------------------- #


def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def _serialize(val: list[int], left: list[int], right: list[int], root: int = 0) -> str:
    """Canonical level-order serialisation with trailing nulls trimmed."""
    if not val:
        return "null"
    out: list[str] = []
    queue: list[int] = [root]
    head = 0
    while head < len(queue):
        node = queue[head]
        head += 1
        if node == -1:
            out.append("null")
            continue
        out.append(str(val[node]))
        queue.append(left[node])
        queue.append(right[node])
    while out and out[-1] == "null":
        out.pop()
    return " ".join(out)


def _random_tree(seed: int, n: int, lo: int, hi: int) -> str:
    """A randomly shaped tree of n nodes (depth stays O(log n))."""
    if n <= 0:
        return "null"
    rng = _rng(seed)
    val = [rng.randint(lo, hi) for _ in range(n)]
    left = [-1] * n
    right = [-1] * n
    slots: list[tuple[int, int]] = [(0, 0), (0, 1)]
    for index in range(1, n):
        pick = rng.randrange(len(slots))
        slots[pick], slots[-1] = slots[-1], slots[pick]
        node, side = slots.pop()
        if side == 0:
            left[node] = index
        else:
            right[node] = index
        slots.append((index, 0))
        slots.append((index, 1))
    return _serialize(val, left, right)


def _bst_arrays(values: list[int]) -> tuple[list[int], list[int], list[int]]:
    val: list[int] = []
    left: list[int] = []
    right: list[int] = []
    for value in values:
        val.append(value)
        left.append(-1)
        right.append(-1)
        index = len(val) - 1
        if index == 0:
            continue
        cur = 0
        while True:
            if value < val[cur]:
                if left[cur] == -1:
                    left[cur] = index
                    break
                cur = left[cur]
            else:
                if right[cur] == -1:
                    right[cur] = index
                    break
                cur = right[cur]
    return val, left, right


def _random_bst(seed: int, n: int, lo: int, hi: int) -> str:
    rng = _rng(seed)
    values = rng.sample(range(lo, hi), n)
    return _serialize(*_bst_arrays(values))


def _bst_values(seed: int, n: int, lo: int, hi: int) -> list[int]:
    rng = _rng(seed)
    return rng.sample(range(lo, hi), n)


def _left_chain(seed: int, n: int, lo: int, hi: int) -> str:
    """A left-skewed chain: depth == n."""
    rng = _rng(seed)
    val = [rng.randint(lo, hi) for _ in range(n)]
    left = [-1] * n
    right = [-1] * n
    for index in range(n - 1):
        left[index] = index + 1
    return _serialize(val, left, right)


def _traversals(seed: int, n: int) -> tuple[list[int], list[int]]:
    """Preorder and inorder of one randomly shaped tree with distinct values."""
    rng = _rng(seed)
    labels = rng.sample(range(1, 10 * n + 1), n)
    tree = _random_tree(seed * 7 + 1, n, 0, 1).split()
    # Rebuild structure from the serialisation, then relabel with distinct ids.
    val, left, right = _parse_tokens(tree)
    for index in range(len(val)):
        val[index] = labels[index]
    preorder: list[int] = []
    inorder: list[int] = []
    stack: list[tuple[int, int]] = [(0, 0)]
    while stack:
        node, state = stack.pop()
        if node == -1:
            continue
        if state == 0:
            preorder.append(val[node])
            stack.append((node, 1))
            stack.append((left[node], 0))
        else:
            inorder.append(val[node])
            stack.append((right[node], 0))
    return preorder, inorder


def _parse_tokens(tokens: list[str]) -> tuple[list[int], list[int], list[int]]:
    if not tokens or tokens[0] == "null":
        return [], [], []
    val: list[int] = []
    left: list[int] = []
    right: list[int] = []

    def add(token: str) -> int:
        val.append(int(token))
        left.append(-1)
        right.append(-1)
        return len(val) - 1

    add(tokens[0])
    queue = [0]
    head = 0
    pos = 1
    while head < len(queue) and pos < len(tokens):
        node = queue[head]
        head += 1
        if pos < len(tokens):
            token = tokens[pos]
            pos += 1
            if token != "null":
                child = add(token)
                left[node] = child
                queue.append(child)
        if pos < len(tokens):
            token = tokens[pos]
            pos += 1
            if token != "null":
                child = add(token)
                right[node] = child
                queue.append(child)
    return val, left, right


def _random_grid(seed: int, rows: int, cols: int, alphabet: str) -> list[str]:
    rng = _rng(seed)
    return ["".join(rng.choice(alphabet) for _ in range(cols)) for _ in range(rows)]


def _random_words(seed: int, count: int, min_len: int, max_len: int, alphabet: str) -> list[str]:
    rng = _rng(seed)
    words = []
    for _ in range(count):
        length = rng.randint(min_len, max_len)
        words.append("".join(rng.choice(alphabet) for _ in range(length)))
    return words


# --------------------------------------------------------------------------- #
#  Shared prose                                                               #
# --------------------------------------------------------------------------- #

_TREE_FORMAT = (
    "A binary tree arrives as a single line of whitespace-separated tokens in "
    "level order (breadth-first). Each token is either an integer or the "
    "literal token `null`, which marks a missing child. Trailing `null` tokens "
    "are omitted. The empty tree is written as the single token `null`.\n\n"
    "For example `1 2 3 null null 4 5` is the tree with root 1, whose left "
    "child 2 has no children, and whose right child 3 has children 4 and 5.\n\n"
    "There is no tree object handed to you: parse the tokens and build your own "
    "nodes (in C, three parallel arrays for value, left index and right index "
    "are enough)."
)

_TREE_CONSTRAINTS = [
    "0 <= number of nodes <= 100000",
    "-1000000 <= node value <= 1000000",
    "The tree is at most 5000 levels deep, so a recursive solution is safe",
    "The whole tree arrives on one line; read the line, then tokenise it",
]

_PY_TREE = """import sys

def parse_tree(line):
    tokens = line.split()
    if not tokens or tokens[0] == 'null':
        return [], [], []
    val = []
    left = []
    right = []
    def add(token):
        val.append(int(token))
        left.append(-1)
        right.append(-1)
        return len(val) - 1
    add(tokens[0])
    queue = [0]
    head = 0
    pos = 1
    while head < len(queue) and pos < len(tokens):
        node = queue[head]
        head += 1
        if pos < len(tokens):
            token = tokens[pos]
            pos += 1
            if token != 'null':
                child = add(token)
                left[node] = child
                queue.append(child)
        if pos < len(tokens):
            token = tokens[pos]
            pos += 1
            if token != 'null':
                child = add(token)
                right[node] = child
                queue.append(child)
    return val, left, right

def serialize(val, left, right, root=0):
    if not val:
        return 'null'
    out = []
    queue = [root]
    head = 0
    while head < len(queue):
        node = queue[head]
        head += 1
        if node == -1:
            out.append('null')
            continue
        out.append(str(val[node]))
        queue.append(left[node])
        queue.append(right[node])
    while out and out[-1] == 'null':
        out.pop()
    return ' '.join(out)

def read_line():
    return sys.stdin.readline().rstrip('\\n')

"""


# --------------------------------------------------------------------------- #
#  01 · Maximum depth of a binary tree                                        #
# --------------------------------------------------------------------------- #

MAX_DEPTH = {
    "slug": "maximum-depth-of-binary-tree",
    "skill_id": "dsa_arrays",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Maximum Depth of Binary Tree",
    "statement": (
        "Return the maximum depth of a binary tree: the number of nodes on the "
        "longest path from the root down to a leaf. The empty tree has depth 0.\n\n"
        + _TREE_FORMAT
    ),
    "constraints": _TREE_CONSTRAINTS,
    "input_format": "One line: the tree in level-order token form.",
    "output_format": "A single integer: the maximum depth.",
    "examples": [
        {
            "stdin": "3 9 20 null null 15 7\n",
            "stdout": "3",
            "explanation": "Root 3, then 20, then 15 (or 7) gives a path of three nodes.",
        },
        {
            "stdin": "null\n",
            "stdout": "0",
            "explanation": "The single token `null` is the empty tree, whose depth is 0.",
        },
    ],
    "criteria": [
        "Return 0 for the empty tree",
        "Handle a skewed tree thousands of levels deep",
        "Visit every node once",
    ],
    "io": {
        "mode": "line",
        "function": "max_depth",
        "todo": "parse the level-order tokens and return the depth of the tree",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": _PY_TREE + (
        "def main():\n"
        "    val, left, right = parse_tree(read_line())\n"
        "    if not val:\n"
        "        print(0)\n"
        "        return\n"
        "    best = 0\n"
        "    stack = [(0, 1)]\n"
        "    while stack:\n"
        "        node, depth = stack.pop()\n"
        "        if node == -1:\n"
        "            continue\n"
        "        if depth > best:\n"
        "            best = depth\n"
        "        stack.append((left[node], depth + 1))\n"
        "        stack.append((right[node], depth + 1))\n"
        "    print(best)\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: classic tree", "stdin": "3 9 20 null null 15 7\n", "hidden": False},
        {"name": "sample: empty tree", "stdin": "null\n", "hidden": False},
        {"name": "hidden: single node", "stdin": "-7\n", "hidden": True},
        {"name": "hidden: right heavy", "stdin": "1 2 3 null null 4 null null 5\n", "hidden": True},
        {"name": "hidden: left spine is shorter", "stdin": "1 2 3 null null 4 5 6\n", "hidden": True},
        {"name": "hidden: deep left chain", "stdin": _left_chain(101, 5000, -10**6, 10**6) + "\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _random_tree(102, 100000, -10**6, 10**6) + "\n", "hidden": True},
    ],
    "wrong": [
        # Counts nodes instead of measuring the longest path.
        (
            "import sys\n"
            "tokens = sys.stdin.readline().split()\n"
            "print(sum(1 for t in tokens if t != 'null'))\n"
        ),
        # Follows the left spine only.
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    if not val:\n"
            "        print(0)\n"
            "        return\n"
            "    node = 0\n"
            "    depth = 0\n"
            "    while node != -1:\n"
            "        depth += 1\n"
            "        node = left[node]\n"
            "    print(depth)\n"
            "main()\n"
        ),
        # Returns the minimum depth (stops at the first leaf found by BFS).
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    if not val:\n"
            "        print(0)\n"
            "        return\n"
            "    queue = [(0, 1)]\n"
            "    head = 0\n"
            "    while head < len(queue):\n"
            "        node, depth = queue[head]\n"
            "        head += 1\n"
            "        if left[node] == -1 and right[node] == -1:\n"
            "            print(depth)\n"
            "            return\n"
            "        if left[node] != -1:\n"
            "            queue.append((left[node], depth + 1))\n"
            "        if right[node] != -1:\n"
            "            queue.append((right[node], depth + 1))\n"
            "main()\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  02 · Same tree                                                             #
# --------------------------------------------------------------------------- #

SAME_TREE = {
    "slug": "same-binary-tree",
    "skill_id": "dsa_arrays",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Same Tree",
    "statement": (
        "Two binary trees are the same when they have identical structure and "
        "identical values at every position. Decide whether the two given trees "
        "are the same.\n\n" + _TREE_FORMAT + "\n\n"
        "Both trees arrive on the same line, separated by a single `|`."
    ),
    "constraints": _TREE_CONSTRAINTS
    + ["The two sections are separated by `|`; either side may be the empty tree `null`"],
    "input_format": "One line: tree A, then `|`, then tree B, all in level-order token form.",
    "output_format": "`true` if the trees are the same, otherwise `false`.",
    "examples": [
        {
            "stdin": "1 2 3 | 1 2 3\n",
            "stdout": "true",
            "explanation": "Same shape and same values at every position.",
        },
        {
            "stdin": "1 2 | 1 null 2\n",
            "stdout": "false",
            "explanation": "Both trees hold the values 1 and 2, but 2 is a left child in one and a right child in the other.",
        },
    ],
    "criteria": [
        "Compare structure, not just the multiset of values",
        "Treat two empty trees as the same",
        "Handle one tree being a prefix of the other",
    ],
    "io": {
        "mode": "line",
        "function": "same_tree",
        "todo": "parse both trees from the line and return 1 if they are identical, else 0",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": _PY_TREE + (
        "def main():\n"
        "    parts = read_line().split('|')\n"
        "    a = parse_tree(parts[0])\n"
        "    b = parse_tree(parts[1])\n"
        "    same = serialize(*a) == serialize(*b)\n"
        "    print('true' if same else 'false')\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: identical", "stdin": "1 2 3 | 1 2 3\n", "hidden": False},
        {"name": "sample: mirrored child", "stdin": "1 2 | 1 null 2\n", "hidden": False},
        {"name": "hidden: both empty", "stdin": "null | null\n", "hidden": True},
        {"name": "hidden: one empty", "stdin": "1 | null\n", "hidden": True},
        {"name": "hidden: same shape different value", "stdin": "1 2 3 | 1 2 4\n", "hidden": True},
        {"name": "hidden: same values different shape", "stdin": "1 2 3 4 | 1 2 3 null 4\n", "hidden": True},
        {"name": "hidden: negatives equal", "stdin": "-5 -6 null -7 | -5 -6 null -7\n", "hidden": True},
        {
            "name": "hidden: equal but written with redundant nulls",
            "stdin": "1 2 null null null | 1 2\n",
            "hidden": True,
        },
        {
            "name": "hidden: scale equal",
            "stdin": _random_tree(111, 100000, -10**6, 10**6)
            + " | "
            + _random_tree(111, 100000, -10**6, 10**6)
            + "\n",
            "hidden": True,
        },
        {
            "name": "hidden: scale differing deep inside",
            "stdin": _random_tree(112, 60000, -10**6, 10**6)
            + " | "
            + _random_tree(113, 60000, -10**6, 10**6)
            + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Compares the multiset of values and ignores the shape.
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    a = parse_tree(parts[0])\n"
            "    b = parse_tree(parts[1])\n"
            "    print('true' if sorted(a[0]) == sorted(b[0]) else 'false')\n"
            "main()\n"
        ),
        # Compares node count and root value only.
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    a = parse_tree(parts[0])\n"
            "    b = parse_tree(parts[1])\n"
            "    ok = len(a[0]) == len(b[0]) and (not a[0] or a[0][0] == b[0][0])\n"
            "    print('true' if ok else 'false')\n"
            "main()\n"
        ),
        # Compares the raw token text, so a trailing null or extra spacing lies.
        (
            "import sys\n"
            "parts = sys.stdin.readline().split('|')\n"
            "print('true' if parts[0].strip() == parts[1].strip() else 'false')\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  03 · Invert a binary tree                                                  #
# --------------------------------------------------------------------------- #

INVERT_TREE = {
    "slug": "invert-binary-tree",
    "skill_id": "dsa_arrays",
    "difficulty": 3,
    "estimated_minutes": 20,
    "title": "Invert Binary Tree",
    "statement": (
        "Invert the tree: swap the left and right child of every node, then "
        "print the resulting tree.\n\n" + _TREE_FORMAT + "\n\n"
        "Print the inverted tree in exactly the same format you read it in — "
        "level order, `null` for a missing child, no trailing `null` tokens. "
        "The empty tree prints as `null`."
    ),
    "constraints": _TREE_CONSTRAINTS,
    "input_format": "One line: the tree in level-order token form.",
    "output_format": "One line: the inverted tree in level-order token form.",
    "examples": [
        {
            "stdin": "4 2 7 1 3 6 9\n",
            "stdout": "4 7 2 9 6 3 1",
            "explanation": "Every node's children are swapped, so the level-order listing is mirrored level by level.",
        },
        {
            "stdin": "1 2 null 3\n",
            "stdout": "1 null 2 null 3",
            "explanation": "The left chain becomes a right chain; the gaps have to be written as `null`.",
        },
    ],
    "criteria": [
        "Print `null` for the empty tree",
        "Emit level order with `null` gaps and no trailing `null`",
        "Swap at every node, not only at the root",
    ],
    "io": {
        "mode": "line",
        "function": "invert_tree",
        "todo": "parse the tree, swap every node's children, and print it back in level-order form",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": _PY_TREE + (
        "def main():\n"
        "    val, left, right = parse_tree(read_line())\n"
        "    for node in range(len(val)):\n"
        "        left[node], right[node] = right[node], left[node]\n"
        "    print(serialize(val, left, right))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: perfect tree", "stdin": "4 2 7 1 3 6 9\n", "hidden": False},
        {"name": "sample: left chain", "stdin": "1 2 null 3\n", "hidden": False},
        {"name": "hidden: empty", "stdin": "null\n", "hidden": True},
        {"name": "hidden: single node", "stdin": "42\n", "hidden": True},
        {"name": "hidden: negative values with gaps", "stdin": "-1 -2 -3 null -4 -5\n", "hidden": True},
        {"name": "hidden: already symmetric", "stdin": "1 2 2 3 4 4 3\n", "hidden": True},
        {"name": "hidden: deep chain", "stdin": _left_chain(121, 5000, -10**6, 10**6) + "\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _random_tree(122, 100000, -10**6, 10**6) + "\n", "hidden": True},
    ],
    "wrong": [
        # Reverses the token list, which is not a mirror once gaps appear.
        (
            "import sys\n"
            "tokens = sys.stdin.readline().split()\n"
            "print(' '.join(reversed(tokens)) if tokens else 'null')\n"
        ),
        # Swaps only the root's children.
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    if val:\n"
            "        left[0], right[0] = right[0], left[0]\n"
            "    print(serialize(val, left, right))\n"
            "main()\n"
        ),
        # Swaps only where a node has two children, leaving single children put.
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    for node in range(len(val)):\n"
            "        if left[node] != -1 and right[node] != -1:\n"
            "            left[node], right[node] = right[node], left[node]\n"
            "    print(serialize(val, left, right))\n"
            "main()\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  04 · Binary tree maximum path sum                                          #
# --------------------------------------------------------------------------- #

MAX_PATH_SUM = {
    "slug": "binary-tree-maximum-path-sum",
    "skill_id": "dsa_arrays",
    "difficulty": 8,
    "estimated_minutes": 45,
    "title": "Binary Tree Maximum Path Sum",
    "statement": (
        "A path is any non-empty sequence of nodes where consecutive nodes are "
        "joined by an edge; a node appears at most once and the path does not "
        "need to pass through the root. Return the largest possible sum of the "
        "values on a path.\n\n"
        "A path may bend: it can come up from the left subtree, cross a node, "
        "and go down into the right subtree. It may also be a single node, "
        "which matters when every value is negative.\n\n" + _TREE_FORMAT
    ),
    "constraints": [
        "1 <= number of nodes <= 100000 (the tree is never empty)",
        "-1000000 <= node value <= 1000000",
        "The answer can reach 10^11, which does not fit in a 32-bit int: "
        "use long long in C/C++ and long in Java",
        "The tree is at most 5000 levels deep, so a recursive solution is safe",
    ],
    "input_format": "One line: the tree in level-order token form.",
    "output_format": "A single integer: the maximum path sum.",
    "examples": [
        {
            "stdin": "1 2 3\n",
            "stdout": "6",
            "explanation": "The path 2 - 1 - 3 bends at the root and sums to 6.",
        },
        {
            "stdin": "-10 9 20 null null 15 7\n",
            "stdout": "42",
            "explanation": "The best path is 15 - 20 - 7 = 42; going up through -10 would only lose value.",
        },
    ],
    "criteria": [
        "Drop a subtree whose best downward sum is negative",
        "Allow the path to bend at a node instead of only running root-to-leaf",
        "Handle an all-negative tree by returning the largest single value",
        "Use 64-bit arithmetic",
    ],
    "io": {
        "mode": "line",
        "function": "max_path_sum",
        "todo": "parse the tree and return the largest sum over any non-empty path",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "long",
    },
    "reference": _PY_TREE + (
        "def main():\n"
        "    val, left, right = parse_tree(read_line())\n"
        "    order = []\n"
        "    stack = [0]\n"
        "    while stack:\n"
        "        node = stack.pop()\n"
        "        order.append(node)\n"
        "        if left[node] != -1:\n"
        "            stack.append(left[node])\n"
        "        if right[node] != -1:\n"
        "            stack.append(right[node])\n"
        "    down = [0] * len(val)\n"
        "    best = None\n"
        "    for node in reversed(order):\n"
        "        l = down[left[node]] if left[node] != -1 else 0\n"
        "        r = down[right[node]] if right[node] != -1 else 0\n"
        "        if l < 0:\n"
        "            l = 0\n"
        "        if r < 0:\n"
        "            r = 0\n"
        "        through = val[node] + l + r\n"
        "        if best is None or through > best:\n"
        "            best = through\n"
        "        down[node] = val[node] + (l if l > r else r)\n"
        "    print(best)\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: bend at root", "stdin": "1 2 3\n", "hidden": False},
        {"name": "sample: skip the root", "stdin": "-10 9 20 null null 15 7\n", "hidden": False},
        {"name": "hidden: single negative node", "stdin": "-3\n", "hidden": True},
        {"name": "hidden: all negative", "stdin": "-5 -2 -8 -1 -9\n", "hidden": True},
        {"name": "hidden: both subtrees must be dropped", "stdin": "5 -1 -2\n", "hidden": True},
        {"name": "hidden: one subtree must be dropped", "stdin": "1 -2 3\n", "hidden": True},
        # Values just under the limit rather than exactly 1000000: an expected
        # output of "1000000" also appears in the constraint text, which the
        # hidden-case leak test (rightly) cannot tell apart from a real leak.
        {"name": "hidden: negative root positive children", "stdin": "-999979 999983 999977\n", "hidden": True},
        {"name": "hidden: best path is a single leaf", "stdin": "-2 -1 -3 null null -4 1000\n", "hidden": True},
        {
            "name": "hidden: deep chain of large values",
            "stdin": _left_chain(131, 5000, 900000, 10**6) + "\n",
            "hidden": True,
        },
        {"name": "hidden: scale", "stdin": _random_tree(132, 100000, -10**6, 10**6) + "\n", "hidden": True},
        {
            "name": "hidden: scale all positive (overflows 32-bit)",
            "stdin": _random_tree(133, 100000, 900000, 10**6) + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Never drops a negative subtree.
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    order = []\n"
            "    stack = [0]\n"
            "    while stack:\n"
            "        node = stack.pop()\n"
            "        order.append(node)\n"
            "        if left[node] != -1:\n"
            "            stack.append(left[node])\n"
            "        if right[node] != -1:\n"
            "            stack.append(right[node])\n"
            "    down = [0] * len(val)\n"
            "    best = None\n"
            "    for node in reversed(order):\n"
            "        l = down[left[node]] if left[node] != -1 else 0\n"
            "        r = down[right[node]] if right[node] != -1 else 0\n"
            "        through = val[node] + l + r\n"
            "        if best is None or through > best:\n"
            "            best = through\n"
            "        down[node] = val[node] + (l if l > r else r)\n"
            "    print(best)\n"
            "main()\n"
        ),
        # Only considers straight downward paths, never a bend.
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    order = []\n"
            "    stack = [0]\n"
            "    while stack:\n"
            "        node = stack.pop()\n"
            "        order.append(node)\n"
            "        if left[node] != -1:\n"
            "            stack.append(left[node])\n"
            "        if right[node] != -1:\n"
            "            stack.append(right[node])\n"
            "    down = [0] * len(val)\n"
            "    best = None\n"
            "    for node in reversed(order):\n"
            "        l = down[left[node]] if left[node] != -1 else 0\n"
            "        r = down[right[node]] if right[node] != -1 else 0\n"
            "        if l < 0:\n"
            "            l = 0\n"
            "        if r < 0:\n"
            "            r = 0\n"
            "        down[node] = val[node] + (l if l > r else r)\n"
            "        if best is None or down[node] > best:\n"
            "            best = down[node]\n"
            "    print(best)\n"
            "main()\n"
        ),
        # Clamps the answer at zero, so an all-negative tree reports 0.
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    order = []\n"
            "    stack = [0]\n"
            "    while stack:\n"
            "        node = stack.pop()\n"
            "        order.append(node)\n"
            "        if left[node] != -1:\n"
            "            stack.append(left[node])\n"
            "        if right[node] != -1:\n"
            "            stack.append(right[node])\n"
            "    down = [0] * len(val)\n"
            "    best = 0\n"
            "    for node in reversed(order):\n"
            "        l = max(0, down[left[node]] if left[node] != -1 else 0)\n"
            "        r = max(0, down[right[node]] if right[node] != -1 else 0)\n"
            "        best = max(best, val[node] + l + r)\n"
            "        down[node] = val[node] + max(l, r)\n"
            "    print(best)\n"
            "main()\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  05 · Level order traversal                                                 #
# --------------------------------------------------------------------------- #

LEVEL_ORDER = {
    "slug": "binary-tree-level-order-traversal",
    "skill_id": "dsa_arrays",
    "difficulty": 4,
    "estimated_minutes": 25,
    "title": "Binary Tree Level Order Traversal",
    "statement": (
        "Print the values of the tree one level at a time, top to bottom, and "
        "left to right within each level.\n\n" + _TREE_FORMAT + "\n\n"
        "Print one line per level, values separated by single spaces. The empty "
        "tree prints nothing at all."
    ),
    "constraints": _TREE_CONSTRAINTS,
    "input_format": "One line: the tree in level-order token form.",
    "output_format": "One line per level, values separated by single spaces. No output for the empty tree.",
    "examples": [
        {
            "stdin": "3 9 20 null null 15 7\n",
            "stdout": "3\n9 20\n15 7",
            "explanation": "Three levels, printed one per line, left to right.",
        },
        {
            "stdin": "1 null 2 null 3\n",
            "stdout": "1\n2\n3",
            "explanation": "A right-leaning chain has one node per level.",
        },
    ],
    "criteria": [
        "Print nothing for the empty tree",
        "Keep left-to-right order within a level",
        "Do not print `null` placeholders",
    ],
    "io": {
        "mode": "line",
        "function": "level_order",
        "todo": "parse the tree and print one line of values per level, top to bottom",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": _PY_TREE + (
        "def main():\n"
        "    val, left, right = parse_tree(read_line())\n"
        "    if not val:\n"
        "        return\n"
        "    out = []\n"
        "    level = [0]\n"
        "    while level:\n"
        "        out.append(' '.join(str(val[node]) for node in level))\n"
        "        nxt = []\n"
        "        for node in level:\n"
        "            if left[node] != -1:\n"
        "                nxt.append(left[node])\n"
        "            if right[node] != -1:\n"
        "                nxt.append(right[node])\n"
        "        level = nxt\n"
        "    sys.stdout.write('\\n'.join(out) + '\\n')\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: three levels", "stdin": "3 9 20 null null 15 7\n", "hidden": False},
        {"name": "sample: right chain", "stdin": "1 null 2 null 3\n", "hidden": False},
        {"name": "hidden: empty", "stdin": "null\n", "hidden": True},
        {"name": "hidden: single node", "stdin": "-9\n", "hidden": True},
        {"name": "hidden: gaps across a level", "stdin": "1 2 3 4 null null 5 6\n", "hidden": True},
        {"name": "hidden: duplicate values", "stdin": "7 7 7 7 7 7 7\n", "hidden": True},
        {"name": "hidden: deep chain", "stdin": _left_chain(141, 5000, -10**6, 10**6) + "\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _random_tree(142, 100000, -10**6, 10**6) + "\n", "hidden": True},
    ],
    "wrong": [
        # Prints every value on one line.
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    if not val:\n"
            "        return\n"
            "    print(' '.join(str(v) for v in val))\n"
            "main()\n"
        ),
        # Bottom-up level order.
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    if not val:\n"
            "        return\n"
            "    out = []\n"
            "    level = [0]\n"
            "    while level:\n"
            "        out.append(' '.join(str(val[node]) for node in level))\n"
            "        nxt = []\n"
            "        for node in level:\n"
            "            if left[node] != -1:\n"
            "                nxt.append(left[node])\n"
            "            if right[node] != -1:\n"
            "                nxt.append(right[node])\n"
            "        level = nxt\n"
            "    sys.stdout.write('\\n'.join(reversed(out)) + '\\n')\n"
            "main()\n"
        ),
        # Depth-first grouping that visits the right child first, so values
        # inside a level come out reversed.
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    if not val:\n"
            "        return\n"
            "    levels = {}\n"
            "    stack = [(0, 0)]\n"
            "    while stack:\n"
            "        node, depth = stack.pop()\n"
            "        levels.setdefault(depth, []).append(val[node])\n"
            "        if left[node] != -1:\n"
            "            stack.append((left[node], depth + 1))\n"
            "        if right[node] != -1:\n"
            "            stack.append((right[node], depth + 1))\n"
            "    out = [' '.join(str(v) for v in levels[d]) for d in sorted(levels)]\n"
            "    sys.stdout.write('\\n'.join(out) + '\\n')\n"
            "main()\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  06 · Serialize and deserialize                                             #
# --------------------------------------------------------------------------- #

SERIALIZE_TREE = {
    "slug": "serialize-and-deserialize-binary-tree",
    "skill_id": "dsa_arrays",
    "difficulty": 7,
    "estimated_minutes": 40,
    "title": "Serialize and Deserialize Binary Tree",
    "statement": (
        "Design an encoding that turns a binary tree into a string and back "
        "again, then prove it round-trips.\n\n"
        "Read the tree, serialise it with your own encoding, deserialise that "
        "string back into a tree, and print the resulting tree in the canonical "
        "level-order format below. Your encoding is entirely your own — only the "
        "final printed tree is graded — but it must survive null gaps and "
        "negative values, so a scheme that cannot tell a missing child from a "
        "value will fail.\n\n" + _TREE_FORMAT + "\n\n"
        "Note that the input may carry redundant trailing `null` tokens; the "
        "canonical output never does, so `1 2 null null null` prints as `1 2`."
    ),
    "constraints": _TREE_CONSTRAINTS,
    "input_format": "One line: the tree in level-order token form, possibly with redundant trailing `null` tokens.",
    "output_format": "One line: the round-tripped tree in canonical level-order token form.",
    "examples": [
        {
            "stdin": "1 2 3 null null 4 5\n",
            "stdout": "1 2 3 null null 4 5",
            "explanation": "The tree survives the round trip unchanged, gaps included.",
        },
        {
            "stdin": "1 2 null null null\n",
            "stdout": "1 2",
            "explanation": "Canonical form omits trailing `null` tokens, so the redundant ones disappear.",
        },
    ],
    "criteria": [
        "Distinguish a missing child from a real value, including negative values",
        "Round-trip the empty tree",
        "Emit canonical level order with no trailing `null`",
    ],
    "io": {
        "mode": "line",
        "function": "round_trip",
        "todo": "serialise the tree with your own encoding, deserialise it, and print it in canonical level-order form",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": _PY_TREE + (
        "def main():\n"
        "    val, left, right = parse_tree(read_line())\n"
        "    encoded = serialize(val, left, right)\n"
        "    val2, left2, right2 = parse_tree(encoded)\n"
        "    print(serialize(val2, left2, right2))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: gaps", "stdin": "1 2 3 null null 4 5\n", "hidden": False},
        {"name": "sample: redundant trailing nulls", "stdin": "1 2 null null null\n", "hidden": False},
        {"name": "hidden: empty tree", "stdin": "null\n", "hidden": True},
        {"name": "hidden: single negative node", "stdin": "-999983\n", "hidden": True},
        {"name": "hidden: negatives with gaps", "stdin": "-1 -2 -3 null -4 null -5\n", "hidden": True},
        {"name": "hidden: sparse right chain", "stdin": "1 null 2 null 3 null 4\n", "hidden": True},
        {"name": "hidden: deep chain", "stdin": _left_chain(151, 5000, -10**6, 10**6) + "\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _random_tree(152, 100000, -10**6, 10**6) + "\n", "hidden": True},
    ],
    "wrong": [
        # Echoes the input, so redundant trailing nulls survive.
        ("import sys\nprint(sys.stdin.readline().strip())\n"),
        # Drops the null markers and rebuilds a complete tree.
        _PY_TREE + (
            "def main():\n"
            "    tokens = [t for t in read_line().split() if t != 'null']\n"
            "    if not tokens:\n"
            "        print('null')\n"
            "        return\n"
            "    print(' '.join(tokens))\n"
            "main()\n"
        ),
        # Encodes with heap indexing (2i+1 / 2i+2) and rebuilds from that,
        # which reorders anything with a gap.
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    if not val:\n"
            "        print('null')\n"
            "        return\n"
            "    slots = {}\n"
            "    stack = [(0, 0)]\n"
            "    while stack:\n"
            "        node, pos = stack.pop()\n"
            "        slots[pos] = val[node]\n"
            "        if left[node] != -1:\n"
            "            stack.append((left[node], 2 * pos + 1))\n"
            "        if right[node] != -1:\n"
            "            stack.append((right[node], 2 * pos + 2))\n"
            "    top = max(slots)\n"
            "    out = [str(slots[i]) if i in slots else 'null' for i in range(top + 1)]\n"
            "    while out and out[-1] == 'null':\n"
            "        out.pop()\n"
            "    print(' '.join(out))\n"
            "main()\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  07 · Subtree of another tree                                               #
# --------------------------------------------------------------------------- #


def _subtree_case(seed: int, n: int, node_pick: int, lo: int, hi: int) -> str:
    tree = _random_tree(seed, n, lo, hi)
    val, left, right = _parse_tokens(tree.split())
    root = node_pick % len(val)
    return tree + " | " + _serialize(val, left, right, root) + "\n"


SUBTREE = {
    "slug": "subtree-of-another-tree",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Subtree of Another Tree",
    "statement": (
        "Decide whether tree S appears inside tree T as a subtree: there is a "
        "node of T such that the tree rooted at that node is identical to S in "
        "both structure and values. A whole tree counts as a subtree of itself, "
        "and the empty tree is a subtree of everything.\n\n" + _TREE_FORMAT + "\n\n"
        "T and S arrive on the same line, separated by a single `|`."
    ),
    "constraints": _TREE_CONSTRAINTS
    + [
        "The section before `|` is T and the section after it is S",
        "Values repeat freely, so matching on a value alone is not enough",
    ],
    "input_format": "One line: tree T, then `|`, then tree S, both in level-order token form.",
    "output_format": "`true` if S is a subtree of T, otherwise `false`.",
    "examples": [
        {
            "stdin": "3 4 5 1 2 | 4 1 2\n",
            "stdout": "true",
            "explanation": "The subtree rooted at 4 is exactly 4 with children 1 and 2.",
        },
        {
            "stdin": "3 4 5 1 2 null null 0 | 4 1 2\n",
            "stdout": "false",
            "explanation": "The node 4 now has an extra grandchild 0, so the subtree rooted there is no longer identical to S.",
        },
    ],
    "criteria": [
        "Match on structure, not merely on a node's value",
        "Require the match to extend to the whole subtree, including its leaves",
        "Treat an empty S as present",
    ],
    "io": {
        "mode": "line",
        "function": "is_subtree",
        "todo": "parse both trees and return 1 if S occurs as a subtree of T, else 0",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": _PY_TREE + (
        "def structural_ids(val, left, right, memo):\n"
        "    order = []\n"
        "    stack = [0]\n"
        "    while stack:\n"
        "        node = stack.pop()\n"
        "        order.append(node)\n"
        "        if left[node] != -1:\n"
        "            stack.append(left[node])\n"
        "        if right[node] != -1:\n"
        "            stack.append(right[node])\n"
        "    ids = [0] * len(val)\n"
        "    for node in reversed(order):\n"
        "        l = ids[left[node]] if left[node] != -1 else -1\n"
        "        r = ids[right[node]] if right[node] != -1 else -1\n"
        "        key = (val[node], l, r)\n"
        "        if key not in memo:\n"
        "            memo[key] = len(memo)\n"
        "        ids[node] = memo[key]\n"
        "    return ids\n"
        "\n"
        "def main():\n"
        "    parts = read_line().split('|')\n"
        "    va, la, ra = parse_tree(parts[0])\n"
        "    vb, lb, rb = parse_tree(parts[1])\n"
        "    if not vb:\n"
        "        print('true')\n"
        "        return\n"
        "    if not va:\n"
        "        print('false')\n"
        "        return\n"
        "    memo = {}\n"
        "    ids_a = structural_ids(va, la, ra, memo)\n"
        "    ids_b = structural_ids(vb, lb, rb, memo)\n"
        "    print('true' if ids_b[0] in set(ids_a) else 'false')\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: present", "stdin": "3 4 5 1 2 | 4 1 2\n", "hidden": False},
        {"name": "sample: extra grandchild", "stdin": "3 4 5 1 2 null null 0 | 4 1 2\n", "hidden": False},
        {"name": "hidden: empty S", "stdin": "1 2 3 | null\n", "hidden": True},
        {"name": "hidden: S equals T", "stdin": "1 2 3 | 1 2 3\n", "hidden": True},
        {"name": "hidden: empty T non-empty S", "stdin": "null | 1\n", "hidden": True},
        {"name": "hidden: value matches but shape does not", "stdin": "1 2 | 2 null 3\n", "hidden": True},
        {"name": "hidden: S is a proper prefix of a subtree", "stdin": "1 2 3 4 | 2\n", "hidden": True},
        {
            "name": "hidden: same values, child on the other side",
            "stdin": "1 2 3 null 4 | 2 4\n",
            "hidden": True,
        },
        {"name": "hidden: duplicate values everywhere", "stdin": "1 1 1 1 1 1 1 | 1 1 1\n", "hidden": True},
        {"name": "hidden: negatives", "stdin": "-1 -2 -3 null null -4 | -3 -4\n", "hidden": True},
        {"name": "hidden: scale present", "stdin": _subtree_case(161, 100000, 37, -1000, 1000), "hidden": True},
        {
            "name": "hidden: scale absent",
            "stdin": _random_tree(162, 100000, -1000, 1000) + " | " + _random_tree(163, 40, -1000, 1000) + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Matches on the root value of S occurring anywhere in T.
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    va, la, ra = parse_tree(parts[0])\n"
            "    vb, lb, rb = parse_tree(parts[1])\n"
            "    if not vb:\n"
            "        print('true')\n"
            "        return\n"
            "    print('true' if vb[0] in set(va) else 'false')\n"
            "main()\n"
        ),
        # Substring search on the serialised form: a match can straddle two
        # different subtrees, and a prefix of a longer subtree looks like a hit.
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    a = serialize(*parse_tree(parts[0]))\n"
            "    b = serialize(*parse_tree(parts[1]))\n"
            "    if b == 'null':\n"
            "        print('true')\n"
            "        return\n"
            "    print('true' if b in a else 'false')\n"
            "main()\n"
        ),
        # Compares the values of the candidate subtree in level order while
        # ignoring the null gaps, so different shapes compare equal.
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    va, la, ra = parse_tree(parts[0])\n"
            "    vb, lb, rb = parse_tree(parts[1])\n"
            "    if not vb:\n"
            "        print('true')\n"
            "        return\n"
            "    def values_from(val, left, right, root):\n"
            "        out = []\n"
            "        queue = [root]\n"
            "        head = 0\n"
            "        while head < len(queue):\n"
            "            node = queue[head]\n"
            "            head += 1\n"
            "            out.append(val[node])\n"
            "            if left[node] != -1:\n"
            "                queue.append(left[node])\n"
            "            if right[node] != -1:\n"
            "                queue.append(right[node])\n"
            "        return out\n"
            "    target = values_from(vb, lb, rb, 0)\n"
            "    for node in range(len(va)):\n"
            "        if va[node] == vb[0] and values_from(va, la, ra, node) == target:\n"
            "            print('true')\n"
            "            return\n"
            "    print('false')\n"
            "main()\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  08 · Construct a tree from preorder and inorder                            #
# --------------------------------------------------------------------------- #


def _traversal_case(seed: int, n: int) -> str:
    preorder, inorder = _traversals(seed, n)
    return " ".join(map(str, preorder)) + " | " + " ".join(map(str, inorder)) + "\n"


BUILD_TREE = {
    "slug": "construct-tree-from-preorder-and-inorder",
    "skill_id": "dsa_arrays",
    "difficulty": 7,
    "estimated_minutes": 40,
    "title": "Construct Binary Tree from Preorder and Inorder Traversal",
    "statement": (
        "Given the preorder and inorder traversals of a binary tree whose values "
        "are all distinct, rebuild the tree and print it.\n\n"
        "The two traversals arrive on one line, separated by a single `|`: "
        "preorder first, then inorder.\n\n" + _TREE_FORMAT + "\n\n"
        "Print the rebuilt tree in that canonical level-order format."
    ),
    "constraints": [
        "1 <= n <= 100000",
        "-1000000 <= value <= 1000000 and all values are distinct",
        "The two traversals are consistent: they describe exactly one tree",
        "The tree is at most 5000 levels deep",
        "Locating the root by scanning the inorder list every time is O(n^2) "
        "and will time out; index the positions once",
    ],
    "input_format": "One line: the preorder values, then `|`, then the inorder values.",
    "output_format": "One line: the rebuilt tree in canonical level-order token form.",
    "examples": [
        {
            "stdin": "3 9 20 15 7 | 9 3 15 20 7\n",
            "stdout": "3 9 20 null null 15 7",
            "explanation": "3 is the root; 9 sits left of it in the inorder list, and 15 20 7 to its right.",
        },
        {
            "stdin": "1 2 3 | 3 2 1\n",
            "stdout": "1 2 null 3",
            "explanation": "The inorder listing is fully reversed, so the tree is a left-leaning chain.",
        },
    ],
    "criteria": [
        "Handle a single-node tree",
        "Handle fully skewed trees in either direction",
        "Index the inorder positions instead of rescanning, so n = 100000 finishes",
    ],
    "io": {
        "mode": "line",
        "function": "build_tree",
        "todo": "rebuild the tree from the two traversals and print it in level-order form",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": _PY_TREE + (
        "def main():\n"
        "    parts = read_line().split('|')\n"
        "    pre = [int(x) for x in parts[0].split()]\n"
        "    ino = [int(x) for x in parts[1].split()]\n"
        "    n = len(pre)\n"
        "    pos = {value: index for index, value in enumerate(ino)}\n"
        "    val = list(pre)\n"
        "    left = [-1] * n\n"
        "    right = [-1] * n\n"
        "    stack = [(0, n - 1, 0, n - 1, -1, 0)]\n"
        "    while stack:\n"
        "        pl, ph, il, ih, parent, side = stack.pop()\n"
        "        if pl > ph:\n"
        "            continue\n"
        "        root = pl\n"
        "        if parent != -1:\n"
        "            if side == 0:\n"
        "                left[parent] = root\n"
        "            else:\n"
        "                right[parent] = root\n"
        "        cut = pos[pre[pl]]\n"
        "        size = cut - il\n"
        "        stack.append((pl + 1, pl + size, il, cut - 1, root, 0))\n"
        "        stack.append((pl + size + 1, ph, cut + 1, ih, root, 1))\n"
        "    print(serialize(val, left, right))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: classic", "stdin": "3 9 20 15 7 | 9 3 15 20 7\n", "hidden": False},
        {"name": "sample: left chain", "stdin": "1 2 3 | 3 2 1\n", "hidden": False},
        {"name": "hidden: single node", "stdin": "-5 | -5\n", "hidden": True},
        {"name": "hidden: right chain", "stdin": "1 2 3 4 | 1 2 3 4\n", "hidden": True},
        {"name": "hidden: negatives", "stdin": "-1 -2 -3 | -2 -1 -3\n", "hidden": True},
        {"name": "hidden: zigzag", "stdin": "1 2 3 4 | 2 4 3 1\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _traversal_case(171, 100000), "hidden": True},
    ],
    "wrong": [
        # Ignores the inorder list and inserts the preorder values as a BST.
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    pre = [int(x) for x in parts[0].split()]\n"
            "    n = len(pre)\n"
            "    val = list(pre)\n"
            "    left = [-1] * n\n"
            "    right = [-1] * n\n"
            "    for index in range(1, n):\n"
            "        cur = 0\n"
            "        while True:\n"
            "            if pre[index] < val[cur]:\n"
            "                if left[cur] == -1:\n"
            "                    left[cur] = index\n"
            "                    break\n"
            "                cur = left[cur]\n"
            "            else:\n"
            "                if right[cur] == -1:\n"
            "                    right[cur] = index\n"
            "                    break\n"
            "                cur = right[cur]\n"
            "    print(serialize(val, left, right))\n"
            "main()\n"
        ),
        # Splits the inorder list in the middle instead of at the root.
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    pre = [int(x) for x in parts[0].split()]\n"
            "    ino = [int(x) for x in parts[1].split()]\n"
            "    n = len(pre)\n"
            "    val = list(pre)\n"
            "    left = [-1] * n\n"
            "    right = [-1] * n\n"
            "    stack = [(0, n - 1, 0, n - 1, -1, 0)]\n"
            "    while stack:\n"
            "        pl, ph, il, ih, parent, side = stack.pop()\n"
            "        if pl > ph:\n"
            "            continue\n"
            "        root = pl\n"
            "        if parent != -1:\n"
            "            if side == 0:\n"
            "                left[parent] = root\n"
            "            else:\n"
            "                right[parent] = root\n"
            "        cut = (il + ih) // 2\n"
            "        size = cut - il\n"
            "        stack.append((pl + 1, pl + size, il, cut - 1, root, 0))\n"
            "        stack.append((pl + size + 1, ph, cut + 1, ih, root, 1))\n"
            "    print(serialize(val, left, right))\n"
            "main()\n"
        ),
        # Correct, but rescans the inorder list for every root: O(n^2).
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    pre = [int(x) for x in parts[0].split()]\n"
            "    ino = [int(x) for x in parts[1].split()]\n"
            "    n = len(pre)\n"
            "    val = list(pre)\n"
            "    left = [-1] * n\n"
            "    right = [-1] * n\n"
            "    stack = [(0, n - 1, 0, n - 1, -1, 0)]\n"
            "    while stack:\n"
            "        pl, ph, il, ih, parent, side = stack.pop()\n"
            "        if pl > ph:\n"
            "            continue\n"
            "        root = pl\n"
            "        if parent != -1:\n"
            "            if side == 0:\n"
            "                left[parent] = root\n"
            "            else:\n"
            "                right[parent] = root\n"
            "        cut = ino.index(pre[pl])\n"
            "        size = cut - il\n"
            "        stack.append((pl + 1, pl + size, il, cut - 1, root, 0))\n"
            "        stack.append((pl + size + 1, ph, cut + 1, ih, root, 1))\n"
            "    print(serialize(val, left, right))\n"
            "main()\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  09 · Validate a binary search tree                                         #
# --------------------------------------------------------------------------- #


def _broken_bst(seed: int, n: int) -> str:
    """A large BST whose only violation is deep and invisible to a parent check.

    The maximum of the root's left subtree is raised above the root. Its own
    parent is smaller than it, so every parent-child comparison still holds and
    only a solution that carries the ancestors' bounds down notices.
    """
    values = _bst_values(seed, n, -10**6, 10**6)
    val, left, right = _bst_arrays(values)
    node = left[0]
    while right[node] != -1:
        node = right[node]
    val[node] = 10**6
    return _serialize(val, left, right)


VALIDATE_BST = {
    "slug": "validate-binary-search-tree",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 30,
    "title": "Validate Binary Search Tree",
    "statement": (
        "Decide whether the given binary tree is a valid binary search tree. "
        "It is valid when, for every node, every value in its left subtree is "
        "strictly smaller than the node and every value in its right subtree is "
        "strictly larger. Equal values therefore make a tree invalid.\n\n"
        "The condition applies to whole subtrees, not just to a node's two "
        "immediate children.\n\n" + _TREE_FORMAT
    ),
    "constraints": _TREE_CONSTRAINTS + ["The empty tree is a valid BST"],
    "input_format": "One line: the tree in level-order token form.",
    "output_format": "`true` if the tree is a valid BST, otherwise `false`.",
    "examples": [
        {
            "stdin": "2 1 3\n",
            "stdout": "true",
            "explanation": "1 < 2 < 3, so the tree is a valid BST.",
        },
        {
            "stdin": "5 1 4 null null 3 6\n",
            "stdout": "false",
            "explanation": "3 is a legal left child of 4, but it sits in the right subtree of 5 and 3 < 5, so the tree is invalid.",
        },
    ],
    "criteria": [
        "Enforce the bound across a whole subtree, not just parent and child",
        "Reject duplicate values",
        "Accept the empty tree and a single node",
    ],
    "io": {
        "mode": "line",
        "function": "is_valid_bst",
        "todo": "parse the tree and return 1 if it is a valid binary search tree, else 0",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": _PY_TREE + (
        "def main():\n"
        "    val, left, right = parse_tree(read_line())\n"
        "    if not val:\n"
        "        print('true')\n"
        "        return\n"
        "    stack = []\n"
        "    node = 0\n"
        "    previous = None\n"
        "    ok = True\n"
        "    while stack or node != -1:\n"
        "        while node != -1:\n"
        "            stack.append(node)\n"
        "            node = left[node]\n"
        "        node = stack.pop()\n"
        "        if previous is not None and val[node] <= previous:\n"
        "            ok = False\n"
        "            break\n"
        "        previous = val[node]\n"
        "        node = right[node]\n"
        "    print('true' if ok else 'false')\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: valid", "stdin": "2 1 3\n", "hidden": False},
        {"name": "sample: invalid grandchild", "stdin": "5 1 4 null null 3 6\n", "hidden": False},
        {"name": "hidden: empty", "stdin": "null\n", "hidden": True},
        {"name": "hidden: single node", "stdin": "0\n", "hidden": True},
        {"name": "hidden: duplicate values", "stdin": "2 2 3\n", "hidden": True},
        {"name": "hidden: duplicate deeper", "stdin": "5 3 7 1 5\n", "hidden": True},
        {"name": "hidden: valid with negatives", "stdin": "-5 -10 -1 null null -3 0\n", "hidden": True},
        {"name": "hidden: descending left chain is valid", "stdin": "10 9 null 8 null null null 7\n", "hidden": True},
        {
            "name": "hidden: violation far from its parent",
            "stdin": "20 10 30 5 15 25 35 null null null null null 22\n",
            "hidden": True,
        },
        {"name": "hidden: scale valid", "stdin": _random_bst(181, 100000, -10**6, 10**6) + "\n", "hidden": True},
        {"name": "hidden: scale invalid", "stdin": _broken_bst(182, 100000) + "\n", "hidden": True},
    ],
    "wrong": [
        # Only compares a node against its immediate children.
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    ok = True\n"
            "    for node in range(len(val)):\n"
            "        if left[node] != -1 and val[left[node]] >= val[node]:\n"
            "            ok = False\n"
            "        if right[node] != -1 and val[right[node]] <= val[node]:\n"
            "            ok = False\n"
            "    print('true' if ok else 'false')\n"
            "main()\n"
        ),
        # In-order scan that permits equal neighbours.
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    if not val:\n"
            "        print('true')\n"
            "        return\n"
            "    stack = []\n"
            "    node = 0\n"
            "    previous = None\n"
            "    ok = True\n"
            "    while stack or node != -1:\n"
            "        while node != -1:\n"
            "            stack.append(node)\n"
            "            node = left[node]\n"
            "        node = stack.pop()\n"
            "        if previous is not None and val[node] < previous:\n"
            "            ok = False\n"
            "            break\n"
            "        previous = val[node]\n"
            "        node = right[node]\n"
            "    print('true' if ok else 'false')\n"
            "main()\n"
        ),
        # Carries only one bound down: the parent's, not the whole ancestry.
        _PY_TREE + (
            "def main():\n"
            "    val, left, right = parse_tree(read_line())\n"
            "    if not val:\n"
            "        print('true')\n"
            "        return\n"
            "    ok = True\n"
            "    stack = [(0, None, None)]\n"
            "    while stack:\n"
            "        node, low, high = stack.pop()\n"
            "        if low is not None and val[node] <= low:\n"
            "            ok = False\n"
            "            break\n"
            "        if high is not None and val[node] >= high:\n"
            "            ok = False\n"
            "            break\n"
            "        if left[node] != -1:\n"
            "            stack.append((left[node], None, val[node]))\n"
            "        if right[node] != -1:\n"
            "            stack.append((right[node], val[node], None))\n"
            "    print('true' if ok else 'false')\n"
            "main()\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  10 · Kth smallest element in a BST                                         #
# --------------------------------------------------------------------------- #


def _kth_case(seed: int, n: int, k: int) -> str:
    return f"{k} | " + _random_bst(seed, n, -10**6, 10**6) + "\n"


KTH_SMALLEST = {
    "slug": "kth-smallest-element-in-a-bst",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Kth Smallest Element in a BST",
    "statement": (
        "Given a valid binary search tree with distinct values, return its k-th "
        "smallest value, counting from 1.\n\n"
        "The line starts with k, then a `|`, then the tree.\n\n" + _TREE_FORMAT
    ),
    "constraints": [
        "1 <= n <= 100000 and 1 <= k <= n",
        "-1000000 <= value <= 1000000 and all values are distinct",
        "The tree is a valid BST and is at most 5000 levels deep",
        "k is 1-based: k = 1 asks for the smallest value",
    ],
    "input_format": "One line: k, then `|`, then the tree in level-order token form.",
    "output_format": "A single integer: the k-th smallest value.",
    "examples": [
        {
            "stdin": "1 | 3 1 4 null 2\n",
            "stdout": "1",
            "explanation": "In order the values are 1 2 3 4, so the first is 1.",
        },
        {
            "stdin": "3 | 5 3 6 2 4 null null 1\n",
            "stdout": "3",
            "explanation": "In order the values are 1 2 3 4 5 6, so the third is 3.",
        },
    ],
    "criteria": [
        "Count in sorted (in-order) order, not in traversal-by-level order",
        "Treat k as 1-based",
        "Stop once the k-th value is known instead of materialising every value",
    ],
    "io": {
        "mode": "line",
        "function": "kth_smallest",
        "todo": "parse k and the BST from the line and return the k-th smallest value",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "long",
    },
    "reference": _PY_TREE + (
        "def main():\n"
        "    parts = read_line().split('|')\n"
        "    k = int(parts[0].strip())\n"
        "    val, left, right = parse_tree(parts[1])\n"
        "    stack = []\n"
        "    node = 0\n"
        "    seen = 0\n"
        "    while stack or node != -1:\n"
        "        while node != -1:\n"
        "            stack.append(node)\n"
        "            node = left[node]\n"
        "        node = stack.pop()\n"
        "        seen += 1\n"
        "        if seen == k:\n"
        "            print(val[node])\n"
        "            return\n"
        "        node = right[node]\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: smallest", "stdin": "1 | 3 1 4 null 2\n", "hidden": False},
        {"name": "sample: third", "stdin": "3 | 5 3 6 2 4 null null 1\n", "hidden": False},
        {"name": "hidden: single node", "stdin": "1 | -4\n", "hidden": True},
        {"name": "hidden: largest", "stdin": "4 | 3 1 4 null 2\n", "hidden": True},
        {"name": "hidden: negatives", "stdin": "2 | -5 -10 -1 null null -3 0\n", "hidden": True},
        {"name": "hidden: left chain", "stdin": "2 | 10 9 null 8 null 7\n", "hidden": True},
        {"name": "hidden: right chain", "stdin": "3 | 1 null 2 null 3 null 4\n", "hidden": True},
        {"name": "hidden: scale k = 1", "stdin": _kth_case(191, 100000, 1), "hidden": True},
        {"name": "hidden: scale k deep", "stdin": _kth_case(192, 100000, 99999), "hidden": True},
    ],
    "wrong": [
        # Uses the k-th value in level order rather than in sorted order.
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    k = int(parts[0].strip())\n"
            "    val, left, right = parse_tree(parts[1])\n"
            "    print(val[k - 1])\n"
            "main()\n"
        ),
        # Treats k as 0-based.
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    k = int(parts[0].strip())\n"
            "    val, left, right = parse_tree(parts[1])\n"
            "    values = sorted(val)\n"
            "    print(values[k])\n"
            "main()\n"
        ),
        # Counts in reverse in-order, returning the k-th largest instead.
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    k = int(parts[0].strip())\n"
            "    val, left, right = parse_tree(parts[1])\n"
            "    stack = []\n"
            "    node = 0\n"
            "    seen = 0\n"
            "    while stack or node != -1:\n"
            "        while node != -1:\n"
            "            stack.append(node)\n"
            "            node = right[node]\n"
            "        node = stack.pop()\n"
            "        seen += 1\n"
            "        if seen == k:\n"
            "            print(val[node])\n"
            "            return\n"
            "        node = left[node]\n"
            "main()\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  11 · Lowest common ancestor of a BST                                       #
# --------------------------------------------------------------------------- #


def _lca_case(seed: int, n: int, pick_a: int, pick_b: int) -> str:
    values = _bst_values(seed, n, -10**6, 10**6)
    tree = _serialize(*_bst_arrays(values))
    p = values[pick_a % n]
    q = values[pick_b % n]
    return f"{p} {q} | {tree}\n"


LCA_BST = {
    "slug": "lowest-common-ancestor-of-a-bst",
    "skill_id": "dsa_arrays",
    "difficulty": 4,
    "estimated_minutes": 25,
    "title": "Lowest Common Ancestor of a Binary Search Tree",
    "statement": (
        "Given a valid binary search tree with distinct values and two values p "
        "and q that both occur in it, return the value of their lowest common "
        "ancestor: the deepest node that has both p and q in its subtree. A node "
        "counts as an ancestor of itself.\n\n"
        "The line starts with p and q, then a `|`, then the tree. p and q are "
        "given in no particular order — q may be smaller than p.\n\n" + _TREE_FORMAT
    ),
    "constraints": [
        "1 <= n <= 100000",
        "-1000000 <= value <= 1000000 and all values are distinct",
        "p and q both occur in the tree and may be equal to each other",
        "The tree is a valid BST and is at most 5000 levels deep",
        "p is not necessarily smaller than q",
    ],
    "input_format": "One line: p and q, then `|`, then the tree in level-order token form.",
    "output_format": "A single integer: the value of the lowest common ancestor.",
    "examples": [
        {
            "stdin": "2 8 | 6 2 8 0 4 7 9\n",
            "stdout": "6",
            "explanation": "2 lies in the left subtree of 6 and 8 in the right, so 6 is the deepest node containing both.",
        },
        {
            "stdin": "4 2 | 6 2 8 0 4 7 9\n",
            "stdout": "2",
            "explanation": "Here q is smaller than p, and 2 is an ancestor of 4, so the answer is 2 itself.",
        },
    ],
    "criteria": [
        "Handle p and q given in either order",
        "Return the node itself when one value is an ancestor of the other",
        "Use the BST ordering to descend instead of searching the whole tree",
    ],
    "io": {
        "mode": "line",
        "function": "lowest_common_ancestor",
        "todo": "parse p, q and the BST from the line and return the value of their lowest common ancestor",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "long",
    },
    "reference": _PY_TREE + (
        "def main():\n"
        "    parts = read_line().split('|')\n"
        "    head = parts[0].split()\n"
        "    p = int(head[0])\n"
        "    q = int(head[1])\n"
        "    if p > q:\n"
        "        p, q = q, p\n"
        "    val, left, right = parse_tree(parts[1])\n"
        "    node = 0\n"
        "    while True:\n"
        "        if q < val[node]:\n"
        "            node = left[node]\n"
        "        elif p > val[node]:\n"
        "            node = right[node]\n"
        "        else:\n"
        "            print(val[node])\n"
        "            return\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: split at the root", "stdin": "2 8 | 6 2 8 0 4 7 9\n", "hidden": False},
        {"name": "sample: reversed order, ancestor is one of them", "stdin": "4 2 | 6 2 8 0 4 7 9\n", "hidden": False},
        {"name": "hidden: same node twice", "stdin": "7 7 | 6 2 8 0 4 7 9\n", "hidden": True},
        {"name": "hidden: root is the answer", "stdin": "0 9 | 6 2 8 0 4 7 9\n", "hidden": True},
        {"name": "hidden: single node", "stdin": "3 3 | 3\n", "hidden": True},
        {"name": "hidden: negatives", "stdin": "-3 0 | -5 -10 -1 null null -3 0\n", "hidden": True},
        {"name": "hidden: left chain", "stdin": "7 9 | 10 9 null 8 null 7\n", "hidden": True},
        {"name": "hidden: descending pair on a chain", "stdin": "9 7 | 10 9 null 8 null 7\n", "hidden": True},
        {"name": "hidden: scale", "stdin": _lca_case(201, 100000, 5, 77777), "hidden": True},
        {"name": "hidden: scale reversed pair", "stdin": _lca_case(202, 100000, 99998, 3), "hidden": True},
    ],
    "wrong": [
        # Assumes p < q and never normalises the pair.
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    head = parts[0].split()\n"
            "    p = int(head[0])\n"
            "    q = int(head[1])\n"
            "    val, left, right = parse_tree(parts[1])\n"
            "    node = 0\n"
            "    while True:\n"
            "        if q < val[node]:\n"
            "            node = left[node]\n"
            "        elif p > val[node]:\n"
            "            node = right[node]\n"
            "        else:\n"
            "            print(val[node])\n"
            "            return\n"
            "main()\n"
        ),
        # Descends on p alone, forgetting that the split point is where p and q
        # stop agreeing.
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    head = parts[0].split()\n"
            "    p = int(head[0])\n"
            "    q = int(head[1])\n"
            "    if p > q:\n"
            "        p, q = q, p\n"
            "    val, left, right = parse_tree(parts[1])\n"
            "    node = 0\n"
            "    while val[node] != p:\n"
            "        node = left[node] if p < val[node] else right[node]\n"
            "    print(val[node])\n"
            "main()\n"
        ),
        # Descends only while both values are strictly on one side, but uses
        # >= so a node equal to p or q is stepped past.
        _PY_TREE + (
            "def main():\n"
            "    parts = read_line().split('|')\n"
            "    head = parts[0].split()\n"
            "    p = int(head[0])\n"
            "    q = int(head[1])\n"
            "    if p > q:\n"
            "        p, q = q, p\n"
            "    val, left, right = parse_tree(parts[1])\n"
            "    node = 0\n"
            "    while True:\n"
            "        if q <= val[node] and left[node] != -1:\n"
            "            node = left[node]\n"
            "        elif p >= val[node] and right[node] != -1:\n"
            "            node = right[node]\n"
            "        else:\n"
            "            print(val[node])\n"
            "            return\n"
            "main()\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  Command-stream helpers                                                     #
# --------------------------------------------------------------------------- #

_COMMAND_FORMAT = (
    "The whole session arrives on one line: first the number of operations m, "
    "then m operations, each separated from the next by ` ; ` (a semicolon). "
    "Operations are applied in order."
)


def _trie_stream(seed: int, ops: int, alphabet: str, max_len: int) -> str:
    """A trie session where every query misses.

    Queries end in `z`, a letter that never occurs in an inserted word, so no
    query can be answered early: a solution that scans the stored words per
    query has to look at all of them and runs far over the time limit, while a
    trie answers each one in the length of the word.
    """
    rng = _rng(seed)
    pool = ["".join(rng.choice(alphabet) for _ in range(rng.randint(1, max_len))) for _ in range(ops // 2)]
    commands = []
    for _ in range(ops):
        roll = rng.random()
        word = rng.choice(pool)
        if roll < 0.4:
            commands.append(f"insert {word}")
            continue
        miss = True
        if roll < 0.7:
            query = word[: max(1, len(word) - 1)] + "z" if miss else word
            commands.append(f"search {query}")
        else:
            prefix = word[: rng.randint(1, len(word))]
            if miss:
                prefix = prefix + "z"
            commands.append(f"startsWith {prefix}")
    return f"{len(commands)} ; " + " ; ".join(commands) + "\n"


def _dictionary_stream(seed: int, ops: int, alphabet: str, max_len: int) -> str:
    rng = _rng(seed)
    pool = ["".join(rng.choice(alphabet) for _ in range(rng.randint(1, max_len))) for _ in range(ops // 3)]
    commands = []
    for _ in range(ops):
        word = rng.choice(pool)
        roll = rng.random()
        if roll < 0.45:
            commands.append(f"addWord {word}")
        else:
            chars = list(word)
            for _ in range(rng.randint(0, min(3, len(chars)))):
                chars[rng.randrange(len(chars))] = "."
            commands.append("search " + "".join(chars))
    return f"{len(commands)} ; " + " ; ".join(commands) + "\n"


def _median_stream(seed: int, ops: int, lo: int, hi: int) -> str:
    rng = _rng(seed)
    commands = ["add " + str(rng.randint(lo, hi))]
    for _ in range(ops - 1):
        if rng.random() < 0.6:
            commands.append("add " + str(rng.randint(lo, hi)))
        else:
            commands.append("median")
    return f"{len(commands)} ; " + " ; ".join(commands) + "\n"


# --------------------------------------------------------------------------- #
#  12 · Implement a trie                                                      #
# --------------------------------------------------------------------------- #

IMPLEMENT_TRIE = {
    "slug": "implement-trie-prefix-tree",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 35,
    "title": "Implement Trie (Prefix Tree)",
    "statement": (
        "Build a prefix tree and drive it from a stream of commands.\n\n"
        + _COMMAND_FORMAT
        + "\n\nThe three operations are:\n"
        "  * `insert w` — add the word w. Prints nothing.\n"
        "  * `search w` — print `true` if w was inserted as a whole word, else `false`.\n"
        "  * `startsWith p` — print `true` if any inserted word begins with p, else `false`.\n\n"
        "So `search` and `startsWith` each print exactly one line, in the order "
        "the operations appear, and `insert` prints nothing. Note the difference: "
        "`search app` is false until `app` itself is inserted, even if `apple` is "
        "already there, while `startsWith app` is already true."
    ),
    "constraints": [
        "1 <= m <= 100000",
        "Words and prefixes are non-empty, at most 20 characters, lowercase a-z",
        "The total number of characters over all operations is at most 1500000",
        "Scanning every inserted word per query is O(m^2) and will time out",
    ],
    "input_format": "One line: m, then m operations separated by ` ; `.",
    "output_format": "One line (`true` or `false`) per `search` and per `startsWith` operation, in order.",
    "examples": [
        {
            "stdin": "5 ; insert apple ; search apple ; search app ; startsWith app ; insert app\n",
            "stdout": "true\nfalse\ntrue",
            "explanation": "`apple` was inserted, so searching it is true; `app` is only a prefix so far, so `search app` is false while `startsWith app` is true. The two inserts print nothing.",
        },
        {
            "stdin": "4 ; startsWith a ; insert ab ; search ab ; startsWith abc\n",
            "stdout": "false\ntrue\nfalse",
            "explanation": "The first query runs against an empty trie. After inserting `ab`, searching it is true, but nothing starts with `abc`.",
        },
    ],
    "criteria": [
        "Keep an end-of-word marker so `search` is not satisfied by a prefix",
        "Answer queries against the trie in time proportional to the word length",
        "Handle a query issued before anything has been inserted",
    ],
    "io": {
        "mode": "line",
        "function": "run_trie",
        "todo": "parse the command stream and print one line per search and startsWith operation",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    line = sys.stdin.readline().rstrip('\\n')\n"
        "    parts = [p.strip() for p in line.split(';')]\n"
        "    children = [{}]\n"
        "    terminal = [False]\n"
        "    out = []\n"
        "    for command in parts[1:]:\n"
        "        if not command:\n"
        "            continue\n"
        "        op, _, word = command.partition(' ')\n"
        "        word = word.strip()\n"
        "        if op == 'insert':\n"
        "            node = 0\n"
        "            for ch in word:\n"
        "                nxt = children[node].get(ch)\n"
        "                if nxt is None:\n"
        "                    children.append({})\n"
        "                    terminal.append(False)\n"
        "                    nxt = len(children) - 1\n"
        "                    children[node][ch] = nxt\n"
        "                node = nxt\n"
        "            terminal[node] = True\n"
        "            continue\n"
        "        node = 0\n"
        "        ok = True\n"
        "        for ch in word:\n"
        "            nxt = children[node].get(ch)\n"
        "            if nxt is None:\n"
        "                ok = False\n"
        "                break\n"
        "            node = nxt\n"
        "        if op == 'search':\n"
        "            ok = ok and terminal[node]\n"
        "        out.append('true' if ok else 'false')\n"
        "    sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        "main()\n"
    ),
    "inputs": [
        {
            "name": "sample: apple and app",
            "stdin": "5 ; insert apple ; search apple ; search app ; startsWith app ; insert app\n",
            "hidden": False,
        },
        {
            "name": "sample: query before insert",
            "stdin": "4 ; startsWith a ; insert ab ; search ab ; startsWith abc\n",
            "hidden": False,
        },
        {"name": "hidden: only inserts", "stdin": "2 ; insert a ; insert b\n", "hidden": True},
        {
            "name": "hidden: word becomes searchable after later insert",
            "stdin": "6 ; insert apple ; search app ; insert app ; search app ; search appl ; startsWith appl\n",
            "hidden": True,
        },
        {
            "name": "hidden: prefix is not a word",
            "stdin": "5 ; insert abcdef ; search abc ; startsWith abc ; search abcdef ; startsWith abcdefg\n",
            "hidden": True,
        },
        {
            "name": "hidden: repeated inserts and single letters",
            "stdin": "7 ; insert a ; insert a ; search a ; startsWith a ; insert ab ; search a ; search ab\n",
            "hidden": True,
        },
        {
            "name": "hidden: sibling branches do not leak",
            "stdin": "6 ; insert cat ; insert car ; search ca ; startsWith ca ; search cat ; search cab\n",
            "hidden": True,
        },
        {"name": "hidden: scale", "stdin": _trie_stream(211, 100000, "abcd", 12), "hidden": True},
    ],
    "wrong": [
        # startsWith implemented as an exact search.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "parts = [p.strip() for p in line.split(';')]\n"
            "words = set()\n"
            "out = []\n"
            "for command in parts[1:]:\n"
            "    if not command:\n"
            "        continue\n"
            "    op, _, word = command.partition(' ')\n"
            "    word = word.strip()\n"
            "    if op == 'insert':\n"
            "        words.add(word)\n"
            "    else:\n"
            "        out.append('true' if word in words else 'false')\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
        # No end-of-word marker, so search accepts any prefix.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "parts = [p.strip() for p in line.split(';')]\n"
            "children = [{}]\n"
            "out = []\n"
            "for command in parts[1:]:\n"
            "    if not command:\n"
            "        continue\n"
            "    op, _, word = command.partition(' ')\n"
            "    word = word.strip()\n"
            "    if op == 'insert':\n"
            "        node = 0\n"
            "        for ch in word:\n"
            "            nxt = children[node].get(ch)\n"
            "            if nxt is None:\n"
            "                children.append({})\n"
            "                nxt = len(children) - 1\n"
            "                children[node][ch] = nxt\n"
            "            node = nxt\n"
            "        continue\n"
            "    node = 0\n"
            "    ok = True\n"
            "    for ch in word:\n"
            "        nxt = children[node].get(ch)\n"
            "        if nxt is None:\n"
            "            ok = False\n"
            "            break\n"
            "        node = nxt\n"
            "    out.append('true' if ok else 'false')\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
        # Correct, but rescans every stored word per query: too slow at scale.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "parts = [p.strip() for p in line.split(';')]\n"
            "words = []\n"
            "out = []\n"
            "for command in parts[1:]:\n"
            "    if not command:\n"
            "        continue\n"
            "    op, _, word = command.partition(' ')\n"
            "    word = word.strip()\n"
            "    if op == 'insert':\n"
            "        words.append(word)\n"
            "    elif op == 'search':\n"
            "        out.append('true' if any(w == word for w in words) else 'false')\n"
            "    else:\n"
            "        out.append('true' if any(w.startswith(word) for w in words) else 'false')\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  13 · Add and search words                                                  #
# --------------------------------------------------------------------------- #

WORD_DICTIONARY = {
    "slug": "add-and-search-words-data-structure",
    "skill_id": "dsa_arrays",
    "difficulty": 7,
    "estimated_minutes": 40,
    "title": "Design Add and Search Words Data Structure",
    "statement": (
        "Build a word dictionary that supports wildcard search, driven by a "
        "stream of commands.\n\n" + _COMMAND_FORMAT + "\n\nThe two operations are:\n"
        "  * `addWord w` — add the word w. Prints nothing.\n"
        "  * `search p` — print `true` if some added word matches the pattern p, "
        "else `false`.\n\n"
        "A pattern matches a word only if they have the same length and every "
        "character agrees, where a `.` in the pattern matches any single "
        "character. A `.` never matches zero characters and never matches more "
        "than one, so `.` matches `a` but not `ab`.\n\n"
        "`search` prints exactly one line per occurrence, in order; `addWord` "
        "prints nothing."
    ),
    "constraints": [
        "1 <= m <= 20000",
        "Words are non-empty, at most 12 characters, lowercase a-z",
        "A pattern is at most 12 characters of lowercase a-z and `.`, with at most 3 dots",
        "Comparing every stored word against every pattern is too slow at the top of the range",
    ],
    "input_format": "One line: m, then m operations separated by ` ; `.",
    "output_format": "One line (`true` or `false`) per `search` operation, in order.",
    "examples": [
        {
            "stdin": "5 ; addWord bad ; search bad ; search .ad ; search b.. ; search b.\n",
            "stdout": "true\ntrue\ntrue\nfalse",
            "explanation": "`bad` matches itself, `.ad` and `b..`. The pattern `b.` has length 2 and cannot match a three-letter word.",
        },
        {
            "stdin": "4 ; addWord dad ; addWord mad ; search pad ; search ..d\n",
            "stdout": "false\ntrue",
            "explanation": "No word `pad` was added. The pattern `..d` matches both `dad` and `mad`, so it is true.",
        },
    ],
    "criteria": [
        "Match `.` against exactly one character",
        "Require the pattern and the word to be the same length",
        "Explore the trie branches a `.` opens up instead of comparing every word",
    ],
    "io": {
        "mode": "line",
        "function": "run_dictionary",
        "todo": "parse the command stream and print one line per search operation",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    line = sys.stdin.readline().rstrip('\\n')\n"
        "    parts = [p.strip() for p in line.split(';')]\n"
        "    children = [{}]\n"
        "    terminal = [False]\n"
        "    out = []\n"
        "    for command in parts[1:]:\n"
        "        if not command:\n"
        "            continue\n"
        "        op, _, word = command.partition(' ')\n"
        "        word = word.strip()\n"
        "        if op == 'addWord':\n"
        "            node = 0\n"
        "            for ch in word:\n"
        "                nxt = children[node].get(ch)\n"
        "                if nxt is None:\n"
        "                    children.append({})\n"
        "                    terminal.append(False)\n"
        "                    nxt = len(children) - 1\n"
        "                    children[node][ch] = nxt\n"
        "                node = nxt\n"
        "            terminal[node] = True\n"
        "            continue\n"
        "        found = False\n"
        "        stack = [(0, 0)]\n"
        "        while stack:\n"
        "            node, index = stack.pop()\n"
        "            if index == len(word):\n"
        "                if terminal[node]:\n"
        "                    found = True\n"
        "                    break\n"
        "                continue\n"
        "            ch = word[index]\n"
        "            if ch == '.':\n"
        "                for nxt in children[node].values():\n"
        "                    stack.append((nxt, index + 1))\n"
        "            else:\n"
        "                nxt = children[node].get(ch)\n"
        "                if nxt is not None:\n"
        "                    stack.append((nxt, index + 1))\n"
        "        out.append('true' if found else 'false')\n"
        "    sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        "main()\n"
    ),
    "inputs": [
        {
            "name": "sample: bad",
            "stdin": "5 ; addWord bad ; search bad ; search .ad ; search b.. ; search b.\n",
            "hidden": False,
        },
        {
            "name": "sample: two words",
            "stdin": "4 ; addWord dad ; addWord mad ; search pad ; search ..d\n",
            "hidden": False,
        },
        {"name": "hidden: search before any add", "stdin": "2 ; search . ; addWord a\n", "hidden": True},
        {"name": "hidden: all dots", "stdin": "4 ; addWord abc ; search ... ; search .. ; search ....\n", "hidden": True},
        {
            "name": "hidden: single letter words",
            "stdin": "5 ; addWord a ; search a ; search . ; search b ; search ..\n",
            "hidden": True,
        },
        {
            "name": "hidden: dot must not match a prefix",
            "stdin": "4 ; addWord abcd ; search ab ; search abc. ; search .bcd\n",
            "hidden": True,
        },
        {
            "name": "hidden: branch choice matters",
            "stdin": "5 ; addWord axz ; addWord ayw ; search a.w ; search a.z ; search a.q\n",
            "hidden": True,
        },
        {"name": "hidden: scale", "stdin": _dictionary_stream(221, 20000, "abcde", 8), "hidden": True},
    ],
    "wrong": [
        # Treats '.' as an ordinary character.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "parts = [p.strip() for p in line.split(';')]\n"
            "words = set()\n"
            "out = []\n"
            "for command in parts[1:]:\n"
            "    if not command:\n"
            "        continue\n"
            "    op, _, word = command.partition(' ')\n"
            "    word = word.strip()\n"
            "    if op == 'addWord':\n"
            "        words.add(word)\n"
            "    else:\n"
            "        out.append('true' if word in words else 'false')\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
        # Ignores the length requirement: a pattern that matches a prefix wins.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "parts = [p.strip() for p in line.split(';')]\n"
            "words = []\n"
            "out = []\n"
            "for command in parts[1:]:\n"
            "    if not command:\n"
            "        continue\n"
            "    op, _, word = command.partition(' ')\n"
            "    word = word.strip()\n"
            "    if op == 'addWord':\n"
            "        words.append(word)\n"
            "    else:\n"
            "        hit = False\n"
            "        for w in words:\n"
            "            if len(w) < len(word):\n"
            "                continue\n"
            "            if all(c == '.' or c == w[i] for i, c in enumerate(word)):\n"
            "                hit = True\n"
            "                break\n"
            "        out.append('true' if hit else 'false')\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
        # Only ever follows the first branch a '.' offers.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "parts = [p.strip() for p in line.split(';')]\n"
            "children = [{}]\n"
            "terminal = [False]\n"
            "out = []\n"
            "for command in parts[1:]:\n"
            "    if not command:\n"
            "        continue\n"
            "    op, _, word = command.partition(' ')\n"
            "    word = word.strip()\n"
            "    if op == 'addWord':\n"
            "        node = 0\n"
            "        for ch in word:\n"
            "            nxt = children[node].get(ch)\n"
            "            if nxt is None:\n"
            "                children.append({})\n"
            "                terminal.append(False)\n"
            "                nxt = len(children) - 1\n"
            "                children[node][ch] = nxt\n"
            "            node = nxt\n"
            "        terminal[node] = True\n"
            "        continue\n"
            "    node = 0\n"
            "    ok = True\n"
            "    for ch in word:\n"
            "        if ch == '.':\n"
            "            options = sorted(children[node])\n"
            "            if not options:\n"
            "                ok = False\n"
            "                break\n"
            "            node = children[node][options[0]]\n"
            "        else:\n"
            "            nxt = children[node].get(ch)\n"
            "            if nxt is None:\n"
            "                ok = False\n"
            "                break\n"
            "            node = nxt\n"
            "    out.append('true' if ok and terminal[node] else 'false')\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  14 · Word search II                                                        #
# --------------------------------------------------------------------------- #


def _word_search_ii_case(seed: int, rows: int, cols: int, alphabet: str, count: int) -> str:
    grid = _random_grid(seed, rows, cols, alphabet)
    words = _random_words(seed + 1, count, 3, 8, alphabet)
    unique = sorted(set(words))
    return f"{rows} {cols} | " + " ".join(grid) + " | " + " ".join(unique) + "\n"


WORD_SEARCH_II = {
    "slug": "word-search-ii",
    "skill_id": "dsa_arrays",
    "difficulty": 9,
    "estimated_minutes": 55,
    "title": "Word Search II",
    "statement": (
        "Given a grid of lowercase letters and a list of words, report every "
        "word that can be built from letters of sequentially adjacent cells, "
        "where adjacent means horizontally or vertically neighbouring. A single "
        "cell may not be used twice within one word.\n\n"
        "The line has three sections separated by `|`: the grid dimensions "
        "`R C`, then the R rows of the grid, then the words.\n\n"
        "Print the matching words in ascending lexicographic order, one per "
        "line, each word at most once. If no word matches, print nothing."
    ),
    "constraints": [
        "1 <= R, C <= 12",
        "1 <= number of words <= 1000; the words are distinct",
        "Word lengths are between 1 and 10; all letters are lowercase a-z",
        "Searching the grid separately for every word is too slow: share the "
        "work with a trie",
        "Output must be sorted lexicographically, which makes the answer unique",
    ],
    "input_format": "One line: `R C`, then `|`, then R rows, then `|`, then the words.",
    "output_format": "The matching words in ascending lexicographic order, one per line. Nothing if there are none.",
    "examples": [
        {
            "stdin": "4 4 | oaan etae ihkr iflv | oath pea eat rain\n",
            "stdout": "eat\noath",
            "explanation": "`oath` runs down and across from the top-left, and `eat` is present too. `pea` and `rain` cannot be traced, and the two hits are printed in lexicographic order, so `eat` comes first.",
        },
        {
            "stdin": "1 3 | abc | ab ba abc cba ac\n",
            "stdout": "ab\nabc\nba\ncba",
            "explanation": "A path may walk left as well as right, so `ba` and `cba` are traceable too; only `ac` fails, because a and c are not adjacent. The four hits are printed sorted.",
        },
    ],
    "criteria": [
        "Never reuse a cell within one word",
        "Only allow horizontal and vertical steps",
        "Print each matching word once, sorted lexicographically",
    ],
    "io": {
        "mode": "line",
        "function": "find_words",
        "todo": "parse the grid and words, then print every word found in the grid, sorted",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    line = sys.stdin.readline().rstrip('\\n')\n"
        "    head, grid_part, words_part = line.split('|')\n"
        "    rows, cols = (int(x) for x in head.split())\n"
        "    grid = grid_part.split()\n"
        "    words = words_part.split()\n"
        "    children = [{}]\n"
        "    word_at = [None]\n"
        "    for word in words:\n"
        "        node = 0\n"
        "        for ch in word:\n"
        "            nxt = children[node].get(ch)\n"
        "            if nxt is None:\n"
        "                children.append({})\n"
        "                word_at.append(None)\n"
        "                nxt = len(children) - 1\n"
        "                children[node][ch] = nxt\n"
        "            node = nxt\n"
        "        word_at[node] = word\n"
        "    found = set()\n"
        "    used = [[False] * cols for _ in range(rows)]\n"
        "    sys.setrecursionlimit(10000)\n"
        "\n"
        "    def walk(r, c, node):\n"
        "        ch = grid[r][c]\n"
        "        nxt = children[node].get(ch)\n"
        "        if nxt is None:\n"
        "            return\n"
        "        if word_at[nxt] is not None:\n"
        "            found.add(word_at[nxt])\n"
        "        used[r][c] = True\n"
        "        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n"
        "            nr, nc = r + dr, c + dc\n"
        "            if 0 <= nr < rows and 0 <= nc < cols and not used[nr][nc]:\n"
        "                walk(nr, nc, nxt)\n"
        "        used[r][c] = False\n"
        "\n"
        "    for r in range(rows):\n"
        "        for c in range(cols):\n"
        "            walk(r, c, 0)\n"
        "    out = sorted(found)\n"
        "    sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: classic grid", "stdin": "4 4 | oaan etae ihkr iflv | oath pea eat rain\n", "hidden": False},
        {"name": "sample: single row", "stdin": "1 3 | abc | ab ba abc cba ac\n", "hidden": False},
        {"name": "hidden: no matches", "stdin": "2 2 | ab cd | zz xy\n", "hidden": True},
        {"name": "hidden: single cell", "stdin": "1 1 | a | a aa b\n", "hidden": True},
        {
            "name": "hidden: cell reuse would be needed",
            "stdin": "2 2 | ab ab | aba abab abba\n",
            "hidden": True,
        },
        {
            "name": "hidden: diagonal steps are illegal",
            "stdin": "2 2 | ab cd | ad ac ab\n",
            "hidden": True,
        },
        {
            "name": "hidden: full word list matches, order tested",
            "stdin": "3 3 | aaa aaa aaa | a aa aaa aaaa aaaaaaaaaa aaaaaaaaaaa\n",
            "hidden": True,
        },
        {"name": "hidden: scale", "stdin": _word_search_ii_case(231, 12, 12, "abcd", 1000), "hidden": True},
    ],
    "wrong": [
        # Checks only that the letters exist somewhere in the grid.
        (
            "import sys\n"
            "from collections import Counter\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, grid_part, words_part = line.split('|')\n"
            "available = Counter(''.join(grid_part.split()))\n"
            "out = []\n"
            "for word in sorted(set(words_part.split())):\n"
            "    need = Counter(word)\n"
            "    if all(available[ch] >= n for ch, n in need.items()):\n"
            "        out.append(word)\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
        # Allows a cell to be reused inside one word.
        (
            "import sys\n"
            "sys.setrecursionlimit(10000)\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, grid_part, words_part = line.split('|')\n"
            "rows, cols = (int(x) for x in head.split())\n"
            "grid = grid_part.split()\n"
            "def walk(r, c, word, index):\n"
            "    if grid[r][c] != word[index]:\n"
            "        return False\n"
            "    if index == len(word) - 1:\n"
            "        return True\n"
            "    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n"
            "        nr, nc = r + dr, c + dc\n"
            "        if 0 <= nr < rows and 0 <= nc < cols and walk(nr, nc, word, index + 1):\n"
            "            return True\n"
            "    return False\n"
            "out = []\n"
            "for word in sorted(set(words_part.split())):\n"
            "    if any(walk(r, c, word, 0) for r in range(rows) for c in range(cols)):\n"
            "        out.append(word)\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
        # Correct search, but prints the hits in the order the words were given.
        (
            "import sys\n"
            "sys.setrecursionlimit(10000)\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, grid_part, words_part = line.split('|')\n"
            "rows, cols = (int(x) for x in head.split())\n"
            "grid = grid_part.split()\n"
            "used = [[False] * cols for _ in range(rows)]\n"
            "def walk(r, c, word, index):\n"
            "    if grid[r][c] != word[index]:\n"
            "        return False\n"
            "    if index == len(word) - 1:\n"
            "        return True\n"
            "    used[r][c] = True\n"
            "    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n"
            "        nr, nc = r + dr, c + dc\n"
            "        if 0 <= nr < rows and 0 <= nc < cols and not used[nr][nc]:\n"
            "            if walk(nr, nc, word, index + 1):\n"
            "                used[r][c] = False\n"
            "                return True\n"
            "    used[r][c] = False\n"
            "    return False\n"
            "out = []\n"
            "for word in words_part.split():\n"
            "    if any(walk(r, c, word, 0) for r in range(rows) for c in range(cols)):\n"
            "        out.append(word)\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  15 · Top K frequent elements                                               #
# --------------------------------------------------------------------------- #


def _top_k_case(seed: int, k: int, n: int, lo: int, hi: int) -> str:
    rng = _rng(seed)
    values = [rng.randint(lo, hi) for _ in range(n)]
    return f"{k} | " + " ".join(map(str, values)) + "\n"


TOP_K_FREQUENT = {
    "slug": "top-k-frequent-elements",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Top K Frequent Elements",
    "statement": (
        "Given a list of integers, report the k values that occur most often.\n\n"
        "Ties are resolved so that the answer is unique: order the values by "
        "descending frequency, and where two values occur equally often, put the "
        "smaller value first. Print the first k values of that ordering.\n\n"
        "The line starts with k, then a `|`, then the values."
    ),
    "constraints": [
        "1 <= n <= 200000",
        "-1000000000 <= value <= 1000000000",
        "1 <= k <= number of distinct values",
        "Ties are broken by the smaller value first, so the output is unique",
    ],
    "input_format": "One line: k, then `|`, then the n values separated by spaces.",
    "output_format": "One line: the k values, most frequent first, separated by single spaces.",
    "examples": [
        {
            "stdin": "2 | 1 1 1 2 2 3\n",
            "stdout": "1 2",
            "explanation": "1 occurs three times and 2 twice, so those are the two most frequent.",
        },
        {
            "stdin": "2 | 5 3 5 3 9 1\n",
            "stdout": "3 5",
            "explanation": "3 and 5 both occur twice; the tie is broken by value, so 3 comes first.",
        },
    ],
    "criteria": [
        "Break frequency ties by the smaller value",
        "Print values, not their counts",
        "Handle k equal to the number of distinct values",
    ],
    "io": {
        "mode": "line",
        "function": "top_k_frequent",
        "todo": "parse k and the values, then print the k most frequent values in the required order",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "from collections import Counter\n"
        "def main():\n"
        "    line = sys.stdin.readline().rstrip('\\n')\n"
        "    head, values_part = line.split('|')\n"
        "    k = int(head.strip())\n"
        "    counts = Counter(int(x) for x in values_part.split())\n"
        "    order = sorted(counts.items(), key=lambda item: (-item[1], item[0]))\n"
        "    print(' '.join(str(value) for value, _ in order[:k]))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: clear winner", "stdin": "2 | 1 1 1 2 2 3\n", "hidden": False},
        {"name": "sample: tie broken by value", "stdin": "2 | 5 3 5 3 9 1\n", "hidden": False},
        {"name": "hidden: single value", "stdin": "1 | 7\n", "hidden": True},
        {"name": "hidden: all distinct, k = 3", "stdin": "3 | 9 4 7 1 3\n", "hidden": True},
        {"name": "hidden: negatives tie", "stdin": "3 | -1 -1 -2 -2 -3 -3\n", "hidden": True},
        {"name": "hidden: k equals distinct count", "stdin": "4 | 4 4 3 3 2 2 1\n", "hidden": True},
        {"name": "hidden: large magnitudes", "stdin": "2 | 1000000000 -1000000000 1000000000\n", "hidden": True},
        {"name": "hidden: scale heavy ties", "stdin": _top_k_case(241, 50, 200000, -1000, 1000), "hidden": True},
        {"name": "hidden: scale wide spread", "stdin": _top_k_case(242, 3, 200000, -10**9, 10**9), "hidden": True},
    ],
    "wrong": [
        # Counter.most_common breaks ties by first appearance, not by value.
        (
            "import sys\n"
            "from collections import Counter\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, values_part = line.split('|')\n"
            "k = int(head.strip())\n"
            "counts = Counter(int(x) for x in values_part.split())\n"
            "print(' '.join(str(v) for v, _ in counts.most_common(k)))\n"
        ),
        # Breaks ties by the larger value.
        (
            "import sys\n"
            "from collections import Counter\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, values_part = line.split('|')\n"
            "k = int(head.strip())\n"
            "counts = Counter(int(x) for x in values_part.split())\n"
            "order = sorted(counts.items(), key=lambda item: (-item[1], -item[0]))\n"
            "print(' '.join(str(v) for v, _ in order[:k]))\n"
        ),
        # Prints the counts instead of the values.
        (
            "import sys\n"
            "from collections import Counter\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, values_part = line.split('|')\n"
            "k = int(head.strip())\n"
            "counts = Counter(int(x) for x in values_part.split())\n"
            "order = sorted(counts.items(), key=lambda item: (-item[1], item[0]))\n"
            "print(' '.join(str(c) for _, c in order[:k]))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  16 · Find median from a data stream                                        #
# --------------------------------------------------------------------------- #

MEDIAN_STREAM = {
    "slug": "find-median-from-data-stream",
    "skill_id": "dsa_arrays",
    "difficulty": 7,
    "estimated_minutes": 40,
    "title": "Find Median from Data Stream",
    "statement": (
        "Maintain a growing collection of numbers and report its median on "
        "demand.\n\n" + _COMMAND_FORMAT + "\n\nThe two operations are:\n"
        "  * `add x` — add the integer x to the collection. Prints nothing.\n"
        "  * `median` — print the median of everything added so far.\n\n"
        "The median of an odd number of values is the middle value; for an even "
        "number it is the mean of the two middle values. Print it with exactly "
        "one digit after the decimal point, so an integral median prints as "
        "`4.0` and a half prints as `2.5`. Since every value is an integer, one "
        "decimal place is always exact.\n\n"
        "`median` is never the first operation, so the collection is never empty "
        "when it is asked for."
    ),
    "constraints": [
        "1 <= m <= 100000",
        "-1000000 <= x <= 1000000",
        "The first operation is always an `add`",
        "Re-sorting the collection on every `median` is too slow at the top of the range",
        "Print the median with exactly one digit after the decimal point",
    ],
    "input_format": "One line: m, then m operations separated by ` ; `.",
    "output_format": "One line per `median` operation: the median with exactly one decimal digit.",
    "examples": [
        {
            "stdin": "5 ; add 1 ; add 2 ; median ; add 3 ; median\n",
            "stdout": "1.5\n2.0",
            "explanation": "After 1 and 2 the median is the mean of the two, 1.5. After adding 3 the middle value is 2, printed as 2.0.",
        },
        {
            "stdin": "4 ; add -5 ; median ; add -6 ; median\n",
            "stdout": "-5.0\n-5.5",
            "explanation": "A single value is its own median; then the two middle values -6 and -5 average to -5.5.",
        },
    ],
    "criteria": [
        "Average the two middle values for an even count",
        "Print exactly one decimal digit, including for an integral median",
        "Answer each `median` in O(log n), not by sorting again",
    ],
    "io": {
        "mode": "line",
        "function": "run_median_stream",
        "todo": "parse the command stream and print the median after each median operation",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "import heapq\n"
        "def main():\n"
        "    line = sys.stdin.readline().rstrip('\\n')\n"
        "    parts = [p.strip() for p in line.split(';')]\n"
        "    low = []\n"
        "    high = []\n"
        "    out = []\n"
        "    for command in parts[1:]:\n"
        "        if not command:\n"
        "            continue\n"
        "        if command.startswith('add'):\n"
        "            value = int(command.split()[1])\n"
        "            heapq.heappush(low, -value)\n"
        "            heapq.heappush(high, -heapq.heappop(low))\n"
        "            if len(high) > len(low):\n"
        "                heapq.heappush(low, -heapq.heappop(high))\n"
        "            continue\n"
        "        if len(low) > len(high):\n"
        "            out.append('%.1f' % float(-low[0]))\n"
        "        else:\n"
        "            out.append('%.1f' % ((-low[0] + high[0]) / 2.0))\n"
        "    sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: two then three", "stdin": "5 ; add 1 ; add 2 ; median ; add 3 ; median\n", "hidden": False},
        {"name": "sample: negatives", "stdin": "4 ; add -5 ; median ; add -6 ; median\n", "hidden": False},
        {"name": "hidden: single add", "stdin": "2 ; add 42 ; median\n", "hidden": True},
        {"name": "hidden: no median asked", "stdin": "2 ; add 1 ; add 2\n", "hidden": True},
        {
            "name": "hidden: duplicates",
            "stdin": "7 ; add 5 ; add 5 ; median ; add 5 ; median ; add 5 ; median\n",
            "hidden": True,
        },
        {
            "name": "hidden: descending inserts",
            "stdin": "9 ; add 9 ; median ; add 8 ; median ; add 7 ; median ; add 6 ; median ; add 5\n",
            "hidden": True,
        },
        {
            "name": "hidden: straddling zero",
            "stdin": "8 ; add -1000000 ; add 1000000 ; median ; add 0 ; median ; add 1 ; median ; median\n",
            "hidden": True,
        },
        {"name": "hidden: scale", "stdin": _median_stream(251, 100000, -10**6, 10**6), "hidden": True},
    ],
    "wrong": [
        # Integer median: never reports the .5 between two middle values.
        (
            "import sys\n"
            "import bisect\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "parts = [p.strip() for p in line.split(';')]\n"
            "values = []\n"
            "out = []\n"
            "for command in parts[1:]:\n"
            "    if not command:\n"
            "        continue\n"
            "    if command.startswith('add'):\n"
            "        bisect.insort(values, int(command.split()[1]))\n"
            "        continue\n"
            "    out.append('%.1f' % float(values[len(values) // 2]))\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
        # Reports the mean instead of the median.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "parts = [p.strip() for p in line.split(';')]\n"
            "values = []\n"
            "out = []\n"
            "for command in parts[1:]:\n"
            "    if not command:\n"
            "        continue\n"
            "    if command.startswith('add'):\n"
            "        values.append(int(command.split()[1]))\n"
            "        continue\n"
            "    out.append('%.1f' % (sum(values) / float(len(values))))\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
        # Correct, but sorts the whole collection on every query.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "parts = [p.strip() for p in line.split(';')]\n"
            "values = []\n"
            "out = []\n"
            "for command in parts[1:]:\n"
            "    if not command:\n"
            "        continue\n"
            "    if command.startswith('add'):\n"
            "        values.append(int(command.split()[1]))\n"
            "        continue\n"
            "    ordered = sorted(values)\n"
            "    mid = len(ordered) // 2\n"
            "    if len(ordered) % 2:\n"
            "        out.append('%.1f' % float(ordered[mid]))\n"
            "    else:\n"
            "        out.append('%.1f' % ((ordered[mid - 1] + ordered[mid]) / 2.0))\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  17 · Combination sum                                                       #
# --------------------------------------------------------------------------- #

COMBINATION_SUM = {
    "slug": "combination-sum",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 40,
    "title": "Combination Sum",
    "statement": (
        "Given a set of distinct positive candidate numbers and a target, list "
        "every combination of candidates that sums to the target. A candidate "
        "may be used any number of times, and two combinations are different "
        "only if they use some candidate a different number of times.\n\n"
        "The line starts with the target, then a `|`, then the candidates, which "
        "are not necessarily sorted.\n\n"
        "Print each combination on its own line with its numbers in ascending "
        "order, separated by single spaces. Print the combinations in ascending "
        "lexicographic order: compare two combinations position by position, and "
        "the smaller number at the first differing position comes first; if one "
        "is a prefix of the other, the shorter comes first. If nothing sums to "
        "the target, print nothing."
    ),
    "constraints": [
        "1 <= number of candidates <= 20 and the candidates are distinct",
        "1 <= candidate <= 40",
        "1 <= target <= 45",
        "Every combination is printed with its numbers ascending, and the "
        "combinations themselves in lexicographic order, so the answer is unique",
    ],
    "input_format": "One line: the target, then `|`, then the candidates.",
    "output_format": "One line per combination, numbers ascending and space separated, combinations in lexicographic order. Nothing if there are none.",
    "examples": [
        {
            "stdin": "7 | 2 3 6 7\n",
            "stdout": "2 2 3\n7",
            "explanation": "2 + 2 + 3 = 7 and 7 itself. `2 2 3` sorts before `7` because 2 < 7.",
        },
        {
            "stdin": "8 | 3 5 2\n",
            "stdout": "2 2 2 2\n2 3 3\n3 5",
            "explanation": "The candidates are unsorted on input but each combination is printed ascending, and the three combinations come out in lexicographic order.",
        },
    ],
    "criteria": [
        "Allow a candidate to be reused",
        "Emit each combination once, not once per ordering of it",
        "Sort the candidates first so the required output order falls out",
    ],
    "io": {
        "mode": "line",
        "function": "combination_sum",
        "todo": "parse the target and candidates, then print every combination summing to the target",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    line = sys.stdin.readline().rstrip('\\n')\n"
        "    head, candidates_part = line.split('|')\n"
        "    target = int(head.strip())\n"
        "    candidates = sorted(int(x) for x in candidates_part.split())\n"
        "    out = []\n"
        "    current = []\n"
        "\n"
        "    def walk(start, remaining):\n"
        "        if remaining == 0:\n"
        "            out.append(' '.join(map(str, current)))\n"
        "            return\n"
        "        for index in range(start, len(candidates)):\n"
        "            value = candidates[index]\n"
        "            if value > remaining:\n"
        "                break\n"
        "            current.append(value)\n"
        "            walk(index, remaining - value)\n"
        "            current.pop()\n"
        "\n"
        "    walk(0, target)\n"
        "    sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: target 7", "stdin": "7 | 2 3 6 7\n", "hidden": False},
        {"name": "sample: unsorted candidates", "stdin": "8 | 3 5 2\n", "hidden": False},
        {"name": "hidden: no combination", "stdin": "7 | 4 6\n", "hidden": True},
        {"name": "hidden: single candidate divides target", "stdin": "9 | 3\n", "hidden": True},
        {"name": "hidden: candidate equals target", "stdin": "5 | 5 6 7\n", "hidden": True},
        {"name": "hidden: candidate of 1 explodes", "stdin": "6 | 1 2 3\n", "hidden": True},
        {"name": "hidden: descending input", "stdin": "10 | 9 7 5 3 2\n", "hidden": True},
        {"name": "hidden: largest target", "stdin": "45 | 2 3 5 7 11 13 40\n", "hidden": True},
        {"name": "hidden: scale", "stdin": "40 | 1 2 3 4 5 6 7 8 9 10 11 12\n", "hidden": True},
    ],
    "wrong": [
        # Uses each candidate at most once.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, candidates_part = line.split('|')\n"
            "target = int(head.strip())\n"
            "candidates = sorted(int(x) for x in candidates_part.split())\n"
            "out = []\n"
            "current = []\n"
            "def walk(start, remaining):\n"
            "    if remaining == 0:\n"
            "        out.append(' '.join(map(str, current)))\n"
            "        return\n"
            "    for index in range(start, len(candidates)):\n"
            "        value = candidates[index]\n"
            "        if value > remaining:\n"
            "            break\n"
            "        current.append(value)\n"
            "        walk(index + 1, remaining - value)\n"
            "        current.pop()\n"
            "walk(0, target)\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
        # Counts every ordering, so combinations repeat.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, candidates_part = line.split('|')\n"
            "target = int(head.strip())\n"
            "candidates = sorted(int(x) for x in candidates_part.split())\n"
            "out = []\n"
            "current = []\n"
            "def walk(remaining):\n"
            "    if remaining == 0:\n"
            "        out.append(' '.join(map(str, current)))\n"
            "        return\n"
            "    for value in candidates:\n"
            "        if value > remaining:\n"
            "            break\n"
            "        current.append(value)\n"
            "        walk(remaining - value)\n"
            "        current.pop()\n"
            "walk(target)\n"
            "sys.stdout.write('\\n'.join(sorted(set(out))) + ('\\n' if out else ''))\n"
        ),
        # Forgets to sort the candidates, so both the numbers inside a
        # combination and the order of the lines follow the input order.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, candidates_part = line.split('|')\n"
            "target = int(head.strip())\n"
            "candidates = [int(x) for x in candidates_part.split()]\n"
            "out = []\n"
            "current = []\n"
            "def walk(start, remaining):\n"
            "    if remaining == 0:\n"
            "        out.append(' '.join(map(str, current)))\n"
            "        return\n"
            "    for index in range(start, len(candidates)):\n"
            "        value = candidates[index]\n"
            "        if value > remaining:\n"
            "            continue\n"
            "        current.append(value)\n"
            "        walk(index, remaining - value)\n"
            "        current.pop()\n"
            "walk(0, target)\n"
            "sys.stdout.write('\\n'.join(out) + ('\\n' if out else ''))\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  18 · Word search                                                           #
# --------------------------------------------------------------------------- #


def _word_search_case(seed: int, rows: int, cols: int, alphabet: str, length: int) -> str:
    grid = _random_grid(seed, rows, cols, alphabet)
    word = _random_words(seed + 5, 1, length, length, alphabet)[0]
    return f"{rows} {cols} | " + " ".join(grid) + " | " + word + "\n"


WORD_SEARCH = {
    "slug": "word-search",
    "skill_id": "dsa_arrays",
    "difficulty": 6,
    "estimated_minutes": 35,
    "title": "Word Search",
    "statement": (
        "Given a grid of lowercase letters and a single word, decide whether the "
        "word can be built from letters of sequentially adjacent cells, where "
        "adjacent means horizontally or vertically neighbouring. A single cell "
        "may not be used more than once.\n\n"
        "The line has three sections separated by `|`: the grid dimensions "
        "`R C`, then the R rows of the grid, then the word."
    ),
    "constraints": [
        "1 <= R, C <= 50",
        "1 <= word length <= 15",
        "The grid and the word are lowercase a-z",
        "Only horizontal and vertical steps are allowed, and no cell may repeat "
        "within the path",
    ],
    "input_format": "One line: `R C`, then `|`, then R rows, then `|`, then the word.",
    "output_format": "`true` if the word can be traced in the grid, otherwise `false`.",
    "examples": [
        {
            "stdin": "3 4 | abce sfcs adee | abcced\n",
            "stdout": "true",
            "explanation": "The path runs a-b-c across the top row, down to c, then e and d, never reusing a cell.",
        },
        {
            "stdin": "3 4 | abce sfcs adee | abcb\n",
            "stdout": "false",
            "explanation": "Reaching the final b would mean stepping back onto the b already used, which is not allowed.",
        },
    ],
    "criteria": [
        "Mark cells as used during a path and unmark them on the way back",
        "Reject diagonal steps",
        "Handle a single-cell grid and a single-letter word",
    ],
    "io": {
        "mode": "line",
        "function": "word_search",
        "todo": "parse the grid and the word and return 1 if the word can be traced, else 0",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    sys.setrecursionlimit(10000)\n"
        "    line = sys.stdin.readline().rstrip('\\n')\n"
        "    head, grid_part, word_part = line.split('|')\n"
        "    rows, cols = (int(x) for x in head.split())\n"
        "    grid = grid_part.split()\n"
        "    word = word_part.strip()\n"
        "    used = [[False] * cols for _ in range(rows)]\n"
        "\n"
        "    def walk(r, c, index):\n"
        "        if grid[r][c] != word[index]:\n"
        "            return False\n"
        "        if index == len(word) - 1:\n"
        "            return True\n"
        "        used[r][c] = True\n"
        "        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n"
        "            nr, nc = r + dr, c + dc\n"
        "            if 0 <= nr < rows and 0 <= nc < cols and not used[nr][nc]:\n"
        "                if walk(nr, nc, index + 1):\n"
        "                    used[r][c] = False\n"
        "                    return True\n"
        "        used[r][c] = False\n"
        "        return False\n"
        "\n"
        "    for r in range(rows):\n"
        "        for c in range(cols):\n"
        "            if walk(r, c, 0):\n"
        "                print('true')\n"
        "                return\n"
        "    print('false')\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: found", "stdin": "3 4 | abce sfcs adee | abcced\n", "hidden": False},
        {"name": "sample: needs cell reuse", "stdin": "3 4 | abce sfcs adee | abcb\n", "hidden": False},
        {"name": "hidden: single cell match", "stdin": "1 1 | a | a\n", "hidden": True},
        {"name": "hidden: single cell miss", "stdin": "1 1 | a | b\n", "hidden": True},
        {"name": "hidden: diagonal is illegal", "stdin": "2 2 | ab cd | ad\n", "hidden": True},
        {"name": "hidden: snake path", "stdin": "3 3 | abc fed ghi | abcdefghi\n", "hidden": True},
        {"name": "hidden: word longer than the grid", "stdin": "2 2 | aa aa | aaaaa\n", "hidden": True},
        {"name": "hidden: repeated letters, present", "stdin": "3 3 | aaa aaa aaa | aaaaaaaa\n", "hidden": True},
        {"name": "hidden: scale absent", "stdin": _word_search_case(261, 50, 50, "abcd", 15), "hidden": True},
        {"name": "hidden: scale present", "stdin": "1 15 | abcdefghijklmno | abcdefghijklmno\n", "hidden": True},
    ],
    "wrong": [
        # Lets a cell be reused inside the path.
        (
            "import sys\n"
            "sys.setrecursionlimit(10000)\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, grid_part, word_part = line.split('|')\n"
            "rows, cols = (int(x) for x in head.split())\n"
            "grid = grid_part.split()\n"
            "word = word_part.strip()\n"
            "def walk(r, c, index):\n"
            "    if grid[r][c] != word[index]:\n"
            "        return False\n"
            "    if index == len(word) - 1:\n"
            "        return True\n"
            "    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n"
            "        nr, nc = r + dr, c + dc\n"
            "        if 0 <= nr < rows and 0 <= nc < cols and walk(nr, nc, index + 1):\n"
            "            return True\n"
            "    return False\n"
            "found = any(walk(r, c, 0) for r in range(rows) for c in range(cols))\n"
            "print('true' if found else 'false')\n"
        ),
        # Only looks for the word in a straight line.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, grid_part, word_part = line.split('|')\n"
            "rows, cols = (int(x) for x in head.split())\n"
            "grid = grid_part.split()\n"
            "word = word_part.strip()\n"
            "found = False\n"
            "for row in grid:\n"
            "    if word in row or word in row[::-1]:\n"
            "        found = True\n"
            "for c in range(cols):\n"
            "    column = ''.join(grid[r][c] for r in range(rows))\n"
            "    if word in column or word in column[::-1]:\n"
            "        found = True\n"
            "print('true' if found else 'false')\n"
        ),
        # Only checks that the needed letters are available anywhere.
        (
            "import sys\n"
            "from collections import Counter\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, grid_part, word_part = line.split('|')\n"
            "available = Counter(''.join(grid_part.split()))\n"
            "need = Counter(word_part.strip())\n"
            "ok = all(available[ch] >= n for ch, n in need.items())\n"
            "print('true' if ok else 'false')\n"
        ),
    ],
}


# --------------------------------------------------------------------------- #
#  19 · Subsets                                                               #
# --------------------------------------------------------------------------- #

SUBSETS = {
    "slug": "subsets",
    "skill_id": "dsa_arrays",
    "difficulty": 5,
    "estimated_minutes": 30,
    "title": "Subsets",
    "statement": (
        "Given n distinct integers, list every subset, including the empty "
        "subset and the whole set. There are exactly 2^n of them.\n\n"
        "The line starts with n, then a `|`, then the n values, which are not "
        "necessarily sorted.\n\n"
        "Print one subset per line as its size followed by its elements in "
        "ascending order, separated by single spaces; the empty subset is "
        "therefore the line `0`. Order the lines by the element sequence in "
        "ascending lexicographic order, comparing position by position, with a "
        "prefix coming before any longer sequence it starts. So for `1 2` the "
        "output is `0`, `1 1`, `2 1 2`, `1 2`."
    ),
    "constraints": [
        "1 <= n <= 15, so at most 32768 subsets",
        "-1000000 <= value <= 1000000 and all values are distinct",
        "Each line is the subset size followed by its elements ascending, and "
        "the lines are in lexicographic order of those elements, so the answer "
        "is unique",
    ],
    "input_format": "One line: n, then `|`, then the n values.",
    "output_format": "2^n lines: each the subset size followed by the subset's elements in ascending order.",
    "examples": [
        {
            "stdin": "2 | 1 2\n",
            "stdout": "0\n1 1\n2 1 2\n1 2",
            "explanation": "The empty subset prints as `0`; then {1}, then {1,2}, then {2}. Lexicographic order puts {1} before {1,2} because it is a prefix, and both before {2}.",
        },
        {
            "stdin": "3 | 3 1 2\n",
            "stdout": "0\n1 1\n2 1 2\n3 1 2 3\n2 1 3\n1 2\n2 2 3\n1 3",
            "explanation": "The input is unsorted but the values are sorted first, so the eight subsets come out in lexicographic order of their sorted elements.",
        },
    ],
    "criteria": [
        "Include the empty subset and the full set",
        "Sort the input values before generating, so each subset is ascending",
        "Emit the lines in lexicographic order of the element sequences",
    ],
    "io": {
        "mode": "line",
        "function": "subsets",
        "todo": "parse the values and print every subset, one per line, in the required order",
        "reads": [{"name": "line", "type": "string"}],
        "args": ["line"],
        "returns": "int",
    },
    "reference": (
        "import sys\n"
        "def main():\n"
        "    line = sys.stdin.readline().rstrip('\\n')\n"
        "    head, values_part = line.split('|')\n"
        "    values = sorted(int(x) for x in values_part.split())\n"
        "    out = []\n"
        "    current = []\n"
        "\n"
        "    def walk(start):\n"
        "        out.append(str(len(current)) + (' ' + ' '.join(map(str, current)) if current else ''))\n"
        "        for index in range(start, len(values)):\n"
        "            current.append(values[index])\n"
        "            walk(index + 1)\n"
        "            current.pop()\n"
        "\n"
        "    walk(0)\n"
        "    sys.stdout.write('\\n'.join(out) + '\\n')\n"
        "main()\n"
    ),
    "inputs": [
        {"name": "sample: two values", "stdin": "2 | 1 2\n", "hidden": False},
        {"name": "sample: unsorted input", "stdin": "3 | 3 1 2\n", "hidden": False},
        {"name": "hidden: single value", "stdin": "1 | -7\n", "hidden": True},
        {"name": "hidden: negatives", "stdin": "3 | 0 -1 -2\n", "hidden": True},
        {"name": "hidden: descending input", "stdin": "4 | 4 3 2 1\n", "hidden": True},
        {"name": "hidden: large magnitudes", "stdin": "3 | 1000000 -1000000 0\n", "hidden": True},
        {
            "name": "hidden: scale",
            "stdin": "15 | " + " ".join(str(v) for v in [13, -4, 7, 0, 22, -19, 5, 41, -2, 8, 33, -11, 1, 17, -25]) + "\n",
            "hidden": True,
        },
    ],
    "wrong": [
        # Omits the empty subset.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, values_part = line.split('|')\n"
            "values = sorted(int(x) for x in values_part.split())\n"
            "out = []\n"
            "current = []\n"
            "def walk(start):\n"
            "    if current:\n"
            "        out.append(str(len(current)) + ' ' + ' '.join(map(str, current)))\n"
            "    for index in range(start, len(values)):\n"
            "        current.append(values[index])\n"
            "        walk(index + 1)\n"
            "        current.pop()\n"
            "walk(0)\n"
            "sys.stdout.write('\\n'.join(out) + '\\n')\n"
        ),
        # Bitmask order instead of lexicographic order.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, values_part = line.split('|')\n"
            "values = sorted(int(x) for x in values_part.split())\n"
            "n = len(values)\n"
            "out = []\n"
            "for mask in range(1 << n):\n"
            "    chosen = [values[i] for i in range(n) if mask >> i & 1]\n"
            "    out.append(str(len(chosen)) + (' ' + ' '.join(map(str, chosen)) if chosen else ''))\n"
            "sys.stdout.write('\\n'.join(out) + '\\n')\n"
        ),
        # Never sorts the input, so subsets are not ascending.
        (
            "import sys\n"
            "line = sys.stdin.readline().rstrip('\\n')\n"
            "head, values_part = line.split('|')\n"
            "values = [int(x) for x in values_part.split()]\n"
            "out = []\n"
            "current = []\n"
            "def walk(start):\n"
            "    out.append(str(len(current)) + (' ' + ' '.join(map(str, current)) if current else ''))\n"
            "    for index in range(start, len(values)):\n"
            "        current.append(values[index])\n"
            "        walk(index + 1)\n"
            "        current.pop()\n"
            "walk(0)\n"
            "sys.stdout.write('\\n'.join(out) + '\\n')\n"
        ),
    ],
}


PROBLEMS: list[dict[str, Any]] = [
    MAX_DEPTH,
    SAME_TREE,
    INVERT_TREE,
    MAX_PATH_SUM,
    LEVEL_ORDER,
    SERIALIZE_TREE,
    SUBTREE,
    BUILD_TREE,
    VALIDATE_BST,
    KTH_SMALLEST,
    LCA_BST,
    IMPLEMENT_TRIE,
    WORD_DICTIONARY,
    WORD_SEARCH_II,
    TOP_K_FREQUENT,
    MEDIAN_STREAM,
    COMBINATION_SUM,
    WORD_SEARCH,
    SUBSETS,
]
