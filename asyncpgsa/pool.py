from asyncpg.pool import Pool

from .transactionmanager import ConnectionTransactionContextManager
from .connection import SAConnection


class SAPool(Pool):
    async def _new_connection(self, timeout=None):
        con = await super()._new_connection()
        self._connections.remove(con)
        con = SAConnection.from_connection(con)
        self._connections.add(con)
        return con

    def transaction(self, **kwargs):
        return ConnectionTransactionContextManager(self, **kwargs)

    def begin(self, **kwargs):
        """ an alias for self.transaction() """
        return self.transaction(**kwargs)


def create_pool(dsn=None, *,
                min_size=10,
                max_size=10,
                max_queries=50000,
                setup=None,
                init=None,
                loop=None,
                **connect_kwargs):
    r"""Create a connection pool.

    Can be used either with an ``async with`` block:

    .. code-block:: python

        async with asyncpgsa.create_pool(user='postgres',
                                       command_timeout=60) as pool:
            async with poll.acquire() as con:
                await con.fetch('SELECT 1')

    Or directly with ``await``:

    .. code-block:: python

        pool = await asyncpgsa.create_pool(user='postgres', command_timeout=60)
        con = await poll.acquire()
        try:
            await con.fetch('SELECT 1')
        finally:
            await pool.release(con)

    :param str dsn: Connection arguments specified using as a single string in
                    the following format:
                    ``postgres://user:pass@host:port/database?option=value``.

    :param \*\*connect_kwargs: Keyword arguments for the
                               :func:`~asyncpg.connection.connect` function.
    :param int min_size: Number of connection the pool will be initialized
                         with.
    :param int max_size: Max number of connections in the pool.
    :param int max_queries: Number of queries after a connection is closed
                            and replaced with a new connection.
    :param coroutine setup: A coroutine to initialize a connection right before
                            it is returned from :meth:`~pool.Pool.acquire`.
                            An example use case would be to automatically
                            set up notifications listeners for all connections
                            of a pool.
    :param coroutine init: A coroutine to initialize a connection
                            when it is created. An example use case would
                            be to setup type codecs with
                            set_builtin_type_codec() or set_type_codec()
    :param loop: An asyncio event loop instance.  If ``None``, the default
                 event loop will be used.
    :return: An instance of :class:`~asyncpg.pool.Pool`.
    """
    return SAPool(dsn,
                  min_size=min_size, max_size=max_size,
                  max_queries=max_queries, loop=loop, setup=setup, init=init,
                  **connect_kwargs)

