# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from awx.main.models import Instance


class Command(BaseCommand):
    """Regsiter this instance with the database for HA tracking.

    This command is idempotent. It will register the machine if it is not
    yet present and do nothing if the machine is already registered.

    If a second primary machine is registered, the first primary machine will
    become a secondary machine, and the newly registered primary machine
    will be primary (unless `--timid` is provided, in which case the command
    will simply error out).

    This command will also error out under the following circumstances:

      * Attempting to register a secondary machine with no primary machines.
      * Attempting to register this machine with a different state than its
        existing registration plus `--timid`.
    """
    option_list = BaseCommand.option_list + (
        make_option('--timid', action='store_true', dest='timid'),
        make_option('--primary', action='store_true', dest='primary'),
        make_option('--secondary', action='store_false', dest='primary'),
    )

    def handle(self, **options):
        uuid = settings.SYSTEM_UUID
        timid = options['timid']

        # Is there an existing record for this machine?
        # If so, retrieve that record and look for issues.
        try:
            instance = Instance.objects.get(uuid=uuid)
            existing = True
        except Instance.DoesNotExist:
            instance = Instance(uuid=uuid)
            existing = False

        # Get a status on primary machines (excluding this one, regardless
        # of its status).
        other_instances = Instance.objects.exclude(uuid=uuid)
        primaries = other_instances.filter(primary=True).count()

        # Sanity check: If we're supposed to be being timid, then ensure
        # that there's no crazy mosh pits happening here.
        #
        # If the primacy setting doesn't match what is already on
        # the instance, error out.
        if existing and timid and instance.primary != options['primary']:
            raise CommandError('This instance is already registered as a '
                               '%s instance.' % instance.role)

        # If this instance is being set to primary and a *different* primary
        # machine alreadyexists, error out if we're supposed to be timid.
        if timid and options['primary'] and primaries:
            raise CommandError('Another instance is already registered as '
                               'primary.')

        # Lastly, if there are no primary machines at all, then don't allow
        # this to be registered as a secondary machine.
        if not options['primary'] and not primaries:
            raise CommandError('Unable to register a secondary machine until '
                               'another primary machine has been registered.')

        # If this is a primary machine and there is another primary machine,
        # it must be de-primary-ified.
        if options['primary'] and primaries:
            for old_primary in other_instances.filter(primary=True):
                old_primary.primary = False
                old_primary.save()

        # Okay, we've checked for appropriate errata; perform the registration.
        dirty = instance.primary is not options['primary']
        instance.primary = options['primary']
        instance.save()

        # Done!
        print('Instance %s registered (changed: %r).' % (uuid, dirty))
