import pytest
import subprocess

from awx.main.utils import get_ansible_version

def test_dev(mocker, settings):
    settings.ANSIBLE_VERSION = mocker.Mock()

    res = get_ansible_version()

    assert res == settings.ANSIBLE_VERSION

def test_production(mocker, settings):
    mock_Popen = mocker.MagicMock()
    mocker.patch.object(subprocess, 'Popen', mock_Popen)
    del settings.ANSIBLE_VERSION

    get_ansible_version()

    mock_Popen.assert_called_with(['ansible', '--version'], stdout=subprocess.PIPE)
