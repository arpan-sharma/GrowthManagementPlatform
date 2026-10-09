from dataclasses import dataclass
from datetime import date
from enum import Enum


class TestStatus(str, Enum):
    UPCOMING = "upcoming"
    MARKS_PENDING = "marks_pending"
    DONE = "done"


@dataclass
class Test:
    id: str
    name: str
    batch_id: str
    subject_id: str
    date: date
    max_marks: int
    description: str = ""
    status: TestStatus = TestStatus.UPCOMING
