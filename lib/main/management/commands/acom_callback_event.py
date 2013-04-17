#!/usr/bin/env python

# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
# 
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License. 
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Ansible Commander. If not, see <http://www.gnu.org/licenses/>.

import json
from optparse import make_option
import os
import sys
from django.core.management.base import NoArgsCommand, CommandError

class Command(NoArgsCommand):
    '''
    Management command to log callback events from ansible-playbook.
    '''

    help = 'Ansible Commander Callback Event Capture'

    option_list = NoArgsCommand.option_list + (
        make_option('-j', '--job', dest='job_id',
                    type='int', default=0,
                    help='Job ID (can also be specified using ACOM_JOB_ID '
                         'environment variable)'),
        make_option('-e', '--event', dest='event_type', default=None,
                 help='Event type'),
        make_option('-f', '--file', dest='event_data_file', default=None,
                    help='JSON-formatted data file containing callback event '
                         'data (specify "-" to read from stdin)'),
        make_option('-d', '--data', dest='event_data_json', default=None,
                    help='JSON-formatted callback event data'),
    )

    def handle_noargs(self, **options):
        from lib.main.models import Job, JobEvent
        event_type = options.get('event_type', None)
        if not event_type:
            raise CommandError('No event specified')
        if event_type not in [x[0] for x in JobEvent.EVENT_TYPES]:
            raise CommandError('Unsupported event')
        event_data_file = options.get('event_data_file', None)
        event_data_json = options.get('event_data_json', None)
        if event_data_file is None and event_data_json is None:
            raise CommandError('Either --file or --data must be specified')
        try:
            job_id = int(os.getenv('ACOM_JOB_ID', options.get('job_id', 0)))
        except ValueError:
            raise CommandError('Job ID must be an integer')
        if not job_id:
            raise CommandError('No Job ID specified')
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise CommandError('Job with ID %d not found' % job_id)
        if job.status != 'running':
            raise CommandError('Unable to add event except when job is running')
        try:
            if event_data_json is None:
                try:
                    if event_data_file == '-':
                        event_data_fileobj = sys.stdin
                    else:
                        event_data_fileobj = file(event_data_file, 'rb')
                    event_data = json.load(event_data_fileobj)
                except IOError, e:
                    raise CommandError('Error %r reading from %s' % (e, event_data_file))
            else:
                event_data = json.loads(event_data_json)
        except ValueError:
            raise CommandError('Error parsing JSON data')
        job.job_events.create(event=event_type, event_data=event_data)

if __name__ == '__main__':
    from __init__ import run_command_as_script
    command_name = os.path.splitext(os.path.basename(__file__))[0]
    run_command_as_script(command_name)
