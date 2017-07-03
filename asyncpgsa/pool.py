from collections import ChainMap
import inspect

from asyncpg.pool import Pool, create_pool as _create_pool

from .transactionmanager import ConnectionTransactionContextManager
from .connection import SAConnection


class SAPool(Pool):
    def __init__(self, *args, dialect=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.dialect = dialect

    async def _new_connection(self, timeout=None):
        con = await super()._new_connection()
        self._connections.remove(con)
        con = SAConnection.from_connection(con, dialect=self.dialect)
        self._connections.add(con)
        return con

    def transaction(self, **kwargs):
        return ConnectionTransactionContextManager(self, **kwargs)

    def begin(self, **kwargs):
        """ an alias for self.transaction() """
        return self.transaction(**kwargs)


def create_pool(*args, **kwargs):
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

    All parameters are equivalent to :function:`~asyncpg.pool.create_pool()`.

    :return: An instance of :class:`~asyncpgsa.pool.SAPool`.
    """

    sig = inspect.signature(_create_pool)
    default_kwargs = {p.name: p.default for p in sig.parameters.values()
                      if (p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
                          and p.default is not p.empty)}
    # User may pass additional kwargs.
    # (e.g., connect_kwargs passed to underlying Connection objects)
    passed_kwargs = ChainMap(kwargs, default_kwargs)
    return SAPool(*args, **passed_kwargs)

