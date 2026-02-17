from __future__ import annotations

from typing import Any

ENVELOPE_KEYS = {"ok", "code", "message", "data", "meta"}


def assert_is_envelope(
    body: Any,
    *,
    ok: bool | None = None,
    meta_is_null: bool = True,
    allow_extra_keys: bool = False,
) -> dict[str, Any]:
    """
    Envelope 형태를 강제하는 공용 assert.

    SSOT:
    - top-level 키는 ok/code/message/data/meta
    - code는 Enum이지만 응답에서는 문자열로 내려온다
    - 현 단계에서는 meta는 항상 null(None)이다

    Args:
        body: resp.json() 결과
        ok: 지정하면 body["ok"]가 이 값과 정확히 같아야 한다.
        meta_is_null: True면 body["meta"]는 반드시 None이어야 한다.
        allow_extra_keys: False면 top-level 키가 정확히 5개여야 한다.
                         True면 최소한 ENVELOPE_KEYS는 포함되어야 한다.

    Returns:
        body를 dict로 캐스팅해서 반환 (테스트에서 계속 사용하기 편하게)
    """
    assert isinstance(body, dict), f"Envelope는 dict여야 함. got={type(body)} body={body}"

    keys = set(body.keys())
    if allow_extra_keys:
        missing = ENVELOPE_KEYS - keys
        assert not missing, f"Envelope 필수 키 누락: {missing}. got keys={keys}"
    else:
        assert keys == ENVELOPE_KEYS, (
            f"Envelope top-level 키 불일치. expected={ENVELOPE_KEYS}, got={keys}"
        )

    # ok
    assert isinstance(body["ok"], bool), f"ok는 bool이어야 함. got={type(body['ok'])}"
    if ok is not None:
        assert body["ok"] is ok, f"ok 값 불일치. expected={ok}, got={body['ok']}"

    # code (Enum -> str 직렬화)
    assert isinstance(body["code"], str), f"code는 str이어야 함. got={type(body['code'])}"
    assert body["code"], "code는 빈 문자열이면 안 됨"

    # message
    msg = body["message"]
    assert (msg is None) or isinstance(msg, str), f"message는 str|null이어야 함. got={type(msg)}"

    # data / meta
    # data는 타입이 endpoint마다 다르므로 여기서는 None 여부만 허용
    # (구체 data shape 검증은 각 endpoint 테스트에서 한다)
    if meta_is_null:
        assert body["meta"] is None, (
            f"현 단계 정책상 meta는 항상 null이어야 함. got={body['meta']!r}"
        )

    return body


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
