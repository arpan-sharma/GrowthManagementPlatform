"""Map between domain models and SQLAlchemy rows (services schema)."""
from datetime import date, datetime

from app.db.constants import DEFAULT_INSTITUTION_ID
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
    Notice,
    StudentProfile,
    Subject,
    Topic,
)
from app.repositories.models import Institution, RefreshToken, User

_API_ATTENDANCE = {"present": "Present", "absent": "Absent", "late": "Late"}
_DB_ATTENDANCE = {v: k for k, v in _API_ATTENDANCE.items()}

_API_TEST_STATUS = {"upcoming": "Upcoming", "marks_pending": "Marks pending", "done": "Done"}
_DB_TEST_STATUS = {v: k for k, v in _API_TEST_STATUS.items()}

_API_QUESTION_TYPE = {"mcq": "MCQ", "short_answer": "Short answer"}
_DB_QUESTION_TYPE = {v: k for k, v in _API_QUESTION_TYPE.items()}


def default_institution() -> Institution:
    from app.db.constants import DEFAULT_INSTITUTION_CODE, DEFAULT_INSTITUTION_NAME

    return Institution(
        id=DEFAULT_INSTITUTION_ID,
        name=DEFAULT_INSTITUTION_NAME,
        code=DEFAULT_INSTITUTION_CODE,
        city="Pune",
        phone="+919800000000",
        email="admin@classledger.local",
        status="active",
    )


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(None, 1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def _api_role(db_role: str) -> str:
    return "head_teacher" if db_role == "teacher" else db_role


def _db_role(api_role: str) -> str:
    return "teacher" if api_role == "head_teacher" else api_role


def _iso(value: date | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def user_to_domain(row: UserRow, *, student_id: str | None = None, roll_number: str | None = None) -> User:
    return User(
        id=row.id,
        institution_id=DEFAULT_INSTITUTION_ID,
        role=_api_role(row.role),
        full_name=f"{row.first_name} {row.last_name}".strip(),
        email=row.email,
        phone=row.contact_number,
        password_hash=row.password,
        student_id=student_id,
        roll_number=roll_number or student_id,
        failed_attempts=0,
        locked_until=None,
        must_change_password=False,
        consent_at=None,
    )


def user_to_row(user: User) -> UserRow:
    first, last = _split_name(user.full_name)
    return UserRow(
        id=user.id,
        first_name=first,
        last_name=last,
        email=(user.email or "").lower(),
        password=user.password_hash,
        contact_number=user.phone or "",
        role=_db_role(user.role),
        is_active=True,
    )


def refresh_to_domain(row: RefreshTokenRow) -> RefreshToken:
    return RefreshToken(
        id=row.id,
        user_id=row.user_id,
        family_id=row.family_id,
        token_hash=row.token_hash,
        expires_at=row.expires_at,
        ip=row.ip,
        user_agent=row.user_agent,
        revoked_at=row.revoked_at,
        replaced_by=row.replaced_by,
    )


def refresh_to_row(token: RefreshToken) -> RefreshTokenRow:
    return RefreshTokenRow(
        id=token.id,
        user_id=token.user_id,
        family_id=token.family_id,
        token_hash=token.token_hash,
        expires_at=token.expires_at,
        ip=token.ip,
        user_agent=token.user_agent,
        revoked_at=token.revoked_at,
        replaced_by=token.replaced_by,
    )


def batch_to_domain(row: BatchRow) -> Batch:
    return Batch(
        id=row.id,
        institution_id=DEFAULT_INSTITUTION_ID,
        name=row.name,
        start_date=_iso(row.start_date),
        end_date=_iso(row.end_date),
        status=row.status,
    )


def batch_to_row(batch: Batch) -> BatchRow:
    start = date.fromisoformat(batch.start_date) if batch.start_date else None
    end = date.fromisoformat(batch.end_date) if batch.end_date else None
    return BatchRow(
        id=batch.id,
        name=batch.name,
        start_date=start,
        end_date=end,
        status=batch.status,
    )


def student_to_domain(row: StudentRow, user: UserRow) -> StudentProfile:
    return StudentProfile(
        id=row.id,
        institution_id=DEFAULT_INSTITUTION_ID,
        user_id=user.id,
        batch_id=row.batch_id,
        full_name=f"{user.first_name} {user.last_name}".strip(),
        roll_number=row.id,
        parent_phone=user.contact_number,
        parent_email=user.email,
    )


def student_to_row(student: StudentProfile) -> StudentRow:
    return StudentRow(id=student.id, batch_id=student.batch_id)


def subject_to_domain(row: SubjectRow) -> Subject:
    return Subject(
        id=row.id,
        institution_id=DEFAULT_INSTITUTION_ID,
        name=row.name,
        description=row.description,
    )


def subject_to_row(subject: Subject) -> SubjectRow:
    return SubjectRow(id=subject.id, name=subject.name, description=subject.description)


def chapter_to_domain(row: ChapterRow) -> Chapter:
    return Chapter(
        id=row.id,
        institution_id=DEFAULT_INSTITUTION_ID,
        subject_id=row.subject_id,
        name=row.name,
    )


def chapter_to_row(chapter: Chapter) -> ChapterRow:
    return ChapterRow(id=chapter.id, name=chapter.name, subject_id=chapter.subject_id)


def topic_to_domain(row: TopicRow) -> Topic:
    return Topic(
        id=row.id,
        institution_id=DEFAULT_INSTITUTION_ID,
        chapter_id=row.chapter_id,
        name=row.name,
    )


def topic_to_row(topic: Topic) -> TopicRow:
    return TopicRow(id=topic.id, name=topic.name, chapter_id=topic.chapter_id)


def attendance_to_domain(row: AttendanceRow, *, batch_id: str = "", subject_id: str = "") -> AttendanceMark:
    return AttendanceMark(
        id=row.id,
        institution_id=DEFAULT_INSTITUTION_ID,
        student_id=row.student_id,
        batch_id=batch_id,
        subject_id=subject_id,
        on_date=_iso(row.date),
        status=_API_ATTENDANCE.get(row.status, row.status),
        marked_by=row.marked_by or "",
    )


def attendance_to_row(mark: AttendanceMark) -> AttendanceRow:
    return AttendanceRow(
        id=mark.id,
        student_id=mark.student_id,
        date=date.fromisoformat(mark.on_date),
        status=_DB_ATTENDANCE.get(mark.status, mark.status.lower()),
        marked_by=mark.marked_by or None,
    )


def test_to_domain(row: TestRow, *, subject_id: str = "", chapter_id: str = "") -> Exam:
    return Exam(
        id=row.id,
        institution_id=DEFAULT_INSTITUTION_ID,
        name=row.name,
        subject_id=subject_id,
        chapter_id=chapter_id,
        on_date=_iso(row.date),
        max_marks=row.max_marks,
        batch_id=row.batch_id,
        status=_API_TEST_STATUS.get(row.status, row.status),
    )


def test_to_row(exam: Exam) -> TestRow:
    return TestRow(
        id=exam.id,
        name=exam.name,
        batch_id=exam.batch_id or "",
        date=date.fromisoformat(exam.on_date),
        max_marks=exam.max_marks,
        description="",
        status=_DB_TEST_STATUS.get(exam.status, exam.status.lower().replace(" ", "_")),
    )


def question_to_domain(row: QuestionRow, topic: TopicRow | None = None) -> ExamQuestion:
    chapter_id = ""
    if topic is not None:
        chapter_id = topic.chapter_id
    return ExamQuestion(
        id=row.id,
        institution_id=DEFAULT_INSTITUTION_ID,
        test_id=row.test_id,
        text=row.text,
        question_type=_API_QUESTION_TYPE.get(row.question_type, row.question_type),
        marks=row.marks,
        chapter_id=chapter_id,
        topic_id=row.topic_id,
        answer=row.answer,
    )


def question_to_row(question: ExamQuestion) -> QuestionRow:
    return QuestionRow(
        id=question.id,
        test_id=question.test_id,
        text=question.text,
        topic_id=question.topic_id,
        marks=question.marks,
        question_type=_DB_QUESTION_TYPE.get(question.question_type, question.question_type.lower()),
        options=[],
        answer=question.answer,
    )


def mark_to_domain(test_id: str, student_id: str, marks: int, mark_id: str) -> ExamMark:
    return ExamMark(
        id=mark_id,
        institution_id=DEFAULT_INSTITUTION_ID,
        test_id=test_id,
        student_id=student_id,
        marks=marks,
    )


def notice_to_domain(row: NoticeRow) -> Notice:
    return Notice(
        id=row.id,
        institution_id=DEFAULT_INSTITUTION_ID,
        title=row.title,
        content=row.content,
        date=_iso(row.date),
        status=row.status,
        batch_id=None,
    )


def notice_to_row(notice: Notice) -> NoticeRow:
    posted = date.fromisoformat(notice.date[:10]) if notice.date else None
    return NoticeRow(
        id=notice.id,
        title=notice.title,
        content=notice.content,
        date=posted,
        status=notice.status,
    )
