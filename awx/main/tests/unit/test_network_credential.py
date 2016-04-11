import pytest

from awx.main.models.credential import Credential
from awx.main.models.jobs import Job
from awx.main.models.inventory import Inventory
from awx.main.tasks import RunJob


@pytest.fixture
def options():
    return {
        'username':'test',
        'password':'test',
        'ssh_key_data': """-----BEGIN PRIVATE KEY-----\nstuff==\n-----END PRIVATE KEY-----""",
        'become_method': 'sudo',
        'become_password': 'passwd',
    }


def test_net_cred_parse(mocker, options):
    with mocker.patch('django.db.ConnectionRouter.db_for_write'):
        job = Job(id=1)
        job.inventory = mocker.MagicMock(spec=Inventory, id=2)
        job.network_credential = Credential(**options)

        run_job = RunJob()
        mocker.patch.object(run_job, 'should_use_proot', return_value=False)

        env = run_job.build_env(job, private_data_dir='/tmp')
        assert env['ANSIBLE_NET_USERNAME'] == options['username']
        assert env['ANSIBLE_NET_PASSWORD'] == options['password']
        assert env['ANSIBLE_NET_AUTHORIZE'] == '1'
        assert env['ANSIBLE_NET_AUTHORIZE_PASSWORD'] == options['become_password']


def test_net_cred_ssh_agent(mocker, options):
    with mocker.patch('django.db.ConnectionRouter.db_for_write'):
        run_job = RunJob()

        mock_job_attrs = {'forks': False, 'id': 1, 'cancel_flag': False, 'status': 'running', 'job_type': 'normal',
                          'credential': None, 'cloud_credential': None, 'network_credential': Credential(**options),
                          'become_enabled': False, 'become_method': None, 'become_username': None,
                          'inventory': mocker.MagicMock(spec=Inventory, id=2), 'force_handlers': False,
                          'limit': None, 'verbosity': None, 'job_tags': None, 'skip_tags': False,
                          'start_at_task': False, 'pk': 1, 'launch_type': 'normal', 'job_template':None,
                          'created_by': None, 'extra_vars_dict': None, 'project':None, 'playbook': 'test.yml'}
        mock_job = mocker.MagicMock(spec=Job, **mock_job_attrs)

        mocker.patch.object(run_job, 'update_model', return_value=mock_job)
        mocker.patch.object(run_job, 'build_cwd', return_value='/tmp')
        mocker.patch.object(run_job, 'should_use_proot', return_value=False)
        mocker.patch.object(run_job, 'run_pexpect', return_value=('successful', 0))
        mocker.patch.object(run_job, 'open_fifo_write', return_value=None)

        run_job.run(mock_job.id)
        assert run_job.update_model.call_count == 3

        job_args = run_job.update_model.call_args_list[1][1].get('job_args')
        assert 'ssh-add' in job_args
        assert 'ssh-agent' in job_args
        assert 'network_credential' in job_args
