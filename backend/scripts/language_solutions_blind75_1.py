"""Known-correct solutions for Blind 75 batch 1, one per (problem, language).

Used only by ``scripts/verify_blind75_1.py``; never imported by the app, so
there is no path by which these could be served to a client.

Rather than pasting five near-identical files per problem, each solution is
the *generated* starter with its TODO stub replaced by a real body (and, where
a language needs one, a small prelude inserted just above the function). That
keeps the generated I/O plumbing itself under test: if the starter generator
ever emits input handling that cannot read the scale cases, these solutions
fail with it.
"""

from __future__ import annotations

import re
from typing import Any

from app.data.curriculum_blind75_1 import PROBLEMS
from app.data.curriculum_starters import build_starters

_PROBLEM_BY_SLUG: dict[str, dict[str, Any]] = {p["slug"]: p for p in PROBLEMS}

_STUB = {
    "python": re.compile(r"[ \t]*# TODO:[^\n]*\n[ \t]*return 0\n"),
    "javascript": re.compile(r"[ \t]*// TODO:[^\n]*\n[ \t]*return 0;\n"),
    "cpp": re.compile(r"[ \t]*// TODO:[^\n]*\n[ \t]*return 0;\n"),
    "java": re.compile(r"[ \t]*// TODO:[^\n]*\n[ \t]*return 0;\n"),
    "c": re.compile(r"[ \t]*/\* TODO:[^\n]*\*/\n[ \t]*return 0;\n"),
}

SOLUTIONS: dict[str, dict[str, str]] = {}


def _fill(slug: str, language: str, body: str, prelude: str = "") -> str:
    source = build_starters(_PROBLEM_BY_SLUG[slug])[language]
    match = _STUB[language].search(source)
    if match is None:
        raise RuntimeError(f"no TODO stub found in the {language} starter for {slug}")
    filled = source[: match.start()] + body + source[match.end() :]
    if prelude:
        # The signature line is the one immediately before the stub.
        signature_start = filled.rfind("\n", 0, match.start() - 1) + 1
        filled = filled[:signature_start] + prelude + filled[signature_start:]
    return filled


def register(slug: str, bodies: dict[str, str], preludes: dict[str, str] | None = None) -> None:
    preludes = preludes or {}
    SOLUTIONS[slug] = {
        language: _fill(slug, language, body, preludes.get(language, ""))
        for language, body in bodies.items()
    }


# Problems whose answer is a sequence print a count line and then the values,
# which the generated starter's single-value `print` cannot express. Those
# solutions are written out in full instead of being derived from the starter,
# exactly as the learner has to restructure `main` for themselves.

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

        String nextLine() throws IOException {
            StringBuilder sb = new StringBuilder();
            int c = read();
            while (c != -1 && c != '\\n') {
                if (c != '\\r') sb.append((char) c);
                c = read();
            }
            return sb.toString();
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


def register_full(
    slug: str, python: str, javascript: str, cpp: str, java_body: str, c: str
) -> None:
    SOLUTIONS[slug] = {
        "python": python.lstrip("\n"),
        "javascript": javascript.lstrip("\n"),
        "cpp": cpp.lstrip("\n"),
        "java": _java(java_body),
        "c": c.lstrip("\n"),
    }


# --------------------------------------------------------------------------- #
#  Shared C preludes                                                          #
# --------------------------------------------------------------------------- #

_C_CMP_LL = """
static int cmp_ll(const void* a, const void* b) {
    long long x = *(const long long*)a;
    long long y = *(const long long*)b;
    return (x > y) - (x < y);
}

"""

# --------------------------------------------------------------------------- #
#  01 · two-sum                                                               #
# --------------------------------------------------------------------------- #

register_full(
    "two-sum",
    python='''
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    target = int(data[1])
    seen = {}
    for i in range(n):
        value = int(data[2 + i])
        need = target - value
        if need in seen:
            print(seen[need], i)
            return
        if value not in seen:
            seen[value] = i


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
const n = data[0];
const target = data[1];
const seen = new Map();
for (let i = 0; i < n; i++) {
  const value = data[2 + i];
  const need = target - value;
  if (seen.has(need)) {
    console.log(seen.get(need) + " " + i);
    break;
  }
  if (!seen.has(value)) seen.set(value, i);
}
''',
    cpp='''
#include <iostream>
#include <unordered_map>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    long long target;
    if (!(std::cin >> n >> target)) return 0;
    std::unordered_map<long long, int> seen;
    seen.reserve(static_cast<size_t>(n) * 2);
    for (int i = 0; i < n; i++) {
        long long value;
        std::cin >> value;
        auto it = seen.find(target - value);
        if (it != seen.end()) {
            std::cout << it->second << " " << i << "\\n";
            return 0;
        }
        if (seen.find(value) == seen.end()) seen[value] = i;
    }
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long target = in.nextLong();
        HashMap<Long, Integer> seen = new HashMap<>();
        for (int i = 0; i < n; i++) {
            long value = in.nextLong();
            Integer at = seen.get(target - value);
            if (at != null) {
                System.out.println(at + " " + i);
                return;
            }
            seen.putIfAbsent(value, i);
        }
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

typedef struct { long long value; int index; } Pair;

static int cmp_pair(const void* a, const void* b) {
    const Pair* x = (const Pair*)a;
    const Pair* y = (const Pair*)b;
    return (x->value > y->value) - (x->value < y->value);
}

int main(void) {
    int n = 0;
    long long target = 0;
    if (scanf("%d %lld", &n, &target) != 2) return 0;
    long long* arr = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    Pair* pairs = (Pair*)malloc((size_t)(n > 0 ? n : 1) * sizeof(Pair));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &arr[i]) != 1) break;
        pairs[i].value = arr[i];
        pairs[i].index = i;
    }
    qsort(pairs, (size_t)n, sizeof(Pair), cmp_pair);
    int lo = 0, hi = n - 1;
    while (lo < hi) {
        long long sum = pairs[lo].value + pairs[hi].value;
        if (sum == target) {
            /* qsort is not stable and the pair's values may repeat, so resolve
               the positions against the original array: the first index holding
               either value, then the first later index holding its complement. */
            long long a = pairs[lo].value;
            long long b = pairs[hi].value;
            int first = -1;
            for (int i = 0; i < n; i++) {
                if (arr[i] == a || arr[i] == b) { first = i; break; }
            }
            long long need = target - arr[first];
            int second = -1;
            for (int i = first + 1; i < n; i++) {
                if (arr[i] == need) { second = i; break; }
            }
            printf("%d %d\\n", first, second);
            break;
        }
        if (sum < target) lo++; else hi--;
    }
    free(pairs);
    free(arr);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  02 · contains-duplicate                                                    #
# --------------------------------------------------------------------------- #

register(
    "contains-duplicate",
    {
        "python": """
    return 1 if len(set(arr)) != len(arr) else 0
""".lstrip("\n"),
        "javascript": """
  return new Set(arr).size !== arr.length ? 1 : 0;
""".lstrip("\n"),
        "cpp": """
    std::unordered_set<long long> seen;
    seen.reserve(arr.size() * 2);
    for (long long value : arr) {
        if (!seen.insert(value).second) return 1;
    }
    return 0;
""".lstrip("\n"),
        "java": """
        HashSet<Long> seen = new HashSet<>();
        for (long value : arr) {
            if (!seen.add(value)) return 1;
        }
        return 0;
""".lstrip("\n"),
        "c": """
    long long* copy = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) copy[i] = arr[i];
    qsort(copy, (size_t)n, sizeof(long long), cmp_ll);
    int found = 0;
    for (int i = 1; i < n; i++) {
        if (copy[i] == copy[i - 1]) { found = 1; break; }
    }
    free(copy);
    return found;
""".lstrip("\n"),
    },
    {"c": _C_CMP_LL},
)


# --------------------------------------------------------------------------- #
#  03 · product-except-self                                                   #
# --------------------------------------------------------------------------- #

register_full(
    "product-except-self",
    python='''
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
    sys.stdout.write(str(n) + "\\n")
    sys.stdout.write(" ".join(map(str, out)) + "\\n")


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
const n = data[0];
const arr = data.slice(1, 1 + n);
const out = new Array(n).fill(1);
let prefix = 1;
for (let i = 0; i < n; i++) {
  out[i] = prefix;
  prefix *= arr[i];
}
let suffix = 1;
for (let i = n - 1; i >= 0; i--) {
  out[i] *= suffix;
  suffix *= arr[i];
}
console.log(String(n));
console.log(out.join(" "));
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
    std::vector<long long> arr(n);
    for (int i = 0; i < n; i++) std::cin >> arr[i];
    std::vector<long long> out(n, 1);
    long long prefix = 1;
    for (int i = 0; i < n; i++) {
        out[i] = prefix;
        prefix *= arr[i];
    }
    long long suffix = 1;
    for (int i = n - 1; i >= 0; i--) {
        out[i] *= suffix;
        suffix *= arr[i];
    }
    std::string result;
    result.reserve(static_cast<size_t>(n) * 8);
    for (int i = 0; i < n; i++) {
        if (i) result.push_back(' ');
        result += std::to_string(out[i]);
    }
    std::cout << n << "\\n" << result << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] arr = new long[n];
        for (int i = 0; i < n; i++) arr[i] = in.nextLong();
        long[] out = new long[n];
        long prefix = 1L;
        for (int i = 0; i < n; i++) {
            out[i] = prefix;
            prefix *= arr[i];
        }
        long suffix = 1L;
        for (int i = n - 1; i >= 0; i--) {
            out[i] *= suffix;
            suffix *= arr[i];
        }
        StringBuilder sb = new StringBuilder();
        sb.append(n).append('\\n');
        for (int i = 0; i < n; i++) {
            if (i > 0) sb.append(' ');
            sb.append(out[i]);
        }
        sb.append('\\n');
        System.out.print(sb);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long long* arr = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    long long* out = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &arr[i]) != 1) break;
    }
    long long prefix = 1;
    for (int i = 0; i < n; i++) {
        out[i] = prefix;
        prefix *= arr[i];
    }
    long long suffix = 1;
    for (int i = n - 1; i >= 0; i--) {
        out[i] *= suffix;
        suffix *= arr[i];
    }
    printf("%d\\n", n);
    for (int i = 0; i < n; i++) {
        printf(i + 1 < n ? "%lld " : "%lld", out[i]);
    }
    printf("\\n");
    free(arr);
    free(out);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  04 · max-product-subarray                                                  #
# --------------------------------------------------------------------------- #

register(
    "max-product-subarray",
    {
        "python": """
    best = cur_max = cur_min = arr[0]
    for value in arr[1:]:
        a = cur_max * value
        b = cur_min * value
        cur_max = max(value, a, b)
        cur_min = min(value, a, b)
        if cur_max > best:
            best = cur_max
    return best
""".lstrip("\n"),
        "javascript": """
  let best = arr[0];
  let curMax = arr[0];
  let curMin = arr[0];
  for (let i = 1; i < arr.length; i++) {
    const v = arr[i];
    const a = curMax * v;
    const b = curMin * v;
    curMax = Math.max(v, a, b);
    curMin = Math.min(v, a, b);
    if (curMax > best) best = curMax;
  }
  return best;
""".lstrip("\n"),
        "cpp": """
    long long best = arr[0];
    long long curMax = arr[0];
    long long curMin = arr[0];
    for (size_t i = 1; i < arr.size(); i++) {
        long long v = arr[i];
        long long a = curMax * v;
        long long b = curMin * v;
        curMax = std::max(v, std::max(a, b));
        curMin = std::min(v, std::min(a, b));
        if (curMax > best) best = curMax;
    }
    return best;
""".lstrip("\n"),
        "java": """
        long best = arr[0];
        long curMax = arr[0];
        long curMin = arr[0];
        for (int i = 1; i < arr.length; i++) {
            long v = arr[i];
            long a = curMax * v;
            long b = curMin * v;
            curMax = Math.max(v, Math.max(a, b));
            curMin = Math.min(v, Math.min(a, b));
            if (curMax > best) best = curMax;
        }
        return best;
""".lstrip("\n"),
        "c": """
    long long best = arr[0];
    long long cur_max = arr[0];
    long long cur_min = arr[0];
    for (int i = 1; i < n; i++) {
        long long v = arr[i];
        long long a = cur_max * v;
        long long b = cur_min * v;
        long long hi = v > a ? v : a;
        if (b > hi) hi = b;
        long long lo = v < a ? v : a;
        if (b < lo) lo = b;
        cur_max = hi;
        cur_min = lo;
        if (cur_max > best) best = cur_max;
    }
    return best;
""".lstrip("\n"),
    },
)


# --------------------------------------------------------------------------- #
#  05 · find-min-rotated                                                      #
# --------------------------------------------------------------------------- #

register(
    "find-min-rotated",
    {
        "python": """
    lo, hi = 0, len(arr) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] > arr[hi]:
            lo = mid + 1
        else:
            hi = mid
    return arr[lo]
""".lstrip("\n"),
        "javascript": """
  let lo = 0;
  let hi = arr.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] > arr[hi]) lo = mid + 1;
    else hi = mid;
  }
  return arr[lo];
""".lstrip("\n"),
        "cpp": """
    int lo = 0;
    int hi = static_cast<int>(arr.size()) - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] > arr[hi]) lo = mid + 1;
        else hi = mid;
    }
    return arr[lo];
""".lstrip("\n"),
        "java": """
        int lo = 0;
        int hi = arr.length - 1;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (arr[mid] > arr[hi]) lo = mid + 1;
            else hi = mid;
        }
        return arr[lo];
""".lstrip("\n"),
        "c": """
    int lo = 0;
    int hi = n - 1;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] > arr[hi]) lo = mid + 1;
        else hi = mid;
    }
    return arr[lo];
""".lstrip("\n"),
    },
)


# --------------------------------------------------------------------------- #
#  06 · search-rotated                                                        #
# --------------------------------------------------------------------------- #

register_full(
    "search-rotated",
    python='''
import sys


def main():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    q = int(data[1])
    arr = [int(x) for x in data[2:2 + n]]
    out = []
    for raw in data[2 + n:2 + n + q]:
        target = int(raw)
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
    sys.stdout.write(str(q) + "\\n")
    sys.stdout.write(" ".join(map(str, out)) + "\\n")


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean);
const n = Number(data[0]);
const q = Number(data[1]);
const arr = new Float64Array(n);
for (let i = 0; i < n; i++) arr[i] = Number(data[2 + i]);
const out = new Array(q);
for (let k = 0; k < q; k++) {
  const target = Number(data[2 + n + k]);
  let lo = 0;
  let hi = n - 1;
  let found = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] === target) { found = mid; break; }
    if (arr[lo] <= arr[mid]) {
      if (arr[lo] <= target && target < arr[mid]) hi = mid - 1;
      else lo = mid + 1;
    } else {
      if (arr[mid] < target && target <= arr[hi]) lo = mid + 1;
      else hi = mid - 1;
    }
  }
  out[k] = found;
}
console.log(String(q));
console.log(out.join(" "));
''',
    cpp='''
#include <iostream>
#include <string>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n, q;
    if (!(std::cin >> n >> q)) return 0;
    std::vector<long long> arr(n);
    for (int i = 0; i < n; i++) std::cin >> arr[i];
    std::string result;
    result.reserve(static_cast<size_t>(q) * 7);
    for (int k = 0; k < q; k++) {
        long long target;
        std::cin >> target;
        int lo = 0, hi = n - 1, found = -1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (arr[mid] == target) { found = mid; break; }
            if (arr[lo] <= arr[mid]) {
                if (arr[lo] <= target && target < arr[mid]) hi = mid - 1;
                else lo = mid + 1;
            } else {
                if (arr[mid] < target && target <= arr[hi]) lo = mid + 1;
                else hi = mid - 1;
            }
        }
        if (k) result.push_back(' ');
        result += std::to_string(found);
    }
    std::cout << q << "\\n" << result << "\\n";
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        int q = (int) in.nextLong();
        long[] arr = new long[n];
        for (int i = 0; i < n; i++) arr[i] = in.nextLong();
        StringBuilder sb = new StringBuilder();
        sb.append(q).append('\\n');
        for (int k = 0; k < q; k++) {
            long target = in.nextLong();
            int lo = 0, hi = n - 1, found = -1;
            while (lo <= hi) {
                int mid = lo + (hi - lo) / 2;
                if (arr[mid] == target) { found = mid; break; }
                if (arr[lo] <= arr[mid]) {
                    if (arr[lo] <= target && target < arr[mid]) hi = mid - 1;
                    else lo = mid + 1;
                } else {
                    if (arr[mid] < target && target <= arr[hi]) lo = mid + 1;
                    else hi = mid - 1;
                }
            }
            if (k > 0) sb.append(' ');
            sb.append(found);
        }
        sb.append('\\n');
        System.out.print(sb);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n = 0, q = 0;
    if (scanf("%d %d", &n, &q) != 2) return 0;
    long long* arr = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &arr[i]) != 1) break;
    }
    printf("%d\\n", q);
    for (int k = 0; k < q; k++) {
        long long target = 0;
        if (scanf("%lld", &target) != 1) break;
        int lo = 0, hi = n - 1, found = -1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (arr[mid] == target) { found = mid; break; }
            if (arr[lo] <= arr[mid]) {
                if (arr[lo] <= target && target < arr[mid]) hi = mid - 1;
                else lo = mid + 1;
            } else {
                if (arr[mid] < target && target <= arr[hi]) lo = mid + 1;
                else hi = mid - 1;
            }
        }
        printf(k + 1 < q ? "%d " : "%d", found);
    }
    printf("\\n");
    free(arr);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  07 · three-sum                                                       #
# --------------------------------------------------------------------------- #

register_full(
    "three-sum",
    python='''
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
            total = arr[i] + arr[lo] + arr[hi]
            if total < 0:
                lo += 1
            elif total > 0:
                hi -= 1
            else:
                out.append("%d %d %d" % (arr[i], arr[lo], arr[hi]))
                lo += 1
                while lo < hi and arr[lo] == arr[lo - 1]:
                    lo += 1
                hi -= 1
                while lo < hi and arr[hi] == arr[hi + 1]:
                    hi -= 1
        i += 1
    sys.stdout.write(str(len(out)) + "\\n")
    if out:
        sys.stdout.write("\\n".join(out) + "\\n")


main()
''',
    javascript='''
const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
const n = data[0];
const arr = data.slice(1, 1 + n).sort((a, b) => a - b);
const out = [];
let i = 0;
while (i < n - 2) {
  if (i > 0 && arr[i] === arr[i - 1]) { i++; continue; }
  let lo = i + 1;
  let hi = n - 1;
  while (lo < hi) {
    const total = arr[i] + arr[lo] + arr[hi];
    if (total < 0) lo++;
    else if (total > 0) hi--;
    else {
      out.push(arr[i] + " " + arr[lo] + " " + arr[hi]);
      lo++;
      while (lo < hi && arr[lo] === arr[lo - 1]) lo++;
      hi--;
      while (lo < hi && arr[hi] === arr[hi + 1]) hi--;
    }
  }
  i++;
}
process.stdout.write(out.length + "\\n" + (out.length ? out.join("\\n") + "\\n" : ""));
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
    std::vector<long long> arr(n);
    for (int i = 0; i < n; i++) std::cin >> arr[i];
    std::sort(arr.begin(), arr.end());
    std::string result;
    int count = 0;
    int i = 0;
    while (i < n - 2) {
        if (i > 0 && arr[i] == arr[i - 1]) { i++; continue; }
        int lo = i + 1, hi = n - 1;
        while (lo < hi) {
            long long total = arr[i] + arr[lo] + arr[hi];
            if (total < 0) lo++;
            else if (total > 0) hi--;
            else {
                result += std::to_string(arr[i]);
                result.push_back(' ');
                result += std::to_string(arr[lo]);
                result.push_back(' ');
                result += std::to_string(arr[hi]);
                result.push_back('\\n');
                count++;
                lo++;
                while (lo < hi && arr[lo] == arr[lo - 1]) lo++;
                hi--;
                while (lo < hi && arr[hi] == arr[hi + 1]) hi--;
            }
        }
        i++;
    }
    std::cout << count << "\\n" << result;
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] arr = new long[n];
        for (int i = 0; i < n; i++) arr[i] = in.nextLong();
        Arrays.sort(arr);
        StringBuilder body = new StringBuilder();
        int count = 0;
        int i = 0;
        while (i < n - 2) {
            if (i > 0 && arr[i] == arr[i - 1]) { i++; continue; }
            int lo = i + 1, hi = n - 1;
            while (lo < hi) {
                long total = arr[i] + arr[lo] + arr[hi];
                if (total < 0) lo++;
                else if (total > 0) hi--;
                else {
                    body.append(arr[i]).append(' ').append(arr[lo]).append(' ')
                        .append(arr[hi]).append('\\n');
                    count++;
                    lo++;
                    while (lo < hi && arr[lo] == arr[lo - 1]) lo++;
                    hi--;
                    while (lo < hi && arr[hi] == arr[hi + 1]) hi--;
                }
            }
            i++;
        }
        System.out.print(count + "\\n" + body);
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
    long long* arr = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &arr[i]) != 1) break;
    }
    qsort(arr, (size_t)n, sizeof(long long), cmp_ll);
    int capacity = 64, count = 0;
    long long* triplets = (long long*)malloc((size_t)capacity * 3 * sizeof(long long));
    int i = 0;
    while (i < n - 2) {
        if (i > 0 && arr[i] == arr[i - 1]) { i++; continue; }
        int lo = i + 1, hi = n - 1;
        while (lo < hi) {
            long long total = arr[i] + arr[lo] + arr[hi];
            if (total < 0) lo++;
            else if (total > 0) hi--;
            else {
                if (count == capacity) {
                    capacity *= 2;
                    triplets = (long long*)realloc(
                        triplets, (size_t)capacity * 3 * sizeof(long long));
                }
                triplets[count * 3] = arr[i];
                triplets[count * 3 + 1] = arr[lo];
                triplets[count * 3 + 2] = arr[hi];
                count++;
                lo++;
                while (lo < hi && arr[lo] == arr[lo - 1]) lo++;
                hi--;
                while (lo < hi && arr[hi] == arr[hi + 1]) hi--;
            }
        }
        i++;
    }
    printf("%d\\n", count);
    for (int k = 0; k < count; k++) {
        printf("%lld %lld %lld\\n", triplets[k * 3], triplets[k * 3 + 1], triplets[k * 3 + 2]);
    }
    free(triplets);
    free(arr);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  08 · container-most-water                                                  #
# --------------------------------------------------------------------------- #

register(
    "container-most-water",
    {
        "python": """
    lo, hi = 0, len(height) - 1
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
    return best
""".lstrip("\n"),
        "javascript": """
  let lo = 0;
  let hi = height.length - 1;
  let best = 0;
  while (lo < hi) {
    const left = height[lo];
    const right = height[hi];
    const area = (hi - lo) * Math.min(left, right);
    if (area > best) best = area;
    if (left < right) lo++;
    else hi--;
  }
  return best;
""".lstrip("\n"),
        "cpp": """
    int lo = 0;
    int hi = static_cast<int>(height.size()) - 1;
    long long best = 0;
    while (lo < hi) {
        long long left = height[lo];
        long long right = height[hi];
        long long area = static_cast<long long>(hi - lo) * std::min(left, right);
        if (area > best) best = area;
        if (left < right) lo++;
        else hi--;
    }
    return best;
""".lstrip("\n"),
        "java": """
        int lo = 0;
        int hi = height.length - 1;
        long best = 0;
        while (lo < hi) {
            long left = height[lo];
            long right = height[hi];
            long area = (long) (hi - lo) * Math.min(left, right);
            if (area > best) best = area;
            if (left < right) lo++;
            else hi--;
        }
        return best;
""".lstrip("\n"),
        "c": """
    int lo = 0;
    int hi = n - 1;
    long long best = 0;
    while (lo < hi) {
        long long left = height[lo];
        long long right = height[hi];
        long long shorter = left < right ? left : right;
        long long area = (long long)(hi - lo) * shorter;
        if (area > best) best = area;
        if (left < right) lo++;
        else hi--;
    }
    return best;
""".lstrip("\n"),
    },
)


# --------------------------------------------------------------------------- #
#  09 · best-time-stock                                                       #
# --------------------------------------------------------------------------- #

register(
    "best-time-stock",
    {
        "python": """
    best = 0
    cheapest = prices[0]
    for price in prices[1:]:
        if price - cheapest > best:
            best = price - cheapest
        if price < cheapest:
            cheapest = price
    return best
""".lstrip("\n"),
        "javascript": """
  let best = 0;
  let cheapest = prices[0];
  for (let i = 1; i < prices.length; i++) {
    const price = prices[i];
    if (price - cheapest > best) best = price - cheapest;
    if (price < cheapest) cheapest = price;
  }
  return best;
""".lstrip("\n"),
        "cpp": """
    long long best = 0;
    long long cheapest = prices[0];
    for (size_t i = 1; i < prices.size(); i++) {
        long long price = prices[i];
        if (price - cheapest > best) best = price - cheapest;
        if (price < cheapest) cheapest = price;
    }
    return best;
""".lstrip("\n"),
        "java": """
        long best = 0;
        long cheapest = prices[0];
        for (int i = 1; i < prices.length; i++) {
            long price = prices[i];
            if (price - cheapest > best) best = price - cheapest;
            if (price < cheapest) cheapest = price;
        }
        return best;
""".lstrip("\n"),
        "c": """
    long long best = 0;
    long long cheapest = prices[0];
    for (int i = 1; i < n; i++) {
        long long price = prices[i];
        if (price - cheapest > best) best = price - cheapest;
        if (price < cheapest) cheapest = price;
    }
    return best;
""".lstrip("\n"),
    },
)


# --------------------------------------------------------------------------- #
#  10 · longest-repeat-char-replacement                                       #
# --------------------------------------------------------------------------- #

register(
    "longest-repeat-char-replacement",
    {
        "python": """
    s, _, k_text = line.rpartition(' ')
    k = int(k_text)
    counts = [0] * 26
    best = 0
    max_count = 0
    start = 0
    for end in range(len(s)):
        index = ord(s[end]) - 65
        counts[index] += 1
        if counts[index] > max_count:
            max_count = counts[index]
        while (end - start + 1) - max_count > k:
            counts[ord(s[start]) - 65] -= 1
            start += 1
            max_count = max(counts)
        if end - start + 1 > best:
            best = end - start + 1
    return best
""".lstrip("\n"),
        "javascript": """
  const cut = line.lastIndexOf(" ");
  const s = line.slice(0, cut);
  const k = Number(line.slice(cut + 1));
  const counts = new Array(26).fill(0);
  let best = 0;
  let maxCount = 0;
  let start = 0;
  for (let end = 0; end < s.length; end++) {
    const index = s.charCodeAt(end) - 65;
    counts[index] += 1;
    if (counts[index] > maxCount) maxCount = counts[index];
    while (end - start + 1 - maxCount > k) {
      counts[s.charCodeAt(start) - 65] -= 1;
      start += 1;
      maxCount = Math.max(...counts);
    }
    if (end - start + 1 > best) best = end - start + 1;
  }
  return best;
""".lstrip("\n"),
        "cpp": """
    size_t cut = line.rfind(' ');
    std::string s = line.substr(0, cut);
    int k = std::stoi(line.substr(cut + 1));
    int counts[26] = {0};
    int best = 0;
    int maxCount = 0;
    int start = 0;
    for (int end = 0; end < static_cast<int>(s.size()); end++) {
        counts[s[end] - 'A']++;
        if (counts[s[end] - 'A'] > maxCount) maxCount = counts[s[end] - 'A'];
        while (end - start + 1 - maxCount > k) {
            counts[s[start] - 'A']--;
            start++;
            maxCount = 0;
            for (int i = 0; i < 26; i++) maxCount = std::max(maxCount, counts[i]);
        }
        if (end - start + 1 > best) best = end - start + 1;
    }
    return best;
""".lstrip("\n"),
        "java": """
        int cut = line.lastIndexOf(' ');
        String s = line.substring(0, cut);
        int k = Integer.parseInt(line.substring(cut + 1).trim());
        int[] counts = new int[26];
        int best = 0;
        int maxCount = 0;
        int start = 0;
        for (int end = 0; end < s.length(); end++) {
            counts[s.charAt(end) - 'A']++;
            maxCount = Math.max(maxCount, counts[s.charAt(end) - 'A']);
            while (end - start + 1 - maxCount > k) {
                counts[s.charAt(start) - 'A']--;
                start++;
                maxCount = 0;
                for (int i = 0; i < 26; i++) maxCount = Math.max(maxCount, counts[i]);
            }
            if (end - start + 1 > best) best = end - start + 1;
        }
        return best;
""".lstrip("\n"),
        "c": """
    const char* cut = strrchr(line, ' ');
    int k = atoi(cut + 1);
    int len = (int)(cut - line);
    int counts[26] = {0};
    int best = 0;
    int max_count = 0;
    int start = 0;
    for (int end = 0; end < len; end++) {
        int index = line[end] - 'A';
        counts[index]++;
        if (counts[index] > max_count) max_count = counts[index];
        while (end - start + 1 - max_count > k) {
            counts[line[start] - 'A']--;
            start++;
            max_count = 0;
            for (int i = 0; i < 26; i++) {
                if (counts[i] > max_count) max_count = counts[i];
            }
        }
        if (end - start + 1 > best) best = end - start + 1;
    }
    return best;
""".lstrip("\n"),
    },
)


# --------------------------------------------------------------------------- #
#  11 · min-window-substring                                                  #
# --------------------------------------------------------------------------- #

register(
    "min-window-substring",
    {
        "python": """
    cut = line.find(' ')
    s = line[:cut]
    t = line[cut + 1:]
    if not t or len(t) > len(s):
        return 0
    need = [0] * 128
    required = 0
    for ch in t:
        if need[ord(ch)] == 0:
            required += 1
        need[ord(ch)] += 1
    have = [0] * 128
    missing = required
    best = len(s) + 1
    start = 0
    for end in range(len(s)):
        code = ord(s[end])
        if need[code]:
            have[code] += 1
            if have[code] == need[code]:
                missing -= 1
        while missing == 0:
            if end - start + 1 < best:
                best = end - start + 1
            left = ord(s[start])
            if need[left]:
                have[left] -= 1
                if have[left] < need[left]:
                    missing += 1
            start += 1
    return 0 if best > len(s) else best
""".lstrip("\n"),
        "javascript": """
  const cut = line.indexOf(" ");
  const s = line.slice(0, cut);
  const t = line.slice(cut + 1);
  if (t.length === 0 || t.length > s.length) return 0;
  const need = new Array(128).fill(0);
  let required = 0;
  for (let i = 0; i < t.length; i++) {
    const code = t.charCodeAt(i);
    if (need[code] === 0) required += 1;
    need[code] += 1;
  }
  const have = new Array(128).fill(0);
  let missing = required;
  let best = s.length + 1;
  let start = 0;
  for (let end = 0; end < s.length; end++) {
    const code = s.charCodeAt(end);
    if (need[code] > 0) {
      have[code] += 1;
      if (have[code] === need[code]) missing -= 1;
    }
    while (missing === 0) {
      if (end - start + 1 < best) best = end - start + 1;
      const left = s.charCodeAt(start);
      if (need[left] > 0) {
        have[left] -= 1;
        if (have[left] < need[left]) missing += 1;
      }
      start += 1;
    }
  }
  return best > s.length ? 0 : best;
""".lstrip("\n"),
        "cpp": """
    size_t cut = line.find(' ');
    std::string s = line.substr(0, cut);
    std::string t = line.substr(cut + 1);
    if (t.empty() || t.size() > s.size()) return 0;
    int need[128] = {0};
    int required = 0;
    for (char ch : t) {
        if (need[(int)ch] == 0) required++;
        need[(int)ch]++;
    }
    int have[128] = {0};
    int missing = required;
    int best = static_cast<int>(s.size()) + 1;
    int start = 0;
    for (int end = 0; end < static_cast<int>(s.size()); end++) {
        int code = (int)s[end];
        if (need[code] > 0) {
            have[code]++;
            if (have[code] == need[code]) missing--;
        }
        while (missing == 0) {
            if (end - start + 1 < best) best = end - start + 1;
            int left = (int)s[start];
            if (need[left] > 0) {
                have[left]--;
                if (have[left] < need[left]) missing++;
            }
            start++;
        }
    }
    return best > static_cast<int>(s.size()) ? 0 : best;
""".lstrip("\n"),
        "java": """
        int cut = line.indexOf(' ');
        String s = line.substring(0, cut);
        String t = line.substring(cut + 1).trim();
        if (t.isEmpty() || t.length() > s.length()) return 0;
        int[] need = new int[128];
        int required = 0;
        for (int i = 0; i < t.length(); i++) {
            if (need[t.charAt(i)] == 0) required++;
            need[t.charAt(i)]++;
        }
        int[] have = new int[128];
        int missing = required;
        int best = s.length() + 1;
        int start = 0;
        for (int end = 0; end < s.length(); end++) {
            char code = s.charAt(end);
            if (need[code] > 0) {
                have[code]++;
                if (have[code] == need[code]) missing--;
            }
            while (missing == 0) {
                if (end - start + 1 < best) best = end - start + 1;
                char left = s.charAt(start);
                if (need[left] > 0) {
                    have[left]--;
                    if (have[left] < need[left]) missing++;
                }
                start++;
            }
        }
        return best > s.length() ? 0 : best;
""".lstrip("\n"),
        "c": """
    const char* cut = strchr(line, ' ');
    int slen = (int)(cut - line);
    const char* t = cut + 1;
    int tlen = (int)strlen(t);
    if (tlen == 0 || tlen > slen) return 0;
    int need[128] = {0};
    int required = 0;
    for (int i = 0; i < tlen; i++) {
        if (need[(unsigned char)t[i]] == 0) required++;
        need[(unsigned char)t[i]]++;
    }
    int have[128] = {0};
    int missing = required;
    int best = slen + 1;
    int start = 0;
    for (int end = 0; end < slen; end++) {
        int code = (unsigned char)line[end];
        if (need[code] > 0) {
            have[code]++;
            if (have[code] == need[code]) missing--;
        }
        while (missing == 0) {
            if (end - start + 1 < best) best = end - start + 1;
            int left = (unsigned char)line[start];
            if (need[left] > 0) {
                have[left]--;
                if (have[left] < need[left]) missing++;
            }
            start++;
        }
    }
    return best > slen ? 0 : best;
""".lstrip("\n"),
    },
)


# --------------------------------------------------------------------------- #
#  12 · valid-anagram                                                         #
# --------------------------------------------------------------------------- #

register(
    "valid-anagram",
    {
        "python": """
    cut = line.find(' ')
    s = line[:cut]
    t = line[cut + 1:]
    if len(s) != len(t):
        return 0
    counts = [0] * 26
    for ch in s:
        counts[ord(ch) - 97] += 1
    for ch in t:
        counts[ord(ch) - 97] -= 1
    return 0 if any(counts) else 1
""".lstrip("\n"),
        "javascript": """
  const cut = line.indexOf(" ");
  const s = line.slice(0, cut);
  const t = line.slice(cut + 1);
  if (s.length !== t.length) return 0;
  const counts = new Array(26).fill(0);
  for (let i = 0; i < s.length; i++) counts[s.charCodeAt(i) - 97] += 1;
  for (let i = 0; i < t.length; i++) counts[t.charCodeAt(i) - 97] -= 1;
  return counts.some((c) => c !== 0) ? 0 : 1;
""".lstrip("\n"),
        "cpp": """
    size_t cut = line.find(' ');
    std::string s = line.substr(0, cut);
    std::string t = line.substr(cut + 1);
    if (s.size() != t.size()) return 0;
    int counts[26] = {0};
    for (char ch : s) counts[ch - 'a']++;
    for (char ch : t) counts[ch - 'a']--;
    for (int i = 0; i < 26; i++) {
        if (counts[i] != 0) return 0;
    }
    return 1;
""".lstrip("\n"),
        "java": """
        int cut = line.indexOf(' ');
        String s = line.substring(0, cut);
        String t = line.substring(cut + 1).trim();
        if (s.length() != t.length()) return 0;
        int[] counts = new int[26];
        for (int i = 0; i < s.length(); i++) counts[s.charAt(i) - 'a']++;
        for (int i = 0; i < t.length(); i++) counts[t.charAt(i) - 'a']--;
        for (int c : counts) {
            if (c != 0) return 0;
        }
        return 1;
""".lstrip("\n"),
        "c": """
    const char* cut = strchr(line, ' ');
    int slen = (int)(cut - line);
    const char* t = cut + 1;
    int tlen = (int)strlen(t);
    if (slen != tlen) return 0;
    int counts[26] = {0};
    for (int i = 0; i < slen; i++) counts[line[i] - 'a']++;
    for (int i = 0; i < tlen; i++) counts[t[i] - 'a']--;
    for (int i = 0; i < 26; i++) {
        if (counts[i] != 0) return 0;
    }
    return 1;
""".lstrip("\n"),
    },
)


# --------------------------------------------------------------------------- #
#  13 · group-anagrams                                                  #
# --------------------------------------------------------------------------- #

_C_STRING_SORTS = """
static int cmp_char(const void* a, const void* b) {
    return (*(const char*)a) - (*(const char*)b);
}

static int cmp_str(const void* a, const void* b) {
    return strcmp(*(const char* const*)a, *(const char* const*)b);
}

"""

register_full(
    "group-anagrams",
    python='''
import sys


def main():
    words = sys.stdin.readline().rstrip("\\n").split()
    groups = {}
    for word in words:
        groups.setdefault("".join(sorted(word)), []).append(word)
    ordered = []
    for members in groups.values():
        members.sort()
        ordered.append(members)
    ordered.sort(key=lambda members: members[0])
    out = [str(len(ordered))]
    for members in ordered:
        out.append(str(len(members)) + " " + " ".join(members))
    sys.stdout.write("\\n".join(out) + "\\n")


main()
''',
    javascript='''
const line = require("fs").readFileSync(0, "utf8").split("\\n")[0] || "";
const words = line.split(/\\s+/).filter(Boolean);
const groups = new Map();
for (const word of words) {
  const key = word.split("").sort().join("");
  if (!groups.has(key)) groups.set(key, []);
  groups.get(key).push(word);
}
const ordered = [];
for (const members of groups.values()) {
  members.sort();
  ordered.push(members);
}
ordered.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
const out = [String(ordered.length)];
for (const members of ordered) out.push(members.length + " " + members.join(" "));
process.stdout.write(out.join("\\n") + "\\n");
''',
    cpp='''
#include <algorithm>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    std::string line;
    std::getline(std::cin, line);
    std::istringstream stream(line);
    std::unordered_map<std::string, std::vector<std::string>> groups;
    std::string word;
    while (stream >> word) {
        std::string key = word;
        std::sort(key.begin(), key.end());
        groups[key].push_back(word);
    }
    std::vector<std::vector<std::string>> ordered;
    ordered.reserve(groups.size());
    for (auto& entry : groups) {
        std::sort(entry.second.begin(), entry.second.end());
        ordered.push_back(std::move(entry.second));
    }
    std::sort(ordered.begin(), ordered.end(),
              [](const std::vector<std::string>& a, const std::vector<std::string>& b) {
                  return a[0] < b[0];
              });
    std::string result = std::to_string(ordered.size());
    result.push_back('\\n');
    for (const auto& members : ordered) {
        result += std::to_string(members.size());
        for (const auto& member : members) {
            result.push_back(' ');
            result += member;
        }
        result.push_back('\\n');
    }
    std::cout << result;
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        String line = in.nextLine();
        HashMap<String, List<String>> groups = new HashMap<>();
        StringTokenizer tokens = new StringTokenizer(line);
        while (tokens.hasMoreTokens()) {
            String word = tokens.nextToken();
            char[] letters = word.toCharArray();
            Arrays.sort(letters);
            groups.computeIfAbsent(new String(letters), k -> new ArrayList<>()).add(word);
        }
        List<List<String>> ordered = new ArrayList<>(groups.values());
        for (List<String> members : ordered) Collections.sort(members);
        ordered.sort(Comparator.comparing(members -> members.get(0)));
        StringBuilder sb = new StringBuilder();
        sb.append(ordered.size()).append('\\n');
        for (List<String> members : ordered) {
            sb.append(members.size());
            for (String member : members) sb.append(' ').append(member);
            sb.append('\\n');
        }
        System.out.print(sb);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { char* key; char* word; } Entry;
typedef struct { int start; int size; } Group;

static Entry* g_entries = NULL;

static int cmp_char(const void* a, const void* b) {
    return (int)(*(const char*)a) - (int)(*(const char*)b);
}

static int cmp_entry(const void* a, const void* b) {
    const Entry* x = (const Entry*)a;
    const Entry* y = (const Entry*)b;
    int byKey = strcmp(x->key, y->key);
    if (byKey != 0) return byKey;
    return strcmp(x->word, y->word);
}

static int cmp_group(const void* a, const void* b) {
    const Group* x = (const Group*)a;
    const Group* y = (const Group*)b;
    return strcmp(g_entries[x->start].word, g_entries[y->start].word);
}

int main(void) {
    size_t capacity = 1 << 12;
    char* line = (char*)malloc(capacity);
    size_t length = 0;
    int ch;
    while ((ch = getchar()) != EOF && ch != '\\n') {
        if (length + 2 > capacity) {
            capacity *= 2;
            line = (char*)realloc(line, capacity);
        }
        line[length++] = (char)ch;
    }
    line[length] = '\\0';

    int count = 0, slots = 64;
    Entry* entries = (Entry*)malloc((size_t)slots * sizeof(Entry));
    char* cursor = line;
    while (1) {
        while (*cursor == ' ' || *cursor == '\\t' || *cursor == '\\r') cursor++;
        if (*cursor == '\\0') break;
        char* start = cursor;
        while (*cursor != '\\0' && *cursor != ' ' && *cursor != '\\t' && *cursor != '\\r') cursor++;
        size_t wordLength = (size_t)(cursor - start);
        if (*cursor != '\\0') { *cursor = '\\0'; cursor++; }
        if (count == slots) {
            slots *= 2;
            entries = (Entry*)realloc(entries, (size_t)slots * sizeof(Entry));
        }
        char* key = (char*)malloc(wordLength + 1);
        memcpy(key, start, wordLength);
        key[wordLength] = '\\0';
        qsort(key, wordLength, 1, cmp_char);
        entries[count].key = key;
        entries[count].word = start;
        count++;
    }

    qsort(entries, (size_t)count, sizeof(Entry), cmp_entry);
    g_entries = entries;
    Group* groups = (Group*)malloc((size_t)(count > 0 ? count : 1) * sizeof(Group));
    int groupCount = 0;
    for (int i = 0; i < count; ) {
        int j = i + 1;
        while (j < count && strcmp(entries[j].key, entries[i].key) == 0) j++;
        groups[groupCount].start = i;
        groups[groupCount].size = j - i;
        groupCount++;
        i = j;
    }
    qsort(groups, (size_t)groupCount, sizeof(Group), cmp_group);

    printf("%d\\n", groupCount);
    for (int g = 0; g < groupCount; g++) {
        printf("%d", groups[g].size);
        for (int k = 0; k < groups[g].size; k++) {
            printf(" %s", entries[groups[g].start + k].word);
        }
        printf("\\n");
    }

    for (int i = 0; i < count; i++) free(entries[i].key);
    free(entries);
    free(groups);
    free(line);
    return 0;
}
''',
)


# --------------------------------------------------------------------------- #
#  14 · valid-parentheses                                                     #
# --------------------------------------------------------------------------- #

register(
    "valid-parentheses",
    {
        "python": """
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    for ch in s:
        if ch in '([{':
            stack.append(ch)
        elif not stack or stack.pop() != pairs[ch]:
            return 0
    return 0 if stack else 1
""".lstrip("\n"),
        "javascript": """
  const pairs = { ")": "(", "]": "[", "}": "{" };
  const stack = [];
  for (const ch of s) {
    if (ch === "(" || ch === "[" || ch === "{") stack.push(ch);
    else if (stack.length === 0 || stack.pop() !== pairs[ch]) return 0;
  }
  return stack.length === 0 ? 1 : 0;
""".lstrip("\n"),
        "cpp": """
    std::string stack;
    for (char ch : s) {
        if (ch == '(' || ch == '[' || ch == '{') {
            stack.push_back(ch);
        } else {
            char want = ch == ')' ? '(' : (ch == ']' ? '[' : '{');
            if (stack.empty() || stack.back() != want) return 0;
            stack.pop_back();
        }
    }
    return stack.empty() ? 1 : 0;
""".lstrip("\n"),
        "java": """
        Deque<Character> stack = new ArrayDeque<>();
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (ch == '(' || ch == '[' || ch == '{') {
                stack.push(ch);
            } else {
                char want = ch == ')' ? '(' : (ch == ']' ? '[' : '{');
                if (stack.isEmpty() || stack.pop() != want) return 0;
            }
        }
        return stack.isEmpty() ? 1 : 0;
""".lstrip("\n"),
        "c": """
    int len = (int)strlen(s);
    char* stack = (char*)malloc((size_t)(len > 0 ? len : 1));
    int top = 0;
    for (int i = 0; i < len; i++) {
        char ch = s[i];
        if (ch == '(' || ch == '[' || ch == '{') {
            stack[top++] = ch;
        } else {
            char want = ch == ')' ? '(' : (ch == ']' ? '[' : '{');
            if (top == 0 || stack[top - 1] != want) { free(stack); return 0; }
            top--;
        }
    }
    int ok = top == 0 ? 1 : 0;
    free(stack);
    return ok;
""".lstrip("\n"),
    },
)


# --------------------------------------------------------------------------- #
#  15 · valid-palindrome                                                      #
# --------------------------------------------------------------------------- #

register(
    "valid-palindrome",
    {
        "python": """
    lo, hi = 0, len(s) - 1
    while lo < hi:
        while lo < hi and not s[lo].isalnum():
            lo += 1
        while lo < hi and not s[hi].isalnum():
            hi -= 1
        if s[lo].lower() != s[hi].lower():
            return 0
        lo += 1
        hi -= 1
    return 1
""".lstrip("\n"),
        "javascript": """
  const isAlnum = (ch) => /[0-9a-zA-Z]/.test(ch);
  let lo = 0;
  let hi = s.length - 1;
  while (lo < hi) {
    while (lo < hi && !isAlnum(s[lo])) lo++;
    while (lo < hi && !isAlnum(s[hi])) hi--;
    if (s[lo].toLowerCase() !== s[hi].toLowerCase()) return 0;
    lo++;
    hi--;
  }
  return 1;
""".lstrip("\n"),
        "cpp": """
    int lo = 0;
    int hi = static_cast<int>(s.size()) - 1;
    while (lo < hi) {
        while (lo < hi && !std::isalnum(static_cast<unsigned char>(s[lo]))) lo++;
        while (lo < hi && !std::isalnum(static_cast<unsigned char>(s[hi]))) hi--;
        if (std::tolower(static_cast<unsigned char>(s[lo]))
            != std::tolower(static_cast<unsigned char>(s[hi]))) {
            return 0;
        }
        lo++;
        hi--;
    }
    return 1;
""".lstrip("\n"),
        "java": """
        int lo = 0;
        int hi = s.length() - 1;
        while (lo < hi) {
            while (lo < hi && !Character.isLetterOrDigit(s.charAt(lo))) lo++;
            while (lo < hi && !Character.isLetterOrDigit(s.charAt(hi))) hi--;
            if (Character.toLowerCase(s.charAt(lo)) != Character.toLowerCase(s.charAt(hi))) {
                return 0;
            }
            lo++;
            hi--;
        }
        return 1;
""".lstrip("\n"),
        "c": """
    int lo = 0;
    int hi = (int)strlen(s) - 1;
    while (lo < hi) {
        while (lo < hi && !isalnum((unsigned char)s[lo])) lo++;
        while (lo < hi && !isalnum((unsigned char)s[hi])) hi--;
        if (tolower((unsigned char)s[lo]) != tolower((unsigned char)s[hi])) return 0;
        lo++;
        hi--;
    }
    return 1;
""".lstrip("\n"),
    },
    {"c": "#include <ctype.h>\n\n", "cpp": "#include <cctype>\n\n"},
)


# --------------------------------------------------------------------------- #
#  16 · longest-palindrome-length                                             #
# --------------------------------------------------------------------------- #

register(
    "longest-palindrome-length",
    {
        "python": """
    n = len(s)
    best = 0
    for centre in range(n):
        for offset in (0, 1):
            lo, hi = centre, centre + offset
            while lo >= 0 and hi < n and s[lo] == s[hi]:
                lo -= 1
                hi += 1
            if hi - lo - 1 > best:
                best = hi - lo - 1
    return best
""".lstrip("\n"),
        "javascript": """
  const n = s.length;
  let best = 0;
  for (let centre = 0; centre < n; centre++) {
    for (const offset of [0, 1]) {
      let lo = centre;
      let hi = centre + offset;
      while (lo >= 0 && hi < n && s[lo] === s[hi]) {
        lo--;
        hi++;
      }
      if (hi - lo - 1 > best) best = hi - lo - 1;
    }
  }
  return best;
""".lstrip("\n"),
        "cpp": """
    int n = static_cast<int>(s.size());
    int best = 0;
    for (int centre = 0; centre < n; centre++) {
        for (int offset = 0; offset < 2; offset++) {
            int lo = centre;
            int hi = centre + offset;
            while (lo >= 0 && hi < n && s[lo] == s[hi]) {
                lo--;
                hi++;
            }
            if (hi - lo - 1 > best) best = hi - lo - 1;
        }
    }
    return best;
""".lstrip("\n"),
        "java": """
        int n = s.length();
        int best = 0;
        for (int centre = 0; centre < n; centre++) {
            for (int offset = 0; offset < 2; offset++) {
                int lo = centre;
                int hi = centre + offset;
                while (lo >= 0 && hi < n && s.charAt(lo) == s.charAt(hi)) {
                    lo--;
                    hi++;
                }
                if (hi - lo - 1 > best) best = hi - lo - 1;
            }
        }
        return best;
""".lstrip("\n"),
        "c": """
    int n = (int)strlen(s);
    int best = 0;
    for (int centre = 0; centre < n; centre++) {
        for (int offset = 0; offset < 2; offset++) {
            int lo = centre;
            int hi = centre + offset;
            while (lo >= 0 && hi < n && s[lo] == s[hi]) {
                lo--;
                hi++;
            }
            if (hi - lo - 1 > best) best = hi - lo - 1;
        }
    }
    return best;
""".lstrip("\n"),
    },
)


# --------------------------------------------------------------------------- #
#  17 · count-palindromic-substrings                                          #
# --------------------------------------------------------------------------- #

register(
    "count-palindromic-substrings",
    {
        "python": """
    n = len(s)
    total = 0
    for centre in range(n):
        for offset in (0, 1):
            lo, hi = centre, centre + offset
            while lo >= 0 and hi < n and s[lo] == s[hi]:
                total += 1
                lo -= 1
                hi += 1
    return total
""".lstrip("\n"),
        "javascript": """
  const n = s.length;
  let total = 0;
  for (let centre = 0; centre < n; centre++) {
    for (const offset of [0, 1]) {
      let lo = centre;
      let hi = centre + offset;
      while (lo >= 0 && hi < n && s[lo] === s[hi]) {
        total++;
        lo--;
        hi++;
      }
    }
  }
  return total;
""".lstrip("\n"),
        "cpp": """
    int n = static_cast<int>(s.size());
    long long total = 0;
    for (int centre = 0; centre < n; centre++) {
        for (int offset = 0; offset < 2; offset++) {
            int lo = centre;
            int hi = centre + offset;
            while (lo >= 0 && hi < n && s[lo] == s[hi]) {
                total++;
                lo--;
                hi++;
            }
        }
    }
    return total;
""".lstrip("\n"),
        "java": """
        int n = s.length();
        long total = 0;
        for (int centre = 0; centre < n; centre++) {
            for (int offset = 0; offset < 2; offset++) {
                int lo = centre;
                int hi = centre + offset;
                while (lo >= 0 && hi < n && s.charAt(lo) == s.charAt(hi)) {
                    total++;
                    lo--;
                    hi++;
                }
            }
        }
        return total;
""".lstrip("\n"),
        "c": """
    int n = (int)strlen(s);
    long long total = 0;
    for (int centre = 0; centre < n; centre++) {
        for (int offset = 0; offset < 2; offset++) {
            int lo = centre;
            int hi = centre + offset;
            while (lo >= 0 && hi < n && s[lo] == s[hi]) {
                total++;
                lo--;
                hi++;
            }
        }
    }
    return total;
""".lstrip("\n"),
    },
)


# --------------------------------------------------------------------------- #
#  18 · decode-encoded-strings                                                #
# --------------------------------------------------------------------------- #

register_full(
    "decode-encoded-strings",
    python='''
import sys


def main():
    line = sys.stdin.readline().rstrip("\\n")
    out = []
    pos = 0
    n = len(line)
    while pos < n:
        hash_at = line.index("#", pos)
        length = int(line[pos:hash_at])
        out.append(line[hash_at + 1:hash_at + 1 + length])
        pos = hash_at + 1 + length
    sys.stdout.write(str(len(out)) + "\\n")
    for value in out:
        sys.stdout.write(value + "\\n")


main()
''',
    javascript='''
const line = require("fs").readFileSync(0, "utf8").split("\\n")[0] || "";
const out = [];
let pos = 0;
while (pos < line.length) {
  const hashAt = line.indexOf("#", pos);
  const length = parseInt(line.slice(pos, hashAt), 10);
  out.push(line.slice(hashAt + 1, hashAt + 1 + length));
  pos = hashAt + 1 + length;
}
process.stdout.write(out.length + "\\n" + out.map((s) => s + "\\n").join(""));
''',
    cpp='''
#include <iostream>
#include <string>
#include <vector>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    std::string line;
    std::getline(std::cin, line);
    if (!line.empty() && line.back() == '\\r') line.pop_back();
    std::vector<std::string> out;
    size_t pos = 0;
    while (pos < line.size()) {
        size_t hashAt = line.find('#', pos);
        int length = std::stoi(line.substr(pos, hashAt - pos));
        out.push_back(line.substr(hashAt + 1, static_cast<size_t>(length)));
        pos = hashAt + 1 + static_cast<size_t>(length);
    }
    std::string result = std::to_string(out.size());
    result.push_back('\\n');
    for (const auto& value : out) {
        result += value;
        result.push_back('\\n');
    }
    std::cout << result;
    return 0;
}
''',
    java_body='''
    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        String line = in.nextLine();
        List<String> out = new ArrayList<>();
        int pos = 0;
        while (pos < line.length()) {
            int hashAt = line.indexOf('#', pos);
            int length = Integer.parseInt(line.substring(pos, hashAt));
            out.add(line.substring(hashAt + 1, hashAt + 1 + length));
            pos = hashAt + 1 + length;
        }
        StringBuilder sb = new StringBuilder();
        sb.append(out.size()).append('\\n');
        for (String value : out) sb.append(value).append('\\n');
        System.out.print(sb);
    }
''',
    c='''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    size_t capacity = 1 << 12;
    char* line = (char*)malloc(capacity);
    size_t length = 0;
    int ch;
    while ((ch = getchar()) != EOF && ch != '\\n') {
        if (ch == '\\r') continue;
        if (length + 2 > capacity) {
            capacity *= 2;
            line = (char*)realloc(line, capacity);
        }
        line[length++] = (char)ch;
    }
    line[length] = '\\0';

    int count = 0, slots = 64;
    char** out = (char**)malloc((size_t)slots * sizeof(char*));
    size_t pos = 0;
    while (pos < length) {
        size_t hashAt = pos;
        while (hashAt < length && line[hashAt] != '#') hashAt++;
        long payloadLength = strtol(line + pos, NULL, 10);
        if (count == slots) {
            slots *= 2;
            out = (char**)realloc(out, (size_t)slots * sizeof(char*));
        }
        char* value = (char*)malloc((size_t)payloadLength + 1);
        memcpy(value, line + hashAt + 1, (size_t)payloadLength);
        value[payloadLength] = '\\0';
        out[count++] = value;
        pos = hashAt + 1 + (size_t)payloadLength;
    }

    printf("%d\\n", count);
    for (int i = 0; i < count; i++) {
        printf("%s\\n", out[i]);
        free(out[i]);
    }
    free(out);
    free(line);
    return 0;
}
''',
)
