from dataclasses import dataclass
from typing import Generator, Optional

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.database import get_session_factory
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.repositories.base import AuthRepository
from app.repositories.memory import InMemoryAuthRepository, seed_dev_data
from app.repositories.seed_sql import seed_sql_data
from app.repositories.sql import SqlAuthRepository
from app.services.auth_service import AuthService
from app.services.platform_service import PlatformService

bearer = HTTPBearer(auto_error=False)

_memory_repo: InMemoryAuthRepository | None = None


def reset_repositories() -> None:
    global _memory_repo
    _memory_repo = None
    get_settings.cache_clear()
    from app.core.database import get_engine, get_session_factory

    get_engine.cache_clear()
    get_session_factory.cache_clear()


def _memory_repository(settings: Settings) -> InMemoryAuthRepository:
    global _memory_repo
    if _memory_repo is None:
        _memory_repo = InMemoryAuthRepository()
        if not settings.is_production:
            seed_dev_data(_memory_repo, settings)
    return _memory_repo


def get_db_session() -> Generator:
    settings = get_settings()
    if not settings.database_url:
        yield None
        return
    session = get_session_factory(settings.database_url)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_repo(session=Depends(get_db_session)) -> AuthRepository:
    settings = get_settings()
    if settings.database_url:
        if session is None:
            raise RuntimeError("Database session missing while DATABASE_URL is set.")
        repo = SqlAuthRepository(session)
        if not settings.is_production and repo.get_user_by_email("admin@gmail.com") is None:
            seed_sql_data(repo, settings)
        return repo
    return _memory_repository(settings)


def get_auth_service(
    repo: AuthRepository = Depends(get_repo), settings: Settings = Depends(get_settings)
) -> AuthService:
    return AuthService(repo, settings)


def get_platform_service(repo: AuthRepository = Depends(get_repo)) -> PlatformService:
    academic = getattr(repo, "academic", None)
    if academic is None:
        raise RuntimeError("Auth repository has no academic store.")
    return PlatformService(repo, academic)


@dataclass(frozen=True)
class Principal:
    user_id: str
    institution_id: str  # tenant: always taken from the token
    role: str
    student_id: Optional[str] = None


def get_principal(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    settings: Settings = Depends(get_settings),
) -> Principal:
    unauth = AppError(401, "invalid_token", "Invalid or expired token.", headers={"WWW-Authenticate": "Bearer"})
    if creds is None or creds.scheme.lower() != "bearer":
        raise unauth
    try:
        claims = decode_access_token(creds.credentials, settings)
    except jwt.PyJWTError:
        raise unauth
    return Principal(
        user_id=claims["sub"],
        institution_id=claims["tid"],
        role=claims["role"],
        student_id=claims.get("sid"),
    )


def require_role(*roles: str):
    def checker(p: Principal = Depends(get_principal)) -> Principal:
        if p.role not in roles:
            raise AppError(403, "forbidden", "You do not have access to this resource.")
        return p

    return checker


require_head_teacher = require_role("head_teacher")
require_student = require_role("student")
