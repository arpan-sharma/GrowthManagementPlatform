import re
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

_PASSWORD = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


def _strong_password(value: str) -> str:
    if not _PASSWORD.fullmatch(value):
        raise ValueError("Password must be at least 8 characters and include a letter and a number.")
    return value


class InstituteIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=80)
    phone: str = Field(pattern=r"^\+?[0-9]{10,15}$")
    email: EmailStr


class HeadTeacherIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(pattern=r"^\+?[0-9]{10,15}$")
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return _strong_password(value)


class ConsentIn(BaseModel):
    terms_accepted: bool
    privacy_accepted: bool

    @model_validator(mode="after")
    def both_required(self):
        if not self.terms_accepted or not self.privacy_accepted:
            raise ValueError("Terms and privacy policy must be accepted.")
        return self


class SignupRequest(BaseModel):
    institute: InstituteIn
    head_teacher: HeadTeacherIn
    consent: ConsentIn


class SignupResponse(BaseModel):
    institution_id: str
    status: Literal["pending_review", "active", "suspended"]
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class StudentLoginRequest(BaseModel):
    institution_code: str = Field(min_length=2, max_length=20)
    roll_number: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=1, max_length=200)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return _strong_password(value)


class UserOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    contact_number: str = ""
    role: str
    institution_id: str
    must_change_password: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserOut


class MeResponse(UserOut):
    institution_name: str
    institution_code: str
