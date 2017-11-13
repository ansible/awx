# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from awx.main.utils import get_licenser
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Returns license type, e.g., 'enterprise', 'open', 'none'"""

    def handle(self, *args, **options):
        super(Command, self).__init__()
        return get_licenser().validate().get('license_type', 'none')
