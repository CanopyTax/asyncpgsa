FROM python:3.8-alpine

RUN apk update && \
    apk add \
    gcc \
    musl-dev \
    postgresql-dev

ADD dev-requirements.txt /repo/dev-requirements.txt
RUN pip install -r /repo/dev-requirements.txt

ADD . /repo
