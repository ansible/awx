import os
import shutil
import sys
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import ansible_runner

from awx.main.isolated.manager import set_pythonpath


class Command(BaseCommand):
    """Tests SSH connectivity between a controller and target isolated node"""
    help = 'Tests SSH connectivity between a controller and target isolated node'

    def add_arguments(self, parser):
        parser.add_argument('--hostname', dest='hostname', type=str,
                            help='Hostname of an isolated node')

    def handle(self, *args, **options):
        hostname = options.get('hostname')
        if not hostname:
            raise CommandError("--hostname is a required argument")

        try:
            path = tempfile.mkdtemp(prefix='awx_isolated_ssh', dir=settings.AWX_PROOT_BASE_PATH)
            ssh_key = None
            if all([
                getattr(settings, 'AWX_ISOLATED_KEY_GENERATION', False) is True,
                getattr(settings, 'AWX_ISOLATED_PRIVATE_KEY', None)
            ]):
                ssh_key = settings.AWX_ISOLATED_PRIVATE_KEY
            env = dict(os.environ.items())
            env['ANSIBLE_HOST_KEY_CHECKING'] = str(settings.AWX_ISOLATED_HOST_KEY_CHECKING)
            set_pythonpath(os.path.join(settings.ANSIBLE_VENV_PATH, 'lib'), env)
            res = ansible_runner.interface.run(
                private_data_dir=path,
                host_pattern='all',
                inventory='{} ansible_ssh_user={}'.format(hostname, settings.AWX_ISOLATED_USERNAME),
                module='shell',
                module_args='ansible-runner --version',
                envvars=env,
                verbosity=3,
                ssh_key=ssh_key,
            )
            sys.exit(res.rc)
        finally:
            shutil.rmtree(path)
