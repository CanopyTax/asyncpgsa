

class ConnectionTransactionContextManager:
    """
    This class is a context manager for a transaction
    and a connection at the same time. It is intended so that one can
    get a connection and transaction in one simple call such as

    async with pool.transaction() as conn:
        conn.execute()

    """

    __slots__ = ('pool', 'acquire_context', 'transaction',
                 'timeout', 'trans_kwargs')

    def __init__(self, pool, timeout=None, **kwargs):
        self.pool = pool
        self.acquire_context = None
        self.transaction = None
        self.timeout = timeout
        self.trans_kwargs = kwargs

    def __enter__(self):
        raise SyntaxError('Must use "async with" for a transaction')

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    async def __aenter__(self):
        self.acquire_context = self.pool.acquire(timeout=self.timeout)
        con = await self.acquire_context.__aenter__()
        self.transaction = con.transaction(**self.trans_kwargs)
        await self.transaction.__aenter__()
        return con

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.transaction.__aexit__(exc_type, exc_val, exc_tb)
        await self.acquire_context.__aexit__(exc_type, exc_val, exc_tb)
