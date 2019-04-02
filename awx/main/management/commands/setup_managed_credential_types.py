# Copyright (c) 2019 Ansible by Red Hat
# All Rights Reserved.

from django.core.management.base import BaseCommand

from awx.main.models import CredentialType


class Command(BaseCommand):

    help = 'Load default managed credential types.'

    def handle(self, *args, **options):
        CredentialType.setup_tower_managed_defaults()
