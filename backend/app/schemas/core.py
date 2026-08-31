from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------ auth


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMModel):
    id: str
    name: str
    email: EmailStr
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    auth_provider: str
    is_onboarded: bool
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --------------------------------------------------------------- profile


class OnboardRequest(BaseModel):
    goal: str = Field(min_length=3, max_length=255)
    experience_level: str = "beginner"
    claimed_skills: dict[str, str] = Field(default_factory=dict)
    path_id: Optional[str] = Field(default=None, max_length=60)


class SkillOut(BaseModel):
    skill_id: str
    skill_name: str
    claimed_level: Optional[str] = None
    verified_level: str
    confidence: float
    needs_improvement: bool
    weak_concepts: list[str] = Field(default_factory=list)
    breakdown: dict[str, Any] = Field(default_factory=dict)
    # Jargon-free wording plus the one action to take, for the dashboard.
    plain_summary: Optional[str] = None
    next_action: dict[str, Any] = Field(default_factory=dict)
    explanation: str
    difficulty_weight: int
    evidence: dict[str, Any] = Field(default_factory=dict)


class DigitalTwinOut(BaseModel):
    user_id: str
    goal: Optional[str] = None
    experience_level: str
    claimed_skills: dict[str, Any] = Field(default_factory=dict)
    overall_confidence: float
    xp: int
    level: int
    streak_days: int
    consistency_score: float
    learning_velocity: float
    avg_completion_seconds: float
    preferred_difficulty: int
    completed_projects: int
    repeated_mistakes: dict[str, Any] = Field(default_factory=dict)
    active_project_id: Optional[str] = None
    active_ticket_id: Optional[str] = None
    path_id: Optional[str] = None
    placement_status: str = "pending"
    verified_skills: list[SkillOut] = Field(default_factory=list)
    skills_needing_improvement: list[SkillOut] = Field(default_factory=list)


# ------------------------------------------------------------ assessment


class AssessmentStartRequest(BaseModel):
    skill_id: str
    claimed_level: Optional[str] = None
    max_questions: int = Field(default=5, ge=1, le=15)
    # A placement probe is shorter and is recorded against the placement plan, so
    # its result can be read back as evidence for the starting point.
    placement: bool = False


class AssessmentQuestionOut(BaseModel):
    id: str
    skill_id: str
    type: str
    difficulty: int
    concept: Optional[str] = None
    prompt: str
    code: Optional[str] = None
    options: Optional[list[str]] = None
    language: str = "javascript"


class AssessmentStateOut(BaseModel):
    session_id: str
    skill_id: str
    status: str
    questions_asked: int
    max_questions: int
    correct_count: int
    current_difficulty: int
    question: Optional[AssessmentQuestionOut] = None
    result: Optional[dict[str, Any]] = None


class AssessmentSubmitRequest(BaseModel):
    session_id: str
    question_id: str
    answer: str
    duration_seconds: float = 0.0


class AssessmentSubmitResponse(BaseModel):
    is_correct: bool
    evaluation: dict[str, Any]
    state: AssessmentStateOut
    skill: dict[str, Any]
    failure_analysis: Optional[dict[str, Any]] = None


# -------------------------------------------------------------- practice


class PracticeRunRequest(BaseModel):
    files: dict[str, str] = Field(default_factory=dict)
    stdin: Optional[str] = None


class PracticeSubmitRequest(BaseModel):
    files: dict[str, str] = Field(default_factory=dict)
    duration_seconds: float = 0.0


# -------------------------------------------------------------- projects


class ProjectCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    idea: str = Field(min_length=10)
    tech_stack: list[str] = Field(min_length=1)
    known_technologies: list[str] = Field(default_factory=list)
    experience_level: str = "intermediate"
    complexity: str = "intermediate"
    desired_outcome: Optional[str] = None


class TicketFilesRequest(BaseModel):
    files: dict[str, str] = Field(default_factory=dict)
    duration_seconds: float = 0.0


# --------------------------------------------------------------- account


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    bio: Optional[str] = Field(default=None, max_length=280)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class AccountDeleteRequest(BaseModel):
    confirmation: str


# ----------------------------------------------------------- leaderboard


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    name: str
    avatar_url: Optional[str] = None
    score: float
    xp: int
    level: int
    verified_skills: int
    overall_confidence: float
    is_current_user: bool = False


class LeaderboardOut(BaseModel):
    entries: list[LeaderboardEntry] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
    confidence_threshold: float
    formula: dict[str, Any]
    current_user: Optional[LeaderboardEntry] = None


# ------------------------------------------------------------- community


class CommunityPostCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    parent_id: Optional[str] = None


class CommunityAuthor(BaseModel):
    id: str
    name: str
    avatar_url: Optional[str] = None


class CommunityPostOut(BaseModel):
    id: str
    module_id: str
    body: str
    created_at: datetime
    author: CommunityAuthor
    can_delete: bool
    parent_id: Optional[str] = None
    replies: list["CommunityPostOut"] = Field(default_factory=list)


# --------------------------------------------------------------- mentor


class MentorTurnBody(BaseModel):
    role: str
    text: str


class MentorRequestBody(BaseModel):
    question: str = Field(min_length=1)
    skill_id: Optional[str] = None
    ticket_id: Optional[str] = None
    module_id: Optional[str] = None
    user_code: Optional[str] = None
    mode: str = "hint"
    # Hint context only — the mentor never grades, so this cannot affect a verdict.
    failing_checks: list[str] = Field(default_factory=list)
    history: list[MentorTurnBody] = Field(default_factory=list)


class EvaluateRequestBody(BaseModel):
    skill_id: str
    task_context: str
    requirements: list[str] = Field(default_factory=list)
    user_submission: str
    language: str = "text"
    current_difficulty: int = 3
