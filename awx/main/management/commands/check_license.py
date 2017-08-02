# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from awx.main.utils import get_licenser
from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):
    """Return 0 if licensed; 1 if unlicensed
    """

    def handle(self, **options):
        super(Command, self).__init__()

        license_info = get_licenser().validate()
        if license_info['valid_key'] is True:
            return 0
        else:
            return 1

