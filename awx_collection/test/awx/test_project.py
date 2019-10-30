import pytest

from awx.main.models import Project


@pytest.mark.django_db
def test_create_project(run_module, admin_user, organization):
    result = run_module('tower_project', dict(
        name='foo',
        organization=organization.name,
        scm_type='git',
        scm_url='https://foo.invalid'
    ), admin_user)
    assert result.pop('changed', None), result

    proj = Project.objects.get(name='foo')
    assert proj.scm_url == 'https://foo.invalid'
    assert proj.organization == organization

    result.pop('invocation')
    assert result == {
        'id': proj.id,
        'project': 'foo',
        'state': 'present'
    }
