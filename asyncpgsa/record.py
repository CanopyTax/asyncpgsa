from sqlalchemy import Column

class Record:
    __slots__ = ('row',)

    def __init__(self, row):
        self.row = row

    def __getattr__(self, item):
        try:
            return self.row[item]
        except KeyError:
            try:
                return getattr(self.row, item)
            except AttributeError:
                raise AttributeError("'Row' object has no attribute '{}'"
                                     .format(item))

    def __getitem__(self, key):
        if isinstance(key, Column):
            key = key.name

        return self.row[key]

    def __bool__(self):
        return self.row is not None


class RecordGenerator:
    __slots__ = ('data', 'iter')

    def __init__(self, data):
        self.data = data
        self.iter = iter(data)

    def __iter__(self):
        return self

    def __next__(self):
        return Record(next(self.iter))

    def __bool__(self):
        return bool(self.data)
