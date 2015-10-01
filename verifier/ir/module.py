class Module(object):
    def __init__(self, name):
        self.name = name
        self.functions = []

    def add_function(self, func):
        self.functions.append(func)
