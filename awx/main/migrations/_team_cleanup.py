# Python
import logging
from django.utils.encoding import smart_text

logger = logging.getLogger(__name__)

def log_migration(wrapped):
    '''setup the logging mechanism for each migration method
    as it runs, Django resets this, so we use a decorator
    to re-add the handler for each method.
    '''
    handler = logging.FileHandler("/tmp/tower_rbac_migrations.log", mode="a", encoding="UTF-8")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    def wrapper(*args, **kwargs):
        logger.handlers = []
        logger.addHandler(handler)
        return wrapped(*args, **kwargs)
    return wrapper

@log_migration
def migrate_team(apps, schema_editor):
    '''If an orphan team exists that is still active, delete it.'''
    Team = apps.get_model('main', 'Team')
    for team in Team.objects.iterator():
        if team.organization is None:
            logger.info(smart_text(u"Deleting orphaned team: {}".format(team.name)))
            team.delete()
