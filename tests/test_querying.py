import enum
import os
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import Column, MetaData, Sequence, Table, types
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql.ddl import CreateSequence, CreateTable, DropSequence, DropTable


class MyEnum(enum.Enum):
    ITEM_1 = "item_1"
    ITEM_2 = "item_2"


class MyIntEnum(enum.IntEnum):
    ITEM_1 = 1
    ITEM_2 = 2


SAMPLE_DATA = [
    {},
    {
        "t_string": "test1",
    },
    {
        "t_string": "",
        "t_list": [],
        "t_enum": None,
        "t_int_enum": None,
        "t_datetime": None,
        "t_date": None,
        "t_interval": None,
        "uniq_uuid": None,
    },
    {
        "t_string": "test3",
        "t_list": ["foo", "bar"],
        # FIXME: elements of Enum subclasses returned as strings
        # 't_enum': MyEnum.ITEM_1,
        # 't_int_enum': MyIntEnum.ITEM_1,
        "t_datetime": datetime(2017, 1, 1),
        # FIXME: passing in a date object doesn't work...
        # 't_date': date(2017, 1, 1),
        "t_interval": timedelta(seconds=60),
        "uniq_uuid": uuid4(),
    },
    {
        "t_string": "test4",
        "t_list": ["bar", "foo"],
        # FIXME: elements of Enum subclasses returned as strings
        # 't_enum': MyEnum.ITEM_2,
        # 't_int_enum': MyIntEnum.ITEM_2,
        "t_datetime": datetime(2018, 1, 1),
        # FIXME: passing in a date object doesn't work...
        # 't_date': date(2018, 1, 1),
        "t_date": datetime(2018, 1, 1),  # datetime works though
        "t_interval": timedelta(seconds=120),
        "uniq_uuid": uuid4(),
    },
]

MROW_SAMPLE_DATA = [
    {
        "t_string": "test1",
    },
    {
        "t_string": "test2",
    },
]


@pytest.fixture(scope="module")
def metadata():
    return MetaData()


@pytest.fixture(scope="module")
def test_querying_table(metadata):
    """
    Create an object for test table.

    """

    # When using pytest-xdist, we don't want concurrent table creations
    # across test processes so we assign a unique name for table based on
    # the current worker id.
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    return Table(
        "test_querying_table_" + worker_id,
        metadata,
        Column("id", types.Integer, autoincrement=True, primary_key=True),
        Column("serial", types.Integer, Sequence("serial_seq")),
        Column("t_string", types.String(60), onupdate="updated"),
        Column("t_list", types.ARRAY(types.String(60))),
        Column("t_enum", types.Enum(MyEnum)),
        Column("t_int_enum", types.Enum(MyIntEnum)),
        Column("t_datetime", types.DateTime()),
        Column("t_date", types.DateTime()),
        Column("t_interval", types.Interval()),
        Column("uniq_uuid", PG_UUID, nullable=False, unique=True, default=uuid4),
    )


@pytest.fixture(autouse=True)
def create_test_querying_table(test_querying_table, connection, event_loop):
    """
    This fixture creates table before each test function in this module and
    drops it after.

    We want to recreate table before each test so that each test gets
    a clean table.

    Note that we have to use psycopg2 for table creation as asyncpgsa cannot
    handle table creations.

    """

    async def create_enum(enum_cls):
        labels = [f"'{e.value}'" for e in enum_cls]  # Enum labels are always strings
        await connection.execute(
            f"CREATE TYPE {enum_cls.__name__.lower()} " f"AS ENUM ({', '.join(labels)})"
        )

    async def drop_enum(enum_cls):
        await connection.execute(f"DROP TYPE {enum_cls.__name__.lower()}")

    event_loop.run_until_complete(create_enum(MyEnum))
    event_loop.run_until_complete(create_enum(MyIntEnum))
    event_loop.run_until_complete(
        connection.execute(CreateSequence(Sequence("serial_seq")))
    )
    event_loop.run_until_complete(connection.execute(CreateTable(test_querying_table)))
    try:
        yield
    finally:
        event_loop.run_until_complete(
            connection.execute(DropTable(test_querying_table))
        )
        event_loop.run_until_complete(
            connection.execute(DropSequence(Sequence("serial_seq")))
        )
        event_loop.run_until_complete(drop_enum(MyIntEnum))
        event_loop.run_until_complete(drop_enum(MyEnum))


async def test_fetch_list(test_querying_table, connection):
    for sample_item in SAMPLE_DATA:
        query = test_querying_table.insert(sample_item)
        assert await connection.fetchval(query)

    query = test_querying_table.select().order_by(test_querying_table.c.id)
    data = list(await connection.fetch(query))

    assert len(data) == len(SAMPLE_DATA)

    for item, sample_item in zip(data, SAMPLE_DATA):
        for key in sample_item.keys():
            if key == "serial":
                # Same increment as `id` column
                expected = item["id"]
            else:
                expected = sample_item[key]
            assert item[key] == expected


async def test_bound_parameters(test_querying_table, connection):
    for sample_item in SAMPLE_DATA:
        query = test_querying_table.insert(sample_item)
        assert await connection.fetchval(query)

    query = (
        test_querying_table.select()
        .order_by(test_querying_table.c.id)
        .where(test_querying_table.c.t_interval < timedelta(seconds=110))
    )
    rows = list(await connection.fetch(query))
    assert len(rows) == 1
    assert rows[0]["t_interval"] == timedelta(seconds=60)

    query = (
        test_querying_table.select()
        .order_by(test_querying_table.c.id)
        .where(test_querying_table.c.t_interval > timedelta(seconds=110))
    )
    rows = list(await connection.fetch(query))
    assert len(rows) == 1
    assert rows[0]["t_interval"] == timedelta(seconds=120)

    query = (
        test_querying_table.select()
        .order_by(test_querying_table.c.id)
        .where(test_querying_table.c.t_datetime < datetime(2017, 10, 1))
    )
    rows = list(await connection.fetch(query))
    assert len(rows) == 1
    assert rows[0]["t_datetime"] == datetime(2017, 1, 1)

    query = (
        test_querying_table.select()
        .order_by(test_querying_table.c.id)
        .where(test_querying_table.c.t_datetime > datetime(2017, 10, 1))
    )
    rows = list(await connection.fetch(query))
    assert len(rows) == 1
    assert rows[0]["t_datetime"] == datetime(2018, 1, 1)

    query = (
        test_querying_table.select()
        .order_by(test_querying_table.c.id)
        .where(test_querying_table.c.t_list == ["foo", "bar"])
    )
    rows = list(await connection.fetch(query))
    assert len(rows) == 1
    assert rows[0]["t_list"] == ["foo", "bar"]

    query = (
        test_querying_table.select()
        .order_by(test_querying_table.c.id)
        .where(test_querying_table.c.t_list.in_([["foo", "bar"], []]))
    )
    rows = list(await connection.fetch(query))
    assert len(rows) == 2
    assert rows[0]["t_list"] == []
    assert rows[1]["t_list"] == ["foo", "bar"]


async def test_defaults(test_querying_table, connection):
    """Test 'default' in a multirow insert and 'onupdate' in an update."""
    query = test_querying_table.insert().values(MROW_SAMPLE_DATA)
    assert await connection.execute(query)

    query = test_querying_table.select().order_by(test_querying_table.c.id)
    data = list(await connection.fetch(query))

    assert len(data) == len(MROW_SAMPLE_DATA)

    query = (
        test_querying_table.update()
        .values()
        .where(test_querying_table.c.id == data[0]["id"])
        .returning(test_querying_table.c.t_string)
    )
    row = await connection.fetchval(query)
    assert row == "updated"


# TODO: test more complex queries
# TODO: test incorrect queries
