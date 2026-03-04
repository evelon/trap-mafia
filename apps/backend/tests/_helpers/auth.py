from typing import Literal, MutableMapping, TypedDict
from uuid import UUID

from httpx import Response


class _UserInfo(TypedDict):
    id: str
    username: str
    in_case: Literal[False]
    current_case_id: None


class UserAuthEnvelopeDict(TypedDict):
    ok: Literal[True]
    code: Literal["OK"]
    message: None
    data: _UserInfo
    meta: None


class UserAuth(TypedDict):
    id: UUID
    username: Literal["username"]
    envelope: UserAuthEnvelopeDict | dict
    cookies: MutableMapping[str, str]
    access_token: str
    refresh_token: str
    response: Response


login_url = "/api/v1/auth/guest-login"
