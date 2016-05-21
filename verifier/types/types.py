#!/usr/bin/env python3

import ast
import copy

# type for isinstance
class Type(object):
    _fields = []

    # for unifier
    @property
    def childs(self):
        return [getattr(self, f) for f in self._fields]

    @property
    def name(self):
        return self.__class__.__name__

    #def __eq__(self, other):
        #if type(self) != type(other):
            #return False
        #else:
            #for v in self._fields:
                #if getattr(self, v) != getattr(other, v):
                    #return False
        #return True

    def dump_fields(self):
        r = []
        for v in self._fields:
            attr = getattr(self, v)
            if isinstance(attr, Type):
                r.append("{0}={1}".format(v, attr.dump()))
            elif isinstance(attr, list):
                r.append("{0}=[{1}]".format(v, ", ".join([a.dump() if isinstance(a, Type) else str(a) for a in attr])))
            else:
                r.append("{0}={1}".format(v, str(attr)))

        return r

    def __repr__(self):
        return self.dump()

    def dump(self):
        return "{0}({1})".format(self.__class__.__name__, ", ".join(self.dump_fields()))

    def copy(self):
        cls = self.__class__
        obj = cls.__new__(cls)
        for v in self._fields:
            attr = getattr(self, v)
            if isinstance(attr, Type):
                attr = attr.copy()
            setattr(obj, v, attr)

        return obj

class Boolean(Type): pass
class String(Type):
    def __init__(self, value=None):
        self.value = value

    def copy(self):
        result = super().copy()
        result.value = self.value
        return result

class Integer(Type): pass
class Iterable(Type):
    _fields = ["subtype"]

    def __init__(self, subtype):
        self.subtype = subtype

class List(Iterable): pass
class Set(Iterable): pass

class Function(Type):
    _fields = ["args", "returntype"]

    def __init__(self, args, returntype):
        self.args = args
        self.returntype = returntype

class Tuple(Type):
    _fields = ["subtypes"]

    def __init__(self, subtypes):
        self.subtypes = subtypes

    @property
    def childs(self):
        return self.subtypes

class Dict(Type):
    _fields = ["keytype", "valuetype"]

    def __init__(self, keytype, valuetype):
        self.keytype = keytype
        self.valuetype = valuetype

# only to be used with return value
class Void(Type): pass

class ProcessClass(Type):
    _fields = []

    def __init__(self, process):
        self.process = process

    def copy(self):
        result = super().copy()
        result.process = self.process
        return result

    @property
    def name(self):
        return "{0}_{1}".format(self.__class__.__name__, self.process.name)

    def dump(self):
        return "{0}({1})".format(self.__class__.__name__, self.process.name)

class Process(Type):
    _fields = ["process_class"]

    def __init__(self, process_class):
        self.process_class = process_class

class ConstantString(Type):
    _fields = []
    def __init__(self, string):
        self.string = string

    @property
    def name(self):
        return "{0}_{1}".format(self.__class__.__name__, self.string)

class Unknown(object):
    _fields = []

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "{Unknown:{0}}".format(self.name)
