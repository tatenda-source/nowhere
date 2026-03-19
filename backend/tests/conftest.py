import pytest
import httpx
from httpx import ASGITransport


@pytest.fixture(scope="session")
def app():
    from backend.main import app as _app
    return _app


@pytest.fixture
async def async_client(app):
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
