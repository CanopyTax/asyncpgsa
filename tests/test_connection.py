import enum
import json
import logging
import uuid
from functools import partial

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.ddl import CreateTable, DropTable

from asyncpgsa import connection

file_table = sa.Table(
    'meows', sa.MetaData(),
    sa.Column('id'),
    sa.Column('id_1'),
)


class NameBasedEnumType(sa.types.TypeDecorator):
    impl = sa.types.Enum

    def __init__(self, enum_cls, **opts):
        assert issubclass(enum_cls, enum.Enum)
        self._opts = opts
        self._enum_cls = enum_cls
        enums = (m.name for m in enum_cls)
        super().__init__(*enums, **opts)

    def process_bind_param(self, value, dialect):
        return value.name if value else None

    def process_result_value(self, value: str, dialect):
        return self._enum_cls[value] if value else None

    def copy(self):
        return NameBasedEnumType(self._enum_cls, **self._opts)


class FileTypes(enum.Enum):
    TEXT = 0
    PNG = 1
    PDF = 2


file_type_table = sa.Table(
    'meows2', sa.MetaData(),
    sa.Column('type', NameBasedEnumType(FileTypes)),
    sa.Column('name', sa.String(length=128)),
)


def test_compile_query():
    ids = list(range(1, 4))
    query = file_table.update() \
        .values(id=None) \
        .where(file_table.c.id.in_(ids))
    q, p = connection.compile_query(query)
    assert q == 'UPDATE meows SET id=$1 WHERE meows.id IN ($2, $3, $4)'
    assert p == [None, 1, 2, 3]


def test_compile_text_query():
    sql = sa.text('SELECT :id, my_date::DATE FROM users').params(id=123)
    q, p = connection.compile_query(sql)
    assert q == 'SELECT $1, my_date::DATE FROM users'
    assert p == [123]


def test_compile_query_with_custom_column_type():
    query = file_type_table.insert().values(type=FileTypes.PDF)
    q, p = connection.compile_query(query)
    assert q == 'INSERT INTO meows2 (type) VALUES ($1)'
    assert p == ['PDF']


def test_compile_query_debug(caplog):
    """Validates that the query is printed to stdout
    when the debug flag is enabled."""
    ids = list(range(1, 3))
    query = file_table.update() \
        .values(id=None) \
        .where(file_table.c.id.in_(ids))

    with caplog.at_level(logging.DEBUG, logger='asyncpgsa.query'):
        results, _ = connection.compile_query(query)
        msgs = [record.msg for record in caplog.records]
        assert results in msgs


def test_compile_query_no_debug(caplog):
    """Validates that no output is printed when
    the debug flag is disabled."""
    ids = list(range(1, 3))
    query = file_table.update() \
        .values(id=None) \
        .where(file_table.c.id.in_(ids))

    with caplog.at_level(logging.WARNING, logger='asyncpgsa.query'):
        results, _ = connection.compile_query(query)
        msgs = [record.msg for record in caplog.records]
        assert results not in msgs


def test_compile_jsonb_with_custom_json_encoder():
    jsonb_table = sa.Table(
        'meowsb', sa.MetaData(),
        sa.Column('data', postgresql.JSONB),
    )

    class JSONEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, uuid.UUID):
                return str(o)
            else:
                return super().default(o)

    dialect = connection.get_dialect(
        json_serializer=partial(json.dumps, cls=JSONEncoder)
    )

    data = {
        'uuid4': uuid.uuid4(),
    }
    query = jsonb_table.insert().values(data=data)
    q, p = connection.compile_query(query, dialect=dialect)
    assert q == 'INSERT INTO meowsb (data) VALUES ($1)'
    assert p == ['{"uuid4": "%s"}' % data['uuid4']]


ddl_test_table = sa.Table(
    'ddl_test_table', sa.MetaData(),
    sa.Column('int_col', sa.Integer),
    sa.Column('str_col', sa.String),
)

def test_compile_create_table_ddl():
    create_statement = CreateTable(ddl_test_table)
    result, params = connection.compile_query(create_statement)
    assert result == (
        '\nCREATE TABLE ddl_test_table (\n\tint_col'
        ' INTEGER, \n\tstr_col VARCHAR\n)\n\n'
    )
    assert len(params) == 0


def test_compile_drop_table_ddl():
    drop_statement = DropTable(ddl_test_table)
    drop_query, params = connection.compile_query(drop_statement)
    assert drop_query == '\nDROP TABLE ddl_test_table'
    assert len(params) == 0
