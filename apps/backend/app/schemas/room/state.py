"""room/state.py

Purpose
- room_snapshot(방 상태 스냅샷) 스키마를 정의합니다.
- REST/SSE 등 어떤 전송 방식에서도 동일한 "방 상태"를 표현하기 위한 SSOT입니다.

Meaning
- RoomSnapshot: 방/설정/현재 케이스/멤버 목록을 한 번에 전달하는 최상위 스냅샷입니다.

Field interpretation
- 본 파일은 Notion의 "room_snapshot" 문서 중 MVP(Simplified) 버전을 기준으로 합니다.
- created_at/joined_at 등 시간 필드는 MVP에서 고정값을 사용할 수 있으나,
  스키마는 일반 ISO-8601 UTC 문자열을 허용합니다.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

# MVP에서 문서 예시로 사용한 고정값(테스트/목업 편의)
MVP_FIXED_UTC_ISO = "1970-01-01T00:00:00.000Z"


class RoomInfo(BaseModel):
    """Purpose
    - 방 자체 메타 정보를 담습니다.

    Meaning
    - room_snapshot.room 블록에 해당합니다.

    Field interpretation
    - id: MVP에서는 1로 고정해서 사용할 수 있습니다.
    - room_name: MVP에서는 "test_room"처럼 고정 문자열을 사용할 수 있습니다.
    - host_user_id: 방장 유저의 UUID입니다.
    - created_at: ISO-8601 UTC 문자열(예: 2026-01-31T09:12:34.567Z)입니다.
    """

    id: Annotated[int, Field(ge=1, description="Room id (MVP: 1 fixed)")] = 1
    room_name: Annotated[
        str,
        Field(min_length=4, max_length=12, description="Room name (MVP:fixed)"),
    ] = "test_room"
    host_user_id: UUID = UUID("00000000-0000-0000-0000-000000000000")
    created_at: Annotated[str, Field(description="ISO-8601 UTC string")] = MVP_FIXED_UTC_ISO


class RoomSettings(BaseModel):
    """Purpose
    - 방 설정(플레이 규칙/제한)을 담습니다.

    Meaning
    - room_snapshot.settings 블록에 해당합니다.

    Field interpretation
    - discuss_duration_sec이 0이면 시간 제한이 없음을 뜻합니다.
    - MVP에서는 아래 기본값을 고정해서 사용할 수 있습니다.
    """

    max_players: Annotated[int, Field(ge=4, le=8)] = 8
    team_policy: Literal["RANDOM", "FIXED"] = "RANDOM"
    full_life: Annotated[int, Field(ge=1, le=4)] = 2
    max_vote_phases_per_round: Annotated[int, Field(ge=1)] = 2

    night_duration_sec: Annotated[int, Field(ge=1)] = 30
    vote_duration_sec: Annotated[int, Field(ge=1)] = 30
    discuss_duration_sec: Annotated[int, Field(ge=0)] = 120


class RoomCurrentCase(BaseModel):
    """Purpose
    - 현재 방에서 진행 중인 케이스(게임 한 판)의 최소 상태를 담습니다.

    Meaning
    - room_snapshot.current_case 블록에 해당합니다.

    Field interpretation
    - case_id가 null이면 아직 케이스가 없으며 status도 null이어야 합니다.
    - case_id가 존재하면 status는 RUNNING 또는 ENDED가 될 수 있습니다.
    - MVP 단순화: status는 RUNNING 또는 null로만 사용해도 됩니다.
    """

    case_id: UUID | None = None
    status: Literal["RUNNING"] | None = None


class RoomMember(BaseModel):
    """Purpose
    - 방에 active한(퇴장하지 않은) 멤버의 최소 정보를 담습니다.

    Meaning
    - room_snapshot.members[] 항목입니다.

    Field interpretation
    - members에는 left_at이 null인 active 멤버만 포함합니다(실제 구현 규칙).
    - members의 정렬은 joined_at ASC(입장 순)입니다(실제 구현 규칙).
    """

    user_id: UUID
    username: Annotated[str, Field(min_length=4, max_length=255)]
    joined_at: Annotated[str, Field(default=MVP_FIXED_UTC_ISO, description="ISO-8601 UTC string")]


class RoomSnapshot(BaseModel):
    """Purpose
    - 방 상태를 SSE/REST에서 한 번에 전달하기 위한 스냅샷입니다.

    Meaning
    - Notion의 room_snapshot 전체 구조에 해당합니다.

    Field interpretation
    - room/settings/current_case/members를 포함합니다.
    - MVP 목업에서는 기본값들을 그대로 사용해도 스냅샷을 만들 수 있습니다.
    """

    room: RoomInfo
    settings: RoomSettings = Field(default_factory=RoomSettings)
    current_case: RoomCurrentCase = Field(default_factory=RoomCurrentCase)
    members: list[RoomMember] = Field(default_factory=list)


def now_utc_iso() -> str:
    """Purpose
    - 테스트/목업에서 현재 시각을 ISO-8601 UTC 문자열로 생성합니다.

    Meaning
    - MVP에서는 고정값을 써도 되지만, 실제 구현에선 현재 시각이 필요할 수 있습니다.

    Field interpretation
    - 반환 형식은 `YYYY-MM-DDTHH:MM:SS.mmmZ`에 가깝게 만듭니다.
    """

    now = datetime.now(timezone.utc)
    # 밀리초 단위로 정규화
    now = now.replace(microsecond=(now.microsecond // 1000) * 1000)
    # ISO-8601 + Z 형태로 변환
    return now.isoformat(timespec="milliseconds").replace("+00:00", "Z")
