

class UnitOfWork:
    """A thin UnitOfWork that groups redis + postgres operations.

    This is intentionally simple: Redis operations are executed immediately, Postgres
    operations can be executed in a transaction via a provided pool connection.
    """

    def __init__(self, redis, pg):
        self.redis = redis
        self.pg = pg
        self._conn = None

    async def __aenter__(self):
        if self.pg:
            self._conn = await self.pg.acquire()
            await self._conn.execute("BEGIN")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._conn:
            if exc:
                await self._conn.execute("ROLLBACK")
            else:
                await self._conn.execute("COMMIT")
            await self.pg.release(self._conn)
