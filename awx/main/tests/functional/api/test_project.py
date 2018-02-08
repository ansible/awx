import os

from backports.tempfile import TemporaryDirectory
from django.conf import settings
import pytest

from awx.api.versioning import reverse


@pytest.mark.django_db
class TestInsightsCredential:
    def test_insights_credential(self, patch, insights_project, admin_user, insights_credential):
        patch(insights_project.get_absolute_url(), 
              {'credential': insights_credential.id}, admin_user,
              expect=200)

    def test_non_insights_credential(self, patch, insights_project, admin_user, scm_credential):
        patch(insights_project.get_absolute_url(), 
              {'credential': scm_credential.id}, admin_user,
              expect=400)


@pytest.mark.django_db
def test_project_custom_virtualenv(get, patch, project, admin):
    with TemporaryDirectory(dir=settings.BASE_VENV_PATH) as temp_dir:
        os.makedirs(os.path.join(temp_dir, 'bin', 'activate'))
        url = reverse('api:project_detail', kwargs={'pk': project.id})
        patch(url, {'custom_virtualenv': temp_dir}, user=admin, expect=200)
        assert get(url, user=admin).data['custom_virtualenv'] == os.path.join(temp_dir, '')


@pytest.mark.django_db
def test_project_invalid_custom_virtualenv(get, patch, project, admin):
    url = reverse('api:project_detail', kwargs={'pk': project.id})
    resp = patch(url, {'custom_virtualenv': '/foo/bar'}, user=admin, expect=400)
    assert resp.data['custom_virtualenv'] == [
        '/foo/bar is not a valid virtualenv in {}'.format(settings.BASE_VENV_PATH)
    ]


@pytest.mark.django_db
def test_project_edit_resets_revision(patch, project, admin_user):
    old_rev = project.scm_revision
    assert old_rev != ''  # counting on fixture to have dummy revision
    patch(
        project.get_absolute_url(), {'scm_url': 'http://foobar.invalid'},
        user=admin_user, expect=200
    )
    project.refresh_from_db()
    assert project.scm_revision != old_rev
    assert project.scm_revision == ''
