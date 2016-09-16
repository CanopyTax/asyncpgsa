import asyncpgsa
import pytest
import sqlalchemy as sa

from . import HOST, PORT, USER, PASS


@pytest.fixture(scope='function')
def pool(event_loop):
    _pool = event_loop.run_until_complete(asyncpgsa.create_pool(host=HOST,
                                                                port=PORT,
                                                                database='postgres',
                                                                user=USER,
                                                                password=PASS,
                                                                min_size=1,
                                                                max_size=10))
    yield _pool


async def test_pool_basic(pool):
    con = await pool.acquire()
    result = await con.fetch('SELECT * FROM sqrt(16)')
    assert next(result).sqrt == 4.0
    await pool.close()


async def test_pool_connection_transaction_context_manager(pool):
    async with pool.transaction() as conn:
        result = await conn.fetch('SELECT * FROM sqrt(16)')

    assert next(result).sqrt == 4.0


async def test_use_sqlalchemy_with_escaped_params(pool):
    """
    Use sqlalchemy with escaped params
    Make sure that the escaped parameters get used in the right order
    :return:
    """
    query = sa.select('*') \
        .select_from(sa.text('sqrt(:num) as a')) \
        .select_from(sa.text('sqrt(:a2) as b')) \
        .select_from(sa.text('sqrt(:z3) as c')) \
        .params(num=16, a2=36, z3=25)
    async with pool.transaction() as conn:
        result = await conn.fetch(query)

    row = next(result)
    assert row.a == 4.0
    assert row.b == 6.0
    assert row.c == 5.0


async def test_use_sa_core_objects(pool):
    pg_tables = sa.Table(
        'pg_tables', sa.MetaData(),
        sa.Column('schemaname'),
        sa.Column('tablename'),
        sa.Column('tableowner'),
        sa.Column('tablespace'),
        sa.Column('hasindexes')
    )

    query = pg_tables.select().where(pg_tables.c.schemaname == 'pg_catalog')
    async with pool.transaction() as conn:
        result = await conn.fetch(query)

    for row in result:
        # just making sure none of these throw KeyError exceptions
        assert isinstance(row.schemaname, str)
        assert hasattr(row, 'tablename')
        assert hasattr(row, 'tableowner')
        assert hasattr(row, 'tablespace')
        assert hasattr(row, 'hasindexes')


async def test_with_without_async_should_throw_exception(pool):
    try:
        with pool.transaction() as conn:
            result = await conn.fetch('SELECT * FROM sqrt(16)')

        raise Exception('Should have thrown SyntaxError')
    except SyntaxError as e:
        assert str(e) == 'Must use "async with" for a transaction'
