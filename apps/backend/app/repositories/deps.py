from typing import Annotated

from fastapi import Depends

from app.infra.db.session import DbSessionDep
from app.repositories.case import CaseRepo
from app.repositories.case_history import CaseSnapshotHistoryRepo
from app.repositories.case_player import CasePlayerRepo
from app.repositories.phase import PhaseRepo
from app.repositories.room import RoomRepo
from app.repositories.room_member import RoomMemberRepo
from app.repositories.user import UserRepo


def get_room_repo(db: DbSessionDep) -> RoomRepo:
    return RoomRepo(db)


RoomRepoDep = Annotated[RoomRepo, Depends(get_room_repo)]


def get_room_member_repo(db: DbSessionDep) -> RoomMemberRepo:
    return RoomMemberRepo(db)


RoomMemberRepoDep = Annotated[RoomMemberRepo, Depends(get_room_member_repo)]


def get_case_repo(db: DbSessionDep) -> CaseRepo:
    return CaseRepo(db)


CaseRepoDep = Annotated[CaseRepo, Depends(get_case_repo)]


def get_user_repo(db: DbSessionDep) -> UserRepo:
    return UserRepo(db)


UserRepoDep = Annotated[UserRepo, Depends(get_user_repo)]


def get_case_player_repo(db: DbSessionDep) -> CasePlayerRepo:
    return CasePlayerRepo(db)


CasePlayerRepoDep = Annotated[CasePlayerRepo, Depends(get_case_player_repo)]


def get_case_history_repo(db: DbSessionDep) -> CaseSnapshotHistoryRepo:
    return CaseSnapshotHistoryRepo(db)


CaseHistoryRepoDep = Annotated[CaseSnapshotHistoryRepo, Depends(get_case_history_repo)]


def get_phase_repo(db: DbSessionDep) -> PhaseRepo:
    return PhaseRepo(db)


PhaseRepoDep = Annotated[PhaseRepo, Depends(get_phase_repo)]
