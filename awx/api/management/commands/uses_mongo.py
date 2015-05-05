# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

import sys

from django.core.management.base import BaseCommand

from awx.main.task_engine import TaskSerializer


class Command(BaseCommand):
    """Return a exit status of 0 if MongoDB should be active, and an
    exit status of 1 otherwise.

    This script is intended to be used by bash and init scripts to
    conditionally start MongoDB, so its focus is on being bash-friendly.
    """
    def handle(self, **kwargs):
        # Get the license data.
        license_reader = TaskSerializer()
        license_data = license_reader.from_file()

        # Does the license contain the system tracking feature?
        # If and only if it does, MongoDB should run.
        system_tracking = license_data['features']['system_tracking']

        # Okay, do we need MongoDB to be turned on?
        # This is a silly variable assignment right now, but I expect the
        # rules here will grow more complicated over time.
        # FIXME: Most likely this should be False if HA is active
        #        (not just enabled by license, but actually in use).
        uses_mongo = system_tracking

        # If we do not need Mongo, return a non-zero exit status.
        print('MongoDB NOT required')
        sys.exit(1)

        # We do need Mongo, return zero.
        print('MongoDB required')
        sys.exit(0)
