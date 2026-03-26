import json
from typing import AsyncIterator

from app.domain.events.case import CaseEventDelta, CaseSnapshotType
from app.infra.pubsub.topics import CaseTopic
from app.infra.pubsub.transport.base import PubSub


class CaseEventBus:
    def __init__(self, pubsub: PubSub):
        self._pubsub = pubsub

    async def publish(self, case_topic: CaseTopic, event: CaseEventDelta) -> None:
        if event.type == CaseSnapshotType.ON_CONNECT:
            raise ValueError("ON_CONNECT must not be published to pubsub")
        payload = event.model_dump(mode="json")
        await self._pubsub.publish(
            case_topic,
            json.dumps(payload, ensure_ascii=False),
        )

    async def subscribe(self, case_topic: CaseTopic) -> AsyncIterator[CaseEventDelta]:
        async for msg in self._pubsub.subscribe(case_topic):
            data = json.loads(msg)
            yield CaseEventDelta.model_validate(data)
