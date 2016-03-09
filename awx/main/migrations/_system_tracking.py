
from awx.fact.models import FactVersion

def migrate_facts(apps, schema_editor):
    Fact = apps.get_model('main', "Fact")
    Host = apps.get_model('main', "Host")

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

    return (migrated_count, not_migrated_count)
