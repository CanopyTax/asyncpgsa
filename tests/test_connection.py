import enum
import logging

from asyncpgsa import connection
import sqlalchemy as sa


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
    query = file_type_table.insert() \
        .values(type=FileTypes.PDF, name='abc')
    q, p = connection.compile_query(query)
    assert q == 'INSERT INTO meows2 (type, name) VALUES ($1, $2)'
    assert p == ['PDF', 'abc']


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
