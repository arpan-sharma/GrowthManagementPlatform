from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import institutions_router
from app.core.config import assert_safe_for_production, get_settings
from app.core.database import check_connection, database_status, validate_schema
from app.core.errors import AppError


def create_app() -> FastAPI:
    settings = get_settings()
    assert_safe_for_production(settings)

    app = FastAPI(
        title=settings.app_name,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # explicit origins only (required with credentials)
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, e: AppError):
        return JSONResponse(status_code=e.status, content=e.body(), headers=e.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, e: RequestValidationError):
        details = [
            {"field": ".".join(str(x) for x in err["loc"][1:]), "message": err["msg"]}
            for err in e.errors()
        ]
        err = AppError(422, "validation_error", "Invalid request.", details)
        return JSONResponse(status_code=422, content=err.body())

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        resp = await call_next(request)
        resp.headers["Cache-Control"] = "no-store" if "/auth" in request.url.path else resp.headers.get("Cache-Control", "no-cache")
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        return resp

    @app.on_event("startup")
    def verify_database() -> None:
        if not settings.database_url:
            return
        check_connection(settings.database_url)
        validate_schema(settings.database_url)

    @app.get("/health", include_in_schema=False)
    def health():
        payload = {"status": "ok", "storage": "postgresql" if settings.database_url else "memory"}
        if settings.database_url:
            payload["database"] = database_status(settings.database_url)
            if payload["database"]["status"] != "ok":
                payload["status"] = "degraded"
        return payload

    app.include_router(institutions_router, prefix=settings.api_prefix)
    return app


app = create_app()
