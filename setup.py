#!/usr/bin/env python3
from setuptools import setup

version = {}

with open('asyncpgsa/version.py') as f:
    exec(f.read(), version)

setup(
    name='asyncpgsa',
    version=version['__version__'],
    install_requires=[
        'asyncpg',
        'sqlalchemy',
    ],
    packages=['asyncpgsa', 'asyncpgsa.testing'],
    url='https://github.com/canopytax/asyncpgsa',
    license='Apache 2.0',
    author='nhumrich',
    author_email='nick.humrich@canopytax.com',
    description='sqlalchemy support for asyncpg'
)
