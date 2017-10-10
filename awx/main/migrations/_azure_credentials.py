import logging

from django.db.models import Q

logger = logging.getLogger('awx.main.migrations')


def remove_azure_credentials(apps, schema_editor):
    '''Azure is not supported as of 3.2 and greater. Instead, azure_rm is
    supported.
    '''
    Credential = apps.get_model('main', 'Credential')
    logger.debug("Removing all Azure Credentials from database.")
    Credential.objects.filter(kind='azure').delete()

