"""Request and response models for institute academic APIs."""
import re
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

AttendanceStatus = Literal["Present", "Late", "Absent"]
FeeStatus = Literal["Paid", "Partial", "Overdue"]
TestStatus = Literal["Upcoming", "Marks pending", "Done"]
QuestionType = Literal["MCQ", "Short answer", "Numerical"]
_PASSWORD = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


class BatchCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class BatchUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[Literal["active", "archived"]] = None


class BatchOut(BaseModel):
    id: str
    name: str
    start_date: str
    end_date: str
    status: str
    student_count: int


class StudentCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: EmailStr
    contact_number: str = Field(pattern=r"^\+?[0-9]{10,15}$")
    roll_number: str = Field(min_length=1, max_length=40)
    batch_id: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not _PASSWORD.fullmatch(value):
            raise ValueError("Password must be at least 8 characters and include a letter and a number.")
        return value


class StudentUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=60)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=60)
    email: Optional[EmailStr] = None
    contact_number: Optional[str] = Field(default=None, pattern=r"^\+?[0-9]{10,15}$")
    batch_id: Optional[str] = None


class StudentOut(BaseModel):
    """users + students columns, plus computed fields used by the frontend."""
    id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    contact_number: str
    batch_id: str
    batch_name: str = ""
    roll_number: str
    is_active: bool = True
    attendance_pct: float = 0
    overall_average: Optional[float] = None
    previous_overall_average: Optional[float] = None
    fee_status: Optional[FeeStatus] = None
    flagged: bool = False
    flag_reason: Optional[str] = None
    today: Optional[AttendanceStatus] = None


class SubjectScoreOut(BaseModel):
    subject: str
    latest_score: float
    last_4_scores: list[float]
    batch_average_diff: float
    subject_attendance_pct: float


class TopicScoreOut(BaseModel):
    id: str
    name: str
    chapter_id: str
    score_pct: float
    attempted: int


class ChapterAnalysisOut(BaseModel):
    id: str
    name: str
    subject: str
    score_pct: float
    topics: list[TopicScoreOut]


class SubjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str = ""


class SubjectOut(BaseModel):
    id: str
    name: str
    description: str


class ChapterCreate(BaseModel):
    subject_id: str
    name: str = Field(min_length=2, max_length=120)


class ChapterOut(BaseModel):
    id: str
    subject_id: str
    name: str


class TopicCreate(BaseModel):
    chapter_id: str
    name: str = Field(min_length=2, max_length=120)


class TopicOut(BaseModel):
    id: str
    chapter_id: str
    name: str


class AttendanceEntry(BaseModel):
    student_id: str
    status: AttendanceStatus


class AttendanceSessionIn(BaseModel):
    batch_id: str
    subject_id: str
    on_date: Optional[date] = None
    marks: list[AttendanceEntry] = Field(min_length=1)


class AttendanceSessionStudentOut(BaseModel):
    student_id: str
    first_name: str
    last_name: str
    roll_number: str
    status: Optional[AttendanceStatus] = None


class AttendanceSessionOut(BaseModel):
    batch_id: str
    batch_name: str
    subject_id: str
    subject_name: str
    on_date: str
    students: list[AttendanceSessionStudentOut]


class AttendanceOut(BaseModel):
    id: str
    student_id: str
    batch_id: str
    subject_id: str
    on_date: str
    status: AttendanceStatus


class QuestionIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    question_type: QuestionType
    marks: int = Field(ge=1, le=100)
    chapter_id: str
    topic_id: str
    answer: str = ""


class QuestionOut(QuestionIn):
    id: str


class TestCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    subject_id: str
    chapter_id: str
    batch_id: Optional[str] = None
    on_date: date
    max_marks: int = Field(ge=1, le=1000)


class MarkEntry(BaseModel):
    student_id: str
    marks: int = Field(ge=0)


class MarksIn(BaseModel):
    entries: list[MarkEntry] = Field(min_length=1)


class MarkOut(BaseModel):
    student_id: str
    marks: int
    percentage: float


class TestOut(BaseModel):
    id: str
    name: str
    subject_id: str
    subject_name: str
    chapter_id: str
    chapter_name: str
    batch_id: Optional[str] = None
    on_date: str
    max_marks: int
    status: TestStatus
    batch_average: Optional[float] = None
    questions: list[QuestionOut]
    marks: list[MarkOut]


class FeePlanIn(BaseModel):
    total: int = Field(gt=0)
    due_date: date


class PaymentIn(BaseModel):
    amount: int = Field(gt=0)


class FeeOut(BaseModel):
    student_id: str
    total: int
    paid: int
    balance: int
    due_date: str
    status: FeeStatus


class StudentProfileOut(BaseModel):
    student: StudentOut
    subjects: list[SubjectScoreOut]
    chapters: list[ChapterAnalysisOut]
    fee: Optional[FeeOut] = None


class NoticeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=2000)
    date: Optional[date] = None
    status: str = "active"


class NoticeOut(BaseModel):
    id: str
    title: str
    content: str
    date: Optional[str] = None
    status: str = "active"


class DashboardOut(BaseModel):
    batch_count: int
    student_count: int
    present_today: int
    absent_today: int
    flagged: list[StudentOut]
    notices: list[NoticeOut]
