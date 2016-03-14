
from awx.fact.models import FactVersion
from mongoengine.connection import ConnectionError
from pymongo.errors import OperationFailure
from django.conf import settings

def drop_system_tracking_db():
    try:
        db = FactVersion._get_db()
        db.connection.drop_database(settings.MONGO_DB)
    except ConnectionError:
        # TODO: Log this. Not a deal-breaker. Just let the user know they
        # may need to manually drop/delete the database.
        pass
    except OperationFailure:
        # TODO: This means the database was up but something happened when we tried to query it
        pass

def migrate_facts(apps, schema_editor):
    Fact = apps.get_model('main', "Fact")
    Host = apps.get_model('main', "Host")

    try:
        n = FactVersion.objects.all().count()
    except ConnectionError:
        # TODO: Let the user know about the error.  Likely this is
        # a new install and we just don't need to do this
        return (0, 0)
    except OperationFailure:
        # TODO: This means the database was up but something happened when we tried to query it
        return (0, 0)

    migrated_count = 0
    not_migrated_count = 0
    for factver in FactVersion.objects.all():
        fact_obj = factver.fact 
        try:
            host = Host.objects.only('id').get(inventory__id=factver.host.inventory_id, name=factver.host.hostname)
            Fact.objects.create(host_id=host.id, timestamp=fact_obj.timestamp, module=fact_obj.module, facts=fact_obj.fact).save()
            migrated_count += 1
        except Host.DoesNotExist:
            # TODO: Log this. No host was found to migrate the facts to.
            # This isn't a hard error. Just something the user would want to know.
            not_migrated_count += 1

    drop_system_tracking_db()
    return (migrated_count, not_migrated_count)
