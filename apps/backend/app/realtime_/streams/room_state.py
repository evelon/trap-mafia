from __future__ import annotations

from collections.abc import AsyncIterator

from app.domain.events.room import RoomSnapshotType
from app.infra.pubsub.bus.room_event_bus import RoomEventBus
from app.infra.pubsub.topics import RoomTopic
from app.mvp import mvp_logs_mapper
from app.queries.room_snapshot import RoomSnapshotQuery
from app.realtime_.sse.frame import build_envelope_sse_frame
from app.schemas.common.ids import RoomId, UserId
from app.schemas.room.sse_response import RoomStateEnvelope
from app.schemas.sse.response import SSEEnvelopeCode, SSEEventType


class RoomStateStream:
    def __init__(
        self,
        room_event_bus: RoomEventBus,
        room_snapshot_query: RoomSnapshotQuery,
    ) -> None:
        self._room_event_bus = room_event_bus
        self._room_snapshot_query = room_snapshot_query

    def _build_close_envelope(self, event_type: RoomSnapshotType) -> RoomStateEnvelope:
        if event_type == RoomSnapshotType.MEMBER_LEFT:
            code = SSEEnvelopeCode.ROOM_LEAVE
        elif event_type == RoomSnapshotType.MEMBER_KICKED:
            code = SSEEnvelopeCode.ROOM_KICKED
        else:
            # LOGGING
            code = SSEEnvelopeCode.ROOM_MEMBERSHIP_INVALID
        return RoomStateEnvelope(ok=True, code=code, message=None, data=None)

    async def stream(self, user_id: UserId, room_id: RoomId) -> AsyncIterator[str]:
        event_id = 1  # MVP
        room_topic = RoomTopic(room_id)

        on_connect_logs = mvp_logs_mapper(RoomSnapshotType.ON_CONNECT)
        snapshot = await self._room_snapshot_query.build_snapshot(
            room_id=room_id,
            last_event=RoomSnapshotType.ON_CONNECT,
            logs=on_connect_logs,
        )

        initial_envelope = RoomStateEnvelope(
            ok=True,
            code=SSEEnvelopeCode.ROOM_STATE,
            message=None,
            data=snapshot,
        )
        yield build_envelope_sse_frame(
            event=SSEEventType.ON_CONNECT,
            id_=event_id,
            data=initial_envelope,
        )

        async for event_delta in self._room_event_bus.subscribe(room_topic):
            if event_delta.type == RoomSnapshotType.STREAM_CLOSE:
                close_envelope = self._build_close_envelope(event_delta.type)
                yield build_envelope_sse_frame(
                    event=SSEEventType.STREAM_CLOSE,
                    id_=event_id,
                    data=close_envelope,
                )
                return

            logs = mvp_logs_mapper(event_delta.type)
            snapshot = await self._room_snapshot_query.build_snapshot(
                room_id=room_id,
                last_event=event_delta.type,
                logs=logs,
            )

            if user_id not in [member.user_id for member in snapshot.members]:
                close_envelope = self._build_close_envelope(event_delta.type)
                yield build_envelope_sse_frame(
                    event=SSEEventType.ROOM_EVENT,
                    id_=event_id,
                    data=close_envelope,
                )
                return

            envelope = RoomStateEnvelope(
                ok=True,
                code=SSEEnvelopeCode.ROOM_STATE,
                message=None,
                data=snapshot,
            )

            yield build_envelope_sse_frame(
                event=SSEEventType.ROOM_EVENT,
                id_=event_id,
                data=envelope,
            )
