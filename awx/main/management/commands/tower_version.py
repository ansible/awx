# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand

from awx import __version__ as tower_version

class Command(BaseCommand):

    help = 'Emit the Tower version and exit'

    def handle(self, *args, **options):
        self.stdout.write(tower_version)
