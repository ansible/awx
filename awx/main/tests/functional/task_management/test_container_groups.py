import subprocess
import base64
from collections import namedtuple

from unittest import mock  # noqa
import pytest

from awx.main.tasks.receptor import AWXReceptorJob
from awx.main.utils import (
    create_temporary_fifo,
)


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
