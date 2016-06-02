from awx.main.models import Job

import pytest

@pytest.mark.django_db
def test_job_blocking(get, post, job_template, inventory, inventory_factory):
    j1 = Job.objects.create(job_template=job_template,
                            inventory=inventory)
    j2 = Job.objects.create(job_template=job_template,
                            inventory=inventory)
    assert j1.is_blocked_by(j2)
    j2.inventory = inventory_factory(name='test-different-inventory')
    assert not j1.is_blocked_by(j2)
    j_callback_1 = Job.objects.create(job_template=job_template,
                                      inventory=inventory,
                                      launch_type='callback',
                                      limit='a')
    j_callback_2 = Job.objects.create(job_template=job_template,
                                      inventory=inventory,
                                      launch_type='callback',
                                      limit='a')
    assert j_callback_1.is_blocked_by(j_callback_2)
    j_callback_2.limit = 'b'
    assert not j_callback_1.is_blocked_by(j_callback_2)

@pytest.mark.django_db
def test_job_blocking_allow_simul(get, post, job_template, inventory):
    job_template.allow_simultaneous = True
    j1 = Job.objects.create(job_template=job_template,
                            inventory=inventory)
    j2 = Job.objects.create(job_template=job_template,
                            inventory=inventory)
    assert not j1.is_blocked_by(j2)
    assert not j2.is_blocked_by(j1)
    job_template.allow_simultaneous = False
    assert j1.is_blocked_by(j2)
    assert j2.is_blocked_by(j1)
