

class Flag(object):
    def __init__(self, initial):
        self.flag = initial
        self.entered = False
        ast.copy_location()

    def __enter__(self):
        self.flag = not self.flag
        if self.entered:
            raise RuntimeError("Should not be used recursively")
        self.entered = True

    def __exit__(self, type, value, traceback):
        self.flag = not self.flag
        self.entered = False

    def __bool__(self):
        return self.flag
