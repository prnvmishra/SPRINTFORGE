from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

#: Kept as a constant so the production check compares against the same literal
#: the field defaults to, rather than a copy that can drift out of step.
UNSAFE_DEFAULT_AUTH_SECRET = "dev-only-insecure-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "SprintForge.AI"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "sqlite:///./sprintforge.db"

    AUTH_SECRET: str = UNSAFE_DEFAULT_AUTH_SECRET
    AUTH_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # "mock" | "openai" | "gemini"
    AI_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    # Any OpenAI-compatible endpoint works here (OpenAI, OpenRouter, Together, vLLM…).
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"
    AI_TIMEOUT_SECONDS: float = 30.0
    # Cap the completion length. Structured verdicts are small, and some gateways
    # (e.g. OpenRouter) reserve the model's *entire* context window when no cap is
    # sent, which rejects the request on low-balance accounts.
    AI_MAX_OUTPUT_TOKENS: int = 700

    # "local" | "piston" | "judge0" | "custom"
    CODE_EXECUTION_PROVIDER: str = "local"
    PISTON_URL: str = "https://emkc.org/api/v2/piston"
    JUDGE0_URL: str = "https://judge0-ce.p.rapidapi.com"
    JUDGE0_API_KEY: str = ""
    CUSTOM_EXECUTION_URL: str = ""
    CUSTOM_EXECUTION_API_KEY: str = ""
    EXECUTION_TIMEOUT_SECONDS: float = 10.0

    # Debugging aid for rendered checks: reports what the render sandbox
    # assembled — file names, the resolved entry document, and a content hash per
    # file. Never file bodies, and never anything about the checks themselves.
    # Off by default and ignored in production, so it cannot ship enabled.
    RENDER_ASSEMBLY_DEBUG: bool = False

    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    # Any localhost port is trusted in development so the Next dev server can
    # move ports without breaking the browser preflight.
    CORS_ORIGIN_REGEX: str = r"http://(localhost|127\.0\.0\.1)(:\d+)?"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def cors_origin_regex_effective(self) -> str:
        """The any-localhost allowance is a development convenience only.

        Left on in production it lets a page served from the deployer's own
        machine make credentialed calls to the live API, which is not something
        the origin list would otherwise permit.
        """
        return "" if self.is_production else self.CORS_ORIGIN_REGEX

    @property
    def sandboxed_execution(self) -> bool:
        """Whether learner code runs somewhere it cannot reach this process.

        `local` runs it as a subprocess of the API under the same user, which is
        fine on a laptop and unacceptable on a public host — it is arbitrary
        remote code execution by design. See `LocalSubprocessProvider`.
        
        `mock` is safe because it doesn't execute any code at all.
        """
        provider = self.CODE_EXECUTION_PROVIDER.lower()
        if provider in {"piston", "judge0", "mock"}:
            return True
        # Allow custom provider if API key is configured
        if provider == "custom" and self.CUSTOM_EXECUTION_API_KEY:
            return True
        return False

    def production_blockers(self) -> List[str]:
        """Settings that are safe in development and dangerous on a public host.

        Returned as a list rather than raising here so startup can report every
        problem at once instead of one per redeploy.
        """
        if not self.is_production:
            return []

        blockers: List[str] = []
        if self.AUTH_SECRET == UNSAFE_DEFAULT_AUTH_SECRET:
            blockers.append(
                "AUTH_SECRET is still the development default, so anyone who has "
                "read this repository can mint a token for any account. Set it to "
                "a long random value."
            )
        if not self.sandboxed_execution:
            blockers.append(
                f"CODE_EXECUTION_PROVIDER is '{self.CODE_EXECUTION_PROVIDER}', which "
                "runs learner-submitted code as this process. Set it to 'piston', 'judge0', "
                "or 'mock' before exposing the API."
            )
        if self.CODE_EXECUTION_PROVIDER.lower() == "judge0" and not self.JUDGE0_API_KEY:
            blockers.append("CODE_EXECUTION_PROVIDER is 'judge0' but JUDGE0_API_KEY is empty.")
        if self.DATABASE_URL.startswith("sqlite"):
            blockers.append(
                "DATABASE_URL is SQLite, which loses every learner's progress when "
                "the container restarts."
            )
        return blockers

    @property
    def render_assembly_debug_enabled(self) -> bool:
        """Both conditions, so a stray env var in production stays inert."""
        return bool(self.RENDER_ASSEMBLY_DEBUG) and self.ENVIRONMENT.lower() != "production"

    @property
    def ai_provider_effective(self) -> str:
        """Fall back to mock when the configured provider has no credentials."""
        provider = self.AI_PROVIDER.lower()
        if provider == "openai" and not self.OPENAI_API_KEY:
            return "mock"
        if provider == "gemini" and not self.GEMINI_API_KEY:
            return "mock"
        return provider


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
