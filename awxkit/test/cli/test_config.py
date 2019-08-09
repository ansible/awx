import pytest
from requests.exceptions import ConnectionError

from awxkit.cli import CLI
from awxkit import config

def test_host_from_environment():
    cli = CLI()
    cli.parse_args(
        ['awx'],
        env={'TOWER_HOST': 'https://xyz.local'}
    )
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
    cli.parse_args(
        ['awx'],
        env={
            'TOWER_USERNAME': 'mary',
            'TOWER_PASSWORD': 'secret'
        }
    )
    with pytest.raises(ConnectionError):
        cli.connect()

    assert config.credentials.default.username == 'mary'
    assert config.credentials.default.password == 'secret'

def test_username_and_password_argv():
    cli = CLI()
    cli.parse_args([
        'awx', '--conf.username', 'mary', '--conf.password', 'secret'
    ])
    with pytest.raises(ConnectionError):
        cli.connect()

    assert config.credentials.default.username == 'mary'
    assert config.credentials.default.password == 'secret'

def test_config_precedence():
    cli = CLI()
    cli.parse_args(
        [
            'awx', '--conf.username', 'mary', '--conf.password', 'secret'
        ],
        env={
            'TOWER_USERNAME': 'IGNORE',
            'TOWER_PASSWORD': 'IGNORE'
        }
    )
    with pytest.raises(ConnectionError):
        cli.connect()

    assert config.credentials.default.username == 'mary'
    assert config.credentials.default.password == 'secret'
