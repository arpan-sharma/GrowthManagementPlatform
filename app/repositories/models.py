from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class Institution:
    id: str
    name: str
    code: str
    city: str
    phone: str
    email: str
    status: str  # pending_review | active | suspended


@dataclass
class User:
    id: str
    institution_id: str
    role: str
    full_name: str
    password_hash: str
    email: Optional[str] = None
    phone: Optional[str] = None
    student_id: Optional[str] = None
    roll_number: Optional[str] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    must_change_password: bool = False
    consent_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class RefreshToken:
    id: str
    user_id: str
    family_id: str
    token_hash: str
    expires_at: datetime
    ip: Optional[str] = None
    user_agent: str = ""
    revoked_at: Optional[datetime] = None
    replaced_by: Optional[str] = None


@dataclass
class AuditEvent:
    action: str
    institution_id: Optional[str]
    user_id: Optional[str]
    ip: Optional[str]
    meta: Optional[dict[str, Any]]
    at: datetime
