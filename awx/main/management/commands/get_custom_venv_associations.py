# Copyright (c) 2021 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand
from awx.main.models import Organization, InventorySource, UnifiedJobTemplate


class Command(BaseCommand):
    """Returns the pip freeze from the path passed in the argument"""

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            type=str,
            nargs='?',
            default='',
            help='run this with a path to a virtual environment as an argument to see the pip freeze data',
        )

    def handle(self, *args, **options):
        # look organiztions and unified job templates (which include JTs, workflows, and Inventory updates)
        super(Command, self).__init__()
        results = {}
        if options.get('path'):
            # sanity check here - is path in list
            path = options.get('path')
            orgs = [{"name": org.name, "id": org.id} for org in Organization.objects.filter(custom_virtualenv=path)]
            ujts = [{"name": org.name, "id": org.id} for org in UnifiedJobTemplate.objects.filter(custom_virtualenv=path)]
            invsrc = [{"name": inv.name, "id": inv.id} for inv in InventorySource.objects.filter(custom_virtualenv=path)]
            results["Organizations"] = orgs
            results["Unified Job Templates"] = ujts
            results["Inventory Sources"] = invsrc
            print(results)
        else:
            print("missing argument: please include a path argument following the command.")
