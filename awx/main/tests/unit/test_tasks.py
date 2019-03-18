# -*- coding: utf-8 -*-

from contextlib import contextmanager
from datetime import datetime
from functools import partial
import configparser
import json
import os
import re
import shutil
import tempfile

from backports.tempfile import TemporaryDirectory
import fcntl
from unittest import mock
import pytest
import yaml

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
    Project,
    ProjectUpdate,
    UnifiedJob,
    User,
    Organization,
    build_safe_env
)

from awx.main import tasks
from awx.main.queue import CallbackQueueDispatcher
from awx.main.utils import encrypt_field, encrypt_value, OutputEventFilter
from awx.main.utils.safe_yaml import SafeLoader
from awx.main.exceptions import AwxTaskError


class TestJobExecution(object):
    pass


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
def job():
    return Job(pk=1, id=1, project=Project(), inventory=Inventory(), job_template=JobTemplate(id=1, name='foo'))


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


@pytest.fixture
def patch_CallbackQueueDispatcher():
    with mock.patch('awx.main.tasks.CallbackQueueDispatcher') as m:
        m.return_value = m
        yield m


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
    ('RABBITMQ_PASS', 'SECRET'),
    ('VMWARE_PASSWORD', 'SECRET'),
    ('API_SECRET', 'SECRET'),
    ('CALLBACK_CONNECTION', 'amqp://tower:password@localhost:5672/tower'),
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

    cred_method = mocker.Mock(return_value=credential)
    inventory_update = mocker.Mock(**{
        'source': 'openstack',
        'source_vars_dict': {},
        'get_cloud_credential': cred_method
    })
    cloud_config = update.build_private_data(inventory_update, private_data_dir)
    cloud_credential = yaml.load(
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

    cred_method = mocker.Mock(return_value=credential)
    inventory_update = mocker.Mock(**{
        'source': 'openstack',
        'source_vars_dict': {'private': source},
        'get_cloud_credential': cred_method
    })
    cloud_config = update.build_private_data(inventory_update, private_data_dir)
    cloud_credential = yaml.load(
        cloud_config.get('credentials')[credential]
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
                extra_vars.update(yaml.load(f, SafeLoader))
    return extra_vars


class TestExtraVarSanitation(TestJobExecution):
    # By default, extra vars are marked as `!unsafe` in the generated yaml
    # _unless_ they've been specified on the JobTemplate's extra_vars (which
    # are deemed trustable, because they can only be added by users w/ enough
    # privilege to add/modify a Job Template)

    UNSAFE = '{{ lookup(''pipe'',''ls -la'') }}'

    def test_vars_unsafe_by_default(self, job, private_data_dir):
        job.created_by = User(pk=123, username='angry-spud')

        task = tasks.RunJob()
        task.build_extra_vars_file(job, private_data_dir, {})

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, SafeLoader)

        # ensure that strings are marked as unsafe
        for unsafe in ['awx_job_template_name', 'tower_job_template_name',
                       'awx_user_name', 'tower_job_launch_type',
                       'awx_project_revision',
                       'tower_project_revision', 'tower_user_name',
                       'awx_job_launch_type']:
            assert hasattr(extra_vars[unsafe], '__UNSAFE__')

        # ensure that non-strings are marked as safe
        for safe in ['awx_job_template_id', 'awx_job_id', 'awx_user_id',
                     'tower_user_id', 'tower_job_template_id',
                     'tower_job_id']:
            assert not hasattr(extra_vars[safe], '__UNSAFE__')


    def test_launchtime_vars_unsafe(self, job, private_data_dir):
        job.extra_vars = json.dumps({'msg': self.UNSAFE})
        task = tasks.RunJob()

        task.build_extra_vars_file(job, private_data_dir, {})

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, SafeLoader)
        assert extra_vars['msg'] == self.UNSAFE
        assert hasattr(extra_vars['msg'], '__UNSAFE__')

    def test_nested_launchtime_vars_unsafe(self, job, private_data_dir):
        job.extra_vars = json.dumps({'msg': {'a': [self.UNSAFE]}})
        task = tasks.RunJob()

        task.build_extra_vars_file(job, private_data_dir, {})

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, SafeLoader)
        assert extra_vars['msg'] == {'a': [self.UNSAFE]}
        assert hasattr(extra_vars['msg']['a'][0], '__UNSAFE__')

    def test_whitelisted_jt_extra_vars(self, job, private_data_dir):
        job.job_template.extra_vars = job.extra_vars = json.dumps({'msg': self.UNSAFE})
        task = tasks.RunJob()

        task.build_extra_vars_file(job, private_data_dir, {})

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, SafeLoader)
        assert extra_vars['msg'] == self.UNSAFE
        assert not hasattr(extra_vars['msg'], '__UNSAFE__')

    def test_nested_whitelisted_vars(self, job, private_data_dir):
        job.extra_vars = json.dumps({'msg': {'a': {'b': [self.UNSAFE]}}})
        job.job_template.extra_vars = job.extra_vars
        task = tasks.RunJob()

        task.build_extra_vars_file(job, private_data_dir, {})

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, SafeLoader)
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

        task.build_extra_vars_file(job, private_data_dir, {})

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, SafeLoader)
        assert extra_vars['msg'] == 'other-value'
        assert hasattr(extra_vars['msg'], '__UNSAFE__')

        assert extra_vars['other_var'] == self.UNSAFE
        assert hasattr(extra_vars['other_var'], '__UNSAFE__')

    def test_overwritten_jt_extra_vars(self, job, private_data_dir):
        job.job_template.extra_vars = json.dumps({'msg': 'SAFE'})
        job.extra_vars = json.dumps({'msg': self.UNSAFE})
        task = tasks.RunJob()

        task.build_extra_vars_file(job, private_data_dir, {})

        fd = open(os.path.join(private_data_dir, 'env', 'extravars'))
        extra_vars = yaml.load(fd, SafeLoader)
        assert extra_vars['msg'] == self.UNSAFE
        assert hasattr(extra_vars['msg'], '__UNSAFE__')


class TestGenericRun():

    def test_generic_failure(self, patch_Job):
        job = Job(status='running', inventory=Inventory())
        job.websocket_emit_status = mock.Mock()

        task = tasks.RunJob()
        task.update_model = mock.Mock(return_value=job)
        task.build_private_data_files = mock.Mock(side_effect=OSError())

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

        task = tasks.RunJob()
        task.update_model = mock.Mock(wraps=update_model_wrapper)
        task.build_private_data_files = mock.Mock()

        with pytest.raises(Exception):
            task.run(1)

        for c in [
            mock.call(1, status='running', start_args=''),
            mock.call(1, status='canceled')
        ]:
            assert c in task.update_model.call_args_list

    def test_event_count(self, patch_CallbackQueueDispatcher):
        task = tasks.RunJob()
        task.instance = Job()
        task.event_ct = 0
        event_data = {}

        [task.event_handler(event_data) for i in range(20)]
        assert 20 == task.event_ct

    def test_finished_callback_eof(self, patch_CallbackQueueDispatcher):
        task = tasks.RunJob()
        task.instance = Job(pk=1, id=1)
        task.event_ct = 17
        task.finished_callback(None)
        patch_CallbackQueueDispatcher.dispatch.assert_called_with({'event': 'EOF', 'final_counter': 17, 'job_id': 1})

    def test_save_job_metadata(self, job, update_model_wrapper):
        class MockMe():
            pass
        task = tasks.RunJob()
        task.instance = job
        task.update_model = mock.Mock(wraps=update_model_wrapper)
        runner_config = MockMe()
        runner_config.command = {'foo': 'bar'}
        runner_config.cwd = '/foobar'
        runner_config.env = { 'switch': 'blade', 'foot': 'ball' }
        task.status_handler({'status': 'starting'}, runner_config)

        task.update_model.assert_called_with(1, job_args=json.dumps({'foo': 'bar'}),
                                           job_cwd='/foobar', job_env={'switch': 'blade', 'foot': 'ball'})


    '''
    def test_artifact_cleanup(self):
        path = tempfile.NamedTemporaryFile(delete=False).name
        try:
            self.task.cleanup_paths.append(path)
            assert os.path.exists(path)
            self.task.run(self.pk)
            assert not os.path.exists(path)
        finally:
            if os.path.exists(path):
                os.remove(path)
    '''

    def test_uses_process_isolation(self, settings):
        job = Job(project=Project(), inventory=Inventory())
        task = tasks.RunJob()
        task.should_use_proot = lambda instance: True

        private_data_dir = '/foo'
        cwd = '/bar'

        settings.AWX_PROOT_HIDE_PATHS = ['/AWX_PROOT_HIDE_PATHS1', '/AWX_PROOT_HIDE_PATHS2']
        settings.ANSIBLE_VENV_PATH = '/ANSIBLE_VENV_PATH'
        settings.AWX_VENV_PATH = '/AWX_VENV_PATH'

        process_isolation_params = task.build_params_process_isolation(job, private_data_dir, cwd)
        assert True is process_isolation_params['process_isolation']
        assert settings.AWX_PROOT_BASE_PATH == process_isolation_params['process_isolation_path'], \
            "Directory where a temp directory will be created for the remapping to take place"
        assert private_data_dir in process_isolation_params['process_isolation_show_paths'], \
            "The per-job private data dir should be in the list of directories the user can see."
        assert cwd in process_isolation_params['process_isolation_show_paths'], \
            "The current working directory should be in the list of directories the user can see."

        for p in [settings.AWX_PROOT_BASE_PATH,
                  '/etc/tower',
                  '/var/lib/awx',
                  '/var/log',
                  settings.PROJECTS_ROOT,
                  settings.JOBOUTPUT_ROOT,
                  '/AWX_PROOT_HIDE_PATHS1',
                  '/AWX_PROOT_HIDE_PATHS2']:
            assert p in process_isolation_params['process_isolation_hide_paths']
        assert 8 == len(process_isolation_params['process_isolation_hide_paths'])
        assert '/ANSIBLE_VENV_PATH' in process_isolation_params['process_isolation_ro_paths']
        assert '/AWX_VENV_PATH' in process_isolation_params['process_isolation_ro_paths']
        assert 2 == len(process_isolation_params['process_isolation_ro_paths'])

    def test_created_by_extra_vars(self):
        job = Job(created_by=User(pk=123, username='angry-spud'))

        task = tasks.RunJob()
        task._write_extra_vars_file = mock.Mock()
        task.build_extra_vars_file(job, None, dict())

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
        task.build_extra_vars_file(job, None, dict())

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

        with pytest.raises(RuntimeError) as e:
            env = task.build_env(job, private_data_dir)

        assert 'a valid Python virtualenv does not exist at /venv/missing' == str(e.value)


class TestAdhocRun(TestJobExecution):

    def test_options_jinja_usage(self, adhoc_job, adhoc_update_model_wrapper):
        adhoc_job.module_args = '{{ ansible_ssh_pass }}'
        adhoc_job.websocket_emit_status = mock.Mock()

        task = tasks.RunAdHocCommand()
        task.update_model = mock.Mock(wraps=adhoc_update_model_wrapper)
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
        task.build_extra_vars_file(adhoc_job, None, dict())

        call_args, _ = task._write_extra_vars_file.call_args_list[0]

        private_data_dir, extra_vars = call_args
        assert extra_vars['tower_user_id'] == 123
        assert extra_vars['tower_user_name'] == "angry-spud"
        assert extra_vars['awx_user_id'] == 123
        assert extra_vars['awx_user_name'] == "angry-spud"


class TestIsolatedExecution(TestJobExecution):

    ISOLATED_HOST = 'some-isolated-host'
    ISOLATED_CONTROLLER_HOST = 'some-isolated-controller-host'

    def get_instance(self):
        instance = super(TestIsolatedExecution, self).get_instance()
        instance.controller_node = self.ISOLATED_CONTROLLER_HOST
        instance.execution_node = self.ISOLATED_HOST
        return instance

    def test_with_ssh_credentials(self):
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
        self.instance.credentials.add(credential)

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

    parametrize = {
        'test_ssh_passwords': [
            dict(field='password', password_name='ssh_password', expected_flag='--ask-pass'),
            dict(field='ssh_key_unlock', password_name='ssh_key_unlock', expected_flag=None),
            dict(field='become_password', password_name='become_password', expected_flag='--ask-become-pass'),
        ]
    }

    def test_username_jinja_usage(self):
        ssh = CredentialType.defaults['ssh']()
        credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {'username': '{{ ansible_ssh_pass }}'}
        )
        self.instance.credentials.add(credential)
        with pytest.raises(Exception):
            self.task.run(self.pk)
        update_model_call = self.task.update_model.call_args[1]
        assert 'Jinja variables are not allowed' in update_model_call['result_traceback']

    @pytest.mark.parametrize("flag", ['become_username', 'become_method'])
    def test_become_jinja_usage(self, flag):
        ssh = CredentialType.defaults['ssh']()
        credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {'username': 'joe', flag: '{{ ansible_ssh_pass }}'}
        )
        self.instance.credentials.add(credential)
        with pytest.raises(Exception):
            self.task.run(self.pk)
        update_model_call = self.task.update_model.call_args[1]
        assert 'Jinja variables are not allowed' in update_model_call['result_traceback']

    def test_ssh_passwords(self, field, password_name, expected_flag):
        ssh = CredentialType.defaults['ssh']()
        credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {'username': 'bob', field: 'secret'}
        )
        credential.inputs[field] = encrypt_field(credential, field)
        self.instance.credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, call_kwargs = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert 'secret' in call_kwargs.get('expect_passwords').values()
        assert '-u bob' in ' '.join(args)
        if expected_flag:
            assert expected_flag in ' '.join(args)

    def test_net_ssh_key_unlock(self):
        net = CredentialType.defaults['net']()
        credential = Credential(
            pk=1,
            credential_type=net,
            inputs = {'ssh_key_unlock': 'secret'}
        )
        credential.inputs['ssh_key_unlock'] = encrypt_field(credential, 'ssh_key_unlock')
        self.instance.credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, call_kwargs = self.run_pexpect.call_args_list[0]

        assert 'secret' in call_kwargs.get('expect_passwords').values()

    def test_net_first_ssh_key_unlock_wins(self):
        for i in range(3):
            net = CredentialType.defaults['net']()
            credential = Credential(
                pk=i,
                credential_type=net,
                inputs = {'ssh_key_unlock': 'secret{}'.format(i)}
            )
            credential.inputs['ssh_key_unlock'] = encrypt_field(credential, 'ssh_key_unlock')
            self.instance.credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, call_kwargs = self.run_pexpect.call_args_list[0]

        assert 'secret0' in call_kwargs.get('expect_passwords').values()

    def test_prefer_ssh_over_net_ssh_key_unlock(self):
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

        self.instance.credentials.add(net_credential)
        self.instance.credentials.add(ssh_credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, call_kwargs = self.run_pexpect.call_args_list[0]

        assert 'ssh_secret' in call_kwargs.get('expect_passwords').values()

    def test_vault_password(self):
        vault = CredentialType.defaults['vault']()
        credential = Credential(
            pk=1,
            credential_type=vault,
            inputs={'vault_password': 'vault-me'}
        )
        credential.inputs['vault_password'] = encrypt_field(credential, 'vault_password')
        self.instance.credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, call_kwargs = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert call_kwargs.get('expect_passwords')[
            re.compile(r'Vault password:\s*?$', re.M)
        ] == 'vault-me'
        assert '--ask-vault-pass' in ' '.join(args)

    def test_vault_password_ask(self):
        vault = CredentialType.defaults['vault']()
        credential = Credential(
            pk=1,
            credential_type=vault,
            inputs={'vault_password': 'ASK'}
        )
        credential.inputs['vault_password'] = encrypt_field(credential, 'vault_password')
        self.instance.credentials.add(credential)
        self.task.run(self.pk, vault_password='provided-at-launch')

        assert self.run_pexpect.call_count == 1
        call_args, call_kwargs = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert call_kwargs.get('expect_passwords')[
            re.compile(r'Vault password:\s*?$', re.M)
        ] == 'provided-at-launch'
        assert '--ask-vault-pass' in ' '.join(args)

    def test_multi_vault_password(self):
        vault = CredentialType.defaults['vault']()
        for i, label in enumerate(['dev', 'prod']):
            credential = Credential(
                pk=i,
                credential_type=vault,
                inputs={'vault_password': 'pass@{}'.format(label), 'vault_id': label}
            )
            credential.inputs['vault_password'] = encrypt_field(credential, 'vault_password')
            self.instance.credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, call_kwargs = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        vault_passwords = dict(
            (k.pattern, v) for k, v in call_kwargs['expect_passwords'].items()
            if 'Vault' in k.pattern
        )
        assert vault_passwords['Vault password \(prod\):\\s*?$'] == 'pass@prod'  # noqa
        assert vault_passwords['Vault password \(dev\):\\s*?$'] == 'pass@dev'  # noqa
        assert vault_passwords['Vault password:\\s*?$'] == ''  # noqa
        assert '--ask-vault-pass' not in ' '.join(args)
        assert '--vault-id dev@prompt' in ' '.join(args)
        assert '--vault-id prod@prompt' in ' '.join(args)

    def test_multi_vault_id_conflict(self):
        vault = CredentialType.defaults['vault']()
        for i in range(2):
            credential = Credential(
                pk=i,
                credential_type=vault,
                inputs={'vault_password': 'some-pass', 'vault_id': 'conflict'}
            )
            credential.inputs['vault_password'] = encrypt_field(credential, 'vault_password')
            self.instance.credentials.add(credential)

        with pytest.raises(Exception):
            self.task.run(self.pk)

    def test_multi_vault_password_ask(self):
        vault = CredentialType.defaults['vault']()
        for i, label in enumerate(['dev', 'prod']):
            credential = Credential(
                pk=i,
                credential_type=vault,
                inputs={'vault_password': 'ASK', 'vault_id': label}
            )
            credential.inputs['vault_password'] = encrypt_field(credential, 'vault_password')
            self.instance.credentials.add(credential)
        self.task.run(self.pk, **{
            'vault_password.dev': 'provided-at-launch@dev',
            'vault_password.prod': 'provided-at-launch@prod'
        })

        assert self.run_pexpect.call_count == 1
        call_args, call_kwargs = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        vault_passwords = dict(
            (k.pattern, v) for k, v in call_kwargs['expect_passwords'].items()
            if 'Vault' in k.pattern
        )
        assert vault_passwords['Vault password \(prod\):\\s*?$'] == 'provided-at-launch@prod'  # noqa
        assert vault_passwords['Vault password \(dev\):\\s*?$'] == 'provided-at-launch@dev'  # noqa
        assert vault_passwords['Vault password:\\s*?$'] == ''  # noqa
        assert '--ask-vault-pass' not in ' '.join(args)
        assert '--vault-id dev@prompt' in ' '.join(args)
        assert '--vault-id prod@prompt' in ' '.join(args)

    def test_ssh_key_with_agent(self):
        ssh = CredentialType.defaults['ssh']()
        credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {
                'username': 'bob',
                'ssh_key_data': self.EXAMPLE_PRIVATE_KEY
            }
        )
        credential.inputs['ssh_key_data'] = encrypt_field(credential, 'ssh_key_data')
        self.instance.credentials.add(credential)

        def run_pexpect_side_effect(private_data, *args, **kwargs):
            args, cwd, env, stdout = args
            ssh_key_data_fifo = '/'.join([private_data, 'credential_1'])
            assert open(ssh_key_data_fifo, 'r').read() == self.EXAMPLE_PRIVATE_KEY
            assert ' '.join(args).startswith(
                'ssh-agent -a %s sh -c ssh-add %s && rm -f %s' % (
                    '/'.join([private_data, 'ssh_auth.sock']),
                    ssh_key_data_fifo,
                    ssh_key_data_fifo
                )
            )
            return ['successful', 0]

        private_data = tempfile.mkdtemp(prefix='awx_')
        self.task.build_private_data_dir = mock.Mock(return_value=private_data)
        self.run_pexpect.side_effect = partial(run_pexpect_side_effect, private_data)
        self.task.run(self.pk, private_data_dir=private_data)

    def test_aws_cloud_credential(self):
        aws = CredentialType.defaults['aws']()
        credential = Credential(
            pk=1,
            credential_type=aws,
            inputs = {'username': 'bob', 'password': 'secret'}
        )
        credential.inputs['password'] = encrypt_field(credential, 'password')
        self.instance.credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['AWS_ACCESS_KEY_ID'] == 'bob'
        assert env['AWS_SECRET_ACCESS_KEY'] == 'secret'
        assert 'AWS_SECURITY_TOKEN' not in env
        assert self.instance.job_env['AWS_SECRET_ACCESS_KEY'] == tasks.HIDDEN_PASSWORD

    def test_aws_cloud_credential_with_sts_token(self):
        aws = CredentialType.defaults['aws']()
        credential = Credential(
            pk=1,
            credential_type=aws,
            inputs = {'username': 'bob', 'password': 'secret', 'security_token': 'token'}
        )
        for key in ('password', 'security_token'):
            credential.inputs[key] = encrypt_field(credential, key)
        self.instance.credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['AWS_ACCESS_KEY_ID'] == 'bob'
        assert env['AWS_SECRET_ACCESS_KEY'] == 'secret'
        assert env['AWS_SECURITY_TOKEN'] == 'token'
        assert self.instance.job_env['AWS_SECRET_ACCESS_KEY'] == tasks.HIDDEN_PASSWORD

    def test_gce_credentials(self):
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
        self.instance.credentials.add(credential)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            json_data = json.load(open(env['GCE_CREDENTIALS_FILE_PATH'], 'rb'))
            assert json_data['type'] == 'service_account'
            assert json_data['private_key'] == self.EXAMPLE_PRIVATE_KEY
            assert json_data['client_email'] == 'bob'
            assert json_data['project_id'] == 'some-project'
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_azure_rm_with_tenant(self):
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
        self.instance.credentials.add(credential)

        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['AZURE_CLIENT_ID'] == 'some-client'
        assert env['AZURE_SECRET'] == 'some-secret'
        assert env['AZURE_TENANT'] == 'some-tenant'
        assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'
        assert self.instance.job_env['AZURE_SECRET'] == tasks.HIDDEN_PASSWORD

    def test_azure_rm_with_password(self):
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
        self.instance.credentials.add(credential)

        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'
        assert env['AZURE_AD_USER'] == 'bob'
        assert env['AZURE_PASSWORD'] == 'secret'
        assert env['AZURE_CLOUD_ENVIRONMENT'] == 'foobar'
        assert self.instance.job_env['AZURE_PASSWORD'] == tasks.HIDDEN_PASSWORD

    def test_vmware_credentials(self):
        vmware = CredentialType.defaults['vmware']()
        credential = Credential(
            pk=1,
            credential_type=vmware,
            inputs = {'username': 'bob', 'password': 'secret', 'host': 'https://example.org'}
        )
        credential.inputs['password'] = encrypt_field(credential, 'password')
        self.instance.credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['VMWARE_USER'] == 'bob'
        assert env['VMWARE_PASSWORD'] == 'secret'
        assert env['VMWARE_HOST'] == 'https://example.org'
        assert self.instance.job_env['VMWARE_PASSWORD'] == tasks.HIDDEN_PASSWORD

    def test_openstack_credentials(self):
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
        self.instance.credentials.add(credential)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
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
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    @pytest.mark.parametrize("ca_file", [None, '/path/to/some/file'])
    def test_rhv_credentials(self, ca_file):
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
        self.instance.credentials.add(credential)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
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
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    @pytest.mark.parametrize('authorize, expected_authorize', [
        [True, '1'],
        [False, '0'],
        [None, '0'],
    ])
    def test_net_credentials(self, authorize, expected_authorize):
        net = CredentialType.defaults['net']()
        inputs = {
            'username': 'bob',
            'password': 'secret',
            'ssh_key_data': self.EXAMPLE_PRIVATE_KEY,
            'authorize_password': 'authorizeme'
        }
        if authorize is not None:
            inputs['authorize'] = authorize
        credential = Credential(pk=1,credential_type=net, inputs = inputs)
        for field in ('password', 'ssh_key_data', 'authorize_password'):
            credential.inputs[field] = encrypt_field(credential, field)
        self.instance.credentials.add(credential)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert env['ANSIBLE_NET_USERNAME'] == 'bob'
            assert env['ANSIBLE_NET_PASSWORD'] == 'secret'
            assert env['ANSIBLE_NET_AUTHORIZE'] == expected_authorize
            if authorize:
                assert env['ANSIBLE_NET_AUTH_PASS'] == 'authorizeme'
            assert open(env['ANSIBLE_NET_SSH_KEYFILE'], 'r').read() == self.EXAMPLE_PRIVATE_KEY
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)
        assert self.instance.job_env['ANSIBLE_NET_PASSWORD'] == tasks.HIDDEN_PASSWORD

    def test_custom_environment_injectors_with_jinja_syntax_error(self):
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
        self.instance.credentials.add(credential)
        with pytest.raises(Exception):
            self.task.run(self.pk)

    def test_custom_environment_injectors(self):
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
        self.instance.credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['MY_CLOUD_API_TOKEN'] == 'ABC123'

    def test_custom_environment_injectors_with_boolean_env_var(self):
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
        self.instance.credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args
        assert env['TURBO_BUTTON'] == str(True)

    def test_custom_environment_injectors_with_reserved_env_var(self):
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
        self.instance.credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['JOB_ID'] == str(self.instance.pk)

    def test_custom_environment_injectors_with_secret_field(self):
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
        self.instance.credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['MY_CLOUD_PRIVATE_VAR'] == 'SUPER-SECRET-123'
        assert 'SUPER-SECRET-123' not in json.dumps(self.task.update_model.call_args_list)
        assert self.instance.job_env['MY_CLOUD_PRIVATE_VAR'] == tasks.HIDDEN_PASSWORD

    def test_custom_environment_injectors_with_extra_vars(self):
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
        self.instance.credentials.add(credential)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            extra_vars = parse_extra_vars(args)
            assert extra_vars["api_token"] == "ABC123"
            assert hasattr(extra_vars["api_token"], '__UNSAFE__')
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_custom_environment_injectors_with_boolean_extra_vars(self):
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
        self.instance.credentials.add(credential)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            extra_vars = parse_extra_vars(args)
            assert extra_vars["turbo_button"] == "True"
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_custom_environment_injectors_with_complicated_boolean_template(self):
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
        self.instance.credentials.add(credential)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            extra_vars = parse_extra_vars(args)
            assert extra_vars["turbo_button"] == "FAST!"
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_custom_environment_injectors_with_secret_extra_vars(self):
        """
        extra_vars that contain secret field values should be censored in the DB
        """
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
        self.instance.credentials.add(credential)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            extra_vars = parse_extra_vars(args)
            assert extra_vars["password"] == "SUPER-SECRET-123"
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

        assert 'SUPER-SECRET-123' not in json.dumps(self.task.update_model.call_args_list)

    def test_custom_environment_injectors_with_file(self):
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
        self.instance.credentials.add(credential)
        self.task.run(self.pk)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert open(env['MY_CLOUD_INI_FILE'], 'r').read() == '[mycloud]\nABC123'
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_custom_environment_injectors_with_unicode_content(self):
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
        self.instance.credentials.add(credential)
        self.task.run(self.pk)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert open(env['MY_CLOUD_INI_FILE'], 'r').read() == value
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_custom_environment_injectors_with_files(self):
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
        self.instance.credentials.add(credential)
        self.task.run(self.pk)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert open(env['MY_CERT_INI_FILE'], 'r').read() == '[mycert]\nCERT123'
            assert open(env['MY_KEY_INI_FILE'], 'r').read() == '[mykey]\nKEY123'
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_multi_cloud(self):
        gce = CredentialType.defaults['gce']()
        gce_credential = Credential(
            pk=1,
            credential_type=gce,
            inputs = {
                'username': 'bob',
                'project': 'some-project',
                'ssh_key_data': 'GCE: %s' % self.EXAMPLE_PRIVATE_KEY
            }
        )
        gce_credential.inputs['ssh_key_data'] = encrypt_field(gce_credential, 'ssh_key_data')
        self.instance.credentials.add(gce_credential)

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
        self.instance.credentials.add(azure_rm_credential)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args

            assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'
            assert env['AZURE_AD_USER'] == 'bob'
            assert env['AZURE_PASSWORD'] == 'secret'

            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)
        assert self.instance.job_env['AZURE_PASSWORD'] == tasks.HIDDEN_PASSWORD

    def test_awx_task_env(self):
        with mock.patch('awx.main.tasks.settings.AWX_TASK_ENV', {'FOO': 'BAR'}):
            self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args
        assert env['FOO'] == 'BAR'


class TestProjectUpdateCredentials(TestJobExecution):

    TASK_CLS = tasks.RunProjectUpdate

    def get_instance(self):
        return ProjectUpdate(
            pk=1,
            project=Project()
        )

    parametrize = {
        'test_username_and_password_auth': [
            dict(scm_type='git'),
            dict(scm_type='hg'),
            dict(scm_type='svn'),
        ],
        'test_ssh_key_auth': [
            dict(scm_type='git'),
            dict(scm_type='hg'),
            dict(scm_type='svn'),
        ],
        'test_awx_task_env': [
            dict(scm_type='git'),
            dict(scm_type='hg'),
            dict(scm_type='svn'),
        ]
    }

    def test_bwrap_exposes_projects_root(self):
        ssh = CredentialType.defaults['ssh']()
        self.instance.scm_type = 'git'
        self.instance.credential = Credential(
            pk=1,
            credential_type=ssh,
        )

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            extra_vars = parse_extra_vars(args)
            assert ' '.join(args).startswith('bwrap')
            assert ' '.join([
                '--bind',
                os.path.realpath(settings.PROJECTS_ROOT),
                os.path.realpath(settings.PROJECTS_ROOT)
            ]) in ' '.join(args)
            assert extra_vars["scm_revision_output"].startswith(settings.PROJECTS_ROOT)
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_username_and_password_auth(self, scm_type):
        ssh = CredentialType.defaults['ssh']()
        self.instance.scm_type = scm_type
        self.instance.credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {'username': 'bob', 'password': 'secret'}
        )
        self.instance.credential.inputs['password'] = encrypt_field(
            self.instance.credential, 'password'
        )
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, call_kwargs = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert 'bob' in call_kwargs.get('expect_passwords').values()
        assert 'secret' in call_kwargs.get('expect_passwords').values()

    def test_ssh_key_auth(self, scm_type):
        ssh = CredentialType.defaults['ssh']()
        self.instance.scm_type = scm_type
        self.instance.credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {
                'username': 'bob',
                'ssh_key_data': self.EXAMPLE_PRIVATE_KEY
            }
        )
        self.instance.credential.inputs['ssh_key_data'] = encrypt_field(
            self.instance.credential, 'ssh_key_data'
        )

        def run_pexpect_side_effect(private_data, *args, **kwargs):
            args, cwd, env, stdout = args
            ssh_key_data_fifo = '/'.join([private_data, 'credential_1'])
            assert open(ssh_key_data_fifo, 'r').read() == self.EXAMPLE_PRIVATE_KEY
            assert ' '.join(args).startswith(
                'ssh-agent -a %s sh -c ssh-add %s && rm -f %s' % (
                    '/'.join([private_data, 'ssh_auth.sock']),
                    ssh_key_data_fifo,
                    ssh_key_data_fifo
                )
            )
            assert 'bob' in kwargs.get('expect_passwords').values()
            return ['successful', 0]

        private_data = tempfile.mkdtemp(prefix='awx_')
        self.task.build_private_data_dir = mock.Mock(return_value=private_data)
        self.run_pexpect.side_effect = partial(run_pexpect_side_effect, private_data)
        self.task.run(self.pk)

    def test_awx_task_env(self, scm_type):
        self.instance.scm_type = scm_type
        with mock.patch('awx.main.tasks.settings.AWX_TASK_ENV', {'FOO': 'BAR'}):
            self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args
        assert env['FOO'] == 'BAR'


class TestInventoryUpdateCredentials(TestJobExecution):

    TASK_CLS = tasks.RunInventoryUpdate

    def get_instance(self):
        return InventoryUpdate(
            pk=1,
            inventory_source=InventorySource(
                pk=1,
                inventory=Inventory(pk=1)
            )
        )

    def test_source_without_credential(self, mocker):
        self.instance.source = 'ec2'
        self.instance.get_cloud_credential = mocker.Mock(return_value=None)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args

            assert 'AWS_ACCESS_KEY_ID' not in env
            assert 'AWS_SECRET_ACCESS_KEY' not in env
            assert 'EC2_INI_PATH' in env

            config = configparser.ConfigParser()
            config.read(env['EC2_INI_PATH'])
            assert 'ec2' in config.sections()
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    @pytest.mark.parametrize('with_credential', [True, False])
    def test_custom_source(self, with_credential, mocker):
        self.instance.source = 'custom'
        self.instance.source_vars = '{"FOO": "BAR"}'
        patch = mock.patch.object(InventoryUpdate, 'source_script', mock.Mock(
            script='#!/bin/sh\necho "Hello, World!"')
        )
        self.patches.append(patch)
        patch.start()

        if with_credential:
            azure_rm = CredentialType.defaults['azure_rm']()

            def get_cred():
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
                return cred
            self.instance.get_cloud_credential = get_cred
        else:
            self.instance.get_cloud_credential = mocker.Mock(return_value=None)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert '--custom' in ' '.join(args)
            script = args[args.index('--source') + 1]
            with open(script, 'r') as f:
                assert f.read() == self.instance.source_script.script
            assert env['FOO'] == 'BAR'
            if with_credential:
                assert env['AZURE_CLIENT_ID'] == 'some-client'
                assert env['AZURE_SECRET'] == 'some-secret'
                assert env['AZURE_TENANT'] == 'some-tenant'
                assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_ec2_source(self):
        aws = CredentialType.defaults['aws']()
        self.instance.source = 'ec2'

        def get_cred():
            cred = Credential(
                pk=1,
                credential_type=aws,
                inputs = {'username': 'bob', 'password': 'secret'}
            )
            cred.inputs['password'] = encrypt_field(cred, 'password')
            return cred
        self.instance.get_cloud_credential = get_cred

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args

            assert env['AWS_ACCESS_KEY_ID'] == 'bob'
            assert env['AWS_SECRET_ACCESS_KEY'] == 'secret'
            assert 'EC2_INI_PATH' in env

            config = configparser.ConfigParser()
            config.read(env['EC2_INI_PATH'])
            assert 'ec2' in config.sections()
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)
        assert self.instance.job_env['AWS_SECRET_ACCESS_KEY'] == tasks.HIDDEN_PASSWORD

    def test_vmware_source(self):
        vmware = CredentialType.defaults['vmware']()
        self.instance.source = 'vmware'

        def get_cred():
            cred = Credential(
                pk=1,
                credential_type=vmware,
                inputs = {'username': 'bob', 'password': 'secret', 'host': 'https://example.org'}
            )
            cred.inputs['password'] = encrypt_field(cred, 'password')
            return cred
        self.instance.get_cloud_credential = get_cred

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args

            config = configparser.ConfigParser()
            config.read(env['VMWARE_INI_PATH'])
            assert config.get('vmware', 'username') == 'bob'
            assert config.get('vmware', 'password') == 'secret'
            assert config.get('vmware', 'server') == 'https://example.org'
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_azure_rm_source_with_tenant(self):
        azure_rm = CredentialType.defaults['azure_rm']()
        self.instance.source = 'azure_rm'
        self.instance.source_regions = 'north, south, east, west'

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
        self.instance.get_cloud_credential = get_cred
        self.instance.source_vars = {
            'include_powerstate': 'yes',
            'group_by_resource_group': 'no'
        }

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert env['AZURE_CLIENT_ID'] == 'some-client'
            assert env['AZURE_SECRET'] == 'some-secret'
            assert env['AZURE_TENANT'] == 'some-tenant'
            assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'
            assert env['AZURE_CLOUD_ENVIRONMENT'] == 'foobar'

            config = configparser.ConfigParser()
            config.read(env['AZURE_INI_PATH'])
            assert config.get('azure', 'include_powerstate') == 'yes'
            assert config.get('azure', 'group_by_resource_group') == 'no'
            assert config.get('azure', 'group_by_location') == 'yes'
            assert 'group_by_security_group' not in config.items('azure')
            assert config.get('azure', 'group_by_tag') == 'yes'
            assert config.get('azure', 'locations') == 'north,south,east,west'
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)
        assert self.instance.job_env['AZURE_SECRET'] == tasks.HIDDEN_PASSWORD

    def test_azure_rm_source_with_password(self):
        azure_rm = CredentialType.defaults['azure_rm']()
        self.instance.source = 'azure_rm'
        self.instance.source_regions = 'all'

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
        self.instance.get_cloud_credential = get_cred
        self.instance.source_vars = {
            'include_powerstate': 'yes',
            'group_by_resource_group': 'no',
            'group_by_security_group': 'no'
        }

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'
            assert env['AZURE_AD_USER'] == 'bob'
            assert env['AZURE_PASSWORD'] == 'secret'
            assert env['AZURE_CLOUD_ENVIRONMENT'] == 'foobar'

            config = configparser.ConfigParser()
            config.read(env['AZURE_INI_PATH'])
            assert config.get('azure', 'include_powerstate') == 'yes'
            assert config.get('azure', 'group_by_resource_group') == 'no'
            assert config.get('azure', 'group_by_location') == 'yes'
            assert config.get('azure', 'group_by_security_group') == 'no'
            assert config.get('azure', 'group_by_tag') == 'yes'
            assert 'locations' not in config.items('azure')
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)
        assert self.instance.job_env['AZURE_PASSWORD'] == tasks.HIDDEN_PASSWORD

    def test_gce_source(self):
        gce = CredentialType.defaults['gce']()
        self.instance.source = 'gce'
        self.instance.source_regions = 'all'

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
        self.instance.get_cloud_credential = get_cred

        expected_gce_zone = ''

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert env['GCE_ZONE'] == expected_gce_zone
            json_data = json.load(open(env['GCE_CREDENTIALS_FILE_PATH'], 'rb'))
            assert json_data['type'] == 'service_account'
            assert json_data['private_key'] == self.EXAMPLE_PRIVATE_KEY
            assert json_data['client_email'] == 'bob'
            assert json_data['project_id'] == 'some-project'

            config = configparser.ConfigParser()
            config.read(env['GCE_INI_PATH'])
            assert 'cache' in config.sections()
            assert config.getint('cache', 'cache_max_age') == 0

            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

        self.instance.source_regions = 'us-east-4'
        expected_gce_zone = 'us-east-4'
        self.task.run(self.pk)

    def test_openstack_source(self):
        openstack = CredentialType.defaults['openstack']()
        self.instance.source = 'openstack'

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
        self.instance.get_cloud_credential = get_cred

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
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
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_satellite6_source(self):
        satellite6 = CredentialType.defaults['satellite6']()
        self.instance.source = 'satellite6'

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
        self.instance.get_cloud_credential = get_cred

        self.instance.source_vars = '{"satellite6_group_patterns": "[a,b,c]", "satellite6_group_prefix": "hey_", "satellite6_want_hostcollections": True}'

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            config = configparser.ConfigParser()
            config.read(env['FOREMAN_INI_PATH'])
            assert config.get('foreman', 'url') == 'https://example.org'
            assert config.get('foreman', 'user') == 'bob'
            assert config.get('foreman', 'password') == 'secret'
            assert config.get('ansible', 'group_patterns') == '[a,b,c]'
            assert config.get('ansible', 'group_prefix') == 'hey_'
            assert config.get('ansible', 'want_hostcollections') == 'True'
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_cloudforms_source(self):
        cloudforms = CredentialType.defaults['cloudforms']()
        self.instance.source = 'cloudforms'

        def get_cred():
            cred = Credential(
                pk=1,
                credential_type=cloudforms,
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
        self.instance.get_cloud_credential = get_cred

        self.instance.source_vars = '{"prefer_ipv4": True}'

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            config = configparser.ConfigParser()
            config.read(env['CLOUDFORMS_INI_PATH'])
            assert config.get('cloudforms', 'url') == 'https://example.org'
            assert config.get('cloudforms', 'username') == 'bob'
            assert config.get('cloudforms', 'password') == 'secret'
            assert config.get('cloudforms', 'ssl_verify') == 'false'
            assert config.get('cloudforms', 'prefer_ipv4') == 'True'

            cache_path = config.get('cache', 'path')
            assert cache_path.startswith(env['AWX_PRIVATE_DATA_DIR'])
            assert os.path.isdir(cache_path)
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    @pytest.mark.parametrize('verify', [True, False])
    def test_tower_source(self, verify):
        tower = CredentialType.defaults['tower']()
        self.instance.source = 'tower'
        self.instance.instance_filters = '12345'
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
        self.instance.get_cloud_credential = get_cred

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert env['TOWER_HOST'] == 'https://tower.example.org'
            assert env['TOWER_USERNAME'] == 'bob'
            assert env['TOWER_PASSWORD'] == 'secret'
            assert env['TOWER_INVENTORY'] == '12345'
            if verify:
                assert env['TOWER_VERIFY_SSL'] == 'True'
            else:
                assert env['TOWER_VERIFY_SSL'] == 'False'
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)
        assert self.instance.job_env['TOWER_PASSWORD'] == tasks.HIDDEN_PASSWORD

    def test_tower_source_ssl_verify_empty(self):
        tower = CredentialType.defaults['tower']()
        self.instance.source = 'tower'
        self.instance.instance_filters = '12345'
        inputs = {
            'host': 'https://tower.example.org',
            'username': 'bob',
            'password': 'secret',
        }

        def get_cred():
            cred = Credential(pk=1, credential_type=tower, inputs = inputs)
            cred.inputs['password'] = encrypt_field(cred, 'password')
            return cred
        self.instance.get_cloud_credential = get_cred

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert env['TOWER_VERIFY_SSL'] == 'False'
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_awx_task_env(self):
        gce = CredentialType.defaults['gce']()
        self.instance.source = 'gce'

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
        self.instance.get_cloud_credential = get_cred

        with mock.patch('awx.main.tasks.settings.AWX_TASK_ENV', {'FOO': 'BAR'}):
            self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args
        assert env['FOO'] == 'BAR'



def test_os_open_oserror():
    with pytest.raises(OSError):
        os.open('this_file_does_not_exist', os.O_RDONLY)


def test_fcntl_ioerror():
    with pytest.raises(OSError):
        fcntl.flock(99999, fcntl.LOCK_EX)


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

    with pytest.raises(OSError, message='dummy message'):
        ProjectUpdate.acquire_lock(instance)
    assert logger.err.called_with("I/O error({0}) while trying to open lock file [{1}]: {2}".format(3, 'this_file_does_not_exist', 'dummy message'))


@mock.patch('os.open')
@mock.patch('os.close')
@mock.patch('logging.getLogger')
@mock.patch('fcntl.flock')
def test_aquire_lock_acquisition_fail_logged(fcntl_flock, logging_getLogger, os_close, os_open):
    err = IOError()
    err.errno = 3
    err.strerror = 'dummy message'

    instance = mock.Mock()
    instance.get_lock_file.return_value = 'this_file_does_not_exist'
    instance.cancel_flag = False

    os_open.return_value = 3

    logger = mock.Mock()
    logging_getLogger.return_value = logger

    fcntl_flock.side_effect = err

    ProjectUpdate = tasks.RunProjectUpdate()
    with pytest.raises(IOError, message='dummy message'):
        ProjectUpdate.acquire_lock(instance)
    os_close.assert_called_with(3)
    assert logger.err.called_with("I/O error({0}) while trying to aquire lock on file [{1}]: {2}".format(3, 'this_file_does_not_exist', 'dummy message'))
