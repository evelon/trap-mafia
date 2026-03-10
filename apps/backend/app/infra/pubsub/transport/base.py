from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from app.realtime.topics import Topic


class PubSub(ABC):
    """Transport-independent Pub/Sub interface.

    - Topic: 앱 의미 단위(예: RoomTopic(room_id))
    - message: transport로 흘려보낼 raw payload (보통 JSON str)
    """

    @abstractmethod
    async def publish(self, topic: Topic, message: str) -> int:
        """Publish message to topic.

        Returns:
            int: number of subscribers that received the message (transport-dependent).
        """
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, topic: Topic) -> AsyncIterator[str]:
        """Subscribe to topic and yield messages.

        Yields:
            str: raw payload (usually JSON str).
        """
        raise NotImplementedError
