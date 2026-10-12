import pytest

from awx.api.versioning import reverse
from awx.main.models import Project, JobTemplate


@pytest.mark.django_db
class TestInsightsCredential:
    def test_insights_credential(self, patch, insights_project, admin_user, insights_credential):
        patch(insights_project.get_absolute_url(), {'credential': insights_credential.id}, admin_user, expect=200)

    def test_non_insights_credential(self, patch, insights_project, admin_user, scm_credential):
        patch(insights_project.get_absolute_url(), {'credential': scm_credential.id}, admin_user, expect=400)


@pytest.mark.django_db
def test_no_changing_overwrite_behavior_if_used(post, patch, organization, admin_user):
    r1 = post(
        url=reverse('api:project_list'),
        data={
            'name': 'fooo',
            'organization': organization.id,
            'allow_override': True,
            'scm_type': 'git',
            'scm_url': 'https://github.com/ansible/test-playbooks.git',
        },
        user=admin_user,
        expect=201,
    )
    jt = JobTemplate.objects.create(name='provides branch', project_id=r1.data['id'], playbook='helloworld.yml', scm_branch='foobar')
    r2 = patch(url=reverse('api:project_detail', kwargs={'pk': r1.data['id']}), data={'allow_override': False}, user=admin_user, expect=400)
    p = Project.objects.get(pk=r1.data['id'])
    assert 'job templates depend on branch override behavior for this project' in str(r2.data['allow_override'])
    assert 'ids: {}'.format(jt.id) in str(r2.data['allow_override'])
    assert p.allow_override is True


@pytest.mark.django_db
def test_changing_overwrite_behavior_okay_if_not_used(post, patch, organization, admin_user):
    r1 = post(
        url=reverse('api:project_list'),
        data={
            'name': 'fooo',
            'organization': organization.id,
            'allow_override': True,
            'scm_type': 'git',
            'scm_url': 'https://github.com/ansible/test-playbooks.git',
        },
        user=admin_user,
        expect=201,
    )
    patch(url=reverse('api:project_detail', kwargs={'pk': r1.data['id']}), data={'allow_override': False}, user=admin_user, expect=200)
    assert Project.objects.get(pk=r1.data['id']).allow_override is False


@pytest.mark.django_db
def test_scm_project_local_path_invalid(get, patch, project, admin):
    url = reverse('api:project_detail', kwargs={'pk': project.id})
    resp = patch(url, {'local_path': '/foo/bar'}, user=admin, expect=400)
    assert resp.data['local_path'] == ['Cannot change local_path for git-based projects']


@pytest.mark.django_db
def test_galaxy_update_on_launch_default(post, organization, admin_user):
    """Test that galaxy_update_on_launch defaults to False"""
    r = post(
        url=reverse('api:project_list'),
        data={
            'name': 'test-project',
            'organization': organization.id,
            'scm_type': 'git',
            'scm_url': 'https://github.com/ansible/test-playbooks.git',
        },
        user=admin_user,
        expect=201,
    )
    assert r.data['galaxy_update_on_launch'] is False
    p = Project.objects.get(pk=r.data['id'])
    assert p.galaxy_update_on_launch is False


@pytest.mark.django_db
def test_galaxy_update_on_launch_create_enabled(post, organization, admin_user):
    """Test creating a project with galaxy_update_on_launch enabled"""
    r = post(
        url=reverse('api:project_list'),
        data={
            'name': 'test-project',
            'organization': organization.id,
            'scm_type': 'git',
            'scm_url': 'https://github.com/ansible/test-playbooks.git',
            'galaxy_update_on_launch': True,
        },
        user=admin_user,
        expect=201,
    )
    assert r.data['galaxy_update_on_launch'] is True
    p = Project.objects.get(pk=r.data['id'])
    assert p.galaxy_update_on_launch is True


@pytest.mark.django_db
def test_galaxy_update_on_launch_update(post, patch, organization, admin_user):
    """Test updating galaxy_update_on_launch via PATCH"""
    r1 = post(
        url=reverse('api:project_list'),
        data={
            'name': 'test-project',
            'organization': organization.id,
            'scm_type': 'git',
            'scm_url': 'https://github.com/ansible/test-playbooks.git',
            'galaxy_update_on_launch': False,
        },
        user=admin_user,
        expect=201,
    )
    assert r1.data['galaxy_update_on_launch'] is False

    r2 = patch(
        url=reverse('api:project_detail', kwargs={'pk': r1.data['id']}),
        data={'galaxy_update_on_launch': True},
        user=admin_user,
        expect=200,
    )
    assert r2.data['galaxy_update_on_launch'] is True
    p = Project.objects.get(pk=r1.data['id'])
    assert p.galaxy_update_on_launch is True
