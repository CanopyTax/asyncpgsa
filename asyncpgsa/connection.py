from asyncpg import connection
from sqlalchemy.sql import ClauseElement
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.dml import Insert as InsertObject

from .record import RecordGenerator, Record

_dialect = postgresql.dialect()
_dialect.implicit_returning = True
_dialect.supports_native_enum = True
_dialect.supports_smallserial = True  # 9.2+
_dialect._backslash_escapes = False
_dialect.supports_sane_multi_rowcount = True  # psycopg 2.0.9+
_dialect._has_native_hstore = True
_dialect.paramstyle = 'named'


def compile_query(query, dialect=_dialect):
    if isinstance(query, str):
        return query, ()
    elif isinstance(query, ClauseElement):
        compiled = query.compile(
            dialect=dialect,
        )

        keys = sorted(
            {compiled.string.find(':' + k): k
             for k in compiled.params.keys()
             }.items())

        final = compiled.string
        params = []
        for i, tup in enumerate(keys):
            _, k = tup
            final = final.replace(':' + k, '$' + str(i + 1))
            params.append(compiled.params[k])

        return final, params


class SAConnection:
    __slots__ = ('connection', 'pool')

    def __init__(self, connection_):
        self.connection = connection_
        self.pool = None

    def __getattr__(self, attr, *args, **kwargs):
        # getattr is only called when attr is NOT found
        return getattr(self.connection, attr)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.pool:
            await self.pool.release(self)
        else:
            await self.close()

    async def execute(self, script, *args, **kwargs) -> str:
        script, params = compile_query(script)
        result = await self.connection.execute(script, *params, *args, **kwargs)
        return RecordGenerator(result)

    async def prepare(self, query, **kwargs):
        query, params = compile_query(query)
        return await self.connection.prepare(query, **kwargs)

    async def fetch(self, query, *args, **kwargs) -> list:
        query, params = compile_query(query)
        result = await self.connection.fetch(query, *params, *args, **kwargs)
        return RecordGenerator(result)

    async def fetchval(self, query, *args, **kwargs):
        query, params = compile_query(query)
        return await self.connection.fetchval(query, *params, *args, **kwargs)

    async def fetchrow(self, query, *args, **kwargs):
        query, params = compile_query(query)
        result = await self.connection.fetchrow(query, *params, *args, **kwargs)
        return Record(result)

    async def insert(self, query, *args, id_col_name: str = 'id', **kwargs):
        if not (isinstance(query, InsertObject) or
                isinstance(query, str)):
            raise ValueError('Query must be an insert object or raw sql string')
        query, params = compile_query(query)
        if id_col_name is not None:
            query += ' RETURNING ' + id_col_name

        return await self.fetchval(query, *params, *args, **kwargs)

    @classmethod
    def from_connection(cls, connection_):
        if connection_.__class__ == connection.Connection:
            return SAConnection(connection_)
        else:
            raise ValueError('Connection object must be of type '
                             'asyncpg.connection.Connection')
