import pytest
from unittest import mock
from django.conf import settings

from awx.main.models import (
    InstanceGroup,
    Job,
    JobTemplate,
    Project,
    Inventory,
)
from awx.main.scheduler.kubernetes import PodManager


@pytest.fixture
def container_group():
    instance_group = mock.Mock(InstanceGroup(name='container-group'))

    return instance_group


@pytest.fixture
def job(container_group):
    return Job(pk=1,
               id=1,
               project=Project(),
               instance_group=container_group,
               inventory=Inventory(),
               job_template=JobTemplate(id=1, name='foo'))


def test_default_pod_spec(job):
    default_image = PodManager(job).pod_definition['spec']['containers'][0]['image']
    assert default_image == settings.AWX_CONTAINER_GROUP_DEFAULT_IMAGE


def test_custom_pod_spec(job):
    job.instance_group.pod_spec_override = """
    spec:
      containers:
        - image: my-custom-image
    """
    custom_image = PodManager(job).pod_definition['spec']['containers'][0]['image']
    assert custom_image == 'my-custom-image'


def test_pod_manager_namespace_property(job):
    pm = PodManager(job)
    assert pm.namespace == settings.AWX_CONTAINER_GROUP_DEFAULT_NAMESPACE

    job.instance_group.pod_spec_override = """
    metadata:
      namespace: my-namespace
    """
    assert PodManager(job).namespace == 'my-namespace'
