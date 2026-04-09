import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from backend.services.intent_service import IntentService
from backend.core.exceptions import DomainError
from backend.core.clock import Clock

@pytest.fixture
def mock_intent_repo():
    repo = AsyncMock()
    repo.save_intent = AsyncMock()
    repo.find_nearby = AsyncMock(return_value=[])
    repo.get_clusters = AsyncMock(return_value=[])
    repo.flag_intent = AsyncMock(return_value=1)
    return repo

@pytest.fixture
def mock_join_repo():
    repo = AsyncMock()
    repo.save_join = AsyncMock(return_value=True)
    repo.is_member = AsyncMock(return_value=True)
    return repo

@pytest.fixture
def mock_message_repo():
    repo = AsyncMock()
    repo.save_message = AsyncMock()
    return repo

@pytest.fixture
def mock_metrics_repo():
    repo = AsyncMock()
    return repo

@pytest.fixture
def mock_spam_detector():
    detector = AsyncMock()
    detector.check = AsyncMock() # Should not raise
    return detector

@pytest.fixture
def mock_clock():
    clock = MagicMock(spec=Clock)
    from datetime import datetime, timezone
    clock.now = MagicMock(return_value=datetime.now(timezone.utc))
    return clock

@pytest.fixture
def service(mock_intent_repo, mock_join_repo, mock_message_repo, mock_metrics_repo, mock_spam_detector, mock_clock):
    return IntentService(
        intent_repo=mock_intent_repo,
        join_repo=mock_join_repo,
        message_repo=mock_message_repo,
        metrics_repo=mock_metrics_repo,
        spam_detector=mock_spam_detector,
        clock=mock_clock
    )

@pytest.mark.asyncio
async def test_create_intent(service, mock_intent_repo, mock_metrics_repo, mock_spam_detector):
    user_id = str(uuid.uuid4())
    await service.create_intent(
        title="New Intent",
        emoji="🚀",
        latitude=40.0,
        longitude=-74.0,
        user_id=user_id
    )
    
    # Verify spam check called
    mock_spam_detector.check.assert_awaited_with("New Intent", user_id)
    
    # Verify repo save called
    mock_intent_repo.save_intent.assert_awaited()
    saved_intent = mock_intent_repo.save_intent.call_args[0][0]
    assert saved_intent.title == "New Intent"
    assert saved_intent.user_id == user_id
    
    # Verify metrics
    mock_metrics_repo.log_intent_creation.assert_awaited()

@pytest.mark.asyncio
async def test_join_intent(service, mock_join_repo, mock_metrics_repo):
    intent_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    res = await service.join_intent(intent_id, user_id)
    
    assert res["joined"] is True
    assert res["intent_id"] == intent_id
    
    mock_join_repo.save_join.assert_awaited_with(intent_id, user_id)
    mock_metrics_repo.log_join.assert_awaited()

@pytest.mark.asyncio
async def test_post_message_success(service, mock_message_repo, mock_metrics_repo):
    intent_id = uuid.uuid4()
    user_id = uuid.uuid4()
    content = "Hello World"
    
    msg = await service.post_message(intent_id, user_id, content)
    
    assert msg.content == content
    assert msg.intent_id == intent_id
    
    mock_message_repo.save_message.assert_awaited()
    mock_metrics_repo.log_message.assert_awaited()

@pytest.mark.asyncio
async def test_post_message_not_joined(service, mock_join_repo):
    intent_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    # Simulate not joined
    mock_join_repo.is_member = AsyncMock(return_value=False)
    
    with pytest.raises(DomainError, match="Must join"):
        await service.post_message(intent_id, user_id, "Hello")
