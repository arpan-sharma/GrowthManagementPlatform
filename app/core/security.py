"""Password hashing, JWT access tokens, opaque refresh tokens."""
import base64
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import Settings, get_settings
from app.repositories.models import User


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


# ---------- passwords ----------
def _prehash(password: str) -> bytes:
    # sha256 -> base64 avoids bcrypt's 72-byte truncation / NUL issues
    return base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest())


def hash_password(password: str, rounds: int | None = None) -> str:
    rounds = rounds or get_settings().bcrypt_rounds
    return bcrypt.hashpw(_prehash(password), bcrypt.gensalt(rounds=rounds)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("$2"):
        try:
            return bcrypt.checkpw(_prehash(password), password_hash.encode())
        except ValueError:
            return False
    return password == password_hash


_dummy_hash: str | None = None


def dummy_verify(password: str) -> None:
    """Burn the same CPU as a real check so unknown users aren't distinguishable by timing."""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = hash_password("dummy-password-for-timing")
    verify_password(password, _dummy_hash)


# ---------- access token (JWT) ----------
def create_access_token(user: User, settings: Settings) -> str:
    now = utcnow()
    payload = {
        "sub": user.id,
        "tid": user.institution_id,  # tenant id: the ONLY source of tenant scoping
        "role": user.role,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(seconds=settings.access_token_ttl_seconds),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    if user.student_id:
        payload["sid"] = user.student_id  # students: bound to their own record
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str, settings: Settings) -> dict:
    if settings.jwt_algorithm != "HS256":
        raise jwt.InvalidAlgorithmError("Only HS256 access tokens are allowed.")
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],  # pinned; never trust the token header
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
        leeway=timedelta(seconds=5),
        options={"require": ["exp", "iat", "nbf", "sub", "iss", "aud", "tid", "role"]},
    )


# ---------- refresh token (opaque, stored hashed) ----------
def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)  # 256 bits


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
