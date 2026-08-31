"""Proves the array-rotate scale case gates complexity without rejecting correct work.

A scale case is only worth adding if it does both jobs, so this asserts both
directions in all six languages:

* a correct O(n) solution passes every case, including the 100000-element one;
* the repeated single-step rotation requirement 3 forbids fails it.

Run after touching `ROTATE_TESTS` or the starters:

    cd backend && PYTHONPATH=. .venv/bin/python scripts/verify_array_rotate.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.curriculum import graded_cases
from app.data.practice_modules import PRACTICE_MODULE_INDEX
from app.schemas.execution import TestCase
from app.services.code_execution_service import LocalSubprocessProvider, time_limit_for

LINEAR = {
    "python": """import sys


def rotate(arr, k):
    if not arr:
        return arr
    k %= len(arr)
    return arr[-k:] + arr[:-k] if k else arr


def main():
    data = sys.stdin.buffer.read().split()
    n, k = int(data[0]), int(data[1])
    arr = [int(x) for x in data[2:2 + n]]
    sys.stdout.write(' '.join(map(str, rotate(arr, k))) + '\\n')


if __name__ == "__main__":
    main()
""",
    "javascript": """const data = require("fs").readFileSync(0, "utf8").split(/\\s+/).filter(Boolean);
const n = Number(data[0]);
const k = Number(data[1]) % n;
const arr = data.slice(2, 2 + n);
const out = k ? arr.slice(n - k).concat(arr.slice(0, n - k)) : arr;
process.stdout.write(out.join(" ") + "\\n");
""",
    "typescript": """const data: string[] = require("fs")
  .readFileSync(0, "utf8")
  .split(/\\s+/)
  .filter((t: string) => t.length > 0);
const n: number = Number(data[0]);
const k: number = Number(data[1]) % n;
const arr: string[] = data.slice(2, 2 + n);
const out: string[] = k ? arr.slice(n - k).concat(arr.slice(0, n - k)) : arr;
process.stdout.write(out.join(" ") + "\\n");
""",
    "java": """import java.io.*;

public class Main {
    public static void main(String[] args) throws IOException {
        DataInputStream in = new DataInputStream(new BufferedInputStream(System.in, 1 << 16));
        int n = nextInt(in);
        long k = nextLong(in);
        int[] arr = new int[n];
        for (int i = 0; i < n; i++) arr[i] = nextInt(in);
        int shift = (int) (k % n);
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            if (i > 0) sb.append(' ');
            sb.append(arr[(i - shift + n) % n]);
        }
        sb.append('\\n');
        System.out.print(sb);
    }

    private static int nextInt(DataInputStream in) throws IOException {
        return (int) nextLong(in);
    }

    private static long nextLong(DataInputStream in) throws IOException {
        long ret = 0;
        int b = in.read();
        while (b < '-') b = in.read();
        boolean neg = b == '-';
        if (neg) b = in.read();
        while (b >= '0') {
            ret = ret * 10 + (b - '0');
            b = in.read();
        }
        return neg ? -ret : ret;
    }
}
""",
    "c": """#include <stdio.h>
#include <stdlib.h>

int main(void) {
    long long n, k;
    if (scanf("%lld %lld", &n, &k) != 2) return 0;
    int *arr = malloc(sizeof(int) * n);
    for (long long i = 0; i < n; i++) scanf("%d", &arr[i]);
    long long s = k % n;
    for (long long i = 0; i < n; i++) {
        long long j = ((i - s) % n + n) % n;
        printf("%s%d", i ? " " : "", arr[j]);
    }
    printf("\\n");
    free(arr);
    return 0;
}
""",
    # Standard headers rather than <bits/stdc++.h>, which is a libstdc++
    # extension and does not exist under the clang toolchain on macOS.
    "cpp": """#include <iostream>
#include <string>
#include <vector>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    long long n, k;
    if (!(cin >> n >> k)) return 0;
    vector<int> arr(n);
    for (long long i = 0; i < n; i++) cin >> arr[i];
    long long s = k % n;
    string out;
    for (long long i = 0; i < n; i++) {
        long long j = ((i - s) % n + n) % n;
        if (i) out += ' ';
        out += to_string(arr[j]);
    }
    out += '\\n';
    cout << out;
    return 0;
}
""",
}

#: Exactly what requirement 3 forbids, in the language most likely to be tried.
QUADRATIC_PYTHON = """import sys


def rotate(arr, k):
    for _ in range(k):
        if arr:
            arr = [arr[-1]] + arr[:-1]
    return arr


def main():
    data = sys.stdin.buffer.read().split()
    n, k = int(data[0]), int(data[1])
    arr = [int(x) for x in data[2:2 + n]]
    sys.stdout.write(' '.join(map(str, rotate(arr, k))) + '\\n')


if __name__ == "__main__":
    main()
"""

PREFIX = {
    "python": "py", "javascript": "js", "typescript": "ts",
    "java": "java", "c": "c", "cpp": "cpp",
}


def cases(module_id: str) -> list[TestCase]:
    module = PRACTICE_MODULE_INDEX[module_id]
    return [
        TestCase(
            name=c["name"],
            stdin=c["stdin"],
            expected_stdout=c["expected_stdout"],
            hidden=c["hidden"],
        )
        for c in graded_cases(module)
    ]


def judge(language: str, source: str, module_id: str):
    return asyncio.run(
        LocalSubprocessProvider().run(language, source, cases(module_id))
    )


def main() -> int:
    failures: list[str] = []

    for language, source in LINEAR.items():
        module_id = f"{PREFIX[language]}-array-rotate"
        total = len(cases(module_id))
        result = judge(language, source, module_id)

        if result.compile_error:
            failures.append(f"{language}: reference does not compile")
            print(f"  {language:11} COMPILE ERROR\n{result.compile_error[:400]}")
            continue
        if not result.supported:
            print(f"  {language:11} SKIP — {result.unsupported_reason}")
            continue

        passed = sum(1 for r in result.results if r.passed)
        slowest = max((r.duration_ms for r in result.results), default=0)
        ok = passed == total
        print(
            f"  {language:11} {'PASS' if ok else 'FAIL'}  {passed}/{total} cases  "
            f"(slowest {slowest}ms, limit {time_limit_for(language):.0f}s)"
        )
        if not ok:
            for r in result.results:
                if not r.passed:
                    failures.append(f"{language}: correct solution failed '{r.name}'")
                    print(
                        f"      x {r.name}  exit={r.exit_code} "
                        f"timed_out={r.timed_out} {r.stderr.strip()[:200]}"
                    )

    print("\n--- the solution requirement 3 forbids must be rejected ---")
    result = judge("python", QUADRATIC_PYTHON, "py-array-rotate")
    scale = next(
        (r for r in result.results if "scale" in r.name), None
    )
    if scale is None:
        failures.append("no scale case found in py-array-rotate")
        print("  no scale case present")
    elif scale.passed:
        failures.append("the quadratic solution passed the scale case")
        print("  FAIL — quadratic solution was credited")
    else:
        print(
            f"  PASS — rejected on '{scale.name}' "
            f"(timed_out={scale.timed_out}, {scale.duration_ms}ms)"
        )

    print()
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for line in failures:
            print(f"  - {line}")
        return 1
    print(
        "OK: a linear solution passes every case in all six languages, and the "
        "repeated single-step rotation is rejected at scale"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
