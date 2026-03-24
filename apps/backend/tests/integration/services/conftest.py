import pytest
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.infra.pubsub.bus.case_event_bus import CaseEventBus
from app.infra.pubsub.bus.room_event_bus import RoomEventBus
from app.infra.redis.client import Redis
from app.infra.redis.pubsub import RedisPubSub
from app.repositories.case import CaseRepo
from app.repositories.case_history import CaseSnapshotHistoryRepo
from app.repositories.case_player import CasePlayerRepo
from app.repositories.phase import PhaseRepo
from app.repositories.room import RoomRepo
from app.repositories.room_member import RoomMemberRepo
from app.services.case import CaseService


@pytest.fixture
def room_event_bus() -> RoomEventBus:
    return RoomEventBus(RedisPubSub(Redis()))


@pytest.fixture
def case_event_bus() -> CaseEventBus:
    return CaseEventBus(RedisPubSub(Redis()))


# Repository fixtures
@pytest.fixture
def case_repo(db_session: AsyncSession) -> CaseRepo:
    return CaseRepo(db_session)


@pytest.fixture
def case_player_repo(db_session: AsyncSession) -> CasePlayerRepo:
    return CasePlayerRepo(db_session)


@pytest.fixture
def case_history_repo(db_session: AsyncSession) -> CaseSnapshotHistoryRepo:
    return CaseSnapshotHistoryRepo(db_session)


@pytest.fixture
def room_member_repo(db_session: AsyncSession) -> RoomMemberRepo:
    return RoomMemberRepo(db_session)


@pytest.fixture
def room_repo(db_session: AsyncSession) -> RoomRepo:
    return RoomRepo(db_session)


@pytest.fixture
def phase_repo(db_session: AsyncSession) -> PhaseRepo:
    return PhaseRepo(db_session)


@pytest.fixture
def case_service(
    db_session: AsyncSession,
    case_repo: CaseRepo,
    case_player_repo: CasePlayerRepo,
    case_history_repo: CaseSnapshotHistoryRepo,
    room_member_repo: RoomMemberRepo,
    room_repo: RoomRepo,
    phase_repo: PhaseRepo,
    room_event_bus: RoomEventBus,
    case_event_bus: CaseEventBus,
) -> CaseService:
    return CaseService(
        db=db_session,
        case_repo=case_repo,
        case_player_repo=case_player_repo,
        case_history_repo=case_history_repo,
        room_member_repo=room_member_repo,
        room_repo=room_repo,
        phase_repo=phase_repo,
        room_event_bus=room_event_bus,
        case_event_bus=case_event_bus,
    )
