# -*- coding: utf-8 -*-
from __future__ import print_function

import sys

import time

from .utils import cprint, color_enabled, STATUS_COLORS
from awxkit.utils import to_str


def monitor_workflow(response, session, print_stdout=True, action_timeout=None, interval=0.25):
    get = response.url.get
    payload = {
        'order_by': 'finished',
        'unified_job_node__workflow_job': response.id,
    }

    def fetch(seen):
        results = response.connection.get('/api/v2/unified_jobs', payload).json()['results']

        # erase lines we've previously printed
        if print_stdout and sys.stdout.isatty():
            for _ in seen:
                sys.stdout.write('\x1b[1A')
                sys.stdout.write('\x1b[2K')

        for result in results:
            result['name'] = to_str(result['name'])
            if print_stdout:
                print(' ↳ {id} - {name} '.format(**result), end='')
                status = result['status']
                if color_enabled():
                    color = STATUS_COLORS.get(status, 'white')
                    cprint(status, color)
                else:
                    print(status)
                seen.add(result['id'])

    if print_stdout:
        cprint('------Starting Standard Out Stream------', 'red')

    if print_stdout:
        print('Launching {}...'.format(to_str(get().json.name)))

    started = time.time()
    seen = set()
    while True:
        if action_timeout and time.time() - started > action_timeout:
            if print_stdout:
                cprint('Monitoring aborted due to action-timeout.', 'red')
            break

        if sys.stdout.isatty():
            # if this is a tty-like device, we can send ANSI codes
            # to draw an auto-updating view
            # otherwise, just wait for the job to finish and print it *once*
            # all at the end
            fetch(seen)

        time.sleep(0.25)
        json = get().json
        if json.finished:
            fetch(seen)
            break
    if print_stdout:
        cprint('------End of Standard Out Stream--------\n', 'red')
    return get().json.status


def monitor(response, session, print_stdout=True, action_timeout=None, interval=0.25):
    get = response.url.get
    payload = {'order_by': 'start_line', 'no_truncate': True}
    if response.type == 'job':
        events = response.related.job_events.get
    else:
        events = response.related.events.get

    next_line = 0

    def fetch(next_line):
        for result in events(**payload).json.results:
            if result['start_line'] != next_line:
                # If this event is a line from _later_ in the stdout,
                # it means that the events didn't arrive in order;
                # skip it for now and wait until the prior lines arrive and are
                # printed
                continue
            stdout = to_str(result.get('stdout'))
            if stdout and print_stdout:
                print(stdout)
            next_line = result['end_line']
        return next_line

    if print_stdout:
        cprint('------Starting Standard Out Stream------', 'red')

    started = time.time()
    while True:
        if action_timeout and time.time() - started > action_timeout:
            if print_stdout:
                cprint('Monitoring aborted due to action-timeout.', 'red')
            break
        next_line = fetch(next_line)
        if next_line:
            payload['start_line__gte'] = next_line

        time.sleep(0.25)
        json = get().json
        if json.event_processing_finished is True or json.status in ('error', 'canceled'):
            fetch(next_line)
            break
    if print_stdout:
        cprint('------End of Standard Out Stream--------\n', 'red')
    return get().json.status
