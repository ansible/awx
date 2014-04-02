def read_to_unicode(obj):
    return [line.decode('utf-8') for line in obj.readlines()]
