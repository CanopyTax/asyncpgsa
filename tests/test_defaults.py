from uuid import uuid4
import pytest
from asyncpgsa import connection
from sqlalchemy import Table, Column, String, MetaData
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()

users = Table('users', metadata,
              Column('id', UUID, unique=True, default=uuid4),
              Column('name', String(60), nullable=False, default='default'),
              Column('version', UUID, default=uuid4, onupdate=uuid4)
              )


def test__insert_query_with_scalar_default():
    query = users.insert()
    new_query, new_params = connection.compile_query(query)
    assert query.parameters.get('name') == 'default'


def test__insert_query_with_callable_default():
    query = users.insert().\
        values(name='username')
    new_query, new_params = connection.compile_query(query)
    assert query.parameters.get('id') is not None
    assert query.parameters.get('version') is not None


def test__update_query_with_callable_default():
    query = users.update().\
        values(name='newname').\
        where(users.c.name == 'default')
    new_query, new_params = connection.compile_query(query)
    assert query.parameters.get('version') is not None
