

class MockPreparedStatement:
    def __init__(self, connection, query, state):
        self._connection = connection
        self._query = query
        self._state = state

    def cursor(self, *args, **kwargs):
        return self._connection.results.get_nowait()

    def __getattr__(self, item):
        raise NotImplementedError('Sorry, this doesnt exist yet. '
                                  'Consider making a PR.')

