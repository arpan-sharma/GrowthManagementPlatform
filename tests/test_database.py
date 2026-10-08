import os

from sqlalchemy import create_engine

from app.core.database import validate_schema
from app.db.models import Base, EXPECTED_TABLES


def test_validate_schema_creates_missing_tables():
    engine = create_engine("sqlite:///:memory:")
    tables = validate_schema(engine.url.render_as_string(hide_password=False), auto_create=True)
    assert tables == EXPECTED_TABLES


def test_app_starts_without_database_url():
    os.environ["DATABASE_URL"] = ""
    from app.api.deps import reset_repositories
    from app.main import create_app

    reset_repositories()
    app = create_app()
    assert app.title == "ClassLedger API"
    reset_repositories()
