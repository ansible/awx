# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

import sys

from optparse import make_option
from django.core.management.base import BaseCommand
from awx.main.models import Instance
from awx.main.task_engine import TaskSerializer


class Command(BaseCommand):
    """Return a exit status of 0 if MongoDB should be active, and an
    exit status of 1 otherwise.

    This script is intended to be used by bash and init scripts to
    conditionally start MongoDB, so its focus is on being bash-friendly.
    """

    def __init__(self):
        super(Command, self).__init__()
        BaseCommand.option_list += (make_option('--local',
                                                dest='local',
                                                default=False,
                                                action="store_true",
                                                help="Only check if mongo should be running locally"),)

    def handle(self, *args, **kwargs):
        # Get the license data.
        license_reader = TaskSerializer()
        license_data = license_reader.from_file()

        # Does the license have features, at all?
        # If there is no license yet, then all features are clearly off.
        if 'features' not in license_data:
            print('No license available.')
            sys.exit(2)

        # Does the license contain the system tracking feature?
        # If and only if it does, MongoDB should run.
        system_tracking = license_data['features']['system_tracking']

        # Okay, do we need MongoDB to be turned on?
        # This is a silly variable assignment right now, but I expect the
        # rules here will grow more complicated over time.
        uses_mongo = system_tracking  # noqa

        if Instance.objects.count() > 1 and kwargs['local'] and uses_mongo:
            print("HA Configuration detected.  Database should be remote")
            uses_mongo = False

        # If we do not need Mongo, return a non-zero exit status.
        if not uses_mongo:
            print('MongoDB NOT required')
            sys.exit(1)

        # We do need Mongo, return zero.
        print('MongoDB required')
        sys.exit(0)
