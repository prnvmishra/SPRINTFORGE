"""Code execution provider abstraction.

CodeExecutionService
├── LocalSubprocessProvider  (development only, resource limited, no network)
├── PistonProvider           (https://github.com/engineer-man/piston)
└── Judge0Provider

Business logic and the frontend depend only on `CodeExecutionService`, never on a
specific provider, so swapping in a Docker/Judge0 sandbox for production is a
config change (CODE_EXECUTION_PROVIDER) and nothing else.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from functools import lru_cache
from glob import glob
from pathlib import Path
from typing import Optional

import httpx

from app.core.config import settings
from app.schemas.execution import ExecutionCaseResult, ExecutionResult, TestCase

logger = logging.getLogger(__name__)

LANGUAGE_SPECS: dict[str, dict[str, object]] = {
    "python": {"filename": "main.py", "run": [sys.executable, "main.py"], "piston": "python", "judge0": 71},
    "javascript": {"filename": "main.js", "run": ["node", "main.js"], "piston": "javascript", "judge0": 63},
    "java": {
        "filename": "Main.java",
        "compile": ["javac", "Main.java"],
        "run": ["java", "Main"],
        "piston": "java",
        "judge0": 62,
    },
    "c": {
        "filename": "main.c",
        "compile": ["cc", "main.c", "-o", "program", "-lm"],
        "run": ["./program"],
        "piston": "c",
        "judge0": 50,
    },
    "cpp": {
        "filename": "main.cpp",
        "compile": ["c++", "main.cpp", "-o", "program", "-std=c++17"],
        "run": ["./program"],
        "piston": "cpp",
        "judge0": 54,
    },
    # TypeScript is compiled by `tsc` and then run by node. Both entries are
    # placeholders: `resolve_commands` rewrites them into absolute paths, because
    # neither `tsc` nor (on a machine using nvm) `node` can be assumed to be on
    # the PATH the judge inherits. See `_typescript_toolchain`.
    "typescript": {
        "filename": "main.ts",
        "compile": ["tsc", "main.ts"],
        "run": ["node", "main.js"],
        "piston": "typescript",
        "judge0": 74,
    },
}

SUPPORTED_LANGUAGES = list(LANGUAGE_SPECS.keys())

# Hook for giving a language a larger wall clock than the configured base.
#
# It is intentionally EMPTY, and Java is the reason. JVM start-up was the
# expected problem, so it was measured on the largest curriculum case
# (n = 200000): a correct Java solution finishes in ~45ms end to end, i.e.
# start-up is noise against a 10s budget. Raising Java to 20s, meanwhile, was
# measured to let an O(n^2) Java solution finish the same case in ~16s — it
# would have turned a should-time-out submission into a pass. A false pass is
# worse than a language quirk, so Java keeps the base limit and start-up is
# absorbed where it actually costs something instead:
#   * compilation gets its own budget (base * 3 below), and javac needs ~0.5s;
#   * every generated Java starter ships a byte-level stdin reader, because
#     Scanner (not the JVM) is what actually blows the limit at n = 200000.
# Add an entry here only with a measurement showing the scale cases still
# reject a solution one complexity class too slow.
TIME_LIMIT_MULTIPLIER: dict[str, float] = {}


def time_limit_for(language: str) -> float:
    base = float(settings.EXECUTION_TIMEOUT_SECONDS)
    return base * TIME_LIMIT_MULTIPLIER.get(language, 1.0)


def _command_works(cmd: list[str]) -> bool:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


@lru_cache(maxsize=1)
def _java_bin_dir() -> Optional[str]:
    """Locate a JDK whose `java`/`javac` actually run.

    macOS ships stubs at /usr/bin/java and /usr/bin/javac that exist on PATH but
    exit with "Unable to locate a Java Runtime" when a JDK is not registered.
    `shutil.which` is therefore not enough: candidates are validated by running
    them, and the first working `bin` directory wins.
    """
    on_path = shutil.which("javac")
    if on_path and _command_works([on_path, "-version"]):
        java = shutil.which("java")
        if java and _command_works([java, "-version"]):
            return str(Path(on_path).parent)

    candidates: list[str] = []
    if os.environ.get("JAVA_HOME"):
        candidates.append(os.environ["JAVA_HOME"])
    try:
        proc = subprocess.run(
            ["/usr/libexec/java_home"], capture_output=True, text=True, timeout=20
        )
        if proc.returncode == 0 and proc.stdout.strip():
            candidates.append(proc.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    candidates += ["/opt/homebrew/opt/openjdk", "/usr/local/opt/openjdk", "/usr/lib/jvm/default"]
    candidates += sorted(glob("/Library/Java/JavaVirtualMachines/*/Contents/Home"), reverse=True)
    candidates += sorted(glob("/usr/lib/jvm/*"), reverse=True)

    for home in candidates:
        bin_dir = Path(home) / "bin"
        if (bin_dir / "javac").exists() and _command_works([str(bin_dir / "javac"), "-version"]):
            return str(bin_dir)
    return None


# --------------------------------------------------------------------------- #
#  TypeScript toolchain                                                       #
# --------------------------------------------------------------------------- #
# `tsc` is not on the PATH of a machine that only ever installed TypeScript as a
# project dependency, and `node` is often behind a version manager (nvm) whose
# shims are absent from the environment a service inherits. So, exactly as with
# the Java stub on macOS, presence on PATH is not proof: candidates are located
# explicitly and validated by *running* them.
#
# TypeScript is therefore a **backend-managed dependency**: `backend/package.json`
# pins it, `cd backend && npm install` puts it in `backend/node_modules`, and that
# copy is the first candidate. The frontend's copy is accepted only as a fallback
# so a dev who has installed one but not the other is not blocked, and a global
# `tsc` last.
#
# TRADE-OFF, deliberately chosen: submissions are FULLY TYPE-CHECKED
# (`--strict --noEmitOnError`), not transpiled with types erased. A
# transpile-only judge would run faster (~200ms instead of ~1.4s) and would never
# reject a submission for a type error, but on a platform whose whole reason to
# teach TypeScript is its type system, a solution with a type error is a wrong
# solution: shipping it as a pass would teach the learner that annotations are
# decoration. The cost is real and accepted — every TypeScript submission pays a
# full `tsc` invocation, which is why compilation gets its own budget
# (`time_limit * 3`) and the type-check runs once per submission rather than once
# per test case.
_TS_COMPILER_FLAGS = (
    "--strict",
    "--noEmitOnError",
    "--target",
    "es2020",
    "--module",
    "commonjs",
    "--lib",
    "es2020",
    # Learners read stdin, so `require`/`process`/`Buffer` must be typed. Those
    # types come from the pinned @types/node beside the pinned compiler, pointed
    # at by absolute path: the temp workdir the judge compiles in has no
    # node_modules of its own to resolve them from.
    "--skipLibCheck",
    "--types",
    "node",
)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_ROOT.parent

TYPESCRIPT_UNAVAILABLE = (
    "TypeScript toolchain unavailable: no working `tsc` and `node` pair was found. "
    "Install the backend-managed compiler with `cd backend && npm install`, or set "
    "CODE_EXECUTION_PROVIDER=piston to execute remotely. Submissions are not graded "
    "until the toolchain is present."
)


@lru_cache(maxsize=1)
def _node_bin() -> Optional[str]:
    """Absolute path to a `node` that actually runs, or None."""
    candidates: list[str] = []
    on_path = shutil.which("node")
    if on_path:
        candidates.append(on_path)
    if os.environ.get("NODE_BIN"):
        candidates.insert(0, os.environ["NODE_BIN"])
    candidates += ["/opt/homebrew/bin/node", "/usr/local/bin/node", "/usr/bin/node"]
    # nvm installs, newest first.
    candidates += sorted(
        glob(str(Path.home() / ".nvm/versions/node/*/bin/node")), reverse=True
    )
    for candidate in candidates:
        if Path(candidate).exists() and _command_works([candidate, "--version"]):
            return candidate
    return None


@lru_cache(maxsize=1)
def _typescript_toolchain() -> Optional[tuple[str, str, Optional[str]]]:
    """Return (node, tsc entry point, typeRoots) for a compiler that actually runs.

    The compiler is invoked as `node <typescript>/bin/tsc` rather than through
    `node_modules/.bin/tsc`: that shim is a `#!/usr/bin/env node` script, so
    running it would reintroduce the PATH assumption this function exists to
    remove. Going through an explicit `node` pins both halves of the toolchain.

    A candidate must also ship `@types/node`, because reading stdin means
    touching `require`, and an install without the types would fail every
    submission with an error about the starter rather than about the host. A
    global `tsc` is deliberately not a candidate for the same reason: it carries
    no types, and it is the least reproducible option available.
    """
    node = _node_bin()
    if node is None:
        return None

    for root in (_BACKEND_ROOT, _REPO_ROOT / "frontend", _REPO_ROOT):
        modules = root / "node_modules"
        entry = modules / "typescript" / "bin" / "tsc"
        node_types = modules / "@types" / "node"
        if not entry.exists() or not node_types.is_dir():
            continue
        if not _command_works([node, str(entry), "--version"]):
            continue
        return node, str(entry), str(modules / "@types")
    return None


def resolve_commands(language: str, spec: dict[str, object]) -> tuple[Optional[list[str]], list[str]]:
    """Return (compile_cmd, run_cmd) with interpreters resolved to real paths."""
    compile_cmd = list(spec["compile"]) if spec.get("compile") else None  # type: ignore[arg-type]
    run_cmd = list(spec["run"])  # type: ignore[arg-type]
    if language == "java":
        bin_dir = _java_bin_dir()
        if bin_dir:
            if compile_cmd:
                compile_cmd[0] = str(Path(bin_dir) / compile_cmd[0])
            run_cmd[0] = str(Path(bin_dir) / run_cmd[0])
    if language == "typescript":
        toolchain = _typescript_toolchain()
        if toolchain is None:
            # Left unresolved on purpose: the caller checks for an unresolvable
            # command and reports TYPESCRIPT_UNAVAILABLE. Substituting a plain
            # `tsc` here would surface as "compilation failed", i.e. as the
            # learner's mistake.
            return compile_cmd, run_cmd
        node, tsc, type_roots = toolchain
        flags = list(_TS_COMPILER_FLAGS)
        if type_roots:
            flags += ["--typeRoots", type_roots]
        compile_cmd = [node, tsc, *flags, str(spec["filename"])]
        run_cmd = [node, *run_cmd[1:]]
    return compile_cmd, run_cmd


def compare_output(actual: str, expected: str, match: str = "trimmed") -> bool:
    if match == "exact":
        return actual == expected
    if match == "tokens":
        return actual.split() == expected.split()
    return actual.strip().replace("\r\n", "\n") == expected.strip().replace("\r\n", "\n")


class CodeExecutionService(ABC):
    name: str = "base"

    @abstractmethod
    async def run(
        self, language: str, source_code: str, test_cases: list[TestCase]
    ) -> ExecutionResult: ...

    def _unsupported(self, language: str, message: str) -> ExecutionResult:
        return ExecutionResult(
            provider=self.name, language=language, supported=False, compile_error=message
        )


class LocalSubprocessProvider(CodeExecutionService):
    """Runs code in a throwaway temp dir with CPU/memory/time limits.

    This is a development convenience only. It is explicitly NOT a security
    boundary; production deployments should set CODE_EXECUTION_PROVIDER to
    `piston` or `judge0`, or run this service inside a locked-down container.
    """

    name = "local"

    def _preexec(self, cpu_seconds: float):  # pragma: no cover - POSIX only
        if os.name != "posix":
            return None

        def limit() -> None:
            import resource

            cpu = int(cpu_seconds) + 1
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
            resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
            resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))

        return limit

    async def run(
        self, language: str, source_code: str, test_cases: list[TestCase]
    ) -> ExecutionResult:
        language = language.lower()
        spec = LANGUAGE_SPECS.get(language)
        if not spec:
            return self._unsupported(language, f"Language '{language}' is not supported.")

        # A missing toolchain must never look like a wrong answer: report it as
        # unsupported so the learner sees "toolchain unavailable" and their
        # submission is not recorded as a failure.
        if language == "typescript" and _typescript_toolchain() is None:
            return self._unsupported(language, TYPESCRIPT_UNAVAILABLE)

        _, run_cmd = resolve_commands(language, spec)
        if (
            not Path(run_cmd[0]).is_absolute()
            and shutil.which(run_cmd[0]) is None
            and not run_cmd[0].startswith("./")
        ):
            return self._unsupported(
                language,
                f"Runtime '{run_cmd[0]}' is not installed on this host. "
                "Set CODE_EXECUTION_PROVIDER=piston to execute remotely.",
            )

        return await asyncio.to_thread(self._run_blocking, language, spec, source_code, test_cases)

    def _run_blocking(
        self,
        language: str,
        spec: dict[str, object],
        source_code: str,
        test_cases: list[TestCase],
    ) -> ExecutionResult:
        with tempfile.TemporaryDirectory(prefix="sprintforge-exec-") as workdir:
            path = Path(workdir) / str(spec["filename"])
            path.write_text(source_code, encoding="utf-8")

            env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": workdir}
            time_limit = time_limit_for(language)
            compile_cmd, run_cmd = resolve_commands(language, spec)

            if language == "typescript" and _typescript_toolchain() is None:
                return self._unsupported(language, TYPESCRIPT_UNAVAILABLE)

            if compile_cmd:
                if not Path(compile_cmd[0]).is_absolute() and shutil.which(compile_cmd[0]) is None:
                    return self._unsupported(
                        language,
                        f"Compiler '{compile_cmd[0]}' is not installed on this host.",
                    )
                try:
                    proc = subprocess.run(
                        compile_cmd,
                        cwd=workdir,
                        capture_output=True,
                        text=True,
                        timeout=time_limit * 3,
                        env=env,
                    )
                except subprocess.TimeoutExpired:
                    return ExecutionResult(
                        provider=self.name,
                        language=language,
                        compile_error="Compilation timed out.",
                    )
                if proc.returncode != 0:
                    return ExecutionResult(
                        provider=self.name,
                        language=language,
                        compile_error=(proc.stderr or proc.stdout or "Compilation failed.")[:4000],
                    )

            results: list[ExecutionCaseResult] = []
            for case in test_cases:
                started = time.perf_counter()
                timed_out = False
                stdout = stderr = ""
                exit_code: Optional[int] = None
                try:
                    proc = subprocess.run(
                        run_cmd,
                        cwd=workdir,
                        input=case.stdin,
                        capture_output=True,
                        text=True,
                        timeout=time_limit,
                        env=env,
                        preexec_fn=self._preexec(time_limit),
                    )
                    stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
                except subprocess.TimeoutExpired:
                    timed_out = True
                    stderr = f"Execution exceeded {time_limit}s time limit."
                except OSError as exc:  # pragma: no cover
                    stderr = f"Execution failed: {exc}"

                passed = (
                    not timed_out
                    and exit_code == 0
                    and compare_output(stdout, case.expected_stdout, case.match)
                )
                results.append(
                    ExecutionCaseResult(
                        name=case.name,
                        passed=passed,
                        hidden=case.hidden,
                        stdout="" if case.hidden else stdout[:4000],
                        stderr=stderr[:4000],
                        expected_stdout=None if case.hidden else case.expected_stdout,
                        exit_code=exit_code,
                        duration_ms=int((time.perf_counter() - started) * 1000),
                        timed_out=timed_out,
                    )
                )
            return ExecutionResult(provider=self.name, language=language, results=results)


class PistonProvider(CodeExecutionService):
    name = "piston"

    async def run(
        self, language: str, source_code: str, test_cases: list[TestCase]
    ) -> ExecutionResult:
        language = language.lower()
        spec = LANGUAGE_SPECS.get(language)
        if not spec:
            return self._unsupported(language, f"Language '{language}' is not supported.")

        results: list[ExecutionCaseResult] = []
        try:
            async with httpx.AsyncClient(timeout=settings.EXECUTION_TIMEOUT_SECONDS * 4) as client:
                for case in test_cases:
                    started = time.perf_counter()
                    response = await client.post(
                        f"{settings.PISTON_URL.rstrip('/')}/execute",
                        json={
                            "language": spec["piston"],
                            "version": "*",
                            "files": [{"name": str(spec["filename"]), "content": source_code}],
                            "stdin": case.stdin,
                            # Without this the remote host's default applies, so
                            # the scale cases stop gating complexity: an O(n^2)
                            # solution passes or fails on a stranger's timeout
                            # rather than the one the problem was measured for.
                            # Piston takes milliseconds.
                            "run_timeout": int(time_limit_for(language) * 1000),
                            "compile_timeout": int(time_limit_for(language) * 3 * 1000),
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                    compile_stage = payload.get("compile") or {}
                    if compile_stage.get("code"):
                        return ExecutionResult(
                            provider=self.name,
                            language=language,
                            compile_error=(compile_stage.get("stderr") or "Compilation failed.")[:4000],
                        )
                    run_stage = payload.get("run") or {}
                    stdout = run_stage.get("stdout", "")
                    exit_code = run_stage.get("code")
                    # Piston kills an over-running program with a signal and
                    # reports `code: null`, so the signal is the only evidence
                    # that the limit was hit rather than the program exiting.
                    timed_out = run_stage.get("signal") in ("SIGKILL", "SIGTERM")
                    passed = exit_code == 0 and compare_output(
                        stdout, case.expected_stdout, case.match
                    )
                    results.append(
                        ExecutionCaseResult(
                            name=case.name,
                            passed=passed,
                            hidden=case.hidden,
                            stdout="" if case.hidden else stdout[:4000],
                            stderr=(run_stage.get("stderr") or "")[:4000],
                            expected_stdout=None if case.hidden else case.expected_stdout,
                            exit_code=exit_code,
                            duration_ms=int((time.perf_counter() - started) * 1000),
                            timed_out=timed_out,
                        )
                    )
        except httpx.HTTPError as exc:
            return self._unsupported(language, f"Remote execution provider unavailable: {exc}")
        return ExecutionResult(provider=self.name, language=language, results=results)


class Judge0Provider(CodeExecutionService):
    name = "judge0"

    async def run(
        self, language: str, source_code: str, test_cases: list[TestCase]
    ) -> ExecutionResult:
        language = language.lower()
        spec = LANGUAGE_SPECS.get(language)
        if not spec:
            return self._unsupported(language, f"Language '{language}' is not supported.")
        if not settings.JUDGE0_API_KEY:
            return self._unsupported(language, "JUDGE0_API_KEY is not configured.")

        headers = {
            "X-RapidAPI-Key": settings.JUDGE0_API_KEY,
            "X-RapidAPI-Host": settings.JUDGE0_URL.replace("https://", "").replace("http://", ""),
            "Content-Type": "application/json",
        }
        results: list[ExecutionCaseResult] = []
        try:
            async with httpx.AsyncClient(timeout=settings.EXECUTION_TIMEOUT_SECONDS * 6) as client:
                for case in test_cases:
                    started = time.perf_counter()
                    response = await client.post(
                        f"{settings.JUDGE0_URL.rstrip('/')}/submissions",
                        params={"base64_encoded": "false", "wait": "true"},
                        headers=headers,
                        json={
                            "language_id": spec["judge0"],
                            "source_code": source_code,
                            "stdin": case.stdin,
                            "expected_output": case.expected_stdout,
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                    compile_output = payload.get("compile_output")
                    if compile_output:
                        return ExecutionResult(
                            provider=self.name,
                            language=language,
                            compile_error=compile_output[:4000],
                        )
                    stdout = payload.get("stdout") or ""
                    status_id = (payload.get("status") or {}).get("id")
                    # Judge0 status: 3 = Accepted, 4 = Wrong Answer. Those are the
                    # only two that mean the program ran to completion; everything
                    # else (5 = time limit, 6 = compile error, 11+ = runtime error)
                    # is a failure however much of the expected output reached
                    # stdout first. `or` here credited a timed-out or crashed
                    # submission whose partial output happened to match, which is
                    # exactly how an O(n^2) solution slips past a scale case.
                    # Our own comparator still decides between 3 and 4, because it
                    # honours the case's `match` mode (trimmed/tokens/exact) and
                    # Judge0's does not.
                    ran_to_completion = status_id in (3, 4)
                    passed = ran_to_completion and compare_output(
                        stdout, case.expected_stdout, case.match
                    )
                    results.append(
                        ExecutionCaseResult(
                            name=case.name,
                            passed=passed,
                            hidden=case.hidden,
                            stdout="" if case.hidden else stdout[:4000],
                            stderr=(payload.get("stderr") or "")[:4000],
                            expected_stdout=None if case.hidden else case.expected_stdout,
                            exit_code=0 if status_id == 3 else 1,
                            duration_ms=int((time.perf_counter() - started) * 1000),
                            # Status 5 is the time limit. Carrying it through means
                            # the learner is told they were too slow, rather than
                            # being shown a wrong-answer diff for output that was
                            # on its way to being correct.
                            timed_out=status_id == 5,
                        )
                    )
        except httpx.HTTPError as exc:
            return self._unsupported(language, f"Judge0 unavailable: {exc}")
        return ExecutionResult(provider=self.name, language=language, results=results)


_PROVIDERS: dict[str, type[CodeExecutionService]] = {
    "local": LocalSubprocessProvider,
    "piston": PistonProvider,
    "judge0": Judge0Provider,
}


def get_code_execution_service() -> CodeExecutionService:
    provider_cls = _PROVIDERS.get(settings.CODE_EXECUTION_PROVIDER.lower(), LocalSubprocessProvider)
    return provider_cls()
