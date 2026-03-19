from datetime import datetime, timezone
from math import log1p
from .intent import Intent


def calculate_score(
    intent: Intent,
    dist_km: float,
    radius_km: float = 1.0,
    now: datetime = None,
    w_dist: float = 1.0,
    w_fresh: float = 2.0,
    w_pop: float = 0.5,
    decay_seconds: int = 86400,
) -> float:
    """
    Calculates Liveness Score based on Distance, Freshness (Time Decay), and Popularity.
    Weights and decay window are configurable.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # 1. Distance Score (0 to 1, 1 is closest)
    dist_score = max(0, 1.0 - (dist_km / radius_km))

    # 2. Freshness Score (Decay over configured window)
    created_at = intent.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    age_seconds = (now - created_at).total_seconds()
    freshness_score = max(0, 1.0 - (age_seconds / decay_seconds))

    # 3. Popularity Score (Logarithmic)
    pop_score = log1p(intent.join_count)

    return (w_dist * dist_score) + (w_fresh * freshness_score) + (w_pop * pop_score)
