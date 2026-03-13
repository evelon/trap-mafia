from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.infra.pubsub.bus.deps import RoomEventBusDep
from app.queries.deps import RoomSnapshotQueryDep
from app.realtime_.streams.room_state import RoomStateStream


def get_room_state_stream(
    room_event_bus: RoomEventBusDep,
    room_snapshot_query: RoomSnapshotQueryDep,
) -> RoomStateStream:
    return RoomStateStream(room_event_bus, room_snapshot_query)


RoomStateStreamDep = Annotated[RoomStateStream, Depends(get_room_state_stream)]
