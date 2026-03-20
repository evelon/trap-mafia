import logging
from uuid import uuid4

from sqlalchemy.ext.asyncio.session import AsyncSession

from app.core.utils.datetime import now_utc_iso
from app.domain.constants import case as case_const
from app.domain.enum import CaseStatus
from app.models.case import Case, CasePlayer
from app.repositories.case import CaseRepo
from app.repositories.case_history import CaseSnapshotHistoryRepo
from app.repositories.case_player import CasePlayerRepo
from app.repositories.room import RoomRepo
from app.repositories.room_member import RoomMemberRepo
from app.schemas.case.state import (
    CaseSnapshot,
    CaseState,
    NightPhaseInfo,
    PhaseState,
    PhaseType,
    Player,
)
from app.schemas.common.ids import RoomId, UserId

logger = logging.getLogger(__name__)


class CaseService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        case_repo: CaseRepo,
        case_player_repo: CasePlayerRepo,
        case_history_repo: CaseSnapshotHistoryRepo,
        room_member_repo: RoomMemberRepo,
        room_repo: RoomRepo,
    ):
        self._db = db
        self._case_repo = case_repo
        self._case_player_repo = case_player_repo
        self._case_history_repo = case_history_repo
        self._room_member_repo = room_member_repo
        self._room_repo = room_repo

    def _build_initial_snapshot(
        self,
        case: Case,
        schema_version: int,
        *,
        case_players: list[CasePlayer],
        user_id_to_username: dict[UserId, str],
    ) -> CaseSnapshot:

        return CaseSnapshot(
            schema_version=schema_version,
            case_state=CaseState(
                case_id=case.id,
                status=CaseStatus.RUNNING,
                round_no=case_const.INITIAL_ROUND_NO,
            ),
            phase_state=PhaseState(
                phase_id=uuid4(),
                history_id=1,
                phase_type=PhaseType.NIGHT,
                seq_in_round=case_const.INITIAL_SEQ_IN_ROUND,
                phase_no_in_round=case_const.INITIAL_PHASE_NO_IN_ROUND,
                opened_at=now_utc_iso(),
            ),
            players=[
                Player(
                    username=user_id_to_username[player.user_id],
                    seat_no=player.seat_no,
                    life_left=player.life_left,
                    vote_tokens=player.vote_tokens,
                )
                for player in sorted(case_players, key=lambda p: p.seat_no)
            ],
            night_phase_info=NightPhaseInfo(),
            vote_phase_info=None,
            discuss_phase_info=None,
            logs=[],
        )

    async def start_case(self, room_id: RoomId) -> Case:

        room = await self._room_repo.get_by_id(room_id=room_id)
        if room is None:
            logger.error(f"Room not found while starting case: room_id={room_id}")
            raise LookupError(f"Room not found while starting case: room_id={room_id}")

        # room member 조회
        snapshot_room_members = await self._room_member_repo.get_active_members_by_room_id(
            room_id=room_id
        )
        user_ids = [member.user_id for member in snapshot_room_members]
        user_id_to_username = {member.user_id: member.username for member in snapshot_room_members}

        # room 정보로 case record 생성
        case = await self._case_repo.create(room_id=room_id, host_user_id=room.host_id)
        await self._db.flush()

        # case record와 user record로 case_player 생성
        case_players = await self._case_player_repo.create_many(case_id=case.id, user_ids=user_ids)
        await self._db.flush()

        schema_version = case_const.INITIAL_SCHEMA_VERSION
        # 모든 정보를 합쳐 snapshot 만들기
        snapshot = self._build_initial_snapshot(
            case,
            schema_version,
            case_players=case_players,
            user_id_to_username=user_id_to_username,
        )
        _ = await self._case_history_repo.create(
            case_id=case.id,
            snapshot_no=case_const.INITIAL_SNAPSHOT_NO,
            schema_version=schema_version,
            snapshot_json=snapshot.model_dump(mode="json"),
        )
        await self._db.flush()
        return case
