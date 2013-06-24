from __future__ import absolute_import


import sys

if sys.version_info[0] == 3:
    from multiprocessing import connection
else:
    from billiard import _connection as connection  # noqa

sys.modules[__name__] = connection
