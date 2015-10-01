class Logger(object):
    def __init__(self, is_debug=False):
        self.is_debug = is_debug

    def debug(self, msg):
        if self.is_debug:
            print(msg)
