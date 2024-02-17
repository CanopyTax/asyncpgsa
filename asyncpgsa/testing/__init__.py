"""
This is for unit testing things that use this library.
This module creates mocks for all the objects used in this library.
"""

from .mockpgsingleton import MockPG
from .mockpool import MockSAPool

__all__ = ["MockPG", "MockSAPool"]
