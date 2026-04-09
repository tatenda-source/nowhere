import asyncpg
from typing import Optional
from uuid import UUID


async def create_postgres_pool(dsn: str):
    pool = await asyncpg.create_pool(dsn)
    return pool


class PostgresVenueRepo:
    def __init__(self, pool):
        self.pool = pool

    async def get(self, venue_id: UUID) -> Optional[dict]:
        row = await self.pool.fetchrow("SELECT id, name, metadata FROM venues WHERE id=$1", str(venue_id))
        return dict(row) if row else None

    async def save(self, venue: dict):
        # minimal upsert example
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO venues (id, name, metadata) VALUES ($1,$2,$3) ON CONFLICT (id) DO UPDATE SET name=$2, metadata=$3", venue["id"], venue["name"], venue.get("metadata", {}))
