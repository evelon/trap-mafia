import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.models.auth import User
from app.models.case import Case
from app.repositories.case_player import CasePlayerRepo
from app.schemas.common.ids import UserId


async def _get_user_by_user_id(db_session: AsyncSession, user_id: UserId):
    q = select(User).where(User.id == user_id)
    return (await db_session.execute(q)).scalar_one


async def _create_user(db_session: AsyncSession, *, username: str) -> User:
    user = User(username=username)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.anyio
async def test_create_many_inserts_case_players(db_session: AsyncSession, user_case: Case):
    repo = CasePlayerRepo(db_session)

    case_id = user_case.id
    user1 = await _create_user(db_session, username="u1")
    user2 = await _create_user(db_session, username="u2")

    host_user_id = user_case.host_user_id
    user1_id = user1.id
    user2_id = user2.id

    # act
    await repo.create_many(
        case_id=case_id,
        user_ids=[
            host_user_id,
            user1_id,
            user2_id,
        ],
    )
    await db_session.commit()

    rows = await repo.list_by_case_id(case_id=case_id)

    assert len(rows) == 3

    assert rows[0].user_id == host_user_id
    assert rows[0].seat_no == 0
    assert rows[0].life_left == 2
    assert rows[0].vote_tokens == 0

    assert rows[1].user_id == user1_id
    assert rows[1].seat_no == 1
    assert rows[1].life_left == 2
    assert rows[1].vote_tokens == 0

    assert rows[2].user_id == user2_id
    assert rows[2].seat_no == 2
    assert rows[2].life_left == 2
    assert rows[2].vote_tokens == 0
