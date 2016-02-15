import pytest
import mock
import json
import os

from datetime import timedelta

from awx.main.models.organization import Organization, Permission
from awx.main.models.base import PERM_INVENTORY_READ
from awx.main.models.ha import Instance
from awx.main.models.fact import Fact

from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings

from rest_framework.test import (
    APIRequestFactory,
    force_authenticate,
)

'''
Disable all django model signals.
'''
@pytest.fixture(scope="session", autouse=False)
def disable_signals():
    mocked = mock.patch('django.dispatch.Signal.send', autospec=True)
    mocked.start()

'''
FIXME: Not sure how "far" just setting the BROKER_URL will get us.
We may need to incluence CELERY's configuration like we do in the old unit tests (see base.py)

Allows django signal code to execute without the need for redis
'''
@pytest.fixture(scope="session", autouse=True)
def celery_memory_broker():
    settings.BROKER_URL='memory://localhost/'

@pytest.fixture
def user():
    def u(name, is_superuser=False):
        try:
            user = User.objects.get(username=name)
        except User.DoesNotExist:
            user = User(username=name, is_superuser=is_superuser, password=name)
            user.save()
        return user
    return u

@pytest.fixture
def post():
    def rf(_cls, _user, _url, pk=None, kwargs={}, middleware=None):
        view = _cls.as_view()
        request = APIRequestFactory().post(_url, kwargs, format='json')
        if middleware:
            middleware.process_request(request)
        force_authenticate(request, user=_user)
        response = view(request, pk=pk)
        if middleware:
            middleware.process_response(request, response)
        return response
    return rf

@pytest.fixture
def get():
    def rf(_cls, _user, _url, pk=None, params={}, middleware=None):
        view = _cls.as_view()
        request = APIRequestFactory().get(_url, params, format='json')
        if middleware:
            middleware.process_request(request)
        force_authenticate(request, user=_user)
        response = view(request, pk=pk)
        if middleware:
            middleware.process_response(request, response)
        return response
    return rf

@pytest.fixture
def options():
    def rf(_cls, _user, _url, pk=None, params={}, middleware=None):
        view = _cls.as_view()
        request = APIRequestFactory().options(_url, params, format='json')
        if middleware:
            middleware.process_request(request)
        force_authenticate(request, user=_user)
        response = view(request, pk=pk)
        if middleware:
            middleware.process_response(request, response)
        return response
    return rf

@pytest.fixture
def instance(settings):
    return Instance.objects.create(uuid=settings.SYSTEM_UUID, primary=True, hostname="instance.example.org")

@pytest.fixture
def organization(instance):
    return Organization.objects.create(name="test-org", description="test-org-desc")

@pytest.fixture
def organizations(instance):
    def rf(organization_count=1):
        orgs = []
        for i in xrange(0, organization_count):
            o = Organization.objects.create(name="test-org-%d" % i, description="test-org-desc")
            orgs.append(o)
        return orgs
    return rf

@pytest.fixture
def inventory(organization):
    return organization.inventories.create(name="test-inv")

@pytest.fixture
def group(inventory):
    return inventory.groups.create(name='group-1')

@pytest.fixture
def hosts(group):
    def rf(host_count=1):
        hosts = []
        for i in xrange(0, host_count):
            name = '%s-host-%s' % (group.name, i)
            (host, created) = group.inventory.hosts.get_or_create(name=name)
            if created:
                group.hosts.add(host)
            hosts.append(host)
        return hosts
    return rf

@pytest.fixture
def fact_scans(group, fact_ansible_json, fact_packages_json, fact_services_json):
    def rf(fact_scans=1, timestamp_epoch=timezone.now()):
        facts_json = {}
        facts = []
        module_names = ['ansible', 'services', 'packages']
        timestamp_current = timestamp_epoch

        facts_json['ansible'] = fact_ansible_json
        facts_json['packages'] = fact_packages_json
        facts_json['services'] = fact_services_json

        for i in xrange(0, fact_scans):
            for host in group.hosts.all():
                for module_name in module_names:
                    facts.append(Fact.objects.create(host=host, timestamp=timestamp_current, module=module_name, facts=facts_json[module_name]))
            timestamp_current += timedelta(days=1)
        return facts
    return rf

def _fact_json(module_name):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    with open('%s/%s.json' % (current_dir, module_name)) as f:
        return json.load(f)

@pytest.fixture
def fact_ansible_json():
    return _fact_json('ansible')

@pytest.fixture
def fact_packages_json():
    return _fact_json('packages')

@pytest.fixture
def fact_services_json():
    return _fact_json('services')

@pytest.fixture
def team(organization):
    return organization.teams.create(name='test-team')

@pytest.fixture
def permission_inv_read(organization, inventory, team):
    return Permission.objects.create(inventory=inventory, team=team, permission_type=PERM_INVENTORY_READ)

