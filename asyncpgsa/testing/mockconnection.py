from asyncio import Queue

from .mockpreparedstmt import MockPreparedStatement


class MockConnection:
    def __init__(self):
        self.results = Queue()
        self.completed_queries = []

    async def general_query(self, query, *args, **kwargs):
        self.completed_queries.append((query, *args, kwargs))
        return self.results.get_nowait()

    execute = fetch = fetchval = fetchrow = general_query

    async def prepare(self, query, *, timeout=None):
        return MockPreparedStatement(self, query, None)

    async def close(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def __await__(self):
        async def get_conn():
            return self
        return get_conn()
