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
    """Set up CLI with mocked connection for OAuth2 token auth testing"""
    cli = CLI()
    cli.parse_args(cli_args or ['awx', '--conf.token', 'my_oauth_token'])

    mock_root = Mock()
    mock_connection = Mock()
    mock_connection.session.headers = {}
    mock_root.connection = mock_connection
    mock_root.load_session.return_value = mock_root
    cli.root = mock_root

    return cli, mock_root, mock_connection


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


def test_oauth_token_auth():
    """Test that providing an OAuth2 token sets the Bearer header"""
    cli, mock_root, mock_connection = setup_token_auth()
    cli.authenticate()

    assert mock_connection.session.headers['Authorization'] == 'Bearer my_oauth_token'
    mock_connection.login.assert_not_called()
    mock_root.load_session.assert_not_called()


def test_oauth_token_from_cli_flag():
    """Test that --conf.token CLI flag sets Bearer auth"""
    cli, mock_root, mock_connection = setup_token_auth(['awx', '--conf.token', 'cli_token_value'])
    cli.authenticate()

    assert mock_connection.session.headers['Authorization'] == 'Bearer cli_token_value'
    mock_connection.login.assert_not_called()


def test_oauth_token_from_env_var():
    """Test that CONTROLLER_OAUTH_TOKEN env var sets Bearer auth"""
    cli = CLI()
    cli.parse_args(['awx'], env={'CONTROLLER_OAUTH_TOKEN': 'env_token_value'})

    mock_root = Mock()
    mock_connection = Mock()
    mock_connection.session.headers = {}
    mock_root.connection = mock_connection
    cli.root = mock_root

    cli.authenticate()

    assert mock_connection.session.headers['Authorization'] == 'Bearer env_token_value'
    mock_connection.login.assert_not_called()


def test_oauth_token_precedence_over_basic_auth(monkeypatch):
    """Test that OAuth2 token takes precedence over Basic auth"""
    cli, mock_root, mock_connection = setup_token_auth(['awx', '--conf.token', 'my_token', '--conf.username', 'user', '--conf.password', 'pass'])
    monkeypatch.setattr(config, 'force_basic_auth', True)
    cli.authenticate()

    assert mock_connection.session.headers['Authorization'] == 'Bearer my_token'
    mock_connection.login.assert_not_called()


def test_empty_token_falls_through_to_session_auth():
    """Test that an empty token falls through to session-based auth"""
    cli = CLI()
    cli.parse_args(['awx', '--conf.token', '', '--conf.username', 'testuser', '--conf.password', 'testpass'])

    mock_root = Mock()
    mock_load_session = Mock()
    mock_root.load_session.return_value = mock_load_session
    cli.root = mock_root

    cli.authenticate()

    mock_root.load_session.assert_called_once()
    mock_load_session.get.assert_called_once()
