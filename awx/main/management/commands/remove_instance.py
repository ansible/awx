# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from awx.main.management.commands._base_instance import BaseCommandInstance
instance_str = BaseCommandInstance.instance_str

from awx.main.models import Instance


class Command(BaseCommandInstance):
    """Internal tower command.
    Remove an existing instance from the HA instance table.

    This command is idempotent.

    This command will error out in the following conditions:

      * Attempting to remove a primary instance.
    """
    def __init__(self):
        super(Command, self).__init__()

        self.include_option_hostname_uuid_find()

    def handle(self, *args, **options):
        # Is there an existing record for this machine? If so, retrieve that record and look for issues.
        try:
            # Get the instance.
            instance = Instance.objects.get(**self.get_unique_fields())

            # Sanity check: Do not remove the primary instance.
            if instance.primary:
                raise CommandError('I cowardly refuse to remove the primary instance %s.' % instance_str(instance))

            # Remove the instance.
            instance.delete()
            print('Successfully removed instance %s.' % instance_str(instance))
        except Instance.DoesNotExist:
            print('No matching instance found to remove.')

