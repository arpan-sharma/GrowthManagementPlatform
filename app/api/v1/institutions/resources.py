"""Institute resources. Tenant id always comes from the access token, never the request body."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import Principal, get_platform_service, get_principal, require_head_teacher
from app.schemas.platform import (
    AttendanceOut,
    AttendanceSessionIn,
    AttendanceSessionOut,
    StudentProfileOut,
    BatchCreate,
    BatchOut,
    BatchUpdate,
    ChapterCreate,
    ChapterOut,
    DashboardOut,
    FeeOut,
    FeePlanIn,
    NoticeCreate,
    NoticeOut,
    PaymentIn,
    QuestionIn,
    QuestionOut,
    StudentCreate,
    StudentOut,
    StudentUpdate,
    SubjectCreate,
    SubjectOut,
    TestCreate,
    TestOut,
    TopicCreate,
    TopicOut,
    MarksIn,
)
from app.services.platform_service import PlatformService

router = APIRouter(tags=["institute"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.dashboard(principal)


@router.post("/batches", response_model=BatchOut, status_code=201)
def create_batch(
    body: BatchCreate,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.create_batch(principal, body)


@router.get("/batches", response_model=list[BatchOut])
def list_batches(
    principal: Principal = Depends(get_principal),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.list_batches(principal)


@router.get("/batches/{batch_id}", response_model=BatchOut)
def get_batch(
    batch_id: str,
    principal: Principal = Depends(get_principal),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.get_batch(principal, batch_id)


@router.patch("/batches/{batch_id}", response_model=BatchOut)
def update_batch(
    batch_id: str,
    body: BatchUpdate,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.update_batch(principal, batch_id, body)


@router.post("/students", response_model=StudentOut, status_code=201)
def create_student(
    body: StudentCreate,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.create_student(principal, body)


@router.get("/students", response_model=list[StudentOut])
def list_students(
    batch_id: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.list_students(principal, batch_id)


@router.get("/students/{student_id}", response_model=StudentProfileOut)
def get_student(
    student_id: str,
    principal: Principal = Depends(get_principal),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.get_student(principal, student_id)


@router.patch("/students/{student_id}", response_model=StudentOut)
def update_student(
    student_id: str,
    body: StudentUpdate,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.update_student(principal, student_id, body)


@router.delete("/students/{student_id}", status_code=204)
def delete_student(
    student_id: str,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    svc.delete_student(principal, student_id)
    return Response(status_code=204)


@router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(
    body: SubjectCreate,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.create_subject(principal, body)


@router.get("/subjects", response_model=list[SubjectOut])
def list_subjects(
    principal: Principal = Depends(get_principal),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.list_subjects(principal)


@router.post("/chapters", response_model=ChapterOut, status_code=201)
def create_chapter(
    body: ChapterCreate,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.create_chapter(principal, body)


@router.get("/chapters", response_model=list[ChapterOut])
def list_chapters(
    subject_id: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.list_chapters(principal, subject_id)


@router.post("/topics", response_model=TopicOut, status_code=201)
def create_topic(
    body: TopicCreate,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.create_topic(principal, body)


@router.get("/topics", response_model=list[TopicOut])
def list_topics(
    chapter_id: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.list_topics(principal, chapter_id)


@router.get("/attendance/session", response_model=AttendanceSessionOut)
def get_attendance_session(
    batch_id: str,
    subject_id: str,
    on_date: Optional[date] = None,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.get_attendance_session(principal, batch_id, subject_id, on_date)


@router.post("/attendance/session", response_model=AttendanceSessionOut, status_code=201)
def save_attendance_session(
    body: AttendanceSessionIn,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.mark_attendance(principal, body)


@router.post("/attendance", response_model=AttendanceSessionOut, status_code=201)
def mark_attendance(
    body: AttendanceSessionIn,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.mark_attendance(principal, body)


@router.get("/attendance", response_model=list[AttendanceOut])
def list_attendance(
    on_date: Optional[date] = None,
    batch_id: Optional[str] = None,
    student_id: Optional[str] = Query(default=None),
    principal: Principal = Depends(get_principal),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.list_attendance(principal, on_date, batch_id, student_id)


@router.post("/tests", response_model=TestOut, status_code=201)
def create_test(
    body: TestCreate,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.create_test(principal, body)


@router.get("/tests", response_model=list[TestOut])
def list_tests(
    principal: Principal = Depends(get_principal),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.list_tests(principal)


@router.get("/tests/{test_id}", response_model=TestOut)
def get_test(
    test_id: str,
    principal: Principal = Depends(get_principal),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.get_test(principal, test_id)


@router.post("/tests/{test_id}/questions", response_model=QuestionOut, status_code=201)
def add_question(
    test_id: str,
    body: QuestionIn,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.add_question(principal, test_id, body)


@router.put("/tests/{test_id}/marks", response_model=TestOut)
def save_marks(
    test_id: str,
    body: MarksIn,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.save_marks(principal, test_id, body)


@router.put("/fees/{student_id}", response_model=FeeOut)
def set_fee_plan(
    student_id: str,
    body: FeePlanIn,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.set_fee_plan(principal, student_id, body)


@router.post("/fees/{student_id}/payments", response_model=FeeOut, status_code=201)
def record_payment(
    student_id: str,
    body: PaymentIn,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.record_payment(principal, student_id, body)


@router.get("/fees", response_model=list[FeeOut])
def list_fees(
    principal: Principal = Depends(get_principal),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.list_fees(principal)


@router.post("/notices", response_model=NoticeOut, status_code=201)
def create_notice(
    body: NoticeCreate,
    principal: Principal = Depends(require_head_teacher),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.create_notice(principal, body)


@router.get("/notices", response_model=list[NoticeOut])
def list_notices(
    principal: Principal = Depends(get_principal),
    svc: PlatformService = Depends(get_platform_service),
):
    return svc.list_notices(principal)
