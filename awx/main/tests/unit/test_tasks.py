# -*- coding: utf-8 -*-

import configparser
import json
import os
import shutil
import tempfile

from backports.tempfile import TemporaryDirectory
import fcntl
from unittest import mock
import pytest
import yaml
import jinja2

from django.conf import settings

from awx.main.models import (
    AdHocCommand,
    Credential,
    CredentialType,
    Inventory,
    InventorySource,
    InventoryUpdate,
    Job,
    JobTemplate,
    Notification,
    Organization,
    Project,
    ProjectUpdate,
    UnifiedJob,
    User,
    CustomInventoryScript,
    build_safe_env
)
from awx.main.models.credential import ManagedCredentialType

from awx.main import tasks
from awx.main.utils import encrypt_field, encrypt_value
from awx.main.utils.safe_yaml import SafeLoader

from awx.main.utils.licensing import Licenser


class TestJobExecution(object):
    EXAMPLE_PRIVATE_KEY = '-----BEGIN PRIVATE KEY-----\nxyz==\n-----END PRIVATE KEY-----'


@pytest.fixture
def private_data_dir():
    private_data = tempfile.mkdtemp(prefix='awx_')
    yield private_data
    shutil.rmtree(private_data, True)


@pytest.fixture
def patch_Job():
    with mock.patch.object(Job, 'cloud_credentials') as mock_cred:
        mock_cred.__get__ = lambda *args, **kwargs: []
        with mock.patch.object(Job, 'network_credentials') as mock_net:
            mock_net.__get__ = lambda *args, **kwargs: []
            yield


@pytest.fixture
def patch_Organization():
    _credentials = []
    credentials_mock = mock.Mock(**{
        'all': lambda: _credentials,
        'add': _credentials.append,
        'exists': lambda: len(_credentials) > 0,
        'spec_set': ['all', 'add', 'exists'],
    })
    with mock.patch.object(Organization, 'galaxy_credentials', credentials_mock):
        yield


@pytest.fixture
def job():
    return Job(
        pk=1, id=1,
        project=Project(local_path='/projects/_23_foo'),
        inventory=Inventory(), job_template=JobTemplate(id=1, name='foo'))


@pytest.fixture
def adhoc_job():
    return AdHocCommand(pk=1, id=1, inventory=Inventory())


@pytest.fixture
def update_model_wrapper(job):
    def fn(pk, **kwargs):
        for k, v in kwargs.items():
            setattr(job, k, v)
        return job
    return fn


@pytest.fixture
def adhoc_update_model_wrapper(adhoc_job):
    def fn(pk, **kwargs):
        for k, v in kwargs.items():
            setattr(adhoc_job, k, v)
        return adhoc_job
    return fn


def test_send_notifications_not_list():
    with pytest.raises(TypeError):
        tasks.send_notifications(None)


def test_send_notifications_job_id(mocker):
    with mocker.patch('awx.main.models.UnifiedJob.objects.get'):
        tasks.send_notifications([], job_id=1)
        assert UnifiedJob.objects.get.called
        assert UnifiedJob.objects.get.called_with(id=1)


def test_work_success_callback_missing_job():
    task_data = {'type': 'project_update', 'id': 9999}
    with mock.patch('django.db.models.query.QuerySet.get') as get_mock:
        get_mock.side_effect = ProjectUpdate.DoesNotExist()
        assert tasks.handle_work_success(task_data) is None


@mock.patch('awx.main.models.UnifiedJob.objects.get')
@mock.patch('awx.main.models.Notification.objects.filter')
def test_send_notifications_list(mock_notifications_filter, mock_job_get, mocker):
    mock_job = mocker.MagicMock(spec=UnifiedJob)
    mock_job_get.return_value = mock_job
    mock_notifications = [mocker.MagicMock(spec=Notification, subject="test", body={'hello': 'world'})]
    mock_notifications_filter.return_value = mock_notifications

    tasks.send_notifications([1,2], job_id=1)
    assert Notification.objects.filter.call_count == 1
    assert mock_notifications[0].status == "successful"
    assert mock_notifications[0].save.called

    assert mock_job.notifications.add.called
    assert mock_job.notifications.add.called_with(*mock_notifications)


@pytest.mark.parametrize("key,value", [
    ('REST_API_TOKEN', 'SECRET'),
    ('SECRET_KEY', 'SECRET'),
    ('VMWARE_PASSWORD', 'SECRET'),
    ('API_SECRET', 'SECRET'),
    ('ANSIBLE_GALAXY_SERVER_PRIMARY_GALAXY_TOKEN', 'SECRET'),
])
def test_safe_env_filtering(key, value):
    assert build_safe_env({key: value})[key] == tasks.HIDDEN_PASSWORD


def test_safe_env_returns_new_copy():
    env = {'foo': 'bar'}
    assert build_safe_env(env) is not env


@pytest.mark.parametrize("source,expected", [
    (None, True), (False, False), (True, True)
])
def test_openstack_client_config_generation(mocker, source, expected, private_data_dir):
    update = tasks.RunInventoryUpdate()
    credential_type = CredentialType.defaults['openstack']()
    inputs = {
        'host': 'https://keystone.openstack.example.org',
        'username': 'demo',
        'password': 'secrete',
        'project': 'demo-project',
        'domain': 'my-demo-domain'
    }
    if source is not None:
        inputs['verify_ssl'] = source
    credential = Credential(pk=1, credential_type=credential_type, inputs=inputs)

    inventory_update = mocker.Mock(**{
        'source': 'openstack',
        'source_vars_dict': {},
        'get_cloud_credential': mocker.Mock(return_value=credential),
        'get_extra_credentials': lambda x: [],
        'ansible_virtualenv_path': '/venv/foo'
    })
    cloud_config = update.build_private_data(inventory_update, private_data_dir)
    cloud_credential = yaml.safe_load(
        cloud_config.get('credentials')[credential]
    )
    assert cloud_credential['clouds'] == {
        'devstack': {
            'auth': {
                'auth_url': 'https://keystone.openstack.example.org',
                'password': 'secrete',
                'project_name': 'demo-project',
                'username': 'demo',
                'domain_name': 'my-demo-domain',
            },
            'verify': expected,
            'private': True,
        }
    }


@pytest.mark.parametrize("source,expected", [
    (None, True), (False, False), (True, True)
])
def test_openstack_client_config_generation_with_project_domain_name(mocker, source, expected, private_data_dir):
    update = tasks.RunInventoryUpdate()
    credential_type = CredentialType.defaults['openstack']()
    inputs = {
        'host': 'https://keystone.openstack.example.org',
        'username': 'demo',
        'password': 'secrete',
        'project': 'demo-project',
        'domain': 'my-demo-domain',
        'project_domain_name': 'project-domain',
    }
    if source is not None:
        inputs['verify_ssl'] = source
    credential = Credential(pk=1, credential_type=credential_type, inputs=inputs)

    inventory_update = mocker.Mock(**{
        'source': 'openstack',
        'source_vars_dict': {},
        'get_cloud_credential': mocker.Mock(return_value=credential),
        'get_extra_credentials': lambda x: [],
        'ansible_virtualenv_path': '/venv/foo'
    })
    cloud_config = update.build_private_data(inventory_update, private_data_dir)
    cloud_credential = yaml.safe_load(
        cloud_config.get('credentials')[credential]
    )
    assert cloud_credential['clouds'] == {
        'devstack': {
            'auth': {
                'auth_url': 'https://keystone.openstack.example.org',
                'password': 'secrete',
                'project_name': 'demo-project',
                'username': 'demo',
                'domain_name': 'my-demo-domain',
                'project_domain_name': 'project-domain',
            },
            'verify': expected,
            'private': True,
        }
    }


@pytest.mark.parametrize("source,expected", [
    (False, False), (True, True)
])
def test_openstack_client_config_generation_with_private_source_vars(mocker, source, expected, private_data_dir):
    update = tasks.RunInventoryUpdate()
    credential_type = CredentialType.defaults['openstack']()
    inputs = {
        'host': 'https://keystone.openstack.example.org',
        'username': 'demo',
        'password': 'secrete',
        'project': 'demo-project',
        'domain': None,
        'verify_ssl': True,
    }
    credential = Credential(pk=1, credential_type=credential_type, inputs=inputs)

    inventory_update = mocker.Mock(**{
        'source': 'openstack',
        'source_vars_dict': {'private': source},
        'get_cloud_credential': mocker.Mock(return_value=credential),
        'get_extra_credentials': lambda x: [],
        'ansible_virtualenv_path': '/venv/foo'
    })
    cloud_config = update.build_private_data(inventory_update, private_data_dir)
    cloud_credential = yaml.load(
        cloud_config.get('credentials')[credential], Loader=SafeLoader
    )
    assert cloud_credential['clouds'] == {
        'devstack': {
            'auth': {
                'auth_url': 'https://keystone.openstack.example.org',
                'password': 'secrete',
                'project_name': 'demo-project',
                'username': 'demo'
            },
            'verify': True,
            'private': expected
        }
    }


def pytest_generate_tests(metafunc):
    # pytest.mark.parametrize doesn't work on unittest.TestCase methods
    # see: https://docs.pytest.org/en/latest/example/parametrize.html#parametrizing-test-methods-through-per-class-configuration
    if metafunc.cls and hasattr(metafunc.cls, 'parametrize'):
        funcarglist = metafunc.cls.parametrize.get(metafunc.function.__name__)
        if funcarglist:
            argnames = sorted(funcarglist[0])
            metafunc.parametrize(
                argnames,
                [[funcargs[name] for name in argnames] for funcargs in funcarglist]
            )


def parse_extra_vars(args):
    extra_vars = {}
    for chunk in args:
        if chunk.startswith('@/tmp/'):
            with open(chunk.strip('@'), 'r') as f:
                extra_vars.update(yaml.load(f, Loader=SafeLoader))
    return extra_vars


class TestExtraVarSanitation(TestJobExecution):
    # By default, extra vars are marked as `!unsafe` in the generated yaml
    # _unless_ they've been specified on the JobTemplate's extra_vars (which
    # are deemed trustable, because they can only be added by users w/ enough
    # privilege to add/modify a Job Template)

    UNSAFE = '{{ lookup(''pipe'',''ls -la'') }}'

    def test_vars_unsafe_by_default(self, job, private_data_dir):
        job.created_by = User(pk=123, username='angry-spud')
        job.inventory = Inventory(pk=123, name='example-inv')

        task = tasks.RunJob()
        task.build_extra_vars_file(job, private_data_dir)

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, Loader=SafeLoader)

        # ensure that strings are marked as unsafe
        for unsafe in ['awx_job_template_name', 'tower_job_template_name',
                       'awx_user_name', 'tower_job_launch_type',
                       'awx_project_revision',
                       'tower_project_revision', 'tower_user_name',
                       'awx_job_launch_type',
                       'awx_inventory_name', 'tower_inventory_name']:
            assert hasattr(extra_vars[unsafe], '__UNSAFE__')

        # ensure that non-strings are marked as safe
        for safe in ['awx_job_template_id', 'awx_job_id', 'awx_user_id',
                     'tower_user_id', 'tower_job_template_id',
                     'tower_job_id', 'awx_inventory_id', 'tower_inventory_id']:
            assert not hasattr(extra_vars[safe], '__UNSAFE__')


    def test_launchtime_vars_unsafe(self, job, private_data_dir):
        job.extra_vars = json.dumps({'msg': self.UNSAFE})
        task = tasks.RunJob()

        task.build_extra_vars_file(job, private_data_dir)

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, Loader=SafeLoader)
        assert extra_vars['msg'] == self.UNSAFE
        assert hasattr(extra_vars['msg'], '__UNSAFE__')

    def test_nested_launchtime_vars_unsafe(self, job, private_data_dir):
        job.extra_vars = json.dumps({'msg': {'a': [self.UNSAFE]}})
        task = tasks.RunJob()

        task.build_extra_vars_file(job, private_data_dir)

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, Loader=SafeLoader)
        assert extra_vars['msg'] == {'a': [self.UNSAFE]}
        assert hasattr(extra_vars['msg']['a'][0], '__UNSAFE__')

    def test_allowed_jt_extra_vars(self, job, private_data_dir):
        job.job_template.extra_vars = job.extra_vars = json.dumps({'msg': self.UNSAFE})
        task = tasks.RunJob()

        task.build_extra_vars_file(job, private_data_dir)

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, Loader=SafeLoader)
        assert extra_vars['msg'] == self.UNSAFE
        assert not hasattr(extra_vars['msg'], '__UNSAFE__')

    def test_nested_allowed_vars(self, job, private_data_dir):
        job.extra_vars = json.dumps({'msg': {'a': {'b': [self.UNSAFE]}}})
        job.job_template.extra_vars = job.extra_vars
        task = tasks.RunJob()

        task.build_extra_vars_file(job, private_data_dir)

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, Loader=SafeLoader)
        assert extra_vars['msg'] == {'a': {'b': [self.UNSAFE]}}
        assert not hasattr(extra_vars['msg']['a']['b'][0], '__UNSAFE__')

    def test_sensitive_values_dont_leak(self, job, private_data_dir):
        # JT defines `msg=SENSITIVE`, the job *should not* be able to do
        # `other_var=SENSITIVE`
        job.job_template.extra_vars = json.dumps({'msg': self.UNSAFE})
        job.extra_vars = json.dumps({
            'msg': 'other-value',
            'other_var': self.UNSAFE
        })
        task = tasks.RunJob()

        task.build_extra_vars_file(job, private_data_dir)

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, Loader=SafeLoader)
        assert extra_vars['msg'] == 'other-value'
        assert hasattr(extra_vars['msg'], '__UNSAFE__')

        assert extra_vars['other_var'] == self.UNSAFE
        assert hasattr(extra_vars['other_var'], '__UNSAFE__')

    def test_overwritten_jt_extra_vars(self, job, private_data_dir):
        job.job_template.extra_vars = json.dumps({'msg': 'SAFE'})
        job.extra_vars = json.dumps({'msg': self.UNSAFE})
        task = tasks.RunJob()

        task.build_extra_vars_file(job, private_data_dir)

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, Loader=SafeLoader)
        assert extra_vars['msg'] == self.UNSAFE
        assert hasattr(extra_vars['msg'], '__UNSAFE__')


class TestGenericRun():

    def test_generic_failure(self, patch_Job):
        job = Job(
            status='running', inventory=Inventory(),
            project=Project(local_path='/projects/_23_foo'))
        job.websocket_emit_status = mock.Mock()

        task = tasks.RunJob()
        task.update_model = mock.Mock(return_value=job)
        task.model.objects.get = mock.Mock(return_value=job)
        task.build_private_data_files = mock.Mock(side_effect=OSError())

        with mock.patch('awx.main.tasks.copy_tree'):
            with pytest.raises(Exception):
                task.run(1)

        update_model_call = task.update_model.call_args[1]
        assert 'OSError' in update_model_call['result_traceback']
        assert update_model_call['status'] == 'error'
        assert update_model_call['emitted_events'] == 0

    def test_cancel_flag(self, job, update_model_wrapper):
        job.status = 'running'
        job.cancel_flag = True
        job.websocket_emit_status = mock.Mock()
        job.send_notification_templates = mock.Mock()

        task = tasks.RunJob()
        task.update_model = mock.Mock(wraps=update_model_wrapper)
        task.model.objects.get = mock.Mock(return_value=job)
        task.build_private_data_files = mock.Mock()

        with mock.patch('awx.main.tasks.copy_tree'):
            with pytest.raises(Exception):
                task.run(1)

        for c in [
            mock.call(1, status='running', start_args=''),
            mock.call(1, status='canceled')
        ]:
            assert c in task.update_model.call_args_list

    def test_event_count(self):
        task = tasks.RunJob()
        task.dispatcher = mock.MagicMock()
        task.instance = Job()
        task.event_ct = 0
        event_data = {}

        [task.event_handler(event_data) for i in range(20)]
        assert 20 == task.event_ct

    def test_finished_callback_eof(self):
        task = tasks.RunJob()
        task.dispatcher = mock.MagicMock()
        task.instance = Job(pk=1, id=1)
        task.event_ct = 17
        task.finished_callback(None)
        task.dispatcher.dispatch.assert_called_with({'event': 'EOF', 'final_counter': 17, 'job_id': 1})

    def test_save_job_metadata(self, job, update_model_wrapper):
        class MockMe():
            pass
        task = tasks.RunJob()
        task.instance = job
        task.safe_env = {'secret_key': 'redacted_value'}
        task.update_model = mock.Mock(wraps=update_model_wrapper)
        runner_config = MockMe()
        runner_config.command = {'foo': 'bar'}
        runner_config.cwd = '/foobar'
        runner_config.env = {'switch': 'blade', 'foot': 'ball', 'secret_key': 'secret_value'}
        task.status_handler({'status': 'starting'}, runner_config)

        task.update_model.assert_called_with(1, job_args=json.dumps({'foo': 'bar'}),
                                             job_cwd='/foobar', job_env={'switch': 'blade', 'foot': 'ball', 'secret_key': 'redacted_value'})


    def test_uses_process_isolation(self, settings):
        job = Job(project=Project(), inventory=Inventory())
        task = tasks.RunJob()
        task.should_use_proot = lambda instance: True
        task.instance = job

        private_data_dir = '/foo'
        cwd = '/bar'

        settings.AWX_PROOT_HIDE_PATHS = ['/AWX_PROOT_HIDE_PATHS1', '/AWX_PROOT_HIDE_PATHS2']
        settings.ANSIBLE_VENV_PATH = '/ANSIBLE_VENV_PATH'
        settings.AWX_VENV_PATH = '/AWX_VENV_PATH'

        process_isolation_params = task.build_params_process_isolation(job, private_data_dir, cwd)
        assert True is process_isolation_params['process_isolation']
        assert process_isolation_params['process_isolation_path'].startswith(settings.AWX_PROOT_BASE_PATH), \
            "Directory where a temp directory will be created for the remapping to take place"
        assert private_data_dir in process_isolation_params['process_isolation_show_paths'], \
            "The per-job private data dir should be in the list of directories the user can see."
        assert cwd in process_isolation_params['process_isolation_show_paths'], \
            "The current working directory should be in the list of directories the user can see."

        for p in [settings.AWX_PROOT_BASE_PATH,
                  '/etc/tower',
                  '/etc/ssh',
                  '/var/lib/awx',
                  '/var/log',
                  settings.PROJECTS_ROOT,
                  settings.JOBOUTPUT_ROOT,
                  '/AWX_PROOT_HIDE_PATHS1',
                  '/AWX_PROOT_HIDE_PATHS2']:
            assert p in process_isolation_params['process_isolation_hide_paths']
        assert 9 == len(process_isolation_params['process_isolation_hide_paths'])
        assert '/ANSIBLE_VENV_PATH' in process_isolation_params['process_isolation_ro_paths']
        assert '/AWX_VENV_PATH' in process_isolation_params['process_isolation_ro_paths']
        assert 2 == len(process_isolation_params['process_isolation_ro_paths'])


    @mock.patch('os.makedirs')
    def test_build_params_resource_profiling(self, os_makedirs):
        job = Job(project=Project(), inventory=Inventory())
        task = tasks.RunJob()
        task.should_use_resource_profiling = lambda job: True
        task.instance = job

        resource_profiling_params = task.build_params_resource_profiling(task.instance, '/fake_private_data_dir')
        assert resource_profiling_params['resource_profiling'] is True
        assert resource_profiling_params['resource_profiling_base_cgroup'] == 'ansible-runner'
        assert resource_profiling_params['resource_profiling_cpu_poll_interval'] == '0.25'
        assert resource_profiling_params['resource_profiling_memory_poll_interval'] == '0.25'
        assert resource_profiling_params['resource_profiling_pid_poll_interval'] == '0.25'
        assert resource_profiling_params['resource_profiling_results_dir'] == '/fake_private_data_dir/artifacts/playbook_profiling'


    @pytest.mark.parametrize("scenario, profiling_enabled", [
                             ('global_setting', True),
                             ('default', False)])
    def test_should_use_resource_profiling(self, scenario, profiling_enabled, settings):
        job = Job(project=Project(), inventory=Inventory())
        task = tasks.RunJob()
        task.instance = job

        if scenario == 'global_setting':
            settings.AWX_RESOURCE_PROFILING_ENABLED = True

        assert task.should_use_resource_profiling(task.instance) == profiling_enabled

    def test_created_by_extra_vars(self):
        job = Job(created_by=User(pk=123, username='angry-spud'))

        task = tasks.RunJob()
        task._write_extra_vars_file = mock.Mock()
        task.build_extra_vars_file(job, None)

        call_args, _ = task._write_extra_vars_file.call_args_list[0]

        private_data_dir, extra_vars, safe_dict = call_args
        assert extra_vars['tower_user_id'] == 123
        assert extra_vars['tower_user_name'] == "angry-spud"
        assert extra_vars['awx_user_id'] == 123
        assert extra_vars['awx_user_name'] == "angry-spud"

    def test_survey_extra_vars(self):
        job = Job()
        job.extra_vars = json.dumps({
            'super_secret': encrypt_value('CLASSIFIED', pk=None)
        })
        job.survey_passwords = {
            'super_secret': '$encrypted$'
        }

        task = tasks.RunJob()
        task._write_extra_vars_file = mock.Mock()
        task.build_extra_vars_file(job, None)

        call_args, _ = task._write_extra_vars_file.call_args_list[0]

        private_data_dir, extra_vars, safe_dict = call_args
        assert extra_vars['super_secret'] == "CLASSIFIED"

    def test_awx_task_env(self, patch_Job, private_data_dir):
        job = Job(project=Project(), inventory=Inventory())

        task = tasks.RunJob()
        task._write_extra_vars_file = mock.Mock()

        with mock.patch('awx.main.tasks.settings.AWX_TASK_ENV', {'FOO': 'BAR'}):
            env = task.build_env(job, private_data_dir)
        assert env['FOO'] == 'BAR'

    def test_valid_custom_virtualenv(self, patch_Job, private_data_dir):
        job = Job(project=Project(), inventory=Inventory())

        with TemporaryDirectory(dir=settings.BASE_VENV_PATH) as tempdir:
            job.project.custom_virtualenv = tempdir
            os.makedirs(os.path.join(tempdir, 'lib'))
            os.makedirs(os.path.join(tempdir, 'bin', 'activate'))

            task = tasks.RunJob()
            env = task.build_env(job, private_data_dir)

            assert env['PATH'].startswith(os.path.join(tempdir, 'bin'))
            assert env['VIRTUAL_ENV'] == tempdir

    def test_invalid_custom_virtualenv(self, patch_Job, private_data_dir):
        job = Job(project=Project(), inventory=Inventory())
        job.project.custom_virtualenv = '/venv/missing'
        task = tasks.RunJob()

        with pytest.raises(tasks.InvalidVirtualenvError) as e:
            task.build_env(job, private_data_dir)

        assert 'Invalid virtual environment selected: /venv/missing' == str(e.value)


class TestAdhocRun(TestJobExecution):

    def test_options_jinja_usage(self, adhoc_job, adhoc_update_model_wrapper):
        adhoc_job.module_args = '{{ ansible_ssh_pass }}'
        adhoc_job.websocket_emit_status = mock.Mock()
        adhoc_job.send_notification_templates = mock.Mock()

        task = tasks.RunAdHocCommand()
        task.update_model = mock.Mock(wraps=adhoc_update_model_wrapper)
        task.model.objects.get = mock.Mock(return_value=adhoc_job)
        task.build_inventory = mock.Mock()

        with pytest.raises(Exception):
            task.run(adhoc_job.pk)

        call_args, _ = task.update_model.call_args_list[0]
        update_model_call = task.update_model.call_args[1]
        assert 'Jinja variables are not allowed' in update_model_call['result_traceback']

    '''
    TODO: The jinja action is in _write_extra_vars_file. The extra vars should
    be wrapped in unsafe
    '''
    '''
    def test_extra_vars_jinja_usage(self, adhoc_job, adhoc_update_model_wrapper):
        adhoc_job.module_args = 'ls'
        adhoc_job.extra_vars = json.dumps({
            'foo': '{{ bar }}'
        })
        #adhoc_job.websocket_emit_status = mock.Mock()

        task = tasks.RunAdHocCommand()
        #task.update_model = mock.Mock(wraps=adhoc_update_model_wrapper)
        #task.build_inventory = mock.Mock(return_value='/tmp/something.inventory')
        task._write_extra_vars_file = mock.Mock()

        task.build_extra_vars_file(adhoc_job, 'ignore')

        call_args, _ = task._write_extra_vars_file.call_args_list[0]
        private_data_dir, extra_vars = call_args
        assert extra_vars['foo'] == '{{ bar }}'
    '''

    def test_created_by_extra_vars(self):
        adhoc_job = AdHocCommand(created_by=User(pk=123, username='angry-spud'))

        task = tasks.RunAdHocCommand()
        task._write_extra_vars_file = mock.Mock()
        task.build_extra_vars_file(adhoc_job, None)

        call_args, _ = task._write_extra_vars_file.call_args_list[0]

        private_data_dir, extra_vars = call_args
        assert extra_vars['tower_user_id'] == 123
        assert extra_vars['tower_user_name'] == "angry-spud"
        assert extra_vars['awx_user_id'] == 123
        assert extra_vars['awx_user_name'] == "angry-spud"


@pytest.mark.skip(reason="Isolated code path needs updating after runner integration")
class TestIsolatedExecution(TestJobExecution):

    ISOLATED_HOST = 'some-isolated-host'
    ISOLATED_CONTROLLER_HOST = 'some-isolated-controller-host'

    @pytest.fixture
    def job(self):
        job = Job(pk=1, id=1, project=Project(), inventory=Inventory(), job_template=JobTemplate(id=1, name='foo'))
        job.controller_node = self.ISOLATED_CONTROLLER_HOST
        job.execution_node = self.ISOLATED_HOST
        return job

    def test_with_ssh_credentials(self, job):
        ssh = CredentialType.defaults['ssh']()
        credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {
                'username': 'bob',
                'password': 'secret',
                'ssh_key_data': self.EXAMPLE_PRIVATE_KEY
            }
        )
        credential.inputs['password'] = encrypt_field(credential, 'password')
        job.credentials.add(credential)

        private_data = tempfile.mkdtemp(prefix='awx_')
        self.task.build_private_data_dir = mock.Mock(return_value=private_data)

        def _mock_job_artifacts(*args, **kw):
            artifacts = os.path.join(private_data, 'artifacts')
            if not os.path.exists(artifacts):
                os.makedirs(artifacts)
            if 'run_isolated.yml' in args[0]:
                for filename, data in (
                    ['status', 'successful'],
                    ['rc', '0'],
                    ['stdout', 'IT WORKED!'],
                ):
                    with open(os.path.join(artifacts, filename), 'w') as f:
                        f.write(data)
            return ('successful', 0)
        self.run_pexpect.side_effect = _mock_job_artifacts
        self.task.run(self.pk)

        playbook_run = self.run_pexpect.call_args_list[0][0]
        assert ' '.join(playbook_run[0]).startswith(' '.join([
            'ansible-playbook', 'run_isolated.yml', '-u', settings.AWX_ISOLATED_USERNAME,
            '-T', str(settings.AWX_ISOLATED_CONNECTION_TIMEOUT), '-i', self.ISOLATED_HOST + ',',
            '-e',
        ]))
        extra_vars = playbook_run[0][playbook_run[0].index('-e') + 1]
        extra_vars = json.loads(extra_vars)
        assert extra_vars['dest'] == '/tmp'
        assert extra_vars['src'] == private_data
        assert extra_vars['proot_temp_dir'].startswith('/tmp/awx_proot_')

    def test_systemctl_failure(self):
        # If systemctl fails, read the contents of `artifacts/systemctl_logs`
        mock_get = mock.Mock()
        ssh = CredentialType.defaults['ssh']()
        credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {'username': 'bob',}
        )
        self.instance.credentials.add(credential)

        private_data = tempfile.mkdtemp(prefix='awx_')
        self.task.build_private_data_dir = mock.Mock(return_value=private_data)
        inventory = json.dumps({"all": {"hosts": ["localhost"]}})

        def _mock_job_artifacts(*args, **kw):
            artifacts = os.path.join(private_data, 'artifacts')
            if not os.path.exists(artifacts):
                os.makedirs(artifacts)
            if 'run_isolated.yml' in args[0]:
                for filename, data in (
                    ['daemon.log', 'ERROR IN RUN.PY'],
                ):
                    with open(os.path.join(artifacts, filename), 'w') as f:
                        f.write(data)
            return ('successful', 0)
        self.run_pexpect.side_effect = _mock_job_artifacts

        with mock.patch('time.sleep'):
            with mock.patch('requests.get') as mock_get:
                mock_get.return_value = mock.Mock(content=inventory)
                with pytest.raises(Exception):
                    self.task.run(self.pk, self.ISOLATED_HOST)


class TestJobCredentials(TestJobExecution):
    @pytest.fixture
    def job(self):
        job = Job(pk=1, inventory=Inventory(pk=1), project=Project(pk=1))
        job.websocket_emit_status = mock.Mock()
        job._credentials = []

        def _credentials_filter(credential_type__kind=None):
            creds = job._credentials
            if credential_type__kind:
                creds = [c for c in creds if c.credential_type.kind == credential_type__kind]
            return mock.Mock(
                __iter__ = lambda *args: iter(creds),
                first = lambda: creds[0] if len(creds) else None
            )

        credentials_mock = mock.Mock(**{
            'all': lambda: job._credentials,
            'add': job._credentials.append,
            'filter.side_effect': _credentials_filter,
            'prefetch_related': lambda _: credentials_mock,
            'spec_set': ['all', 'add', 'filter', 'prefetch_related'],
        })

        with mock.patch.object(UnifiedJob, 'credentials', credentials_mock):
            yield job

    @pytest.fixture
    def update_model_wrapper(self, job):
        def fn(pk, **kwargs):
            for k, v in kwargs.items():
                setattr(job, k, v)
            return job
        return fn

    parametrize = {
        'test_ssh_passwords': [
            dict(field='password', password_name='ssh_password', expected_flag='--ask-pass'),
            dict(field='ssh_key_unlock', password_name='ssh_key_unlock', expected_flag=None),
            dict(field='become_password', password_name='become_password', expected_flag='--ask-become-pass'),
        ]
    }

    def test_username_jinja_usage(self, job, private_data_dir):
        task = tasks.RunJob()
        ssh = CredentialType.defaults['ssh']()
        credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {'username': '{{ ansible_ssh_pass }}'}
        )
        job.credentials.add(credential)
        with pytest.raises(ValueError) as e:
            task.build_args(job, private_data_dir, {})

        assert 'Jinja variables are not allowed' in str(e.value)

    @pytest.mark.parametrize("flag", ['become_username', 'become_method'])
    def test_become_jinja_usage(self, job, private_data_dir, flag):
        task = tasks.RunJob()
        ssh = CredentialType.defaults['ssh']()
        credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {'username': 'joe', flag: '{{ ansible_ssh_pass }}'}
        )
        job.credentials.add(credential)

        with pytest.raises(ValueError) as e:
            task.build_args(job, private_data_dir, {})

        assert 'Jinja variables are not allowed' in str(e.value)

    def test_ssh_passwords(self, job, private_data_dir, field, password_name, expected_flag):
        task = tasks.RunJob()
        ssh = CredentialType.defaults['ssh']()
        credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {'username': 'bob', field: 'secret'}
        )
        credential.inputs[field] = encrypt_field(credential, field)
        job.credentials.add(credential)

        passwords = task.build_passwords(job, {})
        password_prompts = task.get_password_prompts(passwords)
        expect_passwords = task.create_expect_passwords_data_struct(password_prompts, passwords)
        args = task.build_args(job, private_data_dir, passwords)

        assert 'secret' in expect_passwords.values()
        assert '-u bob' in ' '.join(args)
        if expected_flag:
            assert expected_flag in ' '.join(args)

    def test_net_ssh_key_unlock(self, job):
        task = tasks.RunJob()
        net = CredentialType.defaults['net']()
        credential = Credential(
            pk=1,
            credential_type=net,
            inputs = {'ssh_key_unlock': 'secret'}
        )
        credential.inputs['ssh_key_unlock'] = encrypt_field(credential, 'ssh_key_unlock')
        job.credentials.add(credential)

        passwords = task.build_passwords(job, {})
        password_prompts = task.get_password_prompts(passwords)
        expect_passwords = task.create_expect_passwords_data_struct(password_prompts, passwords)

        assert 'secret' in expect_passwords.values()

    def test_net_first_ssh_key_unlock_wins(self, job):
        task = tasks.RunJob()
        for i in range(3):
            net = CredentialType.defaults['net']()
            credential = Credential(
                pk=i,
                credential_type=net,
                inputs = {'ssh_key_unlock': 'secret{}'.format(i)}
            )
            credential.inputs['ssh_key_unlock'] = encrypt_field(credential, 'ssh_key_unlock')
            job.credentials.add(credential)

        passwords = task.build_passwords(job, {})
        password_prompts = task.get_password_prompts(passwords)
        expect_passwords = task.create_expect_passwords_data_struct(password_prompts, passwords)

        assert 'secret0' in expect_passwords.values()

    def test_prefer_ssh_over_net_ssh_key_unlock(self, job):
        task = tasks.RunJob()
        net = CredentialType.defaults['net']()
        net_credential = Credential(
            pk=1,
            credential_type=net,
            inputs = {'ssh_key_unlock': 'net_secret'}
        )
        net_credential.inputs['ssh_key_unlock'] = encrypt_field(net_credential, 'ssh_key_unlock')

        ssh = CredentialType.defaults['ssh']()
        ssh_credential = Credential(
            pk=2,
            credential_type=ssh,
            inputs = {'ssh_key_unlock': 'ssh_secret'}
        )
        ssh_credential.inputs['ssh_key_unlock'] = encrypt_field(ssh_credential, 'ssh_key_unlock')

        job.credentials.add(net_credential)
        job.credentials.add(ssh_credential)

        passwords = task.build_passwords(job, {})
        password_prompts = task.get_password_prompts(passwords)
        expect_passwords = task.create_expect_passwords_data_struct(password_prompts, passwords)

        assert 'ssh_secret' in expect_passwords.values()

    def test_vault_password(self, private_data_dir, job):
        task = tasks.RunJob()
        vault = CredentialType.defaults['vault']()
        credential = Credential(
            pk=1,
            credential_type=vault,
            inputs={'vault_password': 'vault-me'}
        )
        credential.inputs['vault_password'] = encrypt_field(credential, 'vault_password')
        job.credentials.add(credential)

        passwords = task.build_passwords(job, {})
        args = task.build_args(job, private_data_dir, passwords)
        password_prompts = task.get_password_prompts(passwords)
        expect_passwords = task.create_expect_passwords_data_struct(password_prompts, passwords)

        assert expect_passwords['Vault password:\s*?$'] == 'vault-me' # noqa
        assert '--ask-vault-pass' in ' '.join(args)

    def test_vault_password_ask(self, private_data_dir, job):
        task = tasks.RunJob()
        vault = CredentialType.defaults['vault']()
        credential = Credential(
            pk=1,
            credential_type=vault,
            inputs={'vault_password': 'ASK'}
        )
        credential.inputs['vault_password'] = encrypt_field(credential, 'vault_password')
        job.credentials.add(credential)

        passwords = task.build_passwords(job, {'vault_password': 'provided-at-launch'})
        args = task.build_args(job, private_data_dir, passwords)
        password_prompts = task.get_password_prompts(passwords)
        expect_passwords = task.create_expect_passwords_data_struct(password_prompts, passwords)

        assert expect_passwords['Vault password:\s*?$'] == 'provided-at-launch' # noqa
        assert '--ask-vault-pass' in ' '.join(args)

    def test_multi_vault_password(self, private_data_dir, job):
        task = tasks.RunJob()
        vault = CredentialType.defaults['vault']()
        for i, label in enumerate(['dev', 'prod', 'dotted.name']):
            credential = Credential(
                pk=i,
                credential_type=vault,
                inputs={'vault_password': 'pass@{}'.format(label), 'vault_id': label}
            )
            credential.inputs['vault_password'] = encrypt_field(credential, 'vault_password')
            job.credentials.add(credential)

        passwords = task.build_passwords(job, {})
        args = task.build_args(job, private_data_dir, passwords)
        password_prompts = task.get_password_prompts(passwords)
        expect_passwords = task.create_expect_passwords_data_struct(password_prompts, passwords)

        vault_passwords = dict(
            (k, v) for k, v in expect_passwords.items()
            if 'Vault' in k
        )
        assert vault_passwords['Vault password \(prod\):\\s*?$'] == 'pass@prod'  # noqa
        assert vault_passwords['Vault password \(dev\):\\s*?$'] == 'pass@dev'  # noqa
        assert vault_passwords['Vault password \(dotted.name\):\\s*?$'] == 'pass@dotted.name'  # noqa
        assert vault_passwords['Vault password:\\s*?$'] == ''  # noqa
        assert '--ask-vault-pass' not in ' '.join(args)
        assert '--vault-id dev@prompt' in ' '.join(args)
        assert '--vault-id prod@prompt' in ' '.join(args)
        assert '--vault-id dotted.name@prompt' in ' '.join(args)

    def test_multi_vault_id_conflict(self, job):
        task = tasks.RunJob()
        vault = CredentialType.defaults['vault']()
        for i in range(2):
            credential = Credential(
                pk=i,
                credential_type=vault,
                inputs={'vault_password': 'some-pass', 'vault_id': 'conflict'}
            )
            credential.inputs['vault_password'] = encrypt_field(credential, 'vault_password')
            job.credentials.add(credential)

        with pytest.raises(RuntimeError) as e:
            task.build_passwords(job, {})

        assert 'multiple vault credentials were specified with --vault-id' in str(e.value)

    def test_multi_vault_password_ask(self, private_data_dir, job):
        task = tasks.RunJob()
        vault = CredentialType.defaults['vault']()
        for i, label in enumerate(['dev', 'prod']):
            credential = Credential(
                pk=i,
                credential_type=vault,
                inputs={'vault_password': 'ASK', 'vault_id': label}
            )
            credential.inputs['vault_password'] = encrypt_field(credential, 'vault_password')
            job.credentials.add(credential)
        passwords = task.build_passwords(job, {
            'vault_password.dev': 'provided-at-launch@dev',
            'vault_password.prod': 'provided-at-launch@prod'
        })
        args = task.build_args(job, private_data_dir, passwords)
        password_prompts = task.get_password_prompts(passwords)
        expect_passwords = task.create_expect_passwords_data_struct(password_prompts, passwords)

        vault_passwords = dict(
            (k, v) for k, v in expect_passwords.items()
            if 'Vault' in k
        )
        assert vault_passwords['Vault password \(prod\):\\s*?$'] == 'provided-at-launch@prod'  # noqa
        assert vault_passwords['Vault password \(dev\):\\s*?$'] == 'provided-at-launch@dev'  # noqa
        assert vault_passwords['Vault password:\\s*?$'] == ''  # noqa
        assert '--ask-vault-pass' not in ' '.join(args)
        assert '--vault-id dev@prompt' in ' '.join(args)
        assert '--vault-id prod@prompt' in ' '.join(args)

    @pytest.mark.parametrize("verify", (True, False))
    def test_k8s_credential(self, job, private_data_dir, verify):
        k8s = CredentialType.defaults['kubernetes_bearer_token']()
        inputs = {
            'host': 'https://example.org/',
            'bearer_token': 'token123',
        }
        if verify:
            inputs['verify_ssl'] = True
            inputs['ssl_ca_cert'] = 'CERTDATA'
        credential = Credential(
            pk=1,
            credential_type=k8s,
            inputs = inputs,
        )
        credential.inputs['bearer_token'] = encrypt_field(credential, 'bearer_token')
        job.credentials.add(credential)

        env = {}
        safe_env = {}
        credential.credential_type.inject_credential(
            credential, env, safe_env, [], private_data_dir
        )

        assert env['K8S_AUTH_HOST'] == 'https://example.org/'
        assert env['K8S_AUTH_API_KEY'] == 'token123'

        if verify:
            assert env['K8S_AUTH_VERIFY_SSL'] == 'True'
            cert = open(env['K8S_AUTH_SSL_CA_CERT'], 'r').read()
            assert cert == 'CERTDATA'
        else:
            assert env['K8S_AUTH_VERIFY_SSL'] == 'False'
            assert 'K8S_AUTH_SSL_CA_CERT' not in env

        assert safe_env['K8S_AUTH_API_KEY'] == tasks.HIDDEN_PASSWORD

    def test_aws_cloud_credential(self, job, private_data_dir):
        aws = CredentialType.defaults['aws']()
        credential = Credential(
            pk=1,
            credential_type=aws,
            inputs = {'username': 'bob', 'password': 'secret'}
        )
        credential.inputs['password'] = encrypt_field(credential, 'password')
        job.credentials.add(credential)

        env = {}
        safe_env = {}
        credential.credential_type.inject_credential(
            credential, env, safe_env, [], private_data_dir
        )

        assert env['AWS_ACCESS_KEY_ID'] == 'bob'
        assert env['AWS_SECRET_ACCESS_KEY'] == 'secret'
        assert 'AWS_SECURITY_TOKEN' not in env
        assert safe_env['AWS_SECRET_ACCESS_KEY'] == tasks.HIDDEN_PASSWORD

    def test_aws_cloud_credential_with_sts_token(self, private_data_dir, job):
        aws = CredentialType.defaults['aws']()
        credential = Credential(
            pk=1,
            credential_type=aws,
            inputs = {'username': 'bob', 'password': 'secret', 'security_token': 'token'}
        )
        for key in ('password', 'security_token'):
            credential.inputs[key] = encrypt_field(credential, key)
        job.credentials.add(credential)

        env = {}
        safe_env = {}
        credential.credential_type.inject_credential(
            credential, env, safe_env, [], private_data_dir
        )

        assert env['AWS_ACCESS_KEY_ID'] == 'bob'
        assert env['AWS_SECRET_ACCESS_KEY'] == 'secret'
        assert env['AWS_SECURITY_TOKEN'] == 'token'
        assert safe_env['AWS_SECRET_ACCESS_KEY'] == tasks.HIDDEN_PASSWORD

    def test_gce_credentials(self, private_data_dir, job):
        gce = CredentialType.defaults['gce']()
        credential = Credential(
            pk=1,
            credential_type=gce,
            inputs = {
                'username': 'bob',
                'project': 'some-project',
                'ssh_key_data': self.EXAMPLE_PRIVATE_KEY
            }
        )
        credential.inputs['ssh_key_data'] = encrypt_field(credential, 'ssh_key_data')
        job.credentials.add(credential)

        env = {}
        safe_env = {}
        credential.credential_type.inject_credential(
            credential, env, safe_env, [], private_data_dir
        )
        json_data = json.load(open(env['GCE_CREDENTIALS_FILE_PATH'], 'rb'))
        assert json_data['type'] == 'service_account'
        assert json_data['private_key'] == self.EXAMPLE_PRIVATE_KEY
        assert json_data['client_email'] == 'bob'
        assert json_data['project_id'] == 'some-project'

    def test_azure_rm_with_tenant(self, private_data_dir, job):
        azure = CredentialType.defaults['azure_rm']()
        credential = Credential(
            pk=1,
            credential_type=azure,
            inputs = {
                'client': 'some-client',
                'secret': 'some-secret',
                'tenant': 'some-tenant',
                'subscription': 'some-subscription'
            }
        )
        credential.inputs['secret'] = encrypt_field(credential, 'secret')
        job.credentials.add(credential)

        env = {}
        safe_env = {}
        credential.credential_type.inject_credential(
            credential, env, safe_env, [], private_data_dir
        )

        assert env['AZURE_CLIENT_ID'] == 'some-client'
        assert env['AZURE_SECRET'] == 'some-secret'
        assert env['AZURE_TENANT'] == 'some-tenant'
        assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'
        assert safe_env['AZURE_SECRET'] == tasks.HIDDEN_PASSWORD

    def test_azure_rm_with_password(self, private_data_dir, job):
        azure = CredentialType.defaults['azure_rm']()
        credential = Credential(
            pk=1,
            credential_type=azure,
            inputs = {
                'subscription': 'some-subscription',
                'username': 'bob',
                'password': 'secret',
                'cloud_environment': 'foobar'
            }
        )
        credential.inputs['password'] = encrypt_field(credential, 'password')
        job.credentials.add(credential)

        env = {}
        safe_env = {}
        credential.credential_type.inject_credential(
            credential, env, safe_env, [], private_data_dir
        )

        assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'
        assert env['AZURE_AD_USER'] == 'bob'
        assert env['AZURE_PASSWORD'] == 'secret'
        assert env['AZURE_CLOUD_ENVIRONMENT'] == 'foobar'
        assert safe_env['AZURE_PASSWORD'] == tasks.HIDDEN_PASSWORD

    def test_vmware_credentials(self, private_data_dir, job):
        vmware = CredentialType.defaults['vmware']()
        credential = Credential(
            pk=1,
            credential_type=vmware,
            inputs = {'username': 'bob', 'password': 'secret', 'host': 'https://example.org'}
        )
        credential.inputs['password'] = encrypt_field(credential, 'password')
        job.credentials.add(credential)

        env = {}
        safe_env = {}
        credential.credential_type.inject_credential(
            credential, env, safe_env, [], private_data_dir
        )

        assert env['VMWARE_USER'] == 'bob'
        assert env['VMWARE_PASSWORD'] == 'secret'
        assert env['VMWARE_HOST'] == 'https://example.org'
        assert safe_env['VMWARE_PASSWORD'] == tasks.HIDDEN_PASSWORD

    def test_openstack_credentials(self, private_data_dir, job):
        task = tasks.RunJob()
        openstack = CredentialType.defaults['openstack']()
        credential = Credential(
            pk=1,
            credential_type=openstack,
            inputs = {
                'username': 'bob',
                'password': 'secret',
                'project': 'tenant-name',
                'host': 'https://keystone.example.org'
            }
        )
        credential.inputs['password'] = encrypt_field(credential, 'password')
        job.credentials.add(credential)

        private_data_files = task.build_private_data_files(job, private_data_dir)
        env = task.build_env(job, private_data_dir, private_data_files=private_data_files)
        credential.credential_type.inject_credential(
            credential, env, {}, [], private_data_dir
        )

        shade_config = open(env['OS_CLIENT_CONFIG_FILE'], 'r').read()
        assert shade_config == '\n'.join([
            'clouds:',
            '  devstack:',
            '    auth:',
            '      auth_url: https://keystone.example.org',
            '      password: secret',
            '      project_name: tenant-name',
            '      username: bob',
            '    verify: true',
            ''
        ])

    @pytest.mark.parametrize("ca_file", [None, '/path/to/some/file'])
    def test_rhv_credentials(self, private_data_dir, job, ca_file):
        rhv = CredentialType.defaults['rhv']()
        inputs = {
            'host': 'some-ovirt-host.example.org',
            'username': 'bob',
            'password': 'some-pass',
        }
        if ca_file:
            inputs['ca_file'] = ca_file
        credential = Credential(
            pk=1,
            credential_type=rhv,
            inputs=inputs
        )
        credential.inputs['password'] = encrypt_field(credential, 'password')
        job.credentials.add(credential)

        env = {}
        safe_env = {}
        credential.credential_type.inject_credential(
            credential, env, safe_env, [], private_data_dir
        )

        config = configparser.ConfigParser()
        config.read(env['OVIRT_INI_PATH'])
        assert config.get('ovirt', 'ovirt_url') == 'some-ovirt-host.example.org'
        assert config.get('ovirt', 'ovirt_username') == 'bob'
        assert config.get('ovirt', 'ovirt_password') == 'some-pass'
        if ca_file:
            assert config.get('ovirt', 'ovirt_ca_file') == ca_file
        else:
            with pytest.raises(configparser.NoOptionError):
                config.get('ovirt', 'ovirt_ca_file')

    @pytest.mark.parametrize('authorize, expected_authorize', [
        [True, '1'],
        [False, '0'],
        [None, '0'],
    ])
    def test_net_credentials(self, authorize, expected_authorize, job, private_data_dir):
        task = tasks.RunJob()
        net = CredentialType.defaults['net']()
        inputs = {
            'username': 'bob',
            'password': 'secret',
            'ssh_key_data': self.EXAMPLE_PRIVATE_KEY,
            'authorize_password': 'authorizeme'
        }
        if authorize is not None:
            inputs['authorize'] = authorize
        credential = Credential(pk=1, credential_type=net, inputs=inputs)
        for field in ('password', 'ssh_key_data', 'authorize_password'):
            credential.inputs[field] = encrypt_field(credential, field)
        job.credentials.add(credential)

        private_data_files = task.build_private_data_files(job, private_data_dir)
        env = task.build_env(job, private_data_dir, private_data_files=private_data_files)
        safe_env = build_safe_env(env)
        credential.credential_type.inject_credential(
            credential, env, safe_env, [], private_data_dir
        )

        assert env['ANSIBLE_NET_USERNAME'] == 'bob'
        assert env['ANSIBLE_NET_PASSWORD'] == 'secret'
        assert env['ANSIBLE_NET_AUTHORIZE'] == expected_authorize
        if authorize:
            assert env['ANSIBLE_NET_AUTH_PASS'] == 'authorizeme'
        assert open(env['ANSIBLE_NET_SSH_KEYFILE'], 'r').read() == self.EXAMPLE_PRIVATE_KEY
        assert safe_env['ANSIBLE_NET_PASSWORD'] == tasks.HIDDEN_PASSWORD

    def test_custom_environment_injectors_with_jinja_syntax_error(self, private_data_dir):
        some_cloud = CredentialType(
            kind='cloud',
            name='SomeCloud',
            managed_by_tower=False,
            inputs={
                'fields': [{
                    'id': 'api_token',
                    'label': 'API Token',
                    'type': 'string'
                }]
            },
            injectors={
                'env': {
                    'MY_CLOUD_API_TOKEN': '{{api_token.foo()}}'
                }
            }
        )
        credential = Credential(
            pk=1,
            credential_type=some_cloud,
            inputs = {'api_token': 'ABC123'}
        )

        with pytest.raises(jinja2.exceptions.UndefinedError):
            credential.credential_type.inject_credential(
                credential, {}, {}, [], private_data_dir
            )

    def test_custom_environment_injectors(self, private_data_dir):
        some_cloud = CredentialType(
            kind='cloud',
            name='SomeCloud',
            managed_by_tower=False,
            inputs={
                'fields': [{
                    'id': 'api_token',
                    'label': 'API Token',
                    'type': 'string'
                }]
            },
            injectors={
                'env': {
                    'MY_CLOUD_API_TOKEN': '{{api_token}}'
                }
            }
        )
        credential = Credential(
            pk=1,
            credential_type=some_cloud,
            inputs = {'api_token': 'ABC123'}
        )

        env = {}
        credential.credential_type.inject_credential(
            credential, env, {}, [], private_data_dir
        )

        assert env['MY_CLOUD_API_TOKEN'] == 'ABC123'

    def test_custom_environment_injectors_with_boolean_env_var(self, private_data_dir):
        some_cloud = CredentialType(
            kind='cloud',
            name='SomeCloud',
            managed_by_tower=False,
            inputs={
                'fields': [{
                    'id': 'turbo_button',
                    'label': 'Turbo Button',
                    'type': 'boolean'
                }]
            },
            injectors={
                'env': {
                    'TURBO_BUTTON': '{{turbo_button}}'
                }
            }
        )
        credential = Credential(
            pk=1,
            credential_type=some_cloud,
            inputs={'turbo_button': True}
        )

        env = {}
        credential.credential_type.inject_credential(
            credential, env, {}, [], private_data_dir
        )

        assert env['TURBO_BUTTON'] == str(True)

    def test_custom_environment_injectors_with_reserved_env_var(self, private_data_dir, job):
        task = tasks.RunJob()
        some_cloud = CredentialType(
            kind='cloud',
            name='SomeCloud',
            managed_by_tower=False,
            inputs={
                'fields': [{
                    'id': 'api_token',
                    'label': 'API Token',
                    'type': 'string'
                }]
            },
            injectors={
                'env': {
                    'JOB_ID': 'reserved'
                }
            }
        )
        credential = Credential(
            pk=1,
            credential_type=some_cloud,
            inputs = {'api_token': 'ABC123'}
        )
        job.credentials.add(credential)

        env = task.build_env(job, private_data_dir)

        assert env['JOB_ID'] == str(job.pk)

    def test_custom_environment_injectors_with_secret_field(self, private_data_dir):
        some_cloud = CredentialType(
            kind='cloud',
            name='SomeCloud',
            managed_by_tower=False,
            inputs={
                'fields': [{
                    'id': 'password',
                    'label': 'Password',
                    'type': 'string',
                    'secret': True
                }]
            },
            injectors={
                'env': {
                    'MY_CLOUD_PRIVATE_VAR': '{{password}}'
                }
            }
        )
        credential = Credential(
            pk=1,
            credential_type=some_cloud,
            inputs = {'password': 'SUPER-SECRET-123'}
        )
        credential.inputs['password'] = encrypt_field(credential, 'password')

        env = {}
        safe_env = {}
        credential.credential_type.inject_credential(
            credential, env, safe_env, [], private_data_dir
        )

        assert env['MY_CLOUD_PRIVATE_VAR'] == 'SUPER-SECRET-123'
        assert 'SUPER-SECRET-123' not in safe_env.values()
        assert safe_env['MY_CLOUD_PRIVATE_VAR'] == tasks.HIDDEN_PASSWORD

    def test_custom_environment_injectors_with_extra_vars(self, private_data_dir, job):
        task = tasks.RunJob()
        some_cloud = CredentialType(
            kind='cloud',
            name='SomeCloud',
            managed_by_tower=False,
            inputs={
                'fields': [{
                    'id': 'api_token',
                    'label': 'API Token',
                    'type': 'string'
                }]
            },
            injectors={
                'extra_vars': {
                    'api_token': '{{api_token}}'
                }
            }
        )
        credential = Credential(
            pk=1,
            credential_type=some_cloud,
            inputs = {'api_token': 'ABC123'}
        )
        job.credentials.add(credential)

        args = task.build_args(job, private_data_dir, {})
        credential.credential_type.inject_credential(
            credential, {}, {}, args, private_data_dir
        )
        extra_vars = parse_extra_vars(args)

        assert extra_vars["api_token"] == "ABC123"
        assert hasattr(extra_vars["api_token"], '__UNSAFE__')

    def test_custom_environment_injectors_with_boolean_extra_vars(self, job, private_data_dir):
        task = tasks.RunJob()
        some_cloud = CredentialType(
            kind='cloud',
            name='SomeCloud',
            managed_by_tower=False,
            inputs={
                'fields': [{
                    'id': 'turbo_button',
                    'label': 'Turbo Button',
                    'type': 'boolean'
                }]
            },
            injectors={
                'extra_vars': {
                    'turbo_button': '{{turbo_button}}'
                }
            }
        )
        credential = Credential(
            pk=1,
            credential_type=some_cloud,
            inputs={'turbo_button': True}
        )
        job.credentials.add(credential)

        args = task.build_args(job, private_data_dir, {})
        credential.credential_type.inject_credential(
            credential, {}, {}, args, private_data_dir
        )
        extra_vars = parse_extra_vars(args)

        assert extra_vars["turbo_button"] == "True"
        return ['successful', 0]

    def test_custom_environment_injectors_with_complicated_boolean_template(self, job, private_data_dir):
        task = tasks.RunJob()
        some_cloud = CredentialType(
            kind='cloud',
            name='SomeCloud',
            managed_by_tower=False,
            inputs={
                'fields': [{
                    'id': 'turbo_button',
                    'label': 'Turbo Button',
                    'type': 'boolean'
                }]
            },
            injectors={
                'extra_vars': {
                    'turbo_button': '{% if turbo_button %}FAST!{% else %}SLOW!{% endif %}'
                }
            }
        )
        credential = Credential(
            pk=1,
            credential_type=some_cloud,
            inputs={'turbo_button': True}
        )
        job.credentials.add(credential)

        args = task.build_args(job, private_data_dir, {})
        credential.credential_type.inject_credential(
            credential, {}, {}, args, private_data_dir
        )
        extra_vars = parse_extra_vars(args)

        assert extra_vars["turbo_button"] == "FAST!"

    def test_custom_environment_injectors_with_secret_extra_vars(self, job, private_data_dir):
        """
        extra_vars that contain secret field values should be censored in the DB
        """
        task = tasks.RunJob()
        some_cloud = CredentialType(
            kind='cloud',
            name='SomeCloud',
            managed_by_tower=False,
            inputs={
                'fields': [{
                    'id': 'password',
                    'label': 'Password',
                    'type': 'string',
                    'secret': True
                }]
            },
            injectors={
                'extra_vars': {
                    'password': '{{password}}'
                }
            }
        )
        credential = Credential(
            pk=1,
            credential_type=some_cloud,
            inputs = {'password': 'SUPER-SECRET-123'}
        )
        credential.inputs['password'] = encrypt_field(credential, 'password')
        job.credentials.add(credential)

        args = task.build_args(job, private_data_dir, {})
        credential.credential_type.inject_credential(
            credential, {}, {}, args, private_data_dir
        )

        extra_vars = parse_extra_vars(args)
        assert extra_vars["password"] == "SUPER-SECRET-123"

    def test_custom_environment_injectors_with_file(self, private_data_dir):
        some_cloud = CredentialType(
            kind='cloud',
            name='SomeCloud',
            managed_by_tower=False,
            inputs={
                'fields': [{
                    'id': 'api_token',
                    'label': 'API Token',
                    'type': 'string'
                }]
            },
            injectors={
                'file': {
                    'template': '[mycloud]\n{{api_token}}'
                },
                'env': {
                    'MY_CLOUD_INI_FILE': '{{tower.filename}}'
                }
            }
        )
        credential = Credential(
            pk=1,
            credential_type=some_cloud,
            inputs = {'api_token': 'ABC123'}
        )

        env = {}
        credential.credential_type.inject_credential(
            credential, env, {}, [], private_data_dir
        )

        assert open(env['MY_CLOUD_INI_FILE'], 'r').read() == '[mycloud]\nABC123'

    def test_custom_environment_injectors_with_unicode_content(self, private_data_dir):
        value = 'Iñtërnâtiônàlizætiøn'
        some_cloud = CredentialType(
            kind='cloud',
            name='SomeCloud',
            managed_by_tower=False,
            inputs={'fields': []},
            injectors={
                'file': {'template': value},
                'env': {'MY_CLOUD_INI_FILE': '{{tower.filename}}'}
            }
        )
        credential = Credential(
            pk=1,
            credential_type=some_cloud,
        )

        env = {}
        credential.credential_type.inject_credential(
            credential, env, {}, [], private_data_dir
        )

        assert open(env['MY_CLOUD_INI_FILE'], 'r').read() == value

    def test_custom_environment_injectors_with_files(self, private_data_dir):
        some_cloud = CredentialType(
            kind='cloud',
            name='SomeCloud',
            managed_by_tower=False,
            inputs={
                'fields': [{
                    'id': 'cert',
                    'label': 'Certificate',
                    'type': 'string'
                }, {
                    'id': 'key',
                    'label': 'Key',
                    'type': 'string'
                }]
            },
            injectors={
                'file': {
                    'template.cert': '[mycert]\n{{cert}}',
                    'template.key': '[mykey]\n{{key}}'
                },
                'env': {
                    'MY_CERT_INI_FILE': '{{tower.filename.cert}}',
                    'MY_KEY_INI_FILE': '{{tower.filename.key}}'
                }
            }
        )
        credential = Credential(
            pk=1,
            credential_type=some_cloud,
            inputs = {'cert': 'CERT123', 'key': 'KEY123'}
        )

        env = {}
        credential.credential_type.inject_credential(
            credential, env, {}, [], private_data_dir
        )

        assert open(env['MY_CERT_INI_FILE'], 'r').read() == '[mycert]\nCERT123'
        assert open(env['MY_KEY_INI_FILE'], 'r').read() == '[mykey]\nKEY123'

    def test_multi_cloud(self, private_data_dir):
        gce = CredentialType.defaults['gce']()
        gce_credential = Credential(
            pk=1,
            credential_type=gce,
            inputs = {
                'username': 'bob',
                'project': 'some-project',
                'ssh_key_data': self.EXAMPLE_PRIVATE_KEY
            }
        )
        gce_credential.inputs['ssh_key_data'] = encrypt_field(gce_credential, 'ssh_key_data')

        azure_rm = CredentialType.defaults['azure_rm']()
        azure_rm_credential = Credential(
            pk=2,
            credential_type=azure_rm,
            inputs = {
                'subscription': 'some-subscription',
                'username': 'bob',
                'password': 'secret'
            }
        )
        azure_rm_credential.inputs['secret'] = ''
        azure_rm_credential.inputs['secret'] = encrypt_field(azure_rm_credential, 'secret')

        env = {}
        safe_env = {}
        for credential in [gce_credential, azure_rm_credential]:
            credential.credential_type.inject_credential(
                credential, env, safe_env, [], private_data_dir
            )

        assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'
        assert env['AZURE_AD_USER'] == 'bob'
        assert env['AZURE_PASSWORD'] == 'secret'

        json_data = json.load(open(env['GCE_CREDENTIALS_FILE_PATH'], 'rb'))
        assert json_data['type'] == 'service_account'
        assert json_data['private_key'] == self.EXAMPLE_PRIVATE_KEY
        assert json_data['client_email'] == 'bob'
        assert json_data['project_id'] == 'some-project'

        assert safe_env['AZURE_PASSWORD'] == tasks.HIDDEN_PASSWORD

    def test_awx_task_env(self, settings, private_data_dir, job):
        settings.AWX_TASK_ENV = {'FOO': 'BAR'}
        task = tasks.RunJob()
        env = task.build_env(job, private_data_dir)

        assert env['FOO'] == 'BAR'


@pytest.mark.usefixtures("patch_Organization")
class TestProjectUpdateGalaxyCredentials(TestJobExecution):

    @pytest.fixture
    def project_update(self):
        org = Organization(pk=1)
        proj = Project(pk=1, organization=org)
        project_update = ProjectUpdate(pk=1, project=proj, scm_type='git')
        project_update.websocket_emit_status = mock.Mock()
        return project_update

    parametrize = {
        'test_galaxy_credentials_ignore_certs': [
            dict(ignore=True),
            dict(ignore=False),
        ],
    }

    def test_galaxy_credentials_ignore_certs(self, private_data_dir, project_update, ignore):
        settings.GALAXY_IGNORE_CERTS = ignore
        task = tasks.RunProjectUpdate()
        env = task.build_env(project_update, private_data_dir)
        if ignore:
            assert env['ANSIBLE_GALAXY_IGNORE'] is True
        else:
            assert 'ANSIBLE_GALAXY_IGNORE' not in env

    def test_galaxy_credentials_empty(self, private_data_dir, project_update):

        class RunProjectUpdate(tasks.RunProjectUpdate):
            __vars__ = {}

            def _write_extra_vars_file(self, private_data_dir, extra_vars, *kw):
                self.__vars__ = extra_vars

        task = RunProjectUpdate()
        env = task.build_env(project_update, private_data_dir)

        with mock.patch.object(Licenser, 'validate', lambda *args, **kw: {}):
            task.build_extra_vars_file(project_update, private_data_dir)

        assert task.__vars__['roles_enabled'] is False
        assert task.__vars__['collections_enabled'] is False
        for k in env:
            assert not k.startswith('ANSIBLE_GALAXY_SERVER')

    def test_single_public_galaxy(self, private_data_dir, project_update):
        class RunProjectUpdate(tasks.RunProjectUpdate):
            __vars__ = {}

            def _write_extra_vars_file(self, private_data_dir, extra_vars, *kw):
                self.__vars__ = extra_vars

        credential_type = CredentialType.defaults['galaxy_api_token']()
        public_galaxy = Credential(pk=1, credential_type=credential_type, inputs={
            'url': 'https://galaxy.ansible.com/',
        })
        project_update.project.organization.galaxy_credentials.add(public_galaxy)
        task = RunProjectUpdate()
        env = task.build_env(project_update, private_data_dir)

        with mock.patch.object(Licenser, 'validate', lambda *args, **kw: {}):
            task.build_extra_vars_file(project_update, private_data_dir)

        assert task.__vars__['roles_enabled'] is True
        assert task.__vars__['collections_enabled'] is True
        assert sorted([
            (k, v) for k, v in env.items()
            if k.startswith('ANSIBLE_GALAXY')
        ]) == [
            ('ANSIBLE_GALAXY_SERVER_LIST', 'server0'),
            ('ANSIBLE_GALAXY_SERVER_SERVER0_URL', 'https://galaxy.ansible.com/'),
        ]

    def test_multiple_galaxy_endpoints(self, private_data_dir, project_update):
        credential_type = CredentialType.defaults['galaxy_api_token']()
        public_galaxy = Credential(pk=1, credential_type=credential_type, inputs={
            'url': 'https://galaxy.ansible.com/',
        })
        rh = Credential(pk=2, credential_type=credential_type, inputs={
            'url': 'https://cloud.redhat.com/api/automation-hub/',
            'auth_url': 'https://sso.redhat.com/example/openid-connect/token/',
            'token': 'secret123'
        })
        project_update.project.organization.galaxy_credentials.add(public_galaxy)
        project_update.project.organization.galaxy_credentials.add(rh)
        task = tasks.RunProjectUpdate()
        env = task.build_env(project_update, private_data_dir)
        assert sorted([
            (k, v) for k, v in env.items()
            if k.startswith('ANSIBLE_GALAXY')
        ]) == [
            ('ANSIBLE_GALAXY_SERVER_LIST', 'server0,server1'),
            ('ANSIBLE_GALAXY_SERVER_SERVER0_URL', 'https://galaxy.ansible.com/'),
            ('ANSIBLE_GALAXY_SERVER_SERVER1_AUTH_URL', 'https://sso.redhat.com/example/openid-connect/token/'),  # noqa
            ('ANSIBLE_GALAXY_SERVER_SERVER1_TOKEN', 'secret123'),
            ('ANSIBLE_GALAXY_SERVER_SERVER1_URL', 'https://cloud.redhat.com/api/automation-hub/'),
        ]


@pytest.mark.usefixtures("patch_Organization")
class TestProjectUpdateCredentials(TestJobExecution):
    @pytest.fixture
    def project_update(self):
        project_update = ProjectUpdate(
            pk=1,
            project=Project(pk=1, organization=Organization(pk=1)),
        )
        project_update.websocket_emit_status = mock.Mock()
        return project_update

    parametrize = {
        'test_username_and_password_auth': [
            dict(scm_type='git'),
            dict(scm_type='hg'),
            dict(scm_type='svn'),
            dict(scm_type='archive'),
        ],
        'test_ssh_key_auth': [
            dict(scm_type='git'),
            dict(scm_type='hg'),
            dict(scm_type='svn'),
            dict(scm_type='archive'),
        ],
        'test_awx_task_env': [
            dict(scm_type='git'),
            dict(scm_type='hg'),
            dict(scm_type='svn'),
            dict(scm_type='archive'),
        ]
    }

    def test_process_isolation_exposes_projects_root(self, private_data_dir, project_update):
        task = tasks.RunProjectUpdate()
        task.revision_path = 'foobar'
        task.instance = project_update
        ssh = CredentialType.defaults['ssh']()
        project_update.scm_type = 'git'
        project_update.credential = Credential(
            pk=1,
            credential_type=ssh,
        )
        process_isolation = task.build_params_process_isolation(job, private_data_dir, 'cwd')

        assert process_isolation['process_isolation'] is True
        assert settings.PROJECTS_ROOT in process_isolation['process_isolation_show_paths']

        task._write_extra_vars_file = mock.Mock()

        with mock.patch.object(Licenser, 'validate', lambda *args, **kw: {}):
            task.build_extra_vars_file(project_update, private_data_dir)

        call_args, _ = task._write_extra_vars_file.call_args_list[0]
        _, extra_vars = call_args

    def test_username_and_password_auth(self, project_update, scm_type):
        task = tasks.RunProjectUpdate()
        ssh = CredentialType.defaults['ssh']()
        project_update.scm_type = scm_type
        project_update.credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {'username': 'bob', 'password': 'secret'}
        )
        project_update.credential.inputs['password'] = encrypt_field(
            project_update.credential, 'password'
        )

        passwords = task.build_passwords(project_update, {})
        password_prompts = task.get_password_prompts(passwords)
        expect_passwords = task.create_expect_passwords_data_struct(password_prompts, passwords)

        assert 'bob' in expect_passwords.values()
        assert 'secret' in expect_passwords.values()

    def test_ssh_key_auth(self, project_update, scm_type):
        task = tasks.RunProjectUpdate()
        ssh = CredentialType.defaults['ssh']()
        project_update.scm_type = scm_type
        project_update.credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {
                'username': 'bob',
                'ssh_key_data': self.EXAMPLE_PRIVATE_KEY
            }
        )
        project_update.credential.inputs['ssh_key_data'] = encrypt_field(
            project_update.credential, 'ssh_key_data'
        )

        passwords = task.build_passwords(project_update, {})
        password_prompts = task.get_password_prompts(passwords)
        expect_passwords = task.create_expect_passwords_data_struct(password_prompts, passwords)
        assert 'bob' in expect_passwords.values()

    def test_awx_task_env(self, project_update, settings, private_data_dir, scm_type):
        settings.AWX_TASK_ENV = {'FOO': 'BAR'}
        task = tasks.RunProjectUpdate()
        project_update.scm_type = scm_type

        env = task.build_env(project_update, private_data_dir)

        assert env['FOO'] == 'BAR'


class TestInventoryUpdateCredentials(TestJobExecution):
    @pytest.fixture
    def inventory_update(self):
        return InventoryUpdate(
            pk=1,
            inventory_source=InventorySource(
                pk=1,
                inventory=Inventory(pk=1)
            )
        )

    def test_source_without_credential(self, mocker, inventory_update, private_data_dir):
        task = tasks.RunInventoryUpdate()
        inventory_update.source = 'ec2'
        inventory_update.get_cloud_credential = mocker.Mock(return_value=None)
        inventory_update.get_extra_credentials = mocker.Mock(return_value=[])

        private_data_files = task.build_private_data_files(inventory_update, private_data_dir)
        env = task.build_env(inventory_update, private_data_dir, False, private_data_files)

        assert 'AWS_ACCESS_KEY_ID' not in env
        assert 'AWS_SECRET_ACCESS_KEY' not in env

    @pytest.mark.parametrize('with_credential', [True, False])
    def test_custom_source(self, with_credential, mocker, inventory_update, private_data_dir):
        task = tasks.RunInventoryUpdate()
        inventory_update.source = 'custom'
        inventory_update.source_vars = '{"FOO": "BAR"}'
        inventory_update.source_script= CustomInventoryScript(script='#!/bin/sh\necho "Hello, World!"')

        if with_credential:
            azure_rm = CredentialType.defaults['azure_rm']()

            def get_creds():
                cred = Credential(
                    pk=1,
                    credential_type=azure_rm,
                    inputs = {
                        'client': 'some-client',
                        'secret': 'some-secret',
                        'tenant': 'some-tenant',
                        'subscription': 'some-subscription',
                    }
                )
                return [cred]
            inventory_update.get_extra_credentials = get_creds
        else:
            inventory_update.get_extra_credentials = mocker.Mock(return_value=[])
        inventory_update.get_cloud_credential = mocker.Mock(return_value=None)

        env = task.build_env(inventory_update, private_data_dir, False)
        args = task.build_args(inventory_update, private_data_dir, {})

        credentials = task.build_credentials_list(inventory_update)
        for credential in credentials:
            if credential:
                credential.credential_type.inject_credential(
                    credential, env, {}, [], private_data_dir
                )

        assert '--custom' in ' '.join(args)
        script = args[args.index('--source') + 1]
        with open(script, 'r') as f:
            assert f.read() == inventory_update.source_script.script
        assert env['FOO'] == 'BAR'
        if with_credential:
            assert env['AZURE_CLIENT_ID'] == 'some-client'
            assert env['AZURE_SECRET'] == 'some-secret'
            assert env['AZURE_TENANT'] == 'some-tenant'
            assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'

    def test_ec2_source(self, private_data_dir, inventory_update, mocker):
        task = tasks.RunInventoryUpdate()
        aws = CredentialType.defaults['aws']()
        inventory_update.source = 'ec2'

        def get_cred():
            cred = Credential(
                pk=1,
                credential_type=aws,
                inputs = {'username': 'bob', 'password': 'secret'}
            )
            cred.inputs['password'] = encrypt_field(cred, 'password')
            return cred
        inventory_update.get_cloud_credential = get_cred
        inventory_update.get_extra_credentials = mocker.Mock(return_value=[])

        private_data_files = task.build_private_data_files(inventory_update, private_data_dir)
        env = task.build_env(inventory_update, private_data_dir, False, private_data_files)

        safe_env = build_safe_env(env)

        assert env['AWS_ACCESS_KEY_ID'] == 'bob'
        assert env['AWS_SECRET_ACCESS_KEY'] == 'secret'

        assert safe_env['AWS_SECRET_ACCESS_KEY'] == tasks.HIDDEN_PASSWORD

    def test_vmware_source(self, inventory_update, private_data_dir, mocker):
        task = tasks.RunInventoryUpdate()
        vmware = CredentialType.defaults['vmware']()
        inventory_update.source = 'vmware'

        def get_cred():
            cred = Credential(
                pk=1,
                credential_type=vmware,
                inputs = {'username': 'bob', 'password': 'secret', 'host': 'https://example.org'}
            )
            cred.inputs['password'] = encrypt_field(cred, 'password')
            return cred
        inventory_update.get_cloud_credential = get_cred
        inventory_update.get_extra_credentials = mocker.Mock(return_value=[])

        private_data_files = task.build_private_data_files(inventory_update, private_data_dir)
        env = task.build_env(inventory_update, private_data_dir, False, private_data_files)

        safe_env = {}
        credentials = task.build_credentials_list(inventory_update)
        for credential in credentials:
            if credential:
                credential.credential_type.inject_credential(
                    credential, env, safe_env, [], private_data_dir
                )

        env["VMWARE_USER"] == "bob",
        env["VMWARE_PASSWORD"] == "secret",
        env["VMWARE_HOST"] == "https://example.org",
        env["VMWARE_VALIDATE_CERTS"] == "False",

    def test_azure_rm_source_with_tenant(self, private_data_dir, inventory_update, mocker):
        task = tasks.RunInventoryUpdate()
        azure_rm = CredentialType.defaults['azure_rm']()
        inventory_update.source = 'azure_rm'

        def get_cred():
            cred = Credential(
                pk=1,
                credential_type=azure_rm,
                inputs = {
                    'client': 'some-client',
                    'secret': 'some-secret',
                    'tenant': 'some-tenant',
                    'subscription': 'some-subscription',
                    'cloud_environment': 'foobar'
                }
            )
            return cred
        inventory_update.get_cloud_credential = get_cred
        inventory_update.get_extra_credentials = mocker.Mock(return_value=[])
        inventory_update.source_vars = {
            'include_powerstate': 'yes',
            'group_by_resource_group': 'no'
        }

        private_data_files = task.build_private_data_files(inventory_update, private_data_dir)
        env = task.build_env(inventory_update, private_data_dir, False, private_data_files)

        safe_env = build_safe_env(env)

        assert env['AZURE_CLIENT_ID'] == 'some-client'
        assert env['AZURE_SECRET'] == 'some-secret'
        assert env['AZURE_TENANT'] == 'some-tenant'
        assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'
        assert env['AZURE_CLOUD_ENVIRONMENT'] == 'foobar'

        assert safe_env['AZURE_SECRET'] == tasks.HIDDEN_PASSWORD

    def test_azure_rm_source_with_password(self, private_data_dir, inventory_update, mocker):
        task = tasks.RunInventoryUpdate()
        azure_rm = CredentialType.defaults['azure_rm']()
        inventory_update.source = 'azure_rm'

        def get_cred():
            cred = Credential(
                pk=1,
                credential_type=azure_rm,
                inputs = {
                    'subscription': 'some-subscription',
                    'username': 'bob',
                    'password': 'secret',
                    'cloud_environment': 'foobar'
                }
            )
            return cred
        inventory_update.get_cloud_credential = get_cred
        inventory_update.get_extra_credentials = mocker.Mock(return_value=[])
        inventory_update.source_vars = {
            'include_powerstate': 'yes',
            'group_by_resource_group': 'no',
            'group_by_security_group': 'no'
        }

        private_data_files = task.build_private_data_files(inventory_update, private_data_dir)
        env = task.build_env(inventory_update, private_data_dir, False, private_data_files)

        safe_env = build_safe_env(env)

        assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'
        assert env['AZURE_AD_USER'] == 'bob'
        assert env['AZURE_PASSWORD'] == 'secret'
        assert env['AZURE_CLOUD_ENVIRONMENT'] == 'foobar'

        assert safe_env['AZURE_PASSWORD'] == tasks.HIDDEN_PASSWORD

    def test_gce_source(self, inventory_update, private_data_dir, mocker):
        task = tasks.RunInventoryUpdate()
        gce = CredentialType.defaults['gce']()
        inventory_update.source = 'gce'

        def get_cred():
            cred = Credential(
                pk=1,
                credential_type=gce,
                inputs = {
                    'username': 'bob',
                    'project': 'some-project',
                    'ssh_key_data': self.EXAMPLE_PRIVATE_KEY
                }
            )
            cred.inputs['ssh_key_data'] = encrypt_field(
                cred, 'ssh_key_data'
            )
            return cred
        inventory_update.get_cloud_credential = get_cred
        inventory_update.get_extra_credentials = mocker.Mock(return_value=[])

        def run(expected_gce_zone):
            private_data_files = task.build_private_data_files(inventory_update, private_data_dir)
            env = task.build_env(inventory_update, private_data_dir, False, private_data_files)
            safe_env = {}
            credentials = task.build_credentials_list(inventory_update)
            for credential in credentials:
                if credential:
                    credential.credential_type.inject_credential(
                        credential, env, safe_env, [], private_data_dir
                    )

            assert env['GCE_ZONE'] == expected_gce_zone
            json_data = json.load(open(env['GCE_CREDENTIALS_FILE_PATH'], 'rb'))
            assert json_data['type'] == 'service_account'
            assert json_data['private_key'] == self.EXAMPLE_PRIVATE_KEY
            assert json_data['client_email'] == 'bob'
            assert json_data['project_id'] == 'some-project'

    def test_openstack_source(self, inventory_update, private_data_dir, mocker):
        task = tasks.RunInventoryUpdate()
        openstack = CredentialType.defaults['openstack']()
        inventory_update.source = 'openstack'

        def get_cred():
            cred = Credential(
                pk=1,
                credential_type=openstack,
                inputs = {
                    'username': 'bob',
                    'password': 'secret',
                    'project': 'tenant-name',
                    'host': 'https://keystone.example.org'
                }
            )
            cred.inputs['ssh_key_data'] = ''
            cred.inputs['ssh_key_data'] = encrypt_field(
                cred, 'ssh_key_data'
            )
            return cred
        inventory_update.get_cloud_credential = get_cred
        inventory_update.get_extra_credentials = mocker.Mock(return_value=[])

        private_data_files = task.build_private_data_files(inventory_update, private_data_dir)
        env = task.build_env(inventory_update, private_data_dir, False, private_data_files)

        shade_config = open(env['OS_CLIENT_CONFIG_FILE'], 'r').read()
        assert '\n'.join([
            'clouds:',
            '  devstack:',
            '    auth:',
            '      auth_url: https://keystone.example.org',
            '      password: secret',
            '      project_name: tenant-name',
            '      username: bob',
            ''
        ]) in shade_config

    def test_satellite6_source(self, inventory_update, private_data_dir, mocker):
        task = tasks.RunInventoryUpdate()
        satellite6 = CredentialType.defaults['satellite6']()
        inventory_update.source = 'satellite6'

        def get_cred():
            cred = Credential(
                pk=1,
                credential_type=satellite6,
                inputs = {
                    'username': 'bob',
                    'password': 'secret',
                    'host': 'https://example.org'
                }
            )
            cred.inputs['password'] = encrypt_field(
                cred, 'password'
            )
            return cred
        inventory_update.get_cloud_credential = get_cred
        inventory_update.get_extra_credentials = mocker.Mock(return_value=[])

        inventory_update.source_vars = {
            'satellite6_group_patterns': '[a,b,c]',
            'satellite6_group_prefix': 'hey_',
            'satellite6_want_hostcollections': True,
            'satellite6_want_ansible_ssh_host': True,
            'satellite6_rich_params': True,
            'satellite6_want_facts': False
        }

        private_data_files = task.build_private_data_files(inventory_update, private_data_dir)
        env = task.build_env(inventory_update, private_data_dir, False, private_data_files)

        env["FOREMAN_SERVER"] == "https://example.org",
        env["FOREMAN_USER"] == "bob",
        env["FOREMAN_PASSWORD"] == "secret",

    @pytest.mark.parametrize('verify', [True, False])
    def test_tower_source(self, verify, inventory_update, private_data_dir, mocker):
        task = tasks.RunInventoryUpdate()
        tower = CredentialType.defaults['tower']()
        inventory_update.source = 'tower'
        inputs = {
            'host': 'https://tower.example.org',
            'username': 'bob',
            'password': 'secret',
            'verify_ssl': verify
        }

        def get_cred():
            cred = Credential(pk=1, credential_type=tower, inputs = inputs)
            cred.inputs['password'] = encrypt_field(cred, 'password')
            return cred
        inventory_update.get_cloud_credential = get_cred
        inventory_update.get_extra_credentials = mocker.Mock(return_value=[])

        env = task.build_env(inventory_update, private_data_dir, False)

        safe_env = build_safe_env(env)

        assert env['TOWER_HOST'] == 'https://tower.example.org'
        assert env['TOWER_USERNAME'] == 'bob'
        assert env['TOWER_PASSWORD'] == 'secret'
        if verify:
            assert env['TOWER_VERIFY_SSL'] == 'True'
        else:
            assert env['TOWER_VERIFY_SSL'] == 'False'
        assert safe_env['TOWER_PASSWORD'] == tasks.HIDDEN_PASSWORD

    def test_tower_source_ssl_verify_empty(self, inventory_update, private_data_dir, mocker):
        task = tasks.RunInventoryUpdate()
        tower = CredentialType.defaults['tower']()
        inventory_update.source = 'tower'
        inputs = {
            'host': 'https://tower.example.org',
            'username': 'bob',
            'password': 'secret',
        }

        def get_cred():
            cred = Credential(pk=1, credential_type=tower, inputs = inputs)
            cred.inputs['password'] = encrypt_field(cred, 'password')
            return cred
        inventory_update.get_cloud_credential = get_cred
        inventory_update.get_extra_credentials = mocker.Mock(return_value=[])

        env = task.build_env(inventory_update, private_data_dir, False)
        safe_env = {}
        credentials = task.build_credentials_list(inventory_update)
        for credential in credentials:
            if credential:
                credential.credential_type.inject_credential(
                    credential, env, safe_env, [], private_data_dir
                )

        assert env['TOWER_VERIFY_SSL'] == 'False'

    def test_awx_task_env(self, inventory_update, private_data_dir, settings, mocker):
        task = tasks.RunInventoryUpdate()
        gce = CredentialType.defaults['gce']()
        inventory_update.source = 'gce'

        def get_cred():
            cred = Credential(
                pk=1,
                credential_type=gce,
                inputs = {
                    'username': 'bob',
                    'project': 'some-project',
                }
            )
            return cred
        inventory_update.get_cloud_credential = get_cred
        inventory_update.get_extra_credentials = mocker.Mock(return_value=[])
        settings.AWX_TASK_ENV = {'FOO': 'BAR'}

        private_data_files = task.build_private_data_files(inventory_update, private_data_dir)
        env = task.build_env(inventory_update, private_data_dir, False, private_data_files)

        assert env['FOO'] == 'BAR'


def test_os_open_oserror():
    with pytest.raises(OSError):
        os.open('this_file_does_not_exist', os.O_RDONLY)


def test_fcntl_ioerror():
    with pytest.raises(OSError):
        fcntl.lockf(99999, fcntl.LOCK_EX)


@mock.patch('os.open')
@mock.patch('logging.getLogger')
def test_aquire_lock_open_fail_logged(logging_getLogger, os_open):
    err = OSError()
    err.errno = 3
    err.strerror = 'dummy message'

    instance = mock.Mock()
    instance.get_lock_file.return_value = 'this_file_does_not_exist'

    os_open.side_effect = err

    logger = mock.Mock()
    logging_getLogger.return_value = logger

    ProjectUpdate = tasks.RunProjectUpdate()

    with pytest.raises(OSError):
        ProjectUpdate.acquire_lock(instance)
    assert logger.err.called_with("I/O error({0}) while trying to open lock file [{1}]: {2}".format(3, 'this_file_does_not_exist', 'dummy message'))


@mock.patch('os.open')
@mock.patch('os.close')
@mock.patch('logging.getLogger')
@mock.patch('fcntl.lockf')
def test_aquire_lock_acquisition_fail_logged(fcntl_lockf, logging_getLogger, os_close, os_open):
    err = IOError()
    err.errno = 3
    err.strerror = 'dummy message'

    instance = mock.Mock()
    instance.get_lock_file.return_value = 'this_file_does_not_exist'
    instance.cancel_flag = False

    os_open.return_value = 3

    logger = mock.Mock()
    logging_getLogger.return_value = logger

    fcntl_lockf.side_effect = err

    ProjectUpdate = tasks.RunProjectUpdate()
    with pytest.raises(IOError):
        ProjectUpdate.acquire_lock(instance)
    os_close.assert_called_with(3)
    assert logger.err.called_with("I/O error({0}) while trying to aquire lock on file [{1}]: {2}".format(3, 'this_file_does_not_exist', 'dummy message'))


@pytest.mark.parametrize('injector_cls', [
    cls for cls in ManagedCredentialType.registry.values() if cls.injectors
])
def test_managed_injector_redaction(injector_cls):
    """See awx.main.models.inventory.PluginFileInjector._get_shared_env
    The ordering within awx.main.tasks.BaseTask and contract with build_env
    requires that all managed_by_tower injectors are safely redacted by the
    static method build_safe_env without having to employ the safe namespace
    as in inject_credential

    This test enforces that condition uniformly to prevent password leakages
    """
    secrets = set()
    for element in injector_cls.inputs.get('fields', []):
        if element.get('secret', False):
            secrets.add(element['id'])
    env = {}
    for env_name, template in injector_cls.injectors.get('env', {}).items():
        for secret_field_name in secrets:
            if secret_field_name in template:
                env[env_name] = 'very_secret_value'
    assert 'very_secret_value' not in str(build_safe_env(env))


@mock.patch('logging.getLogger')
def test_notification_job_not_finished(logging_getLogger, mocker):
    uj = mocker.MagicMock()
    uj.finished = False
    logger = mocker.Mock()
    logging_getLogger.return_value = logger

    with mocker.patch('awx.main.models.UnifiedJob.objects.get', uj):
        tasks.handle_success_and_failure_notifications(1)
        assert logger.warn.called_with(f"Failed to even try to send notifications for job '{uj}' due to job not being in finished state.")


def test_notification_job_finished(mocker):
    uj = mocker.MagicMock(send_notification_templates=mocker.MagicMock(), finished=True)

    with mocker.patch('awx.main.models.UnifiedJob.objects.get', mocker.MagicMock(return_value=uj)):
        tasks.handle_success_and_failure_notifications(1)
        uj.send_notification_templates.assert_called()
