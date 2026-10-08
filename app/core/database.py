"""PostgreSQL connection and schema validation."""
from functools import lru_cache

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import EXPECTED_TABLES, Base


class DatabaseError(RuntimeError):
    pass


@lru_cache
def get_session_factory(database_url: str) -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(database_url), autocommit=False, autoflush=False)


@lru_cache
def get_engine(database_url: str) -> Engine:
    kwargs: dict = {"pool_pre_ping": True}
    if database_url.startswith("postgresql"):
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 10
    return create_engine(database_url, **kwargs)


def check_connection(database_url: str) -> None:
    """Fail fast if the database is unreachable."""
    engine = get_engine(database_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise DatabaseError(f"Database connection failed: {exc}") from exc


def validate_schema(database_url: str, *, auto_create: bool = False) -> list[str]:
    """
    Ensure all expected tables exist.
    When auto_create is true (development), missing tables are created.
    """
    engine = get_engine(database_url)
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    missing = [name for name in EXPECTED_TABLES if name not in existing]
    if missing and auto_create:
        Base.metadata.create_all(engine, tables=[Base.metadata.tables[name] for name in missing])
        inspector = inspect(engine)
        existing = set(inspector.get_table_names())
        missing = [name for name in EXPECTED_TABLES if name not in existing]
    if missing:
        raise DatabaseError(f"Database schema is missing tables: {', '.join(missing)}")
    return sorted(existing.intersection(EXPECTED_TABLES))


def database_status(database_url: str) -> dict:
    try:
        tables = validate_schema(database_url, auto_create=False)
        with get_engine(database_url).connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "tables": len(tables)}
    except DatabaseError as exc:
        return {"status": "error", "message": str(exc)}
    except SQLAlchemyError as exc:
        return {"status": "error", "message": f"Database error: {exc}"}
