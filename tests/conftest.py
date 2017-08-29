import asyncio

import pytest


def pytest_pycollect_makeitem(collector, name, obj):
    """
    Fix pytest collecting for coroutines.
    """
    if collector.funcnamefilter(name) and asyncio.iscoroutinefunction(obj):
        obj = pytest.mark.asyncio(obj)
        return list(collector._genfunctions(name, obj))


@pytest.fixture
def pool(event_loop):
    from asyncpgsa import create_pool
    from . import HOST, PORT, USER, PASS, DB_NAME

    pool = create_pool(
        min_size=1,
        max_size=3,
        host=HOST,
        port=PORT,
        user=USER,
        password=PASS,
        database=DB_NAME,
        loop=event_loop,
    )

    event_loop.run_until_complete(pool)

    try:
        yield pool
    finally:
        event_loop.run_until_complete(pool.close())


@pytest.fixture
def connection(pool, event_loop):
    conn = event_loop.run_until_complete(pool.acquire())

    try:
        yield conn
    finally:
        event_loop.run_until_complete(pool.release(conn))
