"""PostgreSQL repositories backed by the services/db schema."""
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import case, func, or_, select, update
from sqlalchemy.orm import Session

from app.db.constants import DEFAULT_INSTITUTION_CODE, DEFAULT_INSTITUTION_ID
from app.db.models import (
    AttendanceRow,
    BatchRow,
    ChapterRow,
    NoticeRow,
    QuestionRow,
    RefreshTokenRow,
    ResultRow,
    StudentRow,
    SubjectRow,
    TeacherRow,
    TestRow,
    TopicRow,
    UserRow,
)
from app.repositories.academic import (
    AttendanceMark,
    Batch,
    Chapter,
    Exam,
    ExamMark,
    ExamQuestion,
    FeeAccount,
    Notice,
    StudentProfile,
    Subject,
    Topic,
)
from app.repositories.base import AuthRepository
from app.repositories.mappers import (
    attendance_to_domain,
    attendance_to_row,
    batch_to_domain,
    batch_to_row,
    chapter_to_domain,
    chapter_to_row,
    default_institution,
    mark_to_domain,
    notice_to_domain,
    notice_to_row,
    question_to_domain,
    question_to_row,
    refresh_to_domain,
    refresh_to_row,
    student_to_domain,
    student_to_row,
    subject_to_domain,
    subject_to_row,
    test_to_domain,
    test_to_row,
    topic_to_domain,
    topic_to_row,
    user_to_domain,
    user_to_row,
)
from app.repositories.models import Institution, RefreshToken, User


class SqlAcademicRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _student_query(self):
        return (
            select(StudentRow, UserRow)
            .join(UserRow, UserRow.id == StudentRow.id)
            .where(UserRow.role == "student", UserRow.is_active.is_(True))
        )

    def _student_profile(self, student_row: StudentRow, user_row: UserRow) -> StudentProfile:
        return student_to_domain(student_row, user_row)

    def _topic_subject(self, topic_id: str) -> tuple[str, str]:
        topic = self.session.get(TopicRow, topic_id)
        if topic is None:
            return "", ""
        chapter = self.session.get(ChapterRow, topic.chapter_id)
        if chapter is None:
            return "", topic.chapter_id if topic else ""
        return chapter.subject_id, chapter.id

    def _test_subject_chapter(self, test_id: str) -> tuple[str, str]:
        question = self.session.scalar(select(QuestionRow).where(QuestionRow.test_id == test_id).limit(1))
        if question is None:
            return "", ""
        return self._topic_subject(question.topic_id)

    def save_batch(self, row: Batch) -> None:
        self.session.merge(batch_to_row(row))

    def get_batch(self, institution_id: str, batch_id: str) -> Optional[Batch]:
        db_row = self.session.get(BatchRow, batch_id)
        return batch_to_domain(db_row) if db_row else None

    def list_batches(self, institution_id: str) -> list[Batch]:
        return [batch_to_domain(row) for row in self.session.scalars(select(BatchRow)).all()]

    def save_student(self, row: StudentProfile) -> None:
        student_row = student_to_row(row)
        existing = self.session.get(StudentRow, row.id)
        if existing is None:
            self.session.add(student_row)
        else:
            existing.batch_id = student_row.batch_id
        self.session.flush()

    def get_student(self, institution_id: str, student_id: str) -> Optional[StudentProfile]:
        result = self.session.execute(
            self._student_query().where(StudentRow.id == student_id)
        ).first()
        if result is None:
            return None
        student_row, user_row = result
        return self._student_profile(student_row, user_row)

    def find_student_by_roll(self, institution_id: str, roll_number: str) -> Optional[StudentProfile]:
        roll = roll_number.strip()
        result = self.session.execute(
            self._student_query().where(
                or_(StudentRow.id == roll, UserRow.email.ilike(roll))
            )
        ).first()
        if result is None:
            return None
        student_row, user_row = result
        return self._student_profile(student_row, user_row)

    def list_students(self, institution_id: str, batch_id: Optional[str] = None) -> list[StudentProfile]:
        stmt = self._student_query()
        if batch_id:
            stmt = stmt.where(StudentRow.batch_id == batch_id)
        return [self._student_profile(s, u) for s, u in self.session.execute(stmt).all()]

    def list_student_summaries(self, today: date, batch_id: Optional[str] = None) -> list[dict[str, Any]]:
        att_stats = (
            select(
                AttendanceRow.student_id,
                func.count().label("total"),
                func.coalesce(
                    func.sum(case((AttendanceRow.status.in_(("present", "late")), 1), else_=0)),
                    0,
                ).label("attended"),
            )
            .group_by(AttendanceRow.student_id)
            .subquery()
        )
        today_marks = (
            select(AttendanceRow.student_id, AttendanceRow.status)
            .where(AttendanceRow.date == today)
            .subquery()
        )
        stmt = (
            select(
                StudentRow,
                UserRow,
                BatchRow.name,
                att_stats.c.attended,
                att_stats.c.total,
                today_marks.c.status,
            )
            .join(UserRow, UserRow.id == StudentRow.id)
            .join(BatchRow, BatchRow.id == StudentRow.batch_id)
            .outerjoin(att_stats, att_stats.c.student_id == StudentRow.id)
            .outerjoin(today_marks, today_marks.c.student_id == StudentRow.id)
            .where(UserRow.role == "student", UserRow.is_active.is_(True))
        )
        if batch_id:
            stmt = stmt.where(StudentRow.batch_id == batch_id)
        summaries: list[dict[str, Any]] = []
        for student, user, batch_name, attended, total, today_status in self.session.execute(stmt).all():
            total_n = int(total or 0)
            attended_n = int(attended or 0)
            attendance_pct = round(100 * attended_n / total_n, 1) if total_n else 0.0
            summaries.append(
                {
                    "id": student.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "contact_number": user.contact_number,
                    "batch_id": student.batch_id,
                    "batch_name": batch_name or "",
                    "roll_number": student.id,
                    "is_active": user.is_active,
                    "attendance_pct": attendance_pct,
                    "attendance_total": total_n,
                    "today_db": today_status,
                }
            )
        return summaries

    def save_subject(self, row: Subject) -> None:
        self.session.merge(subject_to_row(row))

    def get_subject(self, institution_id: str, subject_id: str) -> Optional[Subject]:
        db_row = self.session.get(SubjectRow, subject_id)
        return subject_to_domain(db_row) if db_row else None

    def list_subjects(self, institution_id: str) -> list[Subject]:
        return [subject_to_domain(row) for row in self.session.scalars(select(SubjectRow)).all()]

    def save_chapter(self, row: Chapter) -> None:
        self.session.merge(chapter_to_row(row))

    def get_chapter(self, institution_id: str, chapter_id: str) -> Optional[Chapter]:
        db_row = self.session.get(ChapterRow, chapter_id)
        return chapter_to_domain(db_row) if db_row else None

    def list_chapters(self, institution_id: str, subject_id: Optional[str] = None) -> list[Chapter]:
        stmt = select(ChapterRow)
        if subject_id:
            stmt = stmt.where(ChapterRow.subject_id == subject_id)
        return [chapter_to_domain(row) for row in self.session.scalars(stmt).all()]

    def save_topic(self, row: Topic) -> None:
        self.session.merge(topic_to_row(row))

    def get_topic(self, institution_id: str, topic_id: str) -> Optional[Topic]:
        db_row = self.session.get(TopicRow, topic_id)
        return topic_to_domain(db_row) if db_row else None

    def list_topics(self, institution_id: str, chapter_id: Optional[str] = None) -> list[Topic]:
        stmt = select(TopicRow)
        if chapter_id:
            stmt = stmt.where(TopicRow.chapter_id == chapter_id)
        return [topic_to_domain(row) for row in self.session.scalars(stmt).all()]

    def save_attendance(self, row: AttendanceMark) -> None:
        self.session.merge(attendance_to_row(row))

    def find_attendance(
        self, institution_id: str, student_id: str, subject_id: str, on_date: str
    ) -> Optional[AttendanceMark]:
        row = self.session.scalar(
            select(AttendanceRow).where(
                AttendanceRow.student_id == student_id,
                AttendanceRow.date == date.fromisoformat(on_date),
            )
        )
        if row is None:
            return None
        student = self.get_student(institution_id, student_id)
        batch_id = student.batch_id if student else ""
        return attendance_to_domain(row, batch_id=batch_id, subject_id=subject_id)

    def list_attendance(
        self,
        institution_id: str,
        *,
        on_date: Optional[str] = None,
        batch_id: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> list[AttendanceMark]:
        stmt = select(AttendanceRow, StudentRow.batch_id).join(
            StudentRow, StudentRow.id == AttendanceRow.student_id
        )
        if on_date:
            stmt = stmt.where(AttendanceRow.date == date.fromisoformat(on_date))
        if student_id:
            stmt = stmt.where(AttendanceRow.student_id == student_id)
        if batch_id:
            stmt = stmt.where(StudentRow.batch_id == batch_id)
        return [
            attendance_to_domain(row, batch_id=student_batch_id, subject_id="")
            for row, student_batch_id in self.session.execute(stmt).all()
        ]

    def save_test(self, row: Exam) -> None:
        self.session.merge(test_to_row(row))

    def get_test(self, institution_id: str, test_id: str) -> Optional[Exam]:
        db_row = self.session.get(TestRow, test_id)
        if db_row is None:
            return None
        subject_id, chapter_id = self._test_subject_chapter(test_id)
        return test_to_domain(db_row, subject_id=subject_id, chapter_id=chapter_id)

    def list_tests(self, institution_id: str, batch_id: Optional[str] = None) -> list[Exam]:
        stmt = select(TestRow)
        if batch_id:
            stmt = stmt.where(TestRow.batch_id == batch_id)
        rows = self.session.scalars(stmt).all()
        subject_chapter = self._test_subject_chapters([row.id for row in rows])
        return [
            test_to_domain(row, subject_id=subject_chapter.get(row.id, ("", ""))[0], chapter_id=subject_chapter.get(row.id, ("", ""))[1])
            for row in rows
        ]

    def _test_subject_chapters(self, test_ids: list[str]) -> dict[str, tuple[str, str]]:
        if not test_ids:
            return {}
        pairs = self.session.execute(
            select(QuestionRow.test_id, ChapterRow.subject_id, ChapterRow.id)
            .join(TopicRow, TopicRow.id == QuestionRow.topic_id)
            .join(ChapterRow, ChapterRow.id == TopicRow.chapter_id)
            .where(QuestionRow.test_id.in_(test_ids))
        ).all()
        mapping: dict[str, tuple[str, str]] = {}
        for test_id, subject_id, chapter_id in pairs:
            mapping.setdefault(test_id, (subject_id, chapter_id))
        return mapping

    def save_question(self, row: ExamQuestion) -> None:
        self.session.merge(question_to_row(row))

    def list_questions(self, institution_id: str, test_id: str) -> list[ExamQuestion]:
        rows = self.session.scalars(select(QuestionRow).where(QuestionRow.test_id == test_id)).all()
        questions: list[ExamQuestion] = []
        for row in rows:
            topic = self.session.get(TopicRow, row.topic_id)
            questions.append(question_to_domain(row, topic))
        return questions

    def save_mark(self, row: ExamMark) -> None:
        return None

    def find_mark(self, institution_id: str, test_id: str, student_id: str) -> Optional[ExamMark]:
        marks = self._aggregate_marks(test_id=test_id, student_id=student_id)
        return marks[0] if marks else None

    def list_marks(
        self, institution_id: str, test_id: Optional[str] = None, student_id: Optional[str] = None
    ) -> list[ExamMark]:
        return self._aggregate_marks(test_id=test_id, student_id=student_id)

    def _aggregate_marks(
        self, *, test_id: Optional[str] = None, student_id: Optional[str] = None
    ) -> list[ExamMark]:
        stmt = (
            select(
                QuestionRow.test_id,
                ResultRow.student_id,
                func.sum(ResultRow.marks_awarded).label("total"),
                func.min(ResultRow.id).label("mark_id"),
            )
            .join(QuestionRow, QuestionRow.id == ResultRow.question_id)
            .group_by(QuestionRow.test_id, ResultRow.student_id)
        )
        if test_id:
            stmt = stmt.where(QuestionRow.test_id == test_id)
        if student_id:
            stmt = stmt.where(ResultRow.student_id == student_id)
        return [
            mark_to_domain(row.test_id, row.student_id, int(row.total), row.mark_id)
            for row in self.session.execute(stmt).all()
        ]

    def save_fee(self, row: FeeAccount) -> None:
        return None

    def find_fee(self, institution_id: str, student_id: str) -> Optional[FeeAccount]:
        return None

    def list_fees(self, institution_id: str) -> list[FeeAccount]:
        return []

    def save_notice(self, row: Notice) -> None:
        self.session.merge(notice_to_row(row))

    def list_notices(self, institution_id: str, batch_id: Optional[str] = None) -> list[Notice]:
        return [notice_to_domain(row) for row in self.session.scalars(select(NoticeRow)).all()]


class SqlAuthRepository(AuthRepository):
    def __init__(self, session: Session) -> None:
        self.session = session
        self.academic = SqlAcademicRepository(session)

    def get_user_by_email(self, email: str) -> Optional[User]:
        row = self.session.scalar(select(UserRow).where(UserRow.email == email.lower()))
        if row is None:
            return None
        student_id = row.id if row.role == "student" else None
        return user_to_domain(row, student_id=student_id, roll_number=student_id)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        row = self.session.get(UserRow, user_id)
        if row is None:
            return None
        student_id = row.id if row.role == "student" else None
        return user_to_domain(row, student_id=student_id, roll_number=student_id)

    def get_student_by_roll(self, institution_id: str, roll_number: str) -> Optional[User]:
        profile = self.academic.find_student_by_roll(institution_id, roll_number)
        if profile is None:
            return None
        row = self.session.get(UserRow, profile.user_id)
        return user_to_domain(row, student_id=profile.id, roll_number=profile.roll_number) if row else None

    def save_user(self, user: User) -> None:
        if user.email:
            user.email = user.email.lower()
        row = user_to_row(user)
        existing = self.session.get(UserRow, user.id)
        if existing is None:
            self.session.add(row)
        else:
            existing.first_name = row.first_name
            existing.last_name = row.last_name
            existing.email = row.email
            existing.password = row.password
            existing.contact_number = row.contact_number
            existing.role = row.role
            existing.is_active = row.is_active
        # User and student rows share the same id; flush the user before any student write.
        self.session.flush()
        if user.role == "head_teacher":
            if self.session.get(TeacherRow, user.id) is None:
                self.session.add(TeacherRow(id=user.id))
        if user.role == "student" and user.student_id:
            if self.session.get(StudentRow, user.student_id) is None:
                profile = self.academic.get_student(user.institution_id, user.student_id)
                if profile:
                    self.session.add(StudentRow(id=profile.id, batch_id=profile.batch_id))

    def get_institution(self, institution_id: str) -> Optional[Institution]:
        if institution_id == DEFAULT_INSTITUTION_ID:
            return default_institution()
        return None

    def get_institution_by_code(self, code: str) -> Optional[Institution]:
        normalized = code.strip().upper()
        if normalized in {DEFAULT_INSTITUTION_CODE, "DEMO01"}:
            return default_institution()
        return None

    def create_institution_with_admin(self, institution: Institution, user: User) -> None:
        user.institution_id = DEFAULT_INSTITUTION_ID
        self.session.add(user_to_row(user))
        self.session.flush()
        self.session.add(TeacherRow(id=user.id))

    def add_refresh(self, token: RefreshToken) -> None:
        self.session.add(refresh_to_row(token))

    def save_refresh(self, token: RefreshToken) -> None:
        self.session.merge(refresh_to_row(token))

    def get_refresh_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        row = self.session.scalar(select(RefreshTokenRow).where(RefreshTokenRow.token_hash == token_hash))
        return refresh_to_domain(row) if row else None

    def revoke_family(self, family_id: str, now: datetime) -> None:
        self.session.execute(
            update(RefreshTokenRow)
            .where(RefreshTokenRow.family_id == family_id, RefreshTokenRow.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    def revoke_all_for_user(self, user_id: str, now: datetime, except_family: Optional[str] = None) -> None:
        stmt = update(RefreshTokenRow).where(
            RefreshTokenRow.user_id == user_id,
            RefreshTokenRow.revoked_at.is_(None),
        )
        if except_family:
            stmt = stmt.where(RefreshTokenRow.family_id != except_family)
        self.session.execute(stmt.values(revoked_at=now))

    def add_audit(
        self,
        action: str,
        institution_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip: Optional[str] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> None:
        return None
