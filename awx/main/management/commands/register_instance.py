# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import CommandError

from awx.api.license import feature_enabled
from awx.main.management.commands._base_instance import BaseCommandInstance
from awx.main.models import Instance

instance_str = BaseCommandInstance.instance_str

class Command(BaseCommandInstance):
    """Internal tower command.
    Regsiter this instance with the database for HA tracking.

    This command is idempotent.

    This command will error out in the following conditions:

      * Attempting to register a secondary machine with no primary machines.
      * Attempting to register a primary instance when a different primary
      instance exists.
      * Attempting to re-register an instance with changed values.
    """
    def __init__(self):
        super(Command, self).__init__()

        self.include_options_roles()
        self.include_option_hostname_set()

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)

        uuid = self.get_UUID()

        # Are we attempting to register a secondary instance?
        # If so, we are only willing to do that if the Tower license allows
        # it.
        if self.is_option_secondary() and not feature_enabled('ha'):
            raise CommandError('Your Tower license does not permit creation '
                               'of secondary instances.')

        # Is there an existing record for this machine? If so, retrieve that record and look for issues.
        try:
            instance = Instance.objects.get(uuid=uuid)
            if instance.hostname != self.get_option_hostname():
                raise CommandError('Instance already registered with a different hostname %s.' % instance_str(instance))
            print("Instance already registered %s" % instance_str(instance))
        except Instance.DoesNotExist:
            # Get a status on primary machines (excluding this one, regardless of its status).
            other_instances = Instance.objects.exclude(uuid=uuid)
            primaries = other_instances.filter(primary=True).count()

            # If this instance is being set to primary and a *different* primary machine alreadyexists, error out.
            if self.is_option_primary() and primaries:
                raise CommandError('Another instance is already registered as primary.')

            # Lastly, if there are no primary machines at all, then don't allow this to be registered as a secondary machine.
            if self.is_option_secondary() and not primaries:
                raise CommandError('Unable to register a secondary machine until another primary machine has been registered.')

            # Okay, we've checked for appropriate errata; perform the registration.
            instance = Instance(uuid=uuid, primary=self.is_option_primary(), hostname=self.get_option_hostname())
            instance.save()

            # If this is a primary instance, update projects.
            if instance.primary:
                self.update_projects(instance)

            # Done!
            print('Successfully registered instance %s.' % instance_str(instance))
