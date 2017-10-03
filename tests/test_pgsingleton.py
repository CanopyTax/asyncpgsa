from asyncpgsa import pg
import pytest
import sqlalchemy as sa

from . import HOST, PORT, USER, PASS, DB_NAME


@pytest.fixture(scope='function', autouse=True)
def init_pg(event_loop):
    """
    Initializes the pg connection before each test in the module.
    :param event_loop: Active event loop for the test run
    :return: None
    """
    event_loop.run_until_complete(pg.init(
        host=HOST,
        port=PORT,
        database=DB_NAME,
        user=USER,
        # loop=loop,
        password=PASS,
        min_size=1,
        max_size=10
    ))

query = sa.select('*') \
    .select_from(sa.text('sqrt(:num) as a')) \
    .select_from(sa.text('sqrt(:a2) as b')) \
    .select_from(sa.text('sqrt(:z3) as c')) \
    .params(num=16, a2=36, z3=25)


async def test_pg_query_async_with_statement():
    ps = pg.query(query)
    async with ps as cursor:
        row = sentinel = object()
        async for row in cursor:
            assert row['a'] == 4.0
            assert row['b'] == 6.0
            assert row['c'] == 5.0
        if row is sentinel:
            pytest.fail('Cursor had no data')


async def test_pg_query_with_bad_with_statement():
    ps = pg.query(query)

    with pytest.raises(SyntaxError) as exc_info:
        with ps as cursor:
            async for row in cursor:
                assert row['a'] == 4.0
                assert row['b'] == 6.0
                assert row['c'] == 5.0

            result = 2

        assert result == 2

    assert str(exc_info.value) == 'Must use "async with"'


async def test_pg_query_with_no_results():
    ps = pg.query("SELECT * FROM pg_tables WHERE tablename='bob'")
    async with ps as cursor:
        async for row in cursor:
            raise Exception('Should not have hit this line')


async def test_pg_queury_with_await():
    ps = pg.query(query)
    results = await ps
    row = sentinel = object()
    for row in results:
        assert row['a'] == 4.0
        assert row['b'] == 6.0
        assert row['c'] == 5.0
    if row is sentinel:
        pytest.fail('No results')

async def test_fetch():
    for row in await pg.fetch(query):
        assert row['a'] == 4.0
        assert row['b'] == 6.0
        assert row['c'] == 5.0

    assert 1 == 1


async def test_fetch_nonetype():
    query = "SELECT * FROM pg_tables WHERE tablename='foobar_doesnt_exist'"
    result = await pg.fetch(query)
    for r in result:
        assert False, 'Should not have any data'


async def test_fetchrow():
    row = await pg.fetchrow(query)
    assert row['a'] == 4.0
    assert row['b'] == 6.0
    assert row['c'] == 5.0


async def test_fetchrow_nonetype():
    query = "SELECT * FROM pg_tables WHERE tablename='foobar_doesnt_exist'"
    result = await pg.fetchrow(query)
    assert not bool(result)


async def test_fetchrow_sometype():
    result = await pg.fetchrow(query)
    assert bool(result), 'Fetchrow should be truthy with data.'


async def test_execute():
    script = "SELECT 1; SELECT 2;"
    result = await pg.execute(script)
    assert bool(result)


async def test_fetchval():
    value = await pg.fetchval(query, column=2)
    assert value == 5.0

    value = await pg.fetchval(query, column=0)
    assert value == 4.0

    value = await pg.fetchval(query, column=1)
    assert value == 6.0


async def test_sql_with_arguments():
    script = "SELECT $1::INT"
    result = await pg.execute(script, 1)
    assert bool(result)


async def test_execute_with_sa_arguments():
    script = sa.select('*').select_from(sa.text('sqrt(:num) as a'))
    script = script.params(num=16)
    result = await pg.execute(script)
    assert bool(result)

async def test_transaction():
    async with pg.transaction() as conn:
        for row in await conn.fetch(query):
            assert row['a'] == 4.0


async def test_begin():
    async with pg.begin() as conn:
        for row in await conn.fetch(query):
            assert row['a'] == 4.0
