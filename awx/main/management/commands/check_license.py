# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

import json

from awx.main.utils import get_licenser
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Returns license type, e.g., 'enterprise', 'open', 'none'"""

    def add_arguments(self, parser):
        parser.add_argument('--data', dest='data', action='store_true',
                            help='verbose, prints the actual (sanitized) license')

    def handle(self, *args, **options):
        super(Command, self).__init__()
        license = get_licenser().validate()
        if options.get('data'):
            return json.dumps(license)
        return license.get('license_type', 'none')
