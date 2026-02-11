from uuid import UUID

from fastapi import APIRouter, Response, status

from app.schemas.auth.request import GuestLoginRequest
from app.schemas.auth.response import (
    GuestLoginData,
    GuestLoginResponse,
    GuestLogoutResponse,
    LoginCode,
    LogoutCode,
)

router = APIRouter()


@router.post(
    "/guest",
    summary="guest_login",
    response_model=GuestLoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "Temporary API. Creates/returns a guest user session. "
                "(MVP stub: no JWT cookies are issued yet, "
                "and no leave_room side-effect is triggered.)"
            ),
            "headers": {
                "Set-Cookie": {
                    "description": (
                        "TBD: access_token/refresh_token cookies will be "
                        "issued in a future implementation."
                    ),
                    "schema": {"type": "string"},
                },
            },
        },
        status.HTTP_400_BAD_REQUEST: {"description": "TBD: Bad Request"},
    },
)
def guest_login(body: GuestLoginRequest, response: Response):
    """
    POST /api/auth/session/guest

    의미:
    - username만으로 임시(게스트) 로그인 세션을 생성/반환한다.
    - MVP 단계에서는 JWT 쿠키 발급 및 leave_room 부수 효과는 구현하지 않는다(스텁).

    응답:
    - 200: GuestLoginResponse 반환
    - 400: 입력/검증 오류 (TBD)
    """

    data = GuestLoginData(
        id=UUID("00000000-0000-0000-0000-000000000000"),  # 예시
        username=body.username,
        in_case=False,
        current_case_id=None,
    )
    return GuestLoginResponse(ok=True, code=LoginCode.OK, message=None, data=data, meta=None)


@router.post(
    "/logout",
    summary="logout",
    response_model=GuestLogoutResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "Temporary API. Logs out the current session. "
                "(MVP stub: does not clear cookies yet, "
                "and no leave_room side-effect is triggered.)"
            ),
            "headers": {
                "Set-Cookie": {
                    "description": (
                        "TBD: access_token/refresh_token cookies will be cleared (Max-Age=0) "
                        "in a future implementation."
                    ),
                    "schema": {"type": "string"},
                }
            },
        },
        status.HTTP_400_BAD_REQUEST: {"description": "TBD: Bad Request"},
    },
)
def logout(response: Response):
    """
    POST /api/auth/session/logout

    의미:
    - 현재 세션 로그아웃을 수행한다.
    - MVP 단계에서는 쿠키 삭제 및 leave_room 부수 효과는 구현하지 않는다(스텁).

    응답:
    - 200: GuestLogoutResponse 반환
    - 400: 요청/검증 오류 (TBD)
    """
    # response.delete_cookie("access_token")
    # response.delete_cookie("refresh_token")
    # TODO: leave_room()

    return GuestLogoutResponse(ok=True, code=LogoutCode.OK, message=None, data=None, meta=None)
