import sys

class Logger(object):
    def __init__(self, is_debug=False):
        self.is_debug = is_debug

    def debug(self, *args, **kargs):
        if self.is_debug:
            print(*args, **kargs, file=sys.stderr)

DefaultLogger = Logger()

def debug(*args, **kargs):
    DefaultLogger.debug(*args, **kargs)
