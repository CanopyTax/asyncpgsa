import re

from asyncpg import connection
from sqlalchemy.dialects.postgresql import pypostgresql
from sqlalchemy.sql import ClauseElement
from sqlalchemy.sql.dml import Insert as InsertObject, Update as UpdateObject

from .log import query_logger

_dialect = pypostgresql.dialect()
_dialect.implicit_returning = True
_dialect.supports_native_enum = True
_dialect.supports_smallserial = True  # 9.2+
_dialect._backslash_escapes = False
_dialect.supports_sane_multi_rowcount = True  # psycopg 2.0.9+
_dialect._has_native_hstore = True
_dialect.paramstyle = 'named'
_pattern = r'(?<!:):(\w+)'
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
    processors = compiled._bind_processors
    params = []
    try:
        for key in keys:
            processed_param = (processors[key](compiled.params[key])
                               if key in processors
                               else compiled.params[key])
            params.append((key, processed_param))
    except KeyError as e:
        raise MissingParameterError('Parameter {} missing'.format(e))
    return params


def execute_defaults(query):
    if isinstance(query, InsertObject):
        attr_name = 'default'
    elif isinstance(query, UpdateObject):
        attr_name = 'onupdate'
    else:
        return query

    # query.parameters could be a list in a multi row insert
    if isinstance(query.parameters, list):
        for param in query.parameters:
            _execute_default_attr(query, param, attr_name)
    else:
        query.parameters = query.parameters or {}
        _execute_default_attr(query, query.parameters, attr_name)
    return query


def _execute_default_attr(query, param, attr_name):
    for col in query.table.columns:
        attr = getattr(col, attr_name)
        if attr and param.get(col.name) is None:
            if attr.is_scalar:
                param[col.name] = attr.arg
            elif attr.is_callable:
                param[col.name] = attr.arg({})


def compile_query(query, dialect=_dialect, inline=False):
    if isinstance(query, str):
        query_logger.debug(query)
        return query, ()
    elif isinstance(query, ClauseElement):
        query = execute_defaults(query)  # default values for Insert/Update
        compiled = query.compile(dialect=dialect)
        params = _get_keys(compiled)
        new_query, new_params = _replace_keys(compiled.string, params)

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
