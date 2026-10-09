import subprocess
import base64
import json
from collections import namedtuple

from unittest import mock  # noqa
import pytest

from awx.main.tasks.receptor import AWXReceptorJob, upsert_pod_container_env
from awx.main.utils import (
    create_temporary_fifo,
)

from awx.main.scheduler import TaskManager

from . import create_job


@pytest.fixture
def containerized_job(default_instance_group, kube_credential, job_template_factory):
    default_instance_group.credential = kube_credential
    default_instance_group.is_container_group = True
    default_instance_group.save()
    objects = job_template_factory('jt', organization='org1', project='proj', inventory='inv', credential='cred', jobs=['my_job'])
    jt = objects.job_template
    jt.instance_groups.add(default_instance_group)

    j1 = objects.jobs['my_job']
    j1.instance_group = default_instance_group
    j1.status = 'pending'
    j1.save()
    return j1


@pytest.mark.django_db
def test_containerized_job(containerized_job):
    assert containerized_job.is_container_group_task
    assert containerized_job.instance_group.is_container_group
    assert containerized_job.instance_group.credential.kubernetes


@pytest.mark.django_db
def test_max_concurrent_jobs_blocks_start_of_new_jobs(controlplane_instance_group, containerized_job, mocker):
    """Construct a scenario where only 1 job will fit within the max_concurrent_jobs of the container group.

    Since max_concurrent_jobs is set to 1, even though 2 jobs are in pending
    and would be launched into the container group, only one will be started.
    """
    containerized_job.unified_job_template.allow_simultaneous = True
    containerized_job.unified_job_template.save()
    default_instance_group = containerized_job.instance_group
    default_instance_group.max_concurrent_jobs = 1
    default_instance_group.save()
    task_impact = 1
    # Create a second job that should not be scheduled at first, blocked by the other
    create_job(containerized_job.unified_job_template)
    tm = TaskManager()
    with mock.patch('awx.main.models.Job.task_impact', new_callable=mock.PropertyMock) as mock_task_impact:
        mock_task_impact.return_value = task_impact
        with mock.patch.object(TaskManager, "start_task", wraps=tm.start_task) as mock_job:
            tm.schedule()
            mock_job.assert_called_once()


@pytest.mark.django_db
def test_max_forks_blocks_start_of_new_jobs(controlplane_instance_group, containerized_job, mocker):
    """Construct a scenario where only 1 job will fit within the max_forks of the container group.

    In this case, we set the container_group max_forks to 10, and make the task_impact of a job 6.
    Therefore, only 1 job will fit within the max of 10.
    """
    containerized_job.unified_job_template.allow_simultaneous = True
    containerized_job.unified_job_template.save()
    default_instance_group = containerized_job.instance_group
    default_instance_group.max_forks = 10
    # Create a second job that should not be scheduled
    create_job(containerized_job.unified_job_template)
    tm = TaskManager()
    with mock.patch('awx.main.models.Job.task_impact', new_callable=mock.PropertyMock) as mock_task_impact:
        mock_task_impact.return_value = 6
        with mock.patch("awx.main.scheduler.TaskManager.start_task"):
            tm.schedule()
            tm.start_task.assert_called_once()


@pytest.mark.django_db
def test_kubectl_ssl_verification(containerized_job, default_job_execution_environment):
    containerized_job.execution_environment = default_job_execution_environment
    cred = containerized_job.instance_group.credential
    cred.inputs['verify_ssl'] = True
    key_material = subprocess.run('openssl genrsa 2> /dev/null', shell=True, check=True, stdout=subprocess.PIPE)
    key = create_temporary_fifo(key_material.stdout)
    cmd = f"""
    openssl req -x509 -sha256 -new -nodes \
      -key {key} -subj '/C=US/ST=North Carolina/L=Durham/O=Ansible/OU=AWX Development/CN=awx.localhost'
    """
    cert = subprocess.run(cmd.strip(), shell=True, check=True, stdout=subprocess.PIPE)
    cred.inputs['ssl_ca_cert'] = cert.stdout
    cred.save()
    RunJob = namedtuple('RunJob', ['instance', 'build_execution_environment_params'])
    rj = RunJob(instance=containerized_job, build_execution_environment_params=lambda x: {})
    receptor_job = AWXReceptorJob(rj, runner_params={'settings': {}})
    ca_data = receptor_job.kube_config['clusters'][0]['cluster']['certificate-authority-data']
    assert cert.stdout == base64.b64decode(ca_data.encode())


def _pod_env_map(pod_spec):
    """Map worker-container env names to literal values (valueFrom entries map to None)."""
    return {item['name']: item.get('value') for item in pod_spec['spec']['containers'][0].get('env', [])}


def _receptor_job_for_containerized(containerized_job):
    """Build an AWXReceptorJob around a container-group job with empty runner settings."""
    RunJob = namedtuple('RunJob', ['instance', 'build_execution_environment_params'])
    rj = RunJob(instance=containerized_job, build_execution_environment_params=lambda x: {})
    return AWXReceptorJob(rj, runner_params={'settings': {}})


def test_upsert_pod_container_env_appends_and_replaces():
    """New names are appended; a second write of the same name replaces the prior entry."""
    container = {}
    upsert_pod_container_env(container, 'HTTP_PROXY', 'http://first:3128')
    upsert_pod_container_env(container, 'HTTPS_PROXY', 1)
    upsert_pod_container_env(container, 'HTTP_PROXY', 'http://second:3128')
    assert container['env'] == [
        {'name': 'HTTPS_PROXY', 'value': '1'},
        {'name': 'HTTP_PROXY', 'value': 'http://second:3128'},
    ]


def test_upsert_pod_container_env_removes_duplicate_names():
    """All matching names are removed so a later duplicate cannot override the settings value."""
    container = {
        'env': [
            {'name': 'HTTP_PROXY', 'value': 'http://first:3128'},
            {'name': 'KEEP_ME', 'value': '1'},
            {'name': 'HTTP_PROXY', 'value': 'http://second:3128'},
        ]
    }
    upsert_pod_container_env(container, 'HTTP_PROXY', 'http://global-proxy:3128')
    assert container['env'] == [
        {'name': 'KEEP_ME', 'value': '1'},
        {'name': 'HTTP_PROXY', 'value': 'http://global-proxy:3128'},
    ]


def test_upsert_pod_container_env_escapes_kubelet_expansion():
    """Literal $ is doubled so kubelet does not expand $(VAR); already-escaped $$ stays even-parity."""
    container = {}
    upsert_pod_container_env(container, 'PATH_PREFIX', '$(HOME)/bin')
    upsert_pod_container_env(container, 'ALREADY_ESCAPED', '$$(HOME)')
    assert container['env'] == [
        {'name': 'PATH_PREFIX', 'value': '$$(HOME)/bin'},
        {'name': 'ALREADY_ESCAPED', 'value': '$$$$(HOME)'},
    ]


@pytest.mark.django_db
def test_pod_definition_includes_awx_task_env(containerized_job, default_job_execution_environment, settings):
    """AWX_TASK_ENV keys appear on the worker container; keepalive is omitted when disabled."""
    containerized_job.execution_environment = default_job_execution_environment
    settings.AWX_TASK_ENV = {'RUNNER_OMIT_EVENTS': 'True', 'HTTP_PROXY': 'http://proxy:3128'}
    settings.AWX_RUNNER_KEEPALIVE_SECONDS = 0

    pod_spec = _receptor_job_for_containerized(containerized_job).pod_definition
    env_map = _pod_env_map(pod_spec)
    assert env_map['RUNNER_OMIT_EVENTS'] == 'True'
    assert env_map['HTTP_PROXY'] == 'http://proxy:3128'
    assert 'ANSIBLE_RUNNER_KEEPALIVE_SECONDS' not in env_map


@pytest.mark.django_db
def test_pod_definition_empty_awx_task_env_omits_env(containerized_job, default_job_execution_environment, settings):
    """No env list is created when AWX_TASK_ENV is empty and keepalive is off."""
    containerized_job.execution_environment = default_job_execution_environment
    settings.AWX_TASK_ENV = {}
    settings.AWX_RUNNER_KEEPALIVE_SECONDS = 0

    pod_spec = _receptor_job_for_containerized(containerized_job).pod_definition
    assert 'env' not in pod_spec['spec']['containers'][0]


@pytest.mark.django_db
def test_pod_definition_keepalive_and_task_env(containerized_job, default_job_execution_environment, settings):
    """Keepalive seconds and AWX_TASK_ENV are both present on the worker container."""
    containerized_job.execution_environment = default_job_execution_environment
    settings.AWX_TASK_ENV = {'RUNNER_OMIT_EVENTS': 'True'}
    settings.AWX_RUNNER_KEEPALIVE_SECONDS = 30

    env_map = _pod_env_map(_receptor_job_for_containerized(containerized_job).pod_definition)
    assert env_map['RUNNER_OMIT_EVENTS'] == 'True'
    assert env_map['ANSIBLE_RUNNER_KEEPALIVE_SECONDS'] == '30'


@pytest.mark.django_db
def test_pod_definition_awx_task_env_overrides_pod_spec(containerized_job, default_job_execution_environment, settings):
    """Jobs settings extra env wins over instance-group pod_spec_override on the same name."""
    containerized_job.execution_environment = default_job_execution_environment
    containerized_job.instance_group.pod_spec_override = json.dumps(
        {
            'spec': {
                'containers': [
                    {
                        'name': 'worker',
                        'env': [
                            {'name': 'HTTP_PROXY', 'value': 'http://ig-proxy:3128'},
                            {'name': 'KEEP_ME', 'value': '1'},
                        ],
                    }
                ]
            }
        }
    )
    containerized_job.instance_group.save()
    settings.AWX_TASK_ENV = {'HTTP_PROXY': 'http://global-proxy:3128'}
    settings.AWX_RUNNER_KEEPALIVE_SECONDS = 0

    env_map = _pod_env_map(_receptor_job_for_containerized(containerized_job).pod_definition)
    assert env_map['HTTP_PROXY'] == 'http://global-proxy:3128'
    assert env_map['KEEP_ME'] == '1'


@pytest.mark.django_db
def test_pod_definition_awx_task_env_wins_over_duplicate_override(containerized_job, default_job_execution_environment, settings):
    """AWX_TASK_ENV wins even when pod_spec_override lists the same name more than once."""
    containerized_job.execution_environment = default_job_execution_environment
    containerized_job.instance_group.pod_spec_override = json.dumps(
        {
            'spec': {
                'containers': [
                    {
                        'name': 'worker',
                        'env': [
                            {'name': 'HTTP_PROXY', 'value': 'http://first:3128'},
                            {'name': 'KEEP_ME', 'value': '1'},
                            {'name': 'HTTP_PROXY', 'value': 'http://second:3128'},
                        ],
                    }
                ]
            }
        }
    )
    containerized_job.instance_group.save()
    settings.AWX_TASK_ENV = {'HTTP_PROXY': 'http://global-proxy:3128'}
    settings.AWX_RUNNER_KEEPALIVE_SECONDS = 0

    env_list = _receptor_job_for_containerized(containerized_job).pod_definition['spec']['containers'][0]['env']
    assert [item for item in env_list if item.get('name') == 'HTTP_PROXY'] == [{'name': 'HTTP_PROXY', 'value': 'http://global-proxy:3128'}]
    assert any(item.get('name') == 'KEEP_ME' and item.get('value') == '1' for item in env_list)


@pytest.mark.django_db
def test_pod_definition_awx_task_env_replaces_value_from(containerized_job, default_job_execution_environment, settings):
    """A colliding AWX_TASK_ENV key replaces a valueFrom entry with a plain value."""
    containerized_job.execution_environment = default_job_execution_environment
    containerized_job.instance_group.pod_spec_override = json.dumps(
        {
            'spec': {
                'containers': [
                    {
                        'name': 'worker',
                        'env': [
                            {
                                'name': 'HTTP_PROXY',
                                'valueFrom': {'secretKeyRef': {'name': 'proxy-secret', 'key': 'http_proxy'}},
                            },
                            {'name': 'KEEP_ME', 'value': '1'},
                        ],
                    }
                ]
            }
        }
    )
    containerized_job.instance_group.save()
    settings.AWX_TASK_ENV = {'HTTP_PROXY': 'http://global-proxy:3128'}
    settings.AWX_RUNNER_KEEPALIVE_SECONDS = 0

    env_list = _receptor_job_for_containerized(containerized_job).pod_definition['spec']['containers'][0]['env']
    proxy_entry = next(item for item in env_list if item['name'] == 'HTTP_PROXY')
    assert proxy_entry == {'name': 'HTTP_PROXY', 'value': 'http://global-proxy:3128'}
    assert any(item.get('name') == 'KEEP_ME' and item.get('value') == '1' for item in env_list)
