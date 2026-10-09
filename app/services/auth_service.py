import re
import secrets
from datetime import timedelta
from typing import Optional

from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import (
    create_access_token,
    dummy_verify,
    hash_password,
    hash_token,
    new_id,
    new_refresh_token,
    utcnow,
    verify_password,
)
from app.repositories.base import AuthRepository
from app.repositories.models import Institution, RefreshToken, User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    SignupRequest,
    SignupResponse,
    StudentLoginRequest,
    TokenResponse,
    UserOut,
)

IssuedTokens = tuple[TokenResponse, str, int]  # (body, raw_refresh_token, refresh_ttl_seconds)


def _invalid() -> AppError:
    # One generic message for every credential failure (no user enumeration)
    return AppError(401, "invalid_credentials", "Invalid credentials.")


def _invalid_refresh() -> AppError:
    return AppError(401, "invalid_refresh_token", "Session expired. Please sign in again.")


class AuthService:
    def __init__(self, repo: AuthRepository, settings: Settings):
        self.repo = repo
        self.s = settings

    # ---------------- signup ----------------
    def signup(self, req: SignupRequest, ip: Optional[str]) -> SignupResponse:
        email = req.head_teacher.email.lower()
        if self.repo.get_user_by_email(email):
            raise AppError(409, "email_taken", "An account with this email already exists.")
        now = utcnow()
        inst = Institution(
            id=new_id("inst"),
            name=req.institute.name.strip(),
            code=self._make_code(req.institute.name),
            city=req.institute.city.strip(),
            phone=req.institute.phone,
            email=req.institute.email.lower(),
            status="pending_review",  # flip to "active" to skip manual approval
        )
        user = User(
            id=new_id("usr"),
            institution_id=inst.id,
            role="head_teacher",
            full_name=req.head_teacher.full_name.strip(),
            email=email,
            phone=req.head_teacher.phone,
            password_hash=hash_password(req.head_teacher.password),
            consent_at=now,  # DPDP: record when consent was given
        )
        self.repo.create_institution_with_admin(inst, user)  # atomic
        self.repo.add_audit("signup", inst.id, user.id, ip)
        return SignupResponse(
            institution_id=inst.id,
            status=inst.status,  # type: ignore[arg-type]
            message="Thanks for signing up. We will contact you shortly.",
        )

    def _make_code(self, name: str) -> str:
        base = re.sub(r"[^A-Za-z0-9]", "", name).upper()[:6] or "INST"
        while True:
            code = f"{base}{secrets.randbelow(100):02d}"
            if not self.repo.get_institution_by_code(code):
                return code

    # ---------------- login ----------------
    def login_head_teacher(self, req: LoginRequest, ip, ua) -> IssuedTokens:
        user = self.repo.get_user_by_email(req.email.lower())
        if user is not None and user.role != "head_teacher":
            user = None
        return self._login(user, req.password, ip, ua)

    def login_student(self, req: StudentLoginRequest, ip, ua) -> IssuedTokens:
        inst = self.repo.get_institution_by_code(req.institution_code.strip().upper())
        user = self.repo.get_student_by_roll(inst.id, req.roll_number.strip()) if inst else None
        return self._login(user, req.password, ip, ua)

    def _login(self, user: Optional[User], password: str, ip, ua) -> IssuedTokens:
        now = utcnow()
        if user is None:
            dummy_verify(password)
            self.repo.add_audit("login_failed", ip=ip, meta={"reason": "unknown_user"})
            raise _invalid()

        if user.locked_until and user.locked_until > now:
            wait = int((user.locked_until - now).total_seconds())
            raise AppError(
                423, "account_locked", "Too many attempts. Try again later.",
                headers={"Retry-After": str(wait)},
            )

        if not verify_password(password, user.password_hash):
            user.failed_attempts += 1
            if user.failed_attempts >= self.s.max_failed_attempts:
                user.locked_until = now + timedelta(seconds=self.s.lockout_seconds)
                user.failed_attempts = 0
                self.repo.add_audit("account_locked", user.institution_id, user.id, ip)
            self.repo.save_user(user)
            self.repo.add_audit("login_failed", user.institution_id, user.id, ip)
            raise _invalid()

        inst = self.repo.get_institution(user.institution_id)
        if inst is None or inst.status == "suspended":
            raise AppError(403, "account_suspended", "This account is suspended.")
        if inst.status == "pending_review":
            raise AppError(403, "account_pending", "Your institute is awaiting approval.")

        user.failed_attempts = 0
        user.locked_until = None
        self.repo.save_user(user)
        self.repo.add_audit("login_success", inst.id, user.id, ip)
        return self._issue(user, new_id("fam"), ip, ua)

    # ---------------- tokens ----------------
    def _issue(self, user: User, family_id: str, ip, ua, replaces: Optional[RefreshToken] = None) -> IssuedTokens:
        now = utcnow()
        ttl = (
            self.s.refresh_ttl_student_seconds
            if user.role == "student"
            else self.s.refresh_ttl_head_teacher_seconds
        )
        raw = new_refresh_token()
        rec = RefreshToken(
            id=new_id("rt"),
            user_id=user.id,
            family_id=family_id,
            token_hash=hash_token(raw),  # only the hash is stored
            expires_at=now + timedelta(seconds=ttl),
            ip=ip,
            user_agent=(ua or "")[:255],
        )
        self.repo.add_refresh(rec)
        if replaces:
            replaces.revoked_at = now
            replaces.replaced_by = rec.id
            self.repo.save_refresh(replaces)
        body = TokenResponse(
            access_token=create_access_token(user, self.s),
            expires_in=self.s.access_token_ttl_seconds,
            user=self._user_out(user),
        )
        return body, raw, ttl

    def refresh(self, raw: Optional[str], ip, ua) -> IssuedTokens:
        if not raw:
            raise _invalid_refresh()
        rec = self.repo.get_refresh_by_hash(hash_token(raw))
        if rec is None:
            raise _invalid_refresh()
        now = utcnow()
        if rec.revoked_at is not None:
            if rec.replaced_by:  # a rotated-out token was replayed => likely stolen
                self.repo.revoke_family(rec.family_id, now)
                self.repo.add_audit("refresh_reuse_detected", None, rec.user_id, ip)
                raise AppError(401, "token_reuse_detected", "Session invalidated. Please sign in again.")
            raise _invalid_refresh()  # revoked via logout
        if rec.expires_at <= now:
            raise _invalid_refresh()
        user = self.repo.get_user_by_id(rec.user_id)
        inst = self.repo.get_institution(user.institution_id) if user else None
        if not user or not inst or inst.status != "active":
            self.repo.revoke_family(rec.family_id, now)
            raise _invalid_refresh()
        return self._issue(user, rec.family_id, ip, ua, replaces=rec)  # rotation

    def logout(self, user_id: str, raw: Optional[str], ip) -> None:
        if raw:
            rec = self.repo.get_refresh_by_hash(hash_token(raw))
            if rec and rec.user_id == user_id:
                self.repo.revoke_family(rec.family_id, utcnow())
        self.repo.add_audit("logout", None, user_id, ip)

    def logout_all(self, user_id: str, ip) -> None:
        self.repo.revoke_all_for_user(user_id, utcnow())
        self.repo.add_audit("logout_all", None, user_id, ip)

    # ---------------- account ----------------
    def me(self, user_id: str):
        user = self.repo.get_user_by_id(user_id)
        inst = self.repo.get_institution(user.institution_id) if user else None
        if not user or not inst:
            raise AppError(401, "invalid_token", "Invalid or expired token.")
        return user, inst

    def change_password(self, user_id: str, req: ChangePasswordRequest, current_raw_refresh: Optional[str], ip) -> None:
        user = self.repo.get_user_by_id(user_id)
        if not user or not verify_password(req.current_password, user.password_hash):
            raise AppError(400, "wrong_password", "Current password is incorrect.")
        if req.new_password == req.current_password:
            raise AppError(422, "password_unchanged", "New password must differ from the current one.")
        user.password_hash = hash_password(req.new_password)
        user.must_change_password = False
        self.repo.save_user(user)
        keep = None
        if current_raw_refresh:
            rec = self.repo.get_refresh_by_hash(hash_token(current_raw_refresh))
            if rec and rec.user_id == user.id:
                keep = rec.family_id
        self.repo.revoke_all_for_user(user.id, utcnow(), except_family=keep)
        self.repo.add_audit("password_changed", user.institution_id, user.id, ip)

    @staticmethod
    def _user_out(user: User) -> UserOut:
        parts = user.full_name.strip().split(None, 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""
        return UserOut(
            id=user.id,
            first_name=first_name,
            last_name=last_name,
            role=user.role,
            institution_id=user.institution_id,
            email=user.email,
            contact_number=user.phone or "",
            must_change_password=user.must_change_password,
        )
