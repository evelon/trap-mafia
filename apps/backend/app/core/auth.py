from __future__ import annotations

import time
import uuid
from typing import Annotated, Any, Literal

import jwt  # PyJWT
from fastapi import Depends, status

from app.core.config import JwtConfig, get_jwt_config
from app.core.exceptions import EnvelopeException
from app.schemas.common.error import AuthErrorCode

ACCESS_TOKEN = "access_token"
REFRESH_TOKEN = "refresh_token"

_token_type_mapping = {"access_token": "access", "refresh_token": "refresh"}


class JwtHandler:
    def __init__(self, cfg: JwtConfig):
        self.cfg = cfg

    @staticmethod
    def _now() -> int:
        return int(time.time())

    def _encode(self, claims: dict[str, Any]) -> str:
        return jwt.encode(claims, self.cfg.secret_key, algorithm=self.cfg.algorithm)

    def create_access_token(self, *, sub: str, extra: dict[str, Any] | None = None) -> str:
        if extra is not None and set(extra) & {"iss", "aud", "sub", "iat", "exp", "typ"}:
            raise KeyError("parameter `extra` has non-extra fields")

        now = self._now()
        payload: dict[str, Any] = {
            "iss": self.cfg.issuer,
            "aud": self.cfg.audience,
            "sub": sub,
            "iat": now,
            "exp": now + int(self.cfg.access_ttl.total_seconds()),
            "typ": "access",
        }
        if extra:
            payload.update(extra)
        return self._encode(payload)

    def create_refresh_token(self, *, sub: str, jti: str | None = None) -> tuple[str, str]:
        now = self._now()
        refresh_jti = jti or uuid.uuid4().hex
        payload: dict[str, Any] = {
            "iss": self.cfg.issuer,
            "aud": self.cfg.audience,
            "sub": sub,
            "iat": now,
            "exp": now + int(self.cfg.refresh_ttl.total_seconds()),
            "typ": "refresh",
            "jti": refresh_jti,  # refresh 식별자(로테이션/회수에 사용)
        }
        return self._encode(payload), refresh_jti

    def decode_and_verify(self, token: str) -> dict[str, Any]:
        key = (
            self.cfg.public_key
            if (self.cfg.algorithm.startswith("RS") and self.cfg.public_key)
            else self.cfg.secret_key
        )
        try:
            return jwt.decode(
                token,
                key,
                algorithms=[self.cfg.algorithm],
                audience=self.cfg.audience,
                issuer=self.cfg.issuer,
                options={"require": ["exp", "iat", "sub", "typ"]},
            )
        except jwt.ExpiredSignatureError as e:
            raise EnvelopeException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                response_code=AuthErrorCode.AUTH_TOKEN_EXPIRED,
            ) from e
        except jwt.InvalidTokenError as e:
            raise EnvelopeException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                response_code=AuthErrorCode.AUTH_TOKEN_INVALID,
            ) from e

    def extract_user_id_from_token(
        self, token: str, token_type: Literal["access_token", "refresh_token"]
    ) -> str:
        if not token:
            raise EnvelopeException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                response_code=AuthErrorCode.AUTH_TOKEN_NOT_INCLUDED,
            )
        token_typ = _token_type_mapping[token_type]

        claims = self.decode_and_verify(token)

        if claims["typ"] != token_typ:
            raise EnvelopeException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                response_code=AuthErrorCode.AUTH_TOKEN_INVALID,
            )
        sub = claims.get("sub")
        if not isinstance(sub, str) or not sub:
            raise EnvelopeException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                response_code=AuthErrorCode.AUTH_TOKEN_PAYLOAD_INVALID,
            )
        return sub


JwtConfigDep = Annotated[JwtConfig, Depends(get_jwt_config)]


def get_jwt_handler(cfg: JwtConfigDep) -> JwtHandler:
    return JwtHandler(cfg)


JwtHandlerDep = Annotated[JwtHandler, Depends(get_jwt_handler)]
