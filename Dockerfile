# syntax = docker/dockerfile:1.6

FROM python:3.7-slim

WORKDIR /repo/

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git

RUN --mount=type=cache,target=/root/.cache \
    pip install hatch

COPY pyproject.toml README.md ./
# XXX: Can we bypass `.git` requirement from `setuptools-scm` here? Might blow
# up in some envs.
#
# Copied from https://github.com/pypa/setuptools_scm/issues/77#issuecomment-844927695
RUN --mount=type=cache,target=/root/.cache \
    --mount=source=.git,target=.git,type=bind \
    hatch run true  # To sync dependencies

COPY asyncpgsa ./asyncpgsa
COPY docs ./docs
COPY tests ./tests
