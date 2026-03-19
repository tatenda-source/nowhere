from typing import List
from ..core.models.intent import Intent
from ..core.interfaces.repositories import IntentRepository
from .ranking_service import RankingService
from .clustering_service import ClusteringService


class IntentQueryService:
    """Handles read-only queries for intents (CQRS pattern)."""

    def __init__(self, intent_repo: IntentRepository, ranking_service: RankingService):
        self.intent_repo = intent_repo
        self.ranking_service = ranking_service

    async def get_nearby(
        self,
        lat: float,
        lon: float,
        radius: float = 1.0,
        limit: int = 50,
    ) -> List[Intent]:
        """Get intents near a location, ranked by composite score."""
        pairs = await self.intent_repo.find_nearby(lat, lon, radius, limit)
        return self.ranking_service.rank(pairs, radius, limit)

    async def get_clusters(
        self,
        lat: float,
        lon: float,
        radius: float = 10.0,
        zoom: int | None = None,
    ) -> dict:
        """Get clustered view of intents in an area."""
        points = await self.intent_repo.get_geo_points(lat, lon, radius)
        clusters = ClusteringService.cluster(points, radius, zoom=zoom)
        return {"clusters": clusters}
