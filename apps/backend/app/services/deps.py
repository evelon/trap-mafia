from typing import Annotated

from fastapi import Depends

from app.infra.db.session import DbSessionDep
from app.infra.pubsub.bus.deps import RoomEventBusDep
from app.repositories.deps import RoomMemberRepoDep, UserRepoDep
from app.services.room import RoomService


def get_room_service(
    db: DbSessionDep,
    repo: RoomMemberRepoDep,
    user_repo: UserRepoDep,
    room_event_bus: RoomEventBusDep,
) -> RoomService:
    return RoomService(db, member_repo=repo, user_repo=user_repo, room_event_bus=room_event_bus)


RoomServiceDep = Annotated[RoomService, Depends(get_room_service)]
