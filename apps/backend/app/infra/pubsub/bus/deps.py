from typing import Annotated

from fastapi import Depends

from app.infra.pubsub.bus.room_event_bus import RoomEventBus
from app.infra.pubsub.transport.deps import PubSubDep


def get_room_event_bus(pubsub: PubSubDep) -> RoomEventBus:
    return RoomEventBus(pubsub)


RoomEventBusDep = Annotated[RoomEventBus, Depends(get_room_event_bus)]
