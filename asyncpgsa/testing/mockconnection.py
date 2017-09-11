from asyncio import Queue

from asyncpg.connection import Connection

from .mockpreparedstmt import MockPreparedStatement

results = Queue()
completed_queries = []


class MockConnection:
    __slots__ = Connection.__slots__

    @property
    def completed_queries(self):
        return completed_queries

    @property
    def results(self):
        return results

    @results.setter
    def results(self, result):
        global results
        results = result

    async def general_query(self, query, *args, **kwargs):
        completed_queries.append((query, *args, kwargs))
        return results.get_nowait()

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
