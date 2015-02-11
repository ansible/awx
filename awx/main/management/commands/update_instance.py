# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import CommandError
from django.db import transaction

from awx.main.management.commands._base_instance import BaseCommandInstance

from awx.main.models import Instance

instance_str = BaseCommandInstance.instance_str

class Command(BaseCommandInstance):
    """Set an already registered instance to primary or secondary for HA 
    tracking.

    This command is idempotent. Settings a new primary instance when a 
    primary instance already exists will result in the existing primary
    instance set to secondary and the new primary set to primary.

    This command will error out under the following circumstances:

      * Attempting to update a secondary instance with no primary instances.
      * When a matching instance is not found.
    """
    def __init__(self):
        super(Command, self).__init__()

        self.include_options_roles()
        self.include_option_hostname_uuid_find()

    @transaction.atomic
    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)

        # Is there an existing record for this machine? If so, retrieve that record and look for issues.
        try:
            instance = Instance.objects.get(**self.get_unique_fields())
        except Instance.DoesNotExist:
            raise CommandError('No matching instance found to update.')

        # Get a status on primary machines (excluding this one, regardless of its status).
        other_instances = Instance.objects.exclude(**self.get_unique_fields())
        primaries = other_instances.filter(primary=True).count()

        # If this is a primary machine and there is another primary machine, it must be de-primary-ified.
        if self.is_option_primary() and primaries:
            for old_primary in other_instances.filter(primary=True):
                old_primary.primary = False
                old_primary.save()

        # Okay, we've checked for appropriate errata; perform the registration.
        instance.primary = self.is_option_primary()
        instance.save()

        # If this is a primary instance, update projects.
        self.update_projects_if_primary(instance)

        # Done!
        print('Successfully updated instance role %s' % instance_str(instance))
