import json
from typing import AsyncIterator

from app.domain.events import RoomEventDelta, RoomSnapshotType
from app.infra.pubsub.topics import RoomTopic
from app.infra.pubsub.transport.base import PubSub


class RoomEventBus:
    def __init__(self, pubsub: PubSub):
        self._pubsub = pubsub

    async def publish(self, room_topic: RoomTopic, event: RoomEventDelta) -> None:
        if event.type == RoomSnapshotType.ON_CONNECT:
            raise ValueError("ON_CONNECT must not be published to pubsub")
        payload = event.model_dump(mode="json")
        await self._pubsub.publish(
            room_topic,
            json.dumps(payload, ensure_ascii=False),
        )

    async def subscribe(self, room_topic: RoomTopic) -> AsyncIterator[RoomEventDelta]:
        async for msg in self._pubsub.subscribe(room_topic):
            data = json.loads(msg)
            yield RoomEventDelta.model_validate(data)
