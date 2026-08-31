"""Known-correct solutions per (problem, language), used only for verification.

These prove the curriculum foundation works end to end: `scripts/verify_languages.py`
runs them through the real judge against the generated case bank and every case
must pass. They live under ``scripts/`` and are never imported by the app, so
there is no path by which they could be served to a client.

Each solution is the generated starter with its TODO body filled in, which also
keeps the generated I/O plumbing under test.
"""

from __future__ import annotations

SOLUTIONS: dict[str, dict[str, str]] = {}


# --------------------------------------------------------------------------- #
#  max-subarray-sum                                                           #
# --------------------------------------------------------------------------- #

SOLUTIONS["max-subarray-sum"] = {
    "java": """
import java.io.IOException;
import java.util.*;

public class Main {

    static long maxSubarraySum(long[] arr) {
        long best = arr[0];
        long cur = arr[0];
        for (int i = 1; i < arr.length; i++) {
            cur = Math.max(arr[i], cur + arr[i]);
            best = Math.max(best, cur);
        }
        return best;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] arr = new long[n];
        for (int i = 0; i < n; i++) arr[i] = in.nextLong();
        System.out.println(maxSubarraySum(arr));
    }

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
}
""".lstrip(),
    "c": """
#include <stdio.h>
#include <stdlib.h>

long long max_subarray_sum(const long long* arr, int n) {
    long long best = arr[0];
    long long cur = arr[0];
    for (int i = 1; i < n; i++) {
        long long v = arr[i];
        cur = (cur + v > v) ? cur + v : v;
        if (cur > best) best = cur;
    }
    return best;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long long* arr = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &arr[i]) != 1) break;
    }
    printf("%lld\\n", max_subarray_sum(arr, n));
    free(arr);
    return 0;
}
""".lstrip(),
}


# --------------------------------------------------------------------------- #
#  longest-unique-substring                                                   #
# --------------------------------------------------------------------------- #

SOLUTIONS["longest-unique-substring"] = {
    "java": """
import java.io.IOException;
import java.util.*;

public class Main {

    static int longestUnique(String s) {
        int[] last = new int[65536];
        Arrays.fill(last, -1);
        int best = 0;
        int start = 0;
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (last[ch] >= start) start = last[ch] + 1;
            last[ch] = i;
            best = Math.max(best, i - start + 1);
        }
        return best;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        String s = in.nextLine();
        System.out.println(longestUnique(s));
    }

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
}
""".lstrip(),
    "c": """
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int longest_unique(const char* s) {
    int last[256];
    for (int i = 0; i < 256; i++) last[i] = -1;
    int best = 0;
    int start = 0;
    int n = (int)strlen(s);
    for (int i = 0; i < n; i++) {
        unsigned char ch = (unsigned char)s[i];
        if (last[ch] >= start) start = last[ch] + 1;
        last[ch] = i;
        if (i - start + 1 > best) best = i - start + 1;
    }
    return best;
}

int main(void) {
    char* s = NULL;
    size_t cap = 0;
    ssize_t len = getline(&s, &cap, stdin);
    if (len < 0) {
        s = (char*)calloc(1, 1);
        len = 0;
    }
    while (len > 0 && (s[len - 1] == '\\n' || s[len - 1] == '\\r')) {
        s[--len] = '\\0';
    }
    printf("%d\\n", longest_unique(s));
    free(s);
    return 0;
}
""".lstrip(),
}


# --------------------------------------------------------------------------- #
#  min-platforms                                                              #
# --------------------------------------------------------------------------- #

SOLUTIONS["min-platforms"] = {
    "java": """
import java.io.IOException;
import java.util.*;

public class Main {

    static int minPlatforms(long[] arrivals, long[] departures) {
        Arrays.sort(arrivals);
        Arrays.sort(departures);
        int n = arrivals.length;
        int i = 0;
        int j = 0;
        int cur = 0;
        int best = 0;
        while (i < n) {
            if (arrivals[i] <= departures[j]) {
                cur++;
                best = Math.max(best, cur);
                i++;
            } else {
                cur--;
                j++;
            }
        }
        return best;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] arrivals = new long[n];
        for (int i = 0; i < n; i++) arrivals[i] = in.nextLong();
        long[] departures = new long[n];
        for (int i = 0; i < n; i++) departures[i] = in.nextLong();
        System.out.println(minPlatforms(arrivals, departures));
    }

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
}
""".lstrip(),
    "c": """
#include <stdio.h>
#include <stdlib.h>

static int cmp_ll(const void* a, const void* b) {
    long long x = *(const long long*)a;
    long long y = *(const long long*)b;
    return (x > y) - (x < y);
}

int min_platforms(const long long* arrivals, const long long* departures, int n) {
    long long* a = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    long long* d = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int k = 0; k < n; k++) { a[k] = arrivals[k]; d[k] = departures[k]; }
    qsort(a, (size_t)n, sizeof(long long), cmp_ll);
    qsort(d, (size_t)n, sizeof(long long), cmp_ll);
    int i = 0, j = 0, cur = 0, best = 0;
    while (i < n) {
        if (a[i] <= d[j]) {
            cur++;
            if (cur > best) best = cur;
            i++;
        } else {
            cur--;
            j++;
        }
    }
    free(a);
    free(d);
    return best;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long long* arrivals = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &arrivals[i]) != 1) break;
    }
    long long* departures = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &departures[i]) != 1) break;
    }
    printf("%d\\n", min_platforms(arrivals, departures, n));
    free(arrivals);
    free(departures);
    return 0;
}
""".lstrip(),
}


# --------------------------------------------------------------------------- #
#  pairs-with-difference                                                      #
# --------------------------------------------------------------------------- #

SOLUTIONS["pairs-with-difference"] = {
    "java": """
import java.io.IOException;
import java.util.*;

public class Main {

    static long countPairs(long[] arr, long d) {
        HashMap<Long, Integer> counts = new HashMap<>();
        for (long v : arr) counts.merge(v, 1, Integer::sum);
        long total = 0;
        if (d == 0) {
            for (int c : counts.values()) if (c >= 2) total++;
            return total;
        }
        for (long v : counts.keySet()) if (counts.containsKey(v + d)) total++;
        return total;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long d = in.nextLong();
        long[] arr = new long[n];
        for (int i = 0; i < n; i++) arr[i] = in.nextLong();
        System.out.println(countPairs(arr, d));
    }

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
}
""".lstrip(),
    "c": """
#include <stdio.h>
#include <stdlib.h>

static int cmp_ll(const void* a, const void* b) {
    long long x = *(const long long*)a;
    long long y = *(const long long*)b;
    return (x > y) - (x < y);
}

static int contains(const long long* sorted, int m, long long target) {
    int lo = 0, hi = m - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (sorted[mid] == target) return 1;
        if (sorted[mid] < target) lo = mid + 1; else hi = mid - 1;
    }
    return 0;
}

long long count_pairs(const long long* arr, long long d, int n) {
    long long* v = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) v[i] = arr[i];
    qsort(v, (size_t)n, sizeof(long long), cmp_ll);

    long long total = 0;
    if (d == 0) {
        int i = 0;
        while (i < n) {
            int j = i;
            while (j < n && v[j] == v[i]) j++;
            if (j - i >= 2) total++;
            i = j;
        }
        free(v);
        return total;
    }

    /* Deduplicate in place, then binary-search for value + d. */
    int m = 0;
    for (int i = 0; i < n; i++) {
        if (m == 0 || v[m - 1] != v[i]) v[m++] = v[i];
    }
    for (int i = 0; i < m; i++) {
        if (contains(v, m, v[i] + d)) total++;
    }
    free(v);
    return total;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long long d = 0;
    if (scanf("%lld", &d) != 1) return 0;
    long long* arr = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &arr[i]) != 1) break;
    }
    printf("%lld\\n", count_pairs(arr, d, n));
    free(arr);
    return 0;
}
""".lstrip(),
}


# --------------------------------------------------------------------------- #
#  Python / JavaScript / C++                                                  #
# --------------------------------------------------------------------------- #
# The pre-existing three languages are covered too: their starters are now
# generated as well, so the same proof has to hold for them.

SOLUTIONS["max-subarray-sum"]["python"] = '''
import sys


def max_subarray_sum(arr):
    best = cur = arr[0]
    for value in arr[1:]:
        cur = max(value, cur + value)
        best = max(best, cur)
    return best


def main():
    data = sys.stdin.read().split()
    pos = 0
    n = int(data[pos])
    pos += 1
    arr = [int(x) for x in data[pos:pos + n]]
    pos += n
    print(max_subarray_sum(arr))


if __name__ == "__main__":
    main()
'''.lstrip()

SOLUTIONS["max-subarray-sum"]["javascript"] = '''
function maxSubarraySum(arr) {
  let best = arr[0];
  let cur = arr[0];
  for (let i = 1; i < arr.length; i++) {
    cur = Math.max(arr[i], cur + arr[i]);
    best = Math.max(best, cur);
  }
  return best;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos];
pos += 1;
const arr = data.slice(pos, pos + n);
pos += n;
console.log(maxSubarraySum(arr));
'''.lstrip()

SOLUTIONS["max-subarray-sum"]["cpp"] = '''
#include <algorithm>
#include <iostream>
#include <vector>

long long maxSubarraySum(const std::vector<long long>& arr) {
    long long best = arr[0];
    long long cur = arr[0];
    for (size_t i = 1; i < arr.size(); i++) {
        cur = std::max(arr[i], cur + arr[i]);
        best = std::max(best, cur);
    }
    return best;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<long long> arr(n);
    for (int i = 0; i < n; i++) std::cin >> arr[i];
    std::cout << maxSubarraySum(arr) << "\\n";
    return 0;
}
'''.lstrip()

SOLUTIONS["longest-unique-substring"]["python"] = '''
import sys


def longest_unique(s):
    last = {}
    best = 0
    start = 0
    for index, ch in enumerate(s):
        if ch in last and last[ch] >= start:
            start = last[ch] + 1
        last[ch] = index
        best = max(best, index - start + 1)
    return best


def main():
    s = sys.stdin.readline().rstrip('\\n')
    print(longest_unique(s))


if __name__ == "__main__":
    main()
'''.lstrip()

SOLUTIONS["longest-unique-substring"]["javascript"] = '''
function longestUnique(s) {
  const last = new Map();
  let best = 0;
  let start = 0;
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (last.has(ch) && last.get(ch) >= start) start = last.get(ch) + 1;
    last.set(ch, i);
    best = Math.max(best, i - start + 1);
  }
  return best;
}

const input = require("fs").readFileSync(0, "utf8");
const s = input.split("\\n")[0] ?? "";
console.log(longestUnique(s));
'''.lstrip()

SOLUTIONS["longest-unique-substring"]["cpp"] = '''
#include <algorithm>
#include <iostream>
#include <string>
#include <unordered_map>

int longestUnique(const std::string& s) {
    std::unordered_map<char, int> last;
    int best = 0;
    int start = 0;
    for (int i = 0; i < static_cast<int>(s.size()); i++) {
        auto it = last.find(s[i]);
        if (it != last.end() && it->second >= start) start = it->second + 1;
        last[s[i]] = i;
        best = std::max(best, i - start + 1);
    }
    return best;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    std::string s;
    std::getline(std::cin, s);
    std::cout << longestUnique(s) << "\\n";
    return 0;
}
'''.lstrip()

SOLUTIONS["min-platforms"]["python"] = '''
import sys


def min_platforms(arrivals, departures):
    arrivals = sorted(arrivals)
    departures = sorted(departures)
    n = len(arrivals)
    i = j = 0
    current = best = 0
    while i < n:
        if arrivals[i] <= departures[j]:
            current += 1
            best = max(best, current)
            i += 1
        else:
            current -= 1
            j += 1
    return best


def main():
    data = sys.stdin.read().split()
    pos = 0
    n = int(data[pos])
    pos += 1
    arrivals = [int(x) for x in data[pos:pos + n]]
    pos += n
    departures = [int(x) for x in data[pos:pos + n]]
    pos += n
    print(min_platforms(arrivals, departures))


if __name__ == "__main__":
    main()
'''.lstrip()

SOLUTIONS["min-platforms"]["javascript"] = '''
function minPlatforms(arrivals, departures) {
  const a = [...arrivals].sort((x, y) => x - y);
  const d = [...departures].sort((x, y) => x - y);
  let i = 0, j = 0, cur = 0, best = 0;
  while (i < a.length) {
    if (a[i] <= d[j]) { cur++; best = Math.max(best, cur); i++; } else { cur--; j++; }
  }
  return best;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos];
pos += 1;
const arrivals = data.slice(pos, pos + n);
pos += n;
const departures = data.slice(pos, pos + n);
pos += n;
console.log(minPlatforms(arrivals, departures));
'''.lstrip()

SOLUTIONS["min-platforms"]["cpp"] = '''
#include <algorithm>
#include <iostream>
#include <vector>

int minPlatforms(const std::vector<long long>& arrivals, const std::vector<long long>& departures) {
    std::vector<long long> a = arrivals;
    std::vector<long long> d = departures;
    std::sort(a.begin(), a.end());
    std::sort(d.begin(), d.end());
    int n = static_cast<int>(a.size());
    int i = 0, j = 0, cur = 0, best = 0;
    while (i < n) {
        if (a[i] <= d[j]) { cur++; best = std::max(best, cur); i++; } else { cur--; j++; }
    }
    return best;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<long long> arrivals(n);
    for (int i = 0; i < n; i++) std::cin >> arrivals[i];
    std::vector<long long> departures(n);
    for (int i = 0; i < n; i++) std::cin >> departures[i];
    std::cout << minPlatforms(arrivals, departures) << "\\n";
    return 0;
}
'''.lstrip()

SOLUTIONS["pairs-with-difference"]["python"] = '''
import sys
from collections import Counter


def count_pairs(arr, d):
    counts = Counter(arr)
    if d == 0:
        return sum(1 for value in counts.values() if value >= 2)
    return sum(1 for value in counts if value + d in counts)


def main():
    data = sys.stdin.read().split()
    pos = 0
    n = int(data[pos])
    pos += 1
    d = int(data[pos])
    pos += 1
    arr = [int(x) for x in data[pos:pos + n]]
    pos += n
    print(count_pairs(arr, d))


if __name__ == "__main__":
    main()
'''.lstrip()

SOLUTIONS["pairs-with-difference"]["javascript"] = '''
function countPairs(arr, d) {
  const counts = new Map();
  for (const v of arr) counts.set(v, (counts.get(v) ?? 0) + 1);
  let total = 0;
  if (d === 0) {
    for (const c of counts.values()) if (c >= 2) total++;
    return total;
  }
  for (const v of counts.keys()) if (counts.has(v + d)) total++;
  return total;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos];
pos += 1;
const d = data[pos];
pos += 1;
const arr = data.slice(pos, pos + n);
pos += n;
console.log(countPairs(arr, d));
'''.lstrip()

SOLUTIONS["pairs-with-difference"]["cpp"] = '''
#include <iostream>
#include <unordered_map>
#include <vector>

long long countPairs(const std::vector<long long>& arr, long long d) {
    std::unordered_map<long long, int> counts;
    for (long long v : arr) counts[v]++;
    long long total = 0;
    if (d == 0) {
        for (const auto& kv : counts) if (kv.second >= 2) total++;
        return total;
    }
    for (const auto& kv : counts) if (counts.count(kv.first + d)) total++;
    return total;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    long long d;
    if (!(std::cin >> d)) return 0;
    std::vector<long long> arr(n);
    for (int i = 0; i < n; i++) std::cin >> arr[i];
    std::cout << countPairs(arr, d) << "\\n";
    return 0;
}
'''.lstrip()
