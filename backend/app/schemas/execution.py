from typing import Optional

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    name: str
    stdin: str = ""
    expected_stdout: str = ""
    hidden: bool = False
    match: str = "trimmed"  # "trimmed" | "exact" | "tokens"


class ExecutionCaseResult(BaseModel):
    name: str
    passed: bool
    hidden: bool = False
    stdout: str = ""
    stderr: str = ""
    expected_stdout: Optional[str] = None
    exit_code: Optional[int] = None
    duration_ms: int = 0
    timed_out: bool = False


class ExecutionResult(BaseModel):
    provider: str
    language: str
    supported: bool = True
    compile_error: Optional[str] = None
    results: list[ExecutionCaseResult] = Field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def all_passed(self) -> bool:
        return self.total_count > 0 and self.passed_count == self.total_count

    def combined_stderr(self) -> str:
        if self.compile_error:
            return self.compile_error
        return "\n".join(r.stderr for r in self.results if r.stderr).strip()
