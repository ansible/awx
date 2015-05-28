# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand

from awx.main.models import Organization


class Command(BaseCommand):
    """Creates the default organization if and only if no organizations
    exist in the system.
    """
    help = 'Creates a default organization iff there are none.'

    def handle(self, *args, **kwargs):
        # Sanity check: Is there already an organization in the system?
        if Organization.objects.count():
            return

        # Create a default organization.
        org, new = Organization.objects.get_or_create(name='Default')
        if new:
            print('Default organization added.')
