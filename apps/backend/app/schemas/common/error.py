from enum import Enum


class AuthErrorCode(str, Enum):
    AUTH_USER_NOT_FOUND = "AUTH_USER_NOT_FOUND"  # 토큰에 있는 user를 찾을 수 없음.
    AUTH_USERNAME_NOT_FOUND = (
        "AUTH_USERNAME_NOT_FOUND"  # 해당 username 없음 (보안상 `AUTH_UNAUTHORIZED`로 치환 가능)
    )
    AUTH_WRONG_PW = (
        "AUTH_WRONG_PW"  # username 있으나 비밀번호 틀림 (보안상 `AUTH_UNAUTHORIZED`로 치환 가능)
    )
    AUTH_TOKEN_NOT_INCLUDED = "AUTH_TOKEN_NOT_INCLUDED"  # 토큰이 없음
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"  # 토큰값이 유효하지 않음
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"  # 토큰이 만료됨
    AUTH_TOKEN_PAYLOAD_INVALID = "AUTH_TOKEN_PAYLOAD_INVALID"  # 토큰 payload가 유효하지 않음
    AUTH_UNAUTHORIZED = (
        "AUTH_UNAUTHORIZED"  # 401 unauthorized의 일반적인 code. 보안상 이유를 노출하지 않을 경우
    )


class CommonErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
