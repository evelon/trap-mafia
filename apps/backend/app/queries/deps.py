from typing import Annotated

from fastapi import Depends

from app.queries.room_snapshot import RoomSnapshotQuery
from app.repositories.deps import CaseRepoDep, RoomMemberRepoDep, RoomRepoDep


def get_room_snapshot_query(
    room_repo: RoomRepoDep, room_member_repo: RoomMemberRepoDep, case_repo: CaseRepoDep
) -> RoomSnapshotQuery:
    return RoomSnapshotQuery(
        room_repo=room_repo,
        room_member_repo=room_member_repo,
        case_repo=case_repo,
    )


RoomSnapshotQueryDep = Annotated[RoomSnapshotQuery, Depends(get_room_snapshot_query)]
