
import logging

from django.utils.encoding import smart_text
from django.conf import settings

from awx.fact.models import FactVersion
from awx.fact.utils.dbtransform import KeyTransform
from mongoengine.connection import ConnectionError
from pymongo.errors import OperationFailure

logger = logging.getLogger(__name__)

def log_migration(wrapped):
    '''setup the logging mechanism for each migration method
    as it runs, Django resets this, so we use a decorator
    to re-add the handler for each method.
    '''
    handler = logging.FileHandler("/var/log/tower/tower_system_tracking_migrations.log", mode="a", encoding="UTF-8")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    def wrapper(*args, **kwargs):
        logger.handlers = []
        logger.addHandler(handler)
        return wrapped(*args, **kwargs)
    return wrapper

@log_migration
def migrate_facts(apps, schema_editor):
    Fact = apps.get_model('main', "Fact")
    Host = apps.get_model('main', "Host")

    if (not hasattr(settings, 'MONGO_HOST')) or settings.MONGO_HOST == NotImplemented:
        logger.info("failed to find MONGO_HOST in settings. Will NOT attempt to migrate system_tracking data from Mongo to Postgres.")
        # If settings do not specify a mongo database, do not raise error or drop db
        return (0, 0)

    try:
        n = FactVersion.objects.all().count()
    except ConnectionError:
        # Let the user know about the error.  Likely this is
        # a new install and we just don't need to do this
        logger.info(smart_text(u"failed to connect to mongo database host {}. Will NOT attempt to migrate system_tracking data from Mongo to Postgres.".format(settings.MONGO_HOST)))
        return (0, 0)
    except OperationFailure:
        # The database was up but something happened when we tried to query it
        logger.info(smart_text(u"failed to connect to issue Mongo query on host {}. Will NOT attempt to migrate system_tracking data from Mongo to Postgres.".format(settings.MONGO_HOST)))
        return (0, 0)

    migrated_count = 0
    not_migrated_count = 0
    transform = KeyTransform([('.', '\uff0E'), ('$', '\uff04')])
    for factver in FactVersion.objects.all().no_cache():
        try:
            host = Host.objects.only('id').get(inventory__id=factver.host.inventory_id, name=factver.host.hostname)
            fact_obj = transform.replace_outgoing(factver.fact)
            Fact.objects.create(host_id=host.id, timestamp=fact_obj.timestamp, module=fact_obj.module, facts=fact_obj.fact).save()
            migrated_count += 1
        except Host.DoesNotExist:
            # No host was found to migrate the facts to.
            # This isn't a hard error. Just something the user would want to know.
            logger.info(smart_text(u"unable to migrate fact {} <inventory, hostname> not found in Postgres <{}, {}>".format(factver.id, factver.host.inventory_id, factver.host.hostname)))
            not_migrated_count += 1

    logger.info(smart_text(u"successfully migrated {} records of system_tracking data from Mongo to Postgres. {} records not migrated due to corresponding <inventory, hostname> pairs not found in Postgres.".format(migrated_count, not_migrated_count)))
    return (migrated_count, not_migrated_count)

