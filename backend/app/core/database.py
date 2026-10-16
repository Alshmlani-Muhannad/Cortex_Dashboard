"""Database session management (sync SQLAlchemy)."""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables. Used only in dev/demo; production must use Alembic migrations."""
    # Import all models so they are registered on the Base metadata.
    from app.models import base  # noqa: F401
    from app.models import (  # noqa: F401
        alert,
        incident,
        incident_alert,
        event,
        ai_analysis,
        sync_checkpoint,
        sync_job,
        user,
        audit_log,
    )

    from app.models.base import Base

    Base.metadata.create_all(bind=engine)