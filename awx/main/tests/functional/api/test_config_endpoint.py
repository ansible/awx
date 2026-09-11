import pytest
from awx.api.versioning import reverse
from rest_framework import status

from awx.main.models.jobs import JobTemplate


@pytest.mark.django_db
class TestConfigEndpointFields:
    def test_base_fields_all_users(self, get, rando):
        url = reverse('api:api_v2_config_view')
        response = get(url, rando, expect=200)

        assert 'time_zone' in response.data
        assert 'license_info' in response.data
        assert 'version' in response.data
        assert 'eula' in response.data
        assert 'analytics_status' in response.data
        assert 'analytics_collectors' in response.data
        assert 'become_methods' in response.data

    @pytest.mark.parametrize(
        "role_type",
        [
            "superuser",
            "system_auditor",
            "org_admin",
            "org_auditor",
            "org_project_admin",
        ],
    )
    def test_privileged_users_conditional_fields(self, get, user, organization, admin, role_type):
        url = reverse('api:api_v2_config_view')

        if role_type == "superuser":
            test_user = admin
        elif role_type == "system_auditor":
            test_user = user('system-auditor', is_superuser=False)
            test_user.is_system_auditor = True
            test_user.save()
        elif role_type == "org_admin":
            test_user = user('org-admin', is_superuser=False)
            organization.admin_role.members.add(test_user)
        elif role_type == "org_auditor":
            test_user = user('org-auditor', is_superuser=False)
            organization.auditor_role.members.add(test_user)
        elif role_type == "org_project_admin":
            test_user = user('org-project-admin', is_superuser=False)
            organization.project_admin_role.members.add(test_user)

        response = get(url, test_user, expect=200)

        assert 'project_base_dir' in response.data
        assert 'project_local_paths' in response.data
        assert 'custom_virtualenvs' in response.data

    def test_job_template_admin_gets_venvs_only(self, get, user, organization, project, inventory):
        """Test that JobTemplate admin without org access gets only custom_virtualenvs"""
        jt_admin = user('jt-admin', is_superuser=False)

        jt = JobTemplate.objects.create(name='test-jt', organization=organization, project=project, inventory=inventory)
        jt.admin_role.members.add(jt_admin)

        url = reverse('api:api_v2_config_view')
        response = get(url, jt_admin, expect=200)

        assert 'custom_virtualenvs' in response.data
        assert 'project_base_dir' not in response.data
        assert 'project_local_paths' not in response.data

    def test_normal_user_no_conditional_fields(self, get, rando):
        url = reverse('api:api_v2_config_view')
        response = get(url, rando, expect=200)

        assert 'project_base_dir' not in response.data
        assert 'project_local_paths' not in response.data
        assert 'custom_virtualenvs' not in response.data

    def test_unauthenticated_denied(self, get):
        """Test that unauthenticated requests are denied"""
        url = reverse('api:api_v2_config_view')
        response = get(url, None, expect=401)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
