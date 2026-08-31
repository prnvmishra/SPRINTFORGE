"""The settings that are fine on a laptop and dangerous on a public host.

Each of these guards exists because the safe value and the convenient value are
different, and the convenient one is the default. A guard that silently stops
guarding is worse than no guard, so the behaviour is pinned here rather than
left to a code review to notice.
"""

from __future__ import annotations

import pytest

from app.core.config import UNSAFE_DEFAULT_AUTH_SECRET, Settings


def build(**overrides) -> Settings:
    """A production Settings with everything safe unless a test says otherwise."""
    base = {
        "ENVIRONMENT": "production",
        "AUTH_SECRET": "a-real-secret-of-considerable-length",
        "CODE_EXECUTION_PROVIDER": "piston",
        "DATABASE_URL": "postgresql+psycopg://user:pw@db.example.com/sprintforge",
    }
    base.update(overrides)
    return Settings(**base)


def test_a_correctly_configured_production_deploy_has_no_blockers():
    assert build().production_blockers() == []


def test_development_is_never_blocked():
    """The insecure defaults are the point in development; they must not stop it."""
    settings = Settings(
        ENVIRONMENT="development",
        AUTH_SECRET=UNSAFE_DEFAULT_AUTH_SECRET,
        CODE_EXECUTION_PROVIDER="local",
        DATABASE_URL="sqlite:///./sprintforge.db",
    )
    assert settings.production_blockers() == []


def test_the_default_auth_secret_blocks_production():
    """Otherwise anyone who has read the repository can mint a token."""
    blockers = build(AUTH_SECRET=UNSAFE_DEFAULT_AUTH_SECRET).production_blockers()
    assert any("AUTH_SECRET" in b for b in blockers)


def test_local_execution_blocks_production():
    """`local` runs learner-submitted code as the API process."""
    blockers = build(CODE_EXECUTION_PROVIDER="local").production_blockers()
    assert any("CODE_EXECUTION_PROVIDER" in b for b in blockers)


def test_judge0_without_a_key_blocks_production():
    blockers = build(
        CODE_EXECUTION_PROVIDER="judge0", JUDGE0_API_KEY=""
    ).production_blockers()
    assert any("JUDGE0_API_KEY" in b for b in blockers)


def test_sqlite_blocks_production():
    """A restart would take every learner's progress with it."""
    blockers = build(DATABASE_URL="sqlite:///./sprintforge.db").production_blockers()
    assert any("SQLite" in b for b in blockers)


def test_every_blocker_is_reported_at_once():
    """One problem per redeploy is a slow way to find four of them."""
    blockers = build(
        AUTH_SECRET=UNSAFE_DEFAULT_AUTH_SECRET,
        CODE_EXECUTION_PROVIDER="local",
        DATABASE_URL="sqlite:///./sprintforge.db",
    ).production_blockers()
    assert len(blockers) == 3


@pytest.mark.parametrize("provider,sandboxed", [
    ("local", False),
    ("piston", True),
    ("judge0", True),
    ("PISTON", True),
])
def test_sandboxed_execution_reports_the_truth(provider, sandboxed):
    assert Settings(CODE_EXECUTION_PROVIDER=provider).sandboxed_execution is sandboxed


def test_the_any_localhost_cors_allowance_is_development_only():
    """In production it lets a page on the deployer's machine make credentialed
    calls the origin list would not permit."""
    assert build().cors_origin_regex_effective == ""
    assert Settings(ENVIRONMENT="development").cors_origin_regex_effective


def test_startup_refuses_an_unsafe_production_config(monkeypatch):
    """The blockers must actually stop the app, not just be computable."""
    import asyncio

    import app.main as main_module

    class _Unsafe:
        """A stand-in, because Settings is a pydantic model and rejects patching."""

        def production_blockers(self):
            return ["AUTH_SECRET is unset"]

    monkeypatch.setattr(main_module, "settings", _Unsafe())
    lifespan = main_module.lifespan

    async def enter():
        async with lifespan(None):
            pass

    with pytest.raises(RuntimeError, match="Refusing to start"):
        asyncio.run(enter())
