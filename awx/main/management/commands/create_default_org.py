# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved

from django.core.management.base import BaseCommand
from crum import impersonate
from awx.main.models import User, Organization


class Command(BaseCommand):
    """Creates the default organization if and only if no organizations
    exist in the system.
    """
    help = 'Creates a default organization iff there are none.'

    def handle(self, *args, **kwargs):
        # Sanity check: Is there already an organization in the system?
        if Organization.objects.count():
            return

        # Create a default organization as the first superuser found.
        try:
            superuser = User.objects.filter(is_superuser=True, is_active=True).order_by('pk')[0]
        except IndexError:
            superuser = None
        with impersonate(superuser):
            Organization.objects.create(name='Default')
        print('Default organization added.')
