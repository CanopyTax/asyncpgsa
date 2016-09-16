import asyncio

import pytest


def pytest_pycollect_makeitem(collector, name, obj):
    """
    Fix pytest collecting for coroutines.
    """
    if collector.funcnamefilter(name) and asyncio.iscoroutinefunction(obj):
        obj = pytest.mark.asyncio(obj)
        return list(collector._genfunctions(name, obj))
