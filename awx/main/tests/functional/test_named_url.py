# -*- coding: utf-8 -*-
import pytest

from awx.api.versioning import reverse
from awx.main.middleware import URLModificationMiddleware
from awx.main.models import (  # noqa
    Credential,
    Group,
    Host,
    Instance,
    InstanceGroup,
    Inventory,
    InventorySource,
    JobTemplate,
    NotificationTemplate,
    Organization,
    Project,
    User,
    WorkflowJobTemplate,
)


@pytest.mark.django_db
def test_user(get, admin_user):
    test_user = User.objects.create(username='test_user', password='test_user', is_superuser=False)
    url = reverse('api:user_detail', kwargs={'pk': test_user.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_user/')


@pytest.mark.django_db
def test_team(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    test_team = test_org.teams.create(name='test_team')
    url = reverse('api:team_detail', kwargs={'pk': test_team.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_team++test_org/')


@pytest.mark.django_db
def test_organization(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    url = reverse('api:organization_detail', kwargs={'pk': test_org.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_org/')


@pytest.mark.django_db
def test_job_template(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    test_jt = JobTemplate.objects.create(name='test_jt', organization=test_org)
    url = reverse('api:job_template_detail', kwargs={'pk': test_jt.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_jt++test_org/')


@pytest.mark.django_db
def test_job_template_old_way(get, admin_user, mocker):
    test_org = Organization.objects.create(name='test_org')
    test_jt = JobTemplate.objects.create(name='test_jt ♥', organization=test_org)
    url = reverse('api:job_template_detail', kwargs={'pk': test_jt.pk})

    response = get(url, user=admin_user, expect=200)
    new_url = response.data['related']['named_url']
    old_url = '/'.join([url.rsplit('/', 2)[0], test_jt.name, ''])

    assert URLModificationMiddleware._convert_named_url(new_url) == url
    assert URLModificationMiddleware._convert_named_url(old_url) == url


@pytest.mark.django_db
def test_workflow_job_template(get, admin_user):
    test_wfjt = WorkflowJobTemplate.objects.create(name='test_wfjt')
    url = reverse('api:workflow_job_template_detail', kwargs={'pk': test_wfjt.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_wfjt++/')
    test_org = Organization.objects.create(name='test_org')
    test_wfjt.organization = test_org
    test_wfjt.save()
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_wfjt++test_org/')


@pytest.mark.django_db
def test_label(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    test_label = test_org.labels.create(name='test_label')
    url = reverse('api:label_detail', kwargs={'pk': test_label.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_label++test_org/')


@pytest.mark.django_db
def test_project(get, admin_user):
    test_proj = Project.objects.create(name='test_proj')
    url = reverse('api:project_detail', kwargs={'pk': test_proj.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_proj++/')
    test_org = Organization.objects.create(name='test_org')
    test_proj.organization = test_org
    test_proj.save()
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_proj++test_org/')


@pytest.mark.django_db
def test_notification_template(get, admin_user):
    test_notification_template = NotificationTemplate.objects.create(
        name='test_note', notification_type='slack', notification_configuration=dict(channels=["Foo", "Bar"], token="token")
    )
    url = reverse('api:notification_template_detail', kwargs={'pk': test_notification_template.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_note++/')
    test_org = Organization.objects.create(name='test_org')
    test_notification_template.organization = test_org
    test_notification_template.save()
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_note++test_org/')


@pytest.mark.django_db
def test_instance(get, admin_user, settings):
    test_instance = Instance.objects.create(uuid=settings.SYSTEM_UUID, hostname="localhost", capacity=100)
    url = reverse('api:instance_detail', kwargs={'pk': test_instance.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/localhost/')


@pytest.mark.django_db
def test_instance_group(get, admin_user):
    test_instance_group = InstanceGroup.objects.create(name='Tower')
    url = reverse('api:instance_group_detail', kwargs={'pk': test_instance_group.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/Tower/')


@pytest.mark.django_db
def test_inventory(get, admin_user):
    test_inv = Inventory.objects.create(name='test_inv')
    url = reverse('api:inventory_detail', kwargs={'pk': test_inv.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_inv++/')
    test_org = Organization.objects.create(name='test_org')
    test_inv.organization = test_org
    test_inv.save()
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_inv++test_org/')


@pytest.mark.django_db
def test_host(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    test_inv = Inventory.objects.create(name='test_inv', organization=test_org)
    test_host = Host.objects.create(name='test_host', inventory=test_inv)
    url = reverse('api:host_detail', kwargs={'pk': test_host.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_host++test_inv++test_org/')


@pytest.mark.django_db
def test_group(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    test_inv = Inventory.objects.create(name='test_inv', organization=test_org)
    test_group = Group.objects.create(name='test_group', inventory=test_inv)
    url = reverse('api:group_detail', kwargs={'pk': test_group.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_group++test_inv++test_org/')


@pytest.mark.django_db
def test_inventory_source(get, admin_user):
    test_org = Organization.objects.create(name='test_org')
    test_inv = Inventory.objects.create(name='test_inv', organization=test_org)
    test_source = InventorySource.objects.create(name='test_source', inventory=test_inv, source='ec2')
    url = reverse('api:inventory_source_detail', kwargs={'pk': test_source.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_source++test_inv++test_org/')
    test_source.inventory = None
    test_source.save()
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_source++/')


@pytest.mark.django_db
def test_credential(get, admin_user, credentialtype_ssh):
    test_cred = Credential.objects.create(name='test_cred', credential_type=credentialtype_ssh)
    url = reverse('api:credential_detail', kwargs={'pk': test_cred.pk})
    response = get(url, user=admin_user, expect=200)
    assert response.data['related']['named_url'].endswith('/test_cred++Machine+ssh++/')


@pytest.mark.django_db
def test_403_vs_404(get):
    cindy = User.objects.create(username='cindy', password='test_user', is_superuser=False)
    bob = User.objects.create(username='bob', password='test_user', is_superuser=False)

    # bob cannot see cindy, pk lookup should be a 403
    url = reverse('api:user_detail', kwargs={'pk': cindy.pk})
    get(url, user=bob, expect=403)

    # bob cannot see cindy, username lookup should be a 404
    get('/api/v2/users/cindy/', user=bob, expect=404)

    get(f'/api/v2/users/{cindy.pk}/', expect=401)
    get('/api/v2/users/cindy/', expect=404)


@pytest.mark.django_db
class TestOldStyleJTNamedUrlPermissions:
    """Test the deprecated old-style named URL for job templates (name only, no org).

    The middleware has a special _hijack_for_old_jt_name path that resolves
    /api/v2/job_templates/<name>/ without requiring the ++org_name suffix.
    This does an unscoped DB query (ignoring user permissions) to find the JT.
    """

    def test_old_style_url_no_access(self, get):
        """User with no access to any JT should not resolve an old-style named URL."""
        org = Organization.objects.create(name='test_org')
        JobTemplate.objects.create(name='secret_jt', organization=org)
        rando = User.objects.create(username='rando', password='rando')

        old_url = '/api/v2/job_templates/secret_jt/'
        resolved = URLModificationMiddleware._convert_named_url(old_url, user=rando)
        # With user-scoped filtering, the JT is not visible so the name
        # is returned as-is (no rewrite), which results in a 404.
        assert resolved == old_url

    def test_old_style_url_resolves_to_accessible_jt(self, get):
        """When two JTs share a name, old-style URL resolves to the one
        the user can actually access, not an arbitrary pick by org age.
        """
        org_old = Organization.objects.create(name='org_old')
        org_new = Organization.objects.create(name='org_new')
        JobTemplate.objects.create(name='shared_jt', organization=org_old)
        jt_new = JobTemplate.objects.create(name='shared_jt', organization=org_new)

        rando = User.objects.create(username='rando', password='rando')

        # Give rando read access to org_new's JT only
        jt_new.read_role.members.add(rando)

        # The old-style URL should resolve to jt_new (the one rando can see)
        old_url = '/api/v2/job_templates/shared_jt/'
        resolved = URLModificationMiddleware._convert_named_url(old_url, user=rando)
        assert resolved == f'/api/v2/job_templates/{jt_new.pk}/'

        response = get(resolved, user=rando, expect=200)
        assert response.data['id'] == jt_new.pk
        assert response.data['organization'] == org_new.pk

    def test_old_style_url_each_user_sees_own_jt(self, get):
        """Each user resolves the old-style URL to a JT they have access to."""
        org_a = Organization.objects.create(name='alpha_org')
        org_b = Organization.objects.create(name='beta_org')

        jt_a = JobTemplate.objects.create(name='patching', organization=org_a)
        jt_b = JobTemplate.objects.create(name='patching', organization=org_b)

        user_a = User.objects.create(username='user_a', password='user_a')
        user_b = User.objects.create(username='user_b', password='user_b')

        jt_a.read_role.members.add(user_a)
        jt_b.read_role.members.add(user_b)

        old_url = '/api/v2/job_templates/patching/'

        resolved_a = URLModificationMiddleware._convert_named_url(old_url, user=user_a)
        assert resolved_a == f'/api/v2/job_templates/{jt_a.pk}/'
        response_a = get(resolved_a, user=user_a, expect=200)
        assert response_a.data['organization'] == org_a.pk

        resolved_b = URLModificationMiddleware._convert_named_url(old_url, user=user_b)
        assert resolved_b == f'/api/v2/job_templates/{jt_b.pk}/'
        response_b = get(resolved_b, user=user_b, expect=200)
        assert response_b.data['organization'] == org_b.pk

    def test_old_style_url_without_user_falls_back_to_unscoped(self):
        """Without a user (e.g. direct classmethod call), old behavior is preserved."""
        org = Organization.objects.create(name='test_org')
        jt = JobTemplate.objects.create(name='test_jt', organization=org)

        old_url = '/api/v2/job_templates/test_jt/'
        resolved = URLModificationMiddleware._convert_named_url(old_url)
        assert resolved == f'/api/v2/job_templates/{jt.pk}/'

    def test_org_admin_sees_jt_via_old_style_url(self, get):
        """An org admin can view JTs in their org through implicit grant."""
        org = Organization.objects.create(name='test_org')
        jt = JobTemplate.objects.create(name='patching', organization=org)
        admin_user = User.objects.create(username='org_admin', password='org_admin')

        org.admin_role.members.add(admin_user)

        old_url = '/api/v2/job_templates/patching/'
        resolved = URLModificationMiddleware._convert_named_url(old_url, user=admin_user)
        assert resolved == f'/api/v2/job_templates/{jt.pk}/'

        response = get(resolved, user=admin_user, expect=200)
        assert response.data['id'] == jt.pk

    def test_org_member_cannot_see_jt_via_old_style_url(self):
        """An org member does NOT automatically get JT view access.
        The old-style URL should not resolve to the JT.
        """
        org = Organization.objects.create(name='test_org')
        JobTemplate.objects.create(name='patching', organization=org)
        member = User.objects.create(username='member', password='member')

        org.member_role.members.add(member)

        old_url = '/api/v2/job_templates/patching/'
        resolved = URLModificationMiddleware._convert_named_url(old_url, user=member)
        assert resolved == old_url


@pytest.mark.django_db
class TestConvertNamedUrl:
    @pytest.mark.parametrize(
        "url",
        (
            "/api/",
            "/api/v2/",
            "/api/v2/hosts/",
            "/api/v2/hosts/1/",
            "/api/v2/organizations/1/inventories/",
            "/api/foo/",
            "/api/foo/v2/",
            "/api/foo/v2/organizations/",
            "/api/foo/v2/organizations/1/",
            "/api/foo/v2/organizations/1/inventories/",
            "/api/foobar/",
            "/api/foobar/v2/",
            "/api/foobar/v2/organizations/",
            "/api/foobar/v2/organizations/1/",
            "/api/foobar/v2/organizations/1/inventories/",
            "/api/foobar/v2/organizations/1/inventories/",
        ),
    )
    def test_noop(self, url, settings):
        settings.OPTIONAL_API_URLPATTERN_PREFIX = ''
        assert URLModificationMiddleware._convert_named_url(url) == url

        settings.OPTIONAL_API_URLPATTERN_PREFIX = 'foo'
        assert URLModificationMiddleware._convert_named_url(url) == url

    def test_named_org(self):
        test_org = Organization.objects.create(name='test_org')

        assert URLModificationMiddleware._convert_named_url('/api/v2/organizations/test_org/') == f'/api/v2/organizations/{test_org.pk}/'

    def test_named_org_optional_api_urlpattern_prefix_interaction(self, settings):
        settings.OPTIONAL_API_URLPATTERN_PREFIX = 'bar'
        test_org = Organization.objects.create(name='test_org')

        assert URLModificationMiddleware._convert_named_url('/api/bar/v2/organizations/test_org/') == f'/api/bar/v2/organizations/{test_org.pk}/'

    @pytest.mark.parametrize("prefix", ['', 'bar'])
    def test_named_org_not_found(self, prefix, settings):
        settings.OPTIONAL_API_URLPATTERN_PREFIX = prefix
        if prefix:
            prefix += '/'

        assert URLModificationMiddleware._convert_named_url(f'/api/{prefix}v2/organizations/does-not-exist/') == f'/api/{prefix}v2/organizations/0/'

    @pytest.mark.parametrize("prefix", ['', 'bar'])
    def test_named_sub_resource(self, prefix, settings):
        settings.OPTIONAL_API_URLPATTERN_PREFIX = prefix
        test_org = Organization.objects.create(name='test_org')
        if prefix:
            prefix += '/'

        assert (
            URLModificationMiddleware._convert_named_url(f'/api/{prefix}v2/organizations/test_org/inventories/')
            == f'/api/{prefix}v2/organizations/{test_org.pk}/inventories/'
        )

    def test_named_job_template(self):
        org = Organization.objects.create(name='test_org')
        tpl = JobTemplate.objects.create(name='test_tpl', organization=org)

        # first, cause a '404' - we want to verify that no state from previous requests is carried over when named
        # urls are resolved
        assert URLModificationMiddleware._convert_named_url('/api/v2/job_templates/test/tpl++test_org/') == '/api/v2/job_templates/test/tpl++test_org/'

        # try to resolve a valid url - it should succeed
        assert URLModificationMiddleware._convert_named_url('/api/v2/job_templates/test_tpl++test_org/') == f'/api/v2/job_templates/{tpl.pk}/'
