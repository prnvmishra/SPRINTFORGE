# Authoring a curriculum problem

A problem is a dict in `app/data/curriculum_cp.py` (or a module imported into
`CP_PROBLEMS`). Define it once and it is expanded automatically into one
practice module per language — `python`, `javascript`, `java`, `cpp`, `c` —
with id `cp-<slug>-<language>`. Do not write starter code by hand.

TypeScript is a supported, judged language but is deliberately **not** in that
expansion matrix, and its curriculum is authored separately in
`app/data/curriculum_basics_typescript.py`. See `docs/typescript.md` for how it
compiles, why type errors fail a submission, and why Blind 75 was not expanded.

## Required keys

| Key | Meaning |
| --- | --- |
| `slug` | unique, kebab-case; becomes part of the module id |
| `skill_id` | must exist in the knowledge graph |
| `difficulty`, `estimated_minutes` | ints |
| `title`, `statement` | learner-facing |
| `constraints` | list of strings; **state the integer width when sums exceed 2^31** |
| `input_format`, `output_format` | exact stdin/stdout shape |
| `examples` | list of `{stdin, stdout, explanation}` — explanation must be non-empty |
| `criteria` | list of pass criteria |
| `io` | declarative I/O spec; starters are generated from it (see below) |
| `reference` | a **correct Python solution**. It is the only source of expected outputs and is never shipped to a client |
| `inputs` | list of `{name, stdin, hidden}`. Needs ≥1 visible and ≥1 hidden case, including a seeded scale case big enough that a solution one complexity class too slow times out |
| `wrong` | list of plausible-but-broken Python solutions. Each **must** be rejected by at least one case, or the build fails — this is what makes a false pass impossible |

## Restricting a problem to some languages

By default a problem is expanded into all five languages. A problem that teaches
a *language feature* rather than an algorithm declares which languages it
belongs to:

```python
"languages": ["c", "cpp"],       # pointer arithmetic has no Python rendering
```

Only those modules are emitted, and only those starters are generated. Use it
sparingly: an algorithmic problem restricted to one language is just a problem
missing from four catalogues. It exists so that
`app/data/curriculum_basics_*.py` can teach pointers in C, references in C++,
`ArrayList` in Java and comprehensions in Python without restating each as
something it is not, which is what filling five slots per problem would force.

The language-fundamentals sets share their task definitions through
`app/data/curriculum_basics_kit.py`: the progression (printing, types,
operators, conditionals, loops, functions, strings, 1-D arrays, matrices) is the
same in every language, so it is authored once and stamped out per language with
its own slug, skill and idiom hints.

## The `io` spec

```python
"io": {
    "mode": "tokens",           # "tokens" = whitespace-separated numbers, "line" = one raw line
    "function": "count_pairs",  # snake_case; camelCase is derived for JS/Java/C++
    "todo": "return the number of distinct value pairs (a, b) with a - b == d",
    "reads": [                  # in stdin order; "count" makes it an array
        {"name": "n", "type": "int"},
        {"name": "d", "type": "long"},
        {"name": "arr", "type": "long", "count": "n"},
    ],
    "args": ["arr", "d"],       # what the learner's function receives
    "returns": "long",          # "int", "long", or "void" when the answer is printed
},
```

`mode: "line"` takes exactly one `{"name": ..., "type": "string"}` read.
Anything more exotic than this belongs in a new generator in
`app/data/curriculum_starters.py`, not in a hand-written starter.

### Derived reads: never put a computed count on stdin

A read may carry `"value"` instead of being read from stdin, in which case it is
computed from the reads declared before it:

```python
"reads": [
    {"name": "r", "type": "int"},
    {"name": "c", "type": "int"},
    {"name": "k", "type": "int", "value": "r * c"},   # not on stdin
    {"name": "grid", "type": "int", "count": "k"},
],
```

The expression is arithmetic over earlier read names and is emitted verbatim in
all five languages, so it must be valid in all five (`r * c`, `n * n`, `n - 1`).
Referring forward is rejected at build time.

**Do not ask stdin for a count you can compute.** The five matrix problems used
to state their first line as `r c k` with `k = r * c`, purely because the
generator could not express a computed count. A learner who read `r` and `c` and
then went straight for the grid — the obvious reading — consumed `k` as the
first cell and had every value shifted by one, so a correct solution was
rejected with no hint as to why. A count belongs on stdin only when it is
genuinely load-bearing: a bare list with no preceding dimension needs its length
(`n` then `n` values), an edge count `m` is not implied by the vertex count `n`,
and a second list's length `m` is not implied by the first's.

### `returns: "void"` for problems whose answer is a sequence

If the task is to print several values or several lines, say `"void"`. The
generated function then returns nothing and `main` simply calls it. Declaring
such a problem `"int"` produces a starter like `int spiralMatrix(...)` for a
problem that must print `r * c` numbers, plus a `main` that prints the return
value alongside them — a signature the learner cannot satisfy.

## Regenerating and verifying

```bash
cd backend
PYTHONPATH=. .venv/bin/python -m scripts.build_test_cases   # rebuild generated_cases.json
PYTHONPATH=. .venv/bin/python scripts/verify_languages.py \
    --languages python javascript java cpp c                # solvable in every language
PYTHONPATH=. .venv/bin/python -m pytest -q
```

`build_test_cases.py` runs the reference over every input to *derive*
`expected_stdout`, runs it twice to catch non-determinism, and proves every
`wrong` solution is caught. Commit the regenerated `generated_cases.json`;
`test_generated_cases_are_up_to_date` fails if you forget.

For the language-fundamentals sets, `scripts/verify_basics.py` is the
equivalent, and goes further: it runs the reference *and every declared wrong
solution* through the real judge, asserting pass and fail respectively, then
proves each problem is solvable in its own language and that its starter is not.
Iterating on one batch does not need a seven-minute full rebuild:

```bash
PYTHONPATH=. .venv/bin/python -m scripts.build_test_cases --only basics-
PYTHONPATH=. .venv/bin/python scripts/verify_basics.py
```

`verify_languages.py` runs a known-correct solution (registered in
`scripts/language_solutions.py`) through the real judge against the full case
bank, and confirms the generated starter does **not** pass. Register a solution
there for any new problem.

## Traps found the hard way

- **Integer width.** `n <= 2e5` with `|arr[i]| <= 1e9` gives sums up to 2e14.
  The `max-subarray-sum` scale case answers `244875408525`, which silently
  wraps in a 32-bit `int`. Generated starters use `long long` (C/C++) and
  `long` (Java) for all numeric values; if your problem overflows, say so in
  `constraints` too.
- **Java I/O.** `Scanner` cannot read 200000 tokens inside the time limit.
  Generated Java starters ship a byte-level `FastReader`; keep using it.
- **Java time limit — do not raise it.** JVM start-up was measured at ~45ms on
  the largest case, i.e. irrelevant against the 10s budget, while a 20s limit
  was measured to let an O(n²) Java solution finish the same case in ~16s. Java
  therefore runs at the base limit. `TIME_LIMIT_MULTIPLIER` in
  `code_execution_service.py` exists for genuine cases; adding to it requires a
  measurement showing the scale cases still reject a too-slow solution.
- **Java toolchain on macOS.** `/usr/bin/java` is a stub that exists on `PATH`
  but cannot run anything, so `shutil.which` is not proof of a JDK. The
  executor validates candidates by running them (`_java_bin_dir`).
- **No `<bits/stdc++.h>`.** It does not exist on libc++/clang. C++ starters
  list their headers explicitly.
- **C has no array lengths.** Generated C signatures append the count variable
  (`int n`) after the array pointers.
