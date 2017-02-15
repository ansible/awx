# from django.conf import LazySettings
import pytest

# awx.main.utils.reload
from awx.main.main.tasks import _supervisor_service_restart, subprocess


def test_produce_supervisor_command(mocker):
    with mocker.patch.object(subprocess, 'Popen'):
        _supervisor_service_restart(['beat', 'callback', 'fact'])
        subprocess.Popen.assert_called_once_with(
            ['supervisorctl', 'restart', 'tower-processes:receiver', 'tower-processes:factcacher'])

