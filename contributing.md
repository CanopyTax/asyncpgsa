# Installation

Local development uses `hatch` project manager, please refer to the [docs](https://hatch.pypa.io/)
on how to install it. After you have `hatch` installed, any command you run will
install the dependencies in a virtual environment automatically. You can "force"
the installation by running `hatch run true` in the root of the project.

If you want to test the package against another project, you can install it in
development mode:

```bash
pip install -e /path/to/asyncpgsa
```

You can now use `import asyncpgsa` from other code bases, and it will use the
version you have locally.

# Testing

We use [pytest](https://docs.pytest.org/en/latest/) for tests.

The easiest and recommended way to run test suite is to use `docker compose`:

```
docker compose run --rm lib test
```

Otherwise, you need a local postgres running. It can be launched with
`docker compose`:

```
docker compose up -d postgres
docker compose port postgres 5432  # Will echo `0.0.0.0:<port>`
```

Then, the tests can be run locally as:

```
DB_PORT=<port> hatch run test
```

Of course if you are running docker in a VM, like on a mac or windows 
you will also have to forward port 5432 from VM to the host.

You can also change the connection info in `tests/__init__.py`

The tests just run generic postgres queries. Nothing is created/deleted, 
so it should be safe if you also have other stuff in your local db.

