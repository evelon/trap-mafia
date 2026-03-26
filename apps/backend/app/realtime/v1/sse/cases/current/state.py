from fastapi import APIRouter

from app.core.deps.require_in_case import CurrentCase
from app.realtime_.sse.stream import sse_stream_response
from app.realtime_.streams.deps import CaseStateStreamDep
from app.repositories.deps import CaseHistoryRepoDep
from app.schemas.case.sse_response import CaseNotCreatedEnvelope
from app.schemas.sse.response import CaseRESTRespType

router = APIRouter()


@router.get("/state")
async def case_state_sse(
    case: CurrentCase,
    case_history_repo: CaseHistoryRepoDep,
    case_state_stream: CaseStateStreamDep,
    after_snapshot_no: int | None = None,
):
    """GET /rt/v1/sse/cases/current/state?after_snapshot_no=...

    Notion: room_state
    - Auth: User
    - Permission: In Running Case

    Response (SSE)
    - event: CASE_EVENT
    - id: 1부터 단조증가
    - data: RoomStateResponse(JSON)

    Response (REST)
    - 403: PERMISSION_DENIED_NOT_IN_ROOM
    """
    latest = await case_history_repo.get_latest_by_case_id(case_id=case.id)

    if (
        after_snapshot_no is not None
        and latest is not None
        and after_snapshot_no > latest.snapshot_no
    ):
        return CaseNotCreatedEnvelope(
            ok=True,
            code=CaseRESTRespType.SNAPSHOT_NOT_CREATED,
            message=None,
            data=None,
            meta={
                "after_snapshot_no": after_snapshot_no,
                "latest_snapshot_no": latest.snapshot_no,
            },
        )

    stream = case_state_stream.stream(case_id=case.id, after_snapshot_no=after_snapshot_no)

    return sse_stream_response(stream)
