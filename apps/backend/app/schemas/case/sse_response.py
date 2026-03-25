from app.schemas.case.state import CaseSnapshot
from app.schemas.common.envelope import Envelope
from app.schemas.sse.response import CaseRESTRespType, SSEEnvelopeCode

CaseNotCreatedEnvelope = Envelope[None, CaseRESTRespType]
CaseStateEnvelope = Envelope[CaseSnapshot, SSEEnvelopeCode]
