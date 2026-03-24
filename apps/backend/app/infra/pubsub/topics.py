from __future__ import annotations

from dataclasses import dataclass

from app.schemas.common.ids import CaseId, ConnId, RoomId, UserId


class Topic:
    """
    Transport-independent pub/sub topic marker.
    Redis에 대해 독립적인 StateBus를 구현하기 위함.
    """

    pass


@dataclass(frozen=True)
class RoomTopic(Topic):
    room_id: RoomId


@dataclass(frozen=True)
class UserTopic(Topic):
    user_id: UserId


@dataclass(frozen=True)
class CaseTopic(Topic):
    case_id: CaseId


# 확장 대비 (특정 연결)
@dataclass(frozen=True)
class ConnTopic(Topic):
    conn_id: ConnId
