# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from awx.main.models import Instance


class Command(BaseCommand):
    """Remove an existing instance from the HA instance table.

    This command is idempotent. It will remove the machine if it is
    present and do nothing if the machine is absent.

    This command will cowardly refuse to remove the primary machine.
    """
    option_list = BaseCommand.option_list + (
        make_option('--hostname', dest='hostname', default=''),
        make_option('--uuid', dest='uuid', default=''),
    )

    def handle(self, **options):
        # Remove any empty options from the options dictionary.
        fields = {}
        for field in ('uuid', 'hostname'):
            if options[field]:
                fields[field] = options[field]

        # At least one of hostname or uuid must be set.
        if not fields:
            raise CommandError('You must provide either --uuid or --hostname.')

        # Is there an existing record for this machine?
        # If so, retrieve that record and look for issues.
        try:
            # Get the instance.
            instance = Instance.objects.get(**fields)

            # Sanity check: Do not remove the primary instance.
            if instance.primary:
                raise CommandError('I cowardly refuse to remove the primary '
                                   'instance.')

            # Remove the instance.
            instance.delete()
            dirty = True
        except Instance.DoesNotExist:
            dirty = False

        # Done!
        print('Instance removed (changed: %r).' % dirty)
