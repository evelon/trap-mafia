from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.schemas.case.result import (
    CaseResultData,
    CaseResultErrorCode,
    CaseResultErrorResponse,
    CaseResultPlayer,
    CaseResultSuccessCode,
    CaseResultSuccessResponse,
    CaseResultWinner,
)

router = APIRouter()

# NOTE: MVP mock behavior
# - If case_id ends with "...0000": treat as not found
# - If case_id ends with "...0001": treat as still running
# - Otherwise: return a fixed mock result
_NOT_FOUND_CASE_ID = UUID("00000000-0000-0000-0000-000000000000")
_RUNNING_CASE_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.get(
    "/result",
    summary="case_result",
    response_model=CaseResultSuccessResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": CaseResultErrorResponse},
        status.HTTP_409_CONFLICT: {"model": CaseResultErrorResponse},
    },
)
def get_case_result(case_id: UUID):
    """
    GET /api/cases/{case_id}/result

    의미:
    - 과거 case의 최종 결과를 조회한다.
    - case가 종료되지 않았다면 결과를 제공하지 않는다.

    응답:
    - 200: 조회 성공 (CaseResultData)
    - 404: CASE_NOT_FOUND (case_id에 해당하는 case가 없음)
    - 409: CASE_RUNNING (아직 case가 진행 중)
    """
    if case_id == _NOT_FOUND_CASE_ID:
        return CaseResultErrorResponse(
            ok=False,
            code=CaseResultErrorCode.CASE_NOT_FOUND,
            message=None,
            data=None,
            meta=None,
        )

    if case_id == _RUNNING_CASE_ID:
        return CaseResultErrorResponse(
            ok=False,
            code=CaseResultErrorCode.CASE_RUNNING,
            message=None,
            data=None,
            meta=None,
        )

    data = CaseResultData(
        winner=CaseResultWinner.BLUE,
        players=[
            CaseResultPlayer(seat_no=0, team=CaseResultWinner.BLUE),
            CaseResultPlayer(seat_no=1, team=CaseResultWinner.RED),
            CaseResultPlayer(seat_no=2, team=CaseResultWinner.BLUE),
            CaseResultPlayer(seat_no=3, team=CaseResultWinner.RED),
        ],
    )

    return CaseResultSuccessResponse(
        ok=True,
        code=CaseResultSuccessCode.OK,
        message=None,
        data=data,
        meta=None,
    )
