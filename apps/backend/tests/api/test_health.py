import pytest


@pytest.mark.basic
@pytest.mark.asyncio
async def test_health(client, fake_redis):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
