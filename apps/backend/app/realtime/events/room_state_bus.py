import json
from typing import Annotated, AsyncIterator

from fastapi import Depends

from app.infra.pubsub.base import PubSub
from app.infra.pubsub.deps import PubSubDep
from app.realtime.topics import RoomTopic
from app.schemas.room.sse_response import RoomStateResponse


class RoomStateBus:
    def __init__(self, pubsub: PubSub):
        self._pubsub = pubsub

    async def publish(self, room_topic: RoomTopic, event: RoomStateResponse) -> None:
        payload = event.model_dump(mode="json")
        await self._pubsub.publish(
            room_topic,
            json.dumps(payload, ensure_ascii=False),
        )

    async def subscribe(self, room_topic: RoomTopic) -> AsyncIterator[RoomStateResponse]:
        async for msg in self._pubsub.subscribe(room_topic):
            data = json.loads(msg)
            yield RoomStateResponse.model_validate(data)


def get_room_state_bus(pubsub: PubSubDep) -> RoomStateBus:
    return RoomStateBus(pubsub)


RoomStateBusDep = Annotated[RoomStateBus, Depends(get_room_state_bus)]
