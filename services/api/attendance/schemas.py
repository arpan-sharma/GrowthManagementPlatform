from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"


class AttendanceCreate(BaseModel):
    student_id: str = Field(min_length=1)
    date: date
    status: AttendanceStatus
    marked_by: str | None = None


class AttendanceResponse(BaseModel):
    id: str
    student_id: str
    date: date
    status: AttendanceStatus
    marked_by: str | None
