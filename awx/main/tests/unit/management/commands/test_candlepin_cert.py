# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

"""Tests for candlepin_cert management command."""

from io import StringIO
from unittest import mock

import pytest
from django.core.management import call_command
from django.test.utils import override_settings


class TestCandlepinCertCommand:
    """Tests for candlepin_cert management command."""

    @mock.patch('awx.main.management.commands.candlepin_cert._save_candlepin_registration_to_db')
    @mock.patch('awx.main.management.commands.candlepin_cert.CandlepinClient')
    @mock.patch('awx.main.management.commands.candlepin_cert.resolve_registration_credentials')
    @mock.patch('awx.main.management.commands.candlepin_cert._fetch_candlepin_cert_from_db')
    @override_settings(
        AWX_ANALYTICS_CANDLEPIN_URL='https://test.example.com',
        AWX_ANALYTICS_CANDLEPIN_CA=None,
        AWX_ANALYTICS_CANDLEPIN_PROXY_URL=None,
    )
    def test_register_success(self, mock_fetch_cert, mock_resolve_creds, mock_client_class, mock_save_reg):
        """Test successful registration."""
        # No existing cert
        mock_fetch_cert.return_value = (None, None, None)

        # Valid credentials
        mock_resolve_creds.return_value = ('test_user', 'test_pass', 'test_org', 'install-uuid', None)

        # Mock successful registration
        mock_client = mock.Mock()
        mock_client.register_consumer.return_value = ('cert-pem', 'key-pem', 'consumer-uuid')
        mock_client_class.return_value = mock_client

        # Mock successful save
        mock_save_reg.return_value = True

        out = StringIO()
        call_command('candlepin_cert', 'register', stdout=out, stderr=StringIO())

        output = out.getvalue()
        assert 'Registered successfully' in output
        assert 'consumer-uuid' in output

        mock_client.register_consumer.assert_called_once_with('test_user', 'test_pass', 'test_org', install_uuid='install-uuid')
        mock_save_reg.assert_called_once_with('cert-pem', 'key-pem', 'consumer-uuid')

    @mock.patch('awx.main.management.commands.candlepin_cert._fetch_candlepin_cert_from_db')
    def test_register_already_registered_without_force(self, mock_fetch_cert):
        """Test registration fails when cert already exists and --force not provided."""
        # Existing cert
        mock_fetch_cert.return_value = ('existing-cert', 'existing-key', 'existing-uuid')

        out = StringIO()
        call_command('candlepin_cert', 'register', stdout=out, stderr=StringIO())

        output = out.getvalue()
        assert 'already stored' in output
        assert '--force' in output

    @mock.patch('awx.main.management.commands.candlepin_cert._save_candlepin_registration_to_db')
    @mock.patch('awx.main.management.commands.candlepin_cert.CandlepinClient')
    @mock.patch('awx.main.management.commands.candlepin_cert.resolve_registration_credentials')
    @mock.patch('awx.main.management.commands.candlepin_cert._fetch_candlepin_cert_from_db')
    @override_settings(
        AWX_ANALYTICS_CANDLEPIN_URL='https://test.example.com',
        AWX_ANALYTICS_CANDLEPIN_CA=None,
        AWX_ANALYTICS_CANDLEPIN_PROXY_URL=None,
    )
    def test_register_with_force_flag(self, mock_fetch_cert, mock_resolve_creds, mock_client_class, mock_save_reg):
        """Test registration succeeds with --force even when cert exists."""
        # Existing cert
        mock_fetch_cert.return_value = ('existing-cert', 'existing-key', 'existing-uuid')

        # Valid credentials
        mock_resolve_creds.return_value = ('test_user', 'test_pass', 'test_org', 'install-uuid', None)

        # Mock successful registration
        mock_client = mock.Mock()
        mock_client.register_consumer.return_value = ('new-cert-pem', 'new-key-pem', 'new-consumer-uuid')
        mock_client_class.return_value = mock_client

        # Mock successful save
        mock_save_reg.return_value = True

        out = StringIO()
        call_command('candlepin_cert', 'register', '--force', stdout=out, stderr=StringIO())

        output = out.getvalue()
        assert 'Registered successfully' in output

        mock_client.register_consumer.assert_called_once()
        mock_save_reg.assert_called_once_with('new-cert-pem', 'new-key-pem', 'new-consumer-uuid')

    @mock.patch('awx.main.management.commands.candlepin_cert.resolve_registration_credentials')
    @mock.patch('awx.main.management.commands.candlepin_cert._fetch_candlepin_cert_from_db')
    def test_register_missing_credentials(self, mock_fetch_cert, mock_resolve_creds):
        """Test registration fails when credentials are missing."""
        mock_fetch_cert.return_value = (None, None, None)

        # Missing credentials
        mock_resolve_creds.return_value = (None, None, None, None, ['username', 'password'])

        err = StringIO()
        with pytest.raises(SystemExit) as exc_info:
            call_command('candlepin_cert', 'register', stderr=err)

        assert exc_info.value.code == 1
        error_output = err.getvalue()
        assert 'Missing required value' in error_output

    @mock.patch('awx.main.management.commands.candlepin_cert._save_candlepin_cert_to_db')
    @mock.patch('awx.main.management.commands.candlepin_cert.CandlepinClient')
    @mock.patch('awx.main.management.commands.candlepin_cert.parse_cert')
    @mock.patch('awx.main.management.commands.candlepin_cert.needs_renewal')
    @mock.patch('awx.main.management.commands.candlepin_cert._fetch_candlepin_cert_from_db')
    @override_settings(
        AWX_ANALYTICS_CANDLEPIN_URL='https://test.example.com',
        AWX_ANALYTICS_CANDLEPIN_CA=None,
        AWX_ANALYTICS_CANDLEPIN_PROXY_URL=None,
        AWX_ANALYTICS_CANDLEPIN_RENEWAL_THRESHOLD_DAYS=90,
    )
    def test_renew_success(self, mock_fetch_cert, mock_needs_renewal, mock_parse_cert, mock_client_class, mock_save_cert):
        """Test successful certificate renewal."""
        # Existing cert
        mock_fetch_cert.return_value = ('old-cert', 'old-key', 'consumer-uuid')

        # Parse cert returns metadata
        mock_parse_cert.side_effect = [
            {'serial': '123', 'cn': 'test', 'not_after': '2026-06-01', 'days_remaining': 10},  # Current cert
            {'serial': '456', 'cn': 'test', 'not_after': '2027-06-01', 'days_remaining': 365},  # Renewed cert
        ]

        # Renewal needed
        mock_needs_renewal.return_value = True

        # Mock successful check-in and renewal
        mock_client = mock.Mock()
        mock_client.checkin.return_value = True
        mock_client.regenerate_cert.return_value = ('new-cert', 'new-key')
        mock_client_class.return_value = mock_client

        mock_save_cert.return_value = True

        out = StringIO()
        call_command('candlepin_cert', 'renew', stdout=out, stderr=StringIO())

        output = out.getvalue()
        assert 'Check-in successful' in output
        assert 'Certificate renewed successfully' in output
        assert 'saved to database' in output

        mock_client.checkin.assert_called_once_with('consumer-uuid', 'old-cert', 'old-key')
        mock_client.regenerate_cert.assert_called_once()
        mock_save_cert.assert_called_once_with('new-cert', 'new-key')

    @mock.patch('awx.main.management.commands.candlepin_cert._fetch_candlepin_cert_from_db')
    def test_renew_no_cert_in_db(self, mock_fetch_cert):
        """Test renew fails when no certificate exists in database."""
        mock_fetch_cert.return_value = (None, None, None)

        err = StringIO()
        with pytest.raises(SystemExit) as exc_info:
            call_command('candlepin_cert', 'renew', stderr=err)

        assert exc_info.value.code == 1
        error_output = err.getvalue()
        assert 'No Candlepin identity certificate found' in error_output
        assert 'Run the register subcommand first' in error_output

    @mock.patch('awx.main.management.commands.candlepin_cert.CandlepinClient')
    @mock.patch('awx.main.management.commands.candlepin_cert.parse_cert')
    @mock.patch('awx.main.management.commands.candlepin_cert.needs_renewal')
    @mock.patch('awx.main.management.commands.candlepin_cert._fetch_candlepin_cert_from_db')
    @override_settings(
        AWX_ANALYTICS_CANDLEPIN_URL='https://test.example.com',
        AWX_ANALYTICS_CANDLEPIN_CA=None,
        AWX_ANALYTICS_CANDLEPIN_PROXY_URL=None,
        AWX_ANALYTICS_CANDLEPIN_RENEWAL_THRESHOLD_DAYS=90,
    )
    def test_renew_not_needed(self, mock_fetch_cert, mock_needs_renewal, mock_parse_cert, mock_client_class):
        """Test renew when certificate is still valid and renewal not needed."""
        mock_fetch_cert.return_value = ('cert', 'key', 'consumer-uuid')

        # Parse cert returns healthy cert
        mock_parse_cert.return_value = {'serial': '123', 'cn': 'test', 'not_after': '2027-01-01', 'days_remaining': 200}

        # Renewal not needed
        mock_needs_renewal.return_value = False

        # Mock successful check-in
        mock_client = mock.Mock()
        mock_client.checkin.return_value = True
        mock_client_class.return_value = mock_client

        out = StringIO()
        call_command('candlepin_cert', 'renew', stdout=out, stderr=StringIO())

        output = out.getvalue()
        assert 'Check-in successful' in output
        assert 'No renewal needed' in output

        mock_client.checkin.assert_called_once()
        mock_client.regenerate_cert.assert_not_called()

    @mock.patch('awx.main.management.commands.candlepin_cert._save_candlepin_cert_to_db')
    @mock.patch('awx.main.management.commands.candlepin_cert.CandlepinClient')
    @mock.patch('awx.main.management.commands.candlepin_cert.parse_cert')
    @mock.patch('awx.main.management.commands.candlepin_cert.needs_renewal')
    @mock.patch('awx.main.management.commands.candlepin_cert._fetch_candlepin_cert_from_db')
    @override_settings(
        AWX_ANALYTICS_CANDLEPIN_URL='https://test.example.com',
        AWX_ANALYTICS_CANDLEPIN_CA=None,
        AWX_ANALYTICS_CANDLEPIN_PROXY_URL=None,
        AWX_ANALYTICS_CANDLEPIN_RENEWAL_THRESHOLD_DAYS=90,
    )
    def test_renew_with_force_flag(self, mock_fetch_cert, mock_needs_renewal, mock_parse_cert, mock_client_class, mock_save_cert):
        """Test renew --force renews even when not needed."""
        mock_fetch_cert.return_value = ('cert', 'key', 'consumer-uuid')

        # Parse cert
        mock_parse_cert.side_effect = [
            {'serial': '123', 'cn': 'test', 'not_after': '2027-01-01', 'days_remaining': 200},  # Current cert (healthy)
            {'serial': '456', 'cn': 'test', 'not_after': '2027-06-01', 'days_remaining': 365},  # New cert
        ]

        # Would not need renewal without --force
        mock_needs_renewal.return_value = False

        # Mock successful operations
        mock_client = mock.Mock()
        mock_client.checkin.return_value = True
        mock_client.regenerate_cert.return_value = ('new-cert', 'new-key')
        mock_client_class.return_value = mock_client

        mock_save_cert.return_value = True

        out = StringIO()
        call_command('candlepin_cert', 'renew', '--force', stdout=out, stderr=StringIO())

        output = out.getvalue()
        assert 'forced via --force' in output
        assert 'Certificate renewed successfully' in output

        mock_client.regenerate_cert.assert_called_once()

    @mock.patch('awx.main.management.commands.candlepin_cert.CandlepinClient')
    @mock.patch('awx.main.management.commands.candlepin_cert.parse_cert')
    @mock.patch('awx.main.management.commands.candlepin_cert.needs_renewal')
    @mock.patch('awx.main.management.commands.candlepin_cert._fetch_candlepin_cert_from_db')
    @override_settings(
        AWX_ANALYTICS_CANDLEPIN_URL='https://test.example.com',
        AWX_ANALYTICS_CANDLEPIN_CA=None,
        AWX_ANALYTICS_CANDLEPIN_PROXY_URL=None,
        AWX_ANALYTICS_CANDLEPIN_RENEWAL_THRESHOLD_DAYS=90,
    )
    def test_renew_checkin_failure(self, mock_fetch_cert, mock_needs_renewal, mock_parse_cert, mock_client_class):
        """Test renew handles check-in failure gracefully."""
        mock_fetch_cert.return_value = ('cert', 'key', 'consumer-uuid')

        mock_parse_cert.return_value = {'serial': '123', 'cn': 'test', 'not_after': '2027-01-01', 'days_remaining': 100}
        mock_needs_renewal.return_value = False  # Not needed for renewal, just testing check-in failure

        # Mock failed check-in
        mock_client = mock.Mock()
        mock_client.checkin.return_value = False
        mock_client_class.return_value = mock_client

        err = StringIO()
        with pytest.raises(SystemExit) as exc_info:
            call_command('candlepin_cert', 'renew', stderr=err)

        assert exc_info.value.code == 1
        error_output = err.getvalue()
        assert 'Check-in with Candlepin failed' in error_output

    @mock.patch('awx.main.management.commands.candlepin_cert.CandlepinClient')
    @mock.patch('awx.main.management.commands.candlepin_cert.parse_cert')
    @mock.patch('awx.main.management.commands.candlepin_cert.needs_renewal')
    @mock.patch('awx.main.management.commands.candlepin_cert._fetch_candlepin_cert_from_db')
    @override_settings(
        AWX_ANALYTICS_CANDLEPIN_URL='https://test.example.com',
        AWX_ANALYTICS_CANDLEPIN_CA=None,
        AWX_ANALYTICS_CANDLEPIN_PROXY_URL=None,
        AWX_ANALYTICS_CANDLEPIN_RENEWAL_THRESHOLD_DAYS=90,
    )
    def test_renew_regenerate_cert_failure(self, mock_fetch_cert, mock_needs_renewal, mock_parse_cert, mock_client_class):
        """Test renew handles certificate regeneration failure."""
        mock_fetch_cert.return_value = ('cert', 'key', 'consumer-uuid')

        mock_parse_cert.return_value = {'serial': '123', 'cn': 'test', 'not_after': '2026-06-01', 'days_remaining': 10}
        mock_needs_renewal.return_value = True

        # Mock successful check-in but failed regeneration
        mock_client = mock.Mock()
        mock_client.checkin.return_value = True
        mock_client.regenerate_cert.side_effect = Exception('Certificate regeneration failed')
        mock_client_class.return_value = mock_client

        err = StringIO()
        with pytest.raises(SystemExit) as exc_info:
            call_command('candlepin_cert', 'renew', stderr=err)

        assert exc_info.value.code == 1
        error_output = err.getvalue()
        assert 'Certificate renewal failed' in error_output
