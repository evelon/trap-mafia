import anyio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.enum import CaseStatus
from app.schemas.case.state import CaseSnapshot
from app.schemas.room.response import (
    CaseStartResponse,
)
from app.schemas.sse.response import SSEEnvelopeCode, SSEEventType
from tests._helpers.auth import UserAuth
from tests._helpers.entity import room_with_members
from tests._helpers.sse import SSEReader


@pytest.mark.anyio
@pytest.mark.timeout(10)
async def test_case_state_sse_receives_initial_snapshot_after_case_start(
    live_db_session: AsyncSession,
    sse_client: AsyncClient,
    sse_user_auth: UserAuth,
):
    # given
    usernames = [sse_user_auth["username"], "username3", "username4", "username5"]
    _ = await room_with_members(live_db_session, usernames)

    # when: host가 case start
    start_res = await sse_client.post(
        "/api/v1/rooms/current/case-start", json={"red_player_count": None}
    )
    assert start_res.status_code == 200, start_res.text

    start_envelope = CaseStartResponse.model_validate(start_res.json())
    assert start_envelope.ok is True
    assert start_envelope.data

    case_id = start_envelope.data.subject_id

    # then: case state SSE 구독
    async with sse_client.stream(
        "GET",
        "/rt/v1/sse/cases/current/state",
    ) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")

        reader = SSEReader(r)
        first = await reader.read_one(timeout_s=3.0)

        # SSE protocol fields
        assert first["event"] == SSEEventType.CASE_EVENT

        # id: (round_no).(seq_in_round)
        sse_id = first["id"]
        assert sse_id is not None
        assert int(sse_id) == 1

        # envelope
        body = first["data"]
        assert body["ok"] is True
        assert body["code"] == SSEEnvelopeCode.CASE_STATE
        assert body["message"] is None

        # snapshot validation
        snapshot = CaseSnapshot.model_validate(body["data"])

        assert snapshot.schema_version == 1

        assert snapshot.case_state.case_id == case_id
        assert snapshot.case_state.status == CaseStatus.RUNNING
        assert snapshot.case_state.round_no == 1

        assert snapshot.snapshot_no == 1

        assert len(snapshot.players) == 4
        assert [p.seat_no for p in snapshot.players] == list(range(len(snapshot.players)))

        assert snapshot.logs == []

        with anyio.move_on_after(0.5):
            await reader.read_one()
            assert False, "sse should not emit additional snapshot"
