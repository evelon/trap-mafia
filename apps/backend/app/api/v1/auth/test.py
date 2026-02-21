from __future__ import annotations

import hashlib
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response

router = APIRouter()


# 예시: refresh 토큰 jti를 DB에 "해시로" 저장한다고 가정
def hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode("utf-8")).hexdigest()


async def store_refresh_jti(user_id: str, jti_hash: str, expires_in: int) -> None:
    # TODO: DB upsert (user_id + jti_hash), expiry 저장
    ...


async def revoke_refresh_jti(user_id: str, jti_hash: str) -> None:
    # TODO: DB에서 해당 refresh 무효화(삭제/revoked 플래그)
    ...


async def is_refresh_jti_valid(user_id: str, jti_hash: str) -> bool:
    # TODO: DB 조회
    return True


JWT_CFG = JwtConfig(
    issuer="trap-mafia",
    audience="trap-mafia",
    access_ttl=timedelta(minutes=15),
    refresh_ttl=timedelta(days=30),
    algorithm="HS256",  # 운영에서는 RS256도 흔함
    secret_or_private_key="CHANGE_ME",
)

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    # minimum + 실무적 기본값
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=int(JWT_CFG.access_ttl.total_seconds()),
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=int(JWT_CFG.refresh_ttl.total_seconds()),
    )


@router.post("/auth/guest-login")
async def guest_login(response: Response):
    # MVP: 게스트를 user_id로 취급 (너 프로젝트 정책에 맞게)
    user_id = "guest:" + "some-generated-id"

    access = create_access_token(JWT_CFG, sub=user_id)
    refresh, jti = create_refresh_token(JWT_CFG, sub=user_id)

    await store_refresh_jti(user_id, hash_jti(jti), int(JWT_CFG.refresh_ttl.total_seconds()))
    set_auth_cookies(response, access, refresh)

    return {"ok": True, "code": "OK", "message": None, "data": None}


@router.post("/auth/refresh")
async def refresh_tokens(response: Response, refresh_token: str = Depends(lambda: "")):
    # 실제로는 Depends로 쿠키에서 refresh_token 읽어오게 만들면 됨
    if not refresh_token:
        raise HTTPException(status_code=401, detail="missing_refresh_token")

    claims = decode_and_verify(JWT_CFG, refresh_token)
    if claims.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="wrong_token_type")

    user_id = claims["sub"]
    jti = claims.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="missing_jti")

    jti_h = hash_jti(jti)
    if not await is_refresh_jti_valid(user_id, jti_h):
        raise HTTPException(status_code=401, detail="revoked_refresh_token")

    # ✅ refresh token rotation: 기존 refresh 폐기 → 새 refresh 발급
    await revoke_refresh_jti(user_id, jti_h)

    new_access = create_access_token(JWT_CFG, sub=user_id)
    new_refresh, new_jti = create_refresh_token(JWT_CFG, sub=user_id)

    await store_refresh_jti(user_id, hash_jti(new_jti), int(JWT_CFG.refresh_ttl.total_seconds()))
    set_auth_cookies(response, new_access, new_refresh)

    return {"ok": True, "code": "OK", "message": None, "data": None}
