from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

def _normalise(url: str) -> str:
    """Route bare postgres URLs to psycopg 3, the driver we actually ship.

    SQLAlchemy defaults `postgresql://` to psycopg2. Pinning the dialect keeps
    copy-pasted provider URLs (Neon, Supabase, RDS) working unchanged, including
    options like `channel_binding` that psycopg2 rejects.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


DATABASE_URL = _normalise(settings.DATABASE_URL)
is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    # Serverless Postgres closes idle connections aggressively; recycling well
    # inside that window avoids handing out dead connections.
    **({} if is_sqlite else {"pool_recycle": 300, "pool_size": 5, "max_overflow": 5}),
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401  (register mappers)
    from app.core.migrations import apply_additive_migrations

    apply_additive_migrations(engine)
    Base.metadata.create_all(bind=engine)
