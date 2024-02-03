# Install

you will need to clone the directory first, 

then, you need to install dependencies

```
pip install -r dev-requirements.txt
```

and lastly install library as a local dependency

```
pip install -e .
```

You can now use `import asyncpgsa` from other code bases and it will use the
version you have locally

# tests

We use [pytest](https://docs.pytest.org/en/latest/) for tests.

The easiest and recommended way to run test suite is to use `docker compose`:

```
docker compose up --force-recreate --build
```

Otherwise, you need a local postgres running. It can be launched with
`docker compose`:

```
docker compose up -d postgres
docker compose port postgres 5432  # Will echo `0.0.0.0:<port>`
```

Then, the tests can be run locally as:

```
DB_PORT=<port> pytest ./tests
```

Of course if you are running docker in a VM, like on a mac or windows 
you will also have to forward port 5432 from VM to the host.

You can also change the connection info in `tests/__init__.py`

The tests just run generic postgres queries. Nothing is created/deleted, 
so it should be safe if you also have other stuff in your local db.

