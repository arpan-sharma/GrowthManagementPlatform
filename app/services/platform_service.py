"""Institute academic rules. Every read and write is scoped to the caller's institution."""
from datetime import date, datetime, timezone
from typing import Optional, Protocol

from app.core.errors import AppError
from app.core.security import hash_password, new_id
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
from app.repositories.models import User
from app.schemas.platform import (
    AttendanceOut,
    AttendanceSessionIn,
    AttendanceSessionOut,
    AttendanceSessionStudentOut,
    BatchCreate,
    BatchOut,
    BatchUpdate,
    ChapterAnalysisOut,
    ChapterCreate,
    ChapterOut,
    DashboardOut,
    FeeOut,
    FeePlanIn,
    MarkOut,
    MarksIn,
    NoticeCreate,
    NoticeOut,
    PaymentIn,
    QuestionIn,
    QuestionOut,
    StudentCreate,
    StudentOut,
    StudentProfileOut,
    StudentUpdate,
    SubjectCreate,
    SubjectOut,
    SubjectScoreOut,
    TestCreate,
    TestOut,
    TopicCreate,
    TopicOut,
    TopicScoreOut,
)

ATTENDANCE_FLAG_BELOW = 80


class Caller(Protocol):
    user_id: str
    institution_id: str
    role: str
    student_id: Optional[str]


class PlatformService:
    def __init__(self, auth: AuthRepository, academic, today: Optional[date] = None):
        self.auth = auth
        self.db = academic
        self.today = today or datetime.now(timezone.utc).date()

    # ---------- guards ----------
    def _active_institution(self, principal: Caller) -> str:
        institution = self.auth.get_institution(principal.institution_id)
        if institution is None or institution.status != "active":
            raise AppError(403, "account_suspended", "This institute is not active.")
        return institution.id

    def _require_teacher(self, principal: Caller) -> str:
        if principal.role != "head_teacher":
            raise AppError(403, "forbidden", "You do not have access to this resource.")
        return self._active_institution(principal)

    def _student_or_404(self, institution_id: str, student_id: str) -> StudentProfile:
        student = self.db.get_student(institution_id, student_id)
        if student is None:
            raise AppError(404, "not_found", "Student not found.")
        user = self.auth.get_user_by_id(student.user_id)
        if user is None or not user.is_active:
            raise AppError(404, "not_found", "Student not found.")
        return student

    def _roll_taken(self, institution_id: str, roll_number: str) -> bool:
        profile = self.db.find_student_by_roll(institution_id, roll_number)
        if profile is not None:
            user = self.auth.get_user_by_id(profile.user_id)
            if user is not None and user.is_active:
                return True
        user = self.auth.get_student_by_roll(institution_id, roll_number)
        return user is not None and user.is_active

    def _visible_student(self, principal: Caller, student_id: str) -> StudentProfile:
        institution_id = self._active_institution(principal)
        if principal.role == "student" and principal.student_id != student_id:
            raise AppError(404, "not_found", "Student not found.")
        if principal.role not in ("head_teacher", "student"):
            raise AppError(403, "forbidden", "You do not have access to this resource.")
        return self._student_or_404(institution_id, student_id)

    # ---------- batches ----------
    def create_batch(self, principal: Caller, body: BatchCreate) -> BatchOut:
        institution_id = self._require_teacher(principal)
        row = Batch(
            id=new_id("bat"),
            institution_id=institution_id,
            name=body.name.strip(),
            start_date=body.start_date.isoformat() if body.start_date else "",
            end_date=body.end_date.isoformat() if body.end_date else "",
        )
        self.db.save_batch(row)
        return self._batch_out(row)

    def update_batch(self, principal: Caller, batch_id: str, body: BatchUpdate) -> BatchOut:
        institution_id = self._require_teacher(principal)
        row = self._batch_or_404(institution_id, batch_id)
        changes = body.model_dump(exclude_unset=True)
        if "name" in changes and changes["name"] is not None:
            row.name = changes["name"].strip()
        if "start_date" in changes and changes["start_date"] is not None:
            row.start_date = changes["start_date"].isoformat()
        if "end_date" in changes and changes["end_date"] is not None:
            row.end_date = changes["end_date"].isoformat()
        if "status" in changes and changes["status"] is not None:
            row.status = changes["status"]
        self.db.save_batch(row)
        return self._batch_out(row)

    def list_batches(self, principal: Caller) -> list[BatchOut]:
        institution_id = self._active_institution(principal)
        rows = self.db.list_batches(institution_id)
        if principal.role == "student":
            student = self._own_student(principal)
            rows = [row for row in rows if row.id == student.batch_id]
        elif principal.role != "head_teacher":
            raise AppError(403, "forbidden", "You do not have access to this resource.")
        return [self._batch_out(row) for row in rows]

    def get_batch(self, principal: Caller, batch_id: str) -> BatchOut:
        institution_id = self._active_institution(principal)
        if principal.role == "student" and self._own_student(principal).batch_id != batch_id:
            raise AppError(404, "not_found", "Batch not found.")
        return self._batch_out(self._batch_or_404(institution_id, batch_id))

    # ---------- students ----------
    def create_student(self, principal: Caller, body: StudentCreate) -> StudentOut:
        institution_id = self._require_teacher(principal)
        self._batch_or_404(institution_id, body.batch_id)
        roll = body.roll_number.strip()
        if self._roll_taken(institution_id, roll):
            raise AppError(409, "roll_taken", "A student with this roll number already exists.")
        student_id = new_id("stu")
        full_name = f"{body.first_name.strip()} {body.last_name.strip()}".strip()
        user = User(
            id=student_id,
            institution_id=institution_id,
            role="student",
            full_name=full_name,
            phone=body.contact_number,
            email=str(body.email).lower(),
            password_hash=hash_password(body.password),
            student_id=student_id,
            roll_number=roll,
            must_change_password=True,
        )
        profile = StudentProfile(
            id=student_id,
            institution_id=institution_id,
            user_id=student_id,
            batch_id=body.batch_id,
            full_name=full_name,
            roll_number=roll,
            parent_phone=body.contact_number,
            parent_email=user.email,
        )
        self.auth.save_user(user)
        self.db.save_student(profile)
        session = getattr(self.auth, "session", None)
        if session is not None:
            session.flush()
        return self._student_out(profile)

    def update_student(self, principal: Caller, student_id: str, body: StudentUpdate) -> StudentOut:
        institution_id = self._require_teacher(principal)
        student = self._student_or_404(institution_id, student_id)
        changes = body.model_dump(exclude_unset=True)
        if "batch_id" in changes and changes["batch_id"]:
            self._batch_or_404(institution_id, changes["batch_id"])
            student.batch_id = changes["batch_id"]
        if "first_name" in changes or "last_name" in changes:
            parts = student.full_name.strip().split(None, 1)
            first = changes.get("first_name") or (parts[0] if parts else "")
            last = changes.get("last_name") or (parts[1] if len(parts) > 1 else "")
            student.full_name = f"{first} {last}".strip()
        if "contact_number" in changes and changes["contact_number"]:
            student.parent_phone = changes["contact_number"]
        if "email" in changes:
            student.parent_email = str(changes["email"]) if changes["email"] else None
        user = self.auth.get_user_by_id(student.user_id)
        if user:
            user.full_name = student.full_name
            user.phone = student.parent_phone
            user.email = student.parent_email
            if "is_active" in changes and changes["is_active"] is not None:
                user.is_active = changes["is_active"]
            self.auth.save_user(user)
        self.db.save_student(student)
        return self._student_out(student)

    def delete_student(self, principal: Caller, student_id: str) -> None:
        institution_id = self._require_teacher(principal)
        student = self._student_or_404(institution_id, student_id)
        user = self.auth.get_user_by_id(student.user_id)
        if user is None:
            raise AppError(404, "not_found", "Student not found.")
        user.is_active = False
        self.auth.save_user(user)

    def list_students(self, principal: Caller, batch_id: Optional[str] = None) -> list[StudentOut]:
        institution_id = self._active_institution(principal)
        if principal.role == "student":
            return [self._student_out(self._own_student(principal))]
        if principal.role != "head_teacher":
            raise AppError(403, "forbidden", "You do not have access to this resource.")
        if batch_id:
            self._batch_or_404(institution_id, batch_id)
        rows: list[StudentOut] = []
        for row in self.db.list_students(institution_id, batch_id):
            user = self.auth.get_user_by_id(row.user_id)
            if user is None or not user.is_active:
                continue
            rows.append(self._student_out(row))
        return rows

    def get_student(self, principal: Caller, student_id: str) -> StudentProfileOut:
        student = self._visible_student(principal, student_id)
        subjects = self._subject_scores(student.institution_id, student.id)
        focus_subject_id = self._primary_subject_id(student.institution_id, subjects)
        fee_row = self.db.find_fee(student.institution_id, student.id)
        return StudentProfileOut(
            student=self._student_out(student),
            subjects=subjects,
            chapters=self._chapter_analysis(student.institution_id, student.id, focus_subject_id),
            fee=self._fee_out(fee_row) if fee_row else None,
        )

    # ---------- catalog ----------
    def create_subject(self, principal: Caller, body: SubjectCreate) -> SubjectOut:
        institution_id = self._require_teacher(principal)
        row = Subject(id=new_id("sub"), institution_id=institution_id, name=body.name.strip(), description=body.description.strip())
        self.db.save_subject(row)
        return SubjectOut(id=row.id, name=row.name, description=row.description)

    def list_subjects(self, principal: Caller) -> list[SubjectOut]:
        institution_id = self._active_institution(principal)
        self._known_role(principal)
        return [SubjectOut(id=row.id, name=row.name, description=row.description) for row in self.db.list_subjects(institution_id)]

    def create_chapter(self, principal: Caller, body: ChapterCreate) -> ChapterOut:
        institution_id = self._require_teacher(principal)
        if self.db.get_subject(institution_id, body.subject_id) is None:
            raise AppError(404, "not_found", "Subject not found.")
        row = Chapter(id=new_id("ch"), institution_id=institution_id, subject_id=body.subject_id, name=body.name.strip())
        self.db.save_chapter(row)
        return ChapterOut(id=row.id, subject_id=row.subject_id, name=row.name)

    def list_chapters(self, principal: Caller, subject_id: Optional[str] = None) -> list[ChapterOut]:
        institution_id = self._active_institution(principal)
        self._known_role(principal)
        return [
            ChapterOut(id=row.id, subject_id=row.subject_id, name=row.name)
            for row in self.db.list_chapters(institution_id, subject_id)
        ]

    def create_topic(self, principal: Caller, body: TopicCreate) -> TopicOut:
        institution_id = self._require_teacher(principal)
        if self.db.get_chapter(institution_id, body.chapter_id) is None:
            raise AppError(404, "not_found", "Chapter not found.")
        row = Topic(id=new_id("top"), institution_id=institution_id, chapter_id=body.chapter_id, name=body.name.strip())
        self.db.save_topic(row)
        return TopicOut(id=row.id, chapter_id=row.chapter_id, name=row.name)

    def list_topics(self, principal: Caller, chapter_id: Optional[str] = None) -> list[TopicOut]:
        institution_id = self._active_institution(principal)
        self._known_role(principal)
        return [TopicOut(id=row.id, chapter_id=row.chapter_id, name=row.name) for row in self.db.list_topics(institution_id, chapter_id)]

    # ---------- attendance ----------
    def get_attendance_session(
        self,
        principal: Caller,
        batch_id: str,
        subject_id: str,
        on_date: Optional[date] = None,
    ) -> AttendanceSessionOut:
        institution_id = self._require_teacher(principal)
        batch = self._batch_or_404(institution_id, batch_id)
        subject = self.db.get_subject(institution_id, subject_id)
        if subject is None:
            raise AppError(404, "not_found", "Subject not found.")
        session_date = (on_date or self.today).isoformat()
        students = self.db.list_students(institution_id, batch_id)
        rows: list[AttendanceSessionStudentOut] = []
        for student in students:
            mark = self.db.find_attendance(institution_id, student.id, subject_id, session_date)
            parts = student.full_name.strip().split(None, 1)
            rows.append(
                AttendanceSessionStudentOut(
                    student_id=student.id,
                    first_name=parts[0],
                    last_name=parts[1] if len(parts) > 1 else "",
                    roll_number=student.roll_number,
                    status=mark.status if mark else None,  # type: ignore[arg-type]
                )
            )
        return AttendanceSessionOut(
            batch_id=batch.id,
            batch_name=batch.name,
            subject_id=subject.id,
            subject_name=subject.name,
            on_date=session_date,
            students=rows,
        )

    def mark_attendance(self, principal: Caller, body: AttendanceSessionIn) -> AttendanceSessionOut:
        institution_id = self._require_teacher(principal)
        self._batch_or_404(institution_id, body.batch_id)
        if self.db.get_subject(institution_id, body.subject_id) is None:
            raise AppError(404, "not_found", "Subject not found.")
        on_date = (body.on_date or self.today).isoformat()
        for entry in body.marks:
            student = self._student_or_404(institution_id, entry.student_id)
            if student.batch_id != body.batch_id:
                raise AppError(422, "batch_mismatch", "Student is not in this batch.")
            existing = self.db.find_attendance(institution_id, student.id, body.subject_id, on_date)
            row = existing or AttendanceMark(
                id=new_id("att"),
                institution_id=institution_id,
                student_id=student.id,
                batch_id=body.batch_id,
                subject_id=body.subject_id,
                on_date=on_date,
                status=entry.status,
                marked_by=principal.user_id,
            )
            row.status = entry.status
            row.marked_by = principal.user_id
            self.db.save_attendance(row)
        return self.get_attendance_session(
            principal,
            body.batch_id,
            body.subject_id,
            date.fromisoformat(on_date),
        )

    def list_attendance(
        self,
        principal: Caller,
        on_date: Optional[date] = None,
        batch_id: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> list[AttendanceOut]:
        institution_id = self._active_institution(principal)
        if principal.role == "student":
            student_id = self._own_student(principal).id
        elif principal.role != "head_teacher":
            raise AppError(403, "forbidden", "You do not have access to this resource.")
        elif student_id:
            self._student_or_404(institution_id, student_id)
        rows = self.db.list_attendance(
            institution_id,
            on_date=on_date.isoformat() if on_date else None,
            batch_id=batch_id,
            student_id=student_id,
        )
        return [self._attendance_out(row) for row in rows]

    # ---------- tests ----------
    def create_test(self, principal: Caller, body: TestCreate) -> TestOut:
        institution_id = self._require_teacher(principal)
        self._subject_chapter(institution_id, body.subject_id, body.chapter_id)
        if body.batch_id:
            self._batch_or_404(institution_id, body.batch_id)
        status = "Upcoming" if body.on_date > self.today else "Marks pending"
        row = Exam(
            id=new_id("tst"),
            institution_id=institution_id,
            name=body.name.strip(),
            subject_id=body.subject_id,
            chapter_id=body.chapter_id,
            batch_id=body.batch_id,
            on_date=body.on_date.isoformat(),
            max_marks=body.max_marks,
            status=status,
        )
        self.db.save_test(row)
        return self._test_out(principal, row)

    def add_question(self, principal: Caller, test_id: str, body: QuestionIn) -> QuestionOut:
        institution_id = self._require_teacher(principal)
        exam = self._test_or_404(institution_id, test_id)
        self._subject_chapter(institution_id, exam.subject_id, body.chapter_id)
        if self.db.get_topic(institution_id, body.topic_id) is None:
            raise AppError(404, "not_found", "Topic not found.")
        topic = self.db.get_topic(institution_id, body.topic_id)
        if topic and topic.chapter_id != body.chapter_id:
            raise AppError(422, "topic_mismatch", "Topic does not belong to this chapter.")
        row = ExamQuestion(
            id=new_id("q"),
            institution_id=institution_id,
            test_id=test_id,
            text=body.text.strip(),
            question_type=body.question_type,
            marks=body.marks,
            chapter_id=body.chapter_id,
            topic_id=body.topic_id,
            answer=body.answer.strip(),
        )
        self.db.save_question(row)
        return QuestionOut(
            id=row.id,
            text=row.text,
            question_type=row.question_type,  # type: ignore[arg-type]
            marks=row.marks,
            chapter_id=row.chapter_id,
            topic_id=row.topic_id,
            answer=row.answer,
        )

    def save_marks(self, principal: Caller, test_id: str, body: MarksIn) -> TestOut:
        institution_id = self._require_teacher(principal)
        exam = self._test_or_404(institution_id, test_id)
        for entry in body.entries:
            if entry.marks > exam.max_marks:
                raise AppError(422, "marks_exceeded", "Marks cannot exceed the test maximum.")
            student = self._student_or_404(institution_id, entry.student_id)
            if exam.batch_id and student.batch_id != exam.batch_id:
                raise AppError(422, "batch_mismatch", "Student is not in this test's batch.")
            existing = self.db.find_mark(institution_id, test_id, student.id)
            row = existing or ExamMark(
                id=new_id("mk"),
                institution_id=institution_id,
                test_id=test_id,
                student_id=student.id,
                marks=entry.marks,
            )
            row.marks = entry.marks
            self.db.save_mark(row)
        exam.status = "Done"
        self.db.save_test(exam)
        return self._test_out(principal, exam)

    def list_tests(self, principal: Caller) -> list[TestOut]:
        institution_id = self._active_institution(principal)
        batch_id = None
        if principal.role == "student":
            batch_id = self._own_student(principal).batch_id
        elif principal.role != "head_teacher":
            raise AppError(403, "forbidden", "You do not have access to this resource.")
        return [self._test_out(principal, row) for row in self.db.list_tests(institution_id, batch_id)]

    def get_test(self, principal: Caller, test_id: str) -> TestOut:
        institution_id = self._active_institution(principal)
        exam = self._test_or_404(institution_id, test_id)
        if principal.role == "student":
            batch_id = self._own_student(principal).batch_id
            if exam.batch_id not in (None, batch_id):
                raise AppError(404, "not_found", "Test not found.")
        elif principal.role != "head_teacher":
            raise AppError(403, "forbidden", "You do not have access to this resource.")
        return self._test_out(principal, exam)

    # ---------- fees ----------
    def set_fee_plan(self, principal: Caller, student_id: str, body: FeePlanIn) -> FeeOut:
        institution_id = self._require_teacher(principal)
        self._student_or_404(institution_id, student_id)
        existing = self.db.find_fee(institution_id, student_id)
        paid = min(existing.paid, body.total) if existing else 0
        row = existing or FeeAccount(
            id=new_id("fee"),
            institution_id=institution_id,
            student_id=student_id,
            total=body.total,
            paid=paid,
            due_date=body.due_date.isoformat(),
        )
        row.total = body.total
        row.paid = paid
        row.due_date = body.due_date.isoformat()
        self.db.save_fee(row)
        return self._fee_out(row)

    def record_payment(self, principal: Caller, student_id: str, body: PaymentIn) -> FeeOut:
        institution_id = self._require_teacher(principal)
        self._student_or_404(institution_id, student_id)
        row = self.db.find_fee(institution_id, student_id)
        if row is None:
            raise AppError(404, "not_found", "Fee plan not found.")
        if row.paid + body.amount > row.total:
            raise AppError(422, "payment_exceeds_balance", "Payment is larger than the balance.")
        row.paid += body.amount
        self.db.save_fee(row)
        return self._fee_out(row)

    def list_fees(self, principal: Caller) -> list[FeeOut]:
        institution_id = self._active_institution(principal)
        if principal.role == "student":
            row = self.db.find_fee(institution_id, self._own_student(principal).id)
            return [self._fee_out(row)] if row else []
        if principal.role != "head_teacher":
            raise AppError(403, "forbidden", "You do not have access to this resource.")
        return [self._fee_out(row) for row in self.db.list_fees(institution_id)]

    # ---------- notices ----------
    def create_notice(self, principal: Caller, body: NoticeCreate) -> NoticeOut:
        institution_id = self._require_teacher(principal)
        row = Notice(
            id=new_id("ntc"),
            institution_id=institution_id,
            title=body.title.strip(),
            content=body.content.strip(),
            date=(body.date or self.today).isoformat(),
            status=body.status,
            batch_id=None,
        )
        self.db.save_notice(row)
        return self._notice_out(row)

    def list_notices(self, principal: Caller) -> list[NoticeOut]:
        institution_id = self._active_institution(principal)
        batch_id = None
        if principal.role == "student":
            batch_id = self._own_student(principal).batch_id
        elif principal.role != "head_teacher":
            raise AppError(403, "forbidden", "You do not have access to this resource.")
        rows = self.db.list_notices(institution_id, batch_id)
        rows.sort(key=lambda row: row.date, reverse=True)
        return [self._notice_out(row) for row in rows]

    # ---------- dashboard ----------
    def dashboard(self, principal: Caller) -> DashboardOut:
        institution_id = self._require_teacher(principal)
        students = [self._student_out(row) for row in self.db.list_students(institution_id)]
        today = self.today.isoformat()
        marks = self.db.list_attendance(institution_id, on_date=today)
        return DashboardOut(
            batch_count=len(self.db.list_batches(institution_id)),
            student_count=len(students),
            present_today=sum(1 for row in marks if row.status in ("Present", "Late")),
            absent_today=sum(1 for row in marks if row.status == "Absent"),
            flagged=[row for row in students if row.flagged],
            notices=self.list_notices(principal)[:5],
        )

    # ---------- helpers ----------
    def _known_role(self, principal: Caller) -> None:
        if principal.role not in ("head_teacher", "student"):
            raise AppError(403, "forbidden", "You do not have access to this resource.")

    def _own_student(self, principal: Caller) -> StudentProfile:
        if principal.role != "student" or not principal.student_id:
            raise AppError(403, "forbidden", "You do not have access to this resource.")
        return self._student_or_404(principal.institution_id, principal.student_id)

    def _batch_or_404(self, institution_id: str, batch_id: str) -> Batch:
        row = self.db.get_batch(institution_id, batch_id)
        if row is None:
            raise AppError(404, "not_found", "Batch not found.")
        return row

    def _test_or_404(self, institution_id: str, test_id: str) -> Exam:
        row = self.db.get_test(institution_id, test_id)
        if row is None:
            raise AppError(404, "not_found", "Test not found.")
        return row

    def _subject_chapter(self, institution_id: str, subject_id: str, chapter_id: str) -> None:
        if self.db.get_subject(institution_id, subject_id) is None:
            raise AppError(404, "not_found", "Subject not found.")
        chapter = self.db.get_chapter(institution_id, chapter_id)
        if chapter is None or chapter.subject_id != subject_id:
            raise AppError(404, "not_found", "Chapter not found.")

    def _batch_out(self, row: Batch) -> BatchOut:
        count = len(self.db.list_students(row.institution_id, row.id))
        return BatchOut(
            id=row.id,
            name=row.name,
            start_date=row.start_date,
            end_date=row.end_date,
            status=row.status,
            student_count=count,
        )

    def _attendance_out(self, row: AttendanceMark) -> AttendanceOut:
        return AttendanceOut(
            id=row.id,
            student_id=row.student_id,
            batch_id=row.batch_id,
            subject_id=row.subject_id,
            on_date=row.on_date,
            status=row.status,  # type: ignore[arg-type]
        )

    def _fee_out(self, row: FeeAccount) -> FeeOut:
        balance = max(row.total - row.paid, 0)
        if balance == 0:
            status = "Paid"
        elif row.due_date < self.today.isoformat():
            status = "Overdue"
        else:
            status = "Partial"
        return FeeOut(
            student_id=row.student_id,
            total=row.total,
            paid=row.paid,
            balance=balance,
            due_date=row.due_date,
            status=status,  # type: ignore[arg-type]
        )

    def _notice_out(self, row: Notice) -> NoticeOut:
        return NoticeOut(
            id=row.id,
            title=row.title,
            content=row.content,
            date=row.date or None,
            status=row.status,
        )

    def _student_out(self, student: StudentProfile) -> StudentOut:
        attendance = self.db.list_attendance(student.institution_id, student_id=student.id)
        attended = sum(1 for row in attendance if row.status in ("Present", "Late"))
        attendance_pct = round(100 * attended / len(attendance), 1) if attendance else 0.0
        today_rows = [row for row in attendance if row.on_date == self.today.isoformat()]
        today = _day_status(today_rows)
        history = self._student_test_history(student.institution_id, student.id)
        percentages = [pct for _, _, pct in history]
        overall = round(sum(percentages) / len(percentages), 1) if percentages else None
        previous = round(sum(percentages[:-1]) / len(percentages[:-1]), 1) if len(percentages) >= 2 else None
        by_subject: dict[str, list[float]] = {}
        for exam, _, pct in history:
            by_subject.setdefault(exam.subject_id, []).append(pct)
        reasons = []
        if attendance and attendance_pct < ATTENDANCE_FLAG_BELOW:
            reasons.append(f"Attendance {attendance_pct}%")
        for subject_id, scores in by_subject.items():
            if len(scores) < 3:
                continue
            last3 = scores[-3:]
            if last3[1] < last3[0] and last3[2] < last3[1]:
                subject = self.db.get_subject(student.institution_id, subject_id)
                label = subject.name if subject else "A subject"
                reasons.append(f"{label} score dropped 3 tests in a row")
        fee = self.db.find_fee(student.institution_id, student.id)
        batch = self.db.get_batch(student.institution_id, student.batch_id)
        user = self.auth.get_user_by_id(student.user_id)
        parts = student.full_name.strip().split(None, 1)
        return StudentOut(
            id=student.id,
            first_name=parts[0],
            last_name=parts[1] if len(parts) > 1 else "",
            email=student.parent_email,
            contact_number=student.parent_phone,
            batch_id=student.batch_id,
            batch_name=batch.name if batch else "",
            roll_number=student.roll_number,
            is_active=user.is_active if user else True,
            attendance_pct=attendance_pct,
            overall_average=overall,
            previous_overall_average=previous,
            fee_status=self._fee_out(fee).status if fee else None,
            flagged=bool(reasons),
            flag_reason=". ".join(reasons) or None,
            today=today,
        )

    def _test_out(self, principal: Caller, exam: Exam) -> TestOut:
        subject = self.db.get_subject(exam.institution_id, exam.subject_id)
        chapter = self.db.get_chapter(exam.institution_id, exam.chapter_id)
        questions = [
            QuestionOut(
                id=row.id,
                text=row.text,
                question_type=row.question_type,  # type: ignore[arg-type]
                marks=row.marks,
                chapter_id=row.chapter_id,
                topic_id=row.topic_id,
                answer=row.answer if principal.role == "head_teacher" else "",
            )
            for row in self.db.list_questions(exam.institution_id, exam.id)
        ]
        mark_rows = self.db.list_marks(exam.institution_id, test_id=exam.id)
        percentages = [100 * row.marks / exam.max_marks for row in mark_rows]
        average = round(sum(percentages) / len(percentages), 1) if percentages else None
        if principal.role == "student":
            mark_rows = [row for row in mark_rows if row.student_id == principal.student_id]
        marks = [
            MarkOut(student_id=row.student_id, marks=row.marks, percentage=round(100 * row.marks / exam.max_marks, 1))
            for row in mark_rows
        ]
        return TestOut(
            id=exam.id,
            name=exam.name,
            subject_id=exam.subject_id,
            subject_name=subject.name if subject else "",
            chapter_id=exam.chapter_id,
            chapter_name=chapter.name if chapter else "",
            batch_id=exam.batch_id,
            on_date=exam.on_date,
            max_marks=exam.max_marks,
            status=exam.status,  # type: ignore[arg-type]
            batch_average=average,
            questions=questions,
            marks=marks,
        )


    def _student_test_history(self, institution_id: str, student_id: str) -> list[tuple[Exam, ExamMark, float]]:
        rows: list[tuple[Exam, ExamMark, float]] = []
        for mark in self.db.list_marks(institution_id, student_id=student_id):
            exam = self.db.get_test(institution_id, mark.test_id)
            if exam is None or exam.max_marks <= 0 or exam.status != "Done":
                continue
            rows.append((exam, mark, round(100 * mark.marks / exam.max_marks, 1)))
        rows.sort(key=lambda item: item[0].on_date)
        return rows

    def _subject_scores(self, institution_id: str, student_id: str) -> list[SubjectScoreOut]:
        by_subject: dict[str, list[tuple[Exam, float]]] = {}
        for exam, _, pct in self._student_test_history(institution_id, student_id):
            by_subject.setdefault(exam.subject_id, []).append((exam, pct))
        scores: list[SubjectScoreOut] = []
        for subject_id, tests in by_subject.items():
            subject = self.db.get_subject(institution_id, subject_id)
            if subject is None:
                continue
            pcts = [pct for _, pct in tests]
            last4 = pcts[-4:]
            latest_exam, latest = tests[-1]
            batch_pcts = [
                round(100 * row.marks / latest_exam.max_marks, 1)
                for row in self.db.list_marks(institution_id, test_id=latest_exam.id)
            ]
            batch_avg = round(sum(batch_pcts) / len(batch_pcts), 1) if batch_pcts else latest
            att_rows = [
                row for row in self.db.list_attendance(institution_id, student_id=student_id) if row.subject_id == subject_id
            ]
            attended = sum(1 for row in att_rows if row.status in ("Present", "Late"))
            scores.append(
                SubjectScoreOut(
                    subject=subject.name,
                    latest_score=latest,
                    last_4_scores=last4,
                    batch_average_diff=round(latest - batch_avg, 1),
                    subject_attendance_pct=round(100 * attended / len(att_rows), 1) if att_rows else 0.0,
                )
            )
        return scores

    def _primary_subject_id(self, institution_id: str, subjects: list[SubjectScoreOut]) -> Optional[str]:
        if not subjects:
            return None
        names = {row.name: row.id for row in self.db.list_subjects(institution_id)}
        return names.get(subjects[0].subject)

    def _chapter_analysis(
        self,
        institution_id: str,
        student_id: str,
        focus_subject_id: Optional[str] = None,
    ) -> list[ChapterAnalysisOut]:
        by_chapter: dict[str, list[float]] = {}
        chapter_tests: dict[str, list[str]] = {}
        for exam, _, pct in self._student_test_history(institution_id, student_id):
            if focus_subject_id and exam.subject_id != focus_subject_id:
                continue
            by_chapter.setdefault(exam.chapter_id, []).append(pct)
            chapter_tests.setdefault(exam.chapter_id, []).append(exam.id)
        chapters: list[ChapterAnalysisOut] = []
        for chapter_id, pcts in by_chapter.items():
            chapter = self.db.get_chapter(institution_id, chapter_id)
            if chapter is None:
                continue
            subject = self.db.get_subject(institution_id, chapter.subject_id)
            score_pct = round(sum(pcts) / len(pcts), 1)
            topics: list[TopicScoreOut] = []
            for topic in self.db.list_topics(institution_id, chapter_id):
                attempted = sum(
                    1
                    for test_id in chapter_tests[chapter_id]
                    for question in self.db.list_questions(institution_id, test_id)
                    if question.topic_id == topic.id
                )
                topics.append(
                    TopicScoreOut(
                        id=topic.id,
                        name=topic.name,
                        chapter_id=chapter.id,
                        score_pct=score_pct if attempted else 0.0,
                        attempted=attempted,
                    )
                )
            chapters.append(
                ChapterAnalysisOut(
                    id=chapter.id,
                    name=chapter.name,
                    subject=subject.name if subject else "",
                    score_pct=score_pct,
                    topics=topics,
                )
            )
        return chapters


def _day_status(rows: list[AttendanceMark]) -> Optional[str]:
    if not rows:
        return None
    statuses = {row.status for row in rows}
    if "Absent" in statuses:
        return "Absent"
    if "Late" in statuses:
        return "Late"
    return "Present"
