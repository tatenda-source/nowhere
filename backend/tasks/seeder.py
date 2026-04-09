from random import uniform, choice
from uuid import uuid4
from datetime import datetime, timezone
from ..core.models.intent import Intent
from ..infra.persistence.intent_repo import IntentRepository
import logging

logger = logging.getLogger(__name__)

AMBIENT_VIBES = [
    {"emoji": "☕️", "title": "Anyone for coffee?", "desc": "Grab a quick coffee at the corner?"},
    {"emoji": "🚶", "title": "Evening walk?", "desc": "Walking around the block, care to join?"},
    {"emoji": "🏀", "title": "Hoops?", "desc": "Shooting some hoops nearby."},
    {"emoji": "📚", "title": "Study session", "desc": "Focus mode at the library."},
    {"emoji": "🍕", "title": "Pizza slice", "desc": "Grabbing a quick bite."},
    {"emoji": "🎸", "title": "Jamming", "desc": "Acoustic jam in the park."},
]

async def seed_ambient_intents(
    repo: IntentRepository, 
    lat: float, 
    lon: float, 
    count: int = 3, 
    radius_km: float = 0.5
) -> list[Intent]:
    """
    Seeds 'count' random ambient intents around (lat, lon) within 'radius_km'.
    """
    logger.info(f"Seeding {count} ambient intents around {lat}, {lon}")
    
    seeded = []
    
    for _ in range(count):
        # Random offset
        # Approx: 1 deg lat ~ 111km. 1 deg lon ~ 111km * cos(lat)
        # For simplicity, 0.01 deg is roughly 1km.
        # radius_km = 0.5 -> 0.005 deg roughly
        
        offset = radius_km / 111.0 
        r_lat = lat + uniform(-offset, offset)
        r_lon = lon + uniform(-offset, offset)
        
        vibe = choice(AMBIENT_VIBES)
        
        intent = Intent(
            id=uuid4(),
            user_id="system_seeder",
            title=vibe["title"],
            description=vibe["desc"],
            emoji=vibe["emoji"],
            latitude=r_lat,
            longitude=r_lon,
            created_at=datetime.now(timezone.utc),
            is_system=True,
            flags=0
        )
        
        await repo.save_intent(intent)
        seeded.append(intent)
        
    logger.info(f"Successfully seeded {len(seeded)} intents.")
    return seeded
