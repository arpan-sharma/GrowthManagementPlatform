from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.api.attendance.schemas import AttendanceCreate, AttendanceResponse
from services.db.session import get_session
from services.db.tables import Attendance, Student, User

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("", response_model=AttendanceResponse, status_code=201)
def mark_attendance(
    body: AttendanceCreate, session: Session = Depends(get_session)
) -> AttendanceResponse:
    student = session.get(Student, body.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    marked_by = body.marked_by.strip() if body.marked_by else None
    if marked_by is not None and session.get(User, marked_by) is None:
        raise HTTPException(status_code=404, detail="User who marked attendance was not found")

    existing = session.scalar(
        select(Attendance).where(
            Attendance.student_id == body.student_id,
            Attendance.date == body.date,
        )
    )
    if existing is not None:
        existing.status = body.status.value
        existing.marked_by = marked_by
        session.commit()
        return AttendanceResponse(
            id=existing.id,
            student_id=existing.student_id,
            date=existing.date,
            status=body.status,
            marked_by=existing.marked_by,
        )

    attendance_id = f"A{uuid4().hex[:6].upper()}"
    row = Attendance(
        id=attendance_id,
        student_id=body.student_id,
        date=body.date,
        status=body.status.value,
        marked_by=marked_by,
    )
    session.add(row)
    session.commit()
    return AttendanceResponse(
        id=attendance_id,
        student_id=body.student_id,
        date=body.date,
        status=body.status,
        marked_by=marked_by,
    )
