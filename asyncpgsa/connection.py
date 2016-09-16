from asyncpg import connection
from sqlalchemy.sql import ClauseElement
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.dml import Insert as InsertObject
import re
from .record import RecordGenerator, Record

_dialect = postgresql.dialect()
_dialect.implicit_returning = True
_dialect.supports_native_enum = True
_dialect.supports_smallserial = True  # 9.2+
_dialect._backslash_escapes = False
_dialect.supports_sane_multi_rowcount = True  # psycopg 2.0.9+
_dialect._has_native_hstore = True
_dialect.paramstyle = 'named'
_pattern = r':(\w+)(?:\W|)'
_compiled_pattern = re.compile(_pattern, re.M)


class MissingParameterError(KeyError):
    """ This error gets thrown when a parameter is missing in a query """


def _replace_keys(querystring, params, inline=False):
    new_params = []
    for index, param in enumerate(params):
        name, value = param
        if inline:
            querystring = querystring.replace(':' + name, value, 1)
        else:
            querystring = querystring.replace(':' + name,
                                              '$' + str(index + 1), 1)
            new_params.append(value)

    return querystring, new_params


def _get_keys(compiled):
    p = _compiled_pattern
    keys = re.findall(p, compiled.string)
    try:
        params = [(i, compiled.params[i]) for i in keys]
    except KeyError as e:
        raise MissingParameterError('Parameter {} missing'.format(e))
    return params


def compile_query(query, dialect=_dialect, inline=False):
    if isinstance(query, str):
        return query, ()
    elif isinstance(query, ClauseElement):
        compiled = query.compile(dialect=dialect)
        params = _get_keys(compiled)
        new_query, new_params = _replace_keys(compiled.string, params)

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
