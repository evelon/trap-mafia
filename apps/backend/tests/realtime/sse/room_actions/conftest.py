from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import FastAPI

from app.domain.events.case import CaseEventDelta
from app.domain.events.room import RoomEventDelta
from app.infra.pubsub.bus.deps import get_case_event_bus, get_room_event_bus
from app.infra.pubsub.topics import CaseTopic, RoomTopic


@dataclass
class _RoomPublishCall:
    topic: RoomTopic
    event: RoomEventDelta


class FakeRoomEventBus:
    """RoomEventBus 대체용 fake. publish 호출만 기록한다."""

    def __init__(self) -> None:
        self.calls: list[_RoomPublishCall] = []

    async def publish(self, room_topic: RoomTopic, event: RoomEventDelta) -> None:
        self.calls.append(_RoomPublishCall(topic=room_topic, event=event))

    async def subscribe(self, room_topic: RoomTopic):  # pragma: no cover
        raise RuntimeError("subscribe() is not used in these tests")


@dataclass
class _CasePublishCall:
    topic: CaseTopic
    event: CaseEventDelta


class FakeCaseEventBus:
    """RoomEventBus 대체용 fake. publish 호출만 기록한다."""

    def __init__(self) -> None:
        self.calls: list[_CasePublishCall] = []

    async def publish(self, room_topic: CaseTopic, event: CaseEventDelta) -> None:
        self.calls.append(_CasePublishCall(topic=room_topic, event=event))

    async def subscribe(self, room_topic: CaseTopic):  # pragma: no cover
        raise RuntimeError("subscribe() is not used in these tests")


@pytest.fixture
def fake_room_bus(app: FastAPI):
    bus = FakeRoomEventBus()
    app.dependency_overrides[get_room_event_bus] = lambda: bus
    yield bus
    app.dependency_overrides.clear()


@pytest.fixture
def fake_case_bus(app: FastAPI):
    bus = FakeCaseEventBus()
    app.dependency_overrides[get_case_event_bus] = lambda: bus
    yield bus
    app.dependency_overrides.clear()
