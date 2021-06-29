import pytest
from requests.exceptions import ConnectionError

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
