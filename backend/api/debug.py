from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..infra.persistence.intent_repo import IntentRepository
from ..api.deps import get_intent_repo
from ..tasks.seeder import seed_ambient_intents

router = APIRouter()

class DebugSeedRequest(BaseModel):
    latitude: float
    longitude: float
    count: int = 3
    radius_km: float = 0.5

@router.post("/seed")
async def seed_intents(
    request: DebugSeedRequest,
    repo: IntentRepository = Depends(get_intent_repo)
):
    """
    Debug endpoint to manually trigger ambient intent seeding.
    """
    seeded = await seed_ambient_intents(
        repo=repo,
        lat=request.latitude,
        lon=request.longitude,
        count=request.count,
        radius_km=request.radius_km
    )
    return seeded
