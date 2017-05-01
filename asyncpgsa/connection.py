import re

import sqlparse
from asyncpg import connection
from sqlalchemy.dialects.postgresql import pypostgresql
from sqlalchemy.sql import ClauseElement
from sqlalchemy.sql.dml import Insert as InsertObject, Update as UpdateObject

from .log import query_logger
from .record import RecordGenerator, Record

_dialect = pypostgresql.dialect()
_dialect.implicit_returning = True
_dialect.supports_native_enum = True
_dialect.supports_smallserial = True  # 9.2+
_dialect._backslash_escapes = False
_dialect.supports_sane_multi_rowcount = True  # psycopg 2.0.9+
_dialect._has_native_hstore = True
_dialect.paramstyle = 'named'


class MissingParameterError(KeyError):
    """ This error gets thrown when a parameter is missing in a query """


def execute_defaults(query):
    if isinstance(query, InsertObject):
        attr_name = 'default'
    elif isinstance(query, UpdateObject):
        attr_name = 'onupdate'
    else:
        return query

    query.parameters = query.parameters or {}
    for col in query.table.columns:
        attr = getattr(col, attr_name)
        if attr and not query.parameters.get(col.name):
            if attr.is_scalar:
                query.parameters[col.name] = attr.arg
            elif col.default.is_callable:
                query.parameters[col.name] = attr.arg({})

    return query


def placeholder_swap(input_sql, keyword_values=None):
    """
    Takes a given query in `input_sql` and converts all `:keyword` parameters
    into `$1` parameters, and returns a matching list of values ordered
    according to the matching numeric index from the newly generated query.
    :param input_sql: sql to be converted from keyword to numeric placeholders
    :param keyword_values: dict of keyword: value pairs
    :return: tuple of a modified query and list of values from keyword_values
        in which all the values are ordered properly for the paired query
    """
    if not keyword_values:
        keyword_values = {}
    placeholder_type = sqlparse.tokens.Name.Placeholder
    tokens = sqlparse.parse(input_sql)[0]
    placeholders = [token for token in tokens.flatten()
                    if token.ttype == placeholder_type]
    colon_placeholders = [i for i in placeholders
                          if i.value.startswith(':')]
    placeholder_index = len(placeholders) - len(colon_placeholders) + 1
    keywords = {}
    params = []
    for i, placeholder in enumerate(colon_placeholders):
        kw_name = placeholder.value[1:]
        keywords[kw_name] = placeholder_index
        placeholder.value = '$'+str(placeholder_index)
        try:
            params.append(keyword_values[kw_name])
        except KeyError as e:
            raise MissingParameterError('Parameter {} missing'.format(e))
        placeholder_index += 1

    output_sql = str(tokens)
    return output_sql, params


def compile_query(query, dialect=_dialect, inline=False):
    if isinstance(query, str):
        query_logger.debug(query)
        return query, ()
    elif isinstance(query, ClauseElement):
        query = execute_defaults(query)  # default values for Insert/Update
        compiled = query.compile(dialect=dialect)
        new_query, new_params = placeholder_swap(
            compiled.string,
            compiled.params
        )

        query_logger.debug(new_query)

        if inline:
            return new_query
        return new_query, new_params


class SAConnection:
    __slots__ = ('_connection', '_dialect')

    def __init__(self, connection_: connection, *, dialect=None):
        self._connection = connection_
        if not dialect:
            dialect = _dialect
        self._dialect = dialect

    def __getattr__(self, attr, *args, **kwargs):
        # getattr is only called when attr is NOT found
        return getattr(self._connection, attr)

    async def execute(self, script, *args, **kwargs) -> str:
        script, params = compile_query(script, dialect=self._dialect)
        result = await self._connection.execute(script, *params, *args, **kwargs)
        return RecordGenerator(result)

    async def prepare(self, query, **kwargs):
        query, params = compile_query(query, dialect=self._dialect)
        return await self._connection.prepare(query, **kwargs)

    async def fetch(self, query, *args, **kwargs) -> list:
        query, params = compile_query(query, dialect=self._dialect)
        result = await self._connection.fetch(query, *params, *args, **kwargs)
        return RecordGenerator(result)

    async def fetchval(self, query, *args, **kwargs):
        query, params = compile_query(query, dialect=self._dialect)
        return await self._connection.fetchval(query, *params, *args, **kwargs)

    async def fetchrow(self, query, *args, **kwargs):
        query, params = compile_query(query, dialect=self._dialect)
        result = await self._connection.fetchrow(query, *params, *args, **kwargs)
        return Record(result)

    async def insert(self, query, *args, id_col_name: str = 'id', **kwargs):
        if not (isinstance(query, InsertObject) or
                isinstance(query, str)):
            raise ValueError('Query must be an insert object or raw sql string')
        query, params = compile_query(query, dialect=self._dialect)
        if id_col_name is not None:
            query += ' RETURNING ' + id_col_name

        return await self.fetchval(query, *params, *args, **kwargs)

    @classmethod
    def from_connection(cls, connection_: connection, dialect=None):
        if connection_.__class__ == connection.Connection:
            return SAConnection(connection_, dialect=dialect)
        else:
            raise ValueError('Connection object must be of type '
                             'asyncpg.connection.Connection')
