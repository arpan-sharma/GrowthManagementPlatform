from pydantic import BaseModel, Field


class StudentResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    contact_number: str
    batch_id: str
    batch_name: str
    is_active: bool
    today: str | None = None
    attendance_pct: int | None = None


class StudentCreate(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)
    contact_number: str = Field(min_length=1)
    batch_id: str = Field(min_length=1)
