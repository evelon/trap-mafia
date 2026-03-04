# app/infra/pubsub/deps.py
from typing import Annotated

from fastapi import Depends

from app.infra.pubsub.base import PubSub
from app.infra.redis.pubsub import RedisPubSubDep


def get_pubsub(redis_pubsub: RedisPubSubDep) -> PubSub:
    return redis_pubsub


PubSubDep = Annotated[PubSub, Depends(get_pubsub)]
