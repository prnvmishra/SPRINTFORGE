# TypeScript on the platform

TypeScript is a first-class judged language: it has a label, generated and
hand-written starters, a `tsc --strict` compile-and-run path in the judge,
Monaco syntax highlighting, and a twelve-problem basics curriculum.

## How it compiles in the judge, and the trade-off

`LANGUAGE_SPECS["typescript"]` in `app/services/code_execution_service.py`
declares `main.ts`, a compile step and a run step. Both are placeholders:
`resolve_commands` rewrites them into absolute paths, because neither `tsc` nor
(on a machine using nvm) `node` can be assumed to be on the PATH the service
inherits. This follows the Java precedent exactly — `/usr/bin/java` on macOS is
a stub that exists on `PATH` and cannot run anything, so `shutil.which` is not
proof of a toolchain — and `_typescript_toolchain()` therefore validates its
candidates by *running* them, just as `_java_bin_dir()` does.

TypeScript is a **backend-managed dependency**. `backend/package.json` pins
`typescript` and `@types/node`; `cd backend && npm install` puts them in
`backend/node_modules`, and that copy is the first candidate the judge looks
for. The frontend's copy is accepted as a fallback so a dev who installed one
but not the other is not blocked. A global `tsc` is deliberately *not* a
candidate: it carries no `@types/node`, and reading stdin means touching
`require`, so a global compiler would fail every submission with a diagnostic
about the starter rather than about the host.

The compiler is invoked as `node <typescript>/bin/tsc`, not through
`node_modules/.bin/tsc`. That shim is a `#!/usr/bin/env node` script, so running
it would reintroduce the PATH assumption the resolution exists to remove.

### Full type-checking, not transpile-only

The flags are `--strict --noEmitOnError --target es2020 --module commonjs --lib
es2020 --skipLibCheck --types node --typeRoots <backend>/node_modules/@types`.

The alternative was transpile-only: erase the types, emit JavaScript, never
reject a submission for a type error. It is roughly seven times faster (~200ms
against ~1.4s) and it would have been the cheaper integration.

It was rejected. On a platform whose entire reason to teach TypeScript is the
type system, **a solution with a type error is a wrong solution**. Passing it
would teach the learner that annotations are decoration — which is the opposite
of the lesson. `--noEmitOnError` means a type error produces no `main.js` at
all, `tsc` exits non-zero, and the judge reports it as a compile error with
`tsc`'s own diagnostic. `ExecutionResult.all_passed` requires at least one case
to have run, so a submission that did not compile cannot be recorded as a pass.

`scripts/verify_typescript.py` makes this testable rather than incidental: it
submits a program whose *runtime* behaviour is exactly correct and whose types
are wrong, and asserts it is rejected — then submits the honestly annotated
version of the same program and asserts it passes, so the check cannot pass for
the wrong reason.

The cost is accepted and paid where it belongs: compilation has its own budget
(`time_limit * 3`), and the type-check runs once per submission rather than once
per test case.

### When the toolchain is missing

`LocalSubprocessProvider.run` checks `_typescript_toolchain()` before doing
anything else and returns `supported=False` with
`TYPESCRIPT_UNAVAILABLE` — "TypeScript toolchain unavailable: … Install the
backend-managed compiler with `cd backend && npm install` …". No cases are run,
so no case is marked failed. A broken host must never be recorded as a learner's
wrong answer, and `verify_typescript.py` proves this by hiding the toolchain and
asserting the shape of the result.

## The basics curriculum

`app/data/curriculum_basics_typescript.py` holds twelve problems, wired into
`PRACTICE_MODULES` the way the Blind 75 batches are. Each one is chosen because
a *type* feature is the natural way to solve it:

| id | concept |
| --- | --- |
| `ts-basics-annotate-totals` | type annotations |
| `ts-basics-interface-order-lines` | interfaces |
| `ts-basics-union-status-tally` | type aliases, unions of string literals |
| `ts-basics-optional-default-params` | optional and default parameters |
| `ts-basics-tuple-bounds` | arrays vs tuples |
| `ts-basics-generic-dedupe` | generics |
| `ts-basics-unknown-narrowing` | `unknown` vs `any`, `typeof` narrowing |
| `ts-basics-enum-weekday` | enums |
| `ts-basics-record-standings` | typed object manipulation, `Record` |
| `ts-basics-discriminated-shapes` | discriminated unions |
| `ts-basics-type-guard-users` | user-defined type guards |
| `ts-basics-keyof-pluck` | `keyof` and indexed access types |

Expectations are derived at import time by running a Python `oracle`, never
hand-typed. Python rather than the TypeScript reference because deriving
expectations must not require a Node toolchain to *import the app* — but the two
are proven to agree, case for case, by `verify_typescript.py`.

Verify with:

```bash
cd backend
PYTHONPATH=. .venv/bin/python scripts/verify_typescript.py
```

## Why Blind 75 was not expanded into TypeScript

It was considered and rejected, deliberately and completely — the alternative
was a half-expansion, which is worse than either choice.

1. **It would teach nothing about TypeScript.** The `io` spec that generates
   competitive-programming starters knows three types: `int`, `long` and
   `string`. A TypeScript rendering of `two-sum` is therefore the JavaScript
   rendering with `: number[]` added to the plumbing. No interface, no union, no
   generic, no narrowing — nothing the language exists for. The twelve problems
   above teach TypeScript; a TypeScript Blind 75 would only teach that
   TypeScript exists.
2. **The judge contract could not be honoured.** `scripts/verify_languages.py`
   requires a registered known-correct solution per (problem, language), and the
   catalogue is ~135 problems. Shipping them without those solutions would mean
   ~135 modules whose reference has never been run — exactly the unverified
   surface that produces false passes, and exactly what this codebase has been
   burned by before.

So `curriculum_starters.LANGUAGES` — the expansion matrix — is unchanged, and
`curriculum.LANGUAGE_LABELS` with it. TypeScript still has an algorithm problem
against the same case bank as the other five languages (`ts-array-rotate`,
verified by `verify_typescript.py`), so the language is exercised on
stdin/stdout algorithm work and not only on type lessons.

The door is left open rather than nailed shut: `curriculum_starters.py` has a
real `_typescript` generator registered in `_GENERATORS` and reachable through
`build_starter(problem, "typescript")`, and `GENERATED_LANGUAGES` names it. If
someone later commits to authoring and verifying the reference solutions, adding
`"typescript"` to `LANGUAGES` is the whole change.
