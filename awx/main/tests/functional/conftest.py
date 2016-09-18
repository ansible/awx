
# Python
import pytest
import mock
import json
import os
from datetime import timedelta

# Django
from django.core.urlresolvers import resolve
from django.utils.six.moves.urllib.parse import urlparse
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings

# AWX
from awx.main.models.projects import Project
from awx.main.models.base import PERM_INVENTORY_READ
from awx.main.models.ha import Instance
from awx.main.models.fact import Fact

from rest_framework.test import (
    APIRequestFactory,
    force_authenticate,
)

from awx.main.models.credential import Credential
from awx.main.models.jobs import JobTemplate
from awx.main.models.inventory import (
    Group,
    Inventory,
    InventoryUpdate,
    InventorySource
)
from awx.main.models.organization import (
    Organization,
    Permission,
    Team,
)

from awx.main.models.notifications import (
    NotificationTemplate,
    Notification
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
def check_jobtemplate(project, inventory, credential):
    return \
        JobTemplate.objects.create(
            job_type='check',
            project=project,
            inventory=inventory,
            credential=credential,
            name='check-job-template'
        )

@pytest.fixture
def deploy_jobtemplate(project, inventory, credential):
    return \
        JobTemplate.objects.create(
            job_type='run',
            project=project,
            inventory=inventory,
            credential=credential,
            name='deploy-job-template'
        )

@pytest.fixture
def team(organization):
    return organization.teams.create(name='test-team')

@pytest.fixture
def team_member(user, team):
    ret = user('team-member', False)
    team.member_role.members.add(ret)
    return ret


@pytest.fixture
@mock.patch.object(Project, "update", lambda self, **kwargs: None)
def project(instance, organization):
    prj = Project.objects.create(name="test-proj",
                                 description="test-proj-desc",
                                 organization=organization
                                 )
    return prj

@pytest.fixture
def project_factory(organization):
    def factory(name):
        try:
            prj = Project.objects.get(name=name)
        except Project.DoesNotExist:
            prj = Project.objects.create(name=name,
                                         description="description for " + name,
                                         organization=organization
                                         )
        return prj
    return factory

@pytest.fixture
def job_factory(job_template, admin):
    def factory(job_template=job_template, initial_state='new', created_by=admin):
        return job_template.create_job(created_by=created_by, status=initial_state)
    return factory

@pytest.fixture
def team_factory(organization):
    def factory(name):
        try:
            t = Team.objects.get(name=name)
        except Team.DoesNotExist:
            t = Team.objects.create(name=name,
                                    description="description for " + name,
                                    organization=organization)
        return t
    return factory

@pytest.fixture
def user_project(user):
    owner = user('owner')
    return Project.objects.create(name="test-user-project", created_by=owner, description="test-user-project-desc")

@pytest.fixture
def instance(settings):
    return Instance.objects.create(uuid=settings.SYSTEM_UUID, hostname="instance.example.org")

@pytest.fixture
def organization(instance):
    return Organization.objects.create(name="test-org", description="test-org-desc")

@pytest.fixture
def credential():
    return Credential.objects.create(kind='aws', name='test-cred', username='something', password='secret')

@pytest.fixture
def machine_credential():
    return Credential.objects.create(name='machine-cred', kind='ssh', username='test_user', password='pas4word')

@pytest.fixture
def org_credential(organization):
    return Credential.objects.create(kind='aws', name='test-cred', username='something', password='secret', organization=organization)

@pytest.fixture
def inventory(organization):
    return organization.inventories.create(name="test-inv")

@pytest.fixture
def inventory_factory(organization):
    def factory(name, org=organization):
        try:
            inv = Inventory.objects.get(name=name, organization=org)
        except Inventory.DoesNotExist:
            inv = Inventory.objects.create(name=name, organization=org)
        return inv
    return factory

@pytest.fixture
def label(organization):
    return organization.labels.create(name="test-label", description="test-label-desc")

@pytest.fixture
def notification_template(organization):
    return NotificationTemplate.objects.create(name='test-notification_template',
                                               organization=organization,
                                               notification_type="webhook",
                                               notification_configuration=dict(url="http://localhost",
                                                                               headers={"Test": "Header"}))

@pytest.fixture
def notification(notification_template):
    return Notification.objects.create(notification_template=notification_template,
                                       status='successful',
                                       notifications_sent=1,
                                       notification_type='email',
                                       recipients='admin@redhat.com',
                                       subject='email subject')

@pytest.fixture
def job_template_with_survey_passwords(job_template_with_survey_passwords_factory):
    return job_template_with_survey_passwords_factory(persisted=True)

@pytest.fixture
def admin(user):
    return user('admin', True)

@pytest.fixture
def alice(user):
    return user('alice', False)

@pytest.fixture
def bob(user):
    return user('bob', False)

@pytest.fixture
def rando(user):
    "Rando, the random user that doesn't have access to anything"
    return user('rando', False)

@pytest.fixture
def org_admin(user, organization):
    ret = user('org-admin', False)
    organization.admin_role.members.add(ret)
    organization.member_role.members.add(ret)
    return ret

@pytest.fixture
def org_auditor(user, organization):
    ret = user('org-auditor', False)
    organization.auditor_role.members.add(ret)
    organization.member_role.members.add(ret)
    return ret

@pytest.fixture
def org_member(user, organization):
    ret = user('org-member', False)
    organization.member_role.members.add(ret)
    return ret

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
def group_factory(inventory):
    def g(name):
        try:
            return Group.objects.get(name=name, inventory=inventory)
        except:
            return Group.objects.create(inventory=inventory, name=name)
    return g

@pytest.fixture
def hosts(group_factory):
    group1 = group_factory('group-1')

    def rf(host_count=1):
        hosts = []
        for i in xrange(0, host_count):
            name = '%s-host-%s' % (group1.name, i)
            (host, created) = group1.inventory.hosts.get_or_create(name=name)
            if created:
                group1.hosts.add(host)
            hosts.append(host)
        return hosts
    return rf

@pytest.fixture
def group(inventory):
    return inventory.groups.create(name='single-group')

@pytest.fixture
def inventory_source(group, inventory):
    return InventorySource.objects.create(name=group.name, group=group,
                                          inventory=inventory, source='gce')

@pytest.fixture
def inventory_update(inventory_source):
    return InventoryUpdate.objects.create(inventory_source=inventory_source)

@pytest.fixture
def host(group, inventory):
    return group.hosts.create(name='single-host', inventory=inventory)

@pytest.fixture
def permissions():
    return {
        'admin':{'create':True, 'read':True, 'write':True,
                 'update':True, 'delete':True, 'scm_update':True, 'execute':True, 'use':True,},

        'auditor':{'read':True, 'create':False, 'write':False,
                   'update':False, 'delete':False, 'scm_update':False, 'execute':False, 'use':False,},

        'usage':{'read':False, 'create':False, 'write':False,
                 'update':False, 'delete':False, 'scm_update':False, 'execute':False, 'use':True,},
    }


def _request(verb):
    def rf(url, data_or_user=None, user=None, middleware=None, expect=None, **kwargs):
        if type(data_or_user) is User and user is None:
            user = data_or_user
        elif 'data' not in kwargs:
            kwargs['data'] = data_or_user
        if 'format' not in kwargs:
            kwargs['format'] = 'json'

        view, view_args, view_kwargs = resolve(urlparse(url)[2])
        request = getattr(APIRequestFactory(), verb)(url, **kwargs)
        if middleware:
            middleware.process_request(request)
        if user:
            force_authenticate(request, user=user)

        response = view(request, *view_args, **view_kwargs)
        if middleware:
            middleware.process_response(request, response)
        if expect:
            if response.status_code != expect:
                print(response.data)
            assert response.status_code == expect
        response.render()
        return response
    return rf

@pytest.fixture
def post():
    return _request('post')

@pytest.fixture
def get():
    return _request('get')

@pytest.fixture
def put():
    return _request('put')

@pytest.fixture
def patch():
    return _request('patch')

@pytest.fixture
def delete():
    return _request('delete')

@pytest.fixture
def head():
    return _request('head')

@pytest.fixture
def options():
    return _request('options')



@pytest.fixture
def fact_scans(group_factory, fact_ansible_json, fact_packages_json, fact_services_json):
    group1 = group_factory('group-1')

    def rf(fact_scans=1, timestamp_epoch=timezone.now()):
        facts_json = {}
        facts = []
        module_names = ['ansible', 'services', 'packages']
        timestamp_current = timestamp_epoch

        facts_json['ansible'] = fact_ansible_json
        facts_json['packages'] = fact_packages_json
        facts_json['services'] = fact_services_json

        for i in xrange(0, fact_scans):
            for host in group1.hosts.all():
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
def permission_inv_read(organization, inventory, team):
    return Permission.objects.create(inventory=inventory, team=team, permission_type=PERM_INVENTORY_READ)

@pytest.fixture
def job_template(organization):
    jt = JobTemplate(name='test-job_template')
    jt.save()

    return jt

@pytest.fixture
def job_template_labels(organization, job_template):
    job_template.labels.create(name="label-1", organization=organization)
    job_template.labels.create(name="label-2", organization=organization)

    return job_template

