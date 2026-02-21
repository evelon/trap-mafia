from dataclasses import dataclass
from datetime import timedelta
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    database_url: str
    redis_url: str

    # JWT
    # - access/refresh 분리
    # - 운영에서는 RS256(+private/public key)도 고려 가능하지만, MVP는 HS256로 시작해도 충분
    jwt_issuer: str = "trap-mafia"
    jwt_audience: str = "trap-mafia"

    jwt_algorithm: str = "HS256"  # "HS256" | "RS256"
    jwt_secret: str  # HS256 secret or RS256 private key (PEM)
    jwt_public_key: str | None = None  # RS256 verify key (PEM). HS256에서는 None

    jwt_access_expires_minutes: int = 15
    jwt_refresh_expires_days: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]


@dataclass(frozen=True)
class JwtConfig:
    issuer: str
    audience: str
    access_ttl: timedelta
    refresh_ttl: timedelta
    algorithm: str  # "HS256" or "RS256"
    secret_key: str
    public_key: str | None = None  # RS256 검증용(선택)


@lru_cache
def get_jwt_config() -> JwtConfig:
    """Settings로부터 JwtConfig를 조합해 반환합니다."""
    s = get_settings()
    return JwtConfig(
        issuer=s.jwt_issuer,
        audience=s.jwt_audience,
        access_ttl=timedelta(minutes=s.jwt_access_expires_minutes),
        refresh_ttl=timedelta(days=s.jwt_refresh_expires_days),
        algorithm=s.jwt_algorithm,
        secret_key=s.jwt_secret,
        public_key=s.jwt_public_key,
    )
