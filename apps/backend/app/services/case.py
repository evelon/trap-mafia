from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.core.utils.datetime import datetime_to_utc_iso, now_utc_iso
from app.domain.case_logic.night import should_end_night, validate_red_vote
from app.domain.constants import case as case_const
from app.domain.enum import ActionType, CaseStatus
from app.domain.events.case import CaseEventDelta, CaseSnapshotType
from app.domain.exceptions.common import EntityNotFoundError, RoomCaseAlreadyRunningError
from app.infra.pubsub.bus.case_event_bus import CaseEventBus
from app.infra.pubsub.bus.room_event_bus import RoomEventBus
from app.infra.pubsub.topics import CaseTopic
from app.models.case import Case, CaseAction, CasePlayer, Phase
from app.repositories.case import CaseRepo
from app.repositories.case_history import CaseSnapshotHistoryRepo
from app.repositories.case_player import CasePlayerRepo
from app.repositories.phase import PhaseRepo
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
from app.schemas.common.ids import CaseId, PhaseId, RoomId, UserId
from app.schemas.room.mutation import CaseStartMutation

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
        phase_repo: PhaseRepo,
        room_event_bus: RoomEventBus,
        case_event_bus: CaseEventBus,
    ):
        self._db = db
        self._case_repo = case_repo
        self._case_player_repo = case_player_repo
        self._case_history_repo = case_history_repo
        self._room_member_repo = room_member_repo
        self._room_repo = room_repo
        self._phase_repo = phase_repo
        self._room_event_bus = room_event_bus
        self._case_event_bus = case_event_bus

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
                phase_type=PhaseType.NIGHT,
                seq_in_round=case_const.INITIAL_SEQ_IN_ROUND,
                phase_no_in_round=case_const.INITIAL_PHASE_NO_IN_ROUND,
                created_at=now_utc_iso(),
            ),
            players=[
                Player(
                    user_id=player.user_id,
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

    async def start_case(self, room_id: RoomId) -> CaseStartMutation:
        case = await self._case_repo.get_running_by_room_id(room_id=room_id)
        if case is not None:
            raise RoomCaseAlreadyRunningError(room_id)

        room = await self._room_repo.get_by_id(room_id=room_id)
        if room is None:
            logger.error(f"Room not found while starting case: room_id={room_id}")
            raise EntityNotFoundError("Room", {"room_id": room_id})

        # room member 조회
        snapshot_room_members = await self._room_member_repo.get_active_members_by_room_id(
            room_id=room_id
        )
        user_ids = [member.user_id for member in snapshot_room_members]
        user_id_to_username = {member.user_id: member.username for member in snapshot_room_members}

        # room 정보로 case record 생성
        case = await self._case_repo.create(room_id=room_id, host_user_id=room.host_id)
        await self._db.flush()

        # case record로 phase 생성
        phase = await self._phase_repo.create(case_id=case.id)

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
        case_history = await self._case_history_repo.create(
            case_id=case.id,
            snapshot_no=case_const.INITIAL_SNAPSHOT_NO,
            schema_version=schema_version,
            snapshot_json=snapshot.model_dump(mode="json"),
        )
        await self._db.commit()
        try:
            await self._case_event_bus.publish(
                CaseTopic(case.id),
                CaseEventDelta(
                    type=CaseSnapshotType.NIGHT,
                    phase_id=phase.id,
                    snapshot_no=case_history.snapshot_no,
                ),  # type: ignore[call-arg]
            )
        except Exception:
            pass
        return CaseStartMutation(subject_id=case.id)

    async def red_vote(
        self,
        *,
        case_id: UUID,
        actor_player_id: UUID,
        target_seat_no: int | None,  # None이면 skip
    ) -> None:

        phase = await self._phase_repo.get_current_by_case_id(case_id)
        if phase is None:
            raise EntityNotFoundError("CurrentPhase", {"case_id": case_id})

        case = await self._case_repo.get_by_id(case_id=case_id)
        if case is None:
            raise EntityNotFoundError("Case", {"case_id": case_id})

        case_players = await self._case_player_repo.list_by_case_id(case_id=case_id)
        actor = next((player for player in case_players if player.id == actor_player_id), None)
        if actor is None:
            raise EntityNotFoundError(
                "Actor",
                {"case_id": case_id, "actor_player_id": actor_player_id},
            )

        alive_player_ids = {player.id for player in case_players if player.life_left > 0}
        already_acted = await self._has_actor_already_acted(
            phase_id=phase.id,
            actor_player_id=actor_player_id,
        )
        is_night_phase = phase.phase_type == PhaseType.NIGHT
        validate_red_vote(
            is_night_phase=is_night_phase,
            actor_player_id=actor_player_id,
            alive_player_ids=alive_player_ids,
            target_seat_no=target_seat_no,
            actor_seat_no=actor.seat_no,
            max_seat_no=len(case_players),
            already_acted=already_acted,
        )

        try:
            await self._create_case_action(
                case_id=case_id,
                phase_id=phase.id,
                actor_player_id=actor_player_id,
                action_type=ActionType.NIGHT_ACTION_RED_VOTE
                if target_seat_no is not None
                else ActionType.NIGHT_ACTION_SKIP,
                night_target_seat_no=target_seat_no,
            )

            action_count = await self._count_actions(phase_id=phase.id)
            if should_end_night(
                alive_player_count=len(alive_player_ids),
                action_count=action_count,
            ):
                await self._resolve_night(case=case, phase=phase)
                return
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            raise

    # =========================
    # Private - 공통
    # =========================

    async def _build_snapshot(
        self,
        *,
        case: Case,
        phase: Phase,
    ) -> CaseSnapshot:
        """현재 상태로 snapshot 생성"""
        case_players = await self._case_player_repo.list_by_case_id(case_id=case.id)
        room_members = await self._room_member_repo.get_active_members_by_room_id(
            room_id=case.room_id
        )
        user_id_to_username = {member.user_id: member.username for member in room_members}

        phase_type = phase.phase_type

        return CaseSnapshot(
            schema_version=case_const.INITIAL_SCHEMA_VERSION,
            case_state=CaseState(
                case_id=case.id,
                status=case.status,
                round_no=case.current_round_no,
            ),
            phase_state=PhaseState(
                phase_id=phase.id,
                phase_type=phase.phase_type,
                seq_in_round=phase.seq_in_round,
                phase_no_in_round=phase.seq_in_round,
                created_at=datetime_to_utc_iso(phase.created_at),
            ),
            players=[
                Player(
                    user_id=player.user_id,
                    username=user_id_to_username[player.user_id],
                    seat_no=player.seat_no,
                    life_left=player.life_left,
                    vote_tokens=player.vote_tokens,
                )
                for player in sorted(case_players, key=lambda p: p.seat_no)
            ],
            night_phase_info=NightPhaseInfo() if phase_type == PhaseType.NIGHT else None,
            vote_phase_info=None,
            discuss_phase_info=None,
            logs=[],
        )

    async def _persist_snapshot(
        self,
        *,
        case_id: UUID,
        snapshot: CaseSnapshot,
    ) -> int:
        """snapshot 저장 후 snapshot_no 반환"""
        latest = await self._case_history_repo.get_latest_by_case_id(case_id=case_id)
        next_snapshot_no = 1 if latest is None else latest.snapshot_no + 1

        row = await self._case_history_repo.create(
            case_id=case_id,
            snapshot_no=next_snapshot_no,
            schema_version=snapshot.schema_version,
            snapshot_json=snapshot.model_dump(mode="json"),
        )
        await self._db.flush()
        return row.snapshot_no

    async def _emit_snapshot(
        self,
        *,
        case_id: CaseId,
        phase_id: PhaseId,
        snapshot_no: int,
    ) -> None:
        """pubsub emit"""
        await self._case_event_bus.publish(
            CaseTopic(case_id),
            CaseEventDelta(
                type=CaseSnapshotType.NIGHT,
                phase_id=phase_id,
                snapshot_no=snapshot_no,
            ),  # type: ignore[call-arg]
        )

    # =========================
    # Private - Action (공통)
    # =========================

    async def _create_case_action(
        self,
        *,
        case_id: UUID,
        phase_id: UUID,
        actor_player_id: UUID,
        action_type: ActionType,
        night_target_seat_no: int | None = None,
    ) -> CaseAction:
        action = CaseAction(
            case_id=case_id,
            phase_id=phase_id,
            actor_player_id=actor_player_id,
            action_type=action_type,
            night_target_seat_no=night_target_seat_no,
        )
        self._db.add(action)
        await self._db.flush()  # PK 확보

        return action

    async def _has_actor_already_acted(
        self,
        *,
        phase_id: UUID,
        actor_player_id: UUID,
    ) -> bool:
        """해당 phase에서 actor가 이미 action 했는지"""
        query = select(CaseAction.id).where(
            CaseAction.phase_id == phase_id,
            CaseAction.actor_player_id == actor_player_id,
        )
        result = await self._db.execute(query)
        return result.scalar_one_or_none() is not None

    async def _count_actions(
        self,
        *,
        phase_id: UUID,
    ) -> int:
        """해당 phase의 action 개수"""
        query = select(func.count()).select_from(CaseAction).where(CaseAction.phase_id == phase_id)
        result = await self._db.execute(query)
        return int(result.scalar_one())

    # =========================
    # Private - NIGHT
    # =========================

    async def _resolve_night(
        self,
        *,
        case: Case,
        phase: Phase,
    ) -> None:
        """
        NIGHT 종료 처리:
        - 다음 phase 생성
        - snapshot 생성
        - emit
        """
        phase.closed_at = datetime.now(timezone.utc)

        next_phase = Phase(
            case_id=case.id,
            round_no=case.current_round_no,
            seq_in_round=phase.seq_in_round + 1,
            phase_type=PhaseType.DISCUSS,
        )
        self._db.add(next_phase)
        await self._db.flush()

        snapshot = await self._build_snapshot(case=case, phase=phase)
        snapshot_no = await self._persist_snapshot(case_id=case.id, snapshot=snapshot)

        await self._db.commit()
        await self._emit_snapshot(case_id=case.id, phase_id=phase.id, snapshot_no=snapshot_no)
