"""Known-correct solutions for Blind 75 batch 3, one per (problem, language).

Used only by ``scripts/verify_blind75_3.py``, which runs them through the real
judge against the generated case bank. Nothing here is imported by the app, so
none of it can reach a client.

Every problem in this batch reads a single line of stdin, so each language gets
a small prelude: read the line, split it at `|`, and (for the eleven tree
problems) parse the level-order tokens into three parallel arrays — value, left
index and right index — which is the representation a C solution wants anyway.
"""

from __future__ import annotations

SOLUTIONS: dict[str, dict[str, str]] = {}


# --------------------------------------------------------------------------- #
#  Python                                                                     #
# --------------------------------------------------------------------------- #

_PY = r'''
import sys


def read_line():
    return sys.stdin.readline().rstrip("\n")


def parse_tree(text):
    tokens = text.split()
    if not tokens or tokens[0] == "null":
        return [], [], []
    val, left, right = [], [], []

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
        for side in (0, 1):
            if pos >= len(tokens):
                break
            token = tokens[pos]
            pos += 1
            if token == "null":
                continue
            child = add(token)
            if side == 0:
                left[node] = child
            else:
                right[node] = child
            queue.append(child)
    return val, left, right


def serialize(val, left, right, root=0):
    if not val:
        return "null"
    out = [root]
    head = 0
    while head < len(out):
        node = out[head]
        head += 1
        if node == -1:
            continue
        out.append(left[node])
        out.append(right[node])
    while out and out[-1] == -1:
        out.pop()
    return " ".join("null" if node == -1 else str(val[node]) for node in out)


def dfs_order(left, right, n):
    """Nodes with every parent before its children, so reversed() is post-order."""
    order = []
    stack = [0]
    while stack:
        node = stack.pop()
        order.append(node)
        if left[node] != -1:
            stack.append(left[node])
        if right[node] != -1:
            stack.append(right[node])
    return order
'''


# --------------------------------------------------------------------------- #
#  JavaScript                                                                 #
# --------------------------------------------------------------------------- #

_JS = r'''
const __input = require("fs").readFileSync(0, "utf8");
const line = (__input.split("\n")[0] ?? "");

function parseTree(text) {
  const tokens = text.split(/\s+/).filter(Boolean);
  const val = [];
  const left = [];
  const right = [];
  if (tokens.length === 0 || tokens[0] === "null") return { val, left, right };
  const add = (token) => {
    val.push(Number(token));
    left.push(-1);
    right.push(-1);
    return val.length - 1;
  };
  add(tokens[0]);
  const queue = [0];
  let head = 0;
  let pos = 1;
  while (head < queue.length && pos < tokens.length) {
    const node = queue[head++];
    for (let side = 0; side < 2 && pos < tokens.length; side++) {
      const token = tokens[pos++];
      if (token === "null") continue;
      const child = add(token);
      if (side === 0) left[node] = child;
      else right[node] = child;
      queue.push(child);
    }
  }
  return { val, left, right };
}

function serializeTree(t, root) {
  if (t.val.length === 0) return "null";
  const out = [root === undefined ? 0 : root];
  let head = 0;
  while (head < out.length) {
    const node = out[head++];
    if (node === -1) continue;
    out.push(t.left[node]);
    out.push(t.right[node]);
  }
  while (out.length && out[out.length - 1] === -1) out.pop();
  return out.map((node) => (node === -1 ? "null" : String(t.val[node]))).join(" ");
}

function dfsOrder(t) {
  const order = [];
  const stack = [0];
  while (stack.length) {
    const node = stack.pop();
    order.push(node);
    if (t.left[node] !== -1) stack.push(t.left[node]);
    if (t.right[node] !== -1) stack.push(t.right[node]);
  }
  return order;
}
'''


# --------------------------------------------------------------------------- #
#  Java                                                                       #
# --------------------------------------------------------------------------- #

_JAVA_TREE = r'''
    static final class Tree {
        int n;
        long[] val;
        int[] left;
        int[] right;
    }

    static Tree parseTree(String text) {
        Tree t = new Tree();
        StringTokenizer st = new StringTokenizer(text);
        int cap = st.countTokens();
        t.val = new long[Math.max(cap, 1)];
        t.left = new int[Math.max(cap, 1)];
        t.right = new int[Math.max(cap, 1)];
        if (cap == 0) return t;
        String[] toks = new String[cap];
        for (int i = 0; i < cap; i++) toks[i] = st.nextToken();
        if (toks[0].equals("null")) return t;
        int[] queue = new int[cap];
        int qn = 0;
        int head = 0;
        t.val[0] = Long.parseLong(toks[0]);
        t.left[0] = -1;
        t.right[0] = -1;
        t.n = 1;
        queue[qn++] = 0;
        int pos = 1;
        while (head < qn && pos < cap) {
            int node = queue[head++];
            for (int side = 0; side < 2 && pos < cap; side++) {
                String tok = toks[pos++];
                if (tok.equals("null")) continue;
                int child = t.n++;
                t.val[child] = Long.parseLong(tok);
                t.left[child] = -1;
                t.right[child] = -1;
                if (side == 0) t.left[node] = child;
                else t.right[node] = child;
                queue[qn++] = child;
            }
        }
        return t;
    }

    static String serializeTree(Tree t, int root) {
        if (t.n == 0) return "null";
        int[] out = new int[2 * t.n + 2];
        int on = 0;
        int head = 0;
        out[on++] = root;
        while (head < on) {
            int node = out[head++];
            if (node == -1) continue;
            out[on++] = t.left[node];
            out[on++] = t.right[node];
        }
        while (on > 0 && out[on - 1] == -1) on--;
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < on; i++) {
            if (i > 0) sb.append(' ');
            sb.append(out[i] == -1 ? "null" : Long.toString(t.val[out[i]]));
        }
        return sb.toString();
    }

    static int[] dfsOrder(Tree t) {
        int[] order = new int[t.n];
        int[] stack = new int[t.n + 2];
        int sp = 0;
        int on = 0;
        stack[sp++] = 0;
        while (sp > 0) {
            int node = stack[--sp];
            order[on++] = node;
            if (t.left[node] != -1) stack[sp++] = t.left[node];
            if (t.right[node] != -1) stack[sp++] = t.right[node];
        }
        return order;
    }
'''

_JAVA_READ = r'''
    static String readLine() throws IOException {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in), 1 << 20);
        String line = in.readLine();
        return line == null ? "" : line;
    }
'''


def _java(body: str, main: str, tree: bool = True) -> str:
    parts = [
        "import java.io.*;",
        "import java.util.*;",
        "",
        "public class Main {",
        _JAVA_READ,
    ]
    if tree:
        parts.append(_JAVA_TREE)
    parts.append(body)
    parts.append("    public static void main(String[] args) throws IOException {")
    parts.append(main)
    parts.append("    }")
    parts.append("}")
    return "\n".join(parts) + "\n"


# --------------------------------------------------------------------------- #
#  C++                                                                        #
# --------------------------------------------------------------------------- #

_CPP_HEAD = r'''
#include <algorithm>
#include <cstdio>
#include <iostream>
#include <map>
#include <queue>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>
'''

_CPP_TREE = r'''
struct Tree {
    std::vector<long long> val;
    std::vector<int> left;
    std::vector<int> right;
};

Tree parseTree(const std::string& text) {
    Tree t;
    std::istringstream in(text);
    std::vector<std::string> toks;
    std::string tok;
    while (in >> tok) toks.push_back(tok);
    if (toks.empty() || toks[0] == "null") return t;
    std::vector<int> queue;
    t.val.push_back(std::stoll(toks[0]));
    t.left.push_back(-1);
    t.right.push_back(-1);
    queue.push_back(0);
    size_t head = 0;
    size_t pos = 1;
    while (head < queue.size() && pos < toks.size()) {
        int node = queue[head++];
        for (int side = 0; side < 2 && pos < toks.size(); side++) {
            std::string current = toks[pos++];
            if (current == "null") continue;
            t.val.push_back(std::stoll(current));
            t.left.push_back(-1);
            t.right.push_back(-1);
            int child = (int)t.val.size() - 1;
            if (side == 0) t.left[node] = child;
            else t.right[node] = child;
            queue.push_back(child);
        }
    }
    return t;
}

std::string serializeTree(const Tree& t, int root = 0) {
    if (t.val.empty()) return "null";
    std::vector<int> out;
    out.push_back(root);
    size_t head = 0;
    while (head < out.size()) {
        int node = out[head++];
        if (node == -1) continue;
        out.push_back(t.left[node]);
        out.push_back(t.right[node]);
    }
    while (!out.empty() && out.back() == -1) out.pop_back();
    std::string result;
    for (size_t i = 0; i < out.size(); i++) {
        if (i) result += ' ';
        result += out[i] == -1 ? std::string("null") : std::to_string(t.val[out[i]]);
    }
    return result;
}

std::vector<int> dfsOrder(const Tree& t) {
    std::vector<int> order;
    std::vector<int> stack;
    stack.push_back(0);
    while (!stack.empty()) {
        int node = stack.back();
        stack.pop_back();
        order.push_back(node);
        if (t.left[node] != -1) stack.push_back(t.left[node]);
        if (t.right[node] != -1) stack.push_back(t.right[node]);
    }
    return order;
}

std::vector<std::string> sections(const std::string& line, int expected) {
    std::vector<std::string> parts;
    std::string current;
    for (char ch : line) {
        if (ch == '|') {
            parts.push_back(current);
            current.clear();
        } else {
            current += ch;
        }
    }
    parts.push_back(current);
    while ((int)parts.size() < expected) parts.push_back("");
    return parts;
}
'''


def _cpp(body: str, main: str, tree: bool = True) -> str:
    parts = [_CPP_HEAD]
    if tree:
        parts.append(_CPP_TREE)
    parts.append(body)
    parts.append("int main() {")
    parts.append("    std::ios::sync_with_stdio(false);")
    parts.append("    std::cin.tie(nullptr);")
    parts.append("    std::string line;")
    parts.append("    std::getline(std::cin, line);")
    parts.append(main)
    parts.append("    return 0;")
    parts.append("}")
    return "\n".join(parts) + "\n"


# --------------------------------------------------------------------------- #
#  C                                                                          #
# --------------------------------------------------------------------------- #

_C_HEAD = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char* read_whole_line(void) {
    size_t cap = 1 << 16;
    size_t len = 0;
    char* buf = (char*)malloc(cap);
    int c;
    while ((c = getchar()) != EOF && c != '\n') {
        if (len + 2 >= cap) {
            cap *= 2;
            buf = (char*)realloc(buf, cap);
        }
        buf[len++] = (char)c;
    }
    buf[len] = '\0';
    return buf;
}

/* Splits the line at '|' in place. Returns how many sections were produced. */
static int split_sections(char* line, char** parts, int max_parts) {
    int n = 0;
    parts[n++] = line;
    for (char* p = line; *p; p++) {
        if (*p == '|' && n < max_parts) {
            *p = '\0';
            parts[n++] = p + 1;
        }
    }
    return n;
}

static char* trim_spaces(char* s) {
    while (*s == ' ' || *s == '\t' || *s == '\r') s++;
    size_t n = strlen(s);
    while (n > 0 && (s[n - 1] == ' ' || s[n - 1] == '\t' || s[n - 1] == '\r')) s[--n] = '\0';
    return s;
}

static int count_tokens(const char* s) {
    int n = 0;
    int inside = 0;
    for (; *s; s++) {
        if (*s == ' ' || *s == '\t' || *s == '\r') {
            inside = 0;
        } else if (!inside) {
            inside = 1;
            n++;
        }
    }
    return n;
}
'''

_C_TREE = r'''
typedef struct {
    int n;
    long long* val;
    int* left;
    int* right;
} Tree;

/* Level-order tokens with 'null' markers into three parallel arrays. */
static Tree parse_tree(char* text) {
    Tree t;
    int cap = count_tokens(text);
    int alloc = cap > 0 ? cap : 1;
    t.n = 0;
    t.val = (long long*)malloc(sizeof(long long) * alloc);
    t.left = (int*)malloc(sizeof(int) * alloc);
    t.right = (int*)malloc(sizeof(int) * alloc);
    if (cap == 0) return t;
    char** toks = (char**)malloc(sizeof(char*) * cap);
    int m = 0;
    char* save = NULL;
    for (char* tok = strtok_r(text, " \t\r", &save); tok != NULL;
         tok = strtok_r(NULL, " \t\r", &save)) {
        toks[m++] = tok;
    }
    if (m == 0 || strcmp(toks[0], "null") == 0) {
        free(toks);
        return t;
    }
    int* queue = (int*)malloc(sizeof(int) * cap);
    int qn = 0;
    int head = 0;
    t.val[0] = atoll(toks[0]);
    t.left[0] = -1;
    t.right[0] = -1;
    t.n = 1;
    queue[qn++] = 0;
    int pos = 1;
    while (head < qn && pos < m) {
        int node = queue[head++];
        for (int side = 0; side < 2 && pos < m; side++) {
            char* tok = toks[pos++];
            if (strcmp(tok, "null") == 0) continue;
            int child = t.n++;
            t.val[child] = atoll(tok);
            t.left[child] = -1;
            t.right[child] = -1;
            if (side == 0) t.left[node] = child;
            else t.right[node] = child;
            queue[qn++] = child;
        }
    }
    free(toks);
    free(queue);
    return t;
}

static void print_tree(Tree t, int root) {
    if (t.n == 0) {
        printf("null\n");
        return;
    }
    int* out = (int*)malloc(sizeof(int) * (2 * t.n + 2));
    int on = 0;
    int head = 0;
    out[on++] = root;
    while (head < on) {
        int node = out[head++];
        if (node == -1) continue;
        out[on++] = t.left[node];
        out[on++] = t.right[node];
    }
    while (on > 0 && out[on - 1] == -1) on--;
    for (int i = 0; i < on; i++) {
        if (i) putchar(' ');
        if (out[i] == -1) fputs("null", stdout);
        else printf("%lld", t.val[out[i]]);
    }
    putchar('\n');
    free(out);
}

/* Parents before children, so walking the result backwards is post-order. */
static int* dfs_order(Tree t) {
    int* order = (int*)malloc(sizeof(int) * (t.n > 0 ? t.n : 1));
    int* stack = (int*)malloc(sizeof(int) * (t.n + 2));
    int sp = 0;
    int on = 0;
    stack[sp++] = 0;
    while (sp > 0) {
        int node = stack[--sp];
        order[on++] = node;
        if (t.left[node] != -1) stack[sp++] = t.left[node];
        if (t.right[node] != -1) stack[sp++] = t.right[node];
    }
    free(stack);
    return order;
}
'''


def _c(body: str, main: str, tree: bool = True) -> str:
    parts = [_C_HEAD]
    if tree:
        parts.append(_C_TREE)
    parts.append(body)
    parts.append("int main(void) {")
    parts.append("    char* line = read_whole_line();")
    parts.append(main)
    parts.append("    return 0;")
    parts.append("}")
    return "\n".join(parts) + "\n"


def _register(slug: str, python: str, javascript: str, java: str, cpp: str, c: str) -> None:
    SOLUTIONS[slug] = {
        "python": python.lstrip("\n"),
        "javascript": javascript.lstrip("\n"),
        "java": java,
        "cpp": cpp,
        "c": c,
    }


# --------------------------------------------------------------------------- #
#  01 · maximum-depth-of-binary-tree                                          #
# --------------------------------------------------------------------------- #

_register(
    "maximum-depth-of-binary-tree",
    python=_PY + r'''

def main():
    val, left, right = parse_tree(read_line())
    if not val:
        print(0)
        return
    best = 0
    stack = [(0, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > best:
            best = depth
        if left[node] != -1:
            stack.append((left[node], depth + 1))
        if right[node] != -1:
            stack.append((right[node], depth + 1))
    print(best)


main()
''',
    javascript=_JS + r'''
const t = parseTree(line);
if (t.val.length === 0) {
  console.log(0);
} else {
  let best = 0;
  const stack = [[0, 1]];
  while (stack.length) {
    const [node, depth] = stack.pop();
    if (depth > best) best = depth;
    if (t.left[node] !== -1) stack.push([t.left[node], depth + 1]);
    if (t.right[node] !== -1) stack.push([t.right[node], depth + 1]);
  }
  console.log(best);
}
''',
    java=_java(
        body="",
        main=r'''        Tree t = parseTree(readLine());
        if (t.n == 0) {
            System.out.println(0);
            return;
        }
        int[] stack = new int[t.n + 2];
        int[] depth = new int[t.n + 2];
        int sp = 0;
        stack[sp] = 0;
        depth[sp] = 1;
        sp++;
        int best = 0;
        while (sp > 0) {
            sp--;
            int node = stack[sp];
            int d = depth[sp];
            if (d > best) best = d;
            if (t.left[node] != -1) {
                stack[sp] = t.left[node];
                depth[sp] = d + 1;
                sp++;
            }
            if (t.right[node] != -1) {
                stack[sp] = t.right[node];
                depth[sp] = d + 1;
                sp++;
            }
        }
        System.out.println(best);''',
    ),
    cpp=_cpp(
        body="",
        main=r'''    Tree t = parseTree(line);
    if (t.val.empty()) {
        std::cout << 0 << "\n";
        return 0;
    }
    long long best = 0;
    std::vector<std::pair<int, long long>> stack;
    stack.push_back({0, 1});
    while (!stack.empty()) {
        auto entry = stack.back();
        stack.pop_back();
        if (entry.second > best) best = entry.second;
        if (t.left[entry.first] != -1) stack.push_back({t.left[entry.first], entry.second + 1});
        if (t.right[entry.first] != -1) stack.push_back({t.right[entry.first], entry.second + 1});
    }
    std::cout << best << "\n";''',
    ),
    c=_c(
        body="",
        main=r'''    Tree t = parse_tree(line);
    if (t.n == 0) {
        printf("0\n");
        return 0;
    }
    int* stack = (int*)malloc(sizeof(int) * (t.n + 2));
    int* depth = (int*)malloc(sizeof(int) * (t.n + 2));
    int sp = 0;
    stack[sp] = 0;
    depth[sp] = 1;
    sp++;
    int best = 0;
    while (sp > 0) {
        sp--;
        int node = stack[sp];
        int d = depth[sp];
        if (d > best) best = d;
        if (t.left[node] != -1) {
            stack[sp] = t.left[node];
            depth[sp] = d + 1;
            sp++;
        }
        if (t.right[node] != -1) {
            stack[sp] = t.right[node];
            depth[sp] = d + 1;
            sp++;
        }
    }
    printf("%d\n", best);''',
    ),
)


# --------------------------------------------------------------------------- #
#  02 · same-binary-tree                                                      #
# --------------------------------------------------------------------------- #

_register(
    "same-binary-tree",
    python=_PY + r'''

def main():
    parts = read_line().split("|")
    a = parse_tree(parts[0])
    b = parse_tree(parts[1])
    print("true" if serialize(*a) == serialize(*b) else "false")


main()
''',
    javascript=_JS + r'''
const parts = line.split("|");
const a = parseTree(parts[0]);
const b = parseTree(parts[1] ?? "");
console.log(serializeTree(a, 0) === serializeTree(b, 0) ? "true" : "false");
''',
    java=_java(
        body="",
        main=r'''        String[] parts = readLine().split("\\|");
        Tree a = parseTree(parts[0]);
        Tree b = parseTree(parts.length > 1 ? parts[1] : "");
        boolean same = serializeTree(a, 0).equals(serializeTree(b, 0));
        System.out.println(same ? "true" : "false");''',
    ),
    cpp=_cpp(
        body="",
        main=r'''    std::vector<std::string> parts = sections(line, 2);
    Tree a = parseTree(parts[0]);
    Tree b = parseTree(parts[1]);
    std::cout << (serializeTree(a) == serializeTree(b) ? "true" : "false") << "\n";''',
    ),
    c=_c(
        body=r'''
/* Canonical level-order text for one tree, so two trees can be compared. */
static char* tree_text(Tree t) {
    if (t.n == 0) {
        char* out = (char*)malloc(5);
        strcpy(out, "null");
        return out;
    }
    int* order = (int*)malloc(sizeof(int) * (2 * t.n + 2));
    int on = 0;
    int head = 0;
    order[on++] = 0;
    while (head < on) {
        int node = order[head++];
        if (node == -1) continue;
        order[on++] = t.left[node];
        order[on++] = t.right[node];
    }
    while (on > 0 && order[on - 1] == -1) on--;
    size_t cap = (size_t)on * 24 + 8;
    char* out = (char*)malloc(cap);
    size_t len = 0;
    for (int i = 0; i < on; i++) {
        if (i) out[len++] = ' ';
        if (order[i] == -1) {
            memcpy(out + len, "null", 4);
            len += 4;
        } else {
            len += (size_t)sprintf(out + len, "%lld", t.val[order[i]]);
        }
    }
    out[len] = '\0';
    free(order);
    return out;
}
''',
        main=r'''    char* parts[4];
    int count = split_sections(line, parts, 4);
    Tree a = parse_tree(parts[0]);
    Tree b = parse_tree(count > 1 ? parts[1] : (char*)"");
    char* ta = tree_text(a);
    char* tb = tree_text(b);
    printf("%s\n", strcmp(ta, tb) == 0 ? "true" : "false");''',
    ),
)


# --------------------------------------------------------------------------- #
#  03 · invert-binary-tree                                                    #
# --------------------------------------------------------------------------- #

_register(
    "invert-binary-tree",
    python=_PY + r'''

def main():
    val, left, right = parse_tree(read_line())
    for node in range(len(val)):
        left[node], right[node] = right[node], left[node]
    print(serialize(val, left, right))


main()
''',
    javascript=_JS + r'''
const t = parseTree(line);
for (let node = 0; node < t.val.length; node++) {
  const tmp = t.left[node];
  t.left[node] = t.right[node];
  t.right[node] = tmp;
}
console.log(serializeTree(t, 0));
''',
    java=_java(
        body="",
        main=r'''        Tree t = parseTree(readLine());
        for (int node = 0; node < t.n; node++) {
            int tmp = t.left[node];
            t.left[node] = t.right[node];
            t.right[node] = tmp;
        }
        System.out.println(serializeTree(t, 0));''',
    ),
    cpp=_cpp(
        body="",
        main=r'''    Tree t = parseTree(line);
    for (size_t node = 0; node < t.val.size(); node++) std::swap(t.left[node], t.right[node]);
    std::cout << serializeTree(t) << "\n";''',
    ),
    c=_c(
        body="",
        main=r'''    Tree t = parse_tree(line);
    for (int node = 0; node < t.n; node++) {
        int tmp = t.left[node];
        t.left[node] = t.right[node];
        t.right[node] = tmp;
    }
    print_tree(t, 0);''',
    ),
)


# --------------------------------------------------------------------------- #
#  04 · binary-tree-maximum-path-sum                                          #
# --------------------------------------------------------------------------- #

_register(
    "binary-tree-maximum-path-sum",
    python=_PY + r'''

def main():
    val, left, right = parse_tree(read_line())
    order = dfs_order(left, right, len(val))
    down = [0] * len(val)
    best = None
    for node in reversed(order):
        l = down[left[node]] if left[node] != -1 else 0
        r = down[right[node]] if right[node] != -1 else 0
        if l < 0:
            l = 0
        if r < 0:
            r = 0
        through = val[node] + l + r
        if best is None or through > best:
            best = through
        down[node] = val[node] + (l if l > r else r)
    print(best)


main()
''',
    javascript=_JS + r'''
const t = parseTree(line);
const order = dfsOrder(t);
const down = new Array(t.val.length).fill(0n);
let best = null;
for (let i = order.length - 1; i >= 0; i--) {
  const node = order[i];
  let l = t.left[node] !== -1 ? down[t.left[node]] : 0n;
  let r = t.right[node] !== -1 ? down[t.right[node]] : 0n;
  if (l < 0n) l = 0n;
  if (r < 0n) r = 0n;
  const value = BigInt(t.val[node]);
  const through = value + l + r;
  if (best === null || through > best) best = through;
  down[node] = value + (l > r ? l : r);
}
console.log(best.toString());
''',
    java=_java(
        body="",
        main=r'''        Tree t = parseTree(readLine());
        int[] order = dfsOrder(t);
        long[] down = new long[t.n];
        long best = Long.MIN_VALUE;
        for (int i = t.n - 1; i >= 0; i--) {
            int node = order[i];
            long l = t.left[node] != -1 ? down[t.left[node]] : 0L;
            long r = t.right[node] != -1 ? down[t.right[node]] : 0L;
            if (l < 0) l = 0;
            if (r < 0) r = 0;
            long through = t.val[node] + l + r;
            if (through > best) best = through;
            down[node] = t.val[node] + Math.max(l, r);
        }
        System.out.println(best);''',
    ),
    cpp=_cpp(
        body="",
        main=r'''    Tree t = parseTree(line);
    std::vector<int> order = dfsOrder(t);
    std::vector<long long> down(t.val.size(), 0);
    long long best = 0;
    bool first = true;
    for (int i = (int)order.size() - 1; i >= 0; i--) {
        int node = order[i];
        long long l = t.left[node] != -1 ? down[t.left[node]] : 0;
        long long r = t.right[node] != -1 ? down[t.right[node]] : 0;
        if (l < 0) l = 0;
        if (r < 0) r = 0;
        long long through = t.val[node] + l + r;
        if (first || through > best) {
            best = through;
            first = false;
        }
        down[node] = t.val[node] + (l > r ? l : r);
    }
    std::cout << best << "\n";''',
    ),
    c=_c(
        body="",
        main=r'''    Tree t = parse_tree(line);
    int* order = dfs_order(t);
    long long* down = (long long*)malloc(sizeof(long long) * t.n);
    long long best = 0;
    int first = 1;
    for (int i = t.n - 1; i >= 0; i--) {
        int node = order[i];
        long long l = t.left[node] != -1 ? down[t.left[node]] : 0;
        long long r = t.right[node] != -1 ? down[t.right[node]] : 0;
        if (l < 0) l = 0;
        if (r < 0) r = 0;
        long long through = t.val[node] + l + r;
        if (first || through > best) {
            best = through;
            first = 0;
        }
        down[node] = t.val[node] + (l > r ? l : r);
    }
    printf("%lld\n", best);''',
    ),
)


# --------------------------------------------------------------------------- #
#  05 · binary-tree-level-order-traversal                                     #
# --------------------------------------------------------------------------- #

_register(
    "binary-tree-level-order-traversal",
    python=_PY + r'''

def main():
    val, left, right = parse_tree(read_line())
    if not val:
        return
    out = []
    level = [0]
    while level:
        out.append(" ".join(str(val[node]) for node in level))
        nxt = []
        for node in level:
            if left[node] != -1:
                nxt.append(left[node])
            if right[node] != -1:
                nxt.append(right[node])
        level = nxt
    sys.stdout.write("\n".join(out) + "\n")


main()
''',
    javascript=_JS + r'''
const t = parseTree(line);
if (t.val.length > 0) {
  const out = [];
  let level = [0];
  while (level.length) {
    out.push(level.map((node) => String(t.val[node])).join(" "));
    const next = [];
    for (const node of level) {
      if (t.left[node] !== -1) next.push(t.left[node]);
      if (t.right[node] !== -1) next.push(t.right[node]);
    }
    level = next;
  }
  process.stdout.write(out.join("\n") + "\n");
}
''',
    java=_java(
        body="",
        main=r'''        Tree t = parseTree(readLine());
        if (t.n == 0) return;
        StringBuilder sb = new StringBuilder();
        int[] level = new int[t.n];
        int[] next = new int[t.n];
        int ln = 0;
        level[ln++] = 0;
        while (ln > 0) {
            for (int i = 0; i < ln; i++) {
                if (i > 0) sb.append(' ');
                sb.append(t.val[level[i]]);
            }
            sb.append('\n');
            int nn = 0;
            for (int i = 0; i < ln; i++) {
                int node = level[i];
                if (t.left[node] != -1) next[nn++] = t.left[node];
                if (t.right[node] != -1) next[nn++] = t.right[node];
            }
            System.arraycopy(next, 0, level, 0, nn);
            ln = nn;
        }
        System.out.print(sb);''',
    ),
    cpp=_cpp(
        body="",
        main=r'''    Tree t = parseTree(line);
    if (t.val.empty()) return 0;
    std::string out;
    std::vector<int> level;
    level.push_back(0);
    while (!level.empty()) {
        for (size_t i = 0; i < level.size(); i++) {
            if (i) out += ' ';
            out += std::to_string(t.val[level[i]]);
        }
        out += '\n';
        std::vector<int> next;
        for (int node : level) {
            if (t.left[node] != -1) next.push_back(t.left[node]);
            if (t.right[node] != -1) next.push_back(t.right[node]);
        }
        level = next;
    }
    std::cout << out;''',
    ),
    c=_c(
        body="",
        main=r'''    Tree t = parse_tree(line);
    if (t.n == 0) return 0;
    int* level = (int*)malloc(sizeof(int) * (t.n + 1));
    int* next = (int*)malloc(sizeof(int) * (t.n + 1));
    int ln = 0;
    level[ln++] = 0;
    while (ln > 0) {
        for (int i = 0; i < ln; i++) {
            if (i) putchar(' ');
            printf("%lld", t.val[level[i]]);
        }
        putchar('\n');
        int nn = 0;
        for (int i = 0; i < ln; i++) {
            int node = level[i];
            if (t.left[node] != -1) next[nn++] = t.left[node];
            if (t.right[node] != -1) next[nn++] = t.right[node];
        }
        memcpy(level, next, sizeof(int) * (size_t)nn);
        ln = nn;
    }''',
    ),
)


# --------------------------------------------------------------------------- #
#  06 · serialize-and-deserialize-binary-tree                                 #
# --------------------------------------------------------------------------- #
# The round trip is genuine: each solution encodes the tree into its own
# string, parses that string back into fresh arrays, and prints the result.

_register(
    "serialize-and-deserialize-binary-tree",
    python=_PY + r'''

def encode(val, left, right):
    """Own encoding: preorder with '#' for a missing child."""
    if not val:
        return "#"
    out = []
    stack = [0]
    while stack:
        node = stack.pop()
        if node == -1:
            out.append("#")
            continue
        out.append(str(val[node]))
        stack.append(right[node])
        stack.append(left[node])
    return ",".join(out)


def decode(text):
    tokens = text.split(",")
    if tokens[0] == "#":
        return [], [], []
    val, left, right = [], [], []
    pos = 0

    def build():
        nonlocal pos
        token = tokens[pos]
        pos += 1
        if token == "#":
            return -1
        val.append(int(token))
        left.append(-1)
        right.append(-1)
        node = len(val) - 1
        left[node] = build()
        right[node] = build()
        return node

    sys.setrecursionlimit(100000)
    build()
    return val, left, right


def main():
    val, left, right = parse_tree(read_line())
    encoded = encode(val, left, right)
    print(serialize(*decode(encoded)))


main()
''',
    javascript=_JS + r'''
function encode(t) {
  if (t.val.length === 0) return "#";
  const out = [];
  const stack = [0];
  while (stack.length) {
    const node = stack.pop();
    if (node === -1) {
      out.push("#");
      continue;
    }
    out.push(String(t.val[node]));
    stack.push(t.right[node]);
    stack.push(t.left[node]);
  }
  return out.join(",");
}

function decode(text) {
  const tokens = text.split(",");
  const t = { val: [], left: [], right: [] };
  if (tokens[0] === "#") return t;
  let pos = 0;
  const stack = [];
  // Iterative preorder rebuild: each frame records which child comes next.
  const rootToken = tokens[pos++];
  t.val.push(Number(rootToken));
  t.left.push(-1);
  t.right.push(-1);
  stack.push([0, 0]);
  while (stack.length) {
    const frame = stack[stack.length - 1];
    if (frame[1] === 2) {
      stack.pop();
      continue;
    }
    const side = frame[1]++;
    const token = tokens[pos++];
    if (token === "#") continue;
    t.val.push(Number(token));
    t.left.push(-1);
    t.right.push(-1);
    const child = t.val.length - 1;
    if (side === 0) t.left[frame[0]] = child;
    else t.right[frame[0]] = child;
    stack.push([child, 0]);
  }
  return t;
}

const original = parseTree(line);
console.log(serializeTree(decode(encode(original)), 0));
''',
    java=_java(
        body=r'''
    static StringBuilder encode(Tree t) {
        StringBuilder sb = new StringBuilder();
        if (t.n == 0) {
            sb.append('#');
            return sb;
        }
        int[] stack = new int[2 * t.n + 2];
        int sp = 0;
        stack[sp++] = 0;
        boolean first = true;
        while (sp > 0) {
            int node = stack[--sp];
            if (!first) sb.append(',');
            first = false;
            if (node == -1) {
                sb.append('#');
                continue;
            }
            sb.append(t.val[node]);
            stack[sp++] = t.right[node];
            stack[sp++] = t.left[node];
        }
        return sb;
    }

    static Tree decode(String text) {
        String[] tokens = text.split(",");
        Tree t = new Tree();
        t.val = new long[tokens.length];
        t.left = new int[tokens.length];
        t.right = new int[tokens.length];
        if (tokens[0].equals("#")) return t;
        int[] frame = new int[tokens.length + 2];
        int[] side = new int[tokens.length + 2];
        int sp = 0;
        int pos = 0;
        t.val[0] = Long.parseLong(tokens[pos++]);
        t.left[0] = -1;
        t.right[0] = -1;
        t.n = 1;
        frame[sp] = 0;
        side[sp] = 0;
        sp++;
        while (sp > 0) {
            if (side[sp - 1] == 2) {
                sp--;
                continue;
            }
            int parent = frame[sp - 1];
            int which = side[sp - 1]++;
            String token = tokens[pos++];
            if (token.equals("#")) continue;
            int child = t.n++;
            t.val[child] = Long.parseLong(token);
            t.left[child] = -1;
            t.right[child] = -1;
            if (which == 0) t.left[parent] = child;
            else t.right[parent] = child;
            frame[sp] = child;
            side[sp] = 0;
            sp++;
        }
        return t;
    }
''',
        main=r'''        Tree original = parseTree(readLine());
        System.out.println(serializeTree(decode(encode(original).toString()), 0));''',
    ),
    cpp=_cpp(
        body=r'''
std::string encode(const Tree& t) {
    if (t.val.empty()) return "#";
    std::string out;
    std::vector<int> stack;
    stack.push_back(0);
    bool first = true;
    while (!stack.empty()) {
        int node = stack.back();
        stack.pop_back();
        if (!first) out += ',';
        first = false;
        if (node == -1) {
            out += '#';
            continue;
        }
        out += std::to_string(t.val[node]);
        stack.push_back(t.right[node]);
        stack.push_back(t.left[node]);
    }
    return out;
}

Tree decode(const std::string& text) {
    std::vector<std::string> tokens;
    std::string current;
    for (char ch : text) {
        if (ch == ',') {
            tokens.push_back(current);
            current.clear();
        } else {
            current += ch;
        }
    }
    tokens.push_back(current);
    Tree t;
    if (tokens[0] == "#") return t;
    size_t pos = 0;
    t.val.push_back(std::stoll(tokens[pos++]));
    t.left.push_back(-1);
    t.right.push_back(-1);
    std::vector<std::pair<int, int>> stack;
    stack.push_back({0, 0});
    while (!stack.empty()) {
        if (stack.back().second == 2) {
            stack.pop_back();
            continue;
        }
        int parent = stack.back().first;
        int which = stack.back().second++;
        std::string token = tokens[pos++];
        if (token == "#") continue;
        t.val.push_back(std::stoll(token));
        t.left.push_back(-1);
        t.right.push_back(-1);
        int child = (int)t.val.size() - 1;
        if (which == 0) t.left[parent] = child;
        else t.right[parent] = child;
        stack.push_back({child, 0});
    }
    return t;
}
''',
        main=r'''    Tree original = parseTree(line);
    std::cout << serializeTree(decode(encode(original))) << "\n";''',
    ),
    c=_c(
        body=r'''
/* Own encoding: preorder, '#' for a missing child, comma separated. */
static char* encode(Tree t) {
    size_t cap = (size_t)(t.n * 2 + 4) * 24;
    char* out = (char*)malloc(cap);
    size_t len = 0;
    if (t.n == 0) {
        strcpy(out, "#");
        return out;
    }
    int* stack = (int*)malloc(sizeof(int) * (2 * t.n + 2));
    int sp = 0;
    stack[sp++] = 0;
    int first = 1;
    while (sp > 0) {
        int node = stack[--sp];
        if (!first) out[len++] = ',';
        first = 0;
        if (node == -1) {
            out[len++] = '#';
            continue;
        }
        len += (size_t)sprintf(out + len, "%lld", t.val[node]);
        stack[sp++] = t.right[node];
        stack[sp++] = t.left[node];
    }
    out[len] = '\0';
    free(stack);
    return out;
}

static Tree decode(char* text) {
    Tree t;
    int cap = 1;
    for (char* p = text; *p; p++) {
        if (*p == ',') cap++;
    }
    t.n = 0;
    t.val = (long long*)malloc(sizeof(long long) * cap);
    t.left = (int*)malloc(sizeof(int) * cap);
    t.right = (int*)malloc(sizeof(int) * cap);
    char** tokens = (char**)malloc(sizeof(char*) * cap);
    int m = 0;
    char* save = NULL;
    for (char* tok = strtok_r(text, ",", &save); tok != NULL; tok = strtok_r(NULL, ",", &save)) {
        tokens[m++] = tok;
    }
    if (m == 0 || strcmp(tokens[0], "#") == 0) {
        free(tokens);
        return t;
    }
    int* frame = (int*)malloc(sizeof(int) * (cap + 2));
    int* side = (int*)malloc(sizeof(int) * (cap + 2));
    int sp = 0;
    int pos = 0;
    t.val[0] = atoll(tokens[pos++]);
    t.left[0] = -1;
    t.right[0] = -1;
    t.n = 1;
    frame[sp] = 0;
    side[sp] = 0;
    sp++;
    while (sp > 0) {
        if (side[sp - 1] == 2) {
            sp--;
            continue;
        }
        int parent = frame[sp - 1];
        int which = side[sp - 1]++;
        char* token = tokens[pos++];
        if (strcmp(token, "#") == 0) continue;
        int child = t.n++;
        t.val[child] = atoll(token);
        t.left[child] = -1;
        t.right[child] = -1;
        if (which == 0) t.left[parent] = child;
        else t.right[parent] = child;
        frame[sp] = child;
        side[sp] = 0;
        sp++;
    }
    free(tokens);
    free(frame);
    free(side);
    return t;
}
''',
        main=r'''    Tree original = parse_tree(line);
    char* encoded = encode(original);
    Tree rebuilt = decode(encoded);
    print_tree(rebuilt, 0);''',
    ),
)


# --------------------------------------------------------------------------- #
#  07 · subtree-of-another-tree                                               #
# --------------------------------------------------------------------------- #
# A structural fingerprint per node (two moduli plus the subtree size) turns
# "does S occur in T" into a lookup instead of an O(n*m) comparison.

_register(
    "subtree-of-another-tree",
    python=_PY + r'''

MOD1 = 1000000007
MOD2 = 998244353


def fingerprints(val, left, right):
    n = len(val)
    h1 = [0] * n
    h2 = [0] * n
    size = [0] * n
    for node in reversed(dfs_order(left, right, n)):
        l, r = left[node], right[node]
        l1 = h1[l] if l != -1 else 1
        l2 = h2[l] if l != -1 else 1
        r1 = h1[r] if r != -1 else 1
        r2 = h2[r] if r != -1 else 1
        h1[node] = (l1 * 131 + r1 * 137 + (val[node] % MOD1)) % MOD1
        h2[node] = (l2 * 1000003 + r2 * 10007 + (val[node] % MOD2)) % MOD2
        size[node] = 1 + (size[l] if l != -1 else 0) + (size[r] if r != -1 else 0)
    return h1, h2, size


def main():
    parts = read_line().split("|")
    va, la, ra = parse_tree(parts[0])
    vb, lb, rb = parse_tree(parts[1])
    if not vb:
        print("true")
        return
    if not va:
        print("false")
        return
    ah1, ah2, asize = fingerprints(va, la, ra)
    bh1, bh2, bsize = fingerprints(vb, lb, rb)
    target = (bh1[0], bh2[0], bsize[0])
    found = any((ah1[i], ah2[i], asize[i]) == target for i in range(len(va)))
    print("true" if found else "false")


main()
''',
    javascript=_JS + r'''
const MOD1 = 1000000007;
const MOD2 = 998244353;

function fingerprints(t) {
  const n = t.val.length;
  const h1 = new Array(n).fill(0);
  const h2 = new Array(n).fill(0);
  const size = new Array(n).fill(0);
  const order = dfsOrder(t);
  for (let i = order.length - 1; i >= 0; i--) {
    const node = order[i];
    const l = t.left[node];
    const r = t.right[node];
    const l1 = l !== -1 ? h1[l] : 1;
    const l2 = l !== -1 ? h2[l] : 1;
    const r1 = r !== -1 ? h1[r] : 1;
    const r2 = r !== -1 ? h2[r] : 1;
    const v = t.val[node];
    h1[node] = ((l1 * 131 + r1 * 137) % MOD1 + ((v % MOD1) + MOD1)) % MOD1;
    h2[node] = ((l2 * 1000003 + r2 * 10007) % MOD2 + ((v % MOD2) + MOD2)) % MOD2;
    size[node] = 1 + (l !== -1 ? size[l] : 0) + (r !== -1 ? size[r] : 0);
  }
  return { h1, h2, size };
}

const parts = line.split("|");
const a = parseTree(parts[0]);
const b = parseTree(parts[1] ?? "");
if (b.val.length === 0) {
  console.log("true");
} else if (a.val.length === 0) {
  console.log("false");
} else {
  const fa = fingerprints(a);
  const fb = fingerprints(b);
  let found = false;
  for (let i = 0; i < a.val.length; i++) {
    if (fa.h1[i] === fb.h1[0] && fa.h2[i] === fb.h2[0] && fa.size[i] === fb.size[0]) {
      found = true;
      break;
    }
  }
  console.log(found ? "true" : "false");
}
''',
    java=_java(
        body=r'''
    static final long MOD1 = 1000000007L;
    static final long MOD2 = 998244353L;

    static long[][] fingerprints(Tree t) {
        long[] h1 = new long[t.n];
        long[] h2 = new long[t.n];
        long[] size = new long[t.n];
        int[] order = dfsOrder(t);
        for (int i = t.n - 1; i >= 0; i--) {
            int node = order[i];
            int l = t.left[node];
            int r = t.right[node];
            long l1 = l != -1 ? h1[l] : 1L;
            long l2 = l != -1 ? h2[l] : 1L;
            long r1 = r != -1 ? h1[r] : 1L;
            long r2 = r != -1 ? h2[r] : 1L;
            long v = t.val[node];
            h1[node] = ((l1 * 131 + r1 * 137) % MOD1 + (v % MOD1 + MOD1)) % MOD1;
            h2[node] = ((l2 * 1000003 + r2 * 10007) % MOD2 + (v % MOD2 + MOD2)) % MOD2;
            size[node] = 1 + (l != -1 ? size[l] : 0) + (r != -1 ? size[r] : 0);
        }
        return new long[][] {h1, h2, size};
    }
''',
        main=r'''        String[] parts = readLine().split("\\|");
        Tree a = parseTree(parts[0]);
        Tree b = parseTree(parts.length > 1 ? parts[1] : "");
        if (b.n == 0) {
            System.out.println("true");
            return;
        }
        if (a.n == 0) {
            System.out.println("false");
            return;
        }
        long[][] fa = fingerprints(a);
        long[][] fb = fingerprints(b);
        boolean found = false;
        for (int i = 0; i < a.n; i++) {
            if (fa[0][i] == fb[0][0] && fa[1][i] == fb[1][0] && fa[2][i] == fb[2][0]) {
                found = true;
                break;
            }
        }
        System.out.println(found ? "true" : "false");''',
    ),
    cpp=_cpp(
        body=r'''
const long long MOD1 = 1000000007LL;
const long long MOD2 = 998244353LL;

struct Prints {
    std::vector<long long> h1;
    std::vector<long long> h2;
    std::vector<long long> size;
};

Prints fingerprints(const Tree& t) {
    int n = (int)t.val.size();
    Prints p;
    p.h1.assign(n, 0);
    p.h2.assign(n, 0);
    p.size.assign(n, 0);
    std::vector<int> order = dfsOrder(t);
    for (int i = n - 1; i >= 0; i--) {
        int node = order[i];
        int l = t.left[node];
        int r = t.right[node];
        long long l1 = l != -1 ? p.h1[l] : 1;
        long long l2 = l != -1 ? p.h2[l] : 1;
        long long r1 = r != -1 ? p.h1[r] : 1;
        long long r2 = r != -1 ? p.h2[r] : 1;
        long long v = t.val[node];
        p.h1[node] = ((l1 * 131 + r1 * 137) % MOD1 + (v % MOD1 + MOD1)) % MOD1;
        p.h2[node] = ((l2 * 1000003 + r2 * 10007) % MOD2 + (v % MOD2 + MOD2)) % MOD2;
        p.size[node] = 1 + (l != -1 ? p.size[l] : 0) + (r != -1 ? p.size[r] : 0);
    }
    return p;
}
''',
        main=r'''    std::vector<std::string> parts = sections(line, 2);
    Tree a = parseTree(parts[0]);
    Tree b = parseTree(parts[1]);
    if (b.val.empty()) {
        std::cout << "true\n";
        return 0;
    }
    if (a.val.empty()) {
        std::cout << "false\n";
        return 0;
    }
    Prints fa = fingerprints(a);
    Prints fb = fingerprints(b);
    bool found = false;
    for (size_t i = 0; i < a.val.size(); i++) {
        if (fa.h1[i] == fb.h1[0] && fa.h2[i] == fb.h2[0] && fa.size[i] == fb.size[0]) {
            found = true;
            break;
        }
    }
    std::cout << (found ? "true" : "false") << "\n";''',
    ),
    c=_c(
        body=r'''
#define MOD1 1000000007LL
#define MOD2 998244353LL

static void fingerprints(Tree t, long long* h1, long long* h2, long long* size) {
    int* order = dfs_order(t);
    for (int i = t.n - 1; i >= 0; i--) {
        int node = order[i];
        int l = t.left[node];
        int r = t.right[node];
        long long l1 = l != -1 ? h1[l] : 1;
        long long l2 = l != -1 ? h2[l] : 1;
        long long r1 = r != -1 ? h1[r] : 1;
        long long r2 = r != -1 ? h2[r] : 1;
        long long v = t.val[node];
        h1[node] = ((l1 * 131 + r1 * 137) % MOD1 + (v % MOD1 + MOD1)) % MOD1;
        h2[node] = ((l2 * 1000003 + r2 * 10007) % MOD2 + (v % MOD2 + MOD2)) % MOD2;
        size[node] = 1 + (l != -1 ? size[l] : 0) + (r != -1 ? size[r] : 0);
    }
    free(order);
}
''',
        main=r'''    char* parts[4];
    int count = split_sections(line, parts, 4);
    Tree a = parse_tree(parts[0]);
    Tree b = parse_tree(count > 1 ? parts[1] : (char*)"");
    if (b.n == 0) {
        printf("true\n");
        return 0;
    }
    if (a.n == 0) {
        printf("false\n");
        return 0;
    }
    long long* ah1 = (long long*)malloc(sizeof(long long) * a.n);
    long long* ah2 = (long long*)malloc(sizeof(long long) * a.n);
    long long* asz = (long long*)malloc(sizeof(long long) * a.n);
    long long* bh1 = (long long*)malloc(sizeof(long long) * b.n);
    long long* bh2 = (long long*)malloc(sizeof(long long) * b.n);
    long long* bsz = (long long*)malloc(sizeof(long long) * b.n);
    fingerprints(a, ah1, ah2, asz);
    fingerprints(b, bh1, bh2, bsz);
    int found = 0;
    for (int i = 0; i < a.n; i++) {
        if (ah1[i] == bh1[0] && ah2[i] == bh2[0] && asz[i] == bsz[0]) {
            found = 1;
            break;
        }
    }
    printf("%s\n", found ? "true" : "false");''',
    ),
)


# --------------------------------------------------------------------------- #
#  08 · construct-tree-from-preorder-and-inorder                              #
# --------------------------------------------------------------------------- #
# Node i of the rebuilt tree is preorder[i]; the inorder positions are indexed
# once (map, or sort plus binary search in C) so no range is rescanned.

_register(
    "construct-tree-from-preorder-and-inorder",
    python=_PY + r'''

def main():
    parts = read_line().split("|")
    pre = [int(x) for x in parts[0].split()]
    ino = [int(x) for x in parts[1].split()]
    n = len(pre)
    pos = {value: index for index, value in enumerate(ino)}
    val = list(pre)
    left = [-1] * n
    right = [-1] * n
    stack = [(0, n - 1, 0, n - 1, -1, 0)]
    while stack:
        pl, ph, il, ih, parent, side = stack.pop()
        if pl > ph:
            continue
        root = pl
        if parent != -1:
            if side == 0:
                left[parent] = root
            else:
                right[parent] = root
        cut = pos[pre[pl]]
        size = cut - il
        stack.append((pl + 1, pl + size, il, cut - 1, root, 0))
        stack.append((pl + size + 1, ph, cut + 1, ih, root, 1))
    print(serialize(val, left, right))


main()
''',
    javascript=_JS + r'''
const parts = line.split("|");
const pre = parts[0].split(/\s+/).filter(Boolean).map(Number);
const ino = parts[1].split(/\s+/).filter(Boolean).map(Number);
const n = pre.length;
const pos = new Map();
for (let i = 0; i < n; i++) pos.set(ino[i], i);
const t = { val: pre.slice(), left: new Array(n).fill(-1), right: new Array(n).fill(-1) };
const stack = [[0, n - 1, 0, n - 1, -1, 0]];
while (stack.length) {
  const [pl, ph, il, ih, parent, side] = stack.pop();
  if (pl > ph) continue;
  const root = pl;
  if (parent !== -1) {
    if (side === 0) t.left[parent] = root;
    else t.right[parent] = root;
  }
  const cut = pos.get(pre[pl]);
  const size = cut - il;
  stack.push([pl + 1, pl + size, il, cut - 1, root, 0]);
  stack.push([pl + size + 1, ph, cut + 1, ih, root, 1]);
}
console.log(serializeTree(t, 0));
''',
    java=_java(
        body="",
        main=r'''        String[] parts = readLine().split("\\|");
        StringTokenizer pt = new StringTokenizer(parts[0]);
        int n = pt.countTokens();
        long[] pre = new long[n];
        for (int i = 0; i < n; i++) pre[i] = Long.parseLong(pt.nextToken());
        StringTokenizer it = new StringTokenizer(parts[1]);
        HashMap<Long, Integer> pos = new HashMap<>(n * 2);
        for (int i = 0; i < n; i++) pos.put(Long.parseLong(it.nextToken()), i);
        Tree t = new Tree();
        t.n = n;
        t.val = pre;
        t.left = new int[n];
        t.right = new int[n];
        Arrays.fill(t.left, -1);
        Arrays.fill(t.right, -1);
        int[][] stack = new int[n + 2][];
        int sp = 0;
        stack[sp++] = new int[] {0, n - 1, 0, n - 1, -1, 0};
        while (sp > 0) {
            int[] frame = stack[--sp];
            int pl = frame[0], ph = frame[1], il = frame[2], parent = frame[4], side = frame[5];
            int ih = frame[3];
            if (pl > ph) continue;
            int root = pl;
            if (parent != -1) {
                if (side == 0) t.left[parent] = root;
                else t.right[parent] = root;
            }
            int cut = pos.get(pre[pl]);
            int size = cut - il;
            if (sp + 2 >= stack.length) stack = Arrays.copyOf(stack, stack.length * 2);
            stack[sp++] = new int[] {pl + 1, pl + size, il, cut - 1, root, 0};
            stack[sp++] = new int[] {pl + size + 1, ph, cut + 1, ih, root, 1};
        }
        System.out.println(serializeTree(t, 0));''',
    ),
    cpp=_cpp(
        body="",
        main=r'''    std::vector<std::string> parts = sections(line, 2);
    std::vector<long long> pre, ino;
    {
        std::istringstream in(parts[0]);
        long long v;
        while (in >> v) pre.push_back(v);
        std::istringstream in2(parts[1]);
        while (in2 >> v) ino.push_back(v);
    }
    int n = (int)pre.size();
    std::unordered_map<long long, int> pos;
    pos.reserve(n * 2);
    for (int i = 0; i < n; i++) pos[ino[i]] = i;
    Tree t;
    t.val = pre;
    t.left.assign(n, -1);
    t.right.assign(n, -1);
    struct Frame { int pl, ph, il, ih, parent, side; };
    std::vector<Frame> stack;
    stack.push_back({0, n - 1, 0, n - 1, -1, 0});
    while (!stack.empty()) {
        Frame f = stack.back();
        stack.pop_back();
        if (f.pl > f.ph) continue;
        int root = f.pl;
        if (f.parent != -1) {
            if (f.side == 0) t.left[f.parent] = root;
            else t.right[f.parent] = root;
        }
        int cut = pos[pre[f.pl]];
        int size = cut - f.il;
        stack.push_back({f.pl + 1, f.pl + size, f.il, cut - 1, root, 0});
        stack.push_back({f.pl + size + 1, f.ph, cut + 1, f.ih, root, 1});
    }
    std::cout << serializeTree(t) << "\n";''',
    ),
    c=_c(
        body=r'''
typedef struct {
    long long value;
    int index;
} Entry;

static int compare_entries(const void* a, const void* b) {
    long long x = ((const Entry*)a)->value;
    long long y = ((const Entry*)b)->value;
    return x < y ? -1 : (x > y ? 1 : 0);
}

/* Values are distinct, so a sorted table plus binary search replaces a hash
   map and still costs O(log n) per root. */
static int position_of(const Entry* table, int n, long long value) {
    int lo = 0;
    int hi = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (table[mid].value == value) return table[mid].index;
        if (table[mid].value < value) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}

static int read_values(char* text, long long** out) {
    int n = count_tokens(text);
    long long* values = (long long*)malloc(sizeof(long long) * (n > 0 ? n : 1));
    int m = 0;
    char* save = NULL;
    for (char* tok = strtok_r(text, " \t\r", &save); tok != NULL;
         tok = strtok_r(NULL, " \t\r", &save)) {
        values[m++] = atoll(tok);
    }
    *out = values;
    return m;
}
''',
        main=r'''    char* parts[4];
    split_sections(line, parts, 4);
    long long* pre = NULL;
    long long* ino = NULL;
    int n = read_values(parts[0], &pre);
    read_values(parts[1], &ino);
    Entry* table = (Entry*)malloc(sizeof(Entry) * (n > 0 ? n : 1));
    for (int i = 0; i < n; i++) {
        table[i].value = ino[i];
        table[i].index = i;
    }
    qsort(table, (size_t)n, sizeof(Entry), compare_entries);
    Tree t;
    t.n = n;
    t.val = pre;
    t.left = (int*)malloc(sizeof(int) * (n > 0 ? n : 1));
    t.right = (int*)malloc(sizeof(int) * (n > 0 ? n : 1));
    for (int i = 0; i < n; i++) {
        t.left[i] = -1;
        t.right[i] = -1;
    }
    int cap = 2 * n + 8;
    int* frames = (int*)malloc(sizeof(int) * 6 * (size_t)cap);
    int sp = 0;
    frames[0] = 0;
    frames[1] = n - 1;
    frames[2] = 0;
    frames[3] = n - 1;
    frames[4] = -1;
    frames[5] = 0;
    sp = 1;
    while (sp > 0) {
        sp--;
        int* f = frames + 6 * sp;
        int pl = f[0], ph = f[1], il = f[2], ih = f[3], parent = f[4], side = f[5];
        if (pl > ph) continue;
        int root = pl;
        if (parent != -1) {
            if (side == 0) t.left[parent] = root;
            else t.right[parent] = root;
        }
        int cut = position_of(table, n, pre[pl]);
        int size = cut - il;
        int* a = frames + 6 * sp;
        a[0] = pl + 1; a[1] = pl + size; a[2] = il; a[3] = cut - 1; a[4] = root; a[5] = 0;
        sp++;
        int* b = frames + 6 * sp;
        b[0] = pl + size + 1; b[1] = ph; b[2] = cut + 1; b[3] = ih; b[4] = root; b[5] = 1;
        sp++;
    }
    print_tree(t, 0);''',
    ),
)


# --------------------------------------------------------------------------- #
#  09 · validate-binary-search-tree                                           #
# --------------------------------------------------------------------------- #
# An in-order walk must produce strictly increasing values.

_register(
    "validate-binary-search-tree",
    python=_PY + r'''

def main():
    val, left, right = parse_tree(read_line())
    if not val:
        print("true")
        return
    stack = []
    node = 0
    previous = None
    ok = True
    while stack or node != -1:
        while node != -1:
            stack.append(node)
            node = left[node]
        node = stack.pop()
        if previous is not None and val[node] <= previous:
            ok = False
            break
        previous = val[node]
        node = right[node]
    print("true" if ok else "false")


main()
''',
    javascript=_JS + r'''
const t = parseTree(line);
if (t.val.length === 0) {
  console.log("true");
} else {
  const stack = [];
  let node = 0;
  let previous = null;
  let ok = true;
  while (stack.length || node !== -1) {
    while (node !== -1) {
      stack.push(node);
      node = t.left[node];
    }
    node = stack.pop();
    if (previous !== null && t.val[node] <= previous) {
      ok = false;
      break;
    }
    previous = t.val[node];
    node = t.right[node];
  }
  console.log(ok ? "true" : "false");
}
''',
    java=_java(
        body="",
        main=r'''        Tree t = parseTree(readLine());
        if (t.n == 0) {
            System.out.println("true");
            return;
        }
        int[] stack = new int[t.n + 2];
        int sp = 0;
        int node = 0;
        boolean seen = false;
        long previous = 0;
        boolean ok = true;
        while (sp > 0 || node != -1) {
            while (node != -1) {
                stack[sp++] = node;
                node = t.left[node];
            }
            node = stack[--sp];
            if (seen && t.val[node] <= previous) {
                ok = false;
                break;
            }
            seen = true;
            previous = t.val[node];
            node = t.right[node];
        }
        System.out.println(ok ? "true" : "false");''',
    ),
    cpp=_cpp(
        body="",
        main=r'''    Tree t = parseTree(line);
    if (t.val.empty()) {
        std::cout << "true\n";
        return 0;
    }
    std::vector<int> stack;
    int node = 0;
    bool seen = false;
    long long previous = 0;
    bool ok = true;
    while (!stack.empty() || node != -1) {
        while (node != -1) {
            stack.push_back(node);
            node = t.left[node];
        }
        node = stack.back();
        stack.pop_back();
        if (seen && t.val[node] <= previous) {
            ok = false;
            break;
        }
        seen = true;
        previous = t.val[node];
        node = t.right[node];
    }
    std::cout << (ok ? "true" : "false") << "\n";''',
    ),
    c=_c(
        body="",
        main=r'''    Tree t = parse_tree(line);
    if (t.n == 0) {
        printf("true\n");
        return 0;
    }
    int* stack = (int*)malloc(sizeof(int) * (t.n + 2));
    int sp = 0;
    int node = 0;
    int seen = 0;
    long long previous = 0;
    int ok = 1;
    while (sp > 0 || node != -1) {
        while (node != -1) {
            stack[sp++] = node;
            node = t.left[node];
        }
        node = stack[--sp];
        if (seen && t.val[node] <= previous) {
            ok = 0;
            break;
        }
        seen = 1;
        previous = t.val[node];
        node = t.right[node];
    }
    printf("%s\n", ok ? "true" : "false");''',
    ),
)


# --------------------------------------------------------------------------- #
#  10 · kth-smallest-element-in-a-bst                                         #
# --------------------------------------------------------------------------- #

_register(
    "kth-smallest-element-in-a-bst",
    python=_PY + r'''

def main():
    parts = read_line().split("|")
    k = int(parts[0].strip())
    val, left, right = parse_tree(parts[1])
    stack = []
    node = 0
    seen = 0
    while stack or node != -1:
        while node != -1:
            stack.append(node)
            node = left[node]
        node = stack.pop()
        seen += 1
        if seen == k:
            print(val[node])
            return
        node = right[node]


main()
''',
    javascript=_JS + r'''
const parts = line.split("|");
const k = Number(parts[0].trim());
const t = parseTree(parts[1]);
const stack = [];
let node = 0;
let seen = 0;
while (stack.length || node !== -1) {
  while (node !== -1) {
    stack.push(node);
    node = t.left[node];
  }
  node = stack.pop();
  seen += 1;
  if (seen === k) {
    console.log(String(t.val[node]));
    break;
  }
  node = t.right[node];
}
''',
    java=_java(
        body="",
        main=r'''        String[] parts = readLine().split("\\|");
        int k = Integer.parseInt(parts[0].trim());
        Tree t = parseTree(parts[1]);
        int[] stack = new int[t.n + 2];
        int sp = 0;
        int node = 0;
        int seen = 0;
        while (sp > 0 || node != -1) {
            while (node != -1) {
                stack[sp++] = node;
                node = t.left[node];
            }
            node = stack[--sp];
            if (++seen == k) {
                System.out.println(t.val[node]);
                return;
            }
            node = t.right[node];
        }''',
    ),
    cpp=_cpp(
        body="",
        main=r'''    std::vector<std::string> parts = sections(line, 2);
    int k = std::stoi(parts[0]);
    Tree t = parseTree(parts[1]);
    std::vector<int> stack;
    int node = 0;
    int seen = 0;
    while (!stack.empty() || node != -1) {
        while (node != -1) {
            stack.push_back(node);
            node = t.left[node];
        }
        node = stack.back();
        stack.pop_back();
        if (++seen == k) {
            std::cout << t.val[node] << "\n";
            return 0;
        }
        node = t.right[node];
    }''',
    ),
    c=_c(
        body="",
        main=r'''    char* parts[4];
    split_sections(line, parts, 4);
    int k = atoi(parts[0]);
    Tree t = parse_tree(parts[1]);
    int* stack = (int*)malloc(sizeof(int) * (t.n + 2));
    int sp = 0;
    int node = 0;
    int seen = 0;
    while (sp > 0 || node != -1) {
        while (node != -1) {
            stack[sp++] = node;
            node = t.left[node];
        }
        node = stack[--sp];
        if (++seen == k) {
            printf("%lld\n", t.val[node]);
            return 0;
        }
        node = t.right[node];
    }''',
    ),
)


# --------------------------------------------------------------------------- #
#  11 · lowest-common-ancestor-of-a-bst                                       #
# --------------------------------------------------------------------------- #

_register(
    "lowest-common-ancestor-of-a-bst",
    python=_PY + r'''

def main():
    parts = read_line().split("|")
    head = parts[0].split()
    p, q = int(head[0]), int(head[1])
    if p > q:
        p, q = q, p
    val, left, right = parse_tree(parts[1])
    node = 0
    while True:
        if q < val[node]:
            node = left[node]
        elif p > val[node]:
            node = right[node]
        else:
            print(val[node])
            return


main()
''',
    javascript=_JS + r'''
const parts = line.split("|");
const head = parts[0].split(/\s+/).filter(Boolean).map(Number);
let p = head[0];
let q = head[1];
if (p > q) {
  const tmp = p;
  p = q;
  q = tmp;
}
const t = parseTree(parts[1]);
let node = 0;
for (;;) {
  if (q < t.val[node]) node = t.left[node];
  else if (p > t.val[node]) node = t.right[node];
  else {
    console.log(String(t.val[node]));
    break;
  }
}
''',
    java=_java(
        body="",
        main=r'''        String[] parts = readLine().split("\\|");
        StringTokenizer head = new StringTokenizer(parts[0]);
        long p = Long.parseLong(head.nextToken());
        long q = Long.parseLong(head.nextToken());
        if (p > q) {
            long tmp = p;
            p = q;
            q = tmp;
        }
        Tree t = parseTree(parts[1]);
        int node = 0;
        while (true) {
            if (q < t.val[node]) {
                node = t.left[node];
            } else if (p > t.val[node]) {
                node = t.right[node];
            } else {
                System.out.println(t.val[node]);
                return;
            }
        }''',
    ),
    cpp=_cpp(
        body="",
        main=r'''    std::vector<std::string> parts = sections(line, 2);
    long long p = 0;
    long long q = 0;
    {
        std::istringstream in(parts[0]);
        in >> p >> q;
    }
    if (p > q) std::swap(p, q);
    Tree t = parseTree(parts[1]);
    int node = 0;
    for (;;) {
        if (q < t.val[node]) {
            node = t.left[node];
        } else if (p > t.val[node]) {
            node = t.right[node];
        } else {
            std::cout << t.val[node] << "\n";
            return 0;
        }
    }''',
    ),
    c=_c(
        body="",
        main=r'''    char* parts[4];
    split_sections(line, parts, 4);
    long long p = 0;
    long long q = 0;
    sscanf(parts[0], "%lld %lld", &p, &q);
    if (p > q) {
        long long tmp = p;
        p = q;
        q = tmp;
    }
    Tree t = parse_tree(parts[1]);
    int node = 0;
    for (;;) {
        if (q < t.val[node]) {
            node = t.left[node];
        } else if (p > t.val[node]) {
            node = t.right[node];
        } else {
            printf("%lld\n", t.val[node]);
            return 0;
        }
    }''',
    ),
)


# --------------------------------------------------------------------------- #
#  Trie helpers for the command-stream and grid problems                      #
# --------------------------------------------------------------------------- #
# C, C++, Java and JavaScript all use the same first-child / next-sibling trie:
# three small arrays instead of 26 pointers per node, which keeps the memory
# flat even when the whole command stream is one long line.

_C_TRIE = r'''
static int* first_child;
static int* next_sibling;
static char* node_ch;
static char* terminal;
static int node_count;

static void trie_init(int cap) {
    if (cap < 2) cap = 2;
    first_child = (int*)malloc(sizeof(int) * cap);
    next_sibling = (int*)malloc(sizeof(int) * cap);
    node_ch = (char*)malloc((size_t)cap);
    terminal = (char*)calloc((size_t)cap, 1);
    first_child[0] = -1;
    next_sibling[0] = -1;
    node_ch[0] = 0;
    node_count = 1;
}

static int find_child(int node, char c) {
    for (int child = first_child[node]; child != -1; child = next_sibling[child]) {
        if (node_ch[child] == c) return child;
    }
    return -1;
}

static int add_child(int node, char c) {
    int child = node_count++;
    first_child[child] = -1;
    next_sibling[child] = first_child[node];
    node_ch[child] = c;
    terminal[child] = 0;
    first_child[node] = child;
    return child;
}

static char* trim(char* s) {
    while (*s == ' ' || *s == '\t' || *s == '\r') s++;
    size_t n = strlen(s);
    while (n > 0 && (s[n - 1] == ' ' || s[n - 1] == '\t' || s[n - 1] == '\r')) s[--n] = '\0';
    return s;
}
'''

_JAVA_TRIE = r'''
    static int[] firstChild;
    static int[] nextSibling;
    static char[] nodeCh;
    static boolean[] terminal;
    static int nodeCount;

    static void trieInit(int cap) {
        if (cap < 2) cap = 2;
        firstChild = new int[cap];
        nextSibling = new int[cap];
        nodeCh = new char[cap];
        terminal = new boolean[cap];
        firstChild[0] = -1;
        nextSibling[0] = -1;
        nodeCount = 1;
    }

    static int findChild(int node, char c) {
        for (int child = firstChild[node]; child != -1; child = nextSibling[child]) {
            if (nodeCh[child] == c) return child;
        }
        return -1;
    }

    static int addChild(int node, char c) {
        int child = nodeCount++;
        firstChild[child] = -1;
        nextSibling[child] = firstChild[node];
        nodeCh[child] = c;
        firstChild[node] = child;
        return child;
    }
'''

_CPP_TRIE = r'''
std::vector<int> firstChild;
std::vector<int> nextSibling;
std::vector<char> nodeCh;
std::vector<char> terminal;

void trieInit() {
    firstChild.assign(1, -1);
    nextSibling.assign(1, -1);
    nodeCh.assign(1, 0);
    terminal.assign(1, 0);
}

int findChild(int node, char c) {
    for (int child = firstChild[node]; child != -1; child = nextSibling[child]) {
        if (nodeCh[child] == c) return child;
    }
    return -1;
}

int addChild(int node, char c) {
    firstChild.push_back(-1);
    nextSibling.push_back(firstChild[node]);
    nodeCh.push_back(c);
    terminal.push_back(0);
    int child = (int)firstChild.size() - 1;
    firstChild[node] = child;
    return child;
}

std::vector<std::string> splitOn(const std::string& line, char sep, int expected) {
    std::vector<std::string> parts;
    std::string current;
    for (char ch : line) {
        if (ch == sep) {
            parts.push_back(current);
            current.clear();
        } else {
            current += ch;
        }
    }
    parts.push_back(current);
    while ((int)parts.size() < expected) parts.push_back("");
    return parts;
}

std::vector<std::string> commands(const std::string& line) {
    std::vector<std::string> out;
    std::string current;
    for (char ch : line) {
        if (ch == ';') {
            out.push_back(current);
            current.clear();
        } else {
            current += ch;
        }
    }
    out.push_back(current);
    for (std::string& part : out) {
        size_t start = part.find_first_not_of(" \t\r");
        size_t end = part.find_last_not_of(" \t\r");
        part = start == std::string::npos ? std::string() : part.substr(start, end - start + 1);
    }
    return out;
}
'''

_JS_TRIE = r'''
let firstChild = [-1];
let nextSibling = [-1];
let nodeCh = [""];
let terminal = [false];

function findChild(node, c) {
  for (let child = firstChild[node]; child !== -1; child = nextSibling[child]) {
    if (nodeCh[child] === c) return child;
  }
  return -1;
}

function addChild(node, c) {
  firstChild.push(-1);
  nextSibling.push(firstChild[node]);
  nodeCh.push(c);
  terminal.push(false);
  const child = firstChild.length - 1;
  firstChild[node] = child;
  return child;
}

function commands(text) {
  return text.split(";").map((part) => part.trim());
}
'''


# --------------------------------------------------------------------------- #
#  12 · implement-trie-prefix-tree                                            #
# --------------------------------------------------------------------------- #

_register(
    "implement-trie-prefix-tree",
    python=r'''
import sys


def main():
    line = sys.stdin.readline().rstrip("\n")
    children = [{}]
    terminal = [False]
    out = []
    for command in line.split(";")[1:]:
        command = command.strip()
        if not command:
            continue
        op, _, word = command.partition(" ")
        word = word.strip()
        if op == "insert":
            node = 0
            for ch in word:
                nxt = children[node].get(ch)
                if nxt is None:
                    children.append({})
                    terminal.append(False)
                    nxt = len(children) - 1
                    children[node][ch] = nxt
                node = nxt
            terminal[node] = True
            continue
        node = 0
        ok = True
        for ch in word:
            nxt = children[node].get(ch)
            if nxt is None:
                ok = False
                break
            node = nxt
        if op == "search":
            ok = ok and terminal[node]
        out.append("true" if ok else "false")
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


main()
''',
    javascript=_JS + _JS_TRIE + r'''
const out = [];
const parts = commands(line);
for (let i = 1; i < parts.length; i++) {
  const command = parts[i];
  if (!command) continue;
  const space = command.indexOf(" ");
  const op = space === -1 ? command : command.slice(0, space);
  const word = space === -1 ? "" : command.slice(space + 1).trim();
  if (op === "insert") {
    let node = 0;
    for (const ch of word) {
      let next = findChild(node, ch);
      if (next === -1) next = addChild(node, ch);
      node = next;
    }
    terminal[node] = true;
    continue;
  }
  let node = 0;
  let ok = true;
  for (const ch of word) {
    const next = findChild(node, ch);
    if (next === -1) {
      ok = false;
      break;
    }
    node = next;
  }
  if (op === "search") ok = ok && terminal[node];
  out.push(ok ? "true" : "false");
}
process.stdout.write(out.join("\n") + (out.length ? "\n" : ""));
''',
    java=_java(
        body=_JAVA_TRIE,
        main=r'''        String line = readLine();
        trieInit(line.length() + 2);
        StringBuilder sb = new StringBuilder();
        String[] parts = line.split(";");
        for (int i = 1; i < parts.length; i++) {
            String command = parts[i].trim();
            if (command.isEmpty()) continue;
            int space = command.indexOf(' ');
            String op = space == -1 ? command : command.substring(0, space);
            String word = space == -1 ? "" : command.substring(space + 1).trim();
            if (op.equals("insert")) {
                int node = 0;
                for (int j = 0; j < word.length(); j++) {
                    char ch = word.charAt(j);
                    int next = findChild(node, ch);
                    if (next == -1) next = addChild(node, ch);
                    node = next;
                }
                terminal[node] = true;
                continue;
            }
            int node = 0;
            boolean ok = true;
            for (int j = 0; j < word.length(); j++) {
                int next = findChild(node, word.charAt(j));
                if (next == -1) {
                    ok = false;
                    break;
                }
                node = next;
            }
            if (op.equals("search")) ok = ok && terminal[node];
            sb.append(ok ? "true" : "false").append('\n');
        }
        System.out.print(sb);''',
        tree=False,
    ),
    cpp=_cpp(
        body=_CPP_TRIE,
        main=r'''    trieInit();
    std::vector<std::string> parts = commands(line);
    std::string out;
    for (size_t i = 1; i < parts.size(); i++) {
        const std::string& command = parts[i];
        if (command.empty()) continue;
        size_t space = command.find(' ');
        std::string op = space == std::string::npos ? command : command.substr(0, space);
        std::string word = space == std::string::npos ? "" : command.substr(space + 1);
        if (op == "insert") {
            int node = 0;
            for (char ch : word) {
                int next = findChild(node, ch);
                if (next == -1) next = addChild(node, ch);
                node = next;
            }
            terminal[node] = 1;
            continue;
        }
        int node = 0;
        bool ok = true;
        for (char ch : word) {
            int next = findChild(node, ch);
            if (next == -1) {
                ok = false;
                break;
            }
            node = next;
        }
        if (op == "search") ok = ok && terminal[node];
        out += ok ? "true\n" : "false\n";
    }
    std::cout << out;''',
        tree=False,
    ),
    c=_c(
        body=_C_TRIE,
        main=r'''    trie_init((int)strlen(line) + 2);
    char* save = NULL;
    int index = 0;
    for (char* raw = strtok_r(line, ";", &save); raw != NULL; raw = strtok_r(NULL, ";", &save)) {
        char* command = trim(raw);
        if (index++ == 0 || *command == '\0') continue;
        char* space = strchr(command, ' ');
        char* word = (char*)"";
        if (space != NULL) {
            *space = '\0';
            word = trim(space + 1);
        }
        if (strcmp(command, "insert") == 0) {
            int node = 0;
            for (char* p = word; *p; p++) {
                int next = find_child(node, *p);
                if (next == -1) next = add_child(node, *p);
                node = next;
            }
            terminal[node] = 1;
            continue;
        }
        int node = 0;
        int ok = 1;
        for (char* p = word; *p; p++) {
            int next = find_child(node, *p);
            if (next == -1) {
                ok = 0;
                break;
            }
            node = next;
        }
        if (strcmp(command, "search") == 0) ok = ok && terminal[node];
        fputs(ok ? "true\n" : "false\n", stdout);
    }''',
        tree=False,
    ),
)


# --------------------------------------------------------------------------- #
#  13 · add-and-search-words-data-structure                                   #
# --------------------------------------------------------------------------- #
# A '.' fans out over the children of the current node, so the search is a
# depth-first walk of the trie rather than a single descent.

_register(
    "add-and-search-words-data-structure",
    python=r'''
import sys


def main():
    line = sys.stdin.readline().rstrip("\n")
    children = [{}]
    terminal = [False]
    out = []
    for command in line.split(";")[1:]:
        command = command.strip()
        if not command:
            continue
        op, _, word = command.partition(" ")
        word = word.strip()
        if op == "addWord":
            node = 0
            for ch in word:
                nxt = children[node].get(ch)
                if nxt is None:
                    children.append({})
                    terminal.append(False)
                    nxt = len(children) - 1
                    children[node][ch] = nxt
                node = nxt
            terminal[node] = True
            continue
        found = False
        stack = [(0, 0)]
        while stack:
            node, index = stack.pop()
            if index == len(word):
                if terminal[node]:
                    found = True
                    break
                continue
            ch = word[index]
            if ch == ".":
                for nxt in children[node].values():
                    stack.append((nxt, index + 1))
            else:
                nxt = children[node].get(ch)
                if nxt is not None:
                    stack.append((nxt, index + 1))
        out.append("true" if found else "false")
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


main()
''',
    javascript=_JS + _JS_TRIE + r'''
const out = [];
const parts = commands(line);
for (let i = 1; i < parts.length; i++) {
  const command = parts[i];
  if (!command) continue;
  const space = command.indexOf(" ");
  const op = space === -1 ? command : command.slice(0, space);
  const word = space === -1 ? "" : command.slice(space + 1).trim();
  if (op === "addWord") {
    let node = 0;
    for (const ch of word) {
      let next = findChild(node, ch);
      if (next === -1) next = addChild(node, ch);
      node = next;
    }
    terminal[node] = true;
    continue;
  }
  let found = false;
  const stack = [[0, 0]];
  while (stack.length) {
    const [node, index] = stack.pop();
    if (index === word.length) {
      if (terminal[node]) {
        found = true;
        break;
      }
      continue;
    }
    const ch = word[index];
    if (ch === ".") {
      for (let child = firstChild[node]; child !== -1; child = nextSibling[child]) {
        stack.push([child, index + 1]);
      }
    } else {
      const next = findChild(node, ch);
      if (next !== -1) stack.push([next, index + 1]);
    }
  }
  out.push(found ? "true" : "false");
}
process.stdout.write(out.join("\n") + (out.length ? "\n" : ""));
''',
    java=_java(
        body=_JAVA_TRIE,
        main=r'''        String line = readLine();
        trieInit(line.length() + 2);
        StringBuilder sb = new StringBuilder();
        String[] parts = line.split(";");
        int[] stackNode = new int[64];
        int[] stackIndex = new int[64];
        for (int i = 1; i < parts.length; i++) {
            String command = parts[i].trim();
            if (command.isEmpty()) continue;
            int space = command.indexOf(' ');
            String op = space == -1 ? command : command.substring(0, space);
            String word = space == -1 ? "" : command.substring(space + 1).trim();
            if (op.equals("addWord")) {
                int node = 0;
                for (int j = 0; j < word.length(); j++) {
                    char ch = word.charAt(j);
                    int next = findChild(node, ch);
                    if (next == -1) next = addChild(node, ch);
                    node = next;
                }
                terminal[node] = true;
                continue;
            }
            boolean found = false;
            int sp = 0;
            stackNode[sp] = 0;
            stackIndex[sp] = 0;
            sp++;
            while (sp > 0) {
                sp--;
                int node = stackNode[sp];
                int index = stackIndex[sp];
                if (index == word.length()) {
                    if (terminal[node]) {
                        found = true;
                        break;
                    }
                    continue;
                }
                char ch = word.charAt(index);
                if (sp + 28 >= stackNode.length) {
                    stackNode = Arrays.copyOf(stackNode, stackNode.length * 2);
                    stackIndex = Arrays.copyOf(stackIndex, stackIndex.length * 2);
                }
                if (ch == '.') {
                    for (int child = firstChild[node]; child != -1; child = nextSibling[child]) {
                        stackNode[sp] = child;
                        stackIndex[sp] = index + 1;
                        sp++;
                    }
                } else {
                    int next = findChild(node, ch);
                    if (next != -1) {
                        stackNode[sp] = next;
                        stackIndex[sp] = index + 1;
                        sp++;
                    }
                }
            }
            sb.append(found ? "true" : "false").append('\n');
        }
        System.out.print(sb);''',
        tree=False,
    ),
    cpp=_cpp(
        body=_CPP_TRIE,
        main=r'''    trieInit();
    std::vector<std::string> parts = commands(line);
    std::string out;
    for (size_t i = 1; i < parts.size(); i++) {
        const std::string& command = parts[i];
        if (command.empty()) continue;
        size_t space = command.find(' ');
        std::string op = space == std::string::npos ? command : command.substr(0, space);
        std::string word = space == std::string::npos ? "" : command.substr(space + 1);
        if (op == "addWord") {
            int node = 0;
            for (char ch : word) {
                int next = findChild(node, ch);
                if (next == -1) next = addChild(node, ch);
                node = next;
            }
            terminal[node] = 1;
            continue;
        }
        bool found = false;
        std::vector<std::pair<int, int>> stack;
        stack.push_back({0, 0});
        while (!stack.empty()) {
            std::pair<int, int> top = stack.back();
            stack.pop_back();
            if (top.second == (int)word.size()) {
                if (terminal[top.first]) {
                    found = true;
                    break;
                }
                continue;
            }
            char ch = word[top.second];
            if (ch == '.') {
                for (int child = firstChild[top.first]; child != -1; child = nextSibling[child]) {
                    stack.push_back({child, top.second + 1});
                }
            } else {
                int next = findChild(top.first, ch);
                if (next != -1) stack.push_back({next, top.second + 1});
            }
        }
        out += found ? "true\n" : "false\n";
    }
    std::cout << out;''',
        tree=False,
    ),
    c=_c(
        body=_C_TRIE,
        main=r'''    trie_init((int)strlen(line) + 2);
    int stack_cap = 1024;
    int* stack_node = (int*)malloc(sizeof(int) * stack_cap);
    int* stack_index = (int*)malloc(sizeof(int) * stack_cap);
    char* save = NULL;
    int seen = 0;
    for (char* raw = strtok_r(line, ";", &save); raw != NULL; raw = strtok_r(NULL, ";", &save)) {
        char* command = trim(raw);
        if (seen++ == 0 || *command == '\0') continue;
        char* space = strchr(command, ' ');
        char* word = (char*)"";
        if (space != NULL) {
            *space = '\0';
            word = trim(space + 1);
        }
        if (strcmp(command, "addWord") == 0) {
            int node = 0;
            for (char* p = word; *p; p++) {
                int next = find_child(node, *p);
                if (next == -1) next = add_child(node, *p);
                node = next;
            }
            terminal[node] = 1;
            continue;
        }
        int length = (int)strlen(word);
        int found = 0;
        int sp = 0;
        stack_node[sp] = 0;
        stack_index[sp] = 0;
        sp++;
        while (sp > 0) {
            sp--;
            int node = stack_node[sp];
            int index = stack_index[sp];
            if (index == length) {
                if (terminal[node]) {
                    found = 1;
                    break;
                }
                continue;
            }
            if (sp + 32 >= stack_cap) {
                stack_cap *= 2;
                stack_node = (int*)realloc(stack_node, sizeof(int) * stack_cap);
                stack_index = (int*)realloc(stack_index, sizeof(int) * stack_cap);
            }
            char ch = word[index];
            if (ch == '.') {
                for (int child = first_child[node]; child != -1; child = next_sibling[child]) {
                    stack_node[sp] = child;
                    stack_index[sp] = index + 1;
                    sp++;
                }
            } else {
                int next = find_child(node, ch);
                if (next != -1) {
                    stack_node[sp] = next;
                    stack_index[sp] = index + 1;
                    sp++;
                }
            }
        }
        fputs(found ? "true\n" : "false\n", stdout);
    }''',
        tree=False,
    ),
)


# --------------------------------------------------------------------------- #
#  14 · word-search-ii                                                        #
# --------------------------------------------------------------------------- #
# One walk of the grid against a trie of all the words, rather than one grid
# search per word.

_register(
    "word-search-ii",
    python=r'''
import sys


def main():
    sys.setrecursionlimit(10000)
    line = sys.stdin.readline().rstrip("\n")
    head, grid_part, words_part = line.split("|")
    rows, cols = (int(x) for x in head.split())
    grid = grid_part.split()
    words = words_part.split()
    children = [{}]
    word_at = [None]
    for word in words:
        node = 0
        for ch in word:
            nxt = children[node].get(ch)
            if nxt is None:
                children.append({})
                word_at.append(None)
                nxt = len(children) - 1
                children[node][ch] = nxt
            node = nxt
        word_at[node] = word
    found = set()
    used = [[False] * cols for _ in range(rows)]

    def walk(r, c, node):
        nxt = children[node].get(grid[r][c])
        if nxt is None:
            return
        if word_at[nxt] is not None:
            found.add(word_at[nxt])
        used[r][c] = True
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not used[nr][nc]:
                walk(nr, nc, nxt)
        used[r][c] = False

    for r in range(rows):
        for c in range(cols):
            walk(r, c, 0)
    out = sorted(found)
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


main()
''',
    javascript=_JS + _JS_TRIE + r'''
const parts = line.split("|");
const [rows, cols] = parts[0].split(/\s+/).filter(Boolean).map(Number);
const grid = parts[1].split(/\s+/).filter(Boolean);
const words = parts[2].split(/\s+/).filter(Boolean);
const wordAt = [null];
for (const word of words) {
  let node = 0;
  for (const ch of word) {
    let next = findChild(node, ch);
    if (next === -1) {
      next = addChild(node, ch);
      wordAt.push(null);
    }
    node = next;
  }
  wordAt[node] = word;
}
const found = new Set();
const used = [];
for (let r = 0; r < rows; r++) used.push(new Array(cols).fill(false));

function walk(r, c, node) {
  const next = findChild(node, grid[r][c]);
  if (next === -1) return;
  if (wordAt[next] !== null && wordAt[next] !== undefined) found.add(wordAt[next]);
  used[r][c] = true;
  const steps = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  for (const [dr, dc] of steps) {
    const nr = r + dr;
    const nc = c + dc;
    if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !used[nr][nc]) walk(nr, nc, next);
  }
  used[r][c] = false;
}

for (let r = 0; r < rows; r++) {
  for (let c = 0; c < cols; c++) walk(r, c, 0);
}
const out = [...found].sort();
process.stdout.write(out.join("\n") + (out.length ? "\n" : ""));
''',
    java=_java(
        body=_JAVA_TRIE
        + r'''
    static int rows;
    static int cols;
    static String[] grid;
    static boolean[][] used;
    static String[] wordAt;
    static TreeSet<String> found = new TreeSet<>();

    static void walk(int r, int c, int node) {
        int next = findChild(node, grid[r].charAt(c));
        if (next == -1) return;
        if (wordAt[next] != null) found.add(wordAt[next]);
        used[r][c] = true;
        int[][] steps = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
        for (int[] step : steps) {
            int nr = r + step[0];
            int nc = c + step[1];
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !used[nr][nc]) walk(nr, nc, next);
        }
        used[r][c] = false;
    }
''',
        main=r'''        String[] parts = readLine().split("\\|");
        StringTokenizer head = new StringTokenizer(parts[0]);
        rows = Integer.parseInt(head.nextToken());
        cols = Integer.parseInt(head.nextToken());
        StringTokenizer gt = new StringTokenizer(parts[1]);
        grid = new String[rows];
        for (int i = 0; i < rows; i++) grid[i] = gt.nextToken();
        StringTokenizer wt = new StringTokenizer(parts[2]);
        ArrayList<String> words = new ArrayList<>();
        while (wt.hasMoreTokens()) words.add(wt.nextToken());
        int cap = 1;
        for (String word : words) cap += word.length();
        trieInit(cap + 2);
        wordAt = new String[cap + 2];
        for (String word : words) {
            int node = 0;
            for (int j = 0; j < word.length(); j++) {
                char ch = word.charAt(j);
                int next = findChild(node, ch);
                if (next == -1) next = addChild(node, ch);
                node = next;
            }
            wordAt[node] = word;
        }
        used = new boolean[rows][cols];
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) walk(r, c, 0);
        }
        StringBuilder sb = new StringBuilder();
        for (String word : found) sb.append(word).append('\n');
        System.out.print(sb);''',
        tree=False,
    ),
    cpp=_cpp(
        body=_CPP_TRIE
        + r'''
int rowCount;
int colCount;
std::vector<std::string> gridRows;
std::vector<char> usedCell;
std::vector<std::string> wordAt;
std::set<std::string> foundWords;

void walk(int r, int c, int node) {
    int next = findChild(node, gridRows[r][c]);
    if (next == -1) return;
    if (!wordAt[next].empty()) foundWords.insert(wordAt[next]);
    usedCell[r * colCount + c] = 1;
    int steps[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
    for (int i = 0; i < 4; i++) {
        int nr = r + steps[i][0];
        int nc = c + steps[i][1];
        if (nr >= 0 && nr < rowCount && nc >= 0 && nc < colCount && !usedCell[nr * colCount + nc]) {
            walk(nr, nc, next);
        }
    }
    usedCell[r * colCount + c] = 0;
}
''',
        main=r'''    std::vector<std::string> parts = splitOn(line, '|', 3);
    {
        std::istringstream in(parts[0]);
        in >> rowCount >> colCount;
    }
    {
        std::istringstream in(parts[1]);
        std::string row;
        while (in >> row) gridRows.push_back(row);
    }
    std::vector<std::string> words;
    {
        std::istringstream in(parts[2]);
        std::string word;
        while (in >> word) words.push_back(word);
    }
    trieInit();
    wordAt.assign(1, "");
    for (const std::string& word : words) {
        int node = 0;
        for (char ch : word) {
            int next = findChild(node, ch);
            if (next == -1) {
                next = addChild(node, ch);
                wordAt.push_back("");
            }
            node = next;
        }
        wordAt[node] = word;
    }
    usedCell.assign((size_t)rowCount * colCount, 0);
    for (int r = 0; r < rowCount; r++) {
        for (int c = 0; c < colCount; c++) walk(r, c, 0);
    }
    std::string out;
    for (const std::string& word : foundWords) out += word + "\n";
    std::cout << out;''',
        tree=False,
    ),
    c=_c(
        body=_C_TRIE
        + r'''
static int rows;
static int cols;
static char** grid;
static char* used;
static char** word_at;
static char** hits;
static int hit_count;

static void walk(int r, int c, int node) {
    int next = find_child(node, grid[r][c]);
    if (next == -1) return;
    if (word_at[next] != NULL) {
        hits[hit_count++] = word_at[next];
        word_at[next] = NULL; /* report each word once */
    }
    used[r * cols + c] = 1;
    static const int dr[4] = {1, -1, 0, 0};
    static const int dc[4] = {0, 0, 1, -1};
    for (int i = 0; i < 4; i++) {
        int nr = r + dr[i];
        int nc = c + dc[i];
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !used[nr * cols + nc]) {
            walk(nr, nc, next);
        }
    }
    used[r * cols + c] = 0;
}

static int compare_strings(const void* a, const void* b) {
    return strcmp(*(const char**)a, *(const char**)b);
}
''',
        main=r'''    char* parts[4];
    split_sections(line, parts, 4);
    sscanf(parts[0], "%d %d", &rows, &cols);
    grid = (char**)malloc(sizeof(char*) * (size_t)(rows > 0 ? rows : 1));
    int gn = 0;
    char* save = NULL;
    for (char* tok = strtok_r(parts[1], " \t\r", &save); tok != NULL && gn < rows;
         tok = strtok_r(NULL, " \t\r", &save)) {
        grid[gn++] = tok;
    }
    int word_cap = count_tokens(parts[2]);
    char** words = (char**)malloc(sizeof(char*) * (size_t)(word_cap > 0 ? word_cap : 1));
    int wn = 0;
    char* save2 = NULL;
    int total_chars = 1;
    for (char* tok = strtok_r(parts[2], " \t\r", &save2); tok != NULL;
         tok = strtok_r(NULL, " \t\r", &save2)) {
        words[wn++] = tok;
        total_chars += (int)strlen(tok);
    }
    trie_init(total_chars + 2);
    word_at = (char**)calloc((size_t)(total_chars + 2), sizeof(char*));
    for (int i = 0; i < wn; i++) {
        int node = 0;
        for (char* p = words[i]; *p; p++) {
            int next = find_child(node, *p);
            if (next == -1) next = add_child(node, *p);
            node = next;
        }
        word_at[node] = words[i];
    }
    used = (char*)calloc((size_t)(rows * cols), 1);
    hits = (char**)malloc(sizeof(char*) * (size_t)(wn > 0 ? wn : 1));
    hit_count = 0;
    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++) walk(r, c, 0);
    }
    qsort(hits, (size_t)hit_count, sizeof(char*), compare_strings);
    for (int i = 0; i < hit_count; i++) printf("%s\n", hits[i]);''',
        tree=False,
    ),
)


# --------------------------------------------------------------------------- #
#  15 · top-k-frequent-elements                                               #
# --------------------------------------------------------------------------- #
# Sorting the values groups equal ones together, so the counts fall out of one
# pass; the second sort is (count descending, value ascending), which is the
# tie-break the statement fixes.

_register(
    "top-k-frequent-elements",
    python=r'''
import sys
from collections import Counter


def main():
    head, values_part = sys.stdin.readline().rstrip("\n").split("|")
    k = int(head.strip())
    counts = Counter(int(x) for x in values_part.split())
    order = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    print(" ".join(str(value) for value, _ in order[:k]))


main()
''',
    javascript=r'''
const input = require("fs").readFileSync(0, "utf8");
const line = input.split("\n")[0] ?? "";
const parts = line.split("|");
const k = Number(parts[0].trim());
const values = parts[1].split(/\s+/).filter(Boolean).map(Number);
values.sort((a, b) => a - b);
const pairs = [];
let i = 0;
while (i < values.length) {
  let j = i;
  while (j < values.length && values[j] === values[i]) j++;
  pairs.push([values[i], j - i]);
  i = j;
}
pairs.sort((a, b) => (b[1] - a[1]) || (a[0] - b[0]));
console.log(pairs.slice(0, k).map((pair) => String(pair[0])).join(" "));
''',
    java=_java(
        body="",
        main=r'''        String[] parts = readLine().split("\\|");
        int k = Integer.parseInt(parts[0].trim());
        StringTokenizer st = new StringTokenizer(parts[1]);
        int n = st.countTokens();
        long[] values = new long[n];
        for (int i = 0; i < n; i++) values[i] = Long.parseLong(st.nextToken());
        Arrays.sort(values);
        long[] distinct = new long[n];
        int[] counts = new int[n];
        int m = 0;
        int i = 0;
        while (i < n) {
            int j = i;
            while (j < n && values[j] == values[i]) j++;
            distinct[m] = values[i];
            counts[m] = j - i;
            m++;
            i = j;
        }
        Integer[] order = new Integer[m];
        for (int t = 0; t < m; t++) order[t] = t;
        final long[] dv = distinct;
        final int[] cv = counts;
        Arrays.sort(order, (a, b) -> cv[a] != cv[b] ? cv[b] - cv[a] : Long.compare(dv[a], dv[b]));
        StringBuilder sb = new StringBuilder();
        for (int t = 0; t < k; t++) {
            if (t > 0) sb.append(' ');
            sb.append(distinct[order[t]]);
        }
        System.out.println(sb);''',
        tree=False,
    ),
    cpp=_cpp(
        body="",
        main=r'''    std::vector<std::string> parts;
    {
        std::string current;
        for (char ch : line) {
            if (ch == '|') {
                parts.push_back(current);
                current.clear();
            } else {
                current += ch;
            }
        }
        parts.push_back(current);
    }
    int k = std::stoi(parts[0]);
    std::vector<long long> values;
    {
        std::istringstream in(parts[1]);
        long long v;
        while (in >> v) values.push_back(v);
    }
    std::sort(values.begin(), values.end());
    std::vector<std::pair<long long, int>> pairs;
    size_t i = 0;
    while (i < values.size()) {
        size_t j = i;
        while (j < values.size() && values[j] == values[i]) j++;
        pairs.push_back({values[i], (int)(j - i)});
        i = j;
    }
    std::sort(pairs.begin(), pairs.end(),
              [](const std::pair<long long, int>& a, const std::pair<long long, int>& b) {
                  if (a.second != b.second) return a.second > b.second;
                  return a.first < b.first;
              });
    for (int t = 0; t < k; t++) {
        if (t) std::cout << ' ';
        std::cout << pairs[(size_t)t].first;
    }
    std::cout << "\n";''',
        tree=False,
    ),
    c=_c(
        body=r'''
typedef struct {
    long long value;
    int count;
} Bucket;

static int compare_values(const void* a, const void* b) {
    long long x = *(const long long*)a;
    long long y = *(const long long*)b;
    return x < y ? -1 : (x > y ? 1 : 0);
}

static int compare_buckets(const void* a, const void* b) {
    const Bucket* x = (const Bucket*)a;
    const Bucket* y = (const Bucket*)b;
    if (x->count != y->count) return y->count - x->count;
    return x->value < y->value ? -1 : (x->value > y->value ? 1 : 0);
}
''',
        main=r'''    char* parts[4];
    split_sections(line, parts, 4);
    int k = atoi(parts[0]);
    int n = count_tokens(parts[1]);
    long long* values = (long long*)malloc(sizeof(long long) * (size_t)(n > 0 ? n : 1));
    int m = 0;
    char* save = NULL;
    for (char* tok = strtok_r(parts[1], " \t\r", &save); tok != NULL;
         tok = strtok_r(NULL, " \t\r", &save)) {
        values[m++] = atoll(tok);
    }
    qsort(values, (size_t)m, sizeof(long long), compare_values);
    Bucket* buckets = (Bucket*)malloc(sizeof(Bucket) * (size_t)(m > 0 ? m : 1));
    int bn = 0;
    int i = 0;
    while (i < m) {
        int j = i;
        while (j < m && values[j] == values[i]) j++;
        buckets[bn].value = values[i];
        buckets[bn].count = j - i;
        bn++;
        i = j;
    }
    qsort(buckets, (size_t)bn, sizeof(Bucket), compare_buckets);
    for (int t = 0; t < k && t < bn; t++) {
        if (t) putchar(' ');
        printf("%lld", buckets[t].value);
    }
    putchar('\n');''',
        tree=False,
    ),
)


# --------------------------------------------------------------------------- #
#  16 · find-median-from-data-stream                                          #
# --------------------------------------------------------------------------- #
# Two heaps: a max-heap of the lower half and a min-heap of the upper half,
# with the lower half allowed to hold one extra value.

_register(
    "find-median-from-data-stream",
    python=r'''
import heapq
import sys


def main():
    line = sys.stdin.readline().rstrip("\n")
    low = []
    high = []
    out = []
    for command in line.split(";")[1:]:
        command = command.strip()
        if not command:
            continue
        if command[0] == "a":
            value = int(command.split()[1])
            heapq.heappush(low, -value)
            heapq.heappush(high, -heapq.heappop(low))
            if len(high) > len(low):
                heapq.heappush(low, -heapq.heappop(high))
            continue
        if len(low) > len(high):
            out.append("%.1f" % float(-low[0]))
        else:
            out.append("%.1f" % ((-low[0] + high[0]) / 2.0))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


main()
''',
    javascript=r'''
const input = require("fs").readFileSync(0, "utf8");
const line = input.split("\n")[0] ?? "";

class Heap {
  constructor(sign) {
    this.sign = sign; // 1 = min-heap, -1 = max-heap
    this.data = [];
  }
  get size() {
    return this.data.length;
  }
  peek() {
    return this.data[0];
  }
  push(value) {
    const d = this.data;
    d.push(value);
    let i = d.length - 1;
    while (i > 0) {
      const parent = (i - 1) >> 1;
      if (this.sign * (d[parent] - d[i]) <= 0) break;
      const tmp = d[parent];
      d[parent] = d[i];
      d[i] = tmp;
      i = parent;
    }
  }
  pop() {
    const d = this.data;
    const top = d[0];
    const last = d.pop();
    if (d.length) {
      d[0] = last;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1;
        const r = l + 1;
        let best = i;
        if (l < d.length && this.sign * (d[l] - d[best]) < 0) best = l;
        if (r < d.length && this.sign * (d[r] - d[best]) < 0) best = r;
        if (best === i) break;
        const tmp = d[best];
        d[best] = d[i];
        d[i] = tmp;
        i = best;
      }
    }
    return top;
  }
}

const low = new Heap(-1);
const high = new Heap(1);
const out = [];
const parts = line.split(";");
for (let i = 1; i < parts.length; i++) {
  const command = parts[i].trim();
  if (!command) continue;
  if (command[0] === "a") {
    low.push(Number(command.slice(command.indexOf(" ") + 1)));
    high.push(low.pop());
    if (high.size > low.size) low.push(high.pop());
    continue;
  }
  const median = low.size > high.size ? low.peek() : (low.peek() + high.peek()) / 2;
  out.push(median.toFixed(1));
}
process.stdout.write(out.join("\n") + (out.length ? "\n" : ""));
''',
    java=_java(
        body="",
        main=r'''        String line = readLine();
        PriorityQueue<Long> low = new PriorityQueue<>(Comparator.reverseOrder());
        PriorityQueue<Long> high = new PriorityQueue<>();
        StringBuilder sb = new StringBuilder();
        String[] parts = line.split(";");
        for (int i = 1; i < parts.length; i++) {
            String command = parts[i].trim();
            if (command.isEmpty()) continue;
            if (command.charAt(0) == 'a') {
                long value = Long.parseLong(command.substring(command.indexOf(' ') + 1).trim());
                low.add(value);
                high.add(low.poll());
                if (high.size() > low.size()) low.add(high.poll());
                continue;
            }
            double median;
            if (low.size() > high.size()) median = low.peek();
            else median = (low.peek() + high.peek()) / 2.0;
            sb.append(String.format(java.util.Locale.ROOT, "%.1f", median)).append('\n');
        }
        System.out.print(sb);''',
        tree=False,
    ),
    cpp=_cpp(
        body="",
        main=r'''    std::priority_queue<long long> low;
    std::priority_queue<long long, std::vector<long long>, std::greater<long long>> high;
    std::string out;
    std::vector<std::string> parts;
    {
        std::string current;
        for (char ch : line) {
            if (ch == ';') {
                parts.push_back(current);
                current.clear();
            } else {
                current += ch;
            }
        }
        parts.push_back(current);
    }
    char buffer[64];
    for (size_t i = 1; i < parts.size(); i++) {
        std::string command = parts[i];
        size_t start = command.find_first_not_of(" \t\r");
        if (start == std::string::npos) continue;
        command = command.substr(start);
        if (command[0] == 'a') {
            long long value = std::stoll(command.substr(command.find(' ') + 1));
            low.push(value);
            high.push(low.top());
            low.pop();
            if (high.size() > low.size()) {
                low.push(high.top());
                high.pop();
            }
            continue;
        }
        double median;
        if (low.size() > high.size()) median = (double)low.top();
        else median = ((double)low.top() + (double)high.top()) / 2.0;
        snprintf(buffer, sizeof(buffer), "%.1f", median);
        out += buffer;
        out += '\n';
    }
    std::cout << out;''',
        tree=False,
    ),
    c=_c(
        body=r'''
/* Two array heaps. `sign` flips the comparison so one call site builds a
   max-heap of the lower half and the other a min-heap of the upper half. */
typedef struct {
    long long* data;
    int size;
    int sign;
} Heap;

static void heap_init(Heap* h, int cap, int sign) {
    h->data = (long long*)malloc(sizeof(long long) * (size_t)(cap > 1 ? cap : 1));
    h->size = 0;
    h->sign = sign;
}

static void heap_push(Heap* h, long long value) {
    int i = h->size++;
    h->data[i] = value;
    while (i > 0) {
        int parent = (i - 1) / 2;
        if ((long long)h->sign * (h->data[parent] - h->data[i]) <= 0) break;
        long long tmp = h->data[parent];
        h->data[parent] = h->data[i];
        h->data[i] = tmp;
        i = parent;
    }
}

static long long heap_pop(Heap* h) {
    long long top = h->data[0];
    h->data[0] = h->data[--h->size];
    int i = 0;
    for (;;) {
        int l = 2 * i + 1;
        int r = l + 1;
        int best = i;
        if (l < h->size && (long long)h->sign * (h->data[l] - h->data[best]) < 0) best = l;
        if (r < h->size && (long long)h->sign * (h->data[r] - h->data[best]) < 0) best = r;
        if (best == i) break;
        long long tmp = h->data[best];
        h->data[best] = h->data[i];
        h->data[i] = tmp;
        i = best;
    }
    return top;
}
''',
        main=r'''    int cap = (int)strlen(line) + 2;
    Heap low;
    Heap high;
    heap_init(&low, cap, -1);
    heap_init(&high, cap, 1);
    char* save = NULL;
    int seen = 0;
    for (char* raw = strtok_r(line, ";", &save); raw != NULL; raw = strtok_r(NULL, ";", &save)) {
        char* command = trim_spaces(raw);
        if (seen++ == 0 || *command == '\0') continue;
        if (command[0] == 'a') {
            char* space = strchr(command, ' ');
            long long value = atoll(space + 1);
            heap_push(&low, value);
            heap_push(&high, heap_pop(&low));
            if (high.size > low.size) heap_push(&low, heap_pop(&high));
            continue;
        }
        double median;
        if (low.size > high.size) median = (double)low.data[0];
        else median = ((double)low.data[0] + (double)high.data[0]) / 2.0;
        printf("%.1f\n", median);
    }''',
        tree=False,
    ),
)


# --------------------------------------------------------------------------- #
#  17 · combination-sum                                                       #
# --------------------------------------------------------------------------- #
# Candidates sorted ascending and each recursive call resuming at its own
# index: that yields non-decreasing combinations in lexicographic order, which
# is exactly the order the statement demands.

_register(
    "combination-sum",
    python=r'''
import sys


def main():
    head, candidates_part = sys.stdin.readline().rstrip("\n").split("|")
    target = int(head.strip())
    candidates = sorted(int(x) for x in candidates_part.split())
    out = []
    current = []

    def walk(start, remaining):
        if remaining == 0:
            out.append(" ".join(map(str, current)))
            return
        for index in range(start, len(candidates)):
            value = candidates[index]
            if value > remaining:
                break
            current.append(value)
            walk(index, remaining - value)
            current.pop()

    walk(0, target)
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


main()
''',
    javascript=r'''
const input = require("fs").readFileSync(0, "utf8");
const line = input.split("\n")[0] ?? "";
const parts = line.split("|");
const target = Number(parts[0].trim());
const candidates = parts[1].split(/\s+/).filter(Boolean).map(Number).sort((a, b) => a - b);
const out = [];
const current = [];

function walk(start, remaining) {
  if (remaining === 0) {
    out.push(current.join(" "));
    return;
  }
  for (let index = start; index < candidates.length; index++) {
    const value = candidates[index];
    if (value > remaining) break;
    current.push(value);
    walk(index, remaining - value);
    current.pop();
  }
}

walk(0, target);
process.stdout.write(out.join("\n") + (out.length ? "\n" : ""));
''',
    java=_java(
        body=r'''
    static int[] candidates;
    static int[] current = new int[64];
    static int depth = 0;
    static StringBuilder out = new StringBuilder();

    static void walk(int start, int remaining) {
        if (remaining == 0) {
            for (int i = 0; i < depth; i++) {
                if (i > 0) out.append(' ');
                out.append(current[i]);
            }
            out.append('\n');
            return;
        }
        for (int index = start; index < candidates.length; index++) {
            int value = candidates[index];
            if (value > remaining) break;
            current[depth++] = value;
            walk(index, remaining - value);
            depth--;
        }
    }
''',
        main=r'''        String[] parts = readLine().split("\\|");
        int target = Integer.parseInt(parts[0].trim());
        StringTokenizer st = new StringTokenizer(parts[1]);
        candidates = new int[st.countTokens()];
        for (int i = 0; i < candidates.length; i++) candidates[i] = Integer.parseInt(st.nextToken());
        Arrays.sort(candidates);
        walk(0, target);
        System.out.print(out);''',
        tree=False,
    ),
    cpp=_cpp(
        body=r'''
std::vector<int> candidates;
std::vector<int> current;
std::string out;

void walk(int start, int remaining) {
    if (remaining == 0) {
        for (size_t i = 0; i < current.size(); i++) {
            if (i) out += ' ';
            out += std::to_string(current[i]);
        }
        out += '\n';
        return;
    }
    for (size_t index = (size_t)start; index < candidates.size(); index++) {
        int value = candidates[index];
        if (value > remaining) break;
        current.push_back(value);
        walk((int)index, remaining - value);
        current.pop_back();
    }
}
''',
        main=r'''    std::vector<std::string> parts;
    {
        std::string cur;
        for (char ch : line) {
            if (ch == '|') {
                parts.push_back(cur);
                cur.clear();
            } else {
                cur += ch;
            }
        }
        parts.push_back(cur);
    }
    int target = std::stoi(parts[0]);
    {
        std::istringstream in(parts[1]);
        int v;
        while (in >> v) candidates.push_back(v);
    }
    std::sort(candidates.begin(), candidates.end());
    walk(0, target);
    std::cout << out;''',
        tree=False,
    ),
    c=_c(
        body=r'''
static int* candidates;
static int candidate_count;
static int current[64];
static int depth;

static int compare_ints(const void* a, const void* b) {
    return *(const int*)a - *(const int*)b;
}

static void walk(int start, int remaining) {
    if (remaining == 0) {
        for (int i = 0; i < depth; i++) {
            if (i) putchar(' ');
            printf("%d", current[i]);
        }
        putchar('\n');
        return;
    }
    for (int index = start; index < candidate_count; index++) {
        int value = candidates[index];
        if (value > remaining) break;
        current[depth++] = value;
        walk(index, remaining - value);
        depth--;
    }
}
''',
        main=r'''    char* parts[4];
    split_sections(line, parts, 4);
    int target = atoi(parts[0]);
    candidate_count = count_tokens(parts[1]);
    candidates = (int*)malloc(sizeof(int) * (size_t)(candidate_count > 0 ? candidate_count : 1));
    int m = 0;
    char* save = NULL;
    for (char* tok = strtok_r(parts[1], " \t\r", &save); tok != NULL;
         tok = strtok_r(NULL, " \t\r", &save)) {
        candidates[m++] = atoi(tok);
    }
    candidate_count = m;
    qsort(candidates, (size_t)m, sizeof(int), compare_ints);
    depth = 0;
    walk(0, target);''',
        tree=False,
    ),
)


# --------------------------------------------------------------------------- #
#  18 · word-search                                                           #
# --------------------------------------------------------------------------- #

_register(
    "word-search",
    python=r'''
import sys


def main():
    sys.setrecursionlimit(10000)
    head, grid_part, word_part = sys.stdin.readline().rstrip("\n").split("|")
    rows, cols = (int(x) for x in head.split())
    grid = grid_part.split()
    word = word_part.strip()
    used = [[False] * cols for _ in range(rows)]

    def walk(r, c, index):
        if grid[r][c] != word[index]:
            return False
        if index == len(word) - 1:
            return True
        used[r][c] = True
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not used[nr][nc]:
                if walk(nr, nc, index + 1):
                    used[r][c] = False
                    return True
        used[r][c] = False
        return False

    for r in range(rows):
        for c in range(cols):
            if walk(r, c, 0):
                print("true")
                return
    print("false")


main()
''',
    javascript=r'''
const input = require("fs").readFileSync(0, "utf8");
const line = input.split("\n")[0] ?? "";
const parts = line.split("|");
const [rows, cols] = parts[0].split(/\s+/).filter(Boolean).map(Number);
const grid = parts[1].split(/\s+/).filter(Boolean);
const word = parts[2].trim();
const used = [];
for (let r = 0; r < rows; r++) used.push(new Array(cols).fill(false));
const steps = [[1, 0], [-1, 0], [0, 1], [0, -1]];

function walk(r, c, index) {
  if (grid[r][c] !== word[index]) return false;
  if (index === word.length - 1) return true;
  used[r][c] = true;
  for (const [dr, dc] of steps) {
    const nr = r + dr;
    const nc = c + dc;
    if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !used[nr][nc]) {
      if (walk(nr, nc, index + 1)) {
        used[r][c] = false;
        return true;
      }
    }
  }
  used[r][c] = false;
  return false;
}

let found = false;
for (let r = 0; r < rows && !found; r++) {
  for (let c = 0; c < cols && !found; c++) {
    if (walk(r, c, 0)) found = true;
  }
}
console.log(found ? "true" : "false");
''',
    java=_java(
        body=r'''
    static int rows;
    static int cols;
    static String[] grid;
    static String word;
    static boolean[][] used;

    static boolean walk(int r, int c, int index) {
        if (grid[r].charAt(c) != word.charAt(index)) return false;
        if (index == word.length() - 1) return true;
        used[r][c] = true;
        int[][] steps = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
        for (int[] step : steps) {
            int nr = r + step[0];
            int nc = c + step[1];
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !used[nr][nc]) {
                if (walk(nr, nc, index + 1)) {
                    used[r][c] = false;
                    return true;
                }
            }
        }
        used[r][c] = false;
        return false;
    }
''',
        main=r'''        String[] parts = readLine().split("\\|");
        StringTokenizer head = new StringTokenizer(parts[0]);
        rows = Integer.parseInt(head.nextToken());
        cols = Integer.parseInt(head.nextToken());
        StringTokenizer gt = new StringTokenizer(parts[1]);
        grid = new String[rows];
        for (int i = 0; i < rows; i++) grid[i] = gt.nextToken();
        word = parts[2].trim();
        used = new boolean[rows][cols];
        boolean found = false;
        for (int r = 0; r < rows && !found; r++) {
            for (int c = 0; c < cols && !found; c++) {
                if (walk(r, c, 0)) found = true;
            }
        }
        System.out.println(found ? "true" : "false");''',
        tree=False,
    ),
    cpp=_cpp(
        body=r'''
int rowCount;
int colCount;
std::vector<std::string> gridRows;
std::string target;
std::vector<char> usedCell;

bool walk(int r, int c, int index) {
    if (gridRows[r][c] != target[index]) return false;
    if (index == (int)target.size() - 1) return true;
    usedCell[r * colCount + c] = 1;
    int steps[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
    for (int i = 0; i < 4; i++) {
        int nr = r + steps[i][0];
        int nc = c + steps[i][1];
        if (nr >= 0 && nr < rowCount && nc >= 0 && nc < colCount && !usedCell[nr * colCount + nc]) {
            if (walk(nr, nc, index + 1)) {
                usedCell[r * colCount + c] = 0;
                return true;
            }
        }
    }
    usedCell[r * colCount + c] = 0;
    return false;
}
''',
        main=r'''    std::vector<std::string> parts;
    {
        std::string cur;
        for (char ch : line) {
            if (ch == '|') {
                parts.push_back(cur);
                cur.clear();
            } else {
                cur += ch;
            }
        }
        parts.push_back(cur);
    }
    {
        std::istringstream in(parts[0]);
        in >> rowCount >> colCount;
    }
    {
        std::istringstream in(parts[1]);
        std::string row;
        while (in >> row) gridRows.push_back(row);
        std::istringstream in2(parts[2]);
        in2 >> target;
    }
    usedCell.assign((size_t)rowCount * colCount, 0);
    bool found = false;
    for (int r = 0; r < rowCount && !found; r++) {
        for (int c = 0; c < colCount && !found; c++) {
            if (walk(r, c, 0)) found = true;
        }
    }
    std::cout << (found ? "true" : "false") << "\n";''',
        tree=False,
    ),
    c=_c(
        body=r'''
static int rows;
static int cols;
static char** grid;
static char* word;
static int word_len;
static char* used;

static int walk(int r, int c, int index) {
    if (grid[r][c] != word[index]) return 0;
    if (index == word_len - 1) return 1;
    used[r * cols + c] = 1;
    static const int dr[4] = {1, -1, 0, 0};
    static const int dc[4] = {0, 0, 1, -1};
    for (int i = 0; i < 4; i++) {
        int nr = r + dr[i];
        int nc = c + dc[i];
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !used[nr * cols + nc]) {
            if (walk(nr, nc, index + 1)) {
                used[r * cols + c] = 0;
                return 1;
            }
        }
    }
    used[r * cols + c] = 0;
    return 0;
}
''',
        main=r'''    char* parts[4];
    split_sections(line, parts, 4);
    sscanf(parts[0], "%d %d", &rows, &cols);
    grid = (char**)malloc(sizeof(char*) * (size_t)(rows > 0 ? rows : 1));
    int gn = 0;
    char* save = NULL;
    for (char* tok = strtok_r(parts[1], " \t\r", &save); tok != NULL && gn < rows;
         tok = strtok_r(NULL, " \t\r", &save)) {
        grid[gn++] = tok;
    }
    char* save2 = NULL;
    word = strtok_r(parts[2], " \t\r", &save2);
    word_len = (int)strlen(word);
    used = (char*)calloc((size_t)(rows * cols), 1);
    int found = 0;
    for (int r = 0; r < rows && !found; r++) {
        for (int c = 0; c < cols && !found; c++) {
            if (walk(r, c, 0)) found = 1;
        }
    }
    printf("%s\n", found ? "true" : "false");''',
        tree=False,
    ),
)


# --------------------------------------------------------------------------- #
#  19 · subsets                                                               #
# --------------------------------------------------------------------------- #
# Emitting the current subset on entry and then extending it with each later
# value produces the lexicographic order the statement fixes, with the empty
# subset first.

_register(
    "subsets",
    python=r'''
import sys


def main():
    head, values_part = sys.stdin.readline().rstrip("\n").split("|")
    values = sorted(int(x) for x in values_part.split())
    out = []
    current = []

    def walk(start):
        if current:
            out.append(str(len(current)) + " " + " ".join(map(str, current)))
        else:
            out.append("0")
        for index in range(start, len(values)):
            current.append(values[index])
            walk(index + 1)
            current.pop()

    walk(0)
    sys.stdout.write("\n".join(out) + "\n")


main()
''',
    javascript=r'''
const input = require("fs").readFileSync(0, "utf8");
const line = input.split("\n")[0] ?? "";
const parts = line.split("|");
const values = parts[1].split(/\s+/).filter(Boolean).map(Number).sort((a, b) => a - b);
const out = [];
const current = [];

function walk(start) {
  out.push(current.length ? current.length + " " + current.join(" ") : "0");
  for (let index = start; index < values.length; index++) {
    current.push(values[index]);
    walk(index + 1);
    current.pop();
  }
}

walk(0);
process.stdout.write(out.join("\n") + "\n");
''',
    java=_java(
        body=r'''
    static long[] values;
    static long[] current = new long[32];
    static int depth = 0;
    static StringBuilder out = new StringBuilder();

    static void walk(int start) {
        out.append(depth);
        for (int i = 0; i < depth; i++) out.append(' ').append(current[i]);
        out.append('\n');
        for (int index = start; index < values.length; index++) {
            current[depth++] = values[index];
            walk(index + 1);
            depth--;
        }
    }
''',
        main=r'''        String[] parts = readLine().split("\\|");
        StringTokenizer st = new StringTokenizer(parts[1]);
        values = new long[st.countTokens()];
        for (int i = 0; i < values.length; i++) values[i] = Long.parseLong(st.nextToken());
        Arrays.sort(values);
        walk(0);
        System.out.print(out);''',
        tree=False,
    ),
    cpp=_cpp(
        body=r'''
std::vector<long long> values;
std::vector<long long> current;
std::string out;

void walk(int start) {
    out += std::to_string(current.size());
    for (long long value : current) {
        out += ' ';
        out += std::to_string(value);
    }
    out += '\n';
    for (size_t index = (size_t)start; index < values.size(); index++) {
        current.push_back(values[index]);
        walk((int)index + 1);
        current.pop_back();
    }
}
''',
        main=r'''    std::vector<std::string> parts;
    {
        std::string cur;
        for (char ch : line) {
            if (ch == '|') {
                parts.push_back(cur);
                cur.clear();
            } else {
                cur += ch;
            }
        }
        parts.push_back(cur);
    }
    {
        std::istringstream in(parts[1]);
        long long v;
        while (in >> v) values.push_back(v);
    }
    std::sort(values.begin(), values.end());
    walk(0);
    std::cout << out;''',
        tree=False,
    ),
    c=_c(
        body=r'''
static long long* values;
static int value_count;
static long long current[32];
static int depth;

static int compare_longs(const void* a, const void* b) {
    long long x = *(const long long*)a;
    long long y = *(const long long*)b;
    return x < y ? -1 : (x > y ? 1 : 0);
}

static void walk(int start) {
    printf("%d", depth);
    for (int i = 0; i < depth; i++) printf(" %lld", current[i]);
    putchar('\n');
    for (int index = start; index < value_count; index++) {
        current[depth++] = values[index];
        walk(index + 1);
        depth--;
    }
}
''',
        main=r'''    char* parts[4];
    split_sections(line, parts, 4);
    value_count = count_tokens(parts[1]);
    values = (long long*)malloc(sizeof(long long) * (size_t)(value_count > 0 ? value_count : 1));
    int m = 0;
    char* save = NULL;
    for (char* tok = strtok_r(parts[1], " \t\r", &save); tok != NULL;
         tok = strtok_r(NULL, " \t\r", &save)) {
        values[m++] = atoll(tok);
    }
    value_count = m;
    qsort(values, (size_t)m, sizeof(long long), compare_longs);
    depth = 0;
    walk(0);''',
        tree=False,
    ),
)
