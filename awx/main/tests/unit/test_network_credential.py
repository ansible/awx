from awx.main.models.credential import Credential
from awx.main.models.jobs import Job
from awx.main.models.inventory import Inventory
from awx.main.tasks import RunJob

ssh_key_data = """-----BEGIN PRIVATE KEY-----\nstuff==\n-----END PRIVATE KEY-----"""

def test_net_cred_parse(mocker):
    opts = {
        'username':'test',
        'password':'test',
        'ssh_key_data': ssh_key_data,
        'become_method': 'sudo',
        'become_password': 'passwd',
    }

    with mocker.patch('django.db.ConnectionRouter.db_for_write'):
        job = Job(id=1)
        job.inventory = mocker.MagicMock(spec=Inventory, id=2)
        job.network_credential = Credential(**opts)

        run_job = RunJob()
        run_job.should_use_proot = False

        env = run_job.build_env(job, private_data_dir='/tmp')
        assert env['ANSIBLE_NET_USERNAME'] == opts['username']
        assert env['ANSIBLE_NET_PASSWORD'] == opts['password']
        assert env['ANSIBLE_NET_AUTHORIZE'] == '1'
        assert env['ANSIBLE_NET_AUTHORIZE_PASSWORD'] == opts['become_password']
