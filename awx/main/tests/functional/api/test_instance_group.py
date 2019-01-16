import pytest

from awx.api.versioning import reverse
from awx.main.models import (
    Instance,
    InstanceGroup,
    ProjectUpdate,
)


@pytest.fixture
def tower_instance_group():
    ig = InstanceGroup(name='tower')
    ig.save()
    return ig


@pytest.fixture
def instance():
    instance = Instance.objects.create(hostname='iso')
    return instance


@pytest.fixture
def non_iso_instance():
    return Instance.objects.create(hostname='iamnotanisolatedinstance')


@pytest.fixture
def instance_group(job_factory):
    ig = InstanceGroup(name="east")
    ig.save()
    return ig


@pytest.fixture
def isolated_instance_group(instance_group, instance):
    ig = InstanceGroup(name="iso", controller=instance_group)
    ig.save()
    ig.instances.set([instance])
    ig.save()
    return ig


@pytest.fixture
def create_job_factory(job_factory, instance_group):
    def fn(status='running'):
        j = job_factory()
        j.status = status
        j.instance_group = instance_group
        j.save()
        return j
    return fn


@pytest.fixture
def create_project_update_factory(instance_group, project):
    def fn(status='running'):
        pu = ProjectUpdate(project=project)
        pu.status = status
        pu.instance_group = instance_group
        pu.save()
        return pu
    return fn


@pytest.fixture
def instance_group_jobs_running(instance_group, create_job_factory, create_project_update_factory):
    jobs_running = [create_job_factory(status='running') for i in range(0, 2)]
    project_updates_running = [create_project_update_factory(status='running') for i in range(0, 2)]
    return jobs_running + project_updates_running


@pytest.fixture
def instance_group_jobs_successful(instance_group, create_job_factory, create_project_update_factory):
    jobs_successful = [create_job_factory(status='successful') for i in range(0, 2)]
    project_updates_successful = [create_project_update_factory(status='successful') for i in range(0, 2)]
    return jobs_successful + project_updates_successful


@pytest.mark.django_db
def test_delete_instance_group_jobs(delete, instance_group_jobs_successful, instance_group, admin):
    url = reverse("api:instance_group_detail", kwargs={'pk': instance_group.pk})
    delete(url, None, admin, expect=204)


@pytest.mark.django_db
def test_delete_instance_group_jobs_running(delete, instance_group_jobs_running, instance_group_jobs_successful, instance_group, admin):
    def sort_keys(x):
        return (x['type'], str(x['id']))

    url = reverse("api:instance_group_detail", kwargs={'pk': instance_group.pk})
    response = delete(url, None, admin, expect=409)

    expect_transformed = [dict(id=j.id, type=j.model_to_str()) for j in instance_group_jobs_running]
    response_sorted = sorted(response.data['active_jobs'], key=sort_keys)
    expect_sorted = sorted(expect_transformed, key=sort_keys)

    assert response.data['error'] == u"Resource is being used by running jobs."
    assert response_sorted == expect_sorted


@pytest.mark.django_db
def test_delete_rename_tower_instance_group_prevented(delete, options, tower_instance_group, instance_group, user, patch):
    url = reverse("api:instance_group_detail", kwargs={'pk': tower_instance_group.pk})
    super_user = user('bob', True)

    delete(url, None, super_user, expect=403)

    resp = options(url, None, super_user, expect=200)
    assert len(resp.data['actions'].keys()) == 2
    assert 'DELETE' not in resp.data['actions']
    assert 'GET' in resp.data['actions']
    assert 'PUT' in resp.data['actions']

    # Rename 'tower' instance group denied
    patch(url, {'name': 'tower_prime'}, super_user, expect=400)

    # Rename, other instance group OK
    url = reverse("api:instance_group_detail", kwargs={'pk': instance_group.pk})
    patch(url, {'name': 'foobar'}, super_user, expect=200)


@pytest.mark.django_db
def test_prevent_delete_iso_and_control_groups(delete, isolated_instance_group, admin):
    iso_url = reverse("api:instance_group_detail", kwargs={'pk': isolated_instance_group.pk})
    controller_url = reverse("api:instance_group_detail", kwargs={'pk': isolated_instance_group.controller.pk})
    delete(iso_url, None, admin, expect=403)
    delete(controller_url, None, admin, expect=403)


@pytest.mark.django_db
def test_prevent_isolated_instance_added_to_non_isolated_instance_group(post, admin, instance, instance_group, isolated_instance_group):
    url = reverse("api:instance_group_instance_list", kwargs={'pk': instance_group.pk})

    assert True is instance.is_isolated()
    resp = post(url, {'associate': True, 'id': instance.id}, admin, expect=400)
    assert u"Isolated instances may not be added or removed from instances groups via the API." == resp.data['error']


@pytest.mark.django_db
def test_prevent_isolated_instance_added_to_non_isolated_instance_group_via_policy_list(patch, admin, instance, instance_group, isolated_instance_group):
    url = reverse("api:instance_group_detail", kwargs={'pk': instance_group.pk})

    assert True is instance.is_isolated()
    resp = patch(url, {'policy_instance_list': [instance.hostname]}, user=admin, expect=400)
    assert [u"Isolated instances may not be added or removed from instances groups via the API."] == resp.data['policy_instance_list']
    assert instance_group.policy_instance_list == []


@pytest.mark.django_db
def test_prevent_isolated_instance_removal_from_isolated_instance_group(post, admin, instance, instance_group, isolated_instance_group):
    url = reverse("api:instance_group_instance_list", kwargs={'pk': isolated_instance_group.pk})

    assert True is instance.is_isolated()
    resp = post(url, {'disassociate': True, 'id': instance.id}, admin, expect=400)
    assert u"Isolated instances may not be added or removed from instances groups via the API." == resp.data['error']


@pytest.mark.django_db
def test_prevent_non_isolated_instance_added_to_isolated_instance_group(
        post, admin, non_iso_instance, isolated_instance_group):
    url = reverse("api:instance_group_instance_list", kwargs={'pk': isolated_instance_group.pk})

    assert False is non_iso_instance.is_isolated()
    resp = post(url, {'associate': True, 'id': non_iso_instance.id}, admin, expect=400)
    assert u"Isolated instance group membership may not be managed via the API." == resp.data['error']


@pytest.mark.django_db
def test_prevent_non_isolated_instance_added_to_isolated_instance_group_via_policy_list(
        patch, admin, non_iso_instance, isolated_instance_group):
    url = reverse("api:instance_group_detail", kwargs={'pk': isolated_instance_group.pk})

    assert False is non_iso_instance.is_isolated()
    resp = patch(url, {'policy_instance_list': [non_iso_instance.hostname]}, user=admin, expect=400)
    assert [u"Isolated instance group membership may not be managed via the API."] == resp.data['policy_instance_list']
    assert isolated_instance_group.policy_instance_list == []
