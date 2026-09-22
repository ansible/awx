from unittest.mock import patch, MagicMock

import pytest
from django.test import override_settings
from awx.api.versioning import reverse
from awx.api import validation_patterns
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

    def test_basic_auth_clears_service_account_settings(self, post, admin, settings):
        """Test that setting basic auth credentials clears service account settings"""
        # Pre-populate service account settings
        settings.SUBSCRIPTIONS_CLIENT_ID = 'existing_client_id'
        settings.SUBSCRIPTIONS_CLIENT_SECRET = 'existing_client_secret'

        data = {'subscriptions_username': 'test_user', 'subscriptions_password': 'test_password'}

        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)

            assert response.status_code == status.HTTP_200_OK
            # Basic auth settings should be set
            assert settings.SUBSCRIPTIONS_USERNAME == 'test_user'
            assert settings.SUBSCRIPTIONS_PASSWORD == 'test_password'
            # Service account settings should be cleared
            assert settings.SUBSCRIPTIONS_CLIENT_ID == ""
            assert settings.SUBSCRIPTIONS_CLIENT_SECRET == ""

    def test_service_account_clears_basic_auth_settings(self, post, admin, settings):
        """Test that setting service account credentials clears basic auth settings"""
        # Pre-populate basic auth settings
        settings.SUBSCRIPTIONS_USERNAME = 'existing_username'
        settings.SUBSCRIPTIONS_PASSWORD = 'existing_password'

        data = {'subscriptions_client_id': 'test_client_id', 'subscriptions_client_secret': 'test_client_secret'}

        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)

            assert response.status_code == status.HTTP_200_OK
            # Service account settings should be set
            assert settings.SUBSCRIPTIONS_CLIENT_ID == 'test_client_id'
            assert settings.SUBSCRIPTIONS_CLIENT_SECRET == 'test_client_secret'
            # Basic auth settings should be cleared
            assert settings.SUBSCRIPTIONS_USERNAME == ""
            assert settings.SUBSCRIPTIONS_PASSWORD == ""


# ---------------------------------------------------------------------------
# CleanTextMixin on SubscriptionCredentialsSerializer (AAP-93690)
# ---------------------------------------------------------------------------

UNSAFE_INPUT = '<script>alert(1)</script>'

# Deterministic stand-in for the real Tier 2 regex so tests don't depend on
# DAB's pattern generation being importable in every test environment.
FAKE_TIER2_PATTERN = r'^[^\<\>]*$'


@pytest.fixture
def enforce_clean_text():
    """Enable CleanTextMixin enforcement for the duration of a test."""
    with patch('ansible_base.lib.serializers.mixins.get_setting', return_value=True):
        yield


@pytest.mark.django_db
class TestSubscriptionCleanText:
    """CleanText validation on /api/v2/config/subscriptions/ (AAP-93690)."""

    def test_rejects_unsafe_client_id(self, post, admin, enforce_clean_text):
        """AC1: POST rejects unsafe input in subscriptions_client_id."""
        data = {
            'subscriptions_client_id': UNSAFE_INPUT,
            'subscriptions_client_secret': 'valid_secret',
        }
        response = post(reverse('api:api_v2_subscription_view'), data, admin)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'subscriptions_client_id' in response.data

    def test_rejects_unsafe_username(self, post, admin, enforce_clean_text):
        """AC1: POST rejects unsafe input in subscriptions_username."""
        data = {
            'subscriptions_username': UNSAFE_INPUT,
            'subscriptions_password': 'valid_password',
        }
        response = post(reverse('api:api_v2_subscription_view'), data, admin)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'subscriptions_username' in response.data

    def test_allows_unsafe_client_secret(self, post, admin, enforce_clean_text):
        """AC2: client_secret is excluded from CleanText -- unsafe values pass."""
        data = {
            'subscriptions_client_id': 'safe_id',
            'subscriptions_client_secret': UNSAFE_INPUT,
        }
        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)
            assert response.status_code == status.HTTP_200_OK

    def test_allows_unsafe_password(self, post, admin, enforce_clean_text):
        """AC2: password is excluded from CleanText -- unsafe values pass."""
        data = {
            'subscriptions_username': 'safe_user',
            'subscriptions_password': UNSAFE_INPUT,
        }
        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)
            assert response.status_code == status.HTTP_200_OK

    def test_safe_input_passes_with_enforcement(self, post, admin, enforce_clean_text):
        """Safe input succeeds even when enforcement is on."""
        data = {
            'subscriptions_username': 'my_rh_user',
            'subscriptions_password': 'my_rh_pass',
        }
        with patch('awx.api.views.root.get_licenser') as mock_get_licenser:
            mock_licenser = MagicMock()
            mock_licenser.validate_rh.return_value = []
            mock_get_licenser.return_value = mock_licenser

            response = post(reverse('api:api_v2_subscription_view'), data, admin)
            assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestSubscriptionOptionsPatterns:
    """OPTIONS metadata exposes validation patterns (AAP-93690 AC4)."""

    @pytest.fixture(autouse=True)
    def _fake_pattern_helpers(self, monkeypatch):
        """Provide deterministic Tier 1/2 pattern helpers so tests don't depend
        on DAB's build_tier*_frontend_pattern being importable."""
        monkeypatch.setattr(validation_patterns, '_get_tier1_pattern', lambda: {'pattern': 'T1', 'description': 'd1', 'flags': 'u', 'normalize': 'NFC'})
        monkeypatch.setattr(validation_patterns, '_get_tier2_pattern', lambda: {'pattern': FAKE_TIER2_PATTERN, 'description': 'd2', 'flags': 'i'})

    def test_options_shows_patterns_when_enabled(self, options, admin):
        """AC4: client_id and username expose Tier 2 patterns when enforcement is on."""
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            response = options(reverse('api:api_v2_subscription_view'), None, admin)

        assert response.status_code == status.HTTP_200_OK
        post_fields = response.data.get('actions', {}).get('POST', {})
        # Non-excluded fields should have patterns
        assert post_fields['subscriptions_client_id']['pattern'] == FAKE_TIER2_PATTERN, 'client_id should have Tier 2 pattern'
        assert post_fields['subscriptions_username']['pattern'] == FAKE_TIER2_PATTERN, 'username should have Tier 2 pattern'
        # Excluded (secret) fields should NOT have patterns
        assert 'pattern' not in post_fields.get('subscriptions_client_secret', {}), 'client_secret should not have a pattern'
        assert 'pattern' not in post_fields.get('subscriptions_password', {}), 'password should not have a pattern'

    def test_options_no_patterns_when_disabled(self, options, admin):
        """Patterns are absent when enforcement is off."""
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=False):
            response = options(reverse('api:api_v2_subscription_view'), None, admin)

        assert response.status_code == status.HTTP_200_OK
        post_fields = response.data.get('actions', {}).get('POST', {})
        for field_name in ('subscriptions_client_id', 'subscriptions_username'):
            assert 'pattern' not in post_fields.get(field_name, {}), f'{field_name} should not have a pattern when disabled'
