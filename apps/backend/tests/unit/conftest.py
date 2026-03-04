import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.room_member import RoomMemberRepo, get_room_member_repo
from app.repositories.user import UserRepo, get_user_repo
from app.services.auth import get_auth_service
from app.services.room import get_room_service


@pytest.fixture
def user_repo(db_session: AsyncSession):
    return get_user_repo(db_session)


@pytest.fixture
def auth_service(db_session: AsyncSession, user_repo: UserRepo):
    return get_auth_service(db_session, user_repo)


@pytest.fixture
def room_member_repo(db_session: AsyncSession):
    return get_room_member_repo(db_session)


@pytest.fixture
def room_service(db_session: AsyncSession, room_member_repo: RoomMemberRepo, user_repo: UserRepo):
    return get_room_service(db_session, room_member_repo, user_repo)
