import os
import sys


def get_service_name(argv):
    '''
    Return best-effort guess as to the name of this service
    '''
    for arg in argv:
        if arg == '-m':
            continue
        if 'python' in arg:
            continue
        if 'manage' in arg:
            continue
        if arg.startswith('run_'):
            return arg[len('run_') :]
        return arg


def set_application_name(DATABASES, CLUSTER_HOST_ID, proc_function=''):
    if 'sqlite3' in DATABASES['default']['ENGINE']:
        return
    options_dict = DATABASES['default'].setdefault('OPTIONS', dict())
    if proc_function:
        proc_function = f'_{proc_function}'
    connection_name = f'awx-{os.getpid()}-{get_service_name(sys.argv)}{proc_function}-{CLUSTER_HOST_ID}'[:63]
    options_dict['application_name'] = connection_name
