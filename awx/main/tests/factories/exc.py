class NotUnique(Exception):
    def __init__(self, name, objects):
        msg = '{} is not a unique key, found {}={}'.format(name, name, objects[name])
        super(Exception, self).__init__(msg)

