"""Known-correct solutions for Blind 75 batch 2, used only for verification.

Same role as ``scripts/language_solutions.py``, kept separate so the batches do
not collide: ``scripts/verify_blind75_2.py`` runs each of these through the real
judge against the full generated case bank and every case must pass. Nothing
here is imported by the app.

Java sources are assembled from a shared byte-level reader (``_java``) because
``Scanner`` cannot read 200000 tokens inside the time limit.
"""

from __future__ import annotations

SOLUTIONS: dict[str, dict[str, str]] = {}

_JAVA_READER = """
    private static final class FastReader {
        private final java.io.InputStream in;
        private final byte[] buf = new byte[1 << 16];
        private int len = 0;
        private int ptr = 0;

        FastReader(java.io.InputStream in) { this.in = in; }

        private int read() throws IOException {
            if (ptr == len) {
                len = in.read(buf, 0, buf.length);
                ptr = 0;
                if (len <= 0) return -1;
            }
            return buf[ptr++];
        }

        long nextLong() throws IOException {
            int c = read();
            while (c == ' ' || c == '\\n' || c == '\\r' || c == '\\t') c = read();
            boolean negative = c == '-';
            if (negative) c = read();
            long value = 0;
            while (c >= '0' && c <= '9') { value = value * 10 + (c - '0'); c = read(); }
            return negative ? -value : value;
        }
    }
"""


def _java(body: str) -> str:
    """Wrap a class body in the imports, class shell and FastReader."""
    return (
        "import java.io.IOException;\n"
        "import java.util.*;\n"
        "\n"
        "public class Main {\n"
        f"{body.rstrip()}\n"
        f"{_JAVA_READER.rstrip()}\n"
        "}\n"
    )


def _register(slug: str, python: str, javascript: str, cpp: str, java_body: str, c: str) -> None:
    SOLUTIONS[slug] = {
        "python": python.lstrip(),
        "javascript": javascript.lstrip(),
        "cpp": cpp.lstrip(),
        "java": _java(java_body),
        "c": c.lstrip(),
    }


# --------------------------------------------------------------------------- #
#  reverse-linked-list                                                        #
# --------------------------------------------------------------------------- #

_register(
    "reverse-linked-list",
    python='''
import sys


class Node:
    __slots__ = ("value", "next")

    def __init__(self, value):
        self.value = value
        self.next = None


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    head = None
    tail = None
    for token in data[1:1 + n]:
        node = Node(int(token))
        if head is None:
            head = tail = node
        else:
            tail.next = node
            tail = node
    prev = None
    node = head
    while node is not None:
        nxt = node.next
        node.next = prev
        prev = node
        node = nxt
    out = []
    node = prev
    while node is not None:
        out.append(node.value)
        node = node.next
    sys.stdout.write(str(len(out)) + "\\n" + " ".join(map(str, out)) + "\\n")


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean);
const n = Number(data[0]);
let head = null;
let tail = null;
for (let i = 0; i < n; i++) {
  const node = { value: data[1 + i], next: null };
  if (head === null) { head = node; tail = node; } else { tail.next = node; tail = node; }
}
let prev = null;
let node = head;
while (node !== null) {
  const nxt = node.next;
  node.next = prev;
  prev = node;
  node = nxt;
}
const out = [];
for (node = prev; node !== null; node = node.next) out.push(node.value);
process.stdout.write(out.length + "\\n" + out.join(" ") + "\\n");
''',
    cpp='''
#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

struct Node {
    long long value;
    Node* next;
};

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    Node* head = nullptr;
    Node* tail = nullptr;
    for (int i = 0; i < n; i++) {
        long long v;
        std::cin >> v;
        Node* node = new Node{v, nullptr};
        if (!head) { head = tail = node; } else { tail->next = node; tail = node; }
    }
    Node* prev = nullptr;
    Node* node = head;
    while (node) {
        Node* nxt = node->next;
        node->next = prev;
        prev = node;
        node = nxt;
    }
    std::string out;
    int count = 0;
    for (node = prev; node; node = node->next) {
        if (count) out.push_back(' ');
        out += std::to_string(node->value);
        count++;
    }
    std::cout << count << "\\n" << out << "\\n";
    return 0;
}
''',
    java_body='''
    static final class Node {
        long value;
        Node next;
        Node(long value) { this.value = value; }
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        Node head = null, tail = null;
        for (int i = 0; i < n; i++) {
            Node node = new Node(in.nextLong());
            if (head == null) { head = node; tail = node; } else { tail.next = node; tail = node; }
        }
        Node prev = null, node = head;
        while (node != null) {
            Node nxt = node.next;
            node.next = prev;
            prev = node;
            node = nxt;
        }
        StringBuilder sb = new StringBuilder();
        int count = 0;
        for (node = prev; node != null; node = node.next) {
            if (count > 0) sb.append(' ');
            sb.append(node.value);
            count++;
        }
        System.out.println(count);
        System.out.println(sb);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

struct Node {
    long long value;
    struct Node* next;
};

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    struct Node* head = NULL;
    struct Node* tail = NULL;
    for (int i = 0; i < n; i++) {
        long long v = 0;
        if (scanf("%lld", &v) != 1) break;
        struct Node* node = (struct Node*)malloc(sizeof(struct Node));
        node->value = v;
        node->next = NULL;
        if (!head) { head = tail = node; } else { tail->next = node; tail = node; }
    }
    struct Node* prev = NULL;
    struct Node* node = head;
    while (node) {
        struct Node* nxt = node->next;
        node->next = prev;
        prev = node;
        node = nxt;
    }
    int count = 0;
    for (node = prev; node; node = node->next) count++;
    printf("%d\\n", count);
    for (node = prev; node; node = node->next) {
        printf("%lld%s", node->value, node->next ? " " : "");
    }
    printf("\\n");
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  linked-list-cycle-entry                                                    #
# --------------------------------------------------------------------------- #

_register(
    "linked-list-cycle-entry",
    python='''
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    nxt = [int(x) for x in data[1:1 + n]]
    slow = 0
    fast = 0
    while True:
        if nxt[fast] == -1:
            print(-1)
            return
        fast = nxt[fast]
        if nxt[fast] == -1:
            print(-1)
            return
        fast = nxt[fast]
        slow = nxt[slow]
        if slow == fast:
            break
    slow = 0
    while slow != fast:
        slow = nxt[slow]
        fast = nxt[fast]
    print(slow)


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
const n = data[0];
const nxt = data.slice(1, 1 + n);
let slow = 0;
let fast = 0;
let answer = null;
for (;;) {
  if (nxt[fast] === -1) { answer = -1; break; }
  fast = nxt[fast];
  if (nxt[fast] === -1) { answer = -1; break; }
  fast = nxt[fast];
  slow = nxt[slow];
  if (slow === fast) break;
}
if (answer === null) {
  slow = 0;
  while (slow !== fast) { slow = nxt[slow]; fast = nxt[fast]; }
  answer = slow;
}
console.log(answer);
''',
    cpp='''
#include <iostream>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<int> nxt(n);
    for (int i = 0; i < n; i++) std::cin >> nxt[i];
    int slow = 0, fast = 0;
    bool cycle = true;
    while (true) {
        if (nxt[fast] == -1) { cycle = false; break; }
        fast = nxt[fast];
        if (nxt[fast] == -1) { cycle = false; break; }
        fast = nxt[fast];
        slow = nxt[slow];
        if (slow == fast) break;
    }
    if (!cycle) { std::cout << -1 << "\\n"; return 0; }
    slow = 0;
    while (slow != fast) { slow = nxt[slow]; fast = nxt[fast]; }
    std::cout << slow << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        int[] nxt = new int[n];
        for (int i = 0; i < n; i++) nxt[i] = (int) in.nextLong();
        int slow = 0, fast = 0;
        boolean cycle = true;
        while (true) {
            if (nxt[fast] == -1) { cycle = false; break; }
            fast = nxt[fast];
            if (nxt[fast] == -1) { cycle = false; break; }
            fast = nxt[fast];
            slow = nxt[slow];
            if (slow == fast) break;
        }
        if (!cycle) { System.out.println(-1); return; }
        slow = 0;
        while (slow != fast) { slow = nxt[slow]; fast = nxt[fast]; }
        System.out.println(slow);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    int* nxt = (int*)malloc((size_t)(n > 0 ? n : 1) * sizeof(int));
    for (int i = 0; i < n; i++) {
        if (scanf("%d", &nxt[i]) != 1) break;
    }
    int slow = 0, fast = 0, cycle = 1;
    while (1) {
        if (nxt[fast] == -1) { cycle = 0; break; }
        fast = nxt[fast];
        if (nxt[fast] == -1) { cycle = 0; break; }
        fast = nxt[fast];
        slow = nxt[slow];
        if (slow == fast) break;
    }
    if (!cycle) {
        printf("-1\\n");
        free(nxt);
        return 0;
    }
    slow = 0;
    while (slow != fast) { slow = nxt[slow]; fast = nxt[fast]; }
    printf("%d\\n", slow);
    free(nxt);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  merge-two-sorted-lists                                                     #
# --------------------------------------------------------------------------- #

_register(
    "merge-two-sorted-lists",
    python='''
import sys


class Node:
    __slots__ = ("value", "next")

    def __init__(self, value):
        self.value = value
        self.next = None


def build(tokens):
    head = None
    tail = None
    for token in tokens:
        node = Node(int(token))
        if head is None:
            head = tail = node
        else:
            tail.next = node
            tail = node
    return head


def main():
    data = sys.stdin.buffer.read().split()
    pos = 0
    n = int(data[pos]); pos += 1
    first = build(data[pos:pos + n]); pos += n
    m = int(data[pos]); pos += 1
    second = build(data[pos:pos + m]); pos += m
    dummy = Node(0)
    tail = dummy
    a, b = first, second
    while a is not None and b is not None:
        if a.value <= b.value:
            tail.next = a
            a = a.next
        else:
            tail.next = b
            b = b.next
        tail = tail.next
    tail.next = a if a is not None else b
    out = []
    node = dummy.next
    while node is not None:
        out.append(node.value)
        node = node.next
    sys.stdout.write(str(len(out)) + "\\n" + " ".join(map(str, out)) + "\\n")


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean);
let pos = 0;
function build(count) {
  let head = null, tail = null;
  for (let i = 0; i < count; i++) {
    const node = { value: data[pos + i], next: null };
    if (head === null) { head = node; tail = node; } else { tail.next = node; tail = node; }
  }
  pos += count;
  return head;
}
const n = Number(data[pos++]);
const first = build(n);
const m = Number(data[pos++]);
const second = build(m);
const dummy = { value: 0, next: null };
let tail = dummy;
let a = first, b = second;
while (a !== null && b !== null) {
  if (Number(a.value) <= Number(b.value)) { tail.next = a; a = a.next; } else { tail.next = b; b = b.next; }
  tail = tail.next;
}
tail.next = a !== null ? a : b;
const out = [];
for (let node = dummy.next; node !== null; node = node.next) out.push(node.value);
process.stdout.write(out.length + "\\n" + out.join(" ") + "\\n");
''',
    cpp='''
#include <iostream>
#include <string>
#include <vector>

struct Node {
    long long value;
    Node* next;
};

static Node* build(int count) {
    Node* head = nullptr;
    Node* tail = nullptr;
    for (int i = 0; i < count; i++) {
        long long v;
        std::cin >> v;
        Node* node = new Node{v, nullptr};
        if (!head) { head = tail = node; } else { tail->next = node; tail = node; }
    }
    return head;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    Node* a = build(n);
    int m;
    std::cin >> m;
    Node* b = build(m);
    Node dummy{0, nullptr};
    Node* tail = &dummy;
    while (a && b) {
        if (a->value <= b->value) { tail->next = a; a = a->next; } else { tail->next = b; b = b->next; }
        tail = tail->next;
    }
    tail->next = a ? a : b;
    std::string out;
    int count = 0;
    for (Node* node = dummy.next; node; node = node->next) {
        if (count) out.push_back(' ');
        out += std::to_string(node->value);
        count++;
    }
    std::cout << count << "\\n" << out << "\\n";
    return 0;
}
''',
    java_body='''
    static final class Node {
        long value;
        Node next;
        Node(long value) { this.value = value; }
    }

    static Node build(FastReader in, int count) throws IOException {
        Node head = null, tail = null;
        for (int i = 0; i < count; i++) {
            Node node = new Node(in.nextLong());
            if (head == null) { head = node; tail = node; } else { tail.next = node; tail = node; }
        }
        return head;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        Node a = build(in, n);
        int m = (int) in.nextLong();
        Node b = build(in, m);
        Node dummy = new Node(0);
        Node tail = dummy;
        while (a != null && b != null) {
            if (a.value <= b.value) { tail.next = a; a = a.next; } else { tail.next = b; b = b.next; }
            tail = tail.next;
        }
        tail.next = a != null ? a : b;
        StringBuilder sb = new StringBuilder();
        int count = 0;
        for (Node node = dummy.next; node != null; node = node.next) {
            if (count > 0) sb.append(' ');
            sb.append(node.value);
            count++;
        }
        System.out.println(count);
        System.out.println(sb);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

struct Node {
    long long value;
    struct Node* next;
};

static struct Node* build(int count) {
    struct Node* head = NULL;
    struct Node* tail = NULL;
    for (int i = 0; i < count; i++) {
        long long v = 0;
        if (scanf("%lld", &v) != 1) break;
        struct Node* node = (struct Node*)malloc(sizeof(struct Node));
        node->value = v;
        node->next = NULL;
        if (!head) { head = tail = node; } else { tail->next = node; tail = node; }
    }
    return head;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    struct Node* a = build(n);
    int m = 0;
    if (scanf("%d", &m) != 1) m = 0;
    struct Node* b = build(m);
    struct Node dummy;
    dummy.next = NULL;
    struct Node* tail = &dummy;
    while (a && b) {
        if (a->value <= b->value) { tail->next = a; a = a->next; } else { tail->next = b; b = b->next; }
        tail = tail->next;
    }
    tail->next = a ? a : b;
    int count = 0;
    for (struct Node* node = dummy.next; node; node = node->next) count++;
    printf("%d\\n", count);
    for (struct Node* node = dummy.next; node; node = node->next) {
        printf("%lld%s", node->value, node->next ? " " : "");
    }
    printf("\\n");
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  merge-k-sorted-lists                                                       #
# --------------------------------------------------------------------------- #

_register(
    "merge-k-sorted-lists",
    python='''
import sys
import heapq


def main():
    data = sys.stdin.buffer.read().split()
    k = int(data[0])
    m = int(data[1])
    stream = [int(x) for x in data[2:2 + m]]
    heap = []
    lists = []
    pos = 0
    for index in range(k):
        size = stream[pos]; pos += 1
        values = stream[pos:pos + size]; pos += size
        lists.append(values)
        if values:
            heapq.heappush(heap, (values[0], index, 0))
    out = []
    while heap:
        value, index, offset = heapq.heappop(heap)
        out.append(value)
        offset += 1
        if offset < len(lists[index]):
            heapq.heappush(heap, (lists[index][offset], index, offset))
    sys.stdout.write(str(len(out)) + "\\n" + " ".join(map(str, out)) + "\\n")


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
const k = data[0];
const m = data[1];
let pos = 2;
let lists = [];
for (let i = 0; i < k; i++) {
  const size = data[pos++];
  lists.push(data.slice(pos, pos + size));
  pos += size;
}
// Pairwise merge in rounds: O(total log k) without a heap implementation.
function merge(a, b) {
  const out = new Array(a.length + b.length);
  let i = 0, j = 0, t = 0;
  while (i < a.length && j < b.length) out[t++] = a[i] <= b[j] ? a[i++] : b[j++];
  while (i < a.length) out[t++] = a[i++];
  while (j < b.length) out[t++] = b[j++];
  return out;
}
while (lists.length > 1) {
  const next = [];
  for (let i = 0; i < lists.length; i += 2) {
    next.push(i + 1 < lists.length ? merge(lists[i], lists[i + 1]) : lists[i]);
  }
  lists = next;
}
const out = lists.length ? lists[0] : [];
process.stdout.write(out.length + "\\n" + out.join(" ") + "\\n");
''',
    cpp='''
#include <iostream>
#include <queue>
#include <string>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int k;
    long long m;
    if (!(std::cin >> k >> m)) return 0;
    std::vector<std::vector<long long>> lists(k);
    for (int i = 0; i < k; i++) {
        long long size;
        std::cin >> size;
        lists[i].resize((size_t)size);
        for (long long j = 0; j < size; j++) std::cin >> lists[i][(size_t)j];
    }
    using Item = std::pair<long long, std::pair<int, size_t>>;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> heap;
    for (int i = 0; i < k; i++) {
        if (!lists[i].empty()) heap.push({lists[i][0], {i, 0}});
    }
    std::string out;
    long long count = 0;
    while (!heap.empty()) {
        Item top = heap.top();
        heap.pop();
        if (count) out.push_back(' ');
        out += std::to_string(top.first);
        count++;
        size_t offset = top.second.second + 1;
        int index = top.second.first;
        if (offset < lists[index].size()) heap.push({lists[index][offset], {index, offset}});
    }
    std::cout << count << "\\n" << out << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int k = (int) in.nextLong();
        long m = in.nextLong();
        long[][] lists = new long[k][];
        for (int i = 0; i < k; i++) {
            int size = (int) in.nextLong();
            lists[i] = new long[size];
            for (int j = 0; j < size; j++) lists[i][j] = in.nextLong();
        }
        PriorityQueue<long[]> heap = new PriorityQueue<>((x, y) -> Long.compare(x[0], y[0]));
        for (int i = 0; i < k; i++) {
            if (lists[i].length > 0) heap.add(new long[] {lists[i][0], i, 0});
        }
        StringBuilder sb = new StringBuilder();
        long count = 0;
        while (!heap.isEmpty()) {
            long[] top = heap.poll();
            if (count > 0) sb.append(' ');
            sb.append(top[0]);
            count++;
            int index = (int) top[1];
            int offset = (int) top[2] + 1;
            if (offset < lists[index].length) heap.add(new long[] {lists[index][offset], index, offset});
        }
        System.out.println(count);
        System.out.println(sb);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

/* Binary heap over (value, list index, offset). */
typedef struct { long long value; int index; int offset; } Item;

static Item heap_data[1024];
static int heap_size = 0;

static void heap_push(Item item) {
    int i = heap_size++;
    heap_data[i] = item;
    while (i > 0) {
        int parent = (i - 1) / 2;
        if (heap_data[parent].value <= heap_data[i].value) break;
        Item tmp = heap_data[parent];
        heap_data[parent] = heap_data[i];
        heap_data[i] = tmp;
        i = parent;
    }
}

static Item heap_pop(void) {
    Item top = heap_data[0];
    heap_data[0] = heap_data[--heap_size];
    int i = 0;
    while (1) {
        int left = 2 * i + 1, right = left + 1, best = i;
        if (left < heap_size && heap_data[left].value < heap_data[best].value) best = left;
        if (right < heap_size && heap_data[right].value < heap_data[best].value) best = right;
        if (best == i) break;
        Item tmp = heap_data[best];
        heap_data[best] = heap_data[i];
        heap_data[i] = tmp;
        i = best;
    }
    return top;
}

int main(void) {
    int k = 0;
    long long m = 0;
    if (scanf("%d %lld", &k, &m) != 2) return 0;
    long long** lists = (long long**)malloc((size_t)(k > 0 ? k : 1) * sizeof(long long*));
    int* sizes = (int*)malloc((size_t)(k > 0 ? k : 1) * sizeof(int));
    for (int i = 0; i < k; i++) {
        int size = 0;
        if (scanf("%d", &size) != 1) size = 0;
        sizes[i] = size;
        lists[i] = (long long*)malloc((size_t)(size > 0 ? size : 1) * sizeof(long long));
        for (int j = 0; j < size; j++) {
            if (scanf("%lld", &lists[i][j]) != 1) break;
        }
    }
    for (int i = 0; i < k; i++) {
        if (sizes[i] > 0) {
            Item item;
            item.value = lists[i][0];
            item.index = i;
            item.offset = 0;
            heap_push(item);
        }
    }
    long long total = 0;
    for (int i = 0; i < k; i++) total += sizes[i];
    long long* out = (long long*)malloc((size_t)(total > 0 ? total : 1) * sizeof(long long));
    long long count = 0;
    while (heap_size > 0) {
        Item top = heap_pop();
        out[count++] = top.value;
        int offset = top.offset + 1;
        if (offset < sizes[top.index]) {
            Item item;
            item.value = lists[top.index][offset];
            item.index = top.index;
            item.offset = offset;
            heap_push(item);
        }
    }
    printf("%lld\\n", count);
    for (long long i = 0; i < count; i++) {
        printf("%lld%s", out[i], i + 1 < count ? " " : "");
    }
    printf("\\n");
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  remove-nth-from-end                                                        #
# --------------------------------------------------------------------------- #

_register(
    "remove-nth-from-end",
    python='''
import sys


class Node:
    __slots__ = ("value", "next")

    def __init__(self, value):
        self.value = value
        self.next = None


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    k = int(data[1 + n])
    head = None
    tail = None
    for token in data[1:1 + n]:
        node = Node(int(token))
        if head is None:
            head = tail = node
        else:
            tail.next = node
            tail = node
    dummy = Node(0)
    dummy.next = head
    lead = dummy
    for _ in range(k):
        lead = lead.next
    trail = dummy
    while lead.next is not None:
        lead = lead.next
        trail = trail.next
    trail.next = trail.next.next
    out = []
    node = dummy.next
    while node is not None:
        out.append(node.value)
        node = node.next
    sys.stdout.write(str(len(out)) + "\\n" + " ".join(map(str, out)) + "\\n")


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean);
const n = Number(data[0]);
const k = Number(data[1 + n]);
let head = null, tail = null;
for (let i = 0; i < n; i++) {
  const node = { value: data[1 + i], next: null };
  if (head === null) { head = node; tail = node; } else { tail.next = node; tail = node; }
}
const dummy = { value: 0, next: head };
let lead = dummy;
for (let i = 0; i < k; i++) lead = lead.next;
let trail = dummy;
while (lead.next !== null) { lead = lead.next; trail = trail.next; }
trail.next = trail.next.next;
const out = [];
for (let node = dummy.next; node !== null; node = node.next) out.push(node.value);
process.stdout.write(out.length + "\\n" + out.join(" ") + "\\n");
''',
    cpp='''
#include <iostream>
#include <string>
#include <vector>

struct Node {
    long long value;
    Node* next;
};

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<long long> values(n);
    for (int i = 0; i < n; i++) std::cin >> values[i];
    int k;
    std::cin >> k;
    Node* head = nullptr;
    Node* tail = nullptr;
    for (int i = 0; i < n; i++) {
        Node* node = new Node{values[i], nullptr};
        if (!head) { head = tail = node; } else { tail->next = node; tail = node; }
    }
    Node dummy{0, head};
    Node* lead = &dummy;
    for (int i = 0; i < k; i++) lead = lead->next;
    Node* trail = &dummy;
    while (lead->next) { lead = lead->next; trail = trail->next; }
    trail->next = trail->next->next;
    std::string out;
    int count = 0;
    for (Node* node = dummy.next; node; node = node->next) {
        if (count) out.push_back(' ');
        out += std::to_string(node->value);
        count++;
    }
    std::cout << count << "\\n" << out << "\\n";
    return 0;
}
''',
    java_body='''
    static final class Node {
        long value;
        Node next;
        Node(long value) { this.value = value; }
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] values = new long[n];
        for (int i = 0; i < n; i++) values[i] = in.nextLong();
        int k = (int) in.nextLong();
        Node head = null, tail = null;
        for (int i = 0; i < n; i++) {
            Node node = new Node(values[i]);
            if (head == null) { head = node; tail = node; } else { tail.next = node; tail = node; }
        }
        Node dummy = new Node(0);
        dummy.next = head;
        Node lead = dummy;
        for (int i = 0; i < k; i++) lead = lead.next;
        Node trail = dummy;
        while (lead.next != null) { lead = lead.next; trail = trail.next; }
        trail.next = trail.next.next;
        StringBuilder sb = new StringBuilder();
        int count = 0;
        for (Node node = dummy.next; node != null; node = node.next) {
            if (count > 0) sb.append(' ');
            sb.append(node.value);
            count++;
        }
        System.out.println(count);
        System.out.println(sb);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

struct Node {
    long long value;
    struct Node* next;
};

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long long* values = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &values[i]) != 1) break;
    }
    int k = 0;
    if (scanf("%d", &k) != 1) return 0;
    struct Node* head = NULL;
    struct Node* tail = NULL;
    for (int i = 0; i < n; i++) {
        struct Node* node = (struct Node*)malloc(sizeof(struct Node));
        node->value = values[i];
        node->next = NULL;
        if (!head) { head = tail = node; } else { tail->next = node; tail = node; }
    }
    struct Node dummy;
    dummy.value = 0;
    dummy.next = head;
    struct Node* lead = &dummy;
    for (int i = 0; i < k; i++) lead = lead->next;
    struct Node* trail = &dummy;
    while (lead->next) { lead = lead->next; trail = trail->next; }
    trail->next = trail->next->next;
    int count = 0;
    for (struct Node* node = dummy.next; node; node = node->next) count++;
    printf("%d\\n", count);
    for (struct Node* node = dummy.next; node; node = node->next) {
        printf("%lld%s", node->value, node->next ? " " : "");
    }
    printf("\\n");
    free(values);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  reorder-linked-list                                                        #
# --------------------------------------------------------------------------- #

_register(
    "reorder-linked-list",
    python='''
import sys


class Node:
    __slots__ = ("value", "next")

    def __init__(self, value):
        self.value = value
        self.next = None


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    head = None
    tail = None
    for token in data[1:1 + n]:
        node = Node(int(token))
        if head is None:
            head = tail = node
        else:
            tail.next = node
            tail = node
    if n <= 2:
        out = []
        node = head
        while node is not None:
            out.append(node.value)
            node = node.next
        sys.stdout.write(str(len(out)) + "\\n" + " ".join(map(str, out)) + "\\n")
        return
    slow = head
    fast = head
    while fast.next is not None and fast.next.next is not None:
        slow = slow.next
        fast = fast.next.next
    second = slow.next
    slow.next = None
    prev = None
    while second is not None:
        nxt = second.next
        second.next = prev
        prev = second
        second = nxt
    first = head
    second = prev
    out = []
    while first is not None or second is not None:
        if first is not None:
            out.append(first.value)
            first = first.next
        if second is not None:
            out.append(second.value)
            second = second.next
    sys.stdout.write(str(len(out)) + "\\n" + " ".join(map(str, out)) + "\\n")


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean);
const n = Number(data[0]);
let head = null, tail = null;
for (let i = 0; i < n; i++) {
  const node = { value: data[1 + i], next: null };
  if (head === null) { head = node; tail = node; } else { tail.next = node; tail = node; }
}
const out = [];
if (n <= 2) {
  for (let node = head; node !== null; node = node.next) out.push(node.value);
} else {
  let slow = head, fast = head;
  while (fast.next !== null && fast.next.next !== null) { slow = slow.next; fast = fast.next.next; }
  let second = slow.next;
  slow.next = null;
  let prev = null;
  while (second !== null) { const nxt = second.next; second.next = prev; prev = second; second = nxt; }
  let first = head;
  second = prev;
  while (first !== null || second !== null) {
    if (first !== null) { out.push(first.value); first = first.next; }
    if (second !== null) { out.push(second.value); second = second.next; }
  }
}
process.stdout.write(out.length + "\\n" + out.join(" ") + "\\n");
''',
    cpp='''
#include <iostream>
#include <string>
#include <vector>

struct Node {
    long long value;
    Node* next;
};

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    Node* head = nullptr;
    Node* tail = nullptr;
    for (int i = 0; i < n; i++) {
        long long v;
        std::cin >> v;
        Node* node = new Node{v, nullptr};
        if (!head) { head = tail = node; } else { tail->next = node; tail = node; }
    }
    std::string out;
    int count = 0;
    auto emit = [&](long long value) {
        if (count) out.push_back(' ');
        out += std::to_string(value);
        count++;
    };
    if (n <= 2) {
        for (Node* node = head; node; node = node->next) emit(node->value);
    } else {
        Node* slow = head;
        Node* fast = head;
        while (fast->next && fast->next->next) { slow = slow->next; fast = fast->next->next; }
        Node* second = slow->next;
        slow->next = nullptr;
        Node* prev = nullptr;
        while (second) {
            Node* nxt = second->next;
            second->next = prev;
            prev = second;
            second = nxt;
        }
        Node* first = head;
        second = prev;
        while (first || second) {
            if (first) { emit(first->value); first = first->next; }
            if (second) { emit(second->value); second = second->next; }
        }
    }
    std::cout << count << "\\n" << out << "\\n";
    return 0;
}
''',
    java_body='''
    static final class Node {
        long value;
        Node next;
        Node(long value) { this.value = value; }
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        Node head = null, tail = null;
        for (int i = 0; i < n; i++) {
            Node node = new Node(in.nextLong());
            if (head == null) { head = node; tail = node; } else { tail.next = node; tail = node; }
        }
        StringBuilder sb = new StringBuilder();
        int count = 0;
        if (n <= 2) {
            for (Node node = head; node != null; node = node.next) {
                if (count > 0) sb.append(' ');
                sb.append(node.value);
                count++;
            }
        } else {
            Node slow = head, fast = head;
            while (fast.next != null && fast.next.next != null) { slow = slow.next; fast = fast.next.next; }
            Node second = slow.next;
            slow.next = null;
            Node prev = null;
            while (second != null) {
                Node nxt = second.next;
                second.next = prev;
                prev = second;
                second = nxt;
            }
            Node first = head;
            second = prev;
            while (first != null || second != null) {
                if (first != null) {
                    if (count > 0) sb.append(' ');
                    sb.append(first.value);
                    count++;
                    first = first.next;
                }
                if (second != null) {
                    if (count > 0) sb.append(' ');
                    sb.append(second.value);
                    count++;
                    second = second.next;
                }
            }
        }
        System.out.println(count);
        System.out.println(sb);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

struct Node {
    long long value;
    struct Node* next;
};

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    struct Node* head = NULL;
    struct Node* tail = NULL;
    for (int i = 0; i < n; i++) {
        long long v = 0;
        if (scanf("%lld", &v) != 1) break;
        struct Node* node = (struct Node*)malloc(sizeof(struct Node));
        node->value = v;
        node->next = NULL;
        if (!head) { head = tail = node; } else { tail->next = node; tail = node; }
    }
    long long* out = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    int count = 0;
    if (n <= 2) {
        for (struct Node* node = head; node; node = node->next) out[count++] = node->value;
    } else {
        struct Node* slow = head;
        struct Node* fast = head;
        while (fast->next && fast->next->next) { slow = slow->next; fast = fast->next->next; }
        struct Node* second = slow->next;
        slow->next = NULL;
        struct Node* prev = NULL;
        while (second) {
            struct Node* nxt = second->next;
            second->next = prev;
            prev = second;
            second = nxt;
        }
        struct Node* first = head;
        second = prev;
        while (first || second) {
            if (first) { out[count++] = first->value; first = first->next; }
            if (second) { out[count++] = second->value; second = second->next; }
        }
    }
    printf("%d\\n", count);
    for (int i = 0; i < count; i++) {
        printf("%lld%s", out[i], i + 1 < count ? " " : "");
    }
    printf("\\n");
    free(out);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  insert-interval                                                            #
# --------------------------------------------------------------------------- #

_register(
    "insert-interval",
    python='''
import sys


def main():
    data = sys.stdin.buffer.read().split()
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
    lines.extend(f"{a} {b}" for a, b in out)
    sys.stdout.write("\\n".join(lines) + "\\n")


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos++];
const starts = data.slice(pos, pos + n); pos += n;
const ends = data.slice(pos, pos + n); pos += n;
let s = data[pos++];
let e = data[pos++];
const out = [];
let i = 0;
while (i < n && ends[i] < s) { out.push([starts[i], ends[i]]); i++; }
while (i < n && starts[i] <= e) { s = Math.min(s, starts[i]); e = Math.max(e, ends[i]); i++; }
out.push([s, e]);
while (i < n) { out.push([starts[i], ends[i]]); i++; }
const lines = [String(out.length)];
for (const [a, b] of out) lines.push(a + " " + b);
process.stdout.write(lines.join("\\n") + "\\n");
''',
    cpp='''
#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<long long> starts(n), ends(n);
    for (int i = 0; i < n; i++) std::cin >> starts[i];
    for (int i = 0; i < n; i++) std::cin >> ends[i];
    long long s, e;
    std::cin >> s >> e;
    std::vector<std::pair<long long, long long>> out;
    int i = 0;
    while (i < n && ends[i] < s) { out.push_back({starts[i], ends[i]}); i++; }
    while (i < n && starts[i] <= e) {
        s = std::min(s, starts[i]);
        e = std::max(e, ends[i]);
        i++;
    }
    out.push_back({s, e});
    while (i < n) { out.push_back({starts[i], ends[i]}); i++; }
    std::string buffer = std::to_string(out.size());
    for (const auto& pair : out) {
        buffer += "\\n";
        buffer += std::to_string(pair.first);
        buffer += " ";
        buffer += std::to_string(pair.second);
    }
    std::cout << buffer << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] starts = new long[n];
        for (int i = 0; i < n; i++) starts[i] = in.nextLong();
        long[] ends = new long[n];
        for (int i = 0; i < n; i++) ends[i] = in.nextLong();
        long s = in.nextLong();
        long e = in.nextLong();
        ArrayList<long[]> out = new ArrayList<>();
        int i = 0;
        while (i < n && ends[i] < s) { out.add(new long[] {starts[i], ends[i]}); i++; }
        while (i < n && starts[i] <= e) {
            s = Math.min(s, starts[i]);
            e = Math.max(e, ends[i]);
            i++;
        }
        out.add(new long[] {s, e});
        while (i < n) { out.add(new long[] {starts[i], ends[i]}); i++; }
        StringBuilder sb = new StringBuilder();
        sb.append(out.size());
        for (long[] pair : out) sb.append('\\n').append(pair[0]).append(' ').append(pair[1]);
        System.out.println(sb);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long long* starts = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    long long* ends = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &starts[i]) != 1) break;
    }
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &ends[i]) != 1) break;
    }
    long long s = 0, e = 0;
    if (scanf("%lld %lld", &s, &e) != 2) return 0;
    long long* outStart = (long long*)malloc((size_t)(n + 1) * sizeof(long long));
    long long* outEnd = (long long*)malloc((size_t)(n + 1) * sizeof(long long));
    int count = 0;
    int i = 0;
    while (i < n && ends[i] < s) { outStart[count] = starts[i]; outEnd[count] = ends[i]; count++; i++; }
    while (i < n && starts[i] <= e) {
        if (starts[i] < s) s = starts[i];
        if (ends[i] > e) e = ends[i];
        i++;
    }
    outStart[count] = s;
    outEnd[count] = e;
    count++;
    while (i < n) { outStart[count] = starts[i]; outEnd[count] = ends[i]; count++; i++; }
    printf("%d\\n", count);
    for (int j = 0; j < count; j++) printf("%lld %lld\\n", outStart[j], outEnd[j]);
    free(starts);
    free(ends);
    free(outStart);
    free(outEnd);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  merge-intervals                                                            #
# --------------------------------------------------------------------------- #

_register(
    "merge-intervals",
    python='''
import sys


def main():
    data = sys.stdin.buffer.read().split()
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
    lines.extend(f"{a} {b}" for a, b in out)
    sys.stdout.write("\\n".join(lines) + "\\n")


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos++];
const starts = data.slice(pos, pos + n); pos += n;
const ends = data.slice(pos, pos + n); pos += n;
const pairs = [];
for (let i = 0; i < n; i++) pairs.push([starts[i], ends[i]]);
pairs.sort((x, y) => (x[0] - y[0]) || (x[1] - y[1]));
const out = [];
for (const [start, end] of pairs) {
  if (out.length && start <= out[out.length - 1][1]) {
    if (end > out[out.length - 1][1]) out[out.length - 1][1] = end;
  } else {
    out.push([start, end]);
  }
}
const lines = [String(out.length)];
for (const [a, b] of out) lines.push(a + " " + b);
process.stdout.write(lines.join("\\n") + "\\n");
''',
    cpp='''
#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<long long> starts(n), ends(n);
    for (int i = 0; i < n; i++) std::cin >> starts[i];
    for (int i = 0; i < n; i++) std::cin >> ends[i];
    std::vector<std::pair<long long, long long>> pairs(n);
    for (int i = 0; i < n; i++) pairs[i] = {starts[i], ends[i]};
    std::sort(pairs.begin(), pairs.end());
    std::vector<std::pair<long long, long long>> out;
    for (const auto& pair : pairs) {
        if (!out.empty() && pair.first <= out.back().second) {
            if (pair.second > out.back().second) out.back().second = pair.second;
        } else {
            out.push_back(pair);
        }
    }
    std::string buffer = std::to_string(out.size());
    for (const auto& pair : out) {
        buffer += "\\n";
        buffer += std::to_string(pair.first);
        buffer += " ";
        buffer += std::to_string(pair.second);
    }
    std::cout << buffer << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] starts = new long[n];
        for (int i = 0; i < n; i++) starts[i] = in.nextLong();
        long[] ends = new long[n];
        for (int i = 0; i < n; i++) ends[i] = in.nextLong();
        long[][] pairs = new long[n][2];
        for (int i = 0; i < n; i++) { pairs[i][0] = starts[i]; pairs[i][1] = ends[i]; }
        Arrays.sort(pairs, (x, y) -> x[0] != y[0] ? Long.compare(x[0], y[0]) : Long.compare(x[1], y[1]));
        ArrayList<long[]> out = new ArrayList<>();
        for (long[] pair : pairs) {
            if (!out.isEmpty() && pair[0] <= out.get(out.size() - 1)[1]) {
                if (pair[1] > out.get(out.size() - 1)[1]) out.get(out.size() - 1)[1] = pair[1];
            } else {
                out.add(new long[] {pair[0], pair[1]});
            }
        }
        StringBuilder sb = new StringBuilder();
        sb.append(out.size());
        for (long[] pair : out) sb.append('\\n').append(pair[0]).append(' ').append(pair[1]);
        System.out.println(sb);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

typedef struct { long long start; long long end; } Interval;

static int cmp_interval(const void* a, const void* b) {
    const Interval* x = (const Interval*)a;
    const Interval* y = (const Interval*)b;
    if (x->start != y->start) return (x->start > y->start) - (x->start < y->start);
    return (x->end > y->end) - (x->end < y->end);
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    Interval* items = (Interval*)malloc((size_t)(n > 0 ? n : 1) * sizeof(Interval));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &items[i].start) != 1) break;
    }
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &items[i].end) != 1) break;
    }
    qsort(items, (size_t)n, sizeof(Interval), cmp_interval);
    Interval* out = (Interval*)malloc((size_t)(n > 0 ? n : 1) * sizeof(Interval));
    int count = 0;
    for (int i = 0; i < n; i++) {
        if (count > 0 && items[i].start <= out[count - 1].end) {
            if (items[i].end > out[count - 1].end) out[count - 1].end = items[i].end;
        } else {
            out[count++] = items[i];
        }
    }
    printf("%d\\n", count);
    for (int i = 0; i < count; i++) printf("%lld %lld\\n", out[i].start, out[i].end);
    free(items);
    free(out);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  min-intervals-to-remove                                                    #
# --------------------------------------------------------------------------- #

_register(
    "min-intervals-to-remove",
    python='''
import sys


def main():
    data = sys.stdin.buffer.read().split()
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
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos++];
const starts = data.slice(pos, pos + n); pos += n;
const ends = data.slice(pos, pos + n); pos += n;
const pairs = [];
for (let i = 0; i < n; i++) pairs.push([ends[i], starts[i]]);
pairs.sort((x, y) => (x[0] - y[0]) || (x[1] - y[1]));
let kept = 0;
let lastEnd = null;
for (const [end, start] of pairs) {
  if (lastEnd === null || start >= lastEnd) { kept++; lastEnd = end; }
}
console.log(n - kept);
''',
    cpp='''
#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<long long> starts(n), ends(n);
    for (int i = 0; i < n; i++) std::cin >> starts[i];
    for (int i = 0; i < n; i++) std::cin >> ends[i];
    std::vector<std::pair<long long, long long>> pairs(n);
    for (int i = 0; i < n; i++) pairs[i] = {ends[i], starts[i]};
    std::sort(pairs.begin(), pairs.end());
    int kept = 0;
    bool first = true;
    long long lastEnd = 0;
    for (const auto& pair : pairs) {
        if (first || pair.second >= lastEnd) {
            kept++;
            lastEnd = pair.first;
            first = false;
        }
    }
    std::cout << (n - kept) << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] starts = new long[n];
        for (int i = 0; i < n; i++) starts[i] = in.nextLong();
        long[] ends = new long[n];
        for (int i = 0; i < n; i++) ends[i] = in.nextLong();
        long[][] pairs = new long[n][2];
        for (int i = 0; i < n; i++) { pairs[i][0] = ends[i]; pairs[i][1] = starts[i]; }
        Arrays.sort(pairs, (x, y) -> x[0] != y[0] ? Long.compare(x[0], y[0]) : Long.compare(x[1], y[1]));
        int kept = 0;
        boolean first = true;
        long lastEnd = 0;
        for (long[] pair : pairs) {
            if (first || pair[1] >= lastEnd) {
                kept++;
                lastEnd = pair[0];
                first = false;
            }
        }
        System.out.println(n - kept);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

typedef struct { long long end; long long start; } Interval;

static int cmp_interval(const void* a, const void* b) {
    const Interval* x = (const Interval*)a;
    const Interval* y = (const Interval*)b;
    if (x->end != y->end) return (x->end > y->end) - (x->end < y->end);
    return (x->start > y->start) - (x->start < y->start);
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    Interval* items = (Interval*)malloc((size_t)(n > 0 ? n : 1) * sizeof(Interval));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &items[i].start) != 1) break;
    }
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &items[i].end) != 1) break;
    }
    qsort(items, (size_t)n, sizeof(Interval), cmp_interval);
    int kept = 0;
    int first = 1;
    long long lastEnd = 0;
    for (int i = 0; i < n; i++) {
        if (first || items[i].start >= lastEnd) {
            kept++;
            lastEnd = items[i].end;
            first = 0;
        }
    }
    printf("%d\\n", n - kept);
    free(items);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  can-attend-all-meetings                                                    #
# --------------------------------------------------------------------------- #

_register(
    "can-attend-all-meetings",
    python='''
import sys


def main():
    data = sys.stdin.buffer.read().split()
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
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos++];
const starts = data.slice(pos, pos + n); pos += n;
const ends = data.slice(pos, pos + n); pos += n;
const pairs = [];
for (let i = 0; i < n; i++) pairs.push([starts[i], ends[i]]);
pairs.sort((x, y) => (x[0] - y[0]) || (x[1] - y[1]));
let ok = 1;
for (let i = 1; i < n; i++) {
  if (pairs[i][0] < pairs[i - 1][1]) { ok = 0; break; }
}
console.log(ok);
''',
    cpp='''
#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<long long> starts(n), ends(n);
    for (int i = 0; i < n; i++) std::cin >> starts[i];
    for (int i = 0; i < n; i++) std::cin >> ends[i];
    std::vector<std::pair<long long, long long>> pairs(n);
    for (int i = 0; i < n; i++) pairs[i] = {starts[i], ends[i]};
    std::sort(pairs.begin(), pairs.end());
    int ok = 1;
    for (int i = 1; i < n; i++) {
        if (pairs[i].first < pairs[i - 1].second) { ok = 0; break; }
    }
    std::cout << ok << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] starts = new long[n];
        for (int i = 0; i < n; i++) starts[i] = in.nextLong();
        long[] ends = new long[n];
        for (int i = 0; i < n; i++) ends[i] = in.nextLong();
        long[][] pairs = new long[n][2];
        for (int i = 0; i < n; i++) { pairs[i][0] = starts[i]; pairs[i][1] = ends[i]; }
        Arrays.sort(pairs, (x, y) -> x[0] != y[0] ? Long.compare(x[0], y[0]) : Long.compare(x[1], y[1]));
        int ok = 1;
        for (int i = 1; i < n; i++) {
            if (pairs[i][0] < pairs[i - 1][1]) { ok = 0; break; }
        }
        System.out.println(ok);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

typedef struct { long long start; long long end; } Interval;

static int cmp_interval(const void* a, const void* b) {
    const Interval* x = (const Interval*)a;
    const Interval* y = (const Interval*)b;
    if (x->start != y->start) return (x->start > y->start) - (x->start < y->start);
    return (x->end > y->end) - (x->end < y->end);
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    Interval* items = (Interval*)malloc((size_t)(n > 0 ? n : 1) * sizeof(Interval));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &items[i].start) != 1) break;
    }
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &items[i].end) != 1) break;
    }
    qsort(items, (size_t)n, sizeof(Interval), cmp_interval);
    int ok = 1;
    for (int i = 1; i < n; i++) {
        if (items[i].start < items[i - 1].end) { ok = 0; break; }
    }
    printf("%d\\n", ok);
    free(items);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  min-meeting-rooms                                                          #
# --------------------------------------------------------------------------- #

_register(
    "min-meeting-rooms",
    python='''
import sys


def main():
    data = sys.stdin.buffer.read().split()
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
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos++];
const starts = data.slice(pos, pos + n).sort((a, b) => a - b); pos += n;
const ends = data.slice(pos, pos + n).sort((a, b) => a - b); pos += n;
let i = 0, j = 0, cur = 0, best = 0;
while (i < n && j < n) {
  if (starts[i] < ends[j]) {
    cur++;
    if (cur > best) best = cur;
    i++;
  } else {
    cur--;
    j++;
  }
}
console.log(best);
''',
    cpp='''
#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<long long> starts(n), ends(n);
    for (int i = 0; i < n; i++) std::cin >> starts[i];
    for (int i = 0; i < n; i++) std::cin >> ends[i];
    std::sort(starts.begin(), starts.end());
    std::sort(ends.begin(), ends.end());
    int i = 0, j = 0, cur = 0, best = 0;
    while (i < n && j < n) {
        if (starts[i] < ends[j]) {
            cur++;
            if (cur > best) best = cur;
            i++;
        } else {
            cur--;
            j++;
        }
    }
    std::cout << best << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] starts = new long[n];
        for (int i = 0; i < n; i++) starts[i] = in.nextLong();
        long[] ends = new long[n];
        for (int i = 0; i < n; i++) ends[i] = in.nextLong();
        Arrays.sort(starts);
        Arrays.sort(ends);
        int i = 0, j = 0, cur = 0, best = 0;
        while (i < n && j < n) {
            if (starts[i] < ends[j]) {
                cur++;
                if (cur > best) best = cur;
                i++;
            } else {
                cur--;
                j++;
            }
        }
        System.out.println(best);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

static int cmp_ll(const void* a, const void* b) {
    long long x = *(const long long*)a;
    long long y = *(const long long*)b;
    return (x > y) - (x < y);
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long long* starts = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    long long* ends = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &starts[i]) != 1) break;
    }
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &ends[i]) != 1) break;
    }
    qsort(starts, (size_t)n, sizeof(long long), cmp_ll);
    qsort(ends, (size_t)n, sizeof(long long), cmp_ll);
    int i = 0, j = 0, cur = 0, best = 0;
    while (i < n && j < n) {
        if (starts[i] < ends[j]) {
            cur++;
            if (cur > best) best = cur;
            i++;
        } else {
            cur--;
            j++;
        }
    }
    printf("%d\\n", best);
    free(starts);
    free(ends);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  koko-eating-bananas                                                        #
# --------------------------------------------------------------------------- #

_register(
    "koko-eating-bananas",
    python='''
import sys


def main():
    data = sys.stdin.buffer.read().split()
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
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
const n = data[0];
const h = data[1];
const piles = data.slice(2, 2 + n);
let lo = 1;
let hi = 0;
for (const p of piles) if (p > hi) hi = p;
while (lo < hi) {
  const mid = Math.floor((lo + hi) / 2);
  let hours = 0;
  for (const p of piles) {
    hours += Math.ceil(p / mid);
    if (hours > h) break;
  }
  if (hours <= h) hi = mid; else lo = mid + 1;
}
console.log(lo);
''',
    cpp='''
#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    long long h;
    if (!(std::cin >> n >> h)) return 0;
    std::vector<long long> piles(n);
    for (int i = 0; i < n; i++) std::cin >> piles[i];
    long long lo = 1;
    long long hi = *std::max_element(piles.begin(), piles.end());
    while (lo < hi) {
        long long mid = lo + (hi - lo) / 2;
        long long hours = 0;
        for (long long p : piles) {
            hours += (p + mid - 1) / mid;
            if (hours > h) break;
        }
        if (hours <= h) hi = mid; else lo = mid + 1;
    }
    std::cout << lo << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long h = in.nextLong();
        long[] piles = new long[n];
        for (int i = 0; i < n; i++) piles[i] = in.nextLong();
        long lo = 1;
        long hi = 1;
        for (long p : piles) hi = Math.max(hi, p);
        while (lo < hi) {
            long mid = lo + (hi - lo) / 2;
            long hours = 0;
            for (long p : piles) {
                hours += (p + mid - 1) / mid;
                if (hours > h) break;
            }
            if (hours <= h) hi = mid; else lo = mid + 1;
        }
        System.out.println(lo);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n = 0;
    long long h = 0;
    if (scanf("%d %lld", &n, &h) != 2) return 0;
    long long* piles = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    long long hi = 1;
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &piles[i]) != 1) break;
        if (piles[i] > hi) hi = piles[i];
    }
    long long lo = 1;
    while (lo < hi) {
        long long mid = lo + (hi - lo) / 2;
        long long hours = 0;
        for (int i = 0; i < n; i++) {
            hours += (piles[i] + mid - 1) / mid;
            if (hours > h) break;
        }
        if (hours <= h) hi = mid; else lo = mid + 1;
    }
    printf("%lld\\n", lo);
    free(piles);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  first-last-position                                                        #
# --------------------------------------------------------------------------- #

_register(
    "first-last-position",
    python='''
import sys


def lower_bound(arr, target):
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_bound(arr, target):
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] <= target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    target = int(data[1])
    arr = [int(x) for x in data[2:2 + n]]
    first = lower_bound(arr, target)
    if first == n or arr[first] != target:
        print(-1, -1)
        return
    print(first, upper_bound(arr, target) - 1)


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
const n = data[0];
const target = data[1];
const arr = data.slice(2, 2 + n);
function lowerBound(t) {
  let lo = 0, hi = n;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] < t) lo = mid + 1; else hi = mid;
  }
  return lo;
}
function upperBound(t) {
  let lo = 0, hi = n;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] <= t) lo = mid + 1; else hi = mid;
  }
  return lo;
}
const first = lowerBound(target);
if (first === n || arr[first] !== target) {
  console.log("-1 -1");
} else {
  console.log(first + " " + (upperBound(target) - 1));
}
''',
    cpp='''
#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    long long target;
    if (!(std::cin >> n >> target)) return 0;
    std::vector<long long> arr(n);
    for (int i = 0; i < n; i++) std::cin >> arr[i];
    auto lower = std::lower_bound(arr.begin(), arr.end(), target);
    if (lower == arr.end() || *lower != target) {
        std::cout << "-1 -1\\n";
        return 0;
    }
    auto upper = std::upper_bound(arr.begin(), arr.end(), target);
    std::cout << (lower - arr.begin()) << " " << (upper - arr.begin() - 1) << "\\n";
    return 0;
}
''',
    java_body='''
    static int lowerBound(long[] arr, long target) {
        int lo = 0, hi = arr.length;
        while (lo < hi) {
            int mid = (lo + hi) >>> 1;
            if (arr[mid] < target) lo = mid + 1; else hi = mid;
        }
        return lo;
    }

    static int upperBound(long[] arr, long target) {
        int lo = 0, hi = arr.length;
        while (lo < hi) {
            int mid = (lo + hi) >>> 1;
            if (arr[mid] <= target) lo = mid + 1; else hi = mid;
        }
        return lo;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long target = in.nextLong();
        long[] arr = new long[n];
        for (int i = 0; i < n; i++) arr[i] = in.nextLong();
        int first = lowerBound(arr, target);
        if (first == n || arr[first] != target) {
            System.out.println("-1 -1");
            return;
        }
        System.out.println(first + " " + (upperBound(arr, target) - 1));
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n = 0;
    long long target = 0;
    if (scanf("%d %lld", &n, &target) != 2) return 0;
    long long* arr = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &arr[i]) != 1) break;
    }
    int lo = 0, hi = n;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] < target) lo = mid + 1; else hi = mid;
    }
    int first = lo;
    if (first == n || arr[first] != target) {
        printf("-1 -1\\n");
        free(arr);
        return 0;
    }
    lo = 0;
    hi = n;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] <= target) lo = mid + 1; else hi = mid;
    }
    printf("%d %d\\n", first, lo - 1);
    free(arr);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  add-without-plus                                                           #
# --------------------------------------------------------------------------- #
# The masking is the whole point: Python needs an explicit 32-bit mask and a
# sign correction, while C, C++, Java and JavaScript get the wrap for free
# (unsigned intermediates in C/C++, and 32-bit bitwise operators in JS).

_register(
    "add-without-plus",
    python='''
import sys

MASK = 0xFFFFFFFF
SIGN = 0x80000000


def main():
    data = sys.stdin.buffer.read().split()
    a = int(data[0]) & MASK
    b = int(data[1]) & MASK
    while b:
        carry = (a & b) << 1
        a = (a ^ b) & MASK
        b = carry & MASK
    print(a if a < SIGN else a - 0x100000000)


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let a = data[0] | 0;
let b = data[1] | 0;
while (b !== 0) {
  const carry = (a & b) << 1;
  a = (a ^ b) | 0;
  b = carry | 0;
}
console.log(a);
''',
    cpp='''
#include <cstdint>
#include <iostream>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int a, b;
    if (!(std::cin >> a >> b)) return 0;
    uint32_t x = static_cast<uint32_t>(a);
    uint32_t y = static_cast<uint32_t>(b);
    while (y != 0) {
        uint32_t carry = (x & y) << 1;
        x = x ^ y;
        y = carry;
    }
    std::cout << static_cast<int32_t>(x) << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int a = (int) in.nextLong();
        int b = (int) in.nextLong();
        while (b != 0) {
            int carry = (a & b) << 1;
            a = a ^ b;
            b = carry;
        }
        System.out.println(a);
    }
''',
    c='''
#include <stdio.h>
#include <stdint.h>

int main(void) {
    int a = 0, b = 0;
    if (scanf("%d %d", &a, &b) != 2) return 0;
    uint32_t x = (uint32_t)a;
    uint32_t y = (uint32_t)b;
    while (y != 0) {
        uint32_t carry = (x & y) << 1;
        x = x ^ y;
        y = carry;
    }
    printf("%d\\n", (int32_t)x);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  count-set-bits-32                                                          #
# --------------------------------------------------------------------------- #

_register(
    "count-set-bits-32",
    python='''
import sys


def main():
    x = int(sys.stdin.buffer.read().split()[0]) & 0xFFFFFFFF
    count = 0
    while x:
        x &= x - 1
        count += 1
    print(count)


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean);
let x = Number(data[0]) >>> 0;
let count = 0;
while (x !== 0) {
  x = (x & (x - 1)) >>> 0;
  count++;
}
console.log(count);
''',
    cpp='''
#include <cstdint>
#include <iostream>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    long long input;
    if (!(std::cin >> input)) return 0;
    uint32_t x = static_cast<uint32_t>(input & 0xFFFFFFFFLL);
    int count = 0;
    while (x != 0) {
        x &= x - 1;
        count++;
    }
    std::cout << count << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        long input = in.nextLong();
        int x = (int) (input & 0xFFFFFFFFL);
        int count = 0;
        for (int i = 0; i < 32; i++) {
            count += (x >>> i) & 1;
        }
        System.out.println(count);
    }
''',
    c='''
#include <stdio.h>
#include <stdint.h>

int main(void) {
    long long input = 0;
    if (scanf("%lld", &input) != 1) return 0;
    uint32_t x = (uint32_t)(input & 0xFFFFFFFFLL);
    int count = 0;
    while (x != 0) {
        x &= x - 1;
        count++;
    }
    printf("%d\\n", count);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  counting-bits                                                              #
# --------------------------------------------------------------------------- #

_register(
    "counting-bits",
    python='''
import sys


def main():
    n = int(sys.stdin.buffer.read().split()[0])
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        dp[i] = dp[i >> 1] + (i & 1)
    sys.stdout.write(" ".join(map(str, dp)) + "\\n")


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
const n = data[0];
const dp = new Int32Array(n + 1);
for (let i = 1; i <= n; i++) dp[i] = dp[i >> 1] + (i & 1);
process.stdout.write(dp.join(" ") + "\\n");
''',
    cpp='''
#include <iostream>
#include <string>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<int> dp(n + 1, 0);
    for (int i = 1; i <= n; i++) dp[i] = dp[i >> 1] + (i & 1);
    std::string out;
    for (int i = 0; i <= n; i++) {
        if (i) out.push_back(' ');
        out += std::to_string(dp[i]);
    }
    std::cout << out << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        int[] dp = new int[n + 1];
        StringBuilder sb = new StringBuilder();
        sb.append(dp[0]);
        for (int i = 1; i <= n; i++) {
            dp[i] = dp[i >> 1] + (i & 1);
            sb.append(' ').append(dp[i]);
        }
        System.out.println(sb);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    int* dp = (int*)malloc((size_t)(n + 1) * sizeof(int));
    dp[0] = 0;
    for (int i = 1; i <= n; i++) dp[i] = dp[i >> 1] + (i & 1);
    for (int i = 0; i <= n; i++) {
        printf("%d%s", dp[i], i < n ? " " : "");
    }
    printf("\\n");
    free(dp);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  missing-number                                                             #
# --------------------------------------------------------------------------- #

_register(
    "missing-number",
    python='''
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    total = n * (n + 1) // 2
    for token in data[1:1 + n]:
        total -= int(token)
    print(total)


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
const n = data[0];
// n(n+1)/2 reaches 2e10, beyond a 32-bit int but well inside a double.
let total = (n * (n + 1)) / 2;
for (let i = 0; i < n; i++) total -= data[1 + i];
console.log(total);
''',
    cpp='''
#include <iostream>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    long long total = static_cast<long long>(n) * (n + 1) / 2;
    for (int i = 0; i < n; i++) {
        long long v;
        std::cin >> v;
        total -= v;
    }
    std::cout << total << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long total = (long) n * (n + 1) / 2;
        for (int i = 0; i < n; i++) total -= in.nextLong();
        System.out.println(total);
    }
''',
    c='''
#include <stdio.h>

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long long total = (long long)n * (n + 1) / 2;
    for (int i = 0; i < n; i++) {
        long long v = 0;
        if (scanf("%lld", &v) != 1) break;
        total -= v;
    }
    printf("%lld\\n", total);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  reverse-bits-32                                                            #
# --------------------------------------------------------------------------- #

_register(
    "reverse-bits-32",
    python='''
import sys


def main():
    x = int(sys.stdin.buffer.read().split()[0]) & 0xFFFFFFFF
    result = 0
    for _ in range(32):
        result = (result << 1) | (x & 1)
        x >>= 1
    print(result)


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean);
let x = Number(data[0]) >>> 0;
let result = 0;
for (let i = 0; i < 32; i++) {
  // Multiply rather than shift: the result must stay unsigned.
  result = result * 2 + (x & 1);
  x = x >>> 1;
}
console.log(result);
''',
    cpp='''
#include <cstdint>
#include <iostream>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    long long input;
    if (!(std::cin >> input)) return 0;
    uint32_t x = static_cast<uint32_t>(input & 0xFFFFFFFFLL);
    uint32_t result = 0;
    for (int i = 0; i < 32; i++) {
        result = (result << 1) | (x & 1u);
        x >>= 1;
    }
    std::cout << static_cast<long long>(result) << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        long input = in.nextLong();
        long x = input & 0xFFFFFFFFL;
        long result = 0;
        for (int i = 0; i < 32; i++) {
            result = (result << 1) | (x & 1L);
            x >>= 1;
        }
        System.out.println(result);
    }
''',
    c='''
#include <stdio.h>
#include <stdint.h>

int main(void) {
    long long input = 0;
    if (scanf("%lld", &input) != 1) return 0;
    uint32_t x = (uint32_t)(input & 0xFFFFFFFFLL);
    uint32_t result = 0;
    for (int i = 0; i < 32; i++) {
        result = (result << 1) | (x & 1u);
        x >>= 1;
    }
    printf("%llu\\n", (unsigned long long)result);
    return 0;
}
''',
)
