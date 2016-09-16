# Install

you will need to clone the directory first, 

then, you need to install dependencies

```
pip install -r dev-requirements.txt
python setup.py -q install
```

and lastly install library as a local dependency

```
./setup.py develop
```

You can now use `import asyncpgsa` from other code bases and it will use the
version you have locally

# tests

To run the tests you need a local postgres running. The easiest way is 
to use docker-compose

```
docker-compose up -d
```

should do it. Of course if you are running docker in a VM, like on a mac
you will also have to port forward the host 5432 to the VM

You can also change the connection info in `tests/__init__.py`

The tests just run generic postgres queries. Nothing is created/deleted, 
so it should be safe if you also have other stuff in your local db.
