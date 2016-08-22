from asyncio import Queue

from asyncpgsa import compile_query
from .mockpreparedstmt import MockPreparedStatement


class MockConnection:
    def __init__(self):
        self.results = Queue()
        self.completed_queries = []

    async def general_query(self, query, *args, **kwargs):
        self.completed_queries.append((query, *args, kwargs))
        return self.results.get_nowait()

    def __getattr__(self, item):
        if item in ('execute', 'fetch', 'fetchval', 'fetchrow'):
            return self.general_query

        raise Exception('Sorry, {} doesnt exist yet. '
                        'Consider making a PR.'.format(item))

    async def __aenter__(self):
        return self

    async def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    async def prepare(self, query, *, timeout=None):
        return MockPreparedStatement(self, query, None)
