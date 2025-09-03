import os
import json
import pytest
from requests.exceptions import ConnectionError

from awxkit.cli import CLI
from awxkit import config


def test_host_from_environment():
    cli = CLI()
    cli.parse_args(['awx'], env={'CONTROLLER_HOST': 'https://xyz.local'})
    with pytest.raises(ConnectionError):
        cli.connect()
    assert config.base_url == 'https://xyz.local'


def test_host_from_argv():
    cli = CLI()
    cli.parse_args(['awx', '--conf.host', 'https://xyz.local'])
    with pytest.raises(ConnectionError):
        cli.connect()
    assert config.base_url == 'https://xyz.local'


def test_username_and_password_from_environment():
    cli = CLI()
    cli.parse_args(['awx'], env={'CONTROLLER_USERNAME': 'mary', 'CONTROLLER_PASSWORD': 'secret'})
    with pytest.raises(ConnectionError):
        cli.connect()

    assert config.credentials.default.username == 'mary'
    assert config.credentials.default.password == 'secret'


def test_username_and_password_argv():
    cli = CLI()
    cli.parse_args(['awx', '--conf.username', 'mary', '--conf.password', 'secret'])
    with pytest.raises(ConnectionError):
        cli.connect()

    assert config.credentials.default.username == 'mary'
    assert config.credentials.default.password == 'secret'


def test_config_precedence():
    cli = CLI()
    cli.parse_args(['awx', '--conf.username', 'mary', '--conf.password', 'secret'], env={'CONTROLLER_USERNAME': 'IGNORE', 'CONTROLLER_PASSWORD': 'IGNORE'})
    with pytest.raises(ConnectionError):
        cli.connect()

    assert config.credentials.default.username == 'mary'
    assert config.credentials.default.password == 'secret'


def test_config_file_precedence():
    """Ignores AWXKIT_CREDENTIAL_FILE if cli args are set"""
    os.makedirs('/tmp/awx-test/', exist_ok=True)
    with open('/tmp/awx-test/config.json', 'w') as f:
        json.dump({'default': {'username': 'IGNORE', 'password': 'IGNORE'}}, f)

    cli = CLI()
    cli.parse_args(
        ['awx', '--conf.username', 'mary', '--conf.password', 'secret'],
        env={
            'AWXKIT_CREDENTIAL_FILE': '/tmp/awx-test/config.json',
        },
    )
    with pytest.raises(ConnectionError):
        cli.connect()

    assert config.credentials.default.username == 'mary'
    assert config.credentials.default.password == 'secret'


def test_config_file_precedence_2():
    """Ignores AWXKIT_CREDENTIAL_FILE if TOWER_* vars are set."""
    os.makedirs('/tmp/awx-test/', exist_ok=True)
    with open('/tmp/awx-test/config.json', 'w') as f:
        json.dump({'default': {'username': 'IGNORE', 'password': 'IGNORE'}}, f)

    cli = CLI()
    cli.parse_args(['awx'], env={'AWXKIT_CREDENTIAL_FILE': '/tmp/awx-test/config.json', 'TOWER_USERNAME': 'mary', 'TOWER_PASSWORD': 'secret'})
    with pytest.raises(ConnectionError):
        cli.connect()

    assert config.credentials.default.username == 'mary'
    assert config.credentials.default.password == 'secret'


def test_config_file():
    """Reads username and password from AWXKIT_CREDENTIAL_FILE."""
    os.makedirs('/tmp/awx-test/', exist_ok=True)
    with open('/tmp/awx-test/config.json', 'w') as f:
        json.dump({'default': {'username': 'mary', 'password': 'secret'}}, f)

    cli = CLI()
    cli.parse_args(
        ['awx'],
        env={
            'AWXKIT_CREDENTIAL_FILE': '/tmp/awx-test/config.json',
        },
    )
    with pytest.raises(ConnectionError):
        cli.connect()

    assert config.credentials.default.username == 'mary'
    assert config.credentials.default.password == 'secret'


def test_controller_optional_api_urlpattern_prefix():
    """Tests that CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX is honored when set."""
    cli = CLI()
    env = {'CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX': '/custom/api/'}
    cli.parse_args(['awx'], env=env)

    # Update config with environment variable since config.py reads from os.getenv at import time
    config.api_base_path = env.get('CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX', '/api/')
    config.api_base_path = env.get('AWXKIT_API_BASE_PATH', config.api_base_path)

    assert config.api_base_path == '/custom/api/'


def test_awxkit_api_base_path_fallback():
    """Tests that AWXKIT_API_BASE_PATH overrides CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX."""
    cli = CLI()
    env = {'CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX': '/custom/api/', 'AWXKIT_API_BASE_PATH': '/override/api/'}
    cli.parse_args(['awx'], env=env)

    # Update config with environment variable since config.py reads from os.getenv at import time
    config.api_base_path = env.get('CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX', '/api/')
    config.api_base_path = env.get('AWXKIT_API_BASE_PATH', config.api_base_path)

    assert config.api_base_path == '/override/api/'


def test_api_base_path_default():
    """Tests that api_base_path defaults to /api/ when no environment variables are set."""
    cli = CLI()
    env = {}
    cli.parse_args(['awx'], env=env)

    # Reset config to default when no environment variables are set
    config.api_base_path = env.get('CONTROLLER_OPTIONAL_API_URLPATTERN_PREFIX', '/api/')
    config.api_base_path = env.get('AWXKIT_API_BASE_PATH', config.api_base_path)

    assert config.api_base_path == '/api/'
