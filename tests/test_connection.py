# from asyncpgsa import pg
from asyncpgsa import connection
import sqlalchemy as sa

file_table = sa.Table(
    'meows', sa.MetaData(),
    sa.Column('id'),
    sa.Column('id_1'),
)

async def test_replace_keys():
    ids = list(range(1, 10))
    query = file_table.update() \
        .values(id=None) \
        .where(file_table.c.id.in_(ids))
    compiled = query.compile(dialect=connection._dialect)
    keys, params = connection.get_keys(compiled)
    new_query = connection.replace_keys(keys, compiled.string, params)
    assert new_query[0] == 'UPDATE meows SET id=$1 WHERE meows.id IN ' \
                           '($2, $3, $4, $5, $6, $7, $8, $9, $10)'
    assert new_query[1] == [None, 1, 2, 3, 4, 5, 6, 7, 8, 9]

async def test_get_keys():
    ids = list(range(1, 10))
    query = file_table.update() \
        .values(id=None) \
        .where(file_table.c.id.in_(ids))
    compiled = query.compile(dialect=connection._dialect)
    connection.get_keys(compiled)


async def test_compile_query(monkeypatch):
    def mock(x):
        return 'bob', 'sally'
    monkeypatch.setattr('asyncpgsa.connection.get_keys', mock)

    def mock(x, y, z):
        return 'bob', 'sally'
    monkeypatch.setattr('asyncpgsa.connection.replace_keys',
                        mock)
    ids = list(range(1, 40))
    query = file_table.update() \
        .values(id=None) \
        .where(file_table.c.id.in_(ids))

    results = connection.compile_query(query)
    assert ('bob', 'sally') == results
