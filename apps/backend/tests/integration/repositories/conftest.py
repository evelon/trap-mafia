import pytest_asyncio
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.domain.enum import CaseStatus
from app.models.case import Case
from app.models.room import Room


@pytest_asyncio.fixture
async def user_case(db_session: AsyncSession, user_hosted_room: Room) -> Case:
    case = Case(
        room_id=user_hosted_room.id,
        host_user_id=user_hosted_room.host_id,
        status=CaseStatus.RUNNING,
        current_round_no=1,
    )
    db_session.add(case)
    await db_session.commit()
    return case


# Not in MVP
# @pytest_asyncio.fixture
# async def user2_case(db_session: AsyncSession, user2_hosted_room: Room) -> Case:
#     case = Case(
#         room_id=user2_hosted_room.id,
#         host_user_id=user2_hosted_room.host_id,
#         status=CaseStatus.RUNNING,
#         current_round_no=1,
#     )
#     db_session.add(case)
#     await db_session.commit()
#     return case
