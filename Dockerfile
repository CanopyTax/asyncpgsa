FROM python:3.6-alpine

RUN apk update && \
    apk add \
        gcc \
        musl-dev \
        postgresql-dev

ADD . /repo
RUN pip install -r /repo/dev-requirements.txt
