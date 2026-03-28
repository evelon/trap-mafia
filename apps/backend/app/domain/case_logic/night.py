from __future__ import annotations

from enum import Enum
from uuid import UUID


class NightRuleViolationReason(str, Enum):
    NOT_NIGHT_PHASE = "NOT_NIGHT_PHASE"
    NOT_ALIVE = "NOT_ALIVE"
    ALREADY_ACTED = "ALREADY_ACTED"
    INVALID_TARGET_SEAT = "INVALID_TARGET_SEAT"
    SELF_VOTE = "SELF_VOTE"


class NightRuleViolationError(ValueError):
    def __init__(self, reason: NightRuleViolationReason, message: str | None = None) -> None:
        super().__init__(message)
        self.reason = reason


def validate_red_vote(
    *,
    is_night_phase: bool,
    actor_player_id: UUID,
    alive_player_ids: set[UUID],
    target_seat_no: int | None,
    actor_seat_no: int,
    max_seat_no: int,
    already_acted: bool,
) -> None:
    """
    NIGHT phase에서 red vote / skip 입력이 유효한지 검증한다.

    Parameters
    ----------
    is_night_phase:
        현재 phase가 NIGHT인지 여부.
    actor_player_id:
        행동한 플레이어의 case_player id.
    alive_player_ids:
        현재 생존 중인 case_player id 집합.
    target_seat_no:
        투표 대상 seat 번호. None이면 skip으로 간주한다.
    actor_seat_no:
        행동한 플레이어 자신의 seat 번호.
    max_seat_no:
        허용 가능한 seat 번호의 upper bound(exclusive).
    already_acted:
        현재 NIGHT phase에서 이미 의사 표시를 마쳤는지 여부.

    Raises
    ------
    NightRuleViolationError
        현재 phase가 NIGHT가 아니거나, actor가 생존 상태가 아니거나,
        이미 행동을 마쳤거나, target seat이 유효하지 않거나,
        self vote인 경우 발생한다.
    """
    if not is_night_phase:
        raise NightRuleViolationError(reason=NightRuleViolationReason.NOT_NIGHT_PHASE)

    if actor_player_id not in alive_player_ids:
        raise NightRuleViolationError(reason=NightRuleViolationReason.NOT_ALIVE)

    if already_acted:
        raise NightRuleViolationError(reason=NightRuleViolationReason.ALREADY_ACTED)

    # target_seat_no is None -> skip
    if target_seat_no is None:
        return

    if target_seat_no < 0 or target_seat_no >= max_seat_no:
        raise NightRuleViolationError(reason=NightRuleViolationReason.INVALID_TARGET_SEAT)

    if target_seat_no == actor_seat_no:
        raise NightRuleViolationError(reason=NightRuleViolationReason.SELF_VOTE)


def should_end_night(
    *,
    alive_player_count: int,
    action_count: int,
) -> bool:
    """
    NIGHT phase 종료 여부를 판정한다.

    MVP 규칙에서는 모든 플레이어가 red vote 또는 skip으로
    의사 표시를 마치면 NIGHT가 종료된다.

    Parameters
    ----------
    total_player_count:
        현재 NIGHT phase에서 의사 표시 대상이 되는 전체 플레이어 수.
    action_count:
        현재 NIGHT phase에 기록된 action 수.

    Returns
    -------
    bool
        모든 플레이어가 의사 표시를 마쳤으면 True, 아니면 False.
    """
    return action_count >= alive_player_count
