import os
import sys


def set_application_name(DATABASES, CLUSTER_HOST_ID, proc_function=''):
    if 'sqlite3' in DATABASES['default']['ENGINE']:
        return
    options_dict = DATABASES['default'].setdefault('OPTIONS', dict())
    if proc_function:
        proc_function = f'-{proc_function}'
    connection_name = f'{os.getpid()}{proc_function}-{CLUSTER_HOST_ID}-{" ".join(sys.argv)}'[:63]
    options_dict['application_name'] = connection_name
