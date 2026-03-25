import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress

from app.domain.events.case import CaseEventDelta
from app.infra.pubsub.bus.case_event_bus import CaseEventBus
from app.infra.pubsub.topics import CaseTopic
from app.realtime_.sse.frame import build_envelope_sse_frame
from app.repositories.case_history import CaseSnapshotHistoryRepo
from app.schemas.case.sse_response import CaseStateEnvelope
from app.schemas.case.state import CaseSnapshot
from app.schemas.common.ids import CaseId
from app.schemas.sse.response import SSEEnvelopeCode, SSEEventType


class CaseStateStream:
    def __init__(
        self,
        *,
        case_event_bus: CaseEventBus,
        case_history_repo: CaseSnapshotHistoryRepo,
    ) -> None:
        self._case_event_bus = case_event_bus
        self._case_history_repo = case_history_repo

    async def _build_frames(
        self, case_id: CaseId, last_sent_no: int
    ) -> AsyncIterator[tuple[str, int]]:
        rows = await self._case_history_repo.get_after_snapshot_no(
            case_id=case_id,
            last_seen_no=last_sent_no,
        )
        for row in rows:
            snapshot = CaseSnapshot.model_validate(row.snapshot_json)
            envelope = CaseStateEnvelope(
                ok=True, code=SSEEnvelopeCode.CASE_STATE, message=None, data=snapshot
            )
            yield (
                build_envelope_sse_frame(
                    event=SSEEventType.CASE_EVENT,
                    data=envelope,
                    id_=row.snapshot_no,
                ),
                row.snapshot_no,
            )

    async def stream(
        self,
        *,
        case_id: CaseId,
        after_snapshot_no: int | None = None,
    ) -> AsyncIterator[str]:
        """
        emit 규칙:
        - after_snapshot_no가 없으면 1번부터 최신까지 전부 replay
        - after_snapshot_no가 있으면 그 이후 snapshot만 replay
        - replay 중간에 publish된 delta는 queue에 쌓아뒀다가 replay 후 drain
        - 이후에는 pubsub delta가 올 때마다 해당 snapshot_no의 snapshot emit
        """
        case_topic = CaseTopic(case_id)
        q: asyncio.Queue[CaseEventDelta] = asyncio.Queue()

        async def _subscriber() -> None:
            async for delta in self._case_event_bus.subscribe(case_topic):
                await q.put(delta)

        sub_task = asyncio.create_task(_subscriber())

        try:
            last_sent_no = after_snapshot_no or 0

            # 1) 먼저 현재까지 쌓인 snapshot replay
            async for frame, last_seen_no in self._build_frames(case_id, last_sent_no):
                yield frame
                last_sent_no = last_seen_no

            # 2) replay 중 들어온 delta drain
            while True:
                try:
                    delta = q.get_nowait()
                except asyncio.QueueEmpty:
                    break
                if delta.snapshot_no <= last_sent_no:
                    continue

                async for frame, last_seen_no in self._build_frames(case_id, last_sent_no):
                    yield frame
                    last_sent_no = last_seen_no

            # 3) 이제부터는 live consume
            while True:
                delta = await q.get()

                if delta.snapshot_no <= last_sent_no:
                    continue

                async for frame, last_seen_no in self._build_frames(case_id, last_sent_no):
                    yield frame
                    last_sent_no = last_seen_no

        finally:
            sub_task.cancel()
            with suppress(asyncio.CancelledError):
                await sub_task
