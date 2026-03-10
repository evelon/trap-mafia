import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.domain.events.room_event import RoomEventMessage, RoomEventType
from app.infra.pubsub.bus.room_event_bus import RoomEventBus
from app.mvp import MVP_ROOM_ID
from app.realtime.topics import RoomTopic
from tests.conftest import FakePubSub


async def test_publish_serializes_and_calls_pubsub(fake_pubsub: FakePubSub) -> None:
    pubsub = fake_pubsub
    bus = RoomEventBus(pubsub)  # type: ignore[arg-type]

    room_id = MVP_ROOM_ID
    topic = RoomTopic(room_id)

    ts = datetime(2026, 3, 5, 0, 0, 0, tzinfo=timezone.utc)
    ev = RoomEventMessage(
        type=RoomEventType.MEMBER_JOINED,
        user_id=uuid4(),
        ts=ts,
        version=7,
    )

    await bus.publish(topic, ev)

    assert len(pubsub.published) == 1
    assert pubsub.published[0].topic == topic

    payload = json.loads(pubsub.published[0].message)
    roundtrip = RoomEventMessage.model_validate(payload)
    assert roundtrip == ev


async def test_publish_on_connect_is_rejected(fake_pubsub: FakePubSub) -> None:
    pubsub = fake_pubsub
    bus = RoomEventBus(pubsub)  # type: ignore[arg-type]

    room_id = MVP_ROOM_ID
    topic = RoomTopic(room_id)

    ev = RoomEventMessage(type=RoomEventType.ON_CONNECT, ts=datetime.now())  # pyright: ignore[reportCallIssue]

    with pytest.raises(ValueError, match="ON_CONNECT"):
        await bus.publish(topic, ev)

    assert pubsub.published == []


async def test_subscribe_parses_json_to_room_event_message(fake_pubsub: FakePubSub) -> None:
    pubsub = fake_pubsub
    bus = RoomEventBus(pubsub)  # type: ignore[arg-type]

    room_id = MVP_ROOM_ID
    topic = RoomTopic(room_id)

    ts = datetime(2026, 3, 5, 0, 0, 0, tzinfo=timezone.utc)
    ev1 = RoomEventMessage(type=RoomEventType.MEMBER_JOINED, user_id=None, ts=ts)
    ev2 = RoomEventMessage(
        type=RoomEventType.MEMBER_LEFT,
        user_id=uuid4(),
        ts=ts,
        version=None,
    )

    # Enqueue messages as if they came from Redis.
    await pubsub.publish(topic, json.dumps(ev1.model_dump(mode="json"), ensure_ascii=False))
    await pubsub.publish(topic, json.dumps(ev2.model_dump(mode="json"), ensure_ascii=False))

    received: list[RoomEventMessage] = []
    async for ev in bus.subscribe(topic):
        received.append(ev)

    assert received == [ev1, ev2]
