"""Runtime settings. Production refuses insecure JWT or cookie defaults."""
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "dev-insecure-jwt-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ClassLedger API"
    environment: str = "development"
    api_prefix: str = "/api/v1/institutions"

    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "classledger"
    jwt_audience: str = "classledger-api"
    access_token_ttl_seconds: int = 900
    refresh_ttl_head_teacher_seconds: int = 60 * 60 * 24 * 14
    refresh_ttl_student_seconds: int = 60 * 60 * 24 * 7

    bcrypt_rounds: int = 12
    cookie_secure: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    max_failed_attempts: int = 5
    lockout_seconds: int = 900

    database_url: str | None = None

    @field_validator("jwt_algorithm")
    @classmethod
    def pin_algorithm(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError("Only HS256 access tokens are allowed.")
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


def assert_safe_for_production(settings: Settings) -> None:
    if settings.jwt_algorithm != "HS256":
        raise RuntimeError("Refusing to start: JWT_ALGORITHM must be HS256.")
    if not settings.is_production:
        return
    secret = settings.jwt_secret
    if secret == DEFAULT_JWT_SECRET or len(secret) < 32:
        raise RuntimeError("Refusing to start: set a strong JWT_SECRET in production.")
    if not settings.cookie_secure:
        raise RuntimeError("Refusing to start: COOKIE_SECURE must be true in production.")
    if not settings.database_url:
        raise RuntimeError("Refusing to start: DATABASE_URL is required in production.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
