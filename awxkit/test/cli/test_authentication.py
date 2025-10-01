import os
import pytest
from unittest.mock import Mock, patch

from awxkit.cli import CLI
from awxkit import config


# ============================================================================
# AAP-46830: Authentication Tests for Basic Auth Environment Variable Support
# ============================================================================


def test_authenticate_with_force_basic_auth_enabled():
    """Test that AWXKIT_FORCE_BASIC_AUTH=true forces basic authentication"""
    cli = CLI()
    cli.parse_args(['awx', '--conf.username', 'testuser', '--conf.password', 'testpass'])

    # Mock the root object and connection
    mock_root = Mock()
    mock_connection = Mock()
    mock_root.connection = mock_connection
    cli.root = mock_root

    # Store original value and set force_basic_auth to True
    original_value = getattr(config, 'force_basic_auth', False)
    try:
        config.force_basic_auth = True
        cli.authenticate()

        # Verify basic auth was used
        mock_connection.login.assert_called_once_with('testuser', 'testpass')
        mock_root.get.assert_called_once()
        assert not config.use_sessions
    finally:
        # Restore original value
        config.force_basic_auth = original_value


def test_authenticate_with_force_basic_auth_disabled():
    """Test that session auth is used when AWXKIT_FORCE_BASIC_AUTH is false/unset"""
    cli = CLI()
    cli.parse_args(['awx', '--conf.username', 'testuser', '--conf.password', 'testpass'])

    # Mock the root object
    mock_root = Mock()
    mock_load_session = Mock()
    mock_root.load_session.return_value = mock_load_session
    cli.root = mock_root

    # Store original value and set force_basic_auth to False
    original_value = getattr(config, 'force_basic_auth', False)
    try:
        config.force_basic_auth = False
        cli.authenticate()

        # Verify session auth was used
        mock_root.load_session.assert_called_once()
        mock_load_session.get.assert_called_once()
        assert config.use_sessions
    finally:
        # Restore original value
        config.force_basic_auth = original_value


def test_authenticate_basic_auth_without_credentials():
    """Test basic auth behavior when credentials are missing - uses defaults"""
    cli = CLI()
    cli.parse_args(['awx'])  # No credentials provided - will use defaults

    # Mock the root object and connection
    mock_root = Mock()
    mock_connection = Mock()
    mock_root.connection = mock_connection
    cli.root = mock_root

    # Store original value and set force_basic_auth to True
    original_value = getattr(config, 'force_basic_auth', False)
    try:
        config.force_basic_auth = True
        cli.authenticate()

        # Should call login with default credentials (admin/password)
        mock_connection.login.assert_called_once_with('admin', 'password')
        mock_root.get.assert_called_once()
        assert not config.use_sessions
    finally:
        # Restore original value
        config.force_basic_auth = original_value


def test_authenticate_basic_auth_partial_credentials():
    """Test basic auth with only username - password falls back to default"""
    cli = CLI()
    cli.parse_args(['awx', '--conf.username', 'testuser'])  # Only username, password uses default

    mock_root = Mock()
    mock_connection = Mock()
    mock_root.connection = mock_connection
    cli.root = mock_root

    # Store original value and set force_basic_auth to True
    original_value = getattr(config, 'force_basic_auth', False)
    try:
        config.force_basic_auth = True
        cli.authenticate()

        # Should call login with provided username and default password
        mock_connection.login.assert_called_once_with('testuser', 'password')
        mock_root.get.assert_called_once()
        assert not config.use_sessions
    finally:
        # Restore original value
        config.force_basic_auth = original_value


def test_authenticate_basic_auth_empty_credentials():
    """Test basic auth with empty string credentials - should raise ValueError"""
    cli = CLI()
    cli.parse_args(['awx', '--conf.username', '', '--conf.password', ''])

    mock_root = Mock()
    mock_connection = Mock()
    mock_root.connection = mock_connection
    cli.root = mock_root

    # Store original value and set force_basic_auth to True
    original_value = getattr(config, 'force_basic_auth', False)
    try:
        config.force_basic_auth = True

        # Should raise ValueError for empty credentials
        with pytest.raises(ValueError, match="Basic authentication requires both username and password"):
            cli.authenticate()

        # Should not call login with empty credentials
        mock_connection.login.assert_not_called()
    finally:
        # Restore original value
        config.force_basic_auth = original_value


def test_force_basic_auth_environment_variable_loading():
    """Test that AWXKIT_FORCE_BASIC_AUTH environment variable is properly loaded"""
    # Store original value
    original_value = getattr(config, 'force_basic_auth', False)

    try:
        # Test true values by setting environment and checking config
        with patch.dict(os.environ, {'AWXKIT_FORCE_BASIC_AUTH': 'true'}):
            # Simulate config reload by manually setting the value
            from awxkit.utils import to_bool

            config.force_basic_auth = to_bool(os.environ.get('AWXKIT_FORCE_BASIC_AUTH', False))
            assert config.force_basic_auth is True

        with patch.dict(os.environ, {'AWXKIT_FORCE_BASIC_AUTH': '1'}):
            config.force_basic_auth = to_bool(os.environ.get('AWXKIT_FORCE_BASIC_AUTH', False))
            assert config.force_basic_auth is True

        with patch.dict(os.environ, {'AWXKIT_FORCE_BASIC_AUTH': 'false'}):
            config.force_basic_auth = to_bool(os.environ.get('AWXKIT_FORCE_BASIC_AUTH', False))
            assert config.force_basic_auth is False

        with patch.dict(os.environ, {'AWXKIT_FORCE_BASIC_AUTH': '0'}):
            config.force_basic_auth = to_bool(os.environ.get('AWXKIT_FORCE_BASIC_AUTH', False))
            assert config.force_basic_auth is False

        # Test default (unset)
        with patch.dict(os.environ, {}, clear=True):
            config.force_basic_auth = to_bool(os.environ.get('AWXKIT_FORCE_BASIC_AUTH', False))
            assert config.force_basic_auth is False
    finally:
        # Restore original value
        config.force_basic_auth = original_value


def test_aap_gateway_authentication_scenario_integration():
    """Integration test for the specific AAP Gateway scenario from AAP-46830"""
    cli = CLI()
    cli.parse_args([
        'awx',
        '--conf.host', 'https://aap-sbx.cambiahealth.com',
        '--conf.username', 'puretest',
        '--conf.password', 'testpass',
        'projects', 'list'
    ])

    # Mock successful basic auth
    mock_root = Mock()
    mock_connection = Mock()
    mock_root.connection = mock_connection
    cli.root = mock_root

    # Store original value and set force_basic_auth to True
    original_value = getattr(config, 'force_basic_auth', False)
    try:
        config.force_basic_auth = True
        cli.authenticate()

        # Verify the fix works for AAP Gateway scenario
        mock_connection.login.assert_called_once_with('puretest', 'testpass')
        mock_root.get.assert_called_once()
        assert not config.use_sessions
    finally:
        # Restore original value
        config.force_basic_auth = original_value


def test_config_get_method_compatibility():
    """Test that config.get() method works correctly for force_basic_auth"""
    # Store original value
    original_value = getattr(config, 'force_basic_auth', None)

    try:
        # Test when force_basic_auth is set
        config.force_basic_auth = True
        assert config.get('force_basic_auth', False) is True

        # Test when force_basic_auth is unset/False
        config.force_basic_auth = False
        assert config.get('force_basic_auth', False) is False

        # Test default fallback
        if hasattr(config, 'force_basic_auth'):
            delattr(config, 'force_basic_auth')
        assert config.get('force_basic_auth', False) is False
    finally:
        # Restore original value
        if original_value is not None:
            config.force_basic_auth = original_value


def test_authenticate_method_docstring_and_behavior():
    """Test that authenticate method has proper docstring and behavior"""
    cli = CLI()

    # Check docstring is updated
    assert 'Configure the current session for authentication' in cli.authenticate.__doc__

    # Verify method exists and is callable
    assert callable(cli.authenticate)


def test_authenticate_config_use_sessions_state():
    """Test that config.use_sessions is properly set in both auth paths"""
    cli = CLI()
    cli.parse_args(['awx', '--conf.username', 'testuser', '--conf.password', 'testpass'])

    mock_root = Mock()
    mock_connection = Mock()
    mock_root.connection = mock_connection
    cli.root = mock_root

    # Store original value
    original_value = getattr(config, 'force_basic_auth', False)
    original_use_sessions = getattr(config, 'use_sessions', False)

    try:
        # Test basic auth path sets use_sessions to False
        config.force_basic_auth = True
        cli.authenticate()
        assert not config.use_sessions

        # Reset for session auth test
        mock_load_session = Mock()
        mock_root.load_session.return_value = mock_load_session

        # Test session auth path sets use_sessions to True
        config.force_basic_auth = False
        cli.authenticate()
        assert config.use_sessions
    finally:
        # Restore original values
        config.force_basic_auth = original_value
        config.use_sessions = original_use_sessions


def test_authenticate_early_return_behavior():
    """Test that basic auth path returns early and doesn't execute session auth"""
    cli = CLI()
    cli.parse_args(['awx', '--conf.username', 'testuser', '--conf.password', 'testpass'])

    mock_root = Mock()
    mock_connection = Mock()
    mock_root.connection = mock_connection
    cli.root = mock_root

    # Mock load_session to ensure it's not called in basic auth path
    mock_load_session = Mock()
    mock_root.load_session = mock_load_session

    # Store original value and set force_basic_auth to True
    original_value = getattr(config, 'force_basic_auth', False)
    try:
        config.force_basic_auth = True
        cli.authenticate()

        # Verify session auth methods are not called when basic auth is used
        mock_load_session.assert_not_called()
    finally:
        # Restore original value
        config.force_basic_auth = original_value


def test_authenticate_username_password_retrieval():
    """Test that username and password are correctly retrieved from config"""
    cli = CLI()

    # Test with both username and password
    cli.parse_args(['awx', '--conf.username', 'myuser', '--conf.password', 'mypass'])
    assert cli.get_config('username') == 'myuser'
    assert cli.get_config('password') == 'mypass'

    # Test with missing password - falls back to default
    cli.parse_args(['awx', '--conf.username', 'myuser'])
    assert cli.get_config('username') == 'myuser'
    assert cli.get_config('password') == 'password'  # Default password

    # Test with missing username - falls back to default
    cli.parse_args(['awx', '--conf.password', 'mypass'])
    assert cli.get_config('username') == 'admin'  # Default username
    assert cli.get_config('password') == 'mypass'


def test_authenticate_basic_auth_connection_failure():
    """Test basic auth behavior when connection.login() fails"""
    cli = CLI()
    cli.parse_args(['awx', '--conf.username', 'testuser', '--conf.password', 'testpass'])

    mock_root = Mock()
    mock_connection = Mock()
    mock_root.connection = mock_connection
    cli.root = mock_root

    # Mock connection.login to raise an exception
    mock_connection.login.side_effect = Exception("Connection failed")

    # Store original value and set force_basic_auth to True
    original_value = getattr(config, 'force_basic_auth', False)
    try:
        config.force_basic_auth = True

        with pytest.raises(RuntimeError, match="Basic authentication failed: Connection failed"):
            cli.authenticate()

        # Verify login was attempted
        mock_connection.login.assert_called_once_with('testuser', 'testpass')
        assert not config.use_sessions
    finally:
        # Restore original value
        config.force_basic_auth = original_value


def test_authenticate_basic_auth_root_get_failure():
    """Test basic auth behavior when root.get() fails"""
    cli = CLI()
    cli.parse_args(['awx', '--conf.username', 'testuser', '--conf.password', 'testpass'])

    mock_root = Mock()
    mock_connection = Mock()
    mock_root.connection = mock_connection
    cli.root = mock_root

    # Mock root.get to raise an exception
    mock_root.get.side_effect = Exception("API call failed")

    # Store original value and set force_basic_auth to True
    original_value = getattr(config, 'force_basic_auth', False)
    try:
        config.force_basic_auth = True

        with pytest.raises(RuntimeError, match="Basic authentication failed: API call failed"):
            cli.authenticate()

        # Verify both login and get were attempted
        mock_connection.login.assert_called_once_with('testuser', 'testpass')
        mock_root.get.assert_called_once()
        assert not config.use_sessions
    finally:
        # Restore original value
        config.force_basic_auth = original_value
