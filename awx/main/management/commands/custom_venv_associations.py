# Copyright (c) 2021 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand
from awx.main.utils.common import get_custom_venv_choices
from awx.main.models import Organization, InventorySource, JobTemplate, Project


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

    def handle(self, *args, **options):
        # look organiztions and unified job templates (which include JTs, workflows, and Inventory updates)
        super(Command, self).__init__()
        results = {}
        path = options.get('path')
        if path:
            if path in get_custom_venv_choices():  # verify this is a valid path
                path = options.get('path')[0]
                orgs = [{"name": org.name, "id": org.id} for org in Organization.objects.filter(custom_virtualenv=path)]
                jts = [{"name": jt.name, "id": jt.id} for jt in JobTemplate.objects.filter(custom_virtualenv=path)]
                proj = [{"name": proj.name, "id": proj.id} for proj in Project.objects.filter(custom_virtualenv=path)]
                invsrc = [{"name": inv.name, "id": inv.id} for inv in InventorySource.objects.filter(custom_virtualenv=path)]
                results["Organizations"] = orgs
                results["Job Templates"] = jts
                results["Projects"] = proj
                results["Inventory Sources"] = invsrc
                print(results)
