from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.config import JwtConfig, get_jwt_config
from app.repositories.user import UserRepo
from app.services.auth import get_auth_service


@pytest.fixture
def jwt_test_config(app):
    cfg = JwtConfig(
        issuer="trap-mafia-test",
        audience="trap-mafia-test",
        access_ttl=timedelta(minutes=5),
        refresh_ttl=timedelta(days=7),
        algorithm="HS256",
        secret_key="valid-test-token-valid-test-token-valid-test-token-valid-test-token",
        public_key=None,
    )
    app.dependency_overrides[get_jwt_config] = lambda: cfg
    yield cfg
    app.dependency_overrides.pop(get_jwt_config, None)


@pytest.fixture
def auth_service(db_session):
    user_repo = UserRepo(db_session)
    return get_auth_service(db_session, user_repo)
