from typing import Annotated, AsyncIterator

from fastapi import Depends
from redis.asyncio import Redis

from app.infra.pubsub.base import PubSub
from app.infra.redis.client import RedisClientDep
from app.realtime.topics import ConnTopic, RoomTopic, Topic, UserTopic


class RedisPubSub(PubSub):
    def __init__(self, client: Redis):
        self._client = client

    def _topic_to_channel(self, topic: Topic) -> str:
        if isinstance(topic, RoomTopic):
            return f"room:{topic.room_id}"
        if isinstance(topic, UserTopic):
            return f"user:{topic.user_id}"
        if isinstance(topic, ConnTopic):
            return f"conn:{topic.conn_id}"
        raise TypeError(
            f"Unsupported topic: {type(topic)!r}"
        )  # MVP: 나중엔 UnsupportedTokenError 만들어서 사용.

    async def publish(self, topic: Topic, message: str) -> int:
        channel = self._topic_to_channel(topic)
        return await self._client.publish(channel, message)

    def subscribe(self, topic: Topic) -> AsyncIterator[str]:
        async def _gen() -> AsyncIterator[str]:
            channel = self._topic_to_channel(topic)
            pubsub = self._client.pubsub()

            try:
                await pubsub.subscribe(channel)

                async for message in pubsub.listen():
                    if message.get("type") != "message":
                        continue
                    yield message.get("data")
            finally:
                try:
                    await pubsub.unsubscribe(channel)
                finally:
                    await pubsub.close()

        return _gen()


def get_redis_pubsub(redis_client: RedisClientDep) -> RedisPubSub:
    return RedisPubSub(redis_client)


RedisPubSubDep = Annotated[RedisPubSub, Depends(get_redis_pubsub)]
