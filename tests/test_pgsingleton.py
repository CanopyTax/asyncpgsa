import pytest
from asyncpgsa import pg
import sqlalchemy as sa

from . import HOST, PORT, USER, PASS

async def _init():
    await pg.init(
            host=HOST,
            port=PORT,
            database='postgres',
            user=USER,
            # loop=loop,
            password=PASS,
            min_size=1,
            max_size=10
        )

query = sa.select('*') \
    .select_from(sa.text('sqrt(:num) as a')) \
    .select_from(sa.text('sqrt(:a2) as b')) \
    .select_from(sa.text('sqrt(:z3) as c')) \
    .params(num=16, a2=36, z3=25)


pytestmark = pytest.mark.asyncio


async def test_pg_query_async_with_statement():
    await _init()

    ps = pg.query(query)
    async with ps as cursor:
        async for row in cursor:
            assert row.a == 4.0
            assert row.b == 6.0
            assert row.c == 5.0
            result = 2

        assert result == 2


async def test_pg_query_with_bad_with_statement():
    await _init()

    ps = pg.query(query)
    try:
        with ps as cursor:
            async for row in cursor:
                assert row.a == 4.0
                assert row.b == 6.0
                assert row.c == 5.0

            result = 2

        assert result == 2

        # try:
        # event_loop.run_until_complete(async_with())
        raise Exception('Should have thrown exception')
    except SyntaxError as e:
        assert str(e) == 'Must use "async with"'


async def test_pg_query_with_no_results():
    await _init()

    ps = pg.query("select * from pg_tables WHERE tablename='bob'")
    async with ps as cursor:
        async for row in cursor:
            raise Exception('Should not have hit this line')


async def test_fetch():
    await _init()

    for row in await pg.fetch(query):
        assert row.a == 4.0
        assert row.b == 6.0
        assert row.c == 5.0

    assert 1 == 1


async def test_fetchrow():
    await _init()

    row = await pg.fetchrow(query)
    assert row.a == 4.0
    assert row.b == 6.0
    assert row.c == 5.0


async def test_fetchval():
    await _init()

    value = await pg.fetchval(query, column=2)
    assert value == 5.0

    value = await pg.fetchval(query, column=0)
    assert value == 4.0

    value = await pg.fetchval(query, column=1)
    assert value == 6.0


async def test_transaction():
    await _init()

    async with pg.transaction() as conn:
        for row in await conn.fetch(query):
            assert row.a == 4.0


async def test_begin():
    await _init()

    async with pg.begin() as conn:
        for row in await conn.fetch(query):
            assert row.a == 4.0
