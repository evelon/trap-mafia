from app.schemas.room.sse_response import RoomStateEnvelope
from app.schemas.sse.response import SSEEventType


def build_sse_frame(*, event: SSEEventType, data: str, id_: int | None = None) -> str:
    """SSE 프레임을 생성합니다.

    - data는 한 줄 JSON으로 넣습니다(줄바꿈이 있으면 data:가 여러 줄로 쪼개져야 함).
    - optinal field인 retry는 사용하지 않습니다.
    """

    lines: list[str] = [f"event: {event.value}"]
    if id_ is not None:
        lines.append(f"id: {id_}")

    lines.append(f"data: {data}")
    return "\n".join(lines) + "\n\n"


def build_envelope_sse_frame(
    *, event: SSEEventType, data: RoomStateEnvelope, id_: int | None = None
) -> str:
    payload = data.model_dump_json(ensure_ascii=False)
    return build_sse_frame(event=event, data=payload, id_=id_)
