from __future__ import annotations

from typing import Any

from app.schemas.common.envelope import Envelope
from app.schemas.room.sse_response import RoomStateEnvelope


class RespValidator[EnvelopeType: Envelope[Any, Any]]:
    _resp_type: type[EnvelopeType]

    def __init__(self, resp_type: type[EnvelopeType]):
        # resp_type is a concrete Envelope subclass, e.g. RoomEnvelope
        self._resp_type = resp_type

    def assert_envelope(
        self,
        body: Any,
        *,
        ok: bool | None = None,
        meta_is_null: bool = True,
    ) -> EnvelopeType:
        envelope = self._resp_type.model_validate(body)
        assert isinstance(envelope.ok, bool), f"ok는 bool이어야 함. got={type(envelope.ok)}"
        if ok is not None:
            assert envelope.ok is ok, f"ok 값 불일치. expected={ok}, got={envelope.ok}"

        msg = envelope.message
        assert msg is None or isinstance(msg, str), f"message는 str|null이어야 함. got={type(msg)}"

        if meta_is_null:
            assert envelope.meta is None, (
                f"현 단계 정책상 meta는 항상 null이어야 함. got={envelope.meta!r}"
            )

        return envelope


general_failure_validator = RespValidator(Envelope[Any, Any])


def assert_set_cookie_has_tokens(set_cookie_header: str) -> None:
    """
    guest-login 응답에서 access/refresh 쿠키가 세팅되는지(최소) 확인.

    주의:
    - Set-Cookie는 여러 개면 콤마/개행으로 합쳐질 수 있어 단순 포함 검사로 최소 보장만 한다.
    - 속성(HttpOnly/Secure/SameSite/Path)은 운영 환경/테스트 환경 차이로 깨질 수 있어
      지금은 "핵심 존재"만 강제하고, 속성은 별도 테스트로 분리하는 걸 권장.
    """
    assert isinstance(set_cookie_header, str)
    assert "access_token=" in set_cookie_header, f"access_token 쿠키 누락: {set_cookie_header}"
    assert "refresh_token=" in set_cookie_header, f"refresh_token 쿠키 누락: {set_cookie_header}"


room_sse_validator = RespValidator(RoomStateEnvelope)
