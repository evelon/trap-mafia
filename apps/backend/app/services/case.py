from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio.session import AsyncSession

from app.core.utils.datetime import datetime_to_utc_iso
from app.domain.case_logic.night import resolve_red_vote, should_end_night, validate_red_vote
from app.domain.constants import case as case_const
from app.domain.enum import ActionType
from app.domain.events.case import CaseEventDelta, CaseSnapshotType
from app.domain.exceptions.common import EntityNotFoundError, RoomCaseAlreadyRunningError
from app.infra.pubsub.bus.case_event_bus import CaseEventBus
from app.infra.pubsub.bus.room_event_bus import RoomEventBus
from app.infra.pubsub.topics import CaseTopic
from app.models.case import Case, CasePlayer, Phase
from app.models.room import Room
from app.repositories.case import CaseRepo
from app.repositories.case_action import CaseActionRepo
from app.repositories.case_history import CaseSnapshotHistoryRepo
from app.repositories.case_player import CasePlayerRepo
from app.repositories.phase import PhaseRepo
from app.repositories.room import RoomRepo
from app.repositories.room_member import RoomMemberRepo
from app.schemas.case.state import (
    BlueVoteInitResult,
    CaseSnapshot,
    CaseState,
    NightPhaseResult,
    PhaseState,
    PhaseType,
    Player,
    RoundEndResult,
    VotePhaseResult,
)
from app.schemas.common.ids import CaseId, PhaseId, PlayerId, RoomId, UserId
from app.schemas.room.mutation import CaseStartMutation

logger = logging.getLogger(__name__)


@dataclass
class _CaseInitContext:
    room: Room
    user_ids: list[UserId]
    id_to_username: dict[UserId, str]


@dataclass
class _RedVoteContext:
    case: Case
    phase: Phase
    case_players: list[CasePlayer]
    actor: CasePlayer
    alive_player_ids: set[PlayerId]


class CaseService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        case_repo: CaseRepo,
        case_action_repo: CaseActionRepo,
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
        self._case_action_repo = case_action_repo
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
        *,
        phase: Phase,
        schema_version: int,
        case_players: list[CasePlayer],
        user_id_to_username: dict[UserId, str],
    ) -> CaseSnapshot:
        return CaseSnapshot(
            schema_version=schema_version,
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
            night_phase_result=None,
            blue_vote_init_result=None,
            vote_phase_result=None,
            round_end_result=None,
            logs=[],
        )

    async def start_case(self, room_id: RoomId) -> CaseStartMutation:
        running_case = await self._case_repo.get_running_by_room_id(room_id=room_id)
        if running_case is not None:
            raise RoomCaseAlreadyRunningError(room_id)

        ctx = await self._get_case_init_context(room_id=room_id)
        room = ctx.room
        user_ids = ctx.user_ids
        user_id_to_username = ctx.id_to_username

        case, phase, case_players, schema_version = await self._bootstrap_case(
            room=room, user_ids=user_ids
        )
        # 모든 정보를 합쳐 snapshot 만들기
        snapshot = self._build_initial_snapshot(
            case,
            phase=phase,
            schema_version=schema_version,
            case_players=case_players,
            user_id_to_username=user_id_to_username,
        )
        case_history = await self._case_history_repo.create(
            case_id=case.id,
            snapshot_no=case_const.INITIAL_SNAPSHOT_NO,
            schema_version=schema_version,
            snapshot_json=snapshot.model_dump(mode="json"),
        )
        try:
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            raise
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
            logger.exception(
                "Failed to publish initial case snapshot event",
                extra={"case_id": str(case.id), "phase_id": str(phase.id)},
            )
        return CaseStartMutation(subject_id=case.id)

    async def red_vote(
        self,
        *,
        case_id: UUID,
        actor_player_id: UUID,
        target_seat_no: int | None,  # None이면 skip
    ) -> None:
        ctx = await self._get_red_vote_context(case_id=case_id, actor_player_id=actor_player_id)
        case = ctx.case
        phase = ctx.phase
        case_players = ctx.case_players
        actor = ctx.actor
        alive_player_ids = ctx.alive_player_ids

        already_acted = await self._case_action_repo.exists_by_phase_and_actor(
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
            alive_seat_nos={player.seat_no for player in case_players if player.life_left > 0},
            already_acted=already_acted,
        )

        try:
            action_type = (
                ActionType.NIGHT_ACTION_RED_VOTE
                if target_seat_no is not None
                else ActionType.NIGHT_ACTION_SKIP
            )
            await self._case_action_repo.create(
                case_id=case_id,
                phase_id=phase.id,
                actor_player_id=actor_player_id,
                action_type=action_type,
                night_target_seat_no=target_seat_no,
            )
            if target_seat_no is not None:
                actor.vote_tokens = 0

            action_count = await self._case_action_repo.count_by_phase_id(phase_id=phase.id)
            if should_end_night(
                alive_player_count=len(alive_player_ids),
                action_count=action_count,
            ):
                await self._resolve_night(case=case, resolved_phase=phase)
                return
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            raise

    # =========================
    # Private - 공통
    # =========================

    def _build_phase_snapshot(
        self,
        *,
        case: Case,
        phase: Phase,
        case_players: list[CasePlayer],
        user_id_to_username: dict[UserId, str],
        night_phase_result: NightPhaseResult | None,
        blue_vote_init_result: BlueVoteInitResult | None,
        vote_phase_result: VotePhaseResult | None,
        round_end_result: RoundEndResult | None,
    ) -> CaseSnapshot:
        """주어진 데이터로 phase snapshot을 조립한다."""

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
            night_phase_result=night_phase_result,
            blue_vote_init_result=blue_vote_init_result,
            vote_phase_result=vote_phase_result,
            round_end_result=round_end_result,
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
    # Private - CASE OPEN
    # =========================

    async def _get_case_init_context(self, *, room_id: RoomId) -> _CaseInitContext:
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

        return _CaseInitContext(
            room=room,
            user_ids=user_ids,
            id_to_username=user_id_to_username,
        )

    async def _bootstrap_case(self, *, room, user_ids):
        # room 정보로 case record 생성
        case = await self._case_repo.create(room_id=room.id, host_user_id=room.host_id)
        await self._db.flush()

        # case record로 phase 생성
        phase = await self._phase_repo.create(case_id=case.id)

        # case record와 user record로 case_player 생성
        case_players = await self._case_player_repo.create_many(case_id=case.id, user_ids=user_ids)
        await self._db.flush()

        schema_version = case_const.INITIAL_SCHEMA_VERSION

        return case, phase, case_players, schema_version

    # =========================
    # Private - NIGHT
    # =========================

    async def _get_red_vote_context(
        self, *, case_id: CaseId, actor_player_id: PlayerId
    ) -> _RedVoteContext:
        phase = await self._phase_repo.get_current_by_case_id(case_id)
        if phase is None:
            raise EntityNotFoundError("Phase", {"case_id": case_id})

        case = await self._case_repo.get_by_id(case_id=case_id)
        if case is None:
            raise EntityNotFoundError("Case", {"case_id": case_id})

        case_players = await self._case_player_repo.list_by_case_id(case_id=case_id)
        actor = next((player for player in case_players if player.id == actor_player_id), None)
        if actor is None:
            raise EntityNotFoundError(
                "CasePlayer",
                {"case_id": case_id, "actor_player_id": actor_player_id},
            )

        alive_player_ids = {player.id for player in case_players if player.life_left > 0}
        return _RedVoteContext(
            case=case,
            phase=phase,
            case_players=case_players,
            actor=actor,
            alive_player_ids=alive_player_ids,
        )

    async def _resolve_night(
        self,
        *,
        case: Case,
        resolved_phase: Phase,
    ) -> None:
        """
        NIGHT 종료 처리:
        - 다음 phase 생성
        - snapshot 생성
        - emit
        """
        resolved_phase.closed_at = datetime.now(timezone.utc)

        actions = await self._case_action_repo.list_by_phase_id(phase_id=resolved_phase.id)
        case_players = await self._case_player_repo.list_by_case_id(case_id=case.id)
        players_by_seat_no = {player.seat_no: player for player in case_players}

        damaged_seat_no, fail_reason = resolve_red_vote(
            actions_by_actor_id={
                action.actor_player_id: action.night_target_seat_no for action in actions
            },
            player_id_to_team={player.id: player.team for player in case_players},
        )
        if damaged_seat_no is not None:
            players_by_seat_no[damaged_seat_no].life_left -= 1

        next_phase = Phase(
            case_id=case.id,
            round_no=case.current_round_no,
            seq_in_round=resolved_phase.seq_in_round + 1,
            phase_type=PhaseType.DISCUSS,
        )
        self._db.add(next_phase)
        await self._db.flush()

        room_members = await self._room_member_repo.get_active_members_by_room_id(
            room_id=case.room_id
        )
        user_id_to_username = {member.user_id: member.username for member in room_members}

        snapshot = self._build_phase_snapshot(
            case=case,
            phase=resolved_phase,
            case_players=case_players,
            user_id_to_username=user_id_to_username,
            night_phase_result=NightPhaseResult(
                player_damaged=damaged_seat_no,
                fail_reason=fail_reason,
            ),
            blue_vote_init_result=None,
            vote_phase_result=None,
            round_end_result=None,
        )
        snapshot_no = await self._persist_snapshot(case_id=case.id, snapshot=snapshot)

        try:
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            raise
        try:
            await self._emit_snapshot(
                case_id=case.id, phase_id=resolved_phase.id, snapshot_no=snapshot_no
            )
        except Exception:
            logger.exception(
                "Failed to publish resolved night snapshot event",
                extra={"case_id": str(case.id), "phase_id": str(resolved_phase.id)},
            )
