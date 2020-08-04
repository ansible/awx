import pytest
from unittest import mock

from awx.main.models import Project, Credential, CredentialType
from awx.main.models.organization import Organization


@pytest.mark.django_db
def test_project_initial_update():
    with mock.patch.object(Project, "update") as mock_update:
        Project.objects.create(name='foo', scm_type='git')
    mock_update.assert_called_once_with()


@pytest.mark.django_db
def test_does_not_update_nonsensitive_change(project):
    with mock.patch.object(Project, "update") as mock_update:
        project.scm_update_on_launch = not project.scm_update_on_launch
        project.save()
    mock_update.assert_not_called()


@pytest.mark.django_db
def test_sensitive_change_triggers_update(project):
    with mock.patch.object(Project, "update") as mock_update:
        project.scm_url = 'https://foo.invalid'
        project.save()
    mock_update.assert_called_once_with()
    # test other means of initialization
    project = Project.objects.get(pk=project.pk)
    with mock.patch.object(Project, "update") as mock_update:
        project.scm_url = 'https://foo2.invalid'
        project.save()
    mock_update.assert_called_once_with()


@pytest.mark.django_db
def test_local_path_autoset(organization):
    with mock.patch.object(Project, "update"):
        p = Project.objects.create(
            name="test-proj",
            organization=organization,
            scm_url='localhost',
            scm_type='git'
        )
    assert p.local_path == f'_{p.id}__test_proj'


@pytest.mark.django_db
def test_foreign_key_change_changes_modified_by(project, organization):
    assert project._get_fields_snapshot()['organization_id'] == organization.id
    project.organization = Organization(name='foo', pk=41)
    assert project._get_fields_snapshot()['organization_id'] == 41


@pytest.mark.django_db
def test_project_related_jobs(project):
    update = project.create_unified_job()
    assert update.id in [u.id for u in project._get_related_jobs()]


@pytest.mark.django_db
def test_galaxy_credentials(project):
    org = project.organization
    galaxy = CredentialType.defaults['galaxy_api_token']()
    galaxy.save()
    for i in range(5):
        cred = Credential.objects.create(
            name=f'Ansible Galaxy {i + 1}',
            organization=org,
            credential_type=galaxy,
            inputs={
                'url': 'https://galaxy.ansible.com/'
            }
        )
        cred.save()
        org.galaxy_credentials.add(cred)

    assert [
        cred.name for cred in org.galaxy_credentials.all()
    ] == [
        'Ansible Galaxy 1',
        'Ansible Galaxy 2',
        'Ansible Galaxy 3',
        'Ansible Galaxy 4',
        'Ansible Galaxy 5',
    ]
