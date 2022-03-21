import random

import pytest

from awx.api.versioning import reverse
from awx.main.models import (
    ActivityStream,
    Instance,
    InstanceGroup,
    ProjectUpdate,
)
from awx.main.utils import camelcase_to_underscore


@pytest.fixture
def tower_instance_group():
    ig = InstanceGroup(name='default')
    ig.save()
    return ig


@pytest.fixture
def instance():
    return Instance.objects.create(hostname='instance')


@pytest.fixture
def node_type_instance():
    def fn(hostname, node_type):
        return Instance.objects.create(hostname=hostname, node_type=node_type)

    return fn


@pytest.fixture
def instance_group(job_factory):
    ig = InstanceGroup(name="east")
    ig.save()
    return ig


@pytest.fixture
def containerized_instance_group(instance_group, kube_credential):
    ig = InstanceGroup(name="container")
    ig.credential = kube_credential
    ig.is_container_group = True
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


@pytest.fixture(scope='function')
def source_model(request):
    return request.getfixturevalue(request.param)


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
def test_delete_rename_tower_instance_group_prevented(
    delete, options, tower_instance_group, instance_group, user, patch, control_plane_execution_environment, default_job_execution_environment
):
    url = reverse("api:instance_group_detail", kwargs={'pk': tower_instance_group.pk})
    super_user = user('bob', True)

    delete(url, None, super_user, expect=403)

    resp = options(url, None, super_user, expect=200)
    assert len(resp.data['actions'].keys()) == 2
    assert 'DELETE' not in resp.data['actions']
    assert 'GET' in resp.data['actions']
    assert 'PUT' in resp.data['actions']

    # Rename 'default' instance group denied
    patch(url, {'name': 'default_prime'}, super_user, expect=400)

    # Rename, other instance group OK
    url = reverse("api:instance_group_detail", kwargs={'pk': instance_group.pk})
    patch(url, {'name': 'foobar'}, super_user, expect=200)


@pytest.mark.django_db
@pytest.mark.parametrize('source_model', ['job_template', 'inventory', 'organization'], indirect=True)
def test_instance_group_order_persistence(get, post, admin, source_model):
    # create several instance groups in random order
    total = 5
    pks = list(range(total))
    random.shuffle(pks)
    instances = [InstanceGroup.objects.create(name='group-%d' % i) for i in pks]
    view_name = camelcase_to_underscore(source_model.__class__.__name__)
    url = reverse('api:{}_instance_groups_list'.format(view_name), kwargs={'pk': source_model.pk})

    # associate them all
    for instance in instances:
        post(url, {'associate': True, 'id': instance.id}, admin, expect=204)

    for _ in range(10):
        # remove them all
        for instance in instances:
            post(url, {'disassociate': True, 'id': instance.id}, admin, expect=204)
        resp = get(url, admin)
        assert resp.data['count'] == 0

        # add them all in random order
        before = sorted(instances, key=lambda x: random.random())
        for instance in before:
            post(url, {'associate': True, 'id': instance.id}, admin, expect=204)
        resp = get(url, admin)
        assert resp.data['count'] == total
        assert [ig['name'] for ig in resp.data['results']] == [ig.name for ig in before]


@pytest.mark.django_db
def test_instance_group_update_fields(patch, instance, instance_group, admin, containerized_instance_group):
    # policy_instance_ variables can only be updated in instance groups that are NOT containerized
    # instance group (not containerized)
    ig_url = reverse("api:instance_group_detail", kwargs={'pk': instance_group.pk})
    assert not instance_group.is_container_group
    resp = patch(ig_url, {'policy_instance_percentage': 15}, admin, expect=200)
    assert 15 == resp.data['policy_instance_percentage']
    resp = patch(ig_url, {'policy_instance_minimum': 15}, admin, expect=200)
    assert 15 == resp.data['policy_instance_minimum']
    resp = patch(ig_url, {'policy_instance_list': [instance.hostname]}, admin)
    assert [instance.hostname] == resp.data['policy_instance_list']

    # containerized instance group
    cg_url = reverse("api:instance_group_detail", kwargs={'pk': containerized_instance_group.pk})
    assert containerized_instance_group.is_container_group
    resp = patch(cg_url, {'policy_instance_percentage': 15}, admin, expect=400)
    assert ["Containerized instances may not be managed via the API"] == resp.data['policy_instance_percentage']
    resp = patch(cg_url, {'policy_instance_minimum': 15}, admin, expect=400)
    assert ["Containerized instances may not be managed via the API"] == resp.data['policy_instance_minimum']
    resp = patch(cg_url, {'policy_instance_list': [instance.hostname]}, admin)
    assert ["Containerized instances may not be managed via the API"] == resp.data['policy_instance_list']


@pytest.mark.django_db
def test_containerized_group_default_fields(instance_group, kube_credential):
    ig = InstanceGroup(name="test_policy_field_defaults")
    ig.policy_instance_list = [1]
    ig.policy_instance_minimum = 5
    ig.policy_instance_percentage = 5
    ig.save()
    assert ig.policy_instance_list == [1]
    assert ig.policy_instance_minimum == 5
    assert ig.policy_instance_percentage == 5
    ig.credential = kube_credential
    ig.is_container_group = True
    ig.save()
    assert ig.policy_instance_list == []
    assert ig.policy_instance_minimum == 0
    assert ig.policy_instance_percentage == 0


@pytest.mark.django_db
@pytest.mark.parametrize('node_type', ['control', 'hybrid', 'execution'])
def test_instance_attach_to_instance_group(post, instance_group, node_type_instance, admin, node_type):
    instance = node_type_instance(hostname=node_type, node_type=node_type)

    count = ActivityStream.objects.count()

    url = reverse(f'api:instance_group_instance_list', kwargs={'pk': instance_group.pk})
    post(url, {'associate': True, 'id': instance.id}, admin, expect=204 if node_type != 'control' else 400)

    new_activity = ActivityStream.objects.all()[count:]
    if node_type != 'control':
        assert len(new_activity) == 2  # the second is an update of the instance group policy
        new_activity = new_activity[0]
        assert new_activity.operation == 'associate'
        assert new_activity.object1 == 'instance_group'
        assert new_activity.object2 == 'instance'
        assert new_activity.instance.first() == instance
        assert new_activity.instance_group.first() == instance_group
    else:
        assert not new_activity


@pytest.mark.django_db
@pytest.mark.parametrize('node_type', ['control', 'hybrid', 'execution'])
def test_instance_unattach_from_instance_group(post, instance_group, node_type_instance, admin, node_type):
    instance = node_type_instance(hostname=node_type, node_type=node_type)
    instance_group.instances.add(instance)

    count = ActivityStream.objects.count()

    url = reverse(f'api:instance_group_instance_list', kwargs={'pk': instance_group.pk})
    post(url, {'disassociate': True, 'id': instance.id}, admin, expect=204 if node_type != 'control' else 400)

    new_activity = ActivityStream.objects.all()[count:]
    if node_type != 'control':
        assert len(new_activity) == 1
        new_activity = new_activity[0]
        assert new_activity.operation == 'disassociate'
        assert new_activity.object1 == 'instance_group'
        assert new_activity.object2 == 'instance'
        assert new_activity.instance.first() == instance
        assert new_activity.instance_group.first() == instance_group
    else:
        assert not new_activity


@pytest.mark.django_db
@pytest.mark.parametrize('node_type', ['control', 'hybrid', 'execution'])
def test_instance_group_attach_to_instance(post, instance_group, node_type_instance, admin, node_type):
    instance = node_type_instance(hostname=node_type, node_type=node_type)

    count = ActivityStream.objects.count()

    url = reverse(f'api:instance_instance_groups_list', kwargs={'pk': instance.pk})
    post(url, {'associate': True, 'id': instance_group.id}, admin, expect=204 if node_type != 'control' else 400)

    new_activity = ActivityStream.objects.all()[count:]
    if node_type != 'control':
        assert len(new_activity) == 2  # the second is an update of the instance group policy
        new_activity = new_activity[0]
        assert new_activity.operation == 'associate'
        assert new_activity.object1 == 'instance'
        assert new_activity.object2 == 'instance_group'
        assert new_activity.instance.first() == instance
        assert new_activity.instance_group.first() == instance_group
    else:
        assert not new_activity


@pytest.mark.django_db
@pytest.mark.parametrize('node_type', ['control', 'hybrid', 'execution'])
def test_instance_group_unattach_from_instance(post, instance_group, node_type_instance, admin, node_type):
    instance = node_type_instance(hostname=node_type, node_type=node_type)
    instance_group.instances.add(instance)

    count = ActivityStream.objects.count()

    url = reverse(f'api:instance_instance_groups_list', kwargs={'pk': instance.pk})
    post(url, {'disassociate': True, 'id': instance_group.id}, admin, expect=204 if node_type != 'control' else 400)

    new_activity = ActivityStream.objects.all()[count:]
    if node_type != 'control':
        assert len(new_activity) == 1
        new_activity = new_activity[0]
        assert new_activity.operation == 'disassociate'
        assert new_activity.object1 == 'instance'
        assert new_activity.object2 == 'instance_group'
        assert new_activity.instance.first() == instance
        assert new_activity.instance_group.first() == instance_group
    else:
        assert not new_activity


@pytest.mark.django_db
def test_cannot_remove_controlplane_hybrid_instances(post, controlplane_instance_group, node_type_instance, admin_user):
    instance = node_type_instance(hostname='hybrid_node', node_type='hybrid')
    controlplane_instance_group.instances.add(instance)

    url = reverse('api:instance_group_instance_list', kwargs={'pk': controlplane_instance_group.pk})
    r = post(url, {'disassociate': True, 'id': instance.id}, admin_user, expect=400)
    assert 'Cannot disassociate hybrid node' in str(r.data)

    url = reverse('api:instance_instance_groups_list', kwargs={'pk': instance.pk})
    r = post(url, {'disassociate': True, 'id': controlplane_instance_group.id}, admin_user, expect=400)
    assert f'Cannot disassociate hybrid instance' in str(r.data)
