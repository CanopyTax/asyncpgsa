import logging

from asyncpgsa import connection
import sqlalchemy as sa

file_table = sa.Table(
    'meows', sa.MetaData(),
    sa.Column('id'),
    sa.Column('id_1'),
)

async def test_placeholder_swap():
    ids = list(range(1, 10))
    query = file_table.update() \
        .values(id=None) \
        .where(file_table.c.id.in_(ids))
    compiled = query.compile(dialect=connection._dialect)
    query_string, params = connection.placeholder_swap(
        compiled.string, compiled.params)
    assert query_string == 'UPDATE meows SET id=$1 WHERE meows.id IN ' \
                           '($2, $3, $4, $5, $6, $7, $8, $9, $10)'
    assert params == [None, 1, 2, 3, 4, 5, 6, 7, 8, 9]


async def test_placeholder_swap_mixed():
    """Ensure postgres double-colon casting doesn't
    conflict with placeholders
    """
    query = 'SELECT id, :color, id::text as text_id FROM meows WHERE id = $1'
    keyword_params = {'color': 'red'}
    query_string, params = connection.placeholder_swap(
        query, keyword_params)
    assert query_string == 'SELECT id, $2, id::text as text_id FROM ' \
                           'meows WHERE id = $1'
    assert params == ['red']


async def test_compile_query(monkeypatch):
    def mock(*args):
        return 'bob', 'sally'
    monkeypatch.setattr('asyncpgsa.connection.placeholder_swap', mock)
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
