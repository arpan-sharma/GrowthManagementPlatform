from typing import Optional

from fastapi import APIRouter, Cookie, Depends, Header, Request, Response
from fastapi.responses import JSONResponse

from app.api.deps import Principal, get_auth_service, get_principal
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    MeResponse,
    SignupRequest,
    SignupResponse,
    StudentLoginRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE = "refresh_token"


def _meta(request: Request):
    return (request.client.host if request.client else None), request.headers.get("user-agent")


def _set_refresh_cookie(resp: Response, raw: str, ttl: int, s: Settings) -> None:
    resp.set_cookie(
        COOKIE, raw, max_age=ttl, httponly=True, secure=s.cookie_secure,
        samesite="strict", path=f"{s.api_prefix}/auth",
    )


def _clear_refresh_cookie(resp: Response, s: Settings) -> None:
    resp.delete_cookie(COOKIE, path=f"{s.api_prefix}/auth")


@router.post("/signup", response_model=SignupResponse, status_code=201)
def signup(body: SignupRequest, request: Request, svc: AuthService = Depends(get_auth_service)):
    ip, _ = _meta(request)
    return svc.signup(body, ip)


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest, request: Request, response: Response,
    svc: AuthService = Depends(get_auth_service), s: Settings = Depends(get_settings),
):
    ip, ua = _meta(request)
    token_body, raw, ttl = svc.login_head_teacher(body, ip, ua)
    _set_refresh_cookie(response, raw, ttl, s)
    return token_body


@router.post("/student/login", response_model=TokenResponse)
def student_login(
    body: StudentLoginRequest, request: Request, response: Response,
    svc: AuthService = Depends(get_auth_service), s: Settings = Depends(get_settings),
):
    ip, ua = _meta(request)
    token_body, raw, ttl = svc.login_student(body, ip, ua)
    _set_refresh_cookie(response, raw, ttl, s)
    return token_body


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request, response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    x_requested_with: Optional[str] = Header(default=None),
    svc: AuthService = Depends(get_auth_service), s: Settings = Depends(get_settings),
):
    # CSRF defence in depth (cookie is also SameSite=Strict): a cross-site form can't set this header
    if not x_requested_with:
        raise AppError(403, "csrf_failed", "Missing X-Requested-With header.")
    ip, ua = _meta(request)
    try:
        token_body, raw, ttl = svc.refresh(refresh_token, ip, ua)
    except AppError as e:
        err = JSONResponse(status_code=e.status, content=e.body(), headers=e.headers)
        _clear_refresh_cookie(err, s)
        return err
    _set_refresh_cookie(response, raw, ttl, s)
    return token_body


@router.post("/logout", status_code=204)
def logout(
    request: Request, response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    p: Principal = Depends(get_principal),
    svc: AuthService = Depends(get_auth_service), s: Settings = Depends(get_settings),
):
    ip, _ = _meta(request)
    svc.logout(p.user_id, refresh_token, ip)
    _clear_refresh_cookie(response, s)
    response.status_code = 204
    return response


@router.post("/logout-all", status_code=204)
def logout_all(
    request: Request, response: Response,
    p: Principal = Depends(get_principal),
    svc: AuthService = Depends(get_auth_service), s: Settings = Depends(get_settings),
):
    ip, _ = _meta(request)
    svc.logout_all(p.user_id, ip)
    _clear_refresh_cookie(response, s)
    response.status_code = 204
    return response


@router.get("/me", response_model=MeResponse)
def me(p: Principal = Depends(get_principal), svc: AuthService = Depends(get_auth_service)):
    user, inst = svc.me(p.user_id)
    parts = user.full_name.strip().split(None, 1)
    return MeResponse(
        id=user.id,
        first_name=parts[0],
        last_name=parts[1] if len(parts) > 1 else "",
        role=user.role,
        institution_id=inst.id,
        email=user.email,
        contact_number=user.phone or "",
        must_change_password=user.must_change_password,
        institution_name=inst.name,
        institution_code=inst.code,
    )


@router.post("/change-password", status_code=204)
def change_password(
    body: ChangePasswordRequest, request: Request, response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    p: Principal = Depends(get_principal), svc: AuthService = Depends(get_auth_service),
):
    ip, _ = _meta(request)
    svc.change_password(p.user_id, body, refresh_token, ip)
    response.status_code = 204
    return response
