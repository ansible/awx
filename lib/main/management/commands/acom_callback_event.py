#!/usr/bin/env python

# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import json
from optparse import make_option
import os
import sys
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommmand):

    help = 'Ansible Commander Callback Event Capture'

    option_list = BaseCommmand.option_list + (
        make_option('-i', '--launch-job-status', dest='launch_job_status_id',
                    type='int', default=0,
                    help='Inventory ID (can also be specified using '
                         'ACOM_INVENTORY_ID environment variable)'),
        #make_option('--indent', dest='indent', type='int', default=None,
        #            help='Indentation level for pretty printing output'),
    )

    def handle(self, *args, **options):
        from lib.main.models import LaunchJobStatus
        try:
            launch_job_status_id = int(os.getenv('ACOM_LAUNCH_JOB_STATUS_ID',
                                   options.get('launch_job_status_id', 0)))
        except ValueError:
            raise CommandError('Launch job status ID must be an integer')
        if not launch_job_status_id:
            raise CommandError('No launch job status ID specified')
        try:
            launch_job_status = LaunchJobStatus.objects.get(id=launch_job_status_id)
        except Inventory.DoesNotExist:
            raise CommandError('Launch job status with ID %d not found' % launch_job_status_id)
        # FIXME: Do stuff here.

if __name__ == '__main__':
    from __init__ import run_command_as_script
    command_name = os.path.splitext(os.path.basename(__file__))[0]
    run_command_as_script(command_name)
