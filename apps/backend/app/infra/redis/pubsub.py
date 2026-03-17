from typing import Annotated, AsyncIterator

from fastapi import Depends
from redis.asyncio import Redis

from app.infra.pubsub.topics import ConnTopic, RoomTopic, Topic, UserTopic
from app.infra.pubsub.transport.base import PubSub
from app.infra.redis.client import RedisClientDep


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

    def subscribe(self, topic: Topic) -> AsyncIterator[str]:
        async def _gen() -> AsyncIterator[str]:
            channel = self._topic_to_channel(topic)
            pubsub = self._client.pubsub()

            try:
                await pubsub.subscribe(channel)

                async for message in pubsub.listen():
                    if message.get("type") != "message":
                        continue
                    msg = message.get("data")

                    if isinstance(msg, bytes):
                        msg = msg.decode()

                    assert isinstance(msg, str)

                    yield msg
            finally:
                try:
                    await pubsub.unsubscribe(channel)
                finally:
                    await pubsub.close()

        return _gen()

    async def publish(self, topic: Topic, message: str) -> int:
        channel = self._topic_to_channel(topic)
        check = await self._client.publish(channel, message)
        return check


def get_redis_pubsub(redis_client: RedisClientDep) -> RedisPubSub:
    return RedisPubSub(redis_client)


RedisPubSubDep = Annotated[RedisPubSub, Depends(get_redis_pubsub)]
