from typing import Annotated

from fastapi import Depends

from app.infra.db.session import DbSessionDep
from app.repositories.case import CaseRepo
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
