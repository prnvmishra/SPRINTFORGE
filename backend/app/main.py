import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.routers import (
    account,
    ai,
    assessment,
    auth,
    community,
    leaderboard,
    learning_path,
    paths,
    placement,
    practice,
    profile,
    projects,
    rewards,
    roadmaps,
    tickets,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sprintforge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Refuse to serve rather than serve insecurely. Each of these is harmless on
    # a laptop and severe on a public host, and every one of them is the kind of
    # thing that gets noticed after the deploy rather than before it.
    blockers = settings.production_blockers()
    if blockers:
        raise RuntimeError(
            "Refusing to start in production with unsafe settings:\n"
            + "\n".join(f"  * {reason}" for reason in blockers)
        )

    init_db()
    logger.info(
        "SprintForge.AI started · AI provider=%s · execution provider=%s (sandboxed=%s)",
        settings.ai_provider_effective,
        settings.CODE_EXECUTION_PROVIDER,
        settings.sandboxed_execution,
    )
    if not settings.sandboxed_execution:
        logger.warning(
            "Learner code runs as this process (provider=%s). Acceptable locally, "
            "never on a host you do not own.",
            settings.CODE_EXECUTION_PROVIDER,
        )
    yield


app = FastAPI(
    title="SprintForge.AI API",
    description="Continuous Adaptive Learning and Project Execution Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=settings.cors_origin_regex_effective or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (
    auth,
    account,
    profile,
    assessment,
    paths,
    placement,
    practice,
    projects,
    tickets,
    ai,
    rewards,
    leaderboard,
    community,
    learning_path,
    roadmaps,
):
    app.include_router(module.router)

# Uploaded avatars are served straight from disk; no object storage is configured.
UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.get("/health", tags=["meta"])
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "ai_provider": settings.ai_provider_effective,
        "code_execution_provider": settings.CODE_EXECUTION_PROVIDER,
    }
