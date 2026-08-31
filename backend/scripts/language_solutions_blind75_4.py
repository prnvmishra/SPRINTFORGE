"""Known-correct solutions for Blind 75 batch 4, used only for verification.

Same role as :mod:`scripts.language_solutions`: ``scripts/verify_blind75_4.py``
runs each of these through the real judge against the derived case bank and
every case must pass. Nothing here is imported by the application.
"""

from __future__ import annotations

SOLUTIONS: dict[str, dict[str, str]] = {}


# --------------------------------------------------------------------------- #
#  b75-climbing-stairs                                                        #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-climbing-stairs"] = {
    "python": '''
import sys


def climbing_stairs(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    print(climbing_stairs(n))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function climbingStairs(n) {
  let a = 1n;
  let b = 1n;
  for (let i = 0; i < n; i++) {
    const next = a + b;
    a = b;
    b = next;
  }
  return a;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
const n = data[0];
console.log(climbingStairs(n).toString());
'''.lstrip(),
    "cpp": '''
#include <iostream>

long long climbingStairs(int n) {
    long long a = 1, b = 1;
    for (int i = 0; i < n; i++) {
        long long next = a + b;
        a = b;
        b = next;
    }
    return a;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::cout << climbingStairs(n) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static long climbingStairs(int n) {
        long a = 1, b = 1;
        for (int i = 0; i < n; i++) {
            long next = a + b;
            a = b;
            b = next;
        }
        return a;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        System.out.println(climbingStairs(n));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>

long long climbing_stairs(int n) {
    long long a = 1, b = 1;
    for (int i = 0; i < n; i++) {
        long long next = a + b;
        a = b;
        b = next;
    }
    return a;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    printf("%lld\\n", climbing_stairs(n));
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-coin-change                                                            #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-coin-change"] = {
    "python": '''
import sys


def coin_change(coins, amount):
    inf = amount + 1
    dp = [0] + [inf] * amount
    for value in range(1, amount + 1):
        best = inf
        for coin in coins:
            if coin <= value and dp[value - coin] + 1 < best:
                best = dp[value - coin] + 1
        dp[value] = best
    return -1 if dp[amount] >= inf else dp[amount]


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    amount = int(data[1])
    coins = [int(x) for x in data[2:2 + n]]
    print(coin_change(coins, amount))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function coinChange(coins, amount) {
  const inf = amount + 1;
  const dp = new Int32Array(amount + 1).fill(inf);
  dp[0] = 0;
  for (let value = 1; value <= amount; value++) {
    let best = inf;
    for (const coin of coins) {
      if (coin <= value && dp[value - coin] + 1 < best) best = dp[value - coin] + 1;
    }
    dp[value] = best;
  }
  return dp[amount] >= inf ? -1 : dp[amount];
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos];
pos += 1;
const amount = data[pos];
pos += 1;
const coins = data.slice(pos, pos + n);
console.log(coinChange(coins, amount));
'''.lstrip(),
    "cpp": '''
#include <iostream>
#include <vector>

long long coinChange(const std::vector<long long>& coins, int amount) {
    int inf = amount + 1;
    std::vector<int> dp(amount + 1, inf);
    dp[0] = 0;
    for (int value = 1; value <= amount; value++) {
        int best = inf;
        for (long long coin : coins) {
            if (coin <= value && dp[value - (int)coin] + 1 < best) {
                best = dp[value - (int)coin] + 1;
            }
        }
        dp[value] = best;
    }
    return dp[amount] >= inf ? -1 : dp[amount];
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    int amount;
    if (!(std::cin >> amount)) return 0;
    std::vector<long long> coins(n);
    for (int i = 0; i < n; i++) std::cin >> coins[i];
    std::cout << coinChange(coins, amount) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;
import java.util.*;

public class Main {

    static long coinChange(long[] coins, int amount) {
        int inf = amount + 1;
        int[] dp = new int[amount + 1];
        Arrays.fill(dp, inf);
        dp[0] = 0;
        for (int value = 1; value <= amount; value++) {
            int best = inf;
            for (long coin : coins) {
                if (coin <= value && dp[value - (int) coin] + 1 < best) {
                    best = dp[value - (int) coin] + 1;
                }
            }
            dp[value] = best;
        }
        return dp[amount] >= inf ? -1 : dp[amount];
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        int amount = (int) in.nextLong();
        long[] coins = new long[n];
        for (int i = 0; i < n; i++) coins[i] = in.nextLong();
        System.out.println(coinChange(coins, amount));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

long long coin_change(const long long* coins, int amount, int n) {
    int inf = amount + 1;
    int* dp = (int*)malloc((size_t)(amount + 1) * sizeof(int));
    dp[0] = 0;
    for (int v = 1; v <= amount; v++) dp[v] = inf;
    for (int v = 1; v <= amount; v++) {
        int best = inf;
        for (int i = 0; i < n; i++) {
            long long coin = coins[i];
            if (coin <= v && dp[v - (int)coin] + 1 < best) best = dp[v - (int)coin] + 1;
        }
        dp[v] = best;
    }
    long long answer = dp[amount] >= inf ? -1 : dp[amount];
    free(dp);
    return answer;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    int amount = 0;
    if (scanf("%d", &amount) != 1) return 0;
    long long* coins = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &coins[i]) != 1) break;
    }
    printf("%lld\\n", coin_change(coins, amount, n));
    free(coins);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-longest-increasing-subsequence                                         #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-longest-increasing-subsequence"] = {
    "python": '''
import sys
from bisect import bisect_left


def longest_increasing_subsequence(arr):
    tails = []
    for value in arr:
        pos = bisect_left(tails, value)
        if pos == len(tails):
            tails.append(value)
        else:
            tails[pos] = value
    return len(tails)


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    arr = [int(x) for x in data[1:1 + n]]
    print(longest_increasing_subsequence(arr))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function longestIncreasingSubsequence(arr) {
  const tails = new Float64Array(arr.length);
  let size = 0;
  for (const value of arr) {
    let lo = 0;
    let hi = size;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (tails[mid] < value) lo = mid + 1;
      else hi = mid;
    }
    tails[lo] = value;
    if (lo === size) size++;
  }
  return size;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos];
pos += 1;
const arr = data.slice(pos, pos + n);
console.log(longestIncreasingSubsequence(arr));
'''.lstrip(),
    "cpp": '''
#include <algorithm>
#include <iostream>
#include <vector>

int longestIncreasingSubsequence(const std::vector<long long>& arr) {
    std::vector<long long> tails;
    for (long long value : arr) {
        auto it = std::lower_bound(tails.begin(), tails.end(), value);
        if (it == tails.end()) tails.push_back(value);
        else *it = value;
    }
    return static_cast<int>(tails.size());
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<long long> arr(n);
    for (int i = 0; i < n; i++) std::cin >> arr[i];
    std::cout << longestIncreasingSubsequence(arr) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static int longestIncreasingSubsequence(long[] arr) {
        long[] tails = new long[arr.length];
        int size = 0;
        for (long value : arr) {
            int lo = 0, hi = size;
            while (lo < hi) {
                int mid = (lo + hi) >>> 1;
                if (tails[mid] < value) lo = mid + 1;
                else hi = mid;
            }
            tails[lo] = value;
            if (lo == size) size++;
        }
        return size;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] arr = new long[n];
        for (int i = 0; i < n; i++) arr[i] = in.nextLong();
        System.out.println(longestIncreasingSubsequence(arr));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

int longest_increasing_subsequence(const long long* arr, int n) {
    long long* tails = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    int size = 0;
    for (int i = 0; i < n; i++) {
        long long value = arr[i];
        int lo = 0, hi = size;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (tails[mid] < value) lo = mid + 1;
            else hi = mid;
        }
        tails[lo] = value;
        if (lo == size) size++;
    }
    free(tails);
    return size;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long long* arr = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &arr[i]) != 1) break;
    }
    printf("%d\\n", longest_increasing_subsequence(arr, n));
    free(arr);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-longest-common-subsequence                                             #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-longest-common-subsequence"] = {
    "python": '''
import sys


def longest_common_subsequence(line):
    parts = line.split()
    s = parts[0] if len(parts) > 0 else ""
    t = parts[1] if len(parts) > 1 else ""
    prev = [0] * (len(t) + 1)
    for a in s:
        cur = [0] * (len(t) + 1)
        for j, b in enumerate(t, start=1):
            cur[j] = prev[j - 1] + 1 if a == b else max(prev[j], cur[j - 1])
        prev = cur
    return prev[len(t)]


def main():
    line = sys.stdin.readline().rstrip('\\n')
    print(longest_common_subsequence(line))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function longestCommonSubsequence(line) {
  const parts = line.split(/\\s+/).filter(Boolean);
  const s = parts[0] ?? "";
  const t = parts[1] ?? "";
  let prev = new Int32Array(t.length + 1);
  let cur = new Int32Array(t.length + 1);
  for (let i = 0; i < s.length; i++) {
    cur.fill(0);
    for (let j = 1; j <= t.length; j++) {
      if (s[i] === t[j - 1]) cur[j] = prev[j - 1] + 1;
      else cur[j] = Math.max(prev[j], cur[j - 1]);
    }
    const swap = prev;
    prev = cur;
    cur = swap;
  }
  return prev[t.length];
}

const input = require("fs").readFileSync(0, "utf8");
const line = input.split("\\n")[0] ?? "";
console.log(longestCommonSubsequence(line));
'''.lstrip(),
    "cpp": '''
#include <algorithm>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

int longestCommonSubsequence(const std::string& line) {
    std::istringstream stream(line);
    std::string s, t;
    stream >> s;
    stream >> t;
    std::vector<int> prev(t.size() + 1, 0), cur(t.size() + 1, 0);
    for (size_t i = 0; i < s.size(); i++) {
        std::fill(cur.begin(), cur.end(), 0);
        for (size_t j = 1; j <= t.size(); j++) {
            if (s[i] == t[j - 1]) cur[j] = prev[j - 1] + 1;
            else cur[j] = std::max(prev[j], cur[j - 1]);
        }
        std::swap(prev, cur);
    }
    return prev[t.size()];
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    std::string line;
    std::getline(std::cin, line);
    std::cout << longestCommonSubsequence(line) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static int longestCommonSubsequence(String line) {
        String[] parts = line.trim().isEmpty() ? new String[0] : line.trim().split("\\\\s+");
        String s = parts.length > 0 ? parts[0] : "";
        String t = parts.length > 1 ? parts[1] : "";
        int[] prev = new int[t.length() + 1];
        int[] cur = new int[t.length() + 1];
        for (int i = 0; i < s.length(); i++) {
            java.util.Arrays.fill(cur, 0);
            for (int j = 1; j <= t.length(); j++) {
                if (s.charAt(i) == t.charAt(j - 1)) cur[j] = prev[j - 1] + 1;
                else cur[j] = Math.max(prev[j], cur[j - 1]);
            }
            int[] swap = prev;
            prev = cur;
            cur = swap;
        }
        return prev[t.length()];
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        String line = in.nextLine();
        System.out.println(longestCommonSubsequence(line));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int longest_common_subsequence(const char* line) {
    char* copy = strdup(line);
    char* s = strtok(copy, " \\t");
    char* t = s ? strtok(NULL, " \\t") : NULL;
    int ls = s ? (int)strlen(s) : 0;
    int lt = t ? (int)strlen(t) : 0;
    int* prev = (int*)calloc((size_t)lt + 1, sizeof(int));
    int* cur = (int*)calloc((size_t)lt + 1, sizeof(int));
    for (int i = 0; i < ls; i++) {
        memset(cur, 0, ((size_t)lt + 1) * sizeof(int));
        for (int j = 1; j <= lt; j++) {
            if (s[i] == t[j - 1]) {
                cur[j] = prev[j - 1] + 1;
            } else {
                cur[j] = prev[j] > cur[j - 1] ? prev[j] : cur[j - 1];
            }
        }
        int* swap = prev;
        prev = cur;
        cur = swap;
    }
    int answer = prev[lt];
    free(prev);
    free(cur);
    free(copy);
    return answer;
}

int main(void) {
    char* line = NULL;
    size_t cap = 0;
    ssize_t len = getline(&line, &cap, stdin);
    if (len < 0) {
        line = (char*)calloc(1, 1);
        len = 0;
    }
    while (len > 0 && (line[len - 1] == '\\n' || line[len - 1] == '\\r')) {
        line[--len] = '\\0';
    }
    printf("%d\\n", longest_common_subsequence(line));
    free(line);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-word-break                                                             #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-word-break"] = {
    "python": '''
import sys


def word_break(line):
    parts = line.split()
    if not parts:
        return 1
    s = parts[0]
    words = set(parts[1:])
    lengths = sorted({len(w) for w in words})
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        for length in lengths:
            if length > i:
                break
            if dp[i - length] and s[i - length:i] in words:
                dp[i] = True
                break
    return 1 if dp[n] else 0


def main():
    line = sys.stdin.readline().rstrip('\\n')
    print(word_break(line))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function wordBreak(line) {
  const parts = line.split(/\\s+/).filter(Boolean);
  if (parts.length === 0) return 1;
  const s = parts[0];
  const words = new Set(parts.slice(1));
  const lengths = [...new Set(parts.slice(1).map((w) => w.length))].sort((a, b) => a - b);
  const dp = new Uint8Array(s.length + 1);
  dp[0] = 1;
  for (let i = 1; i <= s.length; i++) {
    for (const length of lengths) {
      if (length > i) break;
      if (dp[i - length] && words.has(s.slice(i - length, i))) {
        dp[i] = 1;
        break;
      }
    }
  }
  return dp[s.length] ? 1 : 0;
}

const input = require("fs").readFileSync(0, "utf8");
const line = input.split("\\n")[0] ?? "";
console.log(wordBreak(line));
'''.lstrip(),
    "cpp": '''
#include <algorithm>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>

int wordBreak(const std::string& line) {
    std::istringstream stream(line);
    std::vector<std::string> parts;
    std::string token;
    while (stream >> token) parts.push_back(token);
    if (parts.empty()) return 1;

    std::string s = parts[0];
    std::unordered_set<std::string> words(parts.begin() + 1, parts.end());
    std::vector<int> lengths;
    for (size_t i = 1; i < parts.size(); i++) lengths.push_back((int)parts[i].size());
    std::sort(lengths.begin(), lengths.end());
    lengths.erase(std::unique(lengths.begin(), lengths.end()), lengths.end());

    int n = (int)s.size();
    std::vector<char> dp(n + 1, 0);
    dp[0] = 1;
    for (int i = 1; i <= n; i++) {
        for (int length : lengths) {
            if (length > i) break;
            if (dp[i - length] && words.count(s.substr(i - length, length))) {
                dp[i] = 1;
                break;
            }
        }
    }
    return dp[n] ? 1 : 0;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    std::string line;
    std::getline(std::cin, line);
    std::cout << wordBreak(line) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;
import java.util.*;

public class Main {

    static int wordBreak(String line) {
        String trimmed = line.trim();
        if (trimmed.isEmpty()) return 1;
        String[] parts = trimmed.split("\\\\s+");
        String s = parts[0];
        Set<String> words = new HashSet<>();
        TreeSet<Integer> lengths = new TreeSet<>();
        for (int i = 1; i < parts.length; i++) {
            words.add(parts[i]);
            lengths.add(parts[i].length());
        }
        int n = s.length();
        boolean[] dp = new boolean[n + 1];
        dp[0] = true;
        for (int i = 1; i <= n; i++) {
            for (int length : lengths) {
                if (length > i) break;
                if (dp[i - length] && words.contains(s.substring(i - length, i))) {
                    dp[i] = true;
                    break;
                }
            }
        }
        return dp[n] ? 1 : 0;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        String line = in.nextLine();
        System.out.println(wordBreak(line));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_WORDS 1024

int word_break(const char* line) {
    char* copy = strdup(line);
    char* words[MAX_WORDS];
    int word_count = 0;
    char* token = strtok(copy, " \\t");
    char* s = token;
    if (s == NULL) {
        free(copy);
        return 1;
    }
    token = strtok(NULL, " \\t");
    while (token != NULL && word_count < MAX_WORDS) {
        words[word_count++] = token;
        token = strtok(NULL, " \\t");
    }

    int n = (int)strlen(s);
    char* dp = (char*)calloc((size_t)n + 1, 1);
    dp[0] = 1;
    for (int i = 1; i <= n; i++) {
        for (int w = 0; w < word_count && !dp[i]; w++) {
            int length = (int)strlen(words[w]);
            if (length <= i && dp[i - length] && strncmp(s + i - length, words[w], (size_t)length) == 0) {
                dp[i] = 1;
            }
        }
    }
    int answer = dp[n] ? 1 : 0;
    free(dp);
    free(copy);
    return answer;
}

int main(void) {
    char* line = NULL;
    size_t cap = 0;
    ssize_t len = getline(&line, &cap, stdin);
    if (len < 0) {
        line = (char*)calloc(1, 1);
        len = 0;
    }
    while (len > 0 && (line[len - 1] == '\\n' || line[len - 1] == '\\r')) {
        line[--len] = '\\0';
    }
    printf("%d\\n", word_break(line));
    free(line);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-combination-sum-iv                                                     #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-combination-sum-iv"] = {
    "python": '''
import sys


def combination_sum_iv(nums, target):
    dp = [0] * (target + 1)
    dp[0] = 1
    for total in range(1, target + 1):
        acc = 0
        for value in nums:
            if value <= total:
                acc += dp[total - value]
        dp[total] = acc
    return dp[target]


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    target = int(data[1])
    nums = [int(x) for x in data[2:2 + n]]
    print(combination_sum_iv(nums, target))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function combinationSumIv(nums, target) {
  const dp = new Array(target + 1).fill(0n);
  dp[0] = 1n;
  for (let total = 1; total <= target; total++) {
    let acc = 0n;
    for (const value of nums) {
      if (value <= total) acc += dp[total - value];
    }
    dp[total] = acc;
  }
  return dp[target];
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos];
pos += 1;
const target = data[pos];
pos += 1;
const nums = data.slice(pos, pos + n);
console.log(combinationSumIv(nums, target).toString());
'''.lstrip(),
    "cpp": '''
#include <iostream>
#include <vector>

long long combinationSumIv(const std::vector<long long>& nums, int target) {
    std::vector<long long> dp(target + 1, 0);
    dp[0] = 1;
    for (int total = 1; total <= target; total++) {
        long long acc = 0;
        for (long long value : nums) {
            if (value <= total) acc += dp[total - (int)value];
        }
        dp[total] = acc;
    }
    return dp[target];
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    int target;
    if (!(std::cin >> target)) return 0;
    std::vector<long long> nums(n);
    for (int i = 0; i < n; i++) std::cin >> nums[i];
    std::cout << combinationSumIv(nums, target) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static long combinationSumIv(long[] nums, int target) {
        long[] dp = new long[target + 1];
        dp[0] = 1;
        for (int total = 1; total <= target; total++) {
            long acc = 0;
            for (long value : nums) {
                if (value <= total) acc += dp[total - (int) value];
            }
            dp[total] = acc;
        }
        return dp[target];
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        int target = (int) in.nextLong();
        long[] nums = new long[n];
        for (int i = 0; i < n; i++) nums[i] = in.nextLong();
        System.out.println(combinationSumIv(nums, target));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

long long combination_sum_iv(const long long* nums, int target, int n) {
    long long* dp = (long long*)calloc((size_t)target + 1, sizeof(long long));
    dp[0] = 1;
    for (int total = 1; total <= target; total++) {
        long long acc = 0;
        for (int i = 0; i < n; i++) {
            if (nums[i] <= total) acc += dp[total - (int)nums[i]];
        }
        dp[total] = acc;
    }
    long long answer = dp[target];
    free(dp);
    return answer;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    int target = 0;
    if (scanf("%d", &target) != 1) return 0;
    long long* nums = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &nums[i]) != 1) break;
    }
    printf("%lld\\n", combination_sum_iv(nums, target, n));
    free(nums);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-house-robber                                                           #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-house-robber"] = {
    "python": '''
import sys


def house_robber(nums):
    take = 0
    skip = 0
    for value in nums:
        take, skip = skip + value, max(skip, take)
    return max(take, skip)


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    nums = [int(x) for x in data[1:1 + n]]
    print(house_robber(nums))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function houseRobber(nums) {
  let take = 0;
  let skip = 0;
  for (const value of nums) {
    const nextTake = skip + value;
    skip = Math.max(skip, take);
    take = nextTake;
  }
  return Math.max(take, skip);
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos];
pos += 1;
const nums = data.slice(pos, pos + n);
console.log(houseRobber(nums));
'''.lstrip(),
    "cpp": '''
#include <algorithm>
#include <iostream>
#include <vector>

long long houseRobber(const std::vector<long long>& nums) {
    long long take = 0, skip = 0;
    for (long long value : nums) {
        long long nextTake = skip + value;
        skip = std::max(skip, take);
        take = nextTake;
    }
    return std::max(take, skip);
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<long long> nums(n);
    for (int i = 0; i < n; i++) std::cin >> nums[i];
    std::cout << houseRobber(nums) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static long houseRobber(long[] nums) {
        long take = 0, skip = 0;
        for (long value : nums) {
            long nextTake = skip + value;
            skip = Math.max(skip, take);
            take = nextTake;
        }
        return Math.max(take, skip);
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] nums = new long[n];
        for (int i = 0; i < n; i++) nums[i] = in.nextLong();
        System.out.println(houseRobber(nums));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

long long house_robber(const long long* nums, int n) {
    long long take = 0, skip = 0;
    for (int i = 0; i < n; i++) {
        long long next_take = skip + nums[i];
        long long next_skip = skip > take ? skip : take;
        take = next_take;
        skip = next_skip;
    }
    return take > skip ? take : skip;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long long* nums = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &nums[i]) != 1) break;
    }
    printf("%lld\\n", house_robber(nums, n));
    free(nums);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-house-robber-circular                                                  #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-house-robber-circular"] = {
    "python": '''
import sys


def house_robber_circular(nums):
    def line(values):
        take = 0
        skip = 0
        for value in values:
            take, skip = skip + value, max(skip, take)
        return max(take, skip)

    if len(nums) == 1:
        return nums[0]
    return max(line(nums[:-1]), line(nums[1:]))


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    nums = [int(x) for x in data[1:1 + n]]
    print(house_robber_circular(nums))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function houseRobberCircular(nums) {
  const line = (from, to) => {
    let take = 0;
    let skip = 0;
    for (let i = from; i < to; i++) {
      const nextTake = skip + nums[i];
      skip = Math.max(skip, take);
      take = nextTake;
    }
    return Math.max(take, skip);
  };
  if (nums.length === 1) return nums[0];
  return Math.max(line(0, nums.length - 1), line(1, nums.length));
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos];
pos += 1;
const nums = data.slice(pos, pos + n);
console.log(houseRobberCircular(nums));
'''.lstrip(),
    "cpp": '''
#include <algorithm>
#include <iostream>
#include <vector>

static long long robLine(const std::vector<long long>& nums, int from, int to) {
    long long take = 0, skip = 0;
    for (int i = from; i < to; i++) {
        long long nextTake = skip + nums[i];
        skip = std::max(skip, take);
        take = nextTake;
    }
    return std::max(take, skip);
}

long long houseRobberCircular(const std::vector<long long>& nums) {
    int n = static_cast<int>(nums.size());
    if (n == 1) return nums[0];
    return std::max(robLine(nums, 0, n - 1), robLine(nums, 1, n));
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<long long> nums(n);
    for (int i = 0; i < n; i++) std::cin >> nums[i];
    std::cout << houseRobberCircular(nums) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static long robLine(long[] nums, int from, int to) {
        long take = 0, skip = 0;
        for (int i = from; i < to; i++) {
            long nextTake = skip + nums[i];
            skip = Math.max(skip, take);
            take = nextTake;
        }
        return Math.max(take, skip);
    }

    static long houseRobberCircular(long[] nums) {
        int n = nums.length;
        if (n == 1) return nums[0];
        return Math.max(robLine(nums, 0, n - 1), robLine(nums, 1, n));
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] nums = new long[n];
        for (int i = 0; i < n; i++) nums[i] = in.nextLong();
        System.out.println(houseRobberCircular(nums));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

static long long rob_line(const long long* nums, int from, int to) {
    long long take = 0, skip = 0;
    for (int i = from; i < to; i++) {
        long long next_take = skip + nums[i];
        long long next_skip = skip > take ? skip : take;
        take = next_take;
        skip = next_skip;
    }
    return take > skip ? take : skip;
}

long long house_robber_circular(const long long* nums, int n) {
    if (n == 1) return nums[0];
    long long a = rob_line(nums, 0, n - 1);
    long long b = rob_line(nums, 1, n);
    return a > b ? a : b;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long long* nums = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &nums[i]) != 1) break;
    }
    printf("%lld\\n", house_robber_circular(nums, n));
    free(nums);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-decode-ways                                                            #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-decode-ways"] = {
    "python": '''
import sys


def decode_ways(s):
    if not s:
        return 0
    prev2 = 1
    prev1 = 1 if s[0] != '0' else 0
    for i in range(1, len(s)):
        cur = 0
        if s[i] != '0':
            cur += prev1
        two = int(s[i - 1:i + 1])
        if 10 <= two <= 26:
            cur += prev2
        prev2, prev1 = prev1, cur
    return prev1


def main():
    s = sys.stdin.readline().rstrip('\\n').strip()
    print(decode_ways(s))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function decodeWays(s) {
  if (s.length === 0) return 0n;
  let prev2 = 1n;
  let prev1 = s[0] !== "0" ? 1n : 0n;
  for (let i = 1; i < s.length; i++) {
    let cur = 0n;
    if (s[i] !== "0") cur += prev1;
    const two = Number(s.slice(i - 1, i + 1));
    if (two >= 10 && two <= 26) cur += prev2;
    prev2 = prev1;
    prev1 = cur;
  }
  return prev1;
}

const input = require("fs").readFileSync(0, "utf8");
const s = (input.split("\\n")[0] ?? "").trim();
console.log(decodeWays(s).toString());
'''.lstrip(),
    "cpp": '''
#include <iostream>
#include <string>

long long decodeWays(const std::string& s) {
    if (s.empty()) return 0;
    long long prev2 = 1;
    long long prev1 = s[0] != '0' ? 1 : 0;
    for (size_t i = 1; i < s.size(); i++) {
        long long cur = 0;
        if (s[i] != '0') cur += prev1;
        int two = (s[i - 1] - '0') * 10 + (s[i] - '0');
        if (two >= 10 && two <= 26) cur += prev2;
        prev2 = prev1;
        prev1 = cur;
    }
    return prev1;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    std::string s;
    std::getline(std::cin, s);
    while (!s.empty() && (s.back() == ' ' || s.back() == '\\r' || s.back() == '\\t')) s.pop_back();
    std::cout << decodeWays(s) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static long decodeWays(String s) {
        if (s.isEmpty()) return 0;
        long prev2 = 1;
        long prev1 = s.charAt(0) != '0' ? 1 : 0;
        for (int i = 1; i < s.length(); i++) {
            long cur = 0;
            if (s.charAt(i) != '0') cur += prev1;
            int two = (s.charAt(i - 1) - '0') * 10 + (s.charAt(i) - '0');
            if (two >= 10 && two <= 26) cur += prev2;
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        String s = in.nextLine().trim();
        System.out.println(decodeWays(s));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

long long decode_ways(const char* s) {
    int n = (int)strlen(s);
    if (n == 0) return 0;
    long long prev2 = 1;
    long long prev1 = s[0] != '0' ? 1 : 0;
    for (int i = 1; i < n; i++) {
        long long cur = 0;
        if (s[i] != '0') cur += prev1;
        int two = (s[i - 1] - '0') * 10 + (s[i] - '0');
        if (two >= 10 && two <= 26) cur += prev2;
        prev2 = prev1;
        prev1 = cur;
    }
    return prev1;
}

int main(void) {
    char* s = NULL;
    size_t cap = 0;
    ssize_t len = getline(&s, &cap, stdin);
    if (len < 0) {
        s = (char*)calloc(1, 1);
        len = 0;
    }
    while (len > 0 && (s[len - 1] == '\\n' || s[len - 1] == '\\r' || s[len - 1] == ' ')) {
        s[--len] = '\\0';
    }
    printf("%lld\\n", decode_ways(s));
    free(s);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-unique-paths                                                           #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-unique-paths"] = {
    "python": '''
import sys


def unique_paths(m, n):
    row = [1] * n
    for _ in range(1, m):
        for j in range(1, n):
            row[j] += row[j - 1]
    return row[n - 1]


def main():
    data = sys.stdin.read().split()
    m = int(data[0])
    n = int(data[1])
    print(unique_paths(m, n))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function uniquePaths(m, n) {
  const row = new Array(n).fill(1);
  for (let i = 1; i < m; i++) {
    for (let j = 1; j < n; j++) row[j] += row[j - 1];
  }
  return row[n - 1];
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
const m = data[0];
const n = data[1];
console.log(uniquePaths(m, n));
'''.lstrip(),
    "cpp": '''
#include <iostream>
#include <vector>

long long uniquePaths(int m, int n) {
    std::vector<long long> row(n, 1);
    for (int i = 1; i < m; i++) {
        for (int j = 1; j < n; j++) row[j] += row[j - 1];
    }
    return row[n - 1];
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int m;
    if (!(std::cin >> m)) return 0;
    int n;
    if (!(std::cin >> n)) return 0;
    std::cout << uniquePaths(m, n) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;
import java.util.*;

public class Main {

    static long uniquePaths(int m, int n) {
        long[] row = new long[n];
        Arrays.fill(row, 1L);
        for (int i = 1; i < m; i++) {
            for (int j = 1; j < n; j++) row[j] += row[j - 1];
        }
        return row[n - 1];
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int m = (int) in.nextLong();
        int n = (int) in.nextLong();
        System.out.println(uniquePaths(m, n));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

long long unique_paths(int m, int n) {
    long long* row = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int j = 0; j < n; j++) row[j] = 1;
    for (int i = 1; i < m; i++) {
        for (int j = 1; j < n; j++) row[j] += row[j - 1];
    }
    long long answer = row[n - 1];
    free(row);
    return answer;
}

int main(void) {
    int m = 0;
    if (scanf("%d", &m) != 1) return 0;
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    printf("%lld\\n", unique_paths(m, n));
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-jump-game                                                              #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-jump-game"] = {
    "python": '''
import sys


def jump_game(nums):
    reach = 0
    for i, value in enumerate(nums):
        if i > reach:
            return 0
        if i + value > reach:
            reach = i + value
    return 1


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    nums = [int(x) for x in data[1:1 + n]]
    print(jump_game(nums))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function jumpGame(nums) {
  let reach = 0;
  for (let i = 0; i < nums.length; i++) {
    if (i > reach) return 0;
    if (i + nums[i] > reach) reach = i + nums[i];
  }
  return 1;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos];
pos += 1;
const nums = data.slice(pos, pos + n);
console.log(jumpGame(nums));
'''.lstrip(),
    "cpp": '''
#include <iostream>
#include <vector>

int jumpGame(const std::vector<long long>& nums) {
    long long reach = 0;
    for (long long i = 0; i < static_cast<long long>(nums.size()); i++) {
        if (i > reach) return 0;
        if (i + nums[i] > reach) reach = i + nums[i];
    }
    return 1;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    std::vector<long long> nums(n);
    for (int i = 0; i < n; i++) std::cin >> nums[i];
    std::cout << jumpGame(nums) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static int jumpGame(long[] nums) {
        long reach = 0;
        for (long i = 0; i < nums.length; i++) {
            if (i > reach) return 0;
            if (i + nums[(int) i] > reach) reach = i + nums[(int) i];
        }
        return 1;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] nums = new long[n];
        for (int i = 0; i < n; i++) nums[i] = in.nextLong();
        System.out.println(jumpGame(nums));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

int jump_game(const long long* nums, int n) {
    long long reach = 0;
    for (long long i = 0; i < n; i++) {
        if (i > reach) return 0;
        if (i + nums[i] > reach) reach = i + nums[i];
    }
    return 1;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long long* nums = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &nums[i]) != 1) break;
    }
    printf("%d\\n", jump_game(nums, n));
    free(nums);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-course-schedule                                                        #
# --------------------------------------------------------------------------- #
# Kahn's algorithm everywhere: a hidden case is a 100000-long chain, which a
# recursive depth-first search cannot survive in C, C++ or Java.

SOLUTIONS["b75-course-schedule"] = {
    "python": '''
import sys


def course_schedule(n, src, dst):
    m = len(src)
    head = [-1] * (n + 1)
    nxt = [-1] * m
    to = [0] * m
    indeg = [0] * (n + 1)
    for i in range(m):
        u = src[i]
        v = dst[i]
        to[i] = v
        nxt[i] = head[u]
        head[u] = i
        indeg[v] += 1
    stack = [v for v in range(1, n + 1) if indeg[v] == 0]
    seen = 0
    while stack:
        u = stack.pop()
        seen += 1
        edge = head[u]
        while edge != -1:
            v = to[edge]
            indeg[v] -= 1
            if indeg[v] == 0:
                stack.append(v)
            edge = nxt[edge]
    return 1 if seen == n else 0


def main():
    data = sys.stdin.read().split()
    pos = 0
    n = int(data[pos]); pos += 1
    m = int(data[pos]); pos += 1
    src = [int(x) for x in data[pos:pos + m]]; pos += m
    dst = [int(x) for x in data[pos:pos + m]]; pos += m
    print(course_schedule(n, src, dst))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function courseSchedule(n, src, dst) {
  const m = src.length;
  const head = new Int32Array(n + 1).fill(-1);
  const nxt = new Int32Array(m).fill(-1);
  const to = new Int32Array(m);
  const indeg = new Int32Array(n + 1);
  for (let i = 0; i < m; i++) {
    const u = src[i];
    const v = dst[i];
    to[i] = v;
    nxt[i] = head[u];
    head[u] = i;
    indeg[v] += 1;
  }
  const stack = [];
  for (let v = 1; v <= n; v++) if (indeg[v] === 0) stack.push(v);
  let seen = 0;
  while (stack.length > 0) {
    const u = stack.pop();
    seen += 1;
    for (let edge = head[u]; edge !== -1; edge = nxt[edge]) {
      const v = to[edge];
      indeg[v] -= 1;
      if (indeg[v] === 0) stack.push(v);
    }
  }
  return seen === n ? 1 : 0;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos];
pos += 1;
const m = data[pos];
pos += 1;
const src = data.slice(pos, pos + m);
pos += m;
const dst = data.slice(pos, pos + m);
pos += m;
console.log(courseSchedule(n, src, dst));
'''.lstrip(),
    "cpp": '''
#include <iostream>
#include <vector>

int courseSchedule(int n, const std::vector<int>& src, const std::vector<int>& dst) {
    int m = static_cast<int>(src.size());
    std::vector<int> head(n + 1, -1), nxt(m, -1), to(m, 0), indeg(n + 1, 0);
    for (int i = 0; i < m; i++) {
        int u = src[i], v = dst[i];
        to[i] = v;
        nxt[i] = head[u];
        head[u] = i;
        indeg[v]++;
    }
    std::vector<int> stack;
    for (int v = 1; v <= n; v++) if (indeg[v] == 0) stack.push_back(v);
    int seen = 0;
    while (!stack.empty()) {
        int u = stack.back();
        stack.pop_back();
        seen++;
        for (int edge = head[u]; edge != -1; edge = nxt[edge]) {
            int v = to[edge];
            if (--indeg[v] == 0) stack.push_back(v);
        }
    }
    return seen == n ? 1 : 0;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    int m;
    if (!(std::cin >> m)) return 0;
    std::vector<int> src(m), dst(m);
    for (int i = 0; i < m; i++) std::cin >> src[i];
    for (int i = 0; i < m; i++) std::cin >> dst[i];
    std::cout << courseSchedule(n, src, dst) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;
import java.util.*;

public class Main {

    static int courseSchedule(int n, int[] src, int[] dst) {
        int m = src.length;
        int[] head = new int[n + 1];
        Arrays.fill(head, -1);
        int[] nxt = new int[Math.max(m, 1)];
        int[] to = new int[Math.max(m, 1)];
        int[] indeg = new int[n + 1];
        for (int i = 0; i < m; i++) {
            int u = src[i], v = dst[i];
            to[i] = v;
            nxt[i] = head[u];
            head[u] = i;
            indeg[v]++;
        }
        int[] stack = new int[n];
        int top = 0;
        for (int v = 1; v <= n; v++) if (indeg[v] == 0) stack[top++] = v;
        int seen = 0;
        while (top > 0) {
            int u = stack[--top];
            seen++;
            for (int edge = head[u]; edge != -1; edge = nxt[edge]) {
                int v = to[edge];
                if (--indeg[v] == 0) stack[top++] = v;
            }
        }
        return seen == n ? 1 : 0;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        int m = (int) in.nextLong();
        int[] src = new int[m];
        for (int i = 0; i < m; i++) src[i] = (int) in.nextLong();
        int[] dst = new int[m];
        for (int i = 0; i < m; i++) dst[i] = (int) in.nextLong();
        System.out.println(courseSchedule(n, src, dst));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

int course_schedule(int n, const int* src, const int* dst, int m) {
    int* head = (int*)malloc((size_t)(n + 1) * sizeof(int));
    int* indeg = (int*)calloc((size_t)(n + 1), sizeof(int));
    int* nxt = (int*)malloc((size_t)(m > 0 ? m : 1) * sizeof(int));
    int* to = (int*)malloc((size_t)(m > 0 ? m : 1) * sizeof(int));
    for (int v = 0; v <= n; v++) head[v] = -1;
    for (int i = 0; i < m; i++) {
        int u = src[i], v = dst[i];
        to[i] = v;
        nxt[i] = head[u];
        head[u] = i;
        indeg[v]++;
    }
    int* stack = (int*)malloc((size_t)(n > 0 ? n : 1) * sizeof(int));
    int top = 0;
    for (int v = 1; v <= n; v++) {
        if (indeg[v] == 0) stack[top++] = v;
    }
    int seen = 0;
    while (top > 0) {
        int u = stack[--top];
        seen++;
        for (int edge = head[u]; edge != -1; edge = nxt[edge]) {
            int v = to[edge];
            if (--indeg[v] == 0) stack[top++] = v;
        }
    }
    free(head);
    free(indeg);
    free(nxt);
    free(to);
    free(stack);
    return seen == n ? 1 : 0;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    int m = 0;
    if (scanf("%d", &m) != 1) return 0;
    int* src = (int*)malloc((size_t)(m > 0 ? m : 1) * sizeof(int));
    for (int i = 0; i < m; i++) {
        if (scanf("%d", &src[i]) != 1) break;
    }
    int* dst = (int*)malloc((size_t)(m > 0 ? m : 1) * sizeof(int));
    for (int i = 0; i < m; i++) {
        if (scanf("%d", &dst[i]) != 1) break;
    }
    printf("%d\\n", course_schedule(n, src, dst, m));
    free(src);
    free(dst);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-pacific-atlantic-water-flow                                            #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-pacific-atlantic-water-flow"] = {
    "python": '''
import sys


def pacific_atlantic(grid, r, c):
    def flood(starts):
        seen = bytearray(r * c)
        stack = []
        for cell in starts:
            if not seen[cell]:
                seen[cell] = 1
                stack.append(cell)
        while stack:
            cell = stack.pop()
            i, j = divmod(cell, c)
            height = grid[cell]
            if i > 0 and not seen[cell - c] and grid[cell - c] >= height:
                seen[cell - c] = 1
                stack.append(cell - c)
            if i + 1 < r and not seen[cell + c] and grid[cell + c] >= height:
                seen[cell + c] = 1
                stack.append(cell + c)
            if j > 0 and not seen[cell - 1] and grid[cell - 1] >= height:
                seen[cell - 1] = 1
                stack.append(cell - 1)
            if j + 1 < c and not seen[cell + 1] and grid[cell + 1] >= height:
                seen[cell + 1] = 1
                stack.append(cell + 1)
        return seen

    pacific = flood([j for j in range(c)] + [i * c for i in range(r)])
    atlantic = flood([(r - 1) * c + j for j in range(c)] + [i * c + c - 1 for i in range(r)])
    return sum(1 for cell in range(r * c) if pacific[cell] and atlantic[cell])


def main():
    data = sys.stdin.read().split()
    pos = 0
    r = int(data[pos]); pos += 1
    c = int(data[pos]); pos += 1
    k = r * c
    grid = [int(x) for x in data[pos:pos + k]]
    print(pacific_atlantic(grid, r, c))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function pacificAtlantic(grid, r, c) {
  const flood = (starts) => {
    const seen = new Uint8Array(r * c);
    const stack = [];
    for (const cell of starts) {
      if (!seen[cell]) {
        seen[cell] = 1;
        stack.push(cell);
      }
    }
    while (stack.length > 0) {
      const cell = stack.pop();
      const i = Math.floor(cell / c);
      const j = cell - i * c;
      const height = grid[cell];
      if (i > 0 && !seen[cell - c] && grid[cell - c] >= height) { seen[cell - c] = 1; stack.push(cell - c); }
      if (i + 1 < r && !seen[cell + c] && grid[cell + c] >= height) { seen[cell + c] = 1; stack.push(cell + c); }
      if (j > 0 && !seen[cell - 1] && grid[cell - 1] >= height) { seen[cell - 1] = 1; stack.push(cell - 1); }
      if (j + 1 < c && !seen[cell + 1] && grid[cell + 1] >= height) { seen[cell + 1] = 1; stack.push(cell + 1); }
    }
    return seen;
  };

  const pacStarts = [];
  const atlStarts = [];
  for (let j = 0; j < c; j++) { pacStarts.push(j); atlStarts.push((r - 1) * c + j); }
  for (let i = 0; i < r; i++) { pacStarts.push(i * c); atlStarts.push(i * c + c - 1); }
  const pacific = flood(pacStarts);
  const atlantic = flood(atlStarts);
  let total = 0;
  for (let cell = 0; cell < r * c; cell++) if (pacific[cell] && atlantic[cell]) total++;
  return total;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const r = data[pos];
pos += 1;
const c = data[pos];
pos += 1;
const k = r * c;
const grid = data.slice(pos, pos + k);
console.log(pacificAtlantic(grid, r, c));
'''.lstrip(),
    "cpp": '''
#include <iostream>
#include <vector>

static std::vector<char> flood(const std::vector<int>& grid, int r, int c,
                               const std::vector<int>& starts) {
    std::vector<char> seen(static_cast<size_t>(r) * c, 0);
    std::vector<int> stack;
    for (int cell : starts) {
        if (!seen[cell]) {
            seen[cell] = 1;
            stack.push_back(cell);
        }
    }
    while (!stack.empty()) {
        int cell = stack.back();
        stack.pop_back();
        int i = cell / c, j = cell % c;
        int height = grid[cell];
        if (i > 0 && !seen[cell - c] && grid[cell - c] >= height) { seen[cell - c] = 1; stack.push_back(cell - c); }
        if (i + 1 < r && !seen[cell + c] && grid[cell + c] >= height) { seen[cell + c] = 1; stack.push_back(cell + c); }
        if (j > 0 && !seen[cell - 1] && grid[cell - 1] >= height) { seen[cell - 1] = 1; stack.push_back(cell - 1); }
        if (j + 1 < c && !seen[cell + 1] && grid[cell + 1] >= height) { seen[cell + 1] = 1; stack.push_back(cell + 1); }
    }
    return seen;
}

int pacificAtlantic(const std::vector<int>& grid, int r, int c) {
    std::vector<int> pacStarts, atlStarts;
    for (int j = 0; j < c; j++) { pacStarts.push_back(j); atlStarts.push_back((r - 1) * c + j); }
    for (int i = 0; i < r; i++) { pacStarts.push_back(i * c); atlStarts.push_back(i * c + c - 1); }
    std::vector<char> pacific = flood(grid, r, c, pacStarts);
    std::vector<char> atlantic = flood(grid, r, c, atlStarts);
    int total = 0;
    for (int cell = 0; cell < r * c; cell++) if (pacific[cell] && atlantic[cell]) total++;
    return total;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int r, c;
    if (!(std::cin >> r)) return 0;
    if (!(std::cin >> c)) return 0;
    const int k = r * c;
    std::vector<int> grid(k);
    for (int i = 0; i < k; i++) std::cin >> grid[i];
    std::cout << pacificAtlantic(grid, r, c) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static boolean[] flood(int[] grid, int r, int c, int[] starts) {
        boolean[] seen = new boolean[r * c];
        int[] stack = new int[r * c];
        int top = 0;
        for (int cell : starts) {
            if (!seen[cell]) {
                seen[cell] = true;
                stack[top++] = cell;
            }
        }
        while (top > 0) {
            int cell = stack[--top];
            int i = cell / c, j = cell % c;
            int height = grid[cell];
            if (i > 0 && !seen[cell - c] && grid[cell - c] >= height) { seen[cell - c] = true; stack[top++] = cell - c; }
            if (i + 1 < r && !seen[cell + c] && grid[cell + c] >= height) { seen[cell + c] = true; stack[top++] = cell + c; }
            if (j > 0 && !seen[cell - 1] && grid[cell - 1] >= height) { seen[cell - 1] = true; stack[top++] = cell - 1; }
            if (j + 1 < c && !seen[cell + 1] && grid[cell + 1] >= height) { seen[cell + 1] = true; stack[top++] = cell + 1; }
        }
        return seen;
    }

    static int pacificAtlantic(int[] grid, int r, int c) {
        int[] pac = new int[r + c];
        int[] atl = new int[r + c];
        int pi = 0, ai = 0;
        for (int j = 0; j < c; j++) { pac[pi++] = j; atl[ai++] = (r - 1) * c + j; }
        for (int i = 0; i < r; i++) { pac[pi++] = i * c; atl[ai++] = i * c + c - 1; }
        boolean[] pacific = flood(grid, r, c, pac);
        boolean[] atlantic = flood(grid, r, c, atl);
        int total = 0;
        for (int cell = 0; cell < r * c; cell++) if (pacific[cell] && atlantic[cell]) total++;
        return total;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int r = (int) in.nextLong();
        int c = (int) in.nextLong();
        int k = r * c;
        int[] grid = new int[k];
        for (int i = 0; i < k; i++) grid[i] = (int) in.nextLong();
        System.out.println(pacificAtlantic(grid, r, c));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

static void flood(const int* grid, int r, int c, const int* starts, int start_count,
                  char* seen, int* stack) {
    int top = 0;
    for (int s = 0; s < start_count; s++) {
        int cell = starts[s];
        if (!seen[cell]) {
            seen[cell] = 1;
            stack[top++] = cell;
        }
    }
    while (top > 0) {
        int cell = stack[--top];
        int i = cell / c;
        int j = cell % c;
        int height = grid[cell];
        if (i > 0 && !seen[cell - c] && grid[cell - c] >= height) { seen[cell - c] = 1; stack[top++] = cell - c; }
        if (i + 1 < r && !seen[cell + c] && grid[cell + c] >= height) { seen[cell + c] = 1; stack[top++] = cell + c; }
        if (j > 0 && !seen[cell - 1] && grid[cell - 1] >= height) { seen[cell - 1] = 1; stack[top++] = cell - 1; }
        if (j + 1 < c && !seen[cell + 1] && grid[cell + 1] >= height) { seen[cell + 1] = 1; stack[top++] = cell + 1; }
    }
}

int pacific_atlantic(const int* grid, int r, int c, int k) {
    (void)k;
    int cells = r * c;
    char* pacific = (char*)calloc((size_t)(cells > 0 ? cells : 1), 1);
    char* atlantic = (char*)calloc((size_t)(cells > 0 ? cells : 1), 1);
    int* stack = (int*)malloc((size_t)(cells > 0 ? cells : 1) * sizeof(int));
    int* starts = (int*)malloc((size_t)(r + c) * sizeof(int));

    int count = 0;
    for (int j = 0; j < c; j++) starts[count++] = j;
    for (int i = 0; i < r; i++) starts[count++] = i * c;
    flood(grid, r, c, starts, count, pacific, stack);

    count = 0;
    for (int j = 0; j < c; j++) starts[count++] = (r - 1) * c + j;
    for (int i = 0; i < r; i++) starts[count++] = i * c + c - 1;
    flood(grid, r, c, starts, count, atlantic, stack);

    int total = 0;
    for (int cell = 0; cell < cells; cell++) {
        if (pacific[cell] && atlantic[cell]) total++;
    }
    free(pacific);
    free(atlantic);
    free(stack);
    free(starts);
    return total;
}

int main(void) {
    int r = 0, c = 0;
    if (scanf("%d", &r) != 1) return 0;
    if (scanf("%d", &c) != 1) return 0;
    const int k = r * c;
    int* grid = (int*)malloc((size_t)(k > 0 ? k : 1) * sizeof(int));
    for (int i = 0; i < k; i++) {
        if (scanf("%d", &grid[i]) != 1) break;
    }
    printf("%d\\n", pacific_atlantic(grid, r, c, k));
    free(grid);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-number-of-islands                                                      #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-number-of-islands"] = {
    "python": '''
import sys


def number_of_islands(grid, r, c):
    cells = bytearray(grid)
    islands = 0
    for start in range(r * c):
        if not cells[start]:
            continue
        islands += 1
        cells[start] = 0
        stack = [start]
        while stack:
            cell = stack.pop()
            i, j = divmod(cell, c)
            if i > 0 and cells[cell - c]:
                cells[cell - c] = 0
                stack.append(cell - c)
            if i + 1 < r and cells[cell + c]:
                cells[cell + c] = 0
                stack.append(cell + c)
            if j > 0 and cells[cell - 1]:
                cells[cell - 1] = 0
                stack.append(cell - 1)
            if j + 1 < c and cells[cell + 1]:
                cells[cell + 1] = 0
                stack.append(cell + 1)
    return islands


def main():
    data = sys.stdin.read().split()
    pos = 0
    r = int(data[pos]); pos += 1
    c = int(data[pos]); pos += 1
    k = r * c
    grid = [int(x) for x in data[pos:pos + k]]
    print(number_of_islands(grid, r, c))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function numberOfIslands(grid, r, c) {
  const cells = Uint8Array.from(grid);
  let islands = 0;
  const stack = [];
  for (let start = 0; start < r * c; start++) {
    if (!cells[start]) continue;
    islands++;
    cells[start] = 0;
    stack.push(start);
    while (stack.length > 0) {
      const cell = stack.pop();
      const i = Math.floor(cell / c);
      const j = cell - i * c;
      if (i > 0 && cells[cell - c]) { cells[cell - c] = 0; stack.push(cell - c); }
      if (i + 1 < r && cells[cell + c]) { cells[cell + c] = 0; stack.push(cell + c); }
      if (j > 0 && cells[cell - 1]) { cells[cell - 1] = 0; stack.push(cell - 1); }
      if (j + 1 < c && cells[cell + 1]) { cells[cell + 1] = 0; stack.push(cell + 1); }
    }
  }
  return islands;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const r = data[pos];
pos += 1;
const c = data[pos];
pos += 1;
const k = r * c;
const grid = data.slice(pos, pos + k);
console.log(numberOfIslands(grid, r, c));
'''.lstrip(),
    "cpp": '''
#include <iostream>
#include <vector>

int numberOfIslands(const std::vector<int>& grid, int r, int c) {
    std::vector<char> cells(grid.begin(), grid.end());
    std::vector<int> stack;
    int islands = 0;
    for (int start = 0; start < r * c; start++) {
        if (!cells[start]) continue;
        islands++;
        cells[start] = 0;
        stack.push_back(start);
        while (!stack.empty()) {
            int cell = stack.back();
            stack.pop_back();
            int i = cell / c, j = cell % c;
            if (i > 0 && cells[cell - c]) { cells[cell - c] = 0; stack.push_back(cell - c); }
            if (i + 1 < r && cells[cell + c]) { cells[cell + c] = 0; stack.push_back(cell + c); }
            if (j > 0 && cells[cell - 1]) { cells[cell - 1] = 0; stack.push_back(cell - 1); }
            if (j + 1 < c && cells[cell + 1]) { cells[cell + 1] = 0; stack.push_back(cell + 1); }
        }
    }
    return islands;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int r, c;
    if (!(std::cin >> r)) return 0;
    if (!(std::cin >> c)) return 0;
    const int k = r * c;
    std::vector<int> grid(k);
    for (int i = 0; i < k; i++) std::cin >> grid[i];
    std::cout << numberOfIslands(grid, r, c) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static int numberOfIslands(int[] grid, int r, int c) {
        int cells = r * c;
        byte[] land = new byte[Math.max(cells, 1)];
        for (int i = 0; i < cells; i++) land[i] = (byte) grid[i];
        int[] stack = new int[Math.max(cells, 1)];
        int islands = 0;
        for (int start = 0; start < cells; start++) {
            if (land[start] == 0) continue;
            islands++;
            land[start] = 0;
            int top = 0;
            stack[top++] = start;
            while (top > 0) {
                int cell = stack[--top];
                int i = cell / c, j = cell % c;
                if (i > 0 && land[cell - c] != 0) { land[cell - c] = 0; stack[top++] = cell - c; }
                if (i + 1 < r && land[cell + c] != 0) { land[cell + c] = 0; stack[top++] = cell + c; }
                if (j > 0 && land[cell - 1] != 0) { land[cell - 1] = 0; stack[top++] = cell - 1; }
                if (j + 1 < c && land[cell + 1] != 0) { land[cell + 1] = 0; stack[top++] = cell + 1; }
            }
        }
        return islands;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int r = (int) in.nextLong();
        int c = (int) in.nextLong();
        int k = r * c;
        int[] grid = new int[k];
        for (int i = 0; i < k; i++) grid[i] = (int) in.nextLong();
        System.out.println(numberOfIslands(grid, r, c));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

int number_of_islands(const int* grid, int r, int c, int k) {
    (void)k;
    int cells = r * c;
    char* land = (char*)malloc((size_t)(cells > 0 ? cells : 1));
    for (int i = 0; i < cells; i++) land[i] = (char)grid[i];
    int* stack = (int*)malloc((size_t)(cells > 0 ? cells : 1) * sizeof(int));
    int islands = 0;
    for (int start = 0; start < cells; start++) {
        if (!land[start]) continue;
        islands++;
        land[start] = 0;
        int top = 0;
        stack[top++] = start;
        while (top > 0) {
            int cell = stack[--top];
            int i = cell / c;
            int j = cell % c;
            if (i > 0 && land[cell - c]) { land[cell - c] = 0; stack[top++] = cell - c; }
            if (i + 1 < r && land[cell + c]) { land[cell + c] = 0; stack[top++] = cell + c; }
            if (j > 0 && land[cell - 1]) { land[cell - 1] = 0; stack[top++] = cell - 1; }
            if (j + 1 < c && land[cell + 1]) { land[cell + 1] = 0; stack[top++] = cell + 1; }
        }
    }
    free(land);
    free(stack);
    return islands;
}

int main(void) {
    int r = 0, c = 0;
    if (scanf("%d", &r) != 1) return 0;
    if (scanf("%d", &c) != 1) return 0;
    const int k = r * c;
    int* grid = (int*)malloc((size_t)(k > 0 ? k : 1) * sizeof(int));
    for (int i = 0; i < k; i++) {
        if (scanf("%d", &grid[i]) != 1) break;
    }
    printf("%d\\n", number_of_islands(grid, r, c, k));
    free(grid);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-longest-consecutive-sequence                                           #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-longest-consecutive-sequence"] = {
    "python": '''
import sys


def longest_consecutive(arr):
    values = set(arr)
    best = 0
    for value in values:
        if value - 1 in values:
            continue
        length = 1
        while value + length in values:
            length += 1
        if length > best:
            best = length
    return best


def main():
    data = sys.stdin.read().split()
    n = int(data[0])
    arr = [int(x) for x in data[1:1 + n]]
    print(longest_consecutive(arr))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function longestConsecutive(arr) {
  const values = new Set(arr);
  let best = 0;
  for (const value of values) {
    if (values.has(value - 1)) continue;
    let length = 1;
    while (values.has(value + length)) length++;
    if (length > best) best = length;
  }
  return best;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos];
pos += 1;
const arr = data.slice(pos, pos + n);
console.log(longestConsecutive(arr));
'''.lstrip(),
    "cpp": '''
#include <algorithm>
#include <iostream>
#include <vector>

int longestConsecutive(const std::vector<long long>& arr) {
    std::vector<long long> values = arr;
    std::sort(values.begin(), values.end());
    values.erase(std::unique(values.begin(), values.end()), values.end());
    int best = 0, cur = 0;
    for (size_t i = 0; i < values.size(); i++) {
        if (i > 0 && values[i] == values[i - 1] + 1) cur++;
        else cur = 1;
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
    std::cout << longestConsecutive(arr) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;
import java.util.*;

public class Main {

    static int longestConsecutive(long[] arr) {
        long[] values = arr.clone();
        Arrays.sort(values);
        int best = 0, cur = 0;
        for (int i = 0; i < values.length; i++) {
            if (i > 0 && values[i] == values[i - 1]) continue;
            if (i > 0 && values[i] == values[i - 1] + 1) cur++;
            else cur = 1;
            best = Math.max(best, cur);
        }
        return best;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        long[] arr = new long[n];
        for (int i = 0; i < n; i++) arr[i] = in.nextLong();
        System.out.println(longestConsecutive(arr));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

static int cmp_ll(const void* a, const void* b) {
    long long x = *(const long long*)a;
    long long y = *(const long long*)b;
    return (x > y) - (x < y);
}

int longest_consecutive(const long long* arr, int n) {
    long long* values = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) values[i] = arr[i];
    qsort(values, (size_t)n, sizeof(long long), cmp_ll);
    int best = 0, cur = 0;
    for (int i = 0; i < n; i++) {
        if (i > 0 && values[i] == values[i - 1]) continue;
        if (i > 0 && values[i] == values[i - 1] + 1) cur++;
        else cur = 1;
        if (cur > best) best = cur;
    }
    free(values);
    return best;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    long long* arr = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    for (int i = 0; i < n; i++) {
        if (scanf("%lld", &arr[i]) != 1) break;
    }
    printf("%d\\n", longest_consecutive(arr, n));
    free(arr);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-alien-dictionary                                                       #
# --------------------------------------------------------------------------- #
# The graph has at most 26 vertices, so "always take the smallest available
# letter" is a plain scan rather than a heap in the compiled languages.
# These solutions print inside the function, because the answer is a string.

SOLUTIONS["b75-alien-dictionary"] = {
    "python": '''
import sys


def alien_order(line):
    words = line.split()
    present = [False] * 26
    adj = [[False] * 26 for _ in range(26)]
    indeg = [0] * 26
    for word in words:
        for ch in word:
            present[ord(ch) - 97] = True
    for first, second in zip(words, words[1:]):
        differed = False
        for a, b in zip(first, second):
            if a != b:
                x, y = ord(a) - 97, ord(b) - 97
                if not adj[x][y]:
                    adj[x][y] = True
                    indeg[y] += 1
                differed = True
                break
        if not differed and len(first) > len(second):
            print("INVALID")
            return 0

    total = sum(1 for flag in present if flag)
    order = []
    used = [False] * 26
    for _ in range(total):
        pick = -1
        for i in range(26):
            if present[i] and not used[i] and indeg[i] == 0:
                pick = i
                break
        if pick < 0:
            print("INVALID")
            return 0
        used[pick] = True
        order.append(chr(97 + pick))
        for j in range(26):
            if adj[pick][j]:
                indeg[j] -= 1
    print("".join(order))
    return 0


def main():
    line = sys.stdin.readline().rstrip('\\n')
    alien_order(line)


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function alienOrder(line) {
  const words = line.split(/\\s+/).filter(Boolean);
  const present = new Uint8Array(26);
  const adj = [];
  for (let i = 0; i < 26; i++) adj.push(new Uint8Array(26));
  const indeg = new Int32Array(26);
  for (const word of words) {
    for (const ch of word) present[ch.charCodeAt(0) - 97] = 1;
  }
  for (let w = 0; w + 1 < words.length; w++) {
    const first = words[w];
    const second = words[w + 1];
    let differed = false;
    const limit = Math.min(first.length, second.length);
    for (let i = 0; i < limit; i++) {
      if (first[i] !== second[i]) {
        const x = first.charCodeAt(i) - 97;
        const y = second.charCodeAt(i) - 97;
        if (!adj[x][y]) {
          adj[x][y] = 1;
          indeg[y] += 1;
        }
        differed = true;
        break;
      }
    }
    if (!differed && first.length > second.length) {
      console.log("INVALID");
      return 0;
    }
  }

  let total = 0;
  for (let i = 0; i < 26; i++) if (present[i]) total++;
  const used = new Uint8Array(26);
  const order = [];
  for (let step = 0; step < total; step++) {
    let pick = -1;
    for (let i = 0; i < 26; i++) {
      if (present[i] && !used[i] && indeg[i] === 0) { pick = i; break; }
    }
    if (pick < 0) {
      console.log("INVALID");
      return 0;
    }
    used[pick] = 1;
    order.push(String.fromCharCode(97 + pick));
    for (let j = 0; j < 26; j++) if (adj[pick][j]) indeg[j] -= 1;
  }
  console.log(order.join(""));
  return 0;
}

const input = require("fs").readFileSync(0, "utf8");
const line = input.split("\\n")[0] ?? "";
alienOrder(line);
'''.lstrip(),
    "cpp": '''
#include <algorithm>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

int alienOrder(const std::string& line) {
    std::istringstream stream(line);
    std::vector<std::string> words;
    std::string token;
    while (stream >> token) words.push_back(token);

    bool present[26] = {false};
    bool adj[26][26] = {{false}};
    int indeg[26] = {0};
    for (const std::string& word : words) {
        for (char ch : word) present[ch - 'a'] = true;
    }
    for (size_t w = 0; w + 1 < words.size(); w++) {
        const std::string& first = words[w];
        const std::string& second = words[w + 1];
        bool differed = false;
        size_t limit = std::min(first.size(), second.size());
        for (size_t i = 0; i < limit; i++) {
            if (first[i] != second[i]) {
                int x = first[i] - 'a';
                int y = second[i] - 'a';
                if (!adj[x][y]) {
                    adj[x][y] = true;
                    indeg[y]++;
                }
                differed = true;
                break;
            }
        }
        if (!differed && first.size() > second.size()) {
            std::cout << "INVALID\\n";
            return 0;
        }
    }

    int total = 0;
    for (int i = 0; i < 26; i++) if (present[i]) total++;
    bool used[26] = {false};
    std::string order;
    for (int step = 0; step < total; step++) {
        int pick = -1;
        for (int i = 0; i < 26; i++) {
            if (present[i] && !used[i] && indeg[i] == 0) { pick = i; break; }
        }
        if (pick < 0) {
            std::cout << "INVALID\\n";
            return 0;
        }
        used[pick] = true;
        order.push_back(static_cast<char>('a' + pick));
        for (int j = 0; j < 26; j++) if (adj[pick][j]) indeg[j]--;
    }
    std::cout << order << "\\n";
    return 0;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    std::string line;
    std::getline(std::cin, line);
    alienOrder(line);
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static int alienOrder(String line) {
        String trimmed = line.trim();
        String[] words = trimmed.isEmpty() ? new String[0] : trimmed.split("\\\\s+");
        boolean[] present = new boolean[26];
        boolean[][] adj = new boolean[26][26];
        int[] indeg = new int[26];
        for (String word : words) {
            for (int i = 0; i < word.length(); i++) present[word.charAt(i) - 'a'] = true;
        }
        for (int w = 0; w + 1 < words.length; w++) {
            String first = words[w];
            String second = words[w + 1];
            boolean differed = false;
            int limit = Math.min(first.length(), second.length());
            for (int i = 0; i < limit; i++) {
                if (first.charAt(i) != second.charAt(i)) {
                    int x = first.charAt(i) - 'a';
                    int y = second.charAt(i) - 'a';
                    if (!adj[x][y]) {
                        adj[x][y] = true;
                        indeg[y]++;
                    }
                    differed = true;
                    break;
                }
            }
            if (!differed && first.length() > second.length()) {
                System.out.println("INVALID");
                return 0;
            }
        }

        int total = 0;
        for (int i = 0; i < 26; i++) if (present[i]) total++;
        boolean[] used = new boolean[26];
        StringBuilder order = new StringBuilder();
        for (int step = 0; step < total; step++) {
            int pick = -1;
            for (int i = 0; i < 26; i++) {
                if (present[i] && !used[i] && indeg[i] == 0) { pick = i; break; }
            }
            if (pick < 0) {
                System.out.println("INVALID");
                return 0;
            }
            used[pick] = true;
            order.append((char) ('a' + pick));
            for (int j = 0; j < 26; j++) if (adj[pick][j]) indeg[j]--;
        }
        System.out.println(order.toString());
        return 0;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        String line = in.nextLine();
        alienOrder(line);
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int alien_order(const char* line) {
    char* copy = strdup(line);
    char present[26] = {0};
    char adj[26][26];
    int indeg[26] = {0};
    memset(adj, 0, sizeof(adj));

    char* prev = strtok(copy, " \\t");
    for (const char* p = prev; p != NULL && *p; p++) present[*p - 'a'] = 1;
    int invalid = 0;
    char* cur = prev ? strtok(NULL, " \\t") : NULL;
    while (cur != NULL) {
        for (const char* p = cur; *p; p++) present[*p - 'a'] = 1;
        int lp = (int)strlen(prev);
        int lc = (int)strlen(cur);
        int limit = lp < lc ? lp : lc;
        int differed = 0;
        for (int i = 0; i < limit; i++) {
            if (prev[i] != cur[i]) {
                int x = prev[i] - 'a';
                int y = cur[i] - 'a';
                if (!adj[x][y]) {
                    adj[x][y] = 1;
                    indeg[y]++;
                }
                differed = 1;
                break;
            }
        }
        if (!differed && lp > lc) invalid = 1;
        prev = cur;
        cur = strtok(NULL, " \\t");
    }
    if (invalid) {
        printf("INVALID\\n");
        free(copy);
        return 0;
    }

    int total = 0;
    for (int i = 0; i < 26; i++) if (present[i]) total++;
    char used[26] = {0};
    char order[27];
    int length = 0;
    for (int step = 0; step < total; step++) {
        int pick = -1;
        for (int i = 0; i < 26; i++) {
            if (present[i] && !used[i] && indeg[i] == 0) { pick = i; break; }
        }
        if (pick < 0) {
            printf("INVALID\\n");
            free(copy);
            return 0;
        }
        used[pick] = 1;
        order[length++] = (char)('a' + pick);
        for (int j = 0; j < 26; j++) {
            if (adj[pick][j]) indeg[j]--;
        }
    }
    order[length] = '\\0';
    printf("%s\\n", order);
    free(copy);
    return 0;
}

int main(void) {
    char* line = NULL;
    size_t cap = 0;
    ssize_t len = getline(&line, &cap, stdin);
    if (len < 0) {
        line = (char*)calloc(1, 1);
        len = 0;
    }
    while (len > 0 && (line[len - 1] == '\\n' || line[len - 1] == '\\r')) {
        line[--len] = '\\0';
    }
    alien_order(line);
    free(line);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-connected-components                                                   #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-connected-components"] = {
    "python": '''
import sys


def connected_components(n, src, dst):
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    components = n
    for i in range(len(src)):
        a = find(src[i])
        b = find(dst[i])
        if a != b:
            parent[a] = b
            components -= 1
    return components


def main():
    data = sys.stdin.read().split()
    pos = 0
    n = int(data[pos]); pos += 1
    m = int(data[pos]); pos += 1
    src = [int(x) for x in data[pos:pos + m]]; pos += m
    dst = [int(x) for x in data[pos:pos + m]]; pos += m
    print(connected_components(n, src, dst))


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function connectedComponents(n, src, dst) {
  const parent = new Int32Array(n + 1);
  for (let i = 0; i <= n; i++) parent[i] = i;
  const find = (x) => {
    while (parent[x] !== x) {
      parent[x] = parent[parent[x]];
      x = parent[x];
    }
    return x;
  };
  let components = n;
  for (let i = 0; i < src.length; i++) {
    const a = find(src[i]);
    const b = find(dst[i]);
    if (a !== b) {
      parent[a] = b;
      components--;
    }
  }
  return components;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const n = data[pos];
pos += 1;
const m = data[pos];
pos += 1;
const src = data.slice(pos, pos + m);
pos += m;
const dst = data.slice(pos, pos + m);
pos += m;
console.log(connectedComponents(n, src, dst));
'''.lstrip(),
    "cpp": '''
#include <iostream>
#include <vector>

static int findRoot(std::vector<int>& parent, int x) {
    while (parent[x] != x) {
        parent[x] = parent[parent[x]];
        x = parent[x];
    }
    return x;
}

int connectedComponents(int n, const std::vector<int>& src, const std::vector<int>& dst) {
    std::vector<int> parent(n + 1);
    for (int i = 0; i <= n; i++) parent[i] = i;
    int components = n;
    for (size_t i = 0; i < src.size(); i++) {
        int a = findRoot(parent, src[i]);
        int b = findRoot(parent, dst[i]);
        if (a != b) {
            parent[a] = b;
            components--;
        }
    }
    return components;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int n;
    if (!(std::cin >> n)) return 0;
    int m;
    if (!(std::cin >> m)) return 0;
    std::vector<int> src(m), dst(m);
    for (int i = 0; i < m; i++) std::cin >> src[i];
    for (int i = 0; i < m; i++) std::cin >> dst[i];
    std::cout << connectedComponents(n, src, dst) << "\\n";
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static int[] parent;

    static int find(int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        return x;
    }

    static int connectedComponents(int n, int[] src, int[] dst) {
        parent = new int[n + 1];
        for (int i = 0; i <= n; i++) parent[i] = i;
        int components = n;
        for (int i = 0; i < src.length; i++) {
            int a = find(src[i]);
            int b = find(dst[i]);
            if (a != b) {
                parent[a] = b;
                components--;
            }
        }
        return components;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int n = (int) in.nextLong();
        int m = (int) in.nextLong();
        int[] src = new int[m];
        for (int i = 0; i < m; i++) src[i] = (int) in.nextLong();
        int[] dst = new int[m];
        for (int i = 0; i < m; i++) dst[i] = (int) in.nextLong();
        System.out.println(connectedComponents(n, src, dst));
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

static int find_root(int* parent, int x) {
    while (parent[x] != x) {
        parent[x] = parent[parent[x]];
        x = parent[x];
    }
    return x;
}

int connected_components(int n, const int* src, const int* dst, int m) {
    int* parent = (int*)malloc((size_t)(n + 1) * sizeof(int));
    for (int i = 0; i <= n; i++) parent[i] = i;
    int components = n;
    for (int i = 0; i < m; i++) {
        int a = find_root(parent, src[i]);
        int b = find_root(parent, dst[i]);
        if (a != b) {
            parent[a] = b;
            components--;
        }
    }
    free(parent);
    return components;
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1) return 0;
    int m = 0;
    if (scanf("%d", &m) != 1) return 0;
    int* src = (int*)malloc((size_t)(m > 0 ? m : 1) * sizeof(int));
    for (int i = 0; i < m; i++) {
        if (scanf("%d", &src[i]) != 1) break;
    }
    int* dst = (int*)malloc((size_t)(m > 0 ? m : 1) * sizeof(int));
    for (int i = 0; i < m; i++) {
        if (scanf("%d", &dst[i]) != 1) break;
    }
    printf("%d\\n", connected_components(n, src, dst, m));
    free(src);
    free(dst);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-set-matrix-zeroes                                                      #
# --------------------------------------------------------------------------- #
# The answer is a matrix, so these solutions print inside the function and main
# ignores the return value.

SOLUTIONS["b75-set-matrix-zeroes"] = {
    "python": '''
import sys


def set_matrix_zeroes(grid, r, c):
    cells = list(grid)
    zero_rows = [False] * r
    zero_cols = [False] * c
    for i in range(r):
        base = i * c
        for j in range(c):
            if cells[base + j] == 0:
                zero_rows[i] = True
                zero_cols[j] = True
    out = []
    for i in range(r):
        base = i * c
        row = []
        for j in range(c):
            row.append('0' if zero_rows[i] or zero_cols[j] else str(cells[base + j]))
        out.append(' '.join(row))
    sys.stdout.write('\\n'.join(out) + '\\n')
    return 0


def main():
    data = sys.stdin.read().split()
    pos = 0
    r = int(data[pos]); pos += 1
    c = int(data[pos]); pos += 1
    k = r * c
    grid = [int(x) for x in data[pos:pos + k]]
    set_matrix_zeroes(grid, r, c)


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function setMatrixZeroes(grid, r, c) {
  const zeroRows = new Uint8Array(r);
  const zeroCols = new Uint8Array(c);
  for (let i = 0; i < r; i++) {
    for (let j = 0; j < c; j++) {
      if (grid[i * c + j] === 0) {
        zeroRows[i] = 1;
        zeroCols[j] = 1;
      }
    }
  }
  const out = [];
  for (let i = 0; i < r; i++) {
    const row = new Array(c);
    for (let j = 0; j < c; j++) {
      row[j] = zeroRows[i] || zeroCols[j] ? 0 : grid[i * c + j];
    }
    out.push(row.join(" "));
  }
  console.log(out.join("\\n"));
  return 0;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const r = data[pos];
pos += 1;
const c = data[pos];
pos += 1;
const k = r * c;
const grid = data.slice(pos, pos + k);
setMatrixZeroes(grid, r, c);
'''.lstrip(),
    "cpp": '''
#include <iostream>
#include <vector>

int setMatrixZeroes(const std::vector<int>& grid, int r, int c) {
    std::vector<char> zeroRows(r, 0), zeroCols(c, 0);
    for (int i = 0; i < r; i++) {
        for (int j = 0; j < c; j++) {
            if (grid[i * c + j] == 0) {
                zeroRows[i] = 1;
                zeroCols[j] = 1;
            }
        }
    }
    for (int i = 0; i < r; i++) {
        for (int j = 0; j < c; j++) {
            if (j) std::cout << ' ';
            std::cout << (zeroRows[i] || zeroCols[j] ? 0 : grid[i * c + j]);
        }
        std::cout << '\\n';
    }
    return 0;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int r, c;
    if (!(std::cin >> r)) return 0;
    if (!(std::cin >> c)) return 0;
    const int k = r * c;
    std::vector<int> grid(k);
    for (int i = 0; i < k; i++) std::cin >> grid[i];
    setMatrixZeroes(grid, r, c);
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static int setMatrixZeroes(int[] grid, int r, int c) {
        boolean[] zeroRows = new boolean[r];
        boolean[] zeroCols = new boolean[c];
        for (int i = 0; i < r; i++) {
            for (int j = 0; j < c; j++) {
                if (grid[i * c + j] == 0) {
                    zeroRows[i] = true;
                    zeroCols[j] = true;
                }
            }
        }
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < r; i++) {
            for (int j = 0; j < c; j++) {
                if (j > 0) sb.append(' ');
                sb.append(zeroRows[i] || zeroCols[j] ? 0 : grid[i * c + j]);
            }
            sb.append('\\n');
        }
        System.out.print(sb);
        return 0;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int r = (int) in.nextLong();
        int c = (int) in.nextLong();
        int k = r * c;
        int[] grid = new int[k];
        for (int i = 0; i < k; i++) grid[i] = (int) in.nextLong();
        setMatrixZeroes(grid, r, c);
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

int set_matrix_zeroes(const int* grid, int r, int c, int k) {
    (void)k;
    char* zero_rows = (char*)calloc((size_t)(r > 0 ? r : 1), 1);
    char* zero_cols = (char*)calloc((size_t)(c > 0 ? c : 1), 1);
    for (int i = 0; i < r; i++) {
        for (int j = 0; j < c; j++) {
            if (grid[i * c + j] == 0) {
                zero_rows[i] = 1;
                zero_cols[j] = 1;
            }
        }
    }
    for (int i = 0; i < r; i++) {
        for (int j = 0; j < c; j++) {
            if (j) putchar(' ');
            printf("%d", (zero_rows[i] || zero_cols[j]) ? 0 : grid[i * c + j]);
        }
        putchar('\\n');
    }
    free(zero_rows);
    free(zero_cols);
    return 0;
}

int main(void) {
    int r = 0, c = 0;
    if (scanf("%d", &r) != 1) return 0;
    if (scanf("%d", &c) != 1) return 0;
    const int k = r * c;
    int* grid = (int*)malloc((size_t)(k > 0 ? k : 1) * sizeof(int));
    for (int i = 0; i < k; i++) {
        if (scanf("%d", &grid[i]) != 1) break;
    }
    set_matrix_zeroes(grid, r, c, k);
    free(grid);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-spiral-matrix                                                          #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-spiral-matrix"] = {
    "python": '''
import sys


def spiral_matrix(grid, r, c):
    top, bottom, left, right = 0, r - 1, 0, c - 1
    out = []
    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            out.append(grid[top * c + j])
        for i in range(top + 1, bottom + 1):
            out.append(grid[i * c + right])
        if top < bottom and left < right:
            for j in range(right - 1, left - 1, -1):
                out.append(grid[bottom * c + j])
            for i in range(bottom - 1, top, -1):
                out.append(grid[i * c + left])
        top += 1
        bottom -= 1
        left += 1
        right -= 1
    print(' '.join(str(v) for v in out))
    return 0


def main():
    data = sys.stdin.read().split()
    pos = 0
    r = int(data[pos]); pos += 1
    c = int(data[pos]); pos += 1
    k = r * c
    grid = [int(x) for x in data[pos:pos + k]]
    spiral_matrix(grid, r, c)


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function spiralMatrix(grid, r, c) {
  let top = 0;
  let bottom = r - 1;
  let left = 0;
  let right = c - 1;
  const out = [];
  while (top <= bottom && left <= right) {
    for (let j = left; j <= right; j++) out.push(grid[top * c + j]);
    for (let i = top + 1; i <= bottom; i++) out.push(grid[i * c + right]);
    if (top < bottom && left < right) {
      for (let j = right - 1; j >= left; j--) out.push(grid[bottom * c + j]);
      for (let i = bottom - 1; i > top; i--) out.push(grid[i * c + left]);
    }
    top++;
    bottom--;
    left++;
    right--;
  }
  console.log(out.join(" "));
  return 0;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const r = data[pos];
pos += 1;
const c = data[pos];
pos += 1;
const k = r * c;
const grid = data.slice(pos, pos + k);
spiralMatrix(grid, r, c);
'''.lstrip(),
    "cpp": '''
#include <iostream>
#include <vector>

int spiralMatrix(const std::vector<int>& grid, int r, int c) {
    int top = 0, bottom = r - 1, left = 0, right = c - 1;
    bool first = true;
    while (top <= bottom && left <= right) {
        for (int j = left; j <= right; j++) {
            if (!first) std::cout << ' ';
            std::cout << grid[top * c + j];
            first = false;
        }
        for (int i = top + 1; i <= bottom; i++) {
            std::cout << ' ' << grid[i * c + right];
        }
        if (top < bottom && left < right) {
            for (int j = right - 1; j >= left; j--) std::cout << ' ' << grid[bottom * c + j];
            for (int i = bottom - 1; i > top; i--) std::cout << ' ' << grid[i * c + left];
        }
        top++;
        bottom--;
        left++;
        right--;
    }
    std::cout << '\\n';
    return 0;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int r, c;
    if (!(std::cin >> r)) return 0;
    if (!(std::cin >> c)) return 0;
    const int k = r * c;
    std::vector<int> grid(k);
    for (int i = 0; i < k; i++) std::cin >> grid[i];
    spiralMatrix(grid, r, c);
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static int spiralMatrix(int[] grid, int r, int c) {
        int top = 0, bottom = r - 1, left = 0, right = c - 1;
        StringBuilder sb = new StringBuilder();
        boolean first = true;
        while (top <= bottom && left <= right) {
            for (int j = left; j <= right; j++) {
                if (!first) sb.append(' ');
                sb.append(grid[top * c + j]);
                first = false;
            }
            for (int i = top + 1; i <= bottom; i++) sb.append(' ').append(grid[i * c + right]);
            if (top < bottom && left < right) {
                for (int j = right - 1; j >= left; j--) sb.append(' ').append(grid[bottom * c + j]);
                for (int i = bottom - 1; i > top; i--) sb.append(' ').append(grid[i * c + left]);
            }
            top++;
            bottom--;
            left++;
            right--;
        }
        System.out.println(sb.toString());
        return 0;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int r = (int) in.nextLong();
        int c = (int) in.nextLong();
        int k = r * c;
        int[] grid = new int[k];
        for (int i = 0; i < k; i++) grid[i] = (int) in.nextLong();
        spiralMatrix(grid, r, c);
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

int spiral_matrix(const int* grid, int r, int c, int k) {
    (void)k;
    int top = 0, bottom = r - 1, left = 0, right = c - 1;
    int first = 1;
    while (top <= bottom && left <= right) {
        for (int j = left; j <= right; j++) {
            if (!first) putchar(' ');
            printf("%d", grid[top * c + j]);
            first = 0;
        }
        for (int i = top + 1; i <= bottom; i++) printf(" %d", grid[i * c + right]);
        if (top < bottom && left < right) {
            for (int j = right - 1; j >= left; j--) printf(" %d", grid[bottom * c + j]);
            for (int i = bottom - 1; i > top; i--) printf(" %d", grid[i * c + left]);
        }
        top++;
        bottom--;
        left++;
        right--;
    }
    putchar('\\n');
    return 0;
}

int main(void) {
    int r = 0, c = 0;
    if (scanf("%d", &r) != 1) return 0;
    if (scanf("%d", &c) != 1) return 0;
    const int k = r * c;
    int* grid = (int*)malloc((size_t)(k > 0 ? k : 1) * sizeof(int));
    for (int i = 0; i < k; i++) {
        if (scanf("%d", &grid[i]) != 1) break;
    }
    spiral_matrix(grid, r, c, k);
    free(grid);
    return 0;
}
'''.lstrip(),
}


# --------------------------------------------------------------------------- #
#  b75-rotate-image                                                           #
# --------------------------------------------------------------------------- #

SOLUTIONS["b75-rotate-image"] = {
    "python": '''
import sys


def rotate_image(grid, r, c):
    n = r
    cells = list(grid)
    # In place: transpose, then reverse every row.
    for i in range(n):
        for j in range(i + 1, n):
            cells[i * n + j], cells[j * n + i] = cells[j * n + i], cells[i * n + j]
    for i in range(n):
        base = i * n
        for j in range(n // 2):
            cells[base + j], cells[base + n - 1 - j] = cells[base + n - 1 - j], cells[base + j]
    out = [' '.join(str(cells[i * n + j]) for j in range(n)) for i in range(n)]
    sys.stdout.write('\\n'.join(out) + '\\n')
    return 0


def main():
    data = sys.stdin.read().split()
    pos = 0
    r = int(data[pos]); pos += 1
    c = int(data[pos]); pos += 1
    k = r * c
    grid = [int(x) for x in data[pos:pos + k]]
    rotate_image(grid, r, c)


if __name__ == "__main__":
    main()
'''.lstrip(),
    "javascript": '''
function rotateImage(grid, r, c) {
  const n = r;
  const cells = Array.from(grid);
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const tmp = cells[i * n + j];
      cells[i * n + j] = cells[j * n + i];
      cells[j * n + i] = tmp;
    }
  }
  for (let i = 0; i < n; i++) {
    const base = i * n;
    for (let j = 0; j < n >> 1; j++) {
      const tmp = cells[base + j];
      cells[base + j] = cells[base + n - 1 - j];
      cells[base + n - 1 - j] = tmp;
    }
  }
  const out = [];
  for (let i = 0; i < n; i++) out.push(cells.slice(i * n, i * n + n).join(" "));
  console.log(out.join("\\n"));
  return 0;
}

const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean).map(Number);
let pos = 0;
const r = data[pos];
pos += 1;
const c = data[pos];
pos += 1;
const k = r * c;
const grid = data.slice(pos, pos + k);
rotateImage(grid, r, c);
'''.lstrip(),
    "cpp": '''
#include <algorithm>
#include <iostream>
#include <vector>

int rotateImage(const std::vector<int>& grid, int r, int c) {
    (void)c;
    int n = r;
    std::vector<int> cells = grid;
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) std::swap(cells[i * n + j], cells[j * n + i]);
    }
    for (int i = 0; i < n; i++) {
        std::reverse(cells.begin() + i * n, cells.begin() + i * n + n);
    }
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (j) std::cout << ' ';
            std::cout << cells[i * n + j];
        }
        std::cout << '\\n';
    }
    return 0;
}

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    int r, c;
    if (!(std::cin >> r)) return 0;
    if (!(std::cin >> c)) return 0;
    const int k = r * c;
    std::vector<int> grid(k);
    for (int i = 0; i < k; i++) std::cin >> grid[i];
    rotateImage(grid, r, c);
    return 0;
}
'''.lstrip(),
    "java": '''
import java.io.IOException;

public class Main {

    static int rotateImage(int[] grid, int r, int c) {
        int n = r;
        int[] cells = grid.clone();
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                int tmp = cells[i * n + j];
                cells[i * n + j] = cells[j * n + i];
                cells[j * n + i] = tmp;
            }
        }
        for (int i = 0; i < n; i++) {
            int base = i * n;
            for (int j = 0; j < n / 2; j++) {
                int tmp = cells[base + j];
                cells[base + j] = cells[base + n - 1 - j];
                cells[base + n - 1 - j] = tmp;
            }
        }
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                if (j > 0) sb.append(' ');
                sb.append(cells[i * n + j]);
            }
            sb.append('\\n');
        }
        System.out.print(sb);
        return 0;
    }

    public static void main(String[] args) throws IOException {
        FastReader in = new FastReader(System.in);
        int r = (int) in.nextLong();
        int c = (int) in.nextLong();
        int k = r * c;
        int[] grid = new int[k];
        for (int i = 0; i < k; i++) grid[i] = (int) in.nextLong();
        rotateImage(grid, r, c);
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
'''.lstrip(),
    "c": '''
#include <stdio.h>
#include <stdlib.h>

int rotate_image(const int* grid, int r, int c, int k) {
    (void)c;
    int n = r;
    int* cells = (int*)malloc((size_t)(k > 0 ? k : 1) * sizeof(int));
    for (int i = 0; i < k; i++) cells[i] = grid[i];
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            int tmp = cells[i * n + j];
            cells[i * n + j] = cells[j * n + i];
            cells[j * n + i] = tmp;
        }
    }
    for (int i = 0; i < n; i++) {
        int base = i * n;
        for (int j = 0; j < n / 2; j++) {
            int tmp = cells[base + j];
            cells[base + j] = cells[base + n - 1 - j];
            cells[base + n - 1 - j] = tmp;
        }
    }
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (j) putchar(' ');
            printf("%d", cells[i * n + j]);
        }
        putchar('\\n');
    }
    free(cells);
    return 0;
}

int main(void) {
    int r = 0, c = 0;
    if (scanf("%d", &r) != 1) return 0;
    if (scanf("%d", &c) != 1) return 0;
    const int k = r * c;
    int* grid = (int*)malloc((size_t)(k > 0 ? k : 1) * sizeof(int));
    for (int i = 0; i < k; i++) {
        if (scanf("%d", &grid[i]) != 1) break;
    }
    rotate_image(grid, r, c, k);
    free(grid);
    return 0;
}
'''.lstrip(),
}
