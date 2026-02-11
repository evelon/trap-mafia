from enum import Enum
from uuid import UUID

from pydantic import Field

from app.schemas.common.envelope import Envelope
from app.schemas.common.mutation import BaseMutation, Subject, Target


class JoinRoomCode(str, Enum):
    OK = "OK"


class JoinRoomReason(str, Enum):
    JOINED = "JOINED"
    ALREADY_JOINED = "ALREADY_JOINED"


class JoinRoomMutation(BaseMutation[JoinRoomReason, None]):
    """
    POST /api/rooms/{room_id}/join 성공(200) 시 반환되는 mutation 데이터.

    의미:
    - 현재 사용자가 특정 ROOM에 참가를 시도한 결과를 나타낸다.
    - 이미 참가 중인 경우에도 200으로 응답하며, changed=False로 표현한다.

    필드 해석:
    - target == ROOM
    - subject == ME
    - subject_id == None
    - on_target == True (요청 이후 항상 방에 속한 상태)
    - changed: 실제로 참가 상태가 변경되었는지 여부
    - reason: JOINED | ALREADY_JOINED
    """

    target: Target = Field(
        default=Target.ROOM,
        frozen=True,
        json_schema_extra={"const": Target.ROOM},
    )
    subject: Subject = Field(
        default=Subject.ME,
        frozen=True,
        json_schema_extra={"const": Subject.ME},
    )
    subject_id: None = Field(
        default=None,
        frozen=True,
        description="Always null for subject=ME.",
    )
    on_target: bool = Field(
        default=True,
        frozen=True,
        json_schema_extra={"const": True},
        description="Always true for join_room mutation.",
    )
    changed: bool = Field(
        description="Whether the room membership actually changed by this request.",
        examples=[True, False],
    )
    reason: JoinRoomReason = Field(
        description='Reason string ("JOINED" | "ALREADY_JOINED").',
        examples=["JOINED"],
    )


JoinRoomResponse = Envelope[JoinRoomMutation, JoinRoomCode]


class LeaveRoomCode(str, Enum):
    OK = "OK"


class LeaveRoomReason(str, Enum):
    LEFT = "LEFT"
    ALREADY_LEFT = "ALREADY_LEFT"


class LeaveRoomMutation(BaseMutation[LeaveRoomReason, None]):
    """
    POST /api/rooms/current/leave 성공(200) 시 반환되는 mutation 데이터.

    의미:
    - 현재 사용자가 ROOM에서 나가기를 시도한 결과를 나타낸다.
    - 이미 방에 속해 있지 않은 경우에도 200으로 응답하며, changed=False로 표현한다.

    필드 해석:
    - target == ROOM
    - subject == ME
    - subject_id == None
    - on_target == False (요청 이후 항상 방에 속하지 않은 상태)
    - changed: 실제로 멤버십이 변경되었는지 여부
    - reason: LEFT | ALREADY_LEFT
    """

    target: Target = Field(
        default=Target.ROOM,
        frozen=True,
        json_schema_extra={"const": Target.ROOM},
    )
    subject: Subject = Field(
        default=Subject.ME,
        frozen=True,
        json_schema_extra={"const": Subject.ME},
    )
    subject_id: None = Field(
        default=None,
        frozen=True,
        description="Always null for subject=ME.",
    )
    on_target: bool = Field(
        default=False,
        frozen=True,
        json_schema_extra={"const": False},
        description="Always false for leave_room mutation.",
    )
    changed: bool = Field(
        description="Whether the room membership actually changed by this request.",
        examples=[True, False],
    )
    reason: LeaveRoomReason = Field(
        description='Reason string ("LEFT" | "ALREADY_LEFT").',
        examples=["LEFT"],
    )


LeaveRoomResponse = Envelope[LeaveRoomMutation, LeaveRoomCode]


class KickUserCode(str, Enum):
    OK = "OK"


class KickUserReason(str, Enum):
    KICKED = "KICKED"
    NOT_IN_ROOM = "NOT_IN_ROOM"


class KickUserMutation(BaseMutation[KickUserReason, UUID]):
    """
    POST /api/rooms/current/users/{user_id}/kick 성공(200) 시 반환되는 mutation 데이터.

    의미:
    - 특정 USER를 현재 ROOM에서 내보내기를 시도한 결과를 나타낸다.
    - 대상이 해당 ROOM에 없더라도 200으로 응답하며, changed=False로 표현한다.
    - 이 mutation은 대상 room에서 실제 멤버십이 제거되었는지만 보장한다.
      대상 유저의 다른 room 소속 여부는 반환하지 않는다.

    필드 해석:
    - target == ROOM
    - subject == USER
    - subject_id: 대상 USER의 식별자(UUID)
    - on_target == False (요청 이후 대상은 해당 ROOM에 속하지 않음)
    - changed: 실제로 멤버십이 제거되었는지 여부
    - reason: KICKED | NOT_IN_ROOM
    """

    target: Target = Field(
        default=Target.ROOM,
        frozen=True,
        json_schema_extra={"const": Target.ROOM},
    )
    subject: Subject = Field(
        default=Subject.USER,
        frozen=True,
        json_schema_extra={"const": Subject.USER},
    )
    subject_id: UUID = Field(
        description="Target user's id.",
        examples=["00000000-0000-0000-0000-000000000000"],
    )
    on_target: bool = Field(
        default=False,
        frozen=True,
        json_schema_extra={"const": False},
        description="Always false for kick_user mutation.",
    )
    changed: bool = Field(
        description="Whether the room membership actually changed by this request.",
        examples=[True, False],
    )
    reason: KickUserReason = Field(
        description='Reason string ("KICKED" | "NOT_IN_ROOM").',
        examples=["KICKED"],
    )


KickUserResponse = Envelope[KickUserMutation, KickUserCode]


class CaseStartSuccessCode(str, Enum):
    OK = "OK"


class CaseStartForbiddenCode(str, Enum):
    PERMISSION_DENIED_NOT_IN_ROOM = "PERMISSION_DENIED_NOT_IN_ROOM"
    PERMISSION_DENIED_NOT_HOST = "PERMISSION_DENIED_NOT_HOST"


class CaseStartConflictCode(str, Enum):
    ROOM_CASE_RUNNING = "ROOM_CASE_RUNNING"
    ROOM_NOT_ENOUGH_PLAYERS = "ROOM_NOT_ENOUGH_PLAYERS"
    ROOM_NOT_ALL_READY = "ROOM_NOT_ALL_READY"
    ROOM_DELETED = "ROOM_DELETED"


class CaseStartReason(str, Enum):
    STARTED = "STARTED"


class CaseStartMutation(BaseMutation[CaseStartReason, None]):
    """
    POST /api/rooms/current/case-start 성공(200) 시 반환되는 mutation 데이터.

    의미:
    - 현재 사용자가 ROOM에서 case 시작을 시도한 "성공 결과"를 나타낸다.
    - 권한/조건 불충족으로 시작에 실패한 경우는 403/409로 분리되며, body의 data는 null이다.

    필드 해석:
    - target == ROOM
    - subject == ME
    - subject_id == None
    - on_target == True (요청 이후 room에 case가 존재)
    - changed == True (요청으로 인해 실제로 case 시작이 발생)
    - reason == STARTED
    """

    target: Target = Field(
        default=Target.ROOM,
        frozen=True,
        json_schema_extra={"const": Target.ROOM},
    )
    subject: Subject = Field(
        default=Subject.ME,
        frozen=True,
        json_schema_extra={"const": Subject.ME},
    )
    subject_id: None = Field(
        default=None,
        frozen=True,
        description="Always null for subject=ME.",
    )
    on_target: bool = Field(
        default=True,
        frozen=True,
        json_schema_extra={"const": True},
        description="Always true for case_start success mutation.",
    )
    changed: bool = Field(
        default=True,
        frozen=True,
        json_schema_extra={"const": True},
        description="Always true for case_start success mutation.",
    )
    reason: CaseStartReason = Field(
        default=CaseStartReason.STARTED,
        frozen=True,
        json_schema_extra={"const": CaseStartReason.STARTED},
        description='Reason string ("STARTED").',
        examples=["STARTED"],
    )


CaseStartSuccessResponse = Envelope[CaseStartMutation, CaseStartSuccessCode]
CaseStartForbiddenResponse = Envelope[None, CaseStartForbiddenCode]
CaseStartConflictResponse = Envelope[None, CaseStartConflictCode]
