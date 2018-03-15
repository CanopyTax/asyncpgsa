from asyncpg import connection
from sqlalchemy.dialects.postgresql import pypostgresql
from sqlalchemy.sql import ClauseElement
from sqlalchemy.sql.dml import Insert as InsertObject, Update as UpdateObject

from .log import query_logger

_dialect = pypostgresql.dialect(paramstyle='pyformat')
_dialect.implicit_returning = True
_dialect.supports_native_enum = True
_dialect.supports_smallserial = True  # 9.2+
_dialect._backslash_escapes = False
_dialect.supports_sane_multi_rowcount = True  # psycopg 2.0.9+
_dialect._has_native_hstore = True


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
        if attr and query.parameters.get(col.name) is None:
            if attr.is_scalar:
                query.parameters[col.name] = attr.arg
            elif col.default and col.default.is_callable:
                query.parameters[col.name] = attr.arg({})

    return query


def compile_query(query, dialect=_dialect, inline=False):
    if isinstance(query, str):
        query_logger.debug(query)
        return query, ()
    elif isinstance(query, ClauseElement):
        query = execute_defaults(query)  # default values for Insert/Update
        compiled = query.compile(dialect=dialect)

        keys = compiled.params.keys()
        new_query = compiled.string % {key: '$' + str(i)
                                       for i, key in enumerate(keys, start=1)}
        processors = compiled._bind_processors
        new_params = [processors[key](compiled.params[key])
                      if key in processors else compiled.params[key]
                      for key in keys]

        query_logger.debug(new_query)

        if inline:
            return new_query
        return new_query, new_params


class SAConnection(connection.Connection):
    def __init__(self, *args, dialect=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._dialect = dialect or _dialect

    def _execute(self, query, args, limit, timeout, return_status=False):
        query, compiled_args = compile_query(query, dialect=self._dialect)
        args = compiled_args or args
        return super()._execute(query, args, limit, timeout,
                                return_status=return_status)

    async def execute(self, script, *args, **kwargs) -> str:
        script, params = compile_query(script, dialect=self._dialect)
        args = params or args
        result = await super().execute(script, *args, **kwargs)
        return result

    def cursor(self, query, *args, prefetch=None, timeout=None):
        query, compiled_args = compile_query(query, dialect=self._dialect)
        args = compiled_args or args
        return super().cursor(query, *args, prefetch=prefetch, timeout=timeout)
