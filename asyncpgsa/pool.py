from functools import wraps

import asyncpg

from .transactionmanager import ConnectionTransactionContextManager
from .connection import SAConnection


@wraps(asyncpg.create_pool)
def create_pool(*args,
                dialect=None,
                **connect_kwargs):
    SAConnection._dialect = dialect

    # dict is fine on the pool object as there is usually only one of them
    # asyncpg.pool.Pool.__slots__ += ('__dict__',)

    # monkey patch pool to have some extra methods
    def transaction(self, **kwargs):
        return ConnectionTransactionContextManager(self, **kwargs)
    asyncpg.pool.Pool.transaction = transaction
    asyncpg.pool.Pool.begin = transaction
    pool = asyncpg.create_pool(*args, connection_class=SAConnection,
                               **connect_kwargs)
    return pool

