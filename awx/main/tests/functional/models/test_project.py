import pytest
from unittest import mock

from awx.main.models import Project
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
def test_foreign_key_change_changes_modified_by(project, organization):
    assert project._get_fields_snapshot()['organization_id'] == organization.id
    project.organization = Organization(name='foo', pk=41)
    assert project._get_fields_snapshot()['organization_id'] == 41
