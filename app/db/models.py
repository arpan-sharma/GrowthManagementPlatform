"""SQLAlchemy models aligned with services/db/tables.py (+ refresh_tokens for auth)."""
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    contact_number: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('student', 'teacher')", name="ck_users_role"),
    )


class BatchRow(Base):
    __tablename__ = "batches"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)


class StudentRow(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    batch_id: Mapped[str] = mapped_column(ForeignKey("batches.id"), nullable=False)


class TeacherRow(Base):
    __tablename__ = "teachers"

    id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)


class TeacherSubjectRow(Base):
    __tablename__ = "teacher_subjects"

    teacher_id: Mapped[str] = mapped_column(ForeignKey("teachers.id"), primary_key=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id"), primary_key=True)


class TeacherBatchRow(Base):
    __tablename__ = "teacher_batches"

    teacher_id: Mapped[str] = mapped_column(ForeignKey("teachers.id"), primary_key=True)
    batch_id: Mapped[str] = mapped_column(ForeignKey("batches.id"), primary_key=True)


class SubjectRow(Base):
    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)


class ChapterRow(Base):
    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id"), nullable=False)


class TopicRow(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    chapter_id: Mapped[str] = mapped_column(ForeignKey("chapters.id"), nullable=False)


class AttendanceRow(Base):
    __tablename__ = "attendance"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    marked_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("student_id", "date", name="uq_attendance_student_date"),
        CheckConstraint(
            "status IN ('present', 'absent', 'late')",
            name="ck_attendance_status",
        ),
    )


class TestRow(Base):
    __tablename__ = "tests"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    batch_id: Mapped[str] = mapped_column(ForeignKey("batches.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    max_marks: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String, default="upcoming", nullable=False)

    __table_args__ = (
        CheckConstraint("max_marks > 0", name="ck_tests_max_marks"),
        CheckConstraint(
            "status IN ('upcoming', 'marks_pending', 'done')",
            name="ck_tests_status",
        ),
    )


class QuestionRow(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    test_id: Mapped[str] = mapped_column(ForeignKey("tests.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), nullable=False)
    marks: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(String, nullable=False)
    options: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    answer: Mapped[str] = mapped_column(Text, default="", nullable=False)

    __table_args__ = (
        CheckConstraint("marks > 0", name="ck_questions_marks"),
        CheckConstraint(
            "question_type IN ('mcq', 'short_answer')",
            name="ck_questions_type",
        ),
    )


class ResultRow(Base):
    __tablename__ = "results"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), nullable=False)
    student_answer: Mapped[str] = mapped_column(Text, nullable=False)
    marks_awarded: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "question_id", name="uq_results_student_question"),
        CheckConstraint("marks_awarded >= 0", name="ck_results_marks_awarded"),
    )


class NoticeRow(Base):
    __tablename__ = "notices"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)


class RefreshTokenRow(Base):
    """Auth-only table; not part of services/db but required for JWT refresh."""

    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    family_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str] = mapped_column(String(255), default="")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by: Mapped[str | None] = mapped_column(String(32))


EXPECTED_TABLES = sorted(Base.metadata.tables.keys())
