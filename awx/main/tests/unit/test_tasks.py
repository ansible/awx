from contextlib import contextmanager
from datetime import datetime
from functools import partial
import ConfigParser
import json
import os
import re
import shutil
import tempfile

import fcntl
import mock
import pytest
import yaml
from django.conf import settings


from awx.main.models import (
    Credential,
    CredentialType,
    Inventory,
    InventorySource,
    InventoryUpdate,
    Job,
    Notification,
    Project,
    ProjectUpdate,
    UnifiedJob,
)

from awx.main import tasks
from awx.main.utils import encrypt_field



@contextmanager
def apply_patches(_patches):
    [p.start() for p in _patches]
    yield
    [p.stop() for p in _patches]


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
        assert tasks.handle_work_success(None, task_data) is None


def test_send_notifications_list(mocker):
    patches = list()

    mock_job = mocker.MagicMock(spec=UnifiedJob)
    patches.append(mocker.patch('awx.main.models.UnifiedJob.objects.get', return_value=mock_job))

    mock_notifications = [mocker.MagicMock(spec=Notification, subject="test", body={'hello': 'world'})]
    patches.append(mocker.patch('awx.main.models.Notification.objects.filter', return_value=mock_notifications))

    with apply_patches(patches):
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
    task = tasks.RunJob()
    assert task.build_safe_env({key: value})[key] == tasks.HIDDEN_PASSWORD


def test_safe_env_returns_new_copy():
    task = tasks.RunJob()
    env = {'foo': 'bar'}
    assert task.build_safe_env(env) is not env


def test_openstack_client_config_generation(mocker):
    update = tasks.RunInventoryUpdate()
    inventory_update = mocker.Mock(**{
        'source': 'openstack',
        'credential.host': 'https://keystone.openstack.example.org',
        'credential.username': 'demo',
        'credential.password': 'secrete',
        'credential.project': 'demo-project',
        'credential.domain': 'my-demo-domain',
        'source_vars_dict': {}
    })
    cloud_config = update.build_private_data(inventory_update)
    cloud_credential = yaml.load(
        cloud_config.get('credentials')[inventory_update.credential]
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
            'private': True
        }
    }


@pytest.mark.parametrize("source,expected", [
    (False, False), (True, True)
])
def test_openstack_client_config_generation_with_private_source_vars(mocker, source, expected):
    update = tasks.RunInventoryUpdate()
    inventory_update = mocker.Mock(**{
        'source': 'openstack',
        'credential.host': 'https://keystone.openstack.example.org',
        'credential.username': 'demo',
        'credential.password': 'secrete',
        'credential.project': 'demo-project',
        'credential.domain': None,
        'source_vars_dict': {'private': source}
    })
    cloud_config = update.build_private_data(inventory_update)
    cloud_credential = yaml.load(
        cloud_config.get('credentials')[inventory_update.credential]
    )
    assert cloud_credential['clouds'] == {
        'devstack': {
            'auth': {
                'auth_url': 'https://keystone.openstack.example.org',
                'password': 'secrete',
                'project_name': 'demo-project',
                'username': 'demo'
            },
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


class TestJobExecution:
    """
    For job runs, test that `ansible-playbook` is invoked with the proper
    arguments, environment variables, and pexpect passwords for a variety of
    credential types.
    """

    TASK_CLS = tasks.RunJob
    EXAMPLE_PRIVATE_KEY = '-----BEGIN PRIVATE KEY-----\nxyz==\n-----END PRIVATE KEY-----'

    def setup_method(self, method):
        if not os.path.exists(settings.PROJECTS_ROOT):
            os.mkdir(settings.PROJECTS_ROOT)
        self.project_path = tempfile.mkdtemp(prefix='awx_project_')
        with open(os.path.join(self.project_path, 'helloworld.yml'), 'w') as f:
            f.write('---')

        # The primary goal of these tests is to mock our `run_pexpect` call
        # and make assertions about the arguments and environment passed to it.
        self.run_pexpect = mock.Mock()
        self.run_pexpect.return_value = ['successful', 0]

        self.patches = [
            mock.patch.object(Project, 'get_project_path', lambda *a, **kw: self.project_path),
            # don't emit websocket statuses; they use the DB and complicate testing
            mock.patch.object(UnifiedJob, 'websocket_emit_status', mock.Mock()),
            mock.patch.object(Job, 'inventory', mock.Mock(pk=1, spec_set=['pk'])),
            mock.patch('awx.main.expect.run.run_pexpect', self.run_pexpect)
        ]
        for p in self.patches:
            p.start()

        self.instance = self.get_instance()

        def status_side_effect(pk, **kwargs):
            # If `Job.update_model` is called, we're not actually persisting
            # to the database; just update the status, which is usually
            # the update we care about for testing purposes
            if 'status' in kwargs:
                self.instance.status = kwargs['status']
            return self.instance

        self.task = self.TASK_CLS()
        self.task.update_model = mock.Mock(side_effect=status_side_effect)

        # ignore pre-run and post-run hooks, they complicate testing in a variety of ways
        self.task.pre_run_hook = self.task.post_run_hook = self.task.final_run_hook = mock.Mock()

    def teardown_method(self, method):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.project_path, True)

    def get_instance(self):
        job = Job(
            pk=1,
            created=datetime.utcnow(),
            status='new',
            job_type='run',
            cancel_flag=False,
            project=Project(),
            playbook='helloworld.yml',
            verbosity=3
        )

        # mock the job.extra_credentials M2M relation so we can avoid DB access
        job._extra_credentials = []
        patch = mock.patch.object(Job, 'extra_credentials', mock.Mock(
            all=lambda: job._extra_credentials,
            add=job._extra_credentials.append,
            spec_set=['all', 'add']
        ))
        self.patches.append(patch)
        patch.start()

        return job

    @property
    def pk(self):
        return self.instance.pk


class TestGenericRun(TestJobExecution):

    def test_cancel_flag(self):
        self.instance.cancel_flag = True
        with pytest.raises(Exception):
            self.task.run(self.pk)
        for c in [
            mock.call(self.pk, execution_node=settings.CLUSTER_HOST_ID, status='running'),
            mock.call(self.pk, output_replacements=[], result_traceback=mock.ANY, status='canceled')
        ]:
            assert c in self.task.update_model.call_args_list

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

    def test_uses_bubblewrap(self):
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args
        assert args[0] == 'bwrap'

    def test_bwrap_virtualenvs_are_readonly(self):
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args
        assert '--ro-bind %s %s' % (settings.ANSIBLE_VENV_PATH, settings.ANSIBLE_VENV_PATH) in ' '.join(args)  # noqa
        assert '--ro-bind %s %s' % (settings.AWX_VENV_PATH, settings.AWX_VENV_PATH) in ' '.join(args)  # noqa

    def test_awx_task_env(self):
        patch = mock.patch('awx.main.tasks.settings.AWX_TASK_ENV', {'FOO': 'BAR'})
        patch.start()

        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args
        assert env['FOO'] == 'BAR'


class TestIsolatedExecution(TestJobExecution):

    REMOTE_HOST = 'some-isolated-host'

    def test_with_ssh_credentials(self):
        mock_get = mock.Mock()
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
        self.instance.credential = credential

        private_data = tempfile.mkdtemp(prefix='awx_')
        self.task.build_private_data_dir = mock.Mock(return_value=private_data)
        inventory = json.dumps({"all": {"hosts": ["localhost"]}})

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

        with mock.patch('time.sleep'):
            with mock.patch('requests.get') as mock_get:
                mock_get.return_value = mock.Mock(content=inventory)
                self.task.run(self.pk, self.REMOTE_HOST)
                assert mock_get.call_count == 1
                assert mock.call(
                    'http://127.0.0.1:8013/api/v1/inventories/1/script/?hostvars=1',
                    auth=mock.ANY
                ) in mock_get.call_args_list

        playbook_run = self.run_pexpect.call_args_list[0][0]
        assert ' '.join(playbook_run[0]).startswith(' '.join([
            'ansible-playbook', 'run_isolated.yml', '-u', settings.AWX_ISOLATED_USERNAME,
            '-T', str(settings.AWX_ISOLATED_CONNECTION_TIMEOUT), '-i', self.REMOTE_HOST + ',',
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
        self.instance.credential = credential

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
                    self.task.run(self.pk, self.REMOTE_HOST)


class TestJobCredentials(TestJobExecution):

    parametrize = {
        'test_ssh_passwords': [
            dict(field='password', password_name='ssh_password', expected_flag='--ask-pass'),
            dict(field='ssh_key_unlock', password_name='ssh_key_unlock', expected_flag=None),
            dict(field='become_password', password_name='become_password', expected_flag='--ask-become-pass'),
        ]
    }

    def test_ssh_passwords(self, field, password_name, expected_flag):
        ssh = CredentialType.defaults['ssh']()
        credential = Credential(
            pk=1,
            credential_type=ssh,
            inputs = {'username': 'bob', field: 'secret'}
        )
        credential.inputs[field] = encrypt_field(credential, field)
        self.instance.credential = credential
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, call_kwargs = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert 'secret' in call_kwargs.get('expect_passwords').values()
        assert '-u bob' in ' '.join(args)
        if expected_flag:
            assert expected_flag in ' '.join(args)

    def test_vault_password(self):
        vault = CredentialType.defaults['vault']()
        credential = Credential(
            pk=1,
            credential_type=vault,
            inputs={'vault_password': 'vault-me'}
        )
        credential.inputs['vault_password'] = encrypt_field(credential, 'vault_password')
        self.instance.vault_credential = credential
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, call_kwargs = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert call_kwargs.get('expect_passwords')[
            re.compile(r'Vault password:\s*?$', re.M)
        ] == 'vault-me'
        assert '--ask-vault-pass' in ' '.join(args)

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
        self.instance.credential = credential

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
        self.instance.extra_credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['AWS_ACCESS_KEY_ID'] == 'bob'
        assert env['AWS_SECRET_ACCESS_KEY'] == 'secret'
        assert 'AWS_SECURITY_TOKEN' not in env

    def test_aws_cloud_credential_with_sts_token(self):
        aws = CredentialType.defaults['aws']()
        credential = Credential(
            pk=1,
            credential_type=aws,
            inputs = {'username': 'bob', 'password': 'secret', 'security_token': 'token'}
        )
        for key in ('password', 'security_token'):
            credential.inputs[key] = encrypt_field(credential, key)
        self.instance.extra_credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['AWS_ACCESS_KEY_ID'] == 'bob'
        assert env['AWS_SECRET_ACCESS_KEY'] == 'secret'
        assert env['AWS_SECURITY_TOKEN'] == 'token'

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
        self.instance.extra_credentials.add(credential)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert env['GCE_EMAIL'] == 'bob'
            assert env['GCE_PROJECT'] == 'some-project'
            ssh_key_data = env['GCE_PEM_FILE_PATH']
            assert open(ssh_key_data, 'rb').read() == self.EXAMPLE_PRIVATE_KEY
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
        self.instance.extra_credentials.add(credential)

        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['AZURE_CLIENT_ID'] == 'some-client'
        assert env['AZURE_SECRET'] == 'some-secret'
        assert env['AZURE_TENANT'] == 'some-tenant'
        assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'

    def test_azure_rm_with_password(self):
        azure = CredentialType.defaults['azure_rm']()
        credential = Credential(
            pk=1,
            credential_type=azure,
            inputs = {
                'subscription': 'some-subscription',
                'username': 'bob',
                'password': 'secret'
            }
        )
        credential.inputs['password'] = encrypt_field(credential, 'password')
        self.instance.extra_credentials.add(credential)

        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'
        assert env['AZURE_AD_USER'] == 'bob'
        assert env['AZURE_PASSWORD'] == 'secret'

    def test_vmware_credentials(self):
        vmware = CredentialType.defaults['vmware']()
        credential = Credential(
            pk=1,
            credential_type=vmware,
            inputs = {'username': 'bob', 'password': 'secret', 'host': 'https://example.org'}
        )
        credential.inputs['password'] = encrypt_field(credential, 'password')
        self.instance.extra_credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['VMWARE_USER'] == 'bob'
        assert env['VMWARE_PASSWORD'] == 'secret'
        assert env['VMWARE_HOST'] == 'https://example.org'

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
        self.instance.extra_credentials.add(credential)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            shade_config = open(env['OS_CLIENT_CONFIG_FILE'], 'rb').read()
            assert shade_config == '\n'.join([
                'clouds:',
                '  devstack:',
                '    auth:',
                '      auth_url: https://keystone.example.org',
                '      password: secret',
                '      project_name: tenant-name',
                '      username: bob',
                ''
            ])
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_net_credentials(self):
        net = CredentialType.defaults['net']()
        credential = Credential(
            pk=1,
            credential_type=net,
            inputs = {
                'username': 'bob',
                'password': 'secret',
                'ssh_key_data': self.EXAMPLE_PRIVATE_KEY,
                'authorize': True,
                'authorize_password': 'authorizeme'
            }
        )
        for field in ('password', 'ssh_key_data', 'authorize_password'):
            credential.inputs[field] = encrypt_field(credential, field)
        self.instance.extra_credentials.add(credential)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert env['ANSIBLE_NET_USERNAME'] == 'bob'
            assert env['ANSIBLE_NET_PASSWORD'] == 'secret'
            assert env['ANSIBLE_NET_AUTHORIZE'] == '1'
            assert env['ANSIBLE_NET_AUTH_PASS'] == 'authorizeme'
            assert open(env['ANSIBLE_NET_SSH_KEYFILE'], 'rb').read() == self.EXAMPLE_PRIVATE_KEY
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

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
        self.instance.extra_credentials.add(credential)
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
        self.instance.extra_credentials.add(credential)
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
        self.instance.extra_credentials.add(credential)
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
        self.instance.extra_credentials.add(credential)
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
        self.instance.extra_credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert env['MY_CLOUD_PRIVATE_VAR'] == 'SUPER-SECRET-123'
        assert 'SUPER-SECRET-123' not in json.dumps(self.task.update_model.call_args_list)

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
        self.instance.extra_credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert '-e {"api_token": "ABC123"}' in ' '.join(args)

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
        self.instance.extra_credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args
        assert '-e {"turbo_button": "True"}' in ' '.join(args)

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
        self.instance.extra_credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args
        assert '-e {"turbo_button": "FAST!"}' in ' '.join(args)

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
        self.instance.extra_credentials.add(credential)
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert '-e {"password": "SUPER-SECRET-123"}' in ' '.join(args)
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
        self.instance.extra_credentials.add(credential)
        self.task.run(self.pk)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert open(env['MY_CLOUD_INI_FILE'], 'rb').read() == '[mycloud]\nABC123'
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
        self.instance.extra_credentials.add(gce_credential)

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
        azure_rm_credential.inputs['secret'] = encrypt_field(azure_rm_credential, 'secret')
        self.instance.extra_credentials.add(azure_rm_credential)

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args

            assert env['AZURE_SUBSCRIPTION_ID'] == 'some-subscription'
            assert env['AZURE_AD_USER'] == 'bob'
            assert env['AZURE_PASSWORD'] == 'secret'

            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_awx_task_env(self):
        patch = mock.patch('awx.main.tasks.settings.AWX_TASK_ENV', {'FOO': 'BAR'})
        patch.start()

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
        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, call_kwargs = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args

        assert ' '.join(args).startswith('bwrap')
        ' '.join([
            '--bind',
            settings.PROJECTS_ROOT,
            settings.PROJECTS_ROOT,
        ]) in ' '.join(args)
        assert '"scm_revision_output": "/projects/tmp' in ' '.join(args)

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
        patch = mock.patch('awx.main.tasks.settings.AWX_TASK_ENV', {'FOO': 'BAR'})
        patch.start()

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

    def test_source_without_credential(self):
        self.instance.source = 'ec2'

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args

            assert 'AWS_ACCESS_KEY_ID' not in env
            assert 'AWS_SECRET_ACCESS_KEY' not in env
            assert 'EC2_INI_PATH' in env

            config = ConfigParser.ConfigParser()
            config.read(env['EC2_INI_PATH'])
            assert 'ec2' in config.sections()
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_ec2_source(self):
        aws = CredentialType.defaults['aws']()
        self.instance.source = 'ec2'
        self.instance.credential = Credential(
            pk=1,
            credential_type=aws,
            inputs = {'username': 'bob', 'password': 'secret'}
        )
        self.instance.credential.inputs['password'] = encrypt_field(
            self.instance.credential, 'password'
        )

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args

            assert env['AWS_ACCESS_KEY_ID'] == 'bob'
            assert env['AWS_SECRET_ACCESS_KEY'] == 'secret'
            assert 'EC2_INI_PATH' in env

            config = ConfigParser.ConfigParser()
            config.read(env['EC2_INI_PATH'])
            assert 'ec2' in config.sections()
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_vmware_source(self):
        vmware = CredentialType.defaults['vmware']()
        self.instance.source = 'vmware'
        self.instance.credential = Credential(
            pk=1,
            credential_type=vmware,
            inputs = {'username': 'bob', 'password': 'secret', 'host': 'https://example.org'}
        )
        self.instance.credential.inputs['password'] = encrypt_field(
            self.instance.credential, 'password'
        )

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args

            config = ConfigParser.ConfigParser()
            config.read(env['VMWARE_INI_PATH'])
            assert config.get('vmware', 'username') == 'bob'
            assert config.get('vmware', 'password') == 'secret'
            assert config.get('vmware', 'server') == 'https://example.org'
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_gce_source(self):
        gce = CredentialType.defaults['gce']()
        self.instance.source = 'gce'
        self.instance.source_regions = 'all'
        self.instance.credential = Credential(
            pk=1,
            credential_type=gce,
            inputs = {
                'username': 'bob',
                'project': 'some-project',
                'ssh_key_data': self.EXAMPLE_PRIVATE_KEY
            }
        )
        self.instance.credential.inputs['ssh_key_data'] = encrypt_field(
            self.instance.credential, 'ssh_key_data'
        )
        expected_gce_zone = ''

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            assert env['GCE_EMAIL'] == 'bob'
            assert env['GCE_PROJECT'] == 'some-project'
            assert env['GCE_ZONE'] == expected_gce_zone
            ssh_key_data = env['GCE_PEM_FILE_PATH']
            assert open(ssh_key_data, 'rb').read() == self.EXAMPLE_PRIVATE_KEY
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

        self.instance.source_regions = 'us-east-4'
        expected_gce_zone = 'us-east-4'
        self.task.run(self.pk)

    def test_openstack_source(self):
        openstack = CredentialType.defaults['openstack']()
        self.instance.source = 'openstack'
        self.instance.credential = Credential(
            pk=1,
            credential_type=openstack,
            inputs = {
                'username': 'bob',
                'password': 'secret',
                'project': 'tenant-name',
                'host': 'https://keystone.example.org'
            }
        )
        self.instance.credential.inputs['ssh_key_data'] = encrypt_field(
            self.instance.credential, 'ssh_key_data'
        )

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            shade_config = open(env['OS_CLIENT_CONFIG_FILE'], 'rb').read()
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
        self.instance.credential = Credential(
            pk=1,
            credential_type=satellite6,
            inputs = {
                'username': 'bob',
                'password': 'secret',
                'host': 'https://example.org'
            }
        )
        self.instance.credential.inputs['password'] = encrypt_field(
            self.instance.credential, 'password'
        )
        self.instance.source_vars = '{"satellite6_group_patterns": "[a,b,c]", "satellite6_group_prefix": "hey_"}'

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            config = ConfigParser.ConfigParser()
            config.read(env['FOREMAN_INI_PATH'])
            assert config.get('foreman', 'url') == 'https://example.org'
            assert config.get('foreman', 'user') == 'bob'
            assert config.get('foreman', 'password') == 'secret'
            assert config.get('ansible', 'group_patterns') == '[a,b,c]'
            assert config.get('ansible', 'group_prefix') == 'hey_'
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_cloudforms_source(self):
        cloudforms = CredentialType.defaults['cloudforms']()
        self.instance.source = 'cloudforms'
        self.instance.credential = Credential(
            pk=1,
            credential_type=cloudforms,
            inputs = {
                'username': 'bob',
                'password': 'secret',
                'host': 'https://example.org'
            }
        )
        self.instance.credential.inputs['password'] = encrypt_field(
            self.instance.credential, 'password'
        )

        def run_pexpect_side_effect(*args, **kwargs):
            args, cwd, env, stdout = args
            config = ConfigParser.ConfigParser()
            config.read(env['CLOUDFORMS_INI_PATH'])
            assert config.get('cloudforms', 'url') == 'https://example.org'
            assert config.get('cloudforms', 'username') == 'bob'
            assert config.get('cloudforms', 'password') == 'secret'
            assert config.get('cloudforms', 'ssl_verify') == 'false'
            return ['successful', 0]

        self.run_pexpect.side_effect = run_pexpect_side_effect
        self.task.run(self.pk)

    def test_awx_task_env(self):
        gce = CredentialType.defaults['gce']()
        self.instance.source = 'gce'
        self.instance.credential = Credential(
            pk=1,
            credential_type=gce,
            inputs = {
                'username': 'bob',
                'project': 'some-project',
            }
        )
        patch = mock.patch('awx.main.tasks.settings.AWX_TASK_ENV', {'FOO': 'BAR'})
        patch.start()

        self.task.run(self.pk)

        assert self.run_pexpect.call_count == 1
        call_args, _ = self.run_pexpect.call_args_list[0]
        args, cwd, env, stdout = call_args
        assert env['FOO'] == 'BAR'



def test_os_open_oserror():
    with pytest.raises(OSError):
        os.open('this_file_does_not_exist', os.O_RDONLY)


def test_fcntl_ioerror():
    with pytest.raises(IOError):
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

    with pytest.raises(OSError, errno=3, strerror='dummy message'):
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

    os_open.return_value = 3

    logger = mock.Mock()
    logging_getLogger.return_value = logger

    fcntl_flock.side_effect = err

    ProjectUpdate = tasks.RunProjectUpdate()

    with pytest.raises(IOError, errno=3, strerror='dummy message'):
        ProjectUpdate.acquire_lock(instance)
    os_close.assert_called_with(3)
    assert logger.err.called_with("I/O error({0}) while trying to aquire lock on file [{1}]: {2}".format(3, 'this_file_does_not_exist', 'dummy message'))
