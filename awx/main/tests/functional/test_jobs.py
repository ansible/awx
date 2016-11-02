from awx.main.models import Job

import pytest

@pytest.mark.django_db
def test_orphan_unified_job_creation(instance, inventory):
    job = Job.objects.create(job_template=None, inventory=inventory, name='hi world')
    job2 = job.copy()
    assert job2.job_template is None
    assert job2.inventory == inventory
    assert job2.name == 'hi world'
