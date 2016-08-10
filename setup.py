#!/usr/bin/env python3
from setuptools import setup
from asyncpgsa import __version__

setup(
    name='asyncpgsa',
    version=__version__,
    requires=[
        'asyncpg',
        'sqlalchemy',
    ],
    packages=['asyncpgsa'],
    url='https://github.com/canopytax/asyncpgsa',
    license='Apache 2.0',
    author='nhumrich',
    author_email='nick.humrich@canopytax.com',
    description='sqlalchemy support for asyncpg'
)
