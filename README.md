# asyncpgsa
A python library wrapper around asyncpg for use with sqlalchemy

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
