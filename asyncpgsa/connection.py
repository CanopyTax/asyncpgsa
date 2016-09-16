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


def replace_keys(keys, querystring, params, inline=False):
    new_query = querystring
    new_params = []
    for key, value in enumerate(keys):
        if inline:
            new_query = new_query.replace(':' + value, params[key][1], 1)
        else:
            new_query = new_query.replace(':' + value, '$' + str(key + 1), 1)
            new_params.append(params[key][1])

    return new_query, new_params


def get_keys(compiled):
    import re
    pattern = ':(\w+)(?:\W|)'
    p = re.compile(pattern, re.M)
    keys = re.findall(p, compiled.string)
    params = []
    for i in keys:
        params.append((i, compiled.params[i]))
    return keys, params


def compile_query(query, dialect=_dialect, inline=False):
    if isinstance(query, str):
        return query, ()
    elif isinstance(query, ClauseElement):
        compiled = query.compile(dialect=dialect)
        keys, params = get_keys(compiled)
        new_query, new_params = replace_keys(keys, compiled.string, params)

        if inline:
            return new_query
        return new_query, new_params


class SAConnection:
    __slots__ = ('connection',)

    def __init__(self, connection_: connection):
        self.connection = connection_

    def __getattr__(self, attr, *args, **kwargs):
        # getattr is only called when attr is NOT found
        return getattr(self.connection, attr)

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
