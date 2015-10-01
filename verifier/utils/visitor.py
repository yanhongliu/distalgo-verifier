import collections

def iter_fields(node, _fields=None):
    """
    Yield a tuple of ``(fieldname, value)`` for each field in ``node._fields``
    that is present on *node*.
    """
    fields = node._fields if _fields is None else _fields
    for field in fields:
        try:
            value = getattr(node, field)
            if value is not None:
                yield field, value
        except AttributeError:
            pass

class NodeVisitor(object):
    _nodebaseclass = object

    @classmethod
    def run(cls, node, *args, **kargs):
        visitor = cls(*args, **kargs)
        result = visitor.visit(node)

        result = visitor.post_run(result)

        if hasattr(visitor, "_result"):
            if isinstance(visitor._result, str):
                return getattr(visitor, visitor._result)
            elif isinstance(visitor._result, list) or isinstance(visitor._result, tuple):
                return type(visitor._result)([getattr(visitor, r) for r in visitor._result])
            else:
                raise RuntimeError()
        elif hasattr(visitor, "result"):
            return visitor.result
        else:
            return result

    def post_run(self, result):
        return result

    def visit(self, node):
        """Visit a node."""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        for field, value in iter_fields(node):
            self.visit_one_value(value)

    def visit_one_value(self, value):
        if isinstance(value, list):
            return [self.visit(item) if isinstance(item, self._nodebaseclass) else None for item in value]
        elif isinstance(value, self._nodebaseclass):
            return self.visit(value)
        return None

    def visit_one_field(self, node, field):
        self.visit_some_fields(self, node, [field])

    def visit_other_fields(self, node, fields):
        for field, value in iter_fields(node, [f for f in node._fields if f not in fields]):
            self.visit_one_value(value)

    def visit_some_fields(self, node, fields):
        for field, value in iter_fields(node, fields):
            self.visit_one_value(value)

class NodeDump(NodeVisitor):
    def __init__(self, baseclass=object):
        super().__init__()
        self.indent = 0
        self._nodebaseclass = baseclass

    def visit(self, node):
        shortindstr = ("  " * (self.indent))
        indstr = ("  " * (self.indent + 1))
        self.indent += 2
        print("%s%s:{" % (shortindstr, node.__class__.__name__))
        for field, value in iter_fields(node):
            if isinstance(value, str):
                print("%s%s: %s" % (indstr, field, value))
            else:
                print("%s%s:" % (indstr, field))
                self.visit_one_value(value)
                # print("%s" % str(value))
        print("%s}" % shortindstr)

        self.indent -= 2

class NodeTransformer(NodeVisitor):

    def generic_visit(self, node):
        for field, old_value in iter_fields(node):
            old_value = getattr(node, field, None)
            if isinstance(old_value, list):
                new_values = []
                for value in old_value:
                    if isinstance(value, self._nodebaseclass):
                        value = self.visit(value)
                        if value is None:
                            continue
                        elif not isinstance(value, self._nodebaseclass):
                            new_values.extend(value)
                            continue
                    new_values.append(value)
                old_value[:] = new_values
            elif isinstance(old_value, self._nodebaseclass):
                new_node = self.visit(old_value)
                if new_node is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_node)
        return node
