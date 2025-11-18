"""
Database connection and session management.
Uses SQLAlchemy for ORM and connection pooling.
"""

from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool
from contextlib import contextmanager
from typing import Generator
import logging

from config.settings import get_settings

logger = logging.getLogger(__name__)

# Base class for all ORM models
Base = declarative_base()

# Database engine (singleton)
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()

        _engine = create_engine(
            settings.database_url,
            poolclass=pool.QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=settings.DEBUG_MODE,  # Log SQL queries in debug mode
        )

        # Add connection event listeners
        @event.listens_for(_engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Called when a new connection is created."""
            logger.debug("Database connection established")

        @event.listens_for(_engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Called when a connection is retrieved from the pool."""
            logger.debug("Connection checked out from pool")

        logger.info(f"Database engine created: {settings.DB_NAME}@{settings.DB_HOST}")

    return _engine


def get_session_factory():
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        logger.info("Session factory created")

    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database sessions.
    Use with FastAPI Depends or in context managers.

    Usage:
        with get_db() as db:
            db.query(Creator).all()
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Automatically commits on success, rolls back on exception.

    Usage:
        with get_db_session() as db:
            creator = Creator(handle="@test")
            db.add(creator)
            # Auto-commit on exit
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}", exc_info=True)
        raise
    finally:
        session.close()


def init_db():
    """Initialize database tables."""
    engine = get_engine()

    # Import all models to ensure they're registered
    from models.database_models import (
        Creator,
        Video,
        VideoAnalysis,
        EngagementFeatures,
        Prediction,
        Embedding,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def drop_all_tables():
    """Drop all tables (use with caution!)."""
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")


def check_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection check: SUCCESS")
        return True
    except Exception as e:
        logger.error(f"Database connection check: FAILED - {e}")
        return False


def get_db_stats() -> dict:
    """
    Get database connection pool statistics.

    Returns:
        dict: Pool statistics
    """
    engine = get_engine()
    pool = engine.pool

    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow(),
    }


def close_db_connections():
    """Close all database connections and dispose of engine."""
    global _engine, _SessionLocal

    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None
        logger.info("Database connections closed")


if __name__ == "__main__":
    # Test database connection
    print("Testing database connection...")

    if check_connection():
        print("✓ Database connection successful")

        stats = get_db_stats()
        print(f"\nConnection pool stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Test session creation
        with get_db_session() as db:
            print("\n✓ Database session created successfully")

        close_db_connections()
    else:
        print("✗ Database connection failed")
        print("Check your DATABASE_URL in .env file")
