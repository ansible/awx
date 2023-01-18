import redis
import pytest
from unittest import mock
import json

from awx.main.models import (
    Job,
    Instance,
    JobHostSummary,
    InventoryUpdate,
    InventorySource,
    Project,
    ProjectUpdate,
    SystemJob,
    AdHocCommand,
    InstanceGroup,
    Label,
    ExecutionEnvironment,
)
from awx.main.tasks.system import cluster_node_heartbeat
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
@mock.patch('awx.main.tasks.system.inspect_execution_nodes', lambda *args, **kwargs: None)
@mock.patch('awx.main.models.ha.get_cpu_effective_capacity', lambda cpu: 8)
@mock.patch('awx.main.models.ha.get_mem_effective_capacity', lambda mem: 62)
def test_job_capacity_and_with_inactive_node():
    i = Instance.objects.create(hostname='test-1')
    i.save_health_data('18.0.1', 2, 8000)
    assert i.enabled is True
    assert i.capacity_adjustment == 1.0
    assert i.capacity == 62
    i.enabled = False
    i.save()
    with override_settings(CLUSTER_HOST_ID=i.hostname):
        with mock.patch.object(redis.client.Redis, 'ping', lambda self: True):
            cluster_node_heartbeat()
        i = Instance.objects.get(id=i.id)
        assert i.capacity == 0


@pytest.mark.django_db
@mock.patch('awx.main.models.ha.get_cpu_effective_capacity', lambda cpu: 8)
@mock.patch('awx.main.models.ha.get_mem_effective_capacity', lambda mem: 62)
def test_job_capacity_with_redis_disabled():
    i = Instance.objects.create(hostname='test-1')

    def _raise(self):
        raise redis.ConnectionError()

    with mock.patch.object(redis.client.Redis, 'ping', _raise):
        i.local_health_check()
    assert i.capacity == 0


@pytest.mark.django_db
def test_job_type_name():
    job = Job.objects.create()
    assert job.job_type_name == 'job'

    ahc = AdHocCommand.objects.create()
    assert ahc.job_type_name == 'ad_hoc_command'

    source = InventorySource.objects.create(source='ec2')
    source.save()
    iu = InventoryUpdate.objects.create(inventory_source=source, source='ec2')
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
        job_template=None,
        inventory=inventory,
        name='hi world',
        extra_vars=json.dumps({"SSN": "123-45-6789"}),
        survey_passwords={"SSN": encrypted_str},
        project=project,
    )
    job.credentials.set([machine_credential])
    notification_data = job.notification_data(block=0)
    assert json.loads(notification_data['extra_vars'])['SSN'] == encrypted_str


@pytest.mark.django_db
def test_job_notification_host_data(inventory, machine_credential, project, job_template, host):
    job = Job.objects.create(job_template=job_template, inventory=inventory, name='hi world', project=project)
    JobHostSummary.objects.create(job=job, host=host, changed=1, dark=2, failures=3, ok=4, processed=3, skipped=2, rescued=1, ignored=0)
    assert job.notification_data()['hosts'] == {
        'single-host': {'failed': True, 'changed': 1, 'dark': 2, 'failures': 3, 'ok': 4, 'processed': 3, 'skipped': 2, 'rescued': 1, 'ignored': 0}
    }


@pytest.mark.django_db
class TestLaunchConfig:
    def test_null_creation_from_prompts(self):
        job = Job.objects.create()
        data = {
            "credentials": [],
            "extra_vars": {},
            "limit": None,
            "job_type": None,
            "execution_environment": None,
            "instance_groups": None,
            "labels": None,
            "forks": None,
            "timeout": None,
            "job_slice_count": None,
        }
        config = job.create_config_from_prompts(data)
        assert config is None

    def test_only_limit_defined(self, job_template):
        job = Job.objects.create(job_template=job_template)
        data = {
            "credentials": [],
            "extra_vars": {},
            "job_tags": None,
            "limit": "",
            "execution_environment": None,
            "instance_groups": None,
            "labels": None,
            "forks": None,
            "timeout": None,
            "job_slice_count": None,
        }
        config = job.create_config_from_prompts(data)
        assert config.char_prompts == {"limit": ""}
        assert not config.credentials.exists()
        assert config.prompts_dict() == {"limit": ""}

    def test_many_to_many_fields(self, job_template, organization):
        job = Job.objects.create(job_template=job_template)
        ig1 = InstanceGroup.objects.create(name='bar')
        ig2 = InstanceGroup.objects.create(name='foo')
        job_template.instance_groups.add(ig2)
        label1 = Label.objects.create(name='foo', description='bar', organization=organization)
        label2 = Label.objects.create(name='faz', description='baz', organization=organization)
        # Order should matter here which is why we do 2 and then 1
        data = {
            "credentials": [],
            "extra_vars": {},
            "job_tags": None,
            "limit": None,
            "execution_environment": None,
            "instance_groups": [ig2, ig1],
            "labels": [label2, label1],
            "forks": None,
            "timeout": None,
            "job_slice_count": None,
        }
        config = job.create_config_from_prompts(data)

        assert config.instance_groups.exists()
        config_instance_group_ids = [item.id for item in config.instance_groups.all()]
        assert config_instance_group_ids == [ig2.id, ig1.id]

        assert config.labels.exists()
        config_label_ids = [item.id for item in config.labels.all()]
        assert config_label_ids == [label2.id, label1.id]

    def test_pk_field(self, job_template, organization):
        job = Job.objects.create(job_template=job_template)
        ee = ExecutionEnvironment.objects.create(name='test-ee', image='quay.io/foo/bar')
        # Order should matter here which is why we do 2 and then 1
        data = {
            "credentials": [],
            "extra_vars": {},
            "job_tags": None,
            "limit": None,
            "execution_environment": ee,
            "instance_groups": [],
            "labels": [],
            "forks": None,
            "timeout": None,
            "job_slice_count": None,
        }
        config = job.create_config_from_prompts(data)

        assert config.execution_environment
        # We just write the PK instead of trying to assign an item, that happens on the save
        assert config.execution_environment_id == ee.id
