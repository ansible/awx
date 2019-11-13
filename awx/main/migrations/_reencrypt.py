import logging

from awx.conf.migrations._reencrypt import (
    decrypt_field,
)

logger = logging.getLogger('awx.main.migrations')

__all__ = []


def blank_old_start_args(apps, schema_editor):
    UnifiedJob = apps.get_model('main', 'UnifiedJob')
    for uj in UnifiedJob.objects.defer('result_stdout_text').exclude(start_args='').iterator():
        if uj.status in ['running', 'pending', 'new', 'waiting']:
            continue
        try:
            args_dict = decrypt_field(uj, 'start_args')
        except ValueError:
            args_dict = None
        if args_dict == {}:
            continue
        if uj.start_args:
            logger.debug('Blanking job args for %s', uj.pk)
            uj.start_args = ''
            uj.save()
