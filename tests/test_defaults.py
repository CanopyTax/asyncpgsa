import enum
from uuid import uuid4, UUID
from datetime import date, datetime, timedelta
from asyncpgsa import connection
from sqlalchemy import Table, Column, MetaData, types
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

metadata = MetaData()


class MyEnum(enum.Enum):
    ITEM_1 = 'item_1'
    ITEM_2 = 'item_2'


class MyIntEnum(enum.IntEnum):
    ITEM_1 = 1
    ITEM_2 = 2


name_default = 'default'
t_list_default = ['foo', 'bar']
t_enum_default = MyEnum.ITEM_2
t_int_enum_default = MyIntEnum.ITEM_1
t_datetime_default = datetime(2017, 1, 1)
t_date_default = date(2017, 1, 1)
t_date_2_default = lambda: date(2017, 2, 1)
t_interval_default = timedelta(seconds=60)
t_boolean_default = True


users = Table(
    'users', metadata,
    Column('id', PG_UUID, unique=True, default=uuid4),
    Column('name', types.String(60), nullable=False,
           default=name_default),
    Column('t_list', types.ARRAY(types.String(60)), nullable=False,
           default=t_list_default),
    Column('t_enum', types.Enum(MyEnum), nullable=False,
           default=t_enum_default),
    Column('t_int_enum', types.Enum(MyIntEnum), nullable=False,
           default=t_int_enum_default),
    Column('t_datetime', types.DateTime(), nullable=False,
           default=t_datetime_default),
    Column('t_date', types.DateTime(), nullable=False,
           default=t_date_default),
    Column('t_date_2', types.DateTime(), nullable=False,
           default=t_date_2_default),
    Column('t_interval', types.Interval(), nullable=False,
           default=t_interval_default),
    Column('t_boolean', types.Boolean(), nullable=False,
           default=True),
    Column('version', PG_UUID,
           default=uuid4, onupdate=uuid4)
)


def test_insert_query_defaults():
    query = users.insert()
    new_query, new_params = connection.compile_query(query)
    assert query.parameters.get('name') == name_default
    assert query.parameters.get('t_list') == t_list_default
    assert query.parameters.get('t_enum') == t_enum_default
    assert query.parameters.get('t_int_enum') == t_int_enum_default
    assert query.parameters.get('t_datetime') == t_datetime_default
    assert query.parameters.get('t_date') == t_date_default
    assert query.parameters.get('t_date_2') == t_date_2_default()
    assert query.parameters.get('t_interval') == t_interval_default
    assert isinstance(query.parameters.get('version'), UUID)
    assert query.parameters.get('t_boolean') == t_boolean_default


def test_insert_query_defaults_override():
    query = users.insert()
    query = query.values(
        name='username',
        t_list=['l1', 'l2'],
        t_enum=MyEnum.ITEM_1,
        t_int_enum=MyIntEnum.ITEM_2,
        t_datetime=datetime(2020, 1, 1),
        t_date=date(2020, 1, 1),
        t_date_2=date(2020, 1, 1),
        t_interval=timedelta(seconds=120),
        t_boolean=False
    )
    new_query, new_params = connection.compile_query(query)
    assert query.parameters.get('version')
    assert query.parameters.get('name') == 'username'
    assert query.parameters.get('t_list') == ['l1', 'l2']
    assert query.parameters.get('t_enum') == MyEnum.ITEM_1
    assert query.parameters.get('t_int_enum') == MyIntEnum.ITEM_2
    assert query.parameters.get('t_datetime') == datetime(2020, 1, 1)
    assert query.parameters.get('t_date') == date(2020, 1, 1)
    assert query.parameters.get('t_date_2') == date(2020, 1, 1)
    assert query.parameters.get('t_interval') == timedelta(seconds=120)
    assert query.parameters.get('t_boolean') == False
    assert isinstance(query.parameters.get('version'), UUID)


def test_update_query():
    query = users.update().where(users.c.name == 'default')
    query = query.values(
        name='newname',
        t_list=['l3', 'l4'],
        t_enum=MyEnum.ITEM_1,
        t_int_enum=MyIntEnum.ITEM_2,
        t_datetime=datetime(2030, 1, 1),
        t_date=date(2030, 1, 1),
        t_date_2=date(2030, 1, 1),
        t_interval=timedelta(seconds=180),
        t_boolean=False
    )
    new_query, new_params = connection.compile_query(query)
    assert query.parameters.get('version')
    assert query.parameters.get('name') == 'newname'
    assert query.parameters.get('t_list') == ['l3', 'l4']
    assert query.parameters.get('t_enum') == MyEnum.ITEM_1
    assert query.parameters.get('t_int_enum') == MyIntEnum.ITEM_2
    assert query.parameters.get('t_datetime') == datetime(2030, 1, 1)
    assert query.parameters.get('t_date') == date(2030, 1, 1)
    assert query.parameters.get('t_date_2') == date(2030, 1, 1)
    assert query.parameters.get('t_interval') == timedelta(seconds=180)
    assert query.parameters.get('t_boolean') == False
    assert isinstance(query.parameters.get('version'), UUID)
