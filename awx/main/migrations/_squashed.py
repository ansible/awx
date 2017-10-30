from itertools import chain
from django.db import (
    connection,
    migrations,
)


def squash_data(SQUASHED):
    '''Returns a tuple of the squashed_keys and the key position to begin
    processing replace and operation lists'''

    cm = current_migration()
    squashed_keys = sorted(SQUASHED.keys())
    try:
        if cm is None:
            key_index = 0
        else:
            key_index = squashed_keys.index(cm.name) + 1
    except ValueError:
        key_index = 0
    return squashed_keys, key_index


def current_migration():
    '''Get the latest migration non-squashed migration'''
    try:
        recorder = migrations.recorder.MigrationRecorder(connection)
        return recorder.migration_qs.filter(app='main').exclude(name__contains='squashed').latest('id')
    except recorder.Migration.DoesNotExist:
        return None


def replaces(SQUASHED):
    '''Build a list of replacement migrations based on the most recent non-squashed migration
    and the provided list of SQUASHED migrations. If the most recent non-squashed migration
    is not present anywhere in the SQUASHED dictionary, assume they have all been applied.
    '''
    squashed_keys, key_index = squash_data(SQUASHED)
    return [(b'main', key) for key in squashed_keys[key_index:]]


def operations(SQUASHED):
    '''Build a list of migration operations based on the most recent non-squashed migration
    and the provided list of SQUASHED migrations. If the most recent non-squashed migration
    is not present anywhere in the SQUASHED dictionary, assume they have all been applied.
    '''
    squashed_keys, key_index = squash_data(SQUASHED)
    op_keys = squashed_keys[key_index:]
    ops = [SQUASHED[op_key] for op_key in op_keys]
    return [op for op in chain.from_iterable(ops)]
