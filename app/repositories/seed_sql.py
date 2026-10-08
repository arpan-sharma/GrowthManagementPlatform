"""Seed development rows into the services schema."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import BatchRow, StudentRow, TeacherRow, UserRow
from app.repositories.sql import SqlAuthRepository


def seed_sql_data(repo: SqlAuthRepository, settings: Settings) -> None:
    if repo.get_user_by_email("admin@gmail.com") is not None:
        return

    session: Session = repo.session
    if session.scalar(select(BatchRow).limit(1)) is None:
        session.add(
            BatchRow(
                id="B001",
                name="Physics-2026-A",
                status="active",
            )
        )

    admin = UserRow(
        id="T_ADMIN",
        first_name="Dev",
        last_name="Admin",
        email="admin@gmail.com",
        password="admin",
        contact_number="+919800000000",
        role="teacher",
        is_active=True,
    )
    session.add(admin)
    session.flush()
    session.add(TeacherRow(id=admin.id))

    student = UserRow(
        id="S001",
        first_name="Aarav",
        last_name="Sharma",
        email="aarav@example.com",
        password="demo123",
        contact_number="9876543210",
        role="student",
        is_active=True,
    )
    session.add(student)
    session.flush()
    session.add(StudentRow(id=student.id, batch_id="B001"))
