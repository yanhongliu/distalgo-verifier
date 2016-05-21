import collections

class ObjectDictionary(collections.MutableMapping):
    class Wrapper(object):
        def __init__(self, obj):
            self.obj = obj

        def __hash__(self):
            return id(self.obj)

        def __eq__(self, other):
            if isinstance(other, ObjectDictionary.Wrapper):
                return other.obj is self.obj
            return False

    def __init__(self, *args, **kwds):
        self.store = collections.OrderedDict()
        self.update(collections.OrderedDict(*args, **kwds))

    def __setitem__(self, key, value):
        self.store[ObjectDictionary.Wrapper(key)] = value

    def __getitem__(self, key):
        try:
            return self.store[ObjectDictionary.Wrapper(key)]
        except KeyError:
            raise KeyError(key)

    def __delitem__(self, key):
        del self.store[ObjectDictionary.Wrapper(key)]

    def __iter__(self):
        i = iter(self.store)
        for w in i:
            yield w.obj

    def __len__(self):
        return len(self.store)
