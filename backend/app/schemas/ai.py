from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class EvaluationRequest(BaseModel):
    skill_id: str
    skill_name: str
    task_context: str
    requirements: list[str] = Field(default_factory=list)
    user_submission: str
    language: str = "text"
    current_difficulty: int = Field(default=3, ge=1, le=10)
    deterministic_results: list[dict[str, Any]] = Field(default_factory=list)
    error_logs: Optional[str] = None
    expected_answer: Optional[str] = None


class EvaluationResult(BaseModel):
    """Strictly validated structured output from any AI provider."""

    is_correct: bool
    conceptual_mistake: Optional[str] = None
    next_difficulty: int = Field(default=3, ge=1, le=10)
    feedback: str
    missing_concepts: list[str] = Field(default_factory=list)
    suggested_remediation: Optional[str] = None
    provider: str = "mock"

    @field_validator("missing_concepts", mode="before")
    @classmethod
    def _coerce_concepts(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        return []

    @field_validator("next_difficulty", mode="before")
    @classmethod
    def _clamp_difficulty(cls, value: Any) -> int:
        try:
            number = int(round(float(value)))
        except (TypeError, ValueError):
            return 3
        return max(1, min(10, number))

    @field_validator("feedback", mode="before")
    @classmethod
    def _require_feedback(cls, value: Any) -> str:
        text = str(value or "").strip()
        return text or "Evaluation completed."


class MentorTurn(BaseModel):
    role: Literal["user", "mentor"]
    text: str


class MentorRequest(BaseModel):
    question: str
    skill_id: Optional[str] = None
    skill_name: Optional[str] = None
    task_context: Optional[str] = None
    user_code: Optional[str] = None
    language: str = "text"
    mode: Literal["hint", "concept", "debug"] = "hint"
    # Requirement labels the deterministic checks are currently failing. Hint-only
    # context, never used for grading, but it is what turns vague encouragement into
    # advice about the specific thing that is broken.
    failing_checks: list[str] = Field(default_factory=list)
    # Earlier turns so follow-up questions like "why?" resolve against real context.
    history: list[MentorTurn] = Field(default_factory=list)


class MentorResponse(BaseModel):
    answer: str
    next_step: Optional[str] = None
    guiding_questions: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    reveals_solution: bool = False
    provider: str = "mock"

    @field_validator("answer", mode="before")
    @classmethod
    def _require_answer(cls, value: Any) -> str:
        text = str(value or "").strip()
        return text or "Let's work through this together."

    @field_validator("guiding_questions", "concepts", mode="before")
    @classmethod
    def _coerce_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [part.strip() for part in value.split("|") if part.strip()]
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        return []
