# Python
import pytest
from datetime import timedelta

# Django
from django.utils import timezone
from django.conf import settings

# AWX
from awx.fact.models.fact import Fact, FactHost

# MongoEngine
from mongoengine.connection import ConnectionError

@pytest.fixture(autouse=True)
def mongo_db(request):
    marker = request.keywords.get('mongo_db', None)
    if marker:
        # Drop mongo database
        try:
            db = Fact._get_db()
            db.connection.drop_database(settings.MONGO_DB)
        except ConnectionError:
            raise

@pytest.fixture
def inventories(organization):
    def rf(inventory_count=1):
        invs = []
        for i in xrange(0, inventory_count):
            inv = organization.inventories.create(name="test-inv-%d" % i, description="test-inv-desc")
            invs.append(inv)
        return invs
    return rf

'''
hosts naming convension should align with hosts_mongo 
'''
@pytest.fixture
def hosts(organization):
    def rf(host_count=1, inventories=[]):
        hosts = []
        for inv in inventories:
            for i in xrange(0, host_count):
                name = '%s-host-%s' % (inv.name, i)
                host = inv.hosts.create(name=name)
                hosts.append(host)
        return hosts
    return rf

@pytest.fixture
def hosts_mongo(organization):
    def rf(host_count=1, inventories=[]):
        hosts = []
        for inv in inventories:
            for i in xrange(0, host_count):
                name = '%s-host-%s' % (inv.name, i)
                (host, created) = FactHost.objects.get_or_create(hostname=name, inventory_id=inv.id)
                hosts.append(host)
        return hosts
    return rf

@pytest.fixture
def fact_scans(organization, fact_ansible_json, fact_packages_json, fact_services_json):
    def rf(fact_scans=1, inventories=[], timestamp_epoch=timezone.now()):
        facts_json = {}
        facts = []
        module_names = ['ansible', 'services', 'packages']

        facts_json['ansible'] = fact_ansible_json
        facts_json['packages'] = fact_packages_json
        facts_json['services'] = fact_services_json

        for inv in inventories:
            for host_obj in FactHost.objects.filter(inventory_id=inv.id):
                timestamp_current = timestamp_epoch
                for i in xrange(0, fact_scans):
                    for module_name in module_names:
                        facts.append(Fact.add_fact(timestamp_current, facts_json[module_name],  host_obj, module_name))
                    timestamp_current += timedelta(days=1)
        return facts
    return rf


