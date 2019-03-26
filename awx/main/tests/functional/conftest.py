# Python
import pytest
from unittest import mock
import json
import os
import tempfile
import shutil
import urllib.parse
from datetime import timedelta
from unittest.mock import PropertyMock

# Django
from django.core.urlresolvers import resolve
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db.backends.sqlite3.base import SQLiteCursorWrapper
from jsonbfield.fields import JSONField

# AWX
from awx.main.models.projects import Project
from awx.main.models.ha import Instance
from awx.main.models.fact import Fact

from rest_framework.test import (
    APIRequestFactory,
    force_authenticate,
)

from awx.main.models.credential import CredentialType, Credential
from awx.main.models.jobs import JobTemplate, SystemJobTemplate
from awx.main.models.inventory import (
    Group,
    Inventory,
    InventoryUpdate,
    InventorySource,
    CustomInventoryScript
)
from awx.main.models.organization import (
    Organization,
    Team,
)
from awx.main.models.rbac import Role
from awx.main.models.notifications import (
    NotificationTemplate,
    Notification
)
from awx.main.models.events import (
    JobEvent,
    AdHocCommandEvent,
    ProjectUpdateEvent,
    InventoryUpdateEvent,
    SystemJobEvent,
)
from awx.main.models.workflow import WorkflowJobTemplate
from awx.main.models.ad_hoc_commands import AdHocCommand
from awx.main.models.oauth import OAuth2Application as Application

__SWAGGER_REQUESTS__ = {}


@pytest.fixture(scope="session")
def swagger_autogen(requests=__SWAGGER_REQUESTS__):
    return requests


@pytest.fixture
def user():
    def u(name, is_superuser=False):
        try:
            user = User.objects.get(username=name)
        except User.DoesNotExist:
            user = User(username=name, is_superuser=is_superuser)
            user.set_password(name)
            user.save()
        return user
    return u


@pytest.fixture
def check_jobtemplate(project, inventory, credential):
    jt = JobTemplate.objects.create(
        job_type='check',
        project=project,
        inventory=inventory,
        name='check-job-template'
    )
    jt.credentials.add(credential)
    return jt


@pytest.fixture
def deploy_jobtemplate(project, inventory, credential):
    jt = JobTemplate.objects.create(
        job_type='run',
        project=project,
        inventory=inventory,
        name='deploy-job-template'
    )
    jt.credentials.add(credential)
    return jt


@pytest.fixture
def team(organization):
    return organization.teams.create(name='test-team')


@pytest.fixture
def team_member(user, team):
    ret = user('team-member', False)
    team.member_role.members.add(ret)
    return ret


@pytest.fixture(scope="session", autouse=True)
def project_playbooks():
    '''
    Return playbook_files as playbooks for manual projects when testing.
    '''
    class PlaybooksMock(mock.PropertyMock):
        def __get__(self, obj, obj_type):
            return obj.playbook_files
    mocked = mock.patch.object(Project, 'playbooks', new_callable=PlaybooksMock)
    mocked.start()


@pytest.fixture
@mock.patch.object(Project, "update", lambda self, **kwargs: None)
def project(instance, organization):
    prj = Project.objects.create(name="test-proj",
                                 description="test-proj-desc",
                                 organization=organization,
                                 playbook_files=['helloworld.yml', 'alt-helloworld.yml'],
                                 local_path='_92__test_proj',
                                 scm_revision='1234567890123456789012345678901234567890',
                                 scm_url='localhost',
                                 scm_type='git'
                                 )
    return prj


@pytest.fixture
@mock.patch.object(Project, "update", lambda self, **kwargs: None)
def manual_project(instance, organization):
    prj = Project.objects.create(name="test-manual-proj",
                                 description="manual-proj-desc",
                                 organization=organization,
                                 playbook_files=['helloworld.yml', 'alt-helloworld.yml'],
                                 local_path='_92__test_proj'
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
        return job_template.create_unified_job(_eager_fields={
            'status': initial_state, 'created_by': created_by})
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
def insights_project():
    return Project.objects.create(name="test-insights-project", scm_type="insights")


@pytest.fixture
def instance(settings):
    return Instance.objects.create(uuid=settings.SYSTEM_UUID, hostname="instance.example.org", capacity=100)


@pytest.fixture
def organization(instance):
    return Organization.objects.create(name="test-org", description="test-org-desc")


@pytest.fixture
def credentialtype_ssh():
    ssh = CredentialType.defaults['ssh']()
    ssh.save()
    return ssh


@pytest.fixture
def credentialtype_aws():
    aws = CredentialType.defaults['aws']()
    aws.save()
    return aws


@pytest.fixture
def credentialtype_net():
    net = CredentialType.defaults['net']()
    net.save()
    return net


@pytest.fixture
def credentialtype_vault():
    vault_type = CredentialType.defaults['vault']()
    vault_type.save()
    return vault_type


@pytest.fixture
def credentialtype_scm():
    scm_type = CredentialType.defaults['scm']()
    scm_type.save()
    return scm_type


@pytest.fixture
def credentialtype_insights():
    insights_type = CredentialType.defaults['insights']()
    insights_type.save()
    return insights_type


@pytest.fixture
def credential(credentialtype_aws):
    return Credential.objects.create(credential_type=credentialtype_aws, name='test-cred',
                                     inputs={'username': 'something', 'password': 'secret'})


@pytest.fixture
def net_credential(credentialtype_net):
    return Credential.objects.create(credential_type=credentialtype_net, name='test-cred',
                                     inputs={'username': 'something', 'password': 'secret'})


@pytest.fixture
def vault_credential(credentialtype_vault):
    return Credential.objects.create(credential_type=credentialtype_vault, name='test-cred',
                                     inputs={'vault_password': 'secret'})


@pytest.fixture
def machine_credential(credentialtype_ssh):
    return Credential.objects.create(credential_type=credentialtype_ssh, name='machine-cred',
                                     inputs={'username': 'test_user', 'password': 'pas4word'})


@pytest.fixture
def scm_credential(credentialtype_scm):
    return Credential.objects.create(credential_type=credentialtype_scm, name='scm-cred',
                                     inputs={'username': 'optimus', 'password': 'prime'})


@pytest.fixture
def insights_credential(credentialtype_insights):
    return Credential.objects.create(credential_type=credentialtype_insights, name='insights-cred',
                                     inputs={'username': 'morocco_mole', 'password': 'secret_squirrel'})


@pytest.fixture
def org_credential(organization, credentialtype_aws):
    return Credential.objects.create(credential_type=credentialtype_aws, name='test-cred',
                                     inputs={'username': 'something', 'password': 'secret'},
                                     organization=organization)


@pytest.fixture
def inventory(organization):
    return organization.inventories.create(name="test-inv")


@pytest.fixture
def insights_inventory(inventory):
    inventory.scm_type = 'insights'
    inventory.save()
    return inventory


@pytest.fixture
def scm_inventory_source(inventory, project):
    inv_src = InventorySource(
        name="test-scm-inv",
        source_project=project,
        source='scm',
        source_path='inventory_file',
        update_on_project_update=True,
        inventory=inventory,
        scm_last_revision=project.scm_revision)
    with mock.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.update'):
        inv_src.save()
    return inv_src


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
def notification_template_with_encrypt(organization):
    return NotificationTemplate.objects.create(name='test-notification_template_with_encrypt',
                                               organization=organization,
                                               notification_type="slack",
                                               notification_configuration=dict(channels=["Foo", "Bar"],
                                                                               token="token"))


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
def system_auditor(user):
    u = user('an-auditor', False)
    Role.singleton('system_auditor').members.add(u)
    return u


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
        for i in range(0, organization_count):
            o = Organization.objects.create(name="test-org-%d" % i, description="test-org-desc")
            orgs.append(o)
        return orgs
    return rf


@pytest.fixture
def group_factory(inventory):
    def g(name):
        try:
            return Group.objects.get(name=name, inventory=inventory)
        except Exception:
            return Group.objects.create(inventory=inventory, name=name)
    return g


@pytest.fixture
def hosts(group_factory):
    group1 = group_factory('group-1')

    def rf(host_count=1):
        hosts = []
        for i in range(0, host_count):
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
def inventory_source(inventory):
    # by making it ec2, the credential is not required
    return InventorySource.objects.create(name='single-inv-src',
                                          inventory=inventory, source='ec2')


@pytest.fixture
def inventory_source_factory(inventory_factory):
    def invsrc(name, source=None, inventory=None):
        if inventory is None:
            inventory = inventory_factory("inv-is-%s" % name)
        if source is None:
            source = 'file'
        try:
            return inventory.inventory_sources.get(name=name)
        except Exception:
            return inventory.inventory_sources.create(name=name, source=source)
    return invsrc


@pytest.fixture
def inventory_update(inventory_source):
    return InventoryUpdate.objects.create(inventory_source=inventory_source)


@pytest.fixture
def inventory_script(organization):
    return CustomInventoryScript.objects.create(name='test inv script',
                                                organization=organization,
                                                script='#!/usr/bin/python')


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
        if 'format' not in kwargs and 'content_type' not in kwargs:
            kwargs['format'] = 'json'

        view, view_args, view_kwargs = resolve(urllib.parse.urlparse(url)[2])
        request = getattr(APIRequestFactory(), verb)(url, **kwargs)
        if isinstance(kwargs.get('cookies', None), dict):
            for key, value in kwargs['cookies'].items():
                request.COOKIES[key] = value
        if middleware:
            middleware.process_request(request)
        if user:
            force_authenticate(request, user=user)

        response = view(request, *view_args, **view_kwargs)
        if middleware:
            middleware.process_response(request, response)
        if expect:
            if response.status_code != expect:
                if getattr(response, 'data', None):
                    try:
                        data_copy = response.data.copy()
                        # Make translated strings printable
                        for key, value in response.data.items():
                            if isinstance(value, list):
                                response.data[key] = []
                                for item in value:
                                    response.data[key].append(str(item))
                            else:
                                response.data[key] = str(value)
                    except Exception:
                        response.data = data_copy
            assert response.status_code == expect, 'Response data: {}'.format(
                getattr(response, 'data', None)
            )
        if hasattr(response, 'render'):
            response.render()
        __SWAGGER_REQUESTS__.setdefault(request.path, {})[
            (request.method.lower(), response.status_code)
        ] = (response.get('Content-Type', None), response.content, kwargs.get('data'))
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

        for i in range(0, fact_scans):
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
def ad_hoc_command_factory(inventory, machine_credential, admin):
    def factory(inventory=inventory, credential=machine_credential, initial_state='new', created_by=admin):
        adhoc = AdHocCommand(
            name='test-adhoc', inventory=inventory, credential=credential,
            status=initial_state, created_by=created_by
        )
        adhoc.save()
        return adhoc
    return factory


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


@pytest.fixture
def jt_linked(job_template_factory, credential, net_credential, vault_credential):
    '''
    A job template with a reasonably complete set of related objects to
    test RBAC and other functionality affected by related objects
    '''
    objects = job_template_factory(
        'testJT', organization='org1', project='proj1', inventory='inventory1',
        credential='cred1')
    jt = objects.job_template
    jt.credentials.add(vault_credential)
    jt.save()
    # Add AWS cloud credential and network credential
    jt.credentials.add(credential)
    jt.credentials.add(net_credential)
    return jt


@pytest.fixture
def workflow_job_template(organization):
    wjt = WorkflowJobTemplate(name='test-workflow_job_template', organization=organization)
    wjt.save()

    return wjt


@pytest.fixture
def workflow_job_factory(workflow_job_template, admin):
    def factory(workflow_job_template=workflow_job_template, initial_state='new', created_by=admin):
        return workflow_job_template.create_unified_job(_eager_fields={
            'status': initial_state, 'created_by': created_by})
    return factory


@pytest.fixture
def system_job_template():
    sys_jt = SystemJobTemplate(name='test-system_job_template', job_type='cleanup_jobs')
    sys_jt.save()
    return sys_jt


@pytest.fixture
def system_job_factory(system_job_template, admin):
    def factory(system_job_template=system_job_template, initial_state='new', created_by=admin):
        return system_job_template.create_unified_job(_eager_fields={
            'status': initial_state, 'created_by': created_by})
    return factory


def dumps(value):
    return DjangoJSONEncoder().encode(value)


# Taken from https://github.com/django-extensions/django-extensions/blob/54fe88df801d289882a79824be92d823ab7be33e/django_extensions/db/fields/json.py
def get_db_prep_save(self, value, connection, **kwargs):
    """Convert our JSON object to a string before we save"""
    if value is None and self.null:
        return None
    # default values come in as strings; only non-strings should be
    # run through `dumps`
    if not isinstance(value, str):
        value = dumps(value)

    return value


@pytest.fixture
def monkeypatch_jsonbfield_get_db_prep_save(mocker):
    JSONField.get_db_prep_save = get_db_prep_save


@pytest.fixture
def oauth_application(admin):
    return Application.objects.create(
        name='test app', user=admin, client_type='confidential',
        authorization_grant_type='password'
    )


@pytest.fixture
def sqlite_copy_expert(request):
    # copy_expert is postgres-specific, and SQLite doesn't support it; mock its
    # behavior to test that it writes a file that contains stdout from events
    path = tempfile.mkdtemp(prefix='job-event-stdout')

    def write_stdout(self, sql, fd):
        # simulate postgres copy_expert support with ORM code
        parts = sql.split(' ')
        tablename = parts[parts.index('from') + 1]
        for cls in (JobEvent, AdHocCommandEvent, ProjectUpdateEvent,
                    InventoryUpdateEvent, SystemJobEvent):
            if cls._meta.db_table == tablename:
                for event in cls.objects.order_by('start_line').all():
                    fd.write(event.stdout)

    setattr(SQLiteCursorWrapper, 'copy_expert', write_stdout)
    request.addfinalizer(lambda: shutil.rmtree(path))
    request.addfinalizer(lambda: delattr(SQLiteCursorWrapper, 'copy_expert'))
    return path


@pytest.fixture
def disable_database_settings(mocker):
    m = mocker.patch('awx.conf.settings.SettingsWrapper.all_supported_settings', new_callable=PropertyMock)
    m.return_value = []


@pytest.fixture
def slice_jt_factory(inventory):
    def r(N, jt_kwargs=None):
        for i in range(N):
            inventory.hosts.create(name='foo{}'.format(i))
        if not jt_kwargs:
            jt_kwargs = {}
        return JobTemplate.objects.create(
            name='slice-jt-from-factory',
            job_slice_count=N,
            inventory=inventory,
            **jt_kwargs
        )
    return r


@pytest.fixture
def slice_job_factory(slice_jt_factory):
    def r(N, jt_kwargs=None, prompts=None, spawn=False):
        slice_jt = slice_jt_factory(N, jt_kwargs=jt_kwargs)
        if not prompts:
            prompts = {}
        slice_job = slice_jt.create_unified_job(**prompts)
        if spawn:
            for node in slice_job.workflow_nodes.all():
                # does what the task manager does for spawning workflow jobs
                kv = node.get_job_kwargs()
                job = node.unified_job_template.create_unified_job(**kv)
                node.job = job
                node.save()
        return slice_job
    return r
