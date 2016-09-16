

class Record:
    __slots__ = ('row',)

    def __str__(self):
        return str(self.row)

    def __init__(self, row):
        self.row = row

    def __getattr__(self, item):
        try:
            return self.row[item]
        except KeyError:
            raise AttributeError("'Row' object has no attribute '{}'"
                                 .format(item))

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
