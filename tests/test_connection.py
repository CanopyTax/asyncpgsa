import logging

from asyncpgsa import connection
import sqlalchemy as sa

file_table = sa.Table(
    'meows', sa.MetaData(),
    sa.Column('id'),
    sa.Column('id_1'),
)

async def test__replace_keys():
    ids = list(range(1, 10))
    query = file_table.update() \
        .values(id=None) \
        .where(file_table.c.id.in_(ids))
    compiled = query.compile(dialect=connection._dialect)
    params = connection._get_keys(compiled)
    new_query = connection._replace_keys(compiled.string, params)
    assert new_query[0] == 'UPDATE meows SET id=$1 WHERE meows.id IN ' \
                           '($2, $3, $4, $5, $6, $7, $8, $9, $10)'
    assert new_query[1] == [None, 1, 2, 3, 4, 5, 6, 7, 8, 9]

async def test__get_keys():
    ids = list(range(1, 10))
    query = file_table.update() \
        .values(id=None) \
        .where(file_table.c.id.in_(ids))
    compiled = query.compile(dialect=connection._dialect)
    connection._get_keys(compiled)


async def test_compile_query(monkeypatch):
    def mock(*args):
        return 'bob'
    monkeypatch.setattr('asyncpgsa.connection._get_keys', mock)

    def mock(*args):
        return 'bob', 'sally'
    monkeypatch.setattr('asyncpgsa.connection._replace_keys',
                        mock)
    ids = list(range(1, 40))
    query = file_table.update() \
        .values(id=None) \
        .where(file_table.c.id.in_(ids))

    results = connection.compile_query(query)
    assert ('bob', 'sally') == results


async def test_compile_query_debug(caplog):
    """Validates that the query is printed to stdout
    when the debug flag is enabled."""
    ids = list(range(1, 3))
    query = file_table.update() \
        .values(id=None) \
        .where(file_table.c.id.in_(ids))

    with caplog.atLevel(logging.DEBUG, logger='asyncpgsa.query'):
        results, _ = connection.compile_query(query)
        msgs = [record.msg for record in caplog.records()]
        assert results in msgs


async def test_compile_query_no_debug(caplog):
    """Validates that no output is printed when
    the debug flag is disabled."""
    ids = list(range(1, 3))
    query = file_table.update() \
        .values(id=None) \
        .where(file_table.c.id.in_(ids))

    with caplog.atLevel(logging.WARNING, logger='asyncpgsa.query'):
        results, _ = connection.compile_query(query)
        msgs = [record.msg for record in caplog.records()]
        assert results not in msgs
