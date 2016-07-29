# Python
import logging
from django.utils.encoding import smart_text

logger = logging.getLogger('rbac_migrations')

def migrate_team(apps, schema_editor):
    '''If an orphan team exists that is still active, delete it.'''
    Team = apps.get_model('main', 'Team')
    for team in Team.objects.iterator():
        if team.organization is None:
            logger.info(smart_text(u"Deleting orphaned team: {}".format(team.name)))
            team.delete()
