import pytest
import mock

from django.core.exceptions import ValidationError

from awx.api.versioning import reverse

from awx.main.models import InventorySource, Project, ProjectUpdate


@pytest.fixture
def scm_inventory(inventory, project):
    with mock.patch.object(project, 'update'):
        inventory.inventory_sources.create(
            name='foobar', update_on_project_update=True, source='scm',
            source_project=project, scm_last_revision=project.scm_revision)
    return inventory


@pytest.mark.django_db
def test_inventory_source_notification_on_cloud_only(get, post, inventory_source_factory, user, notification_template):
    u = user('admin', True)

    cloud_is = inventory_source_factory("ec2")
    cloud_is.source = "ec2"
    cloud_is.save()

    not_is = inventory_source_factory("not_ec2")

    url = reverse('api:inventory_source_notification_templates_any_list', kwargs={'pk': cloud_is.id})
    response = post(url, dict(id=notification_template.id), u)
    assert response.status_code == 204

    url = reverse('api:inventory_source_notification_templates_success_list', kwargs={'pk': not_is.id})
    response = post(url, dict(id=notification_template.id), u)
    assert response.status_code == 400


@pytest.mark.django_db
def test_inventory_source_unique_together_with_inv(inventory_factory):
    inv1 = inventory_factory('foo')
    inv2 = inventory_factory('bar')
    is1 = InventorySource(name='foo', source='file', inventory=inv1)
    is1.save()
    is2 = InventorySource(name='foo', source='file', inventory=inv1)
    with pytest.raises(ValidationError):
        is2.validate_unique()
    is2 = InventorySource(name='foo', source='file', inventory=inv2)
    is2.validate_unique()


@pytest.mark.parametrize("role_field,expected_status_code", [
    (None, 403),
    ('admin_role', 200),
    ('update_role', 403),
    ('adhoc_role', 403),
    ('use_role', 403)
])
@pytest.mark.django_db
def test_edit_inventory(put, inventory, alice, role_field, expected_status_code):
    data = { 'organization': inventory.organization.id, 'name': 'New name', 'description': 'Hello world', }
    if role_field:
        getattr(inventory, role_field).members.add(alice)
    put(reverse('api:inventory_detail', kwargs={'pk': inventory.id}), data, alice, expect=expected_status_code)


@pytest.mark.django_db
def test_async_inventory_deletion(delete, get, inventory, alice):
    inventory.admin_role.members.add(alice)
    resp = delete(reverse('api:inventory_detail', kwargs={'pk': inventory.id}), alice)
    assert resp.status_code == 202

    resp = get(reverse('api:inventory_detail', kwargs={'pk': inventory.id}), alice)
    assert resp.status_code == 200
    assert resp.data.get('pending_deletion') is True


@pytest.mark.django_db
def test_async_inventory_duplicate_deletion_prevention(delete, get, inventory, alice):
    inventory.admin_role.members.add(alice)
    resp = delete(reverse('api:inventory_detail', kwargs={'pk': inventory.id}), alice)
    assert resp.status_code == 202

    resp = delete(reverse('api:inventory_detail', kwargs={'pk': inventory.id}), alice)
    assert resp.status_code == 400
    assert resp.data['error'] == 'Inventory is already pending deletion.'


@pytest.mark.parametrize('order_by', ('script', '-script', 'script,pk', '-script,pk'))
@pytest.mark.django_db
def test_list_cannot_order_by_unsearchable_field(get, organization, alice, order_by):
    for i, script in enumerate(('#!/bin/a', '#!/bin/b', '#!/bin/c')):
        custom_script = organization.custom_inventory_scripts.create(
            name="I%d" % i,
            script=script
        )
        custom_script.admin_role.members.add(alice)

    response = get(reverse('api:inventory_script_list'), alice,
                   QUERY_STRING='order_by=%s' % order_by, status=400)
    assert response.status_code == 400


@pytest.mark.parametrize("role_field,expected_status_code", [
    (None, 403),
    ('admin_role', 201),
    ('update_role', 403),
    ('adhoc_role', 403),
    ('use_role', 403)
])
@pytest.mark.django_db
def test_create_inventory_group(post, inventory, alice, role_field, expected_status_code):
    data = { 'name': 'New name', 'description': 'Hello world', }
    if role_field:
        getattr(inventory, role_field).members.add(alice)
    post(reverse('api:inventory_groups_list', kwargs={'pk': inventory.id}), data, alice, expect=expected_status_code)


@pytest.mark.parametrize("role_field,expected_status_code", [
    (None, 403),
    ('admin_role', 201),
    ('update_role', 403),
    ('adhoc_role', 403),
    ('use_role', 403)
])
@pytest.mark.django_db
def test_create_inventory_group_child(post, group, alice, role_field, expected_status_code):
    data = { 'name': 'New name', 'description': 'Hello world', }
    if role_field:
        getattr(group.inventory, role_field).members.add(alice)
    post(reverse('api:group_children_list', kwargs={'pk': group.id}), data, alice, expect=expected_status_code)


@pytest.mark.parametrize("role_field,expected_status_code", [
    (None, 403),
    ('admin_role', 200),
    ('update_role', 403),
    ('adhoc_role', 403),
    ('use_role', 403)
])
@pytest.mark.django_db
def test_edit_inventory_group(put, group, alice, role_field, expected_status_code):
    data = { 'name': 'New name', 'description': 'Hello world', }
    if role_field:
        getattr(group.inventory, role_field).members.add(alice)
    put(reverse('api:group_detail', kwargs={'pk': group.id}), data, alice, expect=expected_status_code)


@pytest.mark.parametrize("role_field,expected_status_code", [
    (None, 403),
    ('admin_role', 201),
    ('update_role', 403),
    ('adhoc_role', 403),
    ('use_role', 403)
])
@pytest.mark.django_db
def test_create_inventory_inventory_source(post, inventory, alice, role_field, expected_status_code):
    data = { 'source': 'ec2', 'name': 'ec2-inv-source'}
    if role_field:
        getattr(inventory, role_field).members.add(alice)
    post(reverse('api:inventory_inventory_sources_list', kwargs={'pk': inventory.id}), data, alice, expect=expected_status_code)


@pytest.mark.parametrize("role_field,expected_status_code", [
    (None, 403),
    ('admin_role', 204),
    ('update_role', 403),
    ('adhoc_role', 403),
    ('use_role', 403)
])
@pytest.mark.django_db
def test_delete_inventory_group(delete, group, alice, role_field, expected_status_code):
    if role_field:
        getattr(group.inventory, role_field).members.add(alice)
    delete(reverse('api:group_detail', kwargs={'pk': group.id}), alice, expect=expected_status_code)


@pytest.mark.parametrize("role_field,expected_status_code", [
    (None, 403),
    ('admin_role', 201),
    ('update_role', 403),
    ('adhoc_role', 403),
    ('use_role', 403)
])
@pytest.mark.django_db
def test_create_inventory_host(post, inventory, alice, role_field, expected_status_code):
    data = { 'name': 'New name', 'description': 'Hello world', }
    if role_field:
        getattr(inventory, role_field).members.add(alice)
    post(reverse('api:inventory_hosts_list', kwargs={'pk': inventory.id}), data, alice, expect=expected_status_code)


@pytest.mark.parametrize("role_field,expected_status_code", [
    (None, 403),
    ('admin_role', 201),
    ('update_role', 403),
    ('adhoc_role', 403),
    ('use_role', 403)
])
@pytest.mark.django_db
def test_create_inventory_group_host(post, group, alice, role_field, expected_status_code):
    data = { 'name': 'New name', 'description': 'Hello world', }
    if role_field:
        getattr(group.inventory, role_field).members.add(alice)
    post(reverse('api:group_hosts_list', kwargs={'pk': group.id}), data, alice, expect=expected_status_code)


@pytest.mark.parametrize("role_field,expected_status_code", [
    (None, 403),
    ('admin_role', 200),
    ('update_role', 403),
    ('adhoc_role', 403),
    ('use_role', 403)
])
@pytest.mark.django_db
def test_edit_inventory_host(put, host, alice, role_field, expected_status_code):
    data = { 'name': 'New name', 'description': 'Hello world', }
    if role_field:
        getattr(host.inventory, role_field).members.add(alice)
    put(reverse('api:host_detail', kwargs={'pk': host.id}), data, alice, expect=expected_status_code)


@pytest.mark.parametrize("role_field,expected_status_code", [
    (None, 403),
    ('admin_role', 204),
    ('update_role', 403),
    ('adhoc_role', 403),
    ('use_role', 403)
])
@pytest.mark.django_db
def test_delete_inventory_host(delete, host, alice, role_field, expected_status_code):
    if role_field:
        getattr(host.inventory, role_field).members.add(alice)
    delete(reverse('api:host_detail', kwargs={'pk': host.id}), alice, expect=expected_status_code)


# See companion test in tests/functional/test_rbac_inventory.py::test_inventory_source_update
@pytest.mark.parametrize("start_access,expected_status_code", [
    (True, 202),
    (False, 403)
])
@pytest.mark.django_db
def test_inventory_update_access_called(post, inventory_source, alice, mock_access, start_access, expected_status_code):
    with mock_access(InventorySource) as mock_instance:
        mock_instance.can_start = mock.MagicMock(return_value=start_access)
        post(reverse('api:inventory_source_update_view', kwargs={'pk': inventory_source.id}),
             {}, alice, expect=expected_status_code)
        mock_instance.can_start.assert_called_once_with(inventory_source)


@pytest.mark.django_db
class TestUpdateOnProjUpdate:

    def test_no_access_update_denied(self, admin_user, scm_inventory, mock_access, post):
        inv_src = scm_inventory.inventory_sources.first()
        with mock_access(Project) as mock_access:
            mock_access.can_start = mock.MagicMock(return_value=False)
            r = post(reverse('api:inventory_source_update_view', kwargs={'pk': inv_src.id}),
                     {}, admin_user, expect=403)
        assert 'You do not have permission to update project' in r.data['detail']

    def test_no_access_update_allowed(self, admin_user, scm_inventory, mock_access, post):
        inv_src = scm_inventory.inventory_sources.first()
        inv_src.source_project.scm_type = 'git'
        inv_src.source_project.save()
        with mock.patch('awx.api.views.InventorySourceUpdateView.get_object') as get_object:
            get_object.return_value = inv_src
            with mock.patch.object(inv_src.source_project, 'update') as mock_update:
                mock_update.return_value = ProjectUpdate(pk=48, id=48)
                r = post(reverse('api:inventory_source_update_view', kwargs={'pk': inv_src.id}),
                         {}, admin_user, expect=202)
        assert 'dependent project' in r.data['detail']
        assert not r.data['inventory_update']


@pytest.mark.django_db
def test_inventory_source_vars_prohibition(post, inventory, admin_user):
    with mock.patch('awx.api.serializers.settings') as mock_settings:
        mock_settings.INV_ENV_VARIABLE_BLACKLIST = ('FOOBAR',)
        r = post(reverse('api:inventory_source_list'),
                 {'name': 'new inv src', 'source_vars': '{\"FOOBAR\": \"val\"}', 'inventory': inventory.pk},
                 admin_user, expect=400)
    assert 'prohibited environment variable' in r.data['source_vars'][0]
    assert 'FOOBAR' in r.data['source_vars'][0]


@pytest.mark.django_db
class TestControlledBySCM:
    '''
    Check that various actions are correctly blocked if object is controlled
    by an SCM follow-project inventory source
    '''
    def test_safe_method_works(self, get, options, scm_inventory, admin_user):
        get(scm_inventory.get_absolute_url(), admin_user, expect=200)
        options(scm_inventory.get_absolute_url(), admin_user, expect=200)
        assert InventorySource.objects.get(inventory=scm_inventory.pk).scm_last_revision != ''

    def test_vars_edit_reset(self, patch, scm_inventory, admin_user):
        patch(scm_inventory.get_absolute_url(), {'variables': 'hello: world'},
              admin_user, expect=200)
        assert InventorySource.objects.get(inventory=scm_inventory.pk).scm_last_revision == ''

    def test_name_edit_allowed(self, patch, scm_inventory, admin_user):
        patch(scm_inventory.get_absolute_url(), {'variables': '---', 'name': 'newname'},
              admin_user, expect=200)
        assert InventorySource.objects.get(inventory=scm_inventory.pk).scm_last_revision != ''

    def test_host_associations_reset(self, post, scm_inventory, admin_user):
        inv_src = scm_inventory.inventory_sources.first()
        h = inv_src.hosts.create(name='barfoo', inventory=scm_inventory)
        g = inv_src.groups.create(name='fooland', inventory=scm_inventory)
        post(reverse('api:host_groups_list', kwargs={'pk': h.id}), {'id': g.id},
             admin_user, expect=204)
        post(reverse('api:group_hosts_list', kwargs={'pk': g.id}), {'id': h.id},
             admin_user, expect=204)
        assert InventorySource.objects.get(inventory=scm_inventory.pk).scm_last_revision == ''

    def test_group_group_associations_reset(self, post, scm_inventory, admin_user):
        inv_src = scm_inventory.inventory_sources.first()
        g1 = inv_src.groups.create(name='barland', inventory=scm_inventory)
        g2 = inv_src.groups.create(name='fooland', inventory=scm_inventory)
        post(reverse('api:group_children_list', kwargs={'pk': g1.id}), {'id': g2.id},
             admin_user, expect=204)
        assert InventorySource.objects.get(inventory=scm_inventory.pk).scm_last_revision == ''

    def test_host_group_delete_reset(self, delete, scm_inventory, admin_user):
        inv_src = scm_inventory.inventory_sources.first()
        h = inv_src.hosts.create(name='barfoo', inventory=scm_inventory)
        g = inv_src.groups.create(name='fooland', inventory=scm_inventory)
        delete(h.get_absolute_url(), admin_user, expect=204)
        delete(g.get_absolute_url(), admin_user, expect=204)
        assert InventorySource.objects.get(inventory=scm_inventory.pk).scm_last_revision == ''

    def test_remove_scm_inv_src(self, delete, scm_inventory, admin_user):
        inv_src = scm_inventory.inventory_sources.first()
        delete(inv_src.get_absolute_url(), admin_user, expect=204)
        assert scm_inventory.inventory_sources.count() == 0

    def test_adding_inv_src_prohibited(self, post, scm_inventory, admin_user):
        post(reverse('api:inventory_inventory_sources_list', kwargs={'pk': scm_inventory.id}),
             {'name': 'new inv src'}, admin_user, expect=403)

    def test_adding_inv_src_without_proj_access_prohibited(self, post, project, inventory, rando):
        inventory.admin_role.members.add(rando)
        post(reverse('api:inventory_inventory_sources_list', kwargs={'pk': inventory.id}),
             {'name': 'new inv src', 'source_project': project.pk}, rando, expect=403)

    def test_no_post_in_options(self, options, scm_inventory, admin_user):
        r = options(reverse('api:inventory_inventory_sources_list', kwargs={'pk': scm_inventory.id}),
                    admin_user, expect=200)
        assert 'POST' not in r.data['actions']


@pytest.mark.django_db
class TestInsightsCredential:
    def test_insights_credential(self, patch, insights_inventory, admin_user, insights_credential):
        patch(insights_inventory.get_absolute_url(),
              {'insights_credential': insights_credential.id}, admin_user,
              expect=200)

    def test_non_insights_credential(self, patch, insights_inventory, admin_user, scm_credential):
        patch(insights_inventory.get_absolute_url(),
              {'insights_credential': scm_credential.id}, admin_user,
              expect=400)
