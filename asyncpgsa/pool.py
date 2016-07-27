import asyncpg
from asyncpg.pool import Pool

from .transactionmanager import ConnectionTransactionContextManager
from .connection import SAConnection


class SAPool(Pool):
    async def _new_connection(self, timeout=None):
        con = await super()._new_connection()
        con = SAConnection.from_connection(con)
        con.pool = self
        return con

    def transaction(self, **kwargs):
        return ConnectionTransactionContextManager(self, **kwargs)

    def begin(self, **kwargs):
        """
        an alias for self.transaction()
        :return:
        """
        return self.transaction(**kwargs)


def create_pool(*args, **kwargs):
    return SAPool(*args, **kwargs)

