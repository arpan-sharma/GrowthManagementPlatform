from collections import defaultdict
from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from services.api.students.schemas import StudentCreate, StudentResponse
from services.db.session import get_session
from services.db.tables import Attendance, Batch, Student, User

router = APIRouter(prefix="/students", tags=["students"])

TODAY_LABEL = {"present": "Present", "late": "Late", "absent": "Absent"}


def _attendance_summary(session: Session, student_ids: list[str]) -> dict[str, tuple[str | None, int | None]]:
    if not student_ids:
        return {}
    marks = session.scalars(select(Attendance).where(Attendance.student_id.in_(student_ids))).all()
    grouped: dict[str, list] = defaultdict(list)
    for mark in marks:
        grouped[mark.student_id].append(mark)

    today = date.today()
    summary: dict[str, tuple[str | None, int | None]] = {}
    for student_id in student_ids:
        rows = grouped.get(student_id, [])
        today_mark = next((row.status for row in rows if row.date == today), None)
        today_label = TODAY_LABEL.get(today_mark) if today_mark else None
        if not rows:
            summary[student_id] = (today_label, None)
            continue
        attended = sum(1 for row in rows if row.status in ("present", "late"))
        summary[student_id] = (today_label, round(attended * 100 / len(rows)))
    return summary


@router.get("", response_model=list[StudentResponse])
def get_students(session: Session = Depends(get_session)) -> list[StudentResponse]:
    rows = session.execute(
        select(User, Student.batch_id, Batch.name)
        .join(Student, Student.id == User.id)
        .join(Batch, Batch.id == Student.batch_id)
        .order_by(User.first_name, User.last_name)
    ).all()
    summary = _attendance_summary(session, [user.id for user, _, _ in rows])
    return [
        StudentResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            contact_number=user.contact_number,
            batch_id=batch_id,
            batch_name=batch_name,
            is_active=user.is_active,
            today=summary[user.id][0],
            attendance_pct=summary[user.id][1],
        )
        for user, batch_id, batch_name in rows
    ]


@router.post("", response_model=StudentResponse, status_code=201)
def add_student(body: StudentCreate, session: Session = Depends(get_session)) -> StudentResponse:
    batch = session.get(Batch, body.batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    email = body.email.strip()
    existing = session.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already exists")

    student_id = f"S{uuid4().hex[:6].upper()}"
    session.add(
        User(
            id=student_id,
            first_name=body.first_name.strip(),
            last_name=body.last_name.strip(),
            email=email,
            password=body.password,
            contact_number=body.contact_number.strip(),
            role="student",
            is_active=True,
        )
    )
    session.flush()
    session.add(Student(id=student_id, batch_id=batch.id))
    session.commit()

    return StudentResponse(
        id=student_id,
        first_name=body.first_name.strip(),
        last_name=body.last_name.strip(),
        email=email,
        contact_number=body.contact_number.strip(),
        batch_id=batch.id,
        batch_name=batch.name,
        is_active=True,
    )
