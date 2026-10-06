"""In-memory academic records for one process. Keyed by institution id from the JWT."""
from dataclasses import dataclass
from typing import Optional

from app.core.config import Settings
from app.core.security import hash_password
from app.repositories.models import User


@dataclass
class Batch:
    id: str
    institution_id: str
    name: str
    start_date: str = ""
    end_date: str = ""
    status: str = "active"


@dataclass
class StudentProfile:
    id: str
    institution_id: str
    user_id: str
    batch_id: str
    full_name: str
    roll_number: str
    parent_phone: str
    parent_email: Optional[str] = None


@dataclass
class Subject:
    id: str
    institution_id: str
    name: str
    description: str = ""


@dataclass
class Chapter:
    id: str
    institution_id: str
    subject_id: str
    name: str


@dataclass
class Topic:
    id: str
    institution_id: str
    chapter_id: str
    name: str


@dataclass
class AttendanceMark:
    id: str
    institution_id: str
    student_id: str
    batch_id: str
    subject_id: str
    on_date: str
    status: str
    marked_by: str


@dataclass
class Exam:
    id: str
    institution_id: str
    name: str
    subject_id: str
    chapter_id: str
    on_date: str
    max_marks: int
    batch_id: Optional[str] = None
    status: str = "Upcoming"


@dataclass
class ExamQuestion:
    id: str
    institution_id: str
    test_id: str
    text: str
    question_type: str
    marks: int
    chapter_id: str
    topic_id: str
    answer: str = ""


@dataclass
class ExamMark:
    id: str
    institution_id: str
    test_id: str
    student_id: str
    marks: int


@dataclass
class FeeAccount:
    id: str
    institution_id: str
    student_id: str
    total: int
    paid: int
    due_date: str


@dataclass
class Notice:
    id: str
    institution_id: str
    title: str
    content: str
    date: str = ""
    status: str = "active"
    batch_id: Optional[str] = None


class InMemoryAcademicRepository:
    def __init__(self) -> None:
        self.batches: dict[str, Batch] = {}
        self.students: dict[str, StudentProfile] = {}
        self.subjects: dict[str, Subject] = {}
        self.chapters: dict[str, Chapter] = {}
        self.topics: dict[str, Topic] = {}
        self.attendance: dict[str, AttendanceMark] = {}
        self.tests: dict[str, Exam] = {}
        self.questions: dict[str, ExamQuestion] = {}
        self.marks: dict[str, ExamMark] = {}
        self.fees: dict[str, FeeAccount] = {}
        self.notices: dict[str, Notice] = {}

    def _owned(self, rows: dict, institution_id: str) -> list:
        return [row for row in rows.values() if row.institution_id == institution_id]

    def save_batch(self, row: Batch) -> None:
        self.batches[row.id] = row

    def get_batch(self, institution_id: str, batch_id: str) -> Optional[Batch]:
        row = self.batches.get(batch_id)
        return row if row and row.institution_id == institution_id else None

    def list_batches(self, institution_id: str) -> list[Batch]:
        return self._owned(self.batches, institution_id)

    def save_student(self, row: StudentProfile) -> None:
        self.students[row.id] = row

    def get_student(self, institution_id: str, student_id: str) -> Optional[StudentProfile]:
        row = self.students.get(student_id)
        return row if row and row.institution_id == institution_id else None

    def find_student_by_roll(self, institution_id: str, roll_number: str) -> Optional[StudentProfile]:
        for row in self.students.values():
            if row.institution_id == institution_id and row.roll_number == roll_number:
                return row
        return None

    def list_students(self, institution_id: str, batch_id: Optional[str] = None) -> list[StudentProfile]:
        rows = self._owned(self.students, institution_id)
        if batch_id:
            rows = [row for row in rows if row.batch_id == batch_id]
        return rows

    def save_subject(self, row: Subject) -> None:
        self.subjects[row.id] = row

    def get_subject(self, institution_id: str, subject_id: str) -> Optional[Subject]:
        row = self.subjects.get(subject_id)
        return row if row and row.institution_id == institution_id else None

    def list_subjects(self, institution_id: str) -> list[Subject]:
        return self._owned(self.subjects, institution_id)

    def save_chapter(self, row: Chapter) -> None:
        self.chapters[row.id] = row

    def get_chapter(self, institution_id: str, chapter_id: str) -> Optional[Chapter]:
        row = self.chapters.get(chapter_id)
        return row if row and row.institution_id == institution_id else None

    def list_chapters(self, institution_id: str, subject_id: Optional[str] = None) -> list[Chapter]:
        rows = self._owned(self.chapters, institution_id)
        if subject_id:
            rows = [row for row in rows if row.subject_id == subject_id]
        return rows

    def save_topic(self, row: Topic) -> None:
        self.topics[row.id] = row

    def get_topic(self, institution_id: str, topic_id: str) -> Optional[Topic]:
        row = self.topics.get(topic_id)
        return row if row and row.institution_id == institution_id else None

    def list_topics(self, institution_id: str, chapter_id: Optional[str] = None) -> list[Topic]:
        rows = self._owned(self.topics, institution_id)
        if chapter_id:
            rows = [row for row in rows if row.chapter_id == chapter_id]
        return rows

    def save_attendance(self, row: AttendanceMark) -> None:
        self.attendance[row.id] = row

    def find_attendance(self, institution_id: str, student_id: str, subject_id: str, on_date: str) -> Optional[AttendanceMark]:
        for row in self.attendance.values():
            if (
                row.institution_id == institution_id
                and row.student_id == student_id
                and row.subject_id == subject_id
                and row.on_date == on_date
            ):
                return row
        return None

    def list_attendance(
        self,
        institution_id: str,
        *,
        on_date: Optional[str] = None,
        batch_id: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> list[AttendanceMark]:
        rows = self._owned(self.attendance, institution_id)
        if on_date:
            rows = [row for row in rows if row.on_date == on_date]
        if batch_id:
            rows = [row for row in rows if row.batch_id == batch_id]
        if student_id:
            rows = [row for row in rows if row.student_id == student_id]
        return rows

    def save_test(self, row: Exam) -> None:
        self.tests[row.id] = row

    def get_test(self, institution_id: str, test_id: str) -> Optional[Exam]:
        row = self.tests.get(test_id)
        return row if row and row.institution_id == institution_id else None

    def list_tests(self, institution_id: str, batch_id: Optional[str] = None) -> list[Exam]:
        rows = self._owned(self.tests, institution_id)
        if batch_id:
            rows = [row for row in rows if row.batch_id in (None, batch_id)]
        return rows

    def save_question(self, row: ExamQuestion) -> None:
        self.questions[row.id] = row

    def list_questions(self, institution_id: str, test_id: str) -> list[ExamQuestion]:
        return [row for row in self._owned(self.questions, institution_id) if row.test_id == test_id]

    def save_mark(self, row: ExamMark) -> None:
        self.marks[row.id] = row

    def find_mark(self, institution_id: str, test_id: str, student_id: str) -> Optional[ExamMark]:
        for row in self.marks.values():
            if row.institution_id == institution_id and row.test_id == test_id and row.student_id == student_id:
                return row
        return None

    def list_marks(self, institution_id: str, test_id: Optional[str] = None, student_id: Optional[str] = None) -> list[ExamMark]:
        rows = self._owned(self.marks, institution_id)
        if test_id:
            rows = [row for row in rows if row.test_id == test_id]
        if student_id:
            rows = [row for row in rows if row.student_id == student_id]
        return rows

    def save_fee(self, row: FeeAccount) -> None:
        self.fees[row.id] = row

    def find_fee(self, institution_id: str, student_id: str) -> Optional[FeeAccount]:
        for row in self.fees.values():
            if row.institution_id == institution_id and row.student_id == student_id:
                return row
        return None

    def list_fees(self, institution_id: str) -> list[FeeAccount]:
        return self._owned(self.fees, institution_id)

    def save_notice(self, row: Notice) -> None:
        self.notices[row.id] = row

    def list_notices(self, institution_id: str, batch_id: Optional[str] = None) -> list[Notice]:
        rows = self._owned(self.notices, institution_id)
        if batch_id:
            rows = [row for row in rows if row.batch_id in (None, batch_id)]
        return rows


def seed_demo_class(repo, settings: Settings) -> None:
    """One batch and student so development login can open the class screens."""
    store = repo.academic
    institution_id = "inst_demo"
    batch = Batch(id="bat_demo", institution_id=institution_id, name="Batch A", status="active")
    subject = Subject(id="sub_maths", institution_id=institution_id, name="Maths")
    chapter = Chapter(id="ch_algebra", institution_id=institution_id, subject_id=subject.id, name="Algebra")
    topic = Topic(id="top_linear", institution_id=institution_id, chapter_id=chapter.id, name="Linear equations")
    student = StudentProfile(
        id="stu_aarav",
        institution_id=institution_id,
        user_id="usr_aarav",
        batch_id=batch.id,
        full_name="Aarav Sharma",
        roll_number="24-018",
        parent_phone="+919800000001",
    )
    user = User(
        id="usr_aarav",
        institution_id=institution_id,
        role="student",
        full_name=student.full_name,
        password_hash=hash_password("student123", rounds=settings.bcrypt_rounds),
        phone=student.parent_phone,
        student_id=student.id,
        roll_number=student.roll_number,
        must_change_password=True,
    )
    fee = FeeAccount(
        id="fee_aarav",
        institution_id=institution_id,
        student_id=student.id,
        total=8000,
        paid=8000,
        due_date="2026-10-05",
    )
    notice = Notice(
        id="ntc_welcome",
        institution_id=institution_id,
        title="Term test",
        content="Term test on Saturday.",
        date="2026-10-01",
        status="active",
        batch_id=None,
    )
    store.save_batch(batch)
    store.save_subject(subject)
    store.save_chapter(chapter)
    store.save_topic(topic)
    store.save_student(student)
    repo.save_user(user)
    store.save_fee(fee)
    store.save_notice(notice)
