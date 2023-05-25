# Copyright (c) 2021 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand
from awx.main.utils.common import get_custom_venv_choices
from awx.main.models import Organization, InventorySource, JobTemplate, Project
import yaml


class Command(BaseCommand):
    """Returns the pip freeze from the path passed in the argument"""

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            type=str,
            nargs=1,
            default='',
            help='run this with a path to a virtual environment as an argument to see the associated Job Templates, Organizations, Projects, and Inventory Sources.',
        )
        parser.add_argument('-q', action='store_true', help='run with -q to output only the results of the query.')

    def handle(self, *args, **options):
        # look organiztions and unified job templates (which include JTs, workflows, and Inventory updates)
        super(Command, self).__init__()
        results = {}
        path = options.get('path')
        if path:
            all_venvs = get_custom_venv_choices()
            if path[0] in all_venvs:  # verify this is a valid path
                path = path[0]
                orgs = [{"name": org.name, "id": org.id} for org in Organization.objects.filter(custom_virtualenv=path)]
                jts = [{"name": jt.name, "id": jt.id} for jt in JobTemplate.objects.filter(custom_virtualenv=path)]
                proj = [{"name": proj.name, "id": proj.id} for proj in Project.objects.filter(custom_virtualenv=path)]
                invsrc = [{"name": inv.name, "id": inv.id} for inv in InventorySource.objects.filter(custom_virtualenv=path)]
                results["organizations"] = orgs
                results["job_templates"] = jts
                results["projects"] = proj
                results["inventory_sources"] = invsrc
                if not options.get('q'):
                    msg = [
                        '# Virtual Environments Associations:',
                        yaml.dump(results),
                        '- To list all (now deprecated) custom virtual environments run:',
                        'awx-manage list_custom_venvs',
                        '',
                        '- To export the contents of a (deprecated) virtual environment, run the following command while supplying the path as an argument:',
                        'awx-manage export_custom_venv /path/to/venv',
                        '',
                        '- Run these commands with `-q` to remove tool tips.',
                        '',
                    ]
                    print('\n'.join(msg))
                else:
                    print(yaml.dump(results))

            else:
                print('\n', '# Incorrect path, verify your path is from the following list:')
                print('\n'.join(all_venvs), '\n')
