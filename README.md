[![Documentation Status](https://readthedocs.org/projects/asyncpgsa/badge/?version=latest)](http://asyncpgsa.readthedocs.io/en/latest/?badge=latest)

# asyncpgsa
A python library wrapper around asyncpg for use with sqlalchemy

## Backwards incompatibility notice
Since this library is still in pre 1.0 world, the api might change. 
I will do my best to minimize changes, and any changes that get added, 
I will mention here. You should lock the version for production apps.

1. 0.9.0 changed the dialect from psycopg2 to pypostgres. This should be
mostly backwards compatible, but if you notice weird issues, this is why.
You can now plug-in your own dialect using `pg.init(..., dialect=my_dialect)`,
or setting the dialect on the pool. See the top of the connection file 
for an example of creating a dialect. Please let me know if the change from
psycopg2 to pypostgres broke you. If this happens enough, 
I might make psycopg2 the default.

## sqlalchemy ORM

Currently this repo does not support SA ORM, only SA Core.

As we at canopy do not use the ORM, if you would like to have ORM support
feel free to PR it. You would need to create an "engine" interface, and that
should be it. Then you can bind your sessions to the engine.


## sqlalchemy Core

This repo supports sqlalchemy core. Go [here](https://github.com/CanopyTax/asyncpgsa/wiki/Examples) for examples.

## Examples
Go [here](https://github.com/CanopyTax/asyncpgsa/wiki/Examples) for examples.

## install

```bash
pip install asyncpgsa
```


## Contributing
To contribute or build this locally see [contributing.md](https://github.com/CanopyTax/asyncpgsa/blob/master/contributing.md)
