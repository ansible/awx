"""
Tests for updating a parent object's ``modified``/``modified_by`` fields when
its instance group associations are changed.

Changing instance groups through the relationship sub-endpoint (for example
``/api/v2/job_templates/<id>/instance_groups/``) does not change any editable
field on the parent, so historically only ``modified`` was bumped (for cache
invalidation) while ``modified_by`` was left pointing at the previous editor.
"""

import pytest
from crum import impersonate
from rest_framework import status

from awx.api.versioning import reverse


@pytest.mark.django_db
def test_job_template_instance_group_attach_updates_modified_by(post, job_template, instance_group_factory, alice, admin):
    instance_group = instance_group_factory('test-ig')

    # Alice edits the template directly, making her the last modifier.
    with impersonate(alice):
        job_template.name = 'edited-by-alice'
        job_template.save()
    job_template.refresh_from_db()
    assert job_template.modified_by == alice
    original_modified = job_template.modified

    # An admin attaches an instance group via the relationship sub-endpoint.
    url = reverse('api:job_template_instance_groups_list', kwargs={'pk': job_template.pk})
    with impersonate(admin):
        post(url, {'id': instance_group.id}, user=admin, expect=status.HTTP_204_NO_CONTENT)

    job_template.refresh_from_db()
    assert job_template.modified > original_modified
    assert job_template.modified_by == admin


@pytest.mark.django_db
def test_job_template_instance_group_detach_updates_modified_by(post, job_template, instance_group_factory, alice, admin):
    instance_group = instance_group_factory('test-ig')

    with impersonate(alice):
        job_template.instance_groups.add(instance_group)
        job_template.name = 'edited-by-alice'
        job_template.save()
    job_template.refresh_from_db()
    assert job_template.modified_by == alice
    original_modified = job_template.modified

    url = reverse('api:job_template_instance_groups_list', kwargs={'pk': job_template.pk})
    with impersonate(admin):
        post(url, {'id': instance_group.id, 'disassociate': True}, user=admin, expect=status.HTTP_204_NO_CONTENT)

    job_template.refresh_from_db()
    assert job_template.modified > original_modified
    assert job_template.modified_by == admin


@pytest.mark.django_db
def test_direct_instance_group_association_updates_modified_by(job_template, instance_group_factory, alice, bob):
    instance_group = instance_group_factory('test-ig')

    with impersonate(alice):
        job_template.instance_groups.add(instance_group)
    job_template.refresh_from_db()
    assert job_template.modified_by == alice

    with impersonate(bob):
        job_template.instance_groups.remove(instance_group)
    job_template.refresh_from_db()
    assert job_template.modified_by == bob


@pytest.mark.django_db
def test_instance_group_clear_updates_modified_by(job_template, instance_group_factory, alice, bob):
    instance_group = instance_group_factory('test-ig')

    with impersonate(alice):
        job_template.instance_groups.add(instance_group)
    job_template.refresh_from_db()
    original_modified = job_template.modified

    with impersonate(bob):
        job_template.instance_groups.clear()
    job_template.refresh_from_db()
    assert job_template.modified > original_modified
    assert job_template.modified_by == bob


@pytest.mark.django_db
def test_noop_instance_group_associations_do_not_update_modified_by(job_template, instance_group_factory, alice, bob):
    instance_group = instance_group_factory('associated-ig')
    unassociated_instance_group = instance_group_factory('unassociated-ig')

    with impersonate(alice):
        job_template.instance_groups.add(instance_group)
        job_template.name = 'edited-by-alice'
        job_template.save()
    job_template.refresh_from_db()
    original_modified = job_template.modified

    with impersonate(bob):
        job_template.instance_groups.add(instance_group)
        job_template.instance_groups.remove(unassociated_instance_group)
    job_template.refresh_from_db()
    assert job_template.modified == original_modified
    assert job_template.modified_by == alice


@pytest.mark.django_db
def test_noop_instance_group_clear_does_not_update_modified_by(job_template, alice, bob):
    with impersonate(alice):
        job_template.name = 'edited-by-alice'
        job_template.save()
    job_template.refresh_from_db()
    original_modified = job_template.modified

    with impersonate(bob):
        job_template.instance_groups.clear()
    job_template.refresh_from_db()
    assert job_template.modified == original_modified
    assert job_template.modified_by == alice
