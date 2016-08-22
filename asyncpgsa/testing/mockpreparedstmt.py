

class MockPreparedStatement:
    def __init__(self, connection, query, state):
        self._connection = connection
        self._query = query
        self._state = state

    def cursor(self, *args, **kwargs):
        return MockCursor(self._connection.results.get_nowait())

    def __getattr__(self, item):
        raise NotImplementedError('Sorry, this doesnt exist yet. '
                                  'Consider making a PR.')


class MockCursor:
    def __init__(self, list):
        self.iterator = iter(list)

    async def __aiter__(self):
        return self

    async def __anext__(self):
        return next(list)



