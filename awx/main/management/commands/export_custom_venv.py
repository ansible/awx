# Copyright (c) 2021 Ansible, Inc.
# All Rights Reserved

from awx.main.utils.common import get_custom_venv_pip_freeze
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Returns the pip freeze from the path passed in the argument"""

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            type=str,
            nargs=1,
            default='',
            help='run this with a path to a virtual environment as an argument to see the pip freeze data',
        )
        parser.add_argument('-q', action='store_true', help='run with -q to output only the results of the query.')

    def handle(self, *args, **options):
        super(Command, self).__init__()
        if options.get('path'):
            pip_data = get_custom_venv_pip_freeze(options.get('path')[0])
            if pip_data:
                print('\n', '# {}'.format("Virtual environment contents:"))
                print(pip_data)
                if not options.get('q'):
                    msg = [
                        'To list all (now deprecated) custom virtual environments run:',
                        'awx-manage list_custom_venvs',
                        '',
                        'To view the connections a (deprecated) virtual environment had in the database, run the following command while supplying the path as an argument:',
                        'awx-manage custom_venv_associations /path/to/venv',
                        '',
                    ]
                    print('\n'.join(msg))
