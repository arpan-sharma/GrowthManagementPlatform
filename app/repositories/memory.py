"""In-memory auth store. Swap this for a SQL repository later; callers stay the same."""
from datetime import datetime
from typing import Any, Optional

from app.core.config import Settings
from app.core.security import hash_password, utcnow
from app.repositories.academic import InMemoryAcademicRepository, seed_demo_class
from app.repositories.base import AuthRepository
from app.repositories.models import AuditEvent, Institution, RefreshToken, User


class InMemoryAuthRepository(AuthRepository):
    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.by_email: dict[str, str] = {}
        self.institutions: dict[str, Institution] = {}
        self.by_code: dict[str, str] = {}
        self.refreshes: dict[str, RefreshToken] = {}
        self.refresh_by_hash: dict[str, str] = {}
        self.audit: list[AuditEvent] = []
        self.academic = InMemoryAcademicRepository()

    def get_user_by_email(self, email: str) -> Optional[User]:
        user_id = self.by_email.get(email.lower())
        return self.users.get(user_id) if user_id else None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    def get_student_by_roll(self, institution_id: str, roll_number: str) -> Optional[User]:
        for user in self.users.values():
            if (
                user.institution_id == institution_id
                and user.role == "student"
                and user.roll_number == roll_number
            ):
                return user
        return None

    def save_user(self, user: User) -> None:
        self.users[user.id] = user
        if user.email:
            self.by_email[user.email.lower()] = user.id

    def get_institution(self, institution_id: str) -> Optional[Institution]:
        return self.institutions.get(institution_id)

    def get_institution_by_code(self, code: str) -> Optional[Institution]:
        inst_id = self.by_code.get(code.upper())
        return self.institutions.get(inst_id) if inst_id else None

    def create_institution_with_admin(self, institution: Institution, user: User) -> None:
        self.institutions[institution.id] = institution
        self.by_code[institution.code.upper()] = institution.id
        self.save_user(user)

    def add_refresh(self, token: RefreshToken) -> None:
        self.refreshes[token.id] = token
        self.refresh_by_hash[token.token_hash] = token.id

    def save_refresh(self, token: RefreshToken) -> None:
        self.refreshes[token.id] = token
        self.refresh_by_hash[token.token_hash] = token.id

    def get_refresh_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        token_id = self.refresh_by_hash.get(token_hash)
        return self.refreshes.get(token_id) if token_id else None

    def revoke_family(self, family_id: str, now: datetime) -> None:
        for token in self.refreshes.values():
            if token.family_id == family_id and token.revoked_at is None:
                token.revoked_at = now

    def revoke_all_for_user(self, user_id: str, now: datetime, except_family: Optional[str] = None) -> None:
        for token in self.refreshes.values():
            if token.user_id != user_id or token.revoked_at is not None:
                continue
            if except_family and token.family_id == except_family:
                continue
            token.revoked_at = now

    def add_audit(
        self,
        action: str,
        institution_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip: Optional[str] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> None:
        self.audit.append(
            AuditEvent(
                action=action,
                institution_id=institution_id,
                user_id=user_id,
                ip=ip,
                meta=meta,
                at=utcnow(),
            )
        )


def seed_dev_data(repo: InMemoryAuthRepository, settings: Settings) -> None:
    """Development-only head teacher. Not created when ENVIRONMENT=production."""
    institution = Institution(
        id="inst_demo",
        name="Demo Institute",
        code="DEMO01",
        city="Pune",
        phone="+919800000000",
        email="admin@gmail.com",
        status="active",
    )
    admin = User(
        id="usr_admin",
        institution_id=institution.id,
        role="head_teacher",
        full_name="Dev Admin",
        email="admin@gmail.com",
        phone="+919800000000",
        password_hash=hash_password("admin", rounds=settings.bcrypt_rounds),
        must_change_password=False,
    )
    repo.create_institution_with_admin(institution, admin)
    seed_demo_class(repo, settings)
