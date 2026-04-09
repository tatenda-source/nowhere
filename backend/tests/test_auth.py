import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from backend.main import app, lifespan


@pytest.fixture(autouse=True)
async def manage_redis():
    async with lifespan(app):
        yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_auth_flow(client: AsyncClient):
    # First request — no cookie
    response = await client.get("/health")
    assert response.status_code == 200
    assert "user_id" in response.cookies


@pytest.mark.asyncio
async def test_header_identity_precedence(client: AsyncClient):
    """X-Nowhere-Identity header should be accepted."""
    custom_id = str(uuid.uuid4())

    response = await client.post(
        "/intents/",
        json={
            "title": "Header Test",
            "emoji": "🧪",
            "latitude": 40.7128,
            "longitude": -74.0060,
        },
        headers={"X-Nowhere-Identity": custom_id},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_join_and_message_flow(client: AsyncClient):
    # Get identity cookie
    res = await client.get("/health")
    cookies = res.cookies

    # Create Intent
    payload = {"title": "Test Chat", "emoji": "🧪", "latitude": 10.0, "longitude": 10.0}
    res = await client.post("/intents/", json=payload, cookies=cookies)
    assert res.status_code == 201
    intent_id = res.json()["id"]

    # Message without joining should fail
    msg = {"user_id": str(uuid.uuid4()), "content": "Hello"}
    res = await client.post(f"/intents/{intent_id}/messages", json=msg, cookies=cookies)
    assert res.status_code == 403

    # Join
    res = await client.post(f"/intents/{intent_id}/join", cookies=cookies)
    assert res.status_code == 200
    assert res.json()["joined"] is True

    # Message after joining should succeed
    msg = {"user_id": str(uuid.uuid4()), "content": "Hello World"}
    res = await client.post(f"/intents/{intent_id}/messages", json=msg, cookies=cookies)
    assert res.status_code == 200
