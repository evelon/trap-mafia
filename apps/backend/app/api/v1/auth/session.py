from uuid import UUID

from fastapi import APIRouter, Request, Response, status

from app.core.auth import ACCESS_TOKEN, REFRESH_TOKEN, JwtHandlerDep
from app.core.config import JwtConfig
from app.core.exceptions import EnvelopeException
from app.schemas.auth.request import GuestLoginRequest
from app.schemas.auth.response import (
    GuestInfo,
    GuestInfoResponse,
    GuestLogoutResponse,
    LoginCode,
    LogoutCode,
)
from app.schemas.common.envelope import Envelope
from app.schemas.common.error import AuthErrorCode
from app.schemas.common.validation import COMMON_422_RESPONSE
from app.services.auth import AuthServiceDep


def set_auth_cookies(
    response: Response, access_token: str, refresh_token: str, jwt_cfg: JwtConfig
) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN,
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=int(jwt_cfg.access_ttl.total_seconds()),
    )
    response.set_cookie(
        key=REFRESH_TOKEN,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=int(jwt_cfg.refresh_ttl.total_seconds()),
    )


router = APIRouter()


@router.get(
    "/me",
    summary="me",
    response_model=GuestInfoResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "No access token attached in cookie.",
            "model": Envelope[None, AuthErrorCode.AUTH_UNAUTHORIZED],
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "code": AuthErrorCode.AUTH_UNAUTHORIZED,
                        "message": None,
                        "data": None,
                        "meta": None,
                    }
                }
            },
        }
    },
)
async def me(
    request: Request,
    auth_service: AuthServiceDep,
    jwt_handler: JwtHandlerDep,
) -> GuestInfoResponse:
    """Return current guest info from access_token cookie.

    - Reads `access_token` from cookies.
    - Decodes JWT using PyJWT.
    - On missing/invalid/expired token, raises 401.
    """

    access_token = request.cookies.get(ACCESS_TOKEN)
    if not access_token:
        raise EnvelopeException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            response_code=AuthErrorCode.AUTH_TOKEN_NOT_INCLUDED,
        )

    user_id = jwt_handler.extract_user_id_from_token(access_token, ACCESS_TOKEN)

    # DB에서 실제 user 조회
    username = await auth_service.get_username_by_user_id(user_id)

    data = GuestInfo(
        id=UUID(user_id),
        username=username,
        in_case=False,
        current_case_id=None,
    )
    return GuestInfoResponse(ok=True, code=LoginCode.OK, message=None, data=data, meta=None)


@router.post(
    "/guest-login",
    summary="guest_login",
    response_model=GuestInfoResponse,
    status_code=status.HTTP_200_OK,
    responses={
        **COMMON_422_RESPONSE,
        status.HTTP_200_OK: {
            "description": (
                "Temporary API. Creates/returns a guest user session. "
                "Issues access_token/refresh_token cookies via Set-Cookie."
            ),
            "headers": {
                "Set-Cookie": {
                    "description": (
                        "Two Set-Cookie headers are returned: access_token and refresh_token. "
                        "Both are HttpOnly, Secure, SameSite=Lax, Path=/."
                    ),
                    "schema": {"type": "string"},
                    "example": "access_token=<jwt>; HttpOnly; Secure; SameSite=Lax; Path=/",
                },
            },
        },
        status.HTTP_400_BAD_REQUEST: {"description": "TBD: Bad Request"},
    },
)
async def guest_login(
    body: GuestLoginRequest,
    response: Response,
    auth_service: AuthServiceDep,
    jwt_handler: JwtHandlerDep,
):
    """
    POST /api/v1/auth/guest-login

    의미:
    - username만으로 임시(게스트) 로그인 세션을 생성/반환한다.
    - MVP 단계에서는 JWT 쿠키 발급 및 leave_room 부수 효과는 구현하지 않는다(스텁).

    응답:
    - 200: GuestLoginResponse 반환
    - 400: 입력/검증 오류 (TBD)
    """
    # 1. get or create user
    user = await auth_service.get_or_create_guest_user(body.username)

    # 2. issue JWT (MVP: sub=username)
    access = jwt_handler.create_access_token(
        sub=str(user.id),
    )
    refresh, jti = jwt_handler.create_refresh_token(sub=str(user.id))

    set_auth_cookies(response, access, refresh, jwt_handler.cfg)

    data = GuestInfo(
        id=user.id,
        username=user.username,
        in_case=False,
        current_case_id=None,
    )
    return GuestInfoResponse(ok=True, code=LoginCode.OK, message=None, data=data, meta=None)


@router.post(
    "/refresh",
    summary="refresh",
    response_model=GuestInfoResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid / expired / missing refresh token.",
            "model": Envelope[None, AuthErrorCode.AUTH_UNAUTHORIZED],
            "content": {
                "application/json": {
                    "example": {
                        "ok": False,
                        "code": AuthErrorCode.AUTH_UNAUTHORIZED,
                        "message": None,
                        "data": None,
                        "meta": None,
                    }
                }
            },
        }
    },
)
async def refresh(
    request: Request,
    response: Response,
    auth_service: AuthServiceDep,
    jwt_handler: JwtHandlerDep,
) -> GuestInfoResponse:
    """
    Refresh access token using refresh_token cookie.

    - Reads `refresh_token` from cookies.
    - Verifies JWT (iss/aud/exp/iat/sub/typ) via JwtHandler.
    - Issues a new access token and sets it as cookie.
    - Returns current guest info (DB lookup).
    """

    refresh_token = request.cookies.get(REFRESH_TOKEN)
    if not refresh_token:
        raise EnvelopeException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            response_code=AuthErrorCode.AUTH_TOKEN_NOT_INCLUDED,
        )

    # NOTE:
    # - extract_user_id_from_token(token, token_type) 내부에서 typ 검증이 일어나야 함.
    #   (여기서는 token_type=REFRESH_TOKEN을 전달해서 refresh 토큰으로 검증되게 함)
    user_id = jwt_handler.extract_user_id_from_token(refresh_token, REFRESH_TOKEN)

    # access 토큰 재발급 (sub=user_id UUID string)
    access = jwt_handler.create_access_token(sub=user_id)

    # access cookie만 갱신 (refresh rotation은 MVP에선 하지 않음)
    response.set_cookie(
        key=ACCESS_TOKEN,
        value=access,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=int(jwt_handler.cfg.access_ttl.total_seconds()),
    )

    # DB에서 user 조회해서 응답 구성
    username = await auth_service.get_username_by_user_id(user_id)

    data = GuestInfo(
        id=UUID(user_id),
        username=username,
        in_case=False,
        current_case_id=None,
    )
    return GuestInfoResponse(ok=True, code=LoginCode.OK, message=None, data=data, meta=None)


@router.post(
    "/logout",
    summary="logout",
    response_model=GuestLogoutResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "Logs out the current session.\n"
                "- Clears access_token/refresh_token cookies via Set-Cookie (Max-Age=0).\n"
                "- (Future) may trigger leave_room if participating in a case."
            ),
            "headers": {
                "Set-Cookie": {
                    "description": (
                        "Two Set-Cookie headers are returned to clear cookies:\n"
                        "- access_token=; Max-Age=0; Path=/; ...\n"
                        "- refresh_token=; Max-Age=0; Path=/; ...\n"
                    ),
                    "schema": {"type": "string"},
                }
            },
        },
    },
)
async def logout(response: Response) -> GuestLogoutResponse:
    """
    POST /api/v1/auth/logout

    의미:
    - 현재 세션의 access/refresh JWT 쿠키를 제거한다.
    - MVP: 토큰 블랙리스트/회전/서버측 세션 무효화는 하지 않는다.
    - MVP: case 참가 중이면 leave_room 등의 부수효과는 아직 구현하지 않는다.

    Side effect:
    - Set-Cookie로 access_token/refresh_token을 Max-Age=0으로 만료시킨다.
    """
    # 쿠키 삭제 지시 (브라우저/클라이언트가 저장된 쿠키를 제거하도록)
    response.delete_cookie(key=ACCESS_TOKEN, path="/")
    response.delete_cookie(key=REFRESH_TOKEN, path="/")

    return GuestLogoutResponse(ok=True, code=LogoutCode.OK, message=None, data=None, meta=None)
