import os
import shutil
import subprocess
import sys
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from awx.main.expect import run


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
            args = [
                'ansible', 'all', '-i', '{},'.format(hostname), '-u',
                settings.AWX_ISOLATED_USERNAME, '-T5', '-m', 'shell',
                '-a', 'ansible-runner --version', '-vvv'
            ]
            if all([
                getattr(settings, 'AWX_ISOLATED_KEY_GENERATION', False) is True,
                getattr(settings, 'AWX_ISOLATED_PRIVATE_KEY', None)
            ]):
                ssh_key_path = os.path.join(path, '.isolated')
                ssh_auth_sock = os.path.join(path, 'ssh_auth.sock')
                run.open_fifo_write(ssh_key_path, settings.AWX_ISOLATED_PRIVATE_KEY)
                args = run.wrap_args_with_ssh_agent(args, ssh_key_path, ssh_auth_sock)
            try:
                print(' '.join(args))
                subprocess.check_call(args)
            except subprocess.CalledProcessError as e:
                sys.exit(e.returncode)
        finally:
            shutil.rmtree(path)
