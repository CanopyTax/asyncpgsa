# Testing our tests!!
from asyncpgsa.testing import MockPG

async def test_use_fetchrow():
    pg = MockPG()
    pg.set_database_results({'sqrt': 3})
    result = await pg.fetchrow('SELECT * FROM sqrt(16);')
    assert result['sqrt'] == 3


async def test_use_fetchval():
    pg = MockPG()
    pg.set_database_results(3)
    result = await pg.fetchval('SELECT * FROM sqrt(16);')
    assert result == 3


async def test_use_fetch():
    pg = MockPG()
    pg.set_database_results([{'sqrt': 3}])
    result = await pg.fetch('SELECT * FROM sqrt(16);')
    assert result[0]['sqrt'] == 3
