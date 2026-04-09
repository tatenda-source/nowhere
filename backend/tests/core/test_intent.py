import pytest
from backend.core.models.intent import Intent
from backend.core.exceptions import InvalidAction
from backend.core.clock import FixedClock
from datetime import datetime, timezone

# Fixed clock for deterministic testing
FIXED_TIME = datetime(2026, 1, 21, 0, 0, 0, tzinfo=timezone.utc)
clock = FixedClock(FIXED_TIME)

def test_intent_creation_valid():
    intent = Intent(
        title="Coffee time",
        emoji="☕",
        latitude=40.7,
        longitude=-74.0,
        user_id="user1",
        created_at=clock.now()
    )
    assert intent.title == "Coffee time"
    assert intent.flags == 0
    assert intent.join_count == 0
    assert intent.created_at == FIXED_TIME

def test_intent_creation_invalid_title():
    with pytest.raises(ValueError, match="Title cannot be empty"):
        Intent(
            title="   ",
            emoji="☕",
            latitude=40.7,
            longitude=-74.0,
            created_at=clock.now()
        )

def test_intent_creation_invalid_emoji():
    with pytest.raises(ValueError, match="Emoji must be a single emoji character"):
        Intent(
            title="Valid",
            emoji="TooLong",
            latitude=40.7,
            longitude=-74.0,
            created_at=clock.now()
        )

def test_intent_flag():
    intent = Intent(
        title="Test",
        emoji="T",
        latitude=10.0,
        longitude=10.0,
        created_at=clock.now()
    )
    assert intent.flags == 0
    
    flagged = intent.flag()
    assert flagged.flags == 1
    assert intent.flags == 0 # Immutability check

def test_intent_with_join_count():
    intent = Intent(
        title="Test",
        emoji="T",
        latitude=10.0,
        longitude=10.0,
        created_at=clock.now()
    )
    assert intent.join_count == 0
    
    joined = intent.with_join_count(5)
    assert joined.join_count == 5
    assert intent.join_count == 0
    
    with pytest.raises(InvalidAction):
        intent.with_join_count(-1)

def test_is_visible():
    # System intent always visible
    sys_intent = Intent(
        title="Sys", 
        emoji="🤖", 
        latitude=0.0, 
        longitude=0.0, 
        is_system=True, 
        join_count=0,
        created_at=clock.now()
    )
    assert sys_intent.is_visible(100.0) is True
    
    # User intent, 0 joins -> restricted visibility
    intent = Intent(
        title="Test",
        emoji="T",
        latitude=0,
        longitude=0,
        join_count=0,
        created_at=clock.now()
    )
    assert intent.is_visible(0.1) is True # < 200m
    assert intent.is_visible(0.3) is False # > 200m
    
    # User intent, >0 joins -> visible
    popular = intent.with_join_count(1)
    assert popular.is_visible(10.0) is True
