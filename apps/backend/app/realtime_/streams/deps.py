from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.infra.pubsub.bus.deps import CaseEventBusDep, RoomEventBusDep
from app.queries.deps import RoomSnapshotQueryDep
from app.realtime_.streams.case_state import CaseStateStream
from app.realtime_.streams.room_state import RoomStateStream
from app.repositories.deps import CaseHistoryRepoDep


def get_room_state_stream(
    room_event_bus: RoomEventBusDep,
    room_snapshot_query: RoomSnapshotQueryDep,
) -> RoomStateStream:
    return RoomStateStream(room_event_bus, room_snapshot_query)


RoomStateStreamDep = Annotated[RoomStateStream, Depends(get_room_state_stream)]


def get_case_state_stream(
    case_event_bus: CaseEventBusDep,
    case_history_repo: CaseHistoryRepoDep,
) -> CaseStateStream:
    return CaseStateStream(case_event_bus=case_event_bus, case_history_repo=case_history_repo)


CaseStateStreamDep = Annotated[CaseStateStream, Depends(get_case_state_stream)]
