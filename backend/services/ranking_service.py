from datetime import datetime, timezone
from backend.core.models.intent import Intent
from backend.core.models.ranking import calculate_score
from backend.config import Settings


class RankingService:
    """Ranks intents by composite score using configurable weights."""

    def __init__(self, settings: Settings):
        self.w_dist = settings.RANKING_W_DIST
        self.w_fresh = settings.RANKING_W_FRESH
        self.w_pop = settings.RANKING_W_POP
        self.decay_seconds = settings.RANKING_DECAY_SECONDS

    def rank(
        self,
        intents: list[tuple[Intent, float]],
        radius_km: float,
        limit: int,
    ) -> list[Intent]:
        """
        Rank intents by score.
        :param intents: list of (intent, distance_km) tuples
        :param radius_km: search radius for distance normalization
        :param limit: max results to return
        """
        now = datetime.now(timezone.utc)
        scored = []

        for intent, dist_km in intents:
            score = calculate_score(
                intent,
                dist_km,
                radius_km,
                now,
                w_dist=self.w_dist,
                w_fresh=self.w_fresh,
                w_pop=self.w_pop,
                decay_seconds=self.decay_seconds,
            )
            scored.append((score, intent))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]
