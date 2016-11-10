from awx.main.models import Job, Instance
from django.test.utils import override_settings
import pytest

@pytest.mark.django_db
def test_orphan_unified_job_creation(instance, inventory):
    job = Job.objects.create(job_template=None, inventory=inventory, name='hi world')
    job2 = job.copy()
    assert job2.job_template is None
    assert job2.inventory == inventory
    assert job2.name == 'hi world'

@pytest.mark.django_db
def test_job_capacity_and_with_inactive_node():
    Instance.objects.create(hostname='test-1', capacity=50)
    assert Instance.objects.total_capacity() == 50
    Instance.objects.create(hostname='test-2', capacity=50)
    assert Instance.objects.total_capacity() == 100
    with override_settings(AWX_ACTIVE_NODE_TIME=0):
        assert Instance.objects.total_capacity() < 100
