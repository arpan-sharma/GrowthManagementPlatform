from fastapi import FastAPI

from services.api.attendance.routes import router as attendance_router
from services.api.students.routes import router as students_router

app = FastAPI(title="GMP")
app.include_router(students_router)
app.include_router(attendance_router)
