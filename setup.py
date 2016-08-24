#!/usr/bin/env python3
from setuptools import setup

setup(
    name='asyncpgsa',
    version='0.5.0',
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
