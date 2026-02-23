from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings


def _parse_csv(value: str) -> list[str]:
    """쉼표로 구분된 문자열을 list[str]로 변환합니다."""
    items = [v.strip() for v in value.split(",")]
    return [v for v in items if v]


def register_middlewares(app: FastAPI) -> None:
    s = get_settings()

    # Origins
    allow_origins = (
        ["*"] if s.cors_allow_origins.strip() == "*" else _parse_csv(s.cors_allow_origins)
    )

    # Methods
    allow_methods = (
        ["*"] if s.cors_allow_methods.strip() == "*" else _parse_csv(s.cors_allow_methods)
    )

    # Headers
    is_prod = s.app_env.lower() in ("staging", "prod")
    headers_value = s.cors_allow_headers_prod if is_prod else s.cors_allow_headers
    allow_headers = ["*"] if headers_value.strip() == "*" else _parse_csv(headers_value)

    # Guard rails: credentials + wildcard origins is not compatible in browsers/spec.
    if s.cors_allow_credentials and allow_origins == ["*"]:
        raise ValueError(
            "Invalid CORS config: "
            "cors_allow_credentials=True cannot be used with cors_allow_origins='*'. "
            "Set cors_allow_origins to an explicit allow-list (or use cors_allow_origin_regex)."
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=s.cors_allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )
