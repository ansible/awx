# Copyright (c) 2021 Ansible, Inc.
# All Rights Reserved

from awx.main.utils.common import get_custom_venv_choices, get_custom_venv_pip_freeze
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Returns either a list of custom venv paths or outputs the pip freeze from the path passed in the argument"""

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            dest='path',
            type=str,
            default='',
            help='run without arguments to see a list of paths, run with one of those paths as an argument and see the pip freeze data',
        )

    def handle(self, *args, **options):
        super(Command, self).__init__()
        if options.get('path'):
            pip_data = get_custom_venv_pip_freeze(options.get('path'))
            print(pip_data)
        else:
            venvs = get_custom_venv_choices()
            for venv in venvs:
                print(venv)
