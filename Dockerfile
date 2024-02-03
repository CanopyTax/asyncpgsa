# syntax = docker/dockerfile:1.6

FROM python:3.7-slim

WORKDIR /repo/

COPY dev-requirements.txt ./
RUN --mount=type=cache,target=/root/.cache \
    pip install -r dev-requirements.txt

COPY asyncpgsa ./asyncpgsa
COPY docs ./docs
COPY tests ./tests
COPY setup.py ./
RUN pip install -e .
