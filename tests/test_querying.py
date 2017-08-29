import pytest

import os
import enum
from uuid import uuid4, UUID
from datetime import datetime, timedelta

from sqlalchemy import Table, Column, MetaData, types
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.engine import create_engine

from . import URL


class MyEnum(enum.Enum):
    ITEM_1 = 'item_1'
    ITEM_2 = 'item_2'


class MyIntEnum(enum.IntEnum):
    ITEM_1 = enum.auto()
    ITEM_2 = enum.auto()


SAMPLE_DATA = [
    {},
    {
        't_string': 'test1',
    },
    {
        't_string': '',
        't_list': [],
        't_enum': None,
        't_int_enum': None,
        't_datetime': None,
        't_date': None,
        't_interval': None,
        'uniq_uuid': None,
    },
    {
        't_string': 'test3',
        't_list': ['foo', 'bar'],
        # FIXME: elements of Enum subclasses returned as strings
        # 't_enum': MyEnum.ITEM_1,
        # 't_int_enum': MyIntEnum.ITEM_1,
        't_datetime': datetime(2017, 1, 1),
        # FIXME: passing in a date object doesn't work...
        # 't_date': date(2017, 1, 1),
        't_interval': timedelta(seconds=60),
        'uniq_uuid': uuid4(),
    },
    {
        't_string': 'test4',
        't_list': ['bar', 'foo'],
        # FIXME: elements of Enum subclasses returned as strings
        # 't_enum': MyEnum.ITEM_2,
        # 't_int_enum': MyIntEnum.ITEM_2,
        't_datetime': datetime(2018, 1, 1),
        # FIXME: passing in a date object doesn't work...
        # 't_date': date(2018, 1, 1),
        't_date': datetime(2018, 1, 1),  # datetime works though
        't_interval': timedelta(seconds=120),
        'uniq_uuid': uuid4(),
    }
]


@pytest.fixture(scope='module')
def metadata():
    metadata = MetaData()
    metadata.bind = create_engine(URL)
    return metadata


@pytest.fixture(scope='module')
def test_querying_table(metadata):
    """
    Create an object for test table.

    """

    # When using pytest-xdist, we don't want concurrent table creations
    # across test processes so we assign a unique name for table based on
    # the current worker id.
    worker_id = os.environ.get('PYTEST_XDIST_WORKER', 'master')
    return Table(
        'test_querying_table_' + worker_id, metadata,
        Column('id', types.Integer, autoincrement=True, primary_key=True),
        Column('t_string', types.String(60)),
        Column('t_list', types.ARRAY(types.String(60))),
        Column('t_enum', types.Enum(MyEnum)),
        Column('t_int_enum', types.Enum(MyIntEnum)),
        Column('t_datetime', types.DateTime()),
        Column('t_date', types.DateTime()),
        Column('t_interval', types.Interval()),
        Column('uniq_uuid', PG_UUID, nullable=False, unique=True, default=uuid4),
    )


@pytest.fixture(autouse=True)
def create_test_querying_table(test_querying_table):
    """
    This fixture creates table before each test function in this module and
    drops it after.

    We want to recreate table before each test so that each test gets
    a clean table.

    Note that we have to use psycopg2 for table creation as asyncpgsa cannot
    handle table creations.

    """

    test_querying_table.create()
    try:
        yield
    finally:
        test_querying_table.drop()


@pytest.mark.parametrize(
    'insert_function', [
        pytest.param(  # FIXME there is a bug with conn.insert()
            lambda conn, query, table: conn.insert(query),
            marks=pytest.mark.skip(reason='there is a bug with conn.insert()')
        ),
        lambda conn, query, table: conn.fetchval(query.returning(table.c.id)),
    ]
)
async def test_insert_and_fetch(insert_function, test_querying_table, connection):
    query = test_querying_table.insert()

    id_ = await insert_function(connection, query, test_querying_table)
    assert id_ is not None
    assert isinstance(id_, int)

    query = test_querying_table \
        .select() \
        .where(test_querying_table.c.id == id_)

    row = await connection.fetchrow(query)

    assert row.id == id_
    assert row.t_string is None
    assert row.t_list is None
    assert row.t_enum is None
    assert row.t_int_enum is None
    assert row.t_datetime is None
    assert row.t_date is None
    assert row.t_interval is None
    assert isinstance(row.uniq_uuid, UUID)


@pytest.mark.parametrize(
    'insert_function', [
        pytest.param(  # FIXME there is a bug with conn.insert()
            lambda conn, query, table: conn.insert(query),
            marks=pytest.mark.skip(reason='there is a bug with conn.insert()')
        ),
        lambda conn, query, table: conn.fetchval(query.returning(table.c.id)),
    ]
)
@pytest.mark.parametrize('sample', SAMPLE_DATA)
async def test_insert_and_fetch_with_values(insert_function, sample, test_querying_table, connection):
    query = test_querying_table.insert(sample)

    id_ = await insert_function(connection, query, test_querying_table)
    assert id_ is not None
    assert isinstance(id_, int)

    query = test_querying_table \
        .select() \
        .where(test_querying_table.c.id == id_)

    row = await connection.fetchrow(query)

    assert row.id == id_
    for key in sample.keys():
        assert getattr(row, key) == sample[key]


async def test_fetch_list(test_querying_table, connection):
    for sample_item in SAMPLE_DATA:
        query = test_querying_table.insert(sample_item)
        assert await connection.fetchval(query)

    query = test_querying_table.select().order_by(test_querying_table.c.id)
    data = list(await connection.fetch(query))

    assert len(data) == len(SAMPLE_DATA)

    for item, sample_item in zip(data, SAMPLE_DATA):
        for key in sample_item.keys():
            assert getattr(item, key) == sample_item[key]

async def test_bound_parameters(test_querying_table, connection):
    for sample_item in SAMPLE_DATA:
        query = test_querying_table.insert(sample_item)
        assert await connection.fetchval(query)

    query = test_querying_table.select().order_by(test_querying_table.c.id) \
        .where(test_querying_table.c.t_interval < timedelta(seconds=110))
    rows = list(await connection.fetch(query))
    assert len(rows) == 1
    assert rows[0].t_interval == timedelta(seconds=60)

    query = test_querying_table.select().order_by(test_querying_table.c.id) \
        .where(test_querying_table.c.t_interval > timedelta(seconds=110))
    rows = list(await connection.fetch(query))
    assert len(rows) == 1
    assert rows[0].t_interval == timedelta(seconds=120)

    query = test_querying_table.select().order_by(test_querying_table.c.id) \
        .where(test_querying_table.c.t_datetime < datetime(2017, 10, 1))
    rows = list(await connection.fetch(query))
    assert len(rows) == 1
    assert rows[0].t_datetime == datetime(2017, 1, 1)

    query = test_querying_table.select().order_by(test_querying_table.c.id) \
        .where(test_querying_table.c.t_datetime > datetime(2017, 10, 1))
    rows = list(await connection.fetch(query))
    assert len(rows) == 1
    assert rows[0].t_datetime == datetime(2018, 1, 1)

    query = test_querying_table.select().order_by(test_querying_table.c.id) \
        .where(test_querying_table.c.t_list == ['foo', 'bar'])
    rows = list(await connection.fetch(query))
    assert len(rows) == 1
    assert rows[0].t_list == ['foo', 'bar']

    query = test_querying_table.select().order_by(test_querying_table.c.id) \
        .where(test_querying_table.c.t_list.in_([['foo', 'bar'], []]))
    rows = list(await connection.fetch(query))
    assert len(rows) == 2
    assert rows[0].t_list == []
    assert rows[1].t_list == ['foo', 'bar']

# TODO: test more complex queries
# TODO: test incorrect queries
