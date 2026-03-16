from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import FastAPI

from app.domain.events import RoomEventDelta
from app.infra.pubsub.bus.deps import get_room_event_bus
from app.infra.pubsub.topics import RoomTopic


@dataclass
class _PublishCall:
    topic: RoomTopic
    event: RoomEventDelta


class FakeRoomEventBus:
    """RoomEventBus 대체용 fake. publish 호출만 기록한다."""

    def __init__(self) -> None:
        self.calls: list[_PublishCall] = []

    async def publish(self, room_topic: RoomTopic, event: RoomEventDelta) -> None:
        self.calls.append(_PublishCall(topic=room_topic, event=event))

    async def subscribe(self, room_topic: RoomTopic):  # pragma: no cover
        raise RuntimeError("subscribe() is not used in these tests")


@pytest.fixture
def fake_bus(app: FastAPI):
    bus = FakeRoomEventBus()
    app.dependency_overrides[get_room_event_bus] = lambda: bus
    yield bus
    app.dependency_overrides.clear()
