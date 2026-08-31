#!/usr/bin/env python3
"""Acceptance check for the five matrix problems' input format.

Run from the backend directory:

    PYTHONPATH=. python -m scripts.verify_grid_input_formats

The bug this guards against is not a crash and not a wrong answer: it is a
*correct* solution being rejected. The owner submitted a working spiral-matrix
solution that read ``r`` and ``c`` and then the grid — the only sensible reading
of the stated format — and the judge failed it, because the format also carried
a third token ``k = r * c`` that his code consumed as the first grid value.

So this script does not test the reference solutions (they were never wrong). It
tests solutions written the way a competent programmer writes them against the
stated format, in two languages per problem, through the real judge and against
every case including the hidden ones. Then it re-runs each problem's declared
wrong solutions to confirm the suite still rejects them: a format change that
made the tests easier to pass would be a worse bug than the one being fixed.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

# Deliberately not importing app.data.curriculum: it builds every practice
# module at import time, which costs minutes. The generated bank is read
# directly instead.
from app.data.curriculum_blind75_4 import PROBLEMS  # noqa: E402
from app.schemas.execution import TestCase  # noqa: E402
from app.services.code_execution_service import LocalSubprocessProvider  # noqa: E402

GENERATED_CASES_PATH = _ROOT / "app" / "data" / "generated_cases.json"

# --------------------------------------------------------------------------- #
#  Spiral Matrix — the owner's own submission, verbatim in shape:             #
#  read r and c, read the grid, walk the spiral. No count token anywhere.     #
# --------------------------------------------------------------------------- #

SPIRAL_CPP = """
#include <iostream>
#include <vector>
using namespace std;

int main() {
    int r, c;
    cin >> r >> c;
    vector<vector<int>> a(r, vector<int>(c));
    for (int i = 0; i < r; i++)
        for (int j = 0; j < c; j++)
            cin >> a[i][j];

    int top = 0, bottom = r - 1, left = 0, right = c - 1;
    vector<int> out;
    while (top <= bottom && left <= right) {
        for (int j = left; j <= right; j++) out.push_back(a[top][j]);
        for (int i = top + 1; i <= bottom; i++) out.push_back(a[i][right]);
        if (top < bottom && left < right) {
            for (int j = right - 1; j >= left; j--) out.push_back(a[bottom][j]);
            for (int i = bottom - 1; i > top; i--) out.push_back(a[i][left]);
        }
        top++; bottom--; left++; right--;
    }
    for (size_t i = 0; i < out.size(); i++) {
        if (i) cout << ' ';
        cout << out[i];
    }
    cout << '\\n';
    return 0;
}
"""

SPIRAL_PY = """
import sys

data = sys.stdin.read().split()
r, c = int(data[0]), int(data[1])
grid = [[int(data[2 + i * c + j]) for j in range(c)] for i in range(r)]

top, bottom, left, right = 0, r - 1, 0, c - 1
out = []
while top <= bottom and left <= right:
    for j in range(left, right + 1):
        out.append(grid[top][j])
    for i in range(top + 1, bottom + 1):
        out.append(grid[i][right])
    if top < bottom and left < right:
        for j in range(right - 1, left - 1, -1):
            out.append(grid[bottom][j])
        for i in range(bottom - 1, top, -1):
            out.append(grid[i][left])
    top, bottom, left, right = top + 1, bottom - 1, left + 1, right - 1
print(' '.join(map(str, out)))
"""

# --------------------------------------------------------------------------- #
#  Rotate Image                                                               #
# --------------------------------------------------------------------------- #

ROTATE_CPP = """
#include <algorithm>
#include <iostream>
#include <vector>
using namespace std;

int main() {
    int r, c;
    cin >> r >> c;
    vector<vector<int>> a(r, vector<int>(c));
    for (int i = 0; i < r; i++)
        for (int j = 0; j < c; j++)
            cin >> a[i][j];

    int n = r;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            swap(a[i][j], a[j][i]);
    for (int i = 0; i < n; i++)
        reverse(a[i].begin(), a[i].end());

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (j) cout << ' ';
            cout << a[i][j];
        }
        cout << '\\n';
    }
    return 0;
}
"""

ROTATE_PY = """
import sys

data = sys.stdin.read().split()
r, c = int(data[0]), int(data[1])
grid = [[int(data[2 + i * c + j]) for j in range(c)] for i in range(r)]

n = r
for i in range(n):
    for j in range(i + 1, n):
        grid[i][j], grid[j][i] = grid[j][i], grid[i][j]
for row in grid:
    row.reverse()
print('\\n'.join(' '.join(map(str, row)) for row in grid))
"""

# --------------------------------------------------------------------------- #
#  Set Matrix Zeroes                                                          #
# --------------------------------------------------------------------------- #

ZEROES_CPP = """
#include <iostream>
#include <vector>
using namespace std;

int main() {
    int r, c;
    cin >> r >> c;
    vector<vector<int>> a(r, vector<int>(c));
    for (int i = 0; i < r; i++)
        for (int j = 0; j < c; j++)
            cin >> a[i][j];

    vector<bool> zeroRow(r, false), zeroCol(c, false);
    for (int i = 0; i < r; i++)
        for (int j = 0; j < c; j++)
            if (a[i][j] == 0) { zeroRow[i] = true; zeroCol[j] = true; }

    for (int i = 0; i < r; i++) {
        for (int j = 0; j < c; j++) {
            if (j) cout << ' ';
            cout << ((zeroRow[i] || zeroCol[j]) ? 0 : a[i][j]);
        }
        cout << '\\n';
    }
    return 0;
}
"""

ZEROES_PY = """
import sys

data = sys.stdin.read().split()
r, c = int(data[0]), int(data[1])
grid = [[int(data[2 + i * c + j]) for j in range(c)] for i in range(r)]

zero_rows = {i for i in range(r) if any(v == 0 for v in grid[i])}
zero_cols = {j for j in range(c) if any(grid[i][j] == 0 for i in range(r))}
out = []
for i in range(r):
    out.append(' '.join(
        '0' if i in zero_rows or j in zero_cols else str(grid[i][j])
        for j in range(c)
    ))
print('\\n'.join(out))
"""

# --------------------------------------------------------------------------- #
#  Number of Islands                                                          #
# --------------------------------------------------------------------------- #

ISLANDS_CPP = """
#include <iostream>
#include <vector>
using namespace std;

int main() {
    int r, c;
    cin >> r >> c;
    vector<vector<int>> a(r, vector<int>(c));
    for (int i = 0; i < r; i++)
        for (int j = 0; j < c; j++)
            cin >> a[i][j];

    int islands = 0;
    vector<pair<int, int>> stack;
    for (int i = 0; i < r; i++) {
        for (int j = 0; j < c; j++) {
            if (a[i][j] != 1) continue;
            islands++;
            stack.push_back({i, j});
            a[i][j] = 0;
            while (!stack.empty()) {
                auto [ci, cj] = stack.back();
                stack.pop_back();
                int di[] = {-1, 1, 0, 0};
                int dj[] = {0, 0, -1, 1};
                for (int d = 0; d < 4; d++) {
                    int ni = ci + di[d], nj = cj + dj[d];
                    if (ni < 0 || ni >= r || nj < 0 || nj >= c) continue;
                    if (a[ni][nj] != 1) continue;
                    a[ni][nj] = 0;
                    stack.push_back({ni, nj});
                }
            }
        }
    }
    cout << islands << '\\n';
    return 0;
}
"""

ISLANDS_PY = """
import sys

data = sys.stdin.read().split()
r, c = int(data[0]), int(data[1])
grid = [[int(data[2 + i * c + j]) for j in range(c)] for i in range(r)]

islands = 0
for si in range(r):
    for sj in range(c):
        if grid[si][sj] != 1:
            continue
        islands += 1
        grid[si][sj] = 0
        stack = [(si, sj)]
        while stack:
            i, j = stack.pop()
            for ni, nj in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                if 0 <= ni < r and 0 <= nj < c and grid[ni][nj] == 1:
                    grid[ni][nj] = 0
                    stack.append((ni, nj))
print(islands)
"""

# --------------------------------------------------------------------------- #
#  Pacific Atlantic Water Flow                                                #
# --------------------------------------------------------------------------- #

PACIFIC_CPP = """
#include <iostream>
#include <vector>
using namespace std;

int r, c;
vector<vector<int>> a;

void flood(vector<vector<char>>& seen, vector<pair<int, int>> stack) {
    for (auto [i, j] : stack) seen[i][j] = 1;
    while (!stack.empty()) {
        auto [i, j] = stack.back();
        stack.pop_back();
        int di[] = {-1, 1, 0, 0};
        int dj[] = {0, 0, -1, 1};
        for (int d = 0; d < 4; d++) {
            int ni = i + di[d], nj = j + dj[d];
            if (ni < 0 || ni >= r || nj < 0 || nj >= c) continue;
            if (seen[ni][nj] || a[ni][nj] < a[i][j]) continue;
            seen[ni][nj] = 1;
            stack.push_back({ni, nj});
        }
    }
}

int main() {
    cin >> r >> c;
    a.assign(r, vector<int>(c));
    for (int i = 0; i < r; i++)
        for (int j = 0; j < c; j++)
            cin >> a[i][j];

    vector<vector<char>> pac(r, vector<char>(c, 0)), atl(r, vector<char>(c, 0));
    vector<pair<int, int>> pacStart, atlStart;
    for (int j = 0; j < c; j++) { pacStart.push_back({0, j}); atlStart.push_back({r - 1, j}); }
    for (int i = 0; i < r; i++) { pacStart.push_back({i, 0}); atlStart.push_back({i, c - 1}); }
    flood(pac, pacStart);
    flood(atl, atlStart);

    int total = 0;
    for (int i = 0; i < r; i++)
        for (int j = 0; j < c; j++)
            if (pac[i][j] && atl[i][j]) total++;
    cout << total << '\\n';
    return 0;
}
"""

PACIFIC_PY = """
import sys

data = sys.stdin.read().split()
r, c = int(data[0]), int(data[1])
grid = [[int(data[2 + i * c + j]) for j in range(c)] for i in range(r)]


def flood(starts):
    seen = [[False] * c for _ in range(r)]
    stack = []
    for i, j in starts:
        if not seen[i][j]:
            seen[i][j] = True
            stack.append((i, j))
    while stack:
        i, j = stack.pop()
        for ni, nj in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
            if 0 <= ni < r and 0 <= nj < c and not seen[ni][nj]:
                if grid[ni][nj] >= grid[i][j]:
                    seen[ni][nj] = True
                    stack.append((ni, nj))
    return seen


pacific = flood([(0, j) for j in range(c)] + [(i, 0) for i in range(r)])
atlantic = flood([(r - 1, j) for j in range(c)] + [(i, c - 1) for i in range(r)])
print(sum(1 for i in range(r) for j in range(c) if pacific[i][j] and atlantic[i][j]))
"""


NATURAL_SOLUTIONS: dict[str, dict[str, str]] = {
    "b75-spiral-matrix": {"cpp": SPIRAL_CPP, "python": SPIRAL_PY},
    "b75-rotate-image": {"cpp": ROTATE_CPP, "python": ROTATE_PY},
    "b75-set-matrix-zeroes": {"cpp": ZEROES_CPP, "python": ZEROES_PY},
    "b75-number-of-islands": {"cpp": ISLANDS_CPP, "python": ISLANDS_PY},
    "b75-pacific-atlantic-water-flow": {"cpp": PACIFIC_CPP, "python": PACIFIC_PY},
}


def _judge_cases(bank: dict, slug: str) -> list[TestCase]:
    return [
        TestCase(
            name=case["name"],
            stdin=case["stdin"],
            expected_stdout=case["expected_stdout"],
            hidden=case["hidden"],
            match=case.get("match", "trimmed"),
        )
        for case in bank[slug]["cases"]
    ]


def main() -> int:
    bank = json.loads(GENERATED_CASES_PATH.read_text())
    problems = {p["slug"]: p for p in PROBLEMS}
    provider = LocalSubprocessProvider()
    failures: list[str] = []

    for slug, solutions in NATURAL_SOLUTIONS.items():
        problem = problems[slug]
        cases = _judge_cases(bank, slug)
        print(f"\n{slug}  ({len(cases)} cases)")
        print(f"  stated format: {problem['input_format'].splitlines()[0]}")

        for language, source in solutions.items():
            result = asyncio.run(provider.run(language, source.lstrip(), cases))
            if result.compile_error:
                failures.append(f"{slug}/{language}: compile error")
                print(f"  {language:8} COMPILE ERROR\n{result.compile_error[:600]}")
                continue
            failed = [r for r in result.results if not r.passed]
            status = "PASS" if not failed else "FAIL"
            print(
                f"  {language:8} {status}  "
                f"{len(result.results) - len(failed)}/{len(result.results)} cases"
            )
            for r in failed:
                failures.append(f"{slug}/{language}: case '{r.name}' failed")
                print(
                    f"      x {r.name}: expected {(r.expected_stdout or '')[:60]!r} "
                    f"got {r.stdout[:60]!r}  {r.stderr.strip()[:120]}"
                )

        # The suite must still reject the known-broken solutions.
        for index, wrong in enumerate(problem["wrong"], start=1):
            result = asyncio.run(provider.run("python", wrong, cases))
            rejected = [r for r in result.results if not r.passed]
            if rejected:
                print(f"  wrong #{index} still rejected by '{rejected[0].name}'")
            else:
                failures.append(f"{slug}: wrong solution #{index} now passes everything")
                print(f"  wrong #{index} PASSES EVERY CASE — the suite has been weakened")

    print()
    if failures:
        print(f"FAIL ({len(failures)})")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("OK every naturally-written solution passes and every wrong solution fails")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
