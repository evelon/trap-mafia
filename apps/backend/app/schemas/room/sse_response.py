from app.schemas.common.envelope import Envelope
from app.schemas.room.state import RoomSnapshot
from app.schemas.sse.response import SSEEnvelopeCode

RoomStateEnvelope = Envelope[RoomSnapshot, SSEEnvelopeCode]
