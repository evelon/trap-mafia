import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.pubsub.bus.deps import get_room_event_bus
from app.infra.pubsub.bus.room_event_bus import RoomEventBus
from app.infra.redis.client import get_redis_client
from app.infra.redis.pubsub import get_redis_pubsub
from app.repositories.deps import get_room_member_repo, get_user_repo
from app.repositories.room_member import RoomMemberRepo
from app.repositories.user import UserRepo
from app.services.auth import get_auth_service
from app.services.deps import get_room_service


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
def redis_client():
    return get_redis_client()


@pytest.fixture
def redis_pubsub(redis_client):
    return get_redis_pubsub(redis_client)


@pytest.fixture
def room_event_bus(redis_pubsub):
    return get_room_event_bus(redis_pubsub)


@pytest.fixture
def room_service(
    db_session: AsyncSession,
    room_member_repo: RoomMemberRepo,
    user_repo: UserRepo,
    room_event_bus: RoomEventBus,
):
    return get_room_service(db_session, room_member_repo, user_repo, room_event_bus)
