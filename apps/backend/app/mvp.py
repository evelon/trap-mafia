# app/mvp.py
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import RoomEventType
from app.infra.db.engine import get_sessionmaker
from app.models.room import Room

MVP_ROOM_ID = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")


async def ensure_singleton_room(db: AsyncSession) -> None:
    """
    MVP 단일 방을 DB에 '있으면 그대로, 없으면 생성'한다.
    - DB 제약(예: host_id NOT NULL)이 있으면 여기에서 같이 맞춰야 함.
    """
    room = await db.get(Room, MVP_ROOM_ID)
    if room is None:
        # TODO: Room.host_id가 NOT NULL이면 실제 존재하는 user_id로 채워야 함
        db.add(Room(id=MVP_ROOM_ID, host_id=None, name="test_room_name"))  # 예시: 임시값(권장X)
        await db.commit()


@asynccontextmanager
async def mvp_lifespan(app: FastAPI):
    # startup
    async with get_sessionmaker()() as db:
        await ensure_singleton_room(db)

    yield
    # shutdown: nothing


# NOTE: MVP mock 구현
# - 실제 구현에서는 "현재 유저가 속한 room_id"를 DB/Redis에서 조회합니다.
def mvp_logs_mapper(event_type: RoomEventType) -> list[str]:
    if event_type == RoomEventType.ON_CONNECT:
        return []
    elif event_type == RoomEventType.MEMBER_LEFT:
        return ["사용자가 방을 나갔습니다"]
    elif event_type == RoomEventType.MEMBER_JOINED:
        return ["사용자가 방에 입장했습니다"]
    elif event_type == RoomEventType.MEMBER_KICKED:
        return ["사용자가 방에서 내보내졌습니다"]
    else:
        return []
