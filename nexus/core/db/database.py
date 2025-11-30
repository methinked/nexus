"""
Database connection and session management.

Provides SQLAlchemy engine, session factory, and dependency injection for FastAPI.
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from nexus.shared.config import CoreConfig

# Load configuration
config = CoreConfig()

# Create SQLAlchemy engine
engine = create_engine(
    config.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in config.database_url else {},
    echo=config.env == "development",
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database sessions in FastAPI endpoints.

    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables defined in models if they don't exist.
    Should be called during application startup.
    """
    from nexus.core.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
