import pytest
from requests.exceptions import ConnectionError
import sys
from unittest.mock import patch

from awxkit.cli import run, CLI


class MockedCLI(CLI):
    def fetch_version_root(self):
        pass

    @property
    def v2(self):
        return MockedCLI()

    @property
    def json(self):
        return {'users': None}


@pytest.mark.parametrize('help_param', ['-h', '--help'])
def test_help(capfd, help_param):
    with pytest.raises(SystemExit):
        run(['awx {}'.format(help_param)])
    out, err = capfd.readouterr()

    assert "usage:" in out
    for snippet in ('--conf.host https://example.awx.org]', '-v, --verbose'):
        assert snippet in out


def test_connection_error(capfd):
    cli = CLI()
    cli.parse_args(['awx'])
    with pytest.raises(ConnectionError):
        cli.connect()


@pytest.mark.parametrize('resource', ['', 'invalid'])
def test_list_resources(capfd, resource):
    # if a valid resource isn't specified, print --help
    cli = MockedCLI()
    cli.parse_args(['awx {}'.format(resource)])
    cli.connect()

    try:
        cli.parse_resource()
        out, err = capfd.readouterr()
    except SystemExit:
        # python2 argparse raises SystemExit for invalid/missing required args,
        # py3 doesn't
        _, out = capfd.readouterr()

    assert "usage:" in out
    for snippet in ('--conf.host https://example.awx.org]', '-v, --verbose'):
        assert snippet in out


class TestHelpHandling:
    """Test suite for improved help handling functionality"""

    def test_get_non_option_args_basic(self):
        """Test _get_non_option_args extracts non-option arguments correctly"""
        cli = CLI()
        cli.argv = ['awx', 'users', 'list', '--verbose']

        result = cli._get_non_option_args()
        assert result == ['users', 'list']

    def test_get_non_option_args_with_flags(self):
        """Test _get_non_option_args ignores option flags"""
        cli = CLI()
        cli.argv = ['awx', '--conf.host', 'example.com', 'jobs', 'create', '--name', 'test']

        result = cli._get_non_option_args()
        # Should include all non-option arguments (including flag values) except 'awx'
        assert result == ['example.com', 'jobs', 'create', 'test']

    def test_get_non_option_args_before_help(self):
        """Test _get_non_option_args with before_help=True stops at help flag"""
        cli = CLI()
        cli.argv = ['awx', 'users', '--help', 'extra', 'args']

        result = cli._get_non_option_args(before_help=True)
        assert result == ['users']

    def test_get_non_option_args_before_help_short_flag(self):
        """Test _get_non_option_args with before_help=True stops at -h flag"""
        cli = CLI()
        cli.argv = ['awx', 'projects', '-h', 'should', 'not', 'appear']

        result = cli._get_non_option_args(before_help=True)
        assert result == ['projects']

    def test_get_non_option_args_no_help_flag(self):
        """Test _get_non_option_args when help flag not present"""
        cli = CLI()
        cli.argv = ['awx', 'organizations', 'list']

        result = cli._get_non_option_args(before_help=True)
        assert result == ['organizations', 'list']

    def test_is_main_help_request_true(self):
        """Test _is_main_help_request returns True for main CLI help"""
        cli = CLI()
        cli.argv = ['awx', '--help']

        result = cli._is_main_help_request()
        assert result is True

    def test_is_main_help_request_short_flag(self):
        """Test _is_main_help_request returns True for main CLI help with -h"""
        cli = CLI()
        cli.argv = ['awx', '-h']

        result = cli._is_main_help_request()
        assert result is True

    def test_is_main_help_request_false_subcommand(self):
        """Test _is_main_help_request returns False for subcommand help"""
        cli = CLI()
        cli.argv = ['awx', 'users', '--help']

        result = cli._is_main_help_request()
        assert result is False

    def test_is_main_help_request_false_action(self):
        """Test _is_main_help_request returns False for action help"""
        cli = CLI()
        cli.argv = ['awx', 'jobs', 'create', '--help']

        result = cli._is_main_help_request()
        assert result is False

    def test_is_main_help_request_false_no_help(self):
        """Test _is_main_help_request returns False when no help flag"""
        cli = CLI()
        cli.argv = ['awx', 'users', 'list']

        result = cli._is_main_help_request()
        assert result is False

    def test_early_help_return_main_cli(self):
        """Test that main CLI help exits early without server connection"""
        cli = CLI()
        # Verify that _is_main_help_request works correctly
        cli.argv = ['awx', '--help']
        assert cli._is_main_help_request() is True

        # Test that parse_args with main help flag should exit
        with patch.object(sys, 'exit') as mock_exit:
            cli.parse_args(['awx', '--help'])
            mock_exit.assert_called_once_with(0)

    def test_no_early_exit_for_subcommand_help(self):
        """Test that subcommand help does not exit early"""
        with patch.object(sys, 'exit') as mock_exit:
            cli = CLI()
            # This should not exit early since it's subcommand help
            cli.parse_args(['awx', 'users', '--help'])

            mock_exit.assert_not_called()

    def test_help_property_detection(self):
        """Test that help property correctly detects help flags"""
        cli = CLI()

        cli.argv = ['awx', '--help']
        assert cli.help is True

        cli.argv = ['awx', '-h']
        assert cli.help is True

        cli.argv = ['awx', 'users', '--help']
        assert cli.help is True

        cli.argv = ['awx', 'users', 'list']
        assert cli.help is False

    def test_short_help_flag_added(self):
        """Test that -h flag is properly added to argument parser"""
        cli = CLI()
        cli.parse_args(['awx'])

        # Verify that both -h and --help are recognized
        help_actions = [action for action in cli.parser._actions if '--help' in action.option_strings]
        assert len(help_actions) == 1
        assert '-h' in help_actions[0].option_strings
        assert '--help' in help_actions[0].option_strings
