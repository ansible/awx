import redis
import pytest
from unittest import mock
import json

from awx.main.models import (Job, Instance, JobHostSummary, InventoryUpdate,
                             InventorySource, Project, ProjectUpdate,
                             SystemJob, AdHocCommand)
from awx.main.tasks import cluster_node_heartbeat
from django.test.utils import override_settings


@pytest.mark.django_db
def test_orphan_unified_job_creation(instance, inventory):
    job = Job.objects.create(job_template=None, inventory=inventory, name='hi world')
    job2 = job.copy_unified_job()
    assert job2.job_template is None
    assert job2.inventory == inventory
    assert job2.name == 'hi world'
    assert job.job_type == job2.job_type
    assert job2.launch_type == 'relaunch'


@pytest.mark.django_db
@mock.patch('awx.main.utils.common.get_cpu_capacity', lambda: (2,8))
@mock.patch('awx.main.utils.common.get_mem_capacity', lambda: (8000,62))
def test_job_capacity_and_with_inactive_node():
    i = Instance.objects.create(hostname='test-1')
    with mock.patch.object(redis.client.Redis, 'ping', lambda self: True):
        i.refresh_capacity()
    assert i.capacity == 62
    i.enabled = False
    i.save()
    with override_settings(CLUSTER_HOST_ID=i.hostname):
        cluster_node_heartbeat()
        i = Instance.objects.get(id=i.id)
        assert i.capacity == 0


@pytest.mark.django_db
@mock.patch('awx.main.utils.common.get_cpu_capacity', lambda: (2,8))
@mock.patch('awx.main.utils.common.get_mem_capacity', lambda: (8000,62))
def test_job_capacity_with_redis_disabled():
    i = Instance.objects.create(hostname='test-1')

    def _raise(self):
        raise redis.ConnectionError()
    with mock.patch.object(redis.client.Redis, 'ping', _raise):
        i.refresh_capacity()
    assert i.capacity == 0


@pytest.mark.django_db
def test_job_type_name():
    job = Job.objects.create()
    assert job.job_type_name == 'job'

    ahc = AdHocCommand.objects.create()
    assert ahc.job_type_name == 'ad_hoc_command'

    source = InventorySource.objects.create(source='ec2')
    source.save()
    iu = InventoryUpdate.objects.create(
        inventory_source=source,
        source='ec2'
    )
    assert iu.job_type_name == 'inventory_update'

    proj = Project.objects.create()
    proj.save()
    pu = ProjectUpdate.objects.create(project=proj)
    assert pu.job_type_name == 'project_update'

    sjob = SystemJob.objects.create()
    assert sjob.job_type_name == 'system_job'


@pytest.mark.django_db
def test_job_notification_data(inventory, machine_credential, project):
    encrypted_str = "$encrypted$"
    job = Job.objects.create(
        job_template=None, inventory=inventory, name='hi world',
        extra_vars=json.dumps({"SSN": "123-45-6789"}),
        survey_passwords={"SSN": encrypted_str},
        project=project,
    )
    job.credentials.set([machine_credential])
    notification_data = job.notification_data(block=0)
    assert json.loads(notification_data['extra_vars'])['SSN'] == encrypted_str


@pytest.mark.django_db
def test_job_notification_host_data(inventory, machine_credential, project, job_template, host):
    job = Job.objects.create(
        job_template=job_template, inventory=inventory, name='hi world', project=project
    )
    JobHostSummary.objects.create(job=job, host=host, changed=1, dark=2, failures=3, ok=4, processed=3, skipped=2, rescued=1, ignored=0)
    assert job.notification_data()['hosts'] == {'single-host': 
                                                {'failed': True,
                                                    'changed': 1, 
                                                    'dark': 2, 
                                                    'failures': 3, 
                                                    'ok': 4, 
                                                    'processed': 3, 
                                                    'skipped': 2, 
                                                    'rescued': 1, 
                                                    'ignored': 0}}


@pytest.mark.django_db
class TestLaunchConfig:

    def test_null_creation_from_prompts(self):
        job = Job.objects.create()
        data = {
            "credentials": [],
            "extra_vars": {},
            "limit": None,
            "job_type": None
        }
        config = job.create_config_from_prompts(data)
        assert config is None

    def test_only_limit_defined(self, job_template):
        job = Job.objects.create(job_template=job_template)
        data = {
            "credentials": [],
            "extra_vars": {},
            "job_tags": None,
            "limit": ""
        }
        config = job.create_config_from_prompts(data)
        assert config.char_prompts == {"limit": ""}
        assert not config.credentials.exists()
        assert config.prompts_dict() == {"limit": ""}
