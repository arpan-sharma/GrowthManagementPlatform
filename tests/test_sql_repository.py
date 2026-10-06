from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.db.constants import DEFAULT_INSTITUTION_ID
from app.db.models import Base
from app.repositories.seed_sql import seed_sql_data
from app.repositories.sql import SqlAuthRepository


def test_sql_repository_roundtrip_and_seed():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        repo = SqlAuthRepository(session)
        settings = Settings(bcrypt_rounds=4, environment="development")
        seed_sql_data(repo, settings)
        session.commit()

        admin = repo.get_user_by_email("admin@gmail.com")
        assert admin is not None
        assert admin.role == "head_teacher"
        assert repo.academic.list_students(DEFAULT_INSTITUTION_ID)
        assert repo.academic.get_batch(DEFAULT_INSTITUTION_ID, "B001") is not None
