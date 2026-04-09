import pytest
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
async def test_create_and_find_nearby_intent(client: AsyncClient):
    lat, lon = 40.7128, -74.0060
    payload = {
        "title": "Coffee run",
        "emoji": "☕",
        "latitude": lat,
        "longitude": lon,
    }
    response = await client.post("/intents/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Coffee run"
    intent_id = data["id"]

    # Find nearby
    response = await client.get(f"/intents/nearby?lat={lat}&lon={lon}")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0
    found = any(i["id"] == intent_id for i in data["intents"])
    assert found


@pytest.mark.asyncio
async def test_empty_state(client: AsyncClient):
    response = await client.get("/intents/nearby?lat=0&lon=0")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["message"] is not None
