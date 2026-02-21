from __future__ import annotations

from datetime import timedelta

import pytest
import pytest_asyncio

from app.core.auth import get_jwt_handler
from app.core.config import JwtConfig, get_jwt_config
from app.services.auth import get_auth_service


@pytest.fixture
def jwt_test_cfg(app):
    cfg = JwtConfig(
        issuer="trap-mafia-test",
        audience="trap-mafia-test",
        access_ttl=timedelta(minutes=5),
        refresh_ttl=timedelta(days=7),
        algorithm="HS256",
        secret_key="test-secret",
        public_key=None,
    )
    app.dependency_overrides[get_jwt_config] = lambda: cfg
    yield cfg
    app.dependency_overrides.pop(get_jwt_config, None)


@pytest.fixture
def jwt_test_handler(jwt_test_cfg):
    handler = get_jwt_handler(jwt_test_cfg)
    yield handler


@pytest_asyncio.fixture
async def auth_service(db_session):
    return get_auth_service(db_session)
