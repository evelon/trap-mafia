from typing import Annotated

from fastapi import Depends

from app.infra.db.session import DbSessionDep
from app.infra.pubsub.bus.deps import CaseEventBusDep, RoomEventBusDep
from app.repositories.deps import (
    CaseHistoryRepoDep,
    CasePlayerRepoDep,
    CaseRepoDep,
    PhaseRepoDep,
    RoomMemberRepoDep,
    RoomRepoDep,
    UserRepoDep,
)
from app.services.case import CaseService
from app.services.room import RoomService


def get_room_service(
    db: DbSessionDep,
    repo: RoomMemberRepoDep,
    user_repo: UserRepoDep,
    room_event_bus: RoomEventBusDep,
) -> RoomService:
    return RoomService(db, member_repo=repo, user_repo=user_repo, room_event_bus=room_event_bus)


RoomServiceDep = Annotated[RoomService, Depends(get_room_service)]


def get_case_service(
    db: DbSessionDep,
    case_repo: CaseRepoDep,
    case_player_repo: CasePlayerRepoDep,
    case_history_repo: CaseHistoryRepoDep,
    room_member_repo: RoomMemberRepoDep,
    room_repo: RoomRepoDep,
    phase_repo: PhaseRepoDep,
    room_event_bus: RoomEventBusDep,
    case_event_bus: CaseEventBusDep,
) -> CaseService:
    case_service = CaseService(
        db,
        case_repo=case_repo,
        case_player_repo=case_player_repo,
        case_history_repo=case_history_repo,
        room_member_repo=room_member_repo,
        room_repo=room_repo,
        phase_repo=phase_repo,
        room_event_bus=room_event_bus,
        case_event_bus=case_event_bus,
    )
    return case_service


CaseServiceDep = Annotated[CaseService, Depends(get_case_service)]
