from .pool import create_pool
from .pgsingleton import PG
from .connection import compile_query
from .version import __version__

pg = PG()
