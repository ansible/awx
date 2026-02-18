import pytest
from typing import Tuple, List, Optional
from unittest.mock import Mock

from awxkit.cli import CLI
from awxkit import config


@pytest.fixture(autouse=True)
def reset_config_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure clean config state for each test to prevent parallel test interference"""
    monkeypatch.setattr(config, 'force_basic_auth', False, raising=False)
    monkeypatch.setattr(config, 'use_sessions', False, raising=False)


# ============================================================================
# Test Helper Functions
# ============================================================================


def setup_basic_auth(cli_args: Optional[List[str]] = None) -> Tuple[CLI, Mock, Mock]:
    """Set up CLI with mocked connection for Basic auth testing"""
    cli = CLI()
    cli.parse_args(cli_args or ['awx', '--conf.username', 'testuser', '--conf.password', 'testpass'])

    mock_root = Mock()
    mock_connection = Mock()
    mock_root.connection = mock_connection
    cli.root = mock_root

    return cli, mock_root, mock_connection


def setup_session_auth(cli_args: Optional[List[str]] = None) -> Tuple[CLI, Mock, Mock]:
    """Set up CLI with mocked session for Session auth testing"""
    cli = CLI()
    cli.parse_args(cli_args or ['awx', '--conf.username', 'testuser', '--conf.password', 'testpass'])

    mock_root = Mock()
    mock_load_session = Mock()
    mock_root.load_session.return_value = mock_load_session
    cli.root = mock_root

    return cli, mock_root, mock_load_session


def setup_token_auth(cli_args: Optional[List[str]] = None) -> Tuple[CLI, Mock, Mock]:
    """Set up CLI with mocked connection for Token auth testing"""
    cli = CLI()
    cli.parse_args(cli_args or ['awx', '--conf.token', 'test-token-abc123'])

    mock_root = Mock()
    mock_connection = Mock()
    mock_root.connection = mock_connection
    cli.root = mock_root

    return cli, mock_root, mock_connection


def test_token_auth_preserved(monkeypatch):
    """
    REGRESSION TEST: Token authentication must still work (existed in 4.6.12)

    This test documents the customer's working scenario from 4.6.12:
        awx login --conf.host URL --conf.username USER --conf.password PASS
        # Returns: {"token": "E*******J"}

        awx --conf.host URL --conf.token E*******J job_templates launch ...
        # This WORKED in 4.6.12

    BREAKING CHANGE: Version 4.6.21 removed token authentication entirely,
    causing customer to report: "neither token no username/password are working"

    This test will FAIL with current code and PASS once fixed.
    """
    cli, mock_root, mock_connection = setup_token_auth(['awx', '--conf.host', 'https://aap-sbx.testbank.com', '--conf.token', 'E1234567890J'])
    monkeypatch.setattr(config, 'force_basic_auth', False)

    # Execute authentication
    cli.authenticate()

    # Token auth should call login with token parameter
    mock_connection.login.assert_called_once_with(None, None, token='E1234567890J')

    # Should NOT use sessions when token is provided
    assert not config.use_sessions


def test_basic_auth_enabled(monkeypatch):
    """Test that AWXKIT_FORCE_BASIC_AUTH=true enables Basic authentication"""
    cli, mock_root, mock_connection = setup_basic_auth()
    monkeypatch.setattr(config, 'force_basic_auth', True)
    cli.authenticate()

    mock_connection.login.assert_called_once_with('testuser', 'testpass')
    mock_root.get.assert_called_once()
    assert not config.use_sessions


def test_session_auth_default(monkeypatch):
    """Test that session auth is used by default (backward compatibility)"""
    cli, mock_root, mock_load_session = setup_session_auth()
    monkeypatch.setattr(config, 'force_basic_auth', False)
    cli.authenticate()

    mock_root.load_session.assert_called_once()
    mock_load_session.get.assert_called_once()
    assert config.use_sessions


def test_aap_gateway_scenario(monkeypatch):
    """Test the specific AAP Gateway scenario from AAP-46830"""
    cli, mock_root, mock_connection = setup_basic_auth(
        ['awx', '--conf.host', 'https://aap-sbx.cambiahealth.com', '--conf.username', 'puretest', '--conf.password', 'testpass']
    )
    monkeypatch.setattr(config, 'force_basic_auth', True)
    cli.authenticate()

    mock_connection.login.assert_called_once_with('puretest', 'testpass')
    mock_root.get.assert_called_once()
    assert not config.use_sessions


def test_empty_credentials_error(monkeypatch):
    """Test error handling for explicitly empty credentials"""
    cli, mock_root, mock_connection = setup_basic_auth(['awx', '--conf.username', '', '--conf.password', ''])
    monkeypatch.setattr(config, 'force_basic_auth', True)

    with pytest.raises(ValueError, match="Basic authentication requires both username and password"):
        cli.authenticate()

    mock_connection.login.assert_not_called()


def test_connection_failure(monkeypatch):
    """Test error handling when Basic auth connection fails"""
    cli, mock_root, mock_connection = setup_basic_auth()
    mock_connection.login.side_effect = Exception("Connection failed")
    monkeypatch.setattr(config, 'force_basic_auth', True)

    with pytest.raises(RuntimeError, match="Basic authentication failed: Connection failed"):
        cli.authenticate()

    mock_connection.login.assert_called_once_with('testuser', 'testpass')
    assert not config.use_sessions
