import collections
from reprlib import recursive_repr as _recursive_repr

class ObjectDictionary(collections.OrderedDict):
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
        super().__init__()
        self.__update(*args, **kwds)

    def __setitem__(self, key, value):
        super().__setitem__(ObjectDictionary.Wrapper(key), value)

    def __getitem__(self, key):
        try:
            return super().__getitem__(ObjectDictionary.Wrapper(key))
        except KeyError:
            raise KeyError(key)

    def __delitem__(self, key):
        super().__delitem__(ObjectDictionary.Wrapper(key))

    def __contains__(self, key):
        return super().__contains__(ObjectDictionary.Wrapper(key))

    def __iter__(self):
        i = super().__iter__()
        for w in i:
            yield w.obj

    def popitem(self):
        (k, v) = super().popitem()
        return (k.obj, v)

    def keys(self,):
        """! getsListOfKeys !"""
        for k in super().keys():
            yield k.obj
    def pop(self, key):
        if key in self:
            result = self[key]
            del self[key]
            return result
        raise KeyError(key)

    def items(self):
        for (k, v) in super().items():
            yield (k, v)

    @_recursive_repr()
    def __repr__(self):
        'od.__repr__() <==> repr(od)'
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self.items()))

    update = __update = collections.MutableMapping.update
