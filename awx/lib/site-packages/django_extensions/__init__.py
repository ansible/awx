
VERSION = (1, 1, 1)

# Dynamically calculate the version based on VERSION tuple
if len(VERSION) > 2 and VERSION[2] is not None:
    if isinstance(VERSION[2], int):
        str_version = "%s.%s.%s" % VERSION[:3]
    else:
        str_version = "%s.%s_%s" % VERSION[:3]
else:
    str_version = "%s.%s" % VERSION[:2]

__version__ = str_version
