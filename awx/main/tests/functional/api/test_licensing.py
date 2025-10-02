from unittest.mock import patch, MagicMock

import pytest
from awx.api.versioning import reverse
from rest_framework import status


@pytest.mark.django_db
class TestApiV2SubscriptionView:
    """Test cases for the /api/v2/config/subscriptions/ endpoint"""

    def test_basic_auth(self, post, admin):
        """Test POST with subscriptions_username and subscriptions_password calls validate_rh with basic_auth=True"""
        data = {'subscriptions_username': 'test_user', 'subscriptions_password': 'test_password'}

        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)

            assert response.status_code == status.HTTP_200_OK
            mock_licenser.validate_rh.assert_called_once_with('test_user', 'test_password', True)

    def test_service_account(self, post, admin):
        """Test POST with subscriptions_client_id and subscriptions_client_secret calls validate_rh with basic_auth=False"""
        data = {'subscriptions_client_id': 'test_client_id', 'subscriptions_client_secret': 'test_client_secret'}

        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)

            assert response.status_code == status.HTTP_200_OK
            mock_licenser.validate_rh.assert_called_once_with('test_client_id', 'test_client_secret', False)

    def test_encrypted_password_basic_auth(self, post, admin, settings):
        """Test POST with $encrypted$ password uses settings value for basic auth"""
        data = {'subscriptions_username': 'test_user', 'subscriptions_password': '$encrypted$'}

        settings.SUBSCRIPTIONS_PASSWORD = 'actual_password_from_settings'

        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)

            assert response.status_code == status.HTTP_200_OK
            mock_licenser.validate_rh.assert_called_once_with('test_user', 'actual_password_from_settings', True)

    def test_encrypted_client_secret_service_account(self, post, admin, settings):
        """Test POST with $encrypted$ client_secret uses settings value for service_account"""
        data = {'subscriptions_client_id': 'test_client_id', 'subscriptions_client_secret': '$encrypted$'}

        settings.SUBSCRIPTIONS_CLIENT_SECRET = 'actual_secret_from_settings'

        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)

            assert response.status_code == status.HTTP_200_OK
            mock_licenser.validate_rh.assert_called_once_with('test_client_id', 'actual_secret_from_settings', False)

    def test_missing_username_returns_error(self, post, admin):
        """Test POST with missing username returns 400 error"""
        data = {'subscriptions_password': 'test_password'}

        response = post(reverse('api:api_v2_subscription_view'), data, admin)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Missing subscription credentials' in response.data['error']

    def test_missing_password_returns_error(self, post, admin, settings):
        """Test POST with missing password returns 400 error"""
        data = {'subscriptions_username': 'test_user'}
        settings.SUBSCRIPTIONS_PASSWORD = None

        response = post(reverse('api:api_v2_subscription_view'), data, admin)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Missing subscription credentials' in response.data['error']

    def test_missing_client_id_returns_error(self, post, admin):
        """Test POST with missing client_id returns 400 error"""
        data = {'subscriptions_client_secret': 'test_secret'}

        response = post(reverse('api:api_v2_subscription_view'), data, admin)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Missing subscription credentials' in response.data['error']

    def test_missing_client_secret_returns_error(self, post, admin, settings):
        """Test POST with missing client_secret returns 400 error"""
        data = {'subscriptions_client_id': 'test_client_id'}
        settings.SUBSCRIPTIONS_CLIENT_SECRET = None

        response = post(reverse('api:api_v2_subscription_view'), data, admin)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Missing subscription credentials' in response.data['error']

    def test_empty_username_returns_error(self, post, admin):
        """Test POST with empty username returns 400 error"""
        data = {'subscriptions_username': '', 'subscriptions_password': 'test_password'}

        response = post(reverse('api:api_v2_subscription_view'), data, admin)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Missing subscription credentials' in response.data['error']

    def test_empty_password_returns_error(self, post, admin, settings):
        """Test POST with empty password returns 400 error"""
        data = {'subscriptions_username': 'test_user', 'subscriptions_password': ''}
        settings.SUBSCRIPTIONS_PASSWORD = None

        response = post(reverse('api:api_v2_subscription_view'), data, admin)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Missing subscription credentials' in response.data['error']

    def test_non_superuser_permission_denied(self, post, rando):
        """Test that non-superuser cannot access the endpoint"""
        data = {'subscriptions_username': 'test_user', 'subscriptions_password': 'test_password'}

        response = post(reverse('api:api_v2_subscription_view'), data, rando)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_settings_updated_on_successful_basic_auth(self, post, admin, settings):
        """Test that settings are updated when basic auth validation succeeds"""
        data = {'subscriptions_username': 'new_username', 'subscriptions_password': 'new_password'}

        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)

            assert response.status_code == status.HTTP_200_OK
            assert settings.SUBSCRIPTIONS_USERNAME == 'new_username'
            assert settings.SUBSCRIPTIONS_PASSWORD == 'new_password'

    def test_settings_updated_on_successful_service_account(self, post, admin, settings):
        """Test that settings are updated when service account validation succeeds"""
        data = {'subscriptions_client_id': 'new_client_id', 'subscriptions_client_secret': 'new_client_secret'}

        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)

            assert response.status_code == status.HTTP_200_OK
            assert settings.SUBSCRIPTIONS_CLIENT_ID == 'new_client_id'
            assert settings.SUBSCRIPTIONS_CLIENT_SECRET == 'new_client_secret'

    def test_analytics_credentials_plumbed_when_missing(self, post, admin, settings):
        """Test that service account credentials are plumbed to analytics when REDHAT_* settings are missing"""
        data = {'subscriptions_client_id': 'analytics_client_id', 'subscriptions_client_secret': 'analytics_client_secret'}

        # Ensure REDHAT_* settings are not set
        settings.REDHAT_USERNAME = None
        settings.REDHAT_PASSWORD = None

        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)

            assert response.status_code == status.HTTP_200_OK
            assert settings.REDHAT_USERNAME == 'analytics_client_id'
            assert settings.REDHAT_PASSWORD == 'analytics_client_secret'

    def test_analytics_credentials_not_overwritten_when_present(self, post, admin, settings):
        """Test that existing REDHAT_* settings are not overwritten"""
        data = {'subscriptions_client_id': 'new_client_id', 'subscriptions_client_secret': 'new_client_secret'}

        # Set existing REDHAT_* settings
        settings.REDHAT_USERNAME = 'existing_username'
        settings.REDHAT_PASSWORD = 'existing_password'

        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)

            assert response.status_code == status.HTTP_200_OK
            # REDHAT_* settings should remain unchanged
            assert settings.REDHAT_USERNAME == 'existing_username'
            assert settings.REDHAT_PASSWORD == 'existing_password'

    def test_validate_rh_exception_handling(self, post, admin):
        """Test that exceptions from validate_rh are properly handled"""
        data = {'subscriptions_username': 'test_user', 'subscriptions_password': 'test_password'}

        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.side_effect = Exception("Connection error")
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_mixed_credentials_prioritizes_client_id(self, post, admin):
        """Test that when both username and client_id are provided, client_id takes precedence"""
        data = {
            'subscriptions_username': 'test_user',
            'subscriptions_password': 'test_password',
            'subscriptions_client_id': 'test_client_id',
            'subscriptions_client_secret': 'test_client_secret',
        }

        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)

            assert response.status_code == status.HTTP_200_OK
            # Should use service account (basic_auth=False) since client_id is present
            mock_licenser.validate_rh.assert_called_once_with('test_client_id', 'test_client_secret', False)
