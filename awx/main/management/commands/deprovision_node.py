# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved

# Borrow from another AWX command
from awx.main.management.commands.deprovision_instance import Command as OtherCommand

# Python
import warnings


class Command(OtherCommand):

    def handle(self, *args, **options):
        # TODO: delete this entire file in 3.3
        warnings.warn('This command is replaced with `deprovision_instance` and will '
                      'be removed in release 3.3.')
        return super(Command, self).handle(*args, **options)
