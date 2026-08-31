"""Known-correct solutions for the language-fundamentals problems.

Used only by ``scripts/verify_basics.py``; never imported by the app, so there
is no path by which one of these could be served to a learner.

Unlike ``language_solutions.py``, which stores each solution as a whole file,
these are stored as *bodies*. Every fundamentals problem is offered in exactly
one language, and a solution is the generated starter for that language with
its TODO replaced by the algorithm. Keeping only the body means the I/O
plumbing under test is the plumbing the learner is actually handed — if the
generator changes how it reads stdin, these solutions change with it instead of
drifting into a copy that no longer resembles the starter.

A `prelude` is source inserted immediately above the function: a `struct`, a
nested class, or the helper that a pointer/reference problem exists to teach.
"""

from __future__ import annotations

from typing import Any

from app.data.curriculum_starters import build_starters

# --------------------------------------------------------------------------- #
#  C                                                                          #
# --------------------------------------------------------------------------- #

_C: dict[str, Any] = {
    "basics-c-sum-two": "    return a + b;",
    "basics-c-truncated-mean": """
    long long total = 0;
    for (int i = 0; i < n; i++) {
        total += arr[i];
    }
    return total / n;
""",
    "basics-c-bitwise-trio": '    printf("%lld %lld %lld\\n", a & b, a | b, a ^ b);',
    "basics-c-leap-year": (
        "    return (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)) ? 1 : 0;"
    ),
    "basics-c-multiples-sum": """
    long long total = 0;
    for (int i = 1; i < n; i++) {
        if (i % 3 == 0 || i % 5 == 0) {
            total += i;
        }
    }
    return total;
""",
    "basics-c-fibonacci": """
    long long a = 1;
    long long b = 1;
    for (int i = 1; i < n; i++) {
        long long next = a + b;
        a = b;
        b = next;
    }
    return a;
""",
    "basics-c-reverse-string": """
    size_t len = strlen(s);
    for (size_t i = len; i > 0; i--) {
        putchar(s[i - 1]);
    }
    putchar('\\n');
""",
    "basics-c-count-vowels": """
    int count = 0;
    for (size_t i = 0; s[i] != '\\0'; i++) {
        if (strchr("aeiouAEIOU", s[i]) != NULL) {
            count++;
        }
    }
    return count;
""",
    "basics-c-second-largest": """
    long long best = arr[0];
    long long second = 0;
    int have_second = 0;
    for (int i = 1; i < n; i++) {
        long long v = arr[i];
        if (v > best) {
            second = best;
            have_second = 1;
            best = v;
        } else if (v != best && (!have_second || v > second)) {
            second = v;
            have_second = 1;
        }
    }
    return have_second ? second : best;
""",
    "basics-c-matrix-transpose": """
    (void)k;
    for (int j = 0; j < c; j++) {
        for (int i = 0; i < r; i++) {
            printf("%lld%c", grid[i * c + j], i + 1 == r ? '\\n' : ' ');
        }
    }
""",
    "basics-c-max-row-sum": """
    (void)k;
    long long best = 0;
    for (int i = 0; i < r; i++) {
        long long total = 0;
        for (int j = 0; j < c; j++) {
            total += grid[i * c + j];
        }
        if (i == 0 || total > best) {
            best = total;
        }
    }
    return best;
""",
    "basics-c-top-scorer": {
        "prelude": """
struct Student {
    long long id;
    long long score;
};
""",
        "body": """
    struct Student best;
    best.id = ids[0];
    best.score = scores[0];
    for (int i = 1; i < n; i++) {
        struct Student current;
        current.id = ids[i];
        current.score = scores[i];
        if (current.score > best.score
            || (current.score == best.score && current.id < best.id)) {
            best = current;
        }
    }
    return best.id;
""",
    },
    "basics-c-pointer-stride": """
    long long total = 0;
    for (int i = 0; i < n; i += s) {
        total += *(arr + i);
    }
    return total;
""",
    "basics-c-dynamic-filter": """
    long long* kept = (long long*)malloc((size_t)(n > 0 ? n : 1) * sizeof(long long));
    int count = 0;
    for (int i = 0; i < n; i++) {
        if (arr[i] > x) {
            kept[count++] = arr[i];
        }
    }
    printf("%d\\n", count);
    for (int i = 0; i < count; i++) {
        printf("%lld%c", kept[i], i + 1 == count ? '\\n' : ' ');
    }
    free(kept);
""",
    "basics-c-sort-three": {
        "prelude": """
static void swap_values(long long* x, long long* y) {
    long long tmp = *x;
    *x = *y;
    *y = tmp;
}
""",
        "body": """
    if (a > b) swap_values(&a, &b);
    if (b > c) swap_values(&b, &c);
    if (a > b) swap_values(&a, &b);
    printf("%lld %lld %lld\\n", a, b, c);
""",
    },
}


# --------------------------------------------------------------------------- #
#  C++                                                                        #
# --------------------------------------------------------------------------- #

_CPP: dict[str, Any] = {
    "basics-cpp-sum-two": "    return a + b;",
    "basics-cpp-truncated-mean": """
    long long total = 0;
    for (long long value : arr) {
        total += value;
    }
    return total / static_cast<long long>(arr.size());
""",
    "basics-cpp-bitwise-trio": (
        '    std::cout << (a & b) << " " << (a | b) << " " << (a ^ b) << "\\n";'
    ),
    "basics-cpp-leap-year": (
        "    return (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)) ? 1 : 0;"
    ),
    "basics-cpp-multiples-sum": """
    long long total = 0;
    for (int i = 1; i < n; i++) {
        if (i % 3 == 0 || i % 5 == 0) {
            total += i;
        }
    }
    return total;
""",
    "basics-cpp-fibonacci": """
    long long a = 1;
    long long b = 1;
    for (int i = 1; i < n; i++) {
        long long next = a + b;
        a = b;
        b = next;
    }
    return a;
""",
    "basics-cpp-reverse-string": """
    std::string out = s;
    std::reverse(out.begin(), out.end());
    std::cout << out << "\\n";
""",
    "basics-cpp-count-vowels": """
    const std::string vowels = "aeiouAEIOU";
    int count = 0;
    for (char ch : s) {
        if (vowels.find(ch) != std::string::npos) {
            count++;
        }
    }
    return count;
""",
    "basics-cpp-second-largest": """
    long long best = arr[0];
    long long second = 0;
    bool haveSecond = false;
    for (size_t i = 1; i < arr.size(); i++) {
        long long v = arr[i];
        if (v > best) {
            second = best;
            haveSecond = true;
            best = v;
        } else if (v != best && (!haveSecond || v > second)) {
            second = v;
            haveSecond = true;
        }
    }
    return haveSecond ? second : best;
""",
    "basics-cpp-matrix-transpose": """
    for (int j = 0; j < c; j++) {
        for (int i = 0; i < r; i++) {
            std::cout << grid[i * c + j] << (i + 1 == r ? '\\n' : ' ');
        }
    }
""",
    "basics-cpp-max-row-sum": """
    long long best = 0;
    for (int i = 0; i < r; i++) {
        long long total = 0;
        for (int j = 0; j < c; j++) {
            total += grid[i * c + j];
        }
        if (i == 0 || total > best) {
            best = total;
        }
    }
    return best;
""",
    "basics-cpp-top-scorer": {
        "prelude": """
struct Student {
    long long id;
    long long score;
};
""",
        "body": """
    std::vector<Student> students;
    students.reserve(ids.size());
    for (size_t i = 0; i < ids.size(); i++) {
        students.push_back(Student{ids[i], scores[i]});
    }
    Student best = students[0];
    for (const Student& current : students) {
        if (current.score > best.score
            || (current.score == best.score && current.id < best.id)) {
            best = current;
        }
    }
    return best.id;
""",
    },
    "basics-cpp-pointer-stride": """
    long long total = 0;
    const long long* base = arr.data();
    const int n = static_cast<int>(arr.size());
    for (int i = 0; i < n; i += s) {
        total += *(base + i);
    }
    return total;
""",
    "basics-cpp-dynamic-filter": """
    std::vector<long long> kept;
    for (long long value : arr) {
        if (value > x) {
            kept.push_back(value);
        }
    }
    std::cout << kept.size() << "\\n";
    for (size_t i = 0; i < kept.size(); i++) {
        std::cout << kept[i] << (i + 1 == kept.size() ? '\\n' : ' ');
    }
""",
    "basics-cpp-minmax-refs": {
        "prelude": """
static void findMinMax(const std::vector<long long>& values, long long& lo, long long& hi) {
    lo = values[0];
    hi = values[0];
    for (long long value : values) {
        if (value < lo) lo = value;
        if (value > hi) hi = value;
    }
}
""",
        "body": """
    long long lo = 0;
    long long hi = 0;
    findMinMax(arr, lo, hi);
    std::cout << lo << " " << hi << "\\n";
""",
    },
}


# --------------------------------------------------------------------------- #
#  Java                                                                       #
# --------------------------------------------------------------------------- #

_JAVA: dict[str, Any] = {
    "basics-java-sum-two": "        return a + b;",
    "basics-java-truncated-mean": """
        long total = 0;
        for (long value : arr) {
            total += value;
        }
        return total / arr.length;
""",
    "basics-java-bitwise-trio": (
        '        System.out.println((a & b) + " " + (a | b) + " " + (a ^ b));'
    ),
    "basics-java-leap-year": (
        "        return (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)) ? 1 : 0;"
    ),
    "basics-java-multiples-sum": """
        long total = 0;
        for (int i = 1; i < n; i++) {
            if (i % 3 == 0 || i % 5 == 0) {
                total += i;
            }
        }
        return total;
""",
    "basics-java-fibonacci": """
        long a = 1;
        long b = 1;
        for (int i = 1; i < n; i++) {
            long next = a + b;
            a = b;
            b = next;
        }
        return a;
""",
    "basics-java-reverse-string": (
        "        System.out.println(new StringBuilder(s).reverse().toString());"
    ),
    "basics-java-count-vowels": """
        int count = 0;
        for (int i = 0; i < s.length(); i++) {
            if ("aeiouAEIOU".indexOf(s.charAt(i)) >= 0) {
                count++;
            }
        }
        return count;
""",
    "basics-java-second-largest": """
        long best = arr[0];
        long second = 0;
        boolean haveSecond = false;
        for (int i = 1; i < arr.length; i++) {
            long v = arr[i];
            if (v > best) {
                second = best;
                haveSecond = true;
                best = v;
            } else if (v != best && (!haveSecond || v > second)) {
                second = v;
                haveSecond = true;
            }
        }
        return haveSecond ? second : best;
""",
    "basics-java-matrix-transpose": """
        StringBuilder sb = new StringBuilder();
        for (int j = 0; j < c; j++) {
            for (int i = 0; i < r; i++) {
                sb.append(grid[i * c + j]);
                sb.append(i + 1 == r ? '\\n' : ' ');
            }
        }
        System.out.print(sb);
""",
    "basics-java-max-row-sum": """
        long best = 0;
        for (int i = 0; i < r; i++) {
            long total = 0;
            for (int j = 0; j < c; j++) {
                total += grid[i * c + j];
            }
            if (i == 0 || total > best) {
                best = total;
            }
        }
        return best;
""",
    "basics-java-top-scorer": {
        "prelude": """
    static final class Student {
        final long id;
        final long score;

        Student(long id, long score) {
            this.id = id;
            this.score = score;
        }
    }
""",
        "body": """
        Student best = new Student(ids[0], scores[0]);
        for (int i = 1; i < ids.length; i++) {
            Student current = new Student(ids[i], scores[i]);
            if (current.score > best.score
                    || (current.score == best.score && current.id < best.id)) {
                best = current;
            }
        }
        return best.id;
""",
    },
    "basics-java-reverse-words": """
        String[] words = s.split(" ");
        StringBuilder sb = new StringBuilder();
        for (int i = words.length - 1; i >= 0; i--) {
            sb.append(words[i]);
            if (i > 0) {
                sb.append(' ');
            }
        }
        System.out.println(sb.toString());
""",
    "basics-java-case-counts": """
        int upper = 0;
        int lower = 0;
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (ch >= 'A' && ch <= 'Z') {
                upper++;
            } else if (ch >= 'a' && ch <= 'z') {
                lower++;
            }
        }
        System.out.println(upper + " " + lower);
""",
    "basics-java-distinct-in-order": """
        HashSet<Long> seen = new HashSet<>();
        ArrayList<Long> order = new ArrayList<>();
        for (long value : arr) {
            if (seen.add(value)) {
                order.add(value);
            }
        }
        StringBuilder sb = new StringBuilder();
        sb.append(order.size()).append('\\n');
        for (int i = 0; i < order.size(); i++) {
            sb.append(order.get(i));
            if (i + 1 < order.size()) {
                sb.append(' ');
            }
        }
        sb.append('\\n');
        System.out.print(sb);
""",
}


# --------------------------------------------------------------------------- #
#  Python                                                                     #
# --------------------------------------------------------------------------- #

_PYTHON: dict[str, Any] = {
    "basics-py-sum-two": "    return a + b",
    "basics-py-truncated-mean": """
    total = sum(arr)
    magnitude = abs(total) // len(arr)
    return magnitude if total >= 0 else -magnitude
""",
    "basics-py-bitwise-trio": "    print(a & b, a | b, a ^ b)",
    "basics-py-leap-year": (
        "    return 1 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 0"
    ),
    "basics-py-multiples-sum": (
        "    return sum(v for v in range(1, n) if v % 3 == 0 or v % 5 == 0)"
    ),
    "basics-py-fibonacci": """
    a, b = 1, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return a
""",
    "basics-py-reverse-string": "    print(s[::-1])",
    "basics-py-count-vowels": '    return sum(1 for ch in s if ch in "aeiouAEIOU")',
    "basics-py-second-largest": """
    distinct = sorted(set(arr), reverse=True)
    return distinct[1] if len(distinct) >= 2 else distinct[0]
""",
    "basics-py-matrix-transpose": """
    for j in range(c):
        print(" ".join(str(grid[i * c + j]) for i in range(r)))
""",
    "basics-py-max-row-sum": (
        "    return max(sum(grid[i * c:i * c + c]) for i in range(r))"
    ),
    "basics-py-slice-halves": """
    print(s[::2])
    print(s[1::2])
""",
    "basics-py-squares-of-evens": "    return sum(v * v for v in arr if v % 2 == 0)",
    "basics-py-mode-value": """
    counts = {}
    for value in arr:
        counts[value] = counts.get(value, 0) + 1
    return max(counts.items(), key=lambda item: (item[1], -item[0]))[0]
""",
    "basics-py-rotate-left": """
    shift = k % len(arr)
    print(" ".join(str(value) for value in arr[shift:] + arr[:shift]))
""",
}


BODIES: dict[str, Any] = {**_C, **_CPP, **_JAVA, **_PYTHON}

_PLACEHOLDERS = {"return 0;", "return 0", "pass"}


def _split(entry: Any) -> tuple[str, str]:
    if isinstance(entry, dict):
        return entry.get("prelude", ""), entry["body"]
    return "", entry


def solution_for(problem: dict[str, Any]) -> str:
    """The generated starter for this problem's language, with the TODO filled in.

    The TODO comment and the placeholder ``return 0`` it sits above are replaced
    by the body; the rest of the starter — every byte of the I/O plumbing the
    learner is given — is untouched.
    """
    slug = problem["slug"]
    entry = BODIES.get(slug)
    if entry is None:
        raise KeyError(f"no known-correct solution registered for {slug!r}")
    prelude, body = _split(entry)

    language = problem["languages"][0]
    lines = build_starters(problem)[language].split("\n")

    todo_index = next(i for i, line in enumerate(lines) if "TODO:" in line)
    end_index = todo_index + 1
    if end_index < len(lines) and lines[end_index].strip() in _PLACEHOLDERS:
        end_index += 1

    signature_index = todo_index - 1
    while signature_index > 0 and not lines[signature_index].strip():
        signature_index -= 1

    body_lines = body.strip("\n").split("\n")
    filled = lines[:todo_index] + body_lines + lines[end_index:]

    if prelude:
        prelude_lines = prelude.strip("\n").split("\n") + [""]
        filled = (
            filled[:signature_index] + prelude_lines + filled[signature_index:]
        )
    return "\n".join(filled)
