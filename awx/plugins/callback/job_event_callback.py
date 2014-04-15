# Copyright (c) 2014 AnsibleWorks, Inc.
# This file is a utility Ansible plugin that is not part of the AWX or Ansible
# packages.  It does not import any code from either package, nor does its
# license apply to Ansible or AWX.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
#    Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#    Neither the name of the <ORGANIZATION> nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Python
import datetime
import json
import logging
import os
import sys
import urllib
import urlparse
import time

# Requests
import requests

# ZeroMQ
import zmq


class TokenAuth(requests.auth.AuthBase):

    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        request.headers['Authorization'] = 'Token %s' % self.token
        return request


class CallbackModule(object):
    '''
    Callback module for logging ansible-playbook job events via the REST API.
    '''

    # These events should never have an associated play.
    EVENTS_WITHOUT_PLAY = [
        'playbook_on_start',
        'playbook_on_stats',
    ]
    # These events should never have an associated task.
    EVENTS_WITHOUT_TASK = EVENTS_WITHOUT_PLAY + [
        'playbook_on_setup',
        'playbook_on_notify',
        'playbook_on_import_for_host',
        'playbook_on_not_import_for_host',
        'playbook_on_no_hosts_matched',
        'playbook_on_no_hosts_remaining',
    ]

    def __init__(self):
        self.job_id = int(os.getenv('JOB_ID'))
        self.base_url = os.getenv('REST_API_URL', '')
        self.auth_token = os.getenv('REST_API_TOKEN', '')
        self.callback_consumer_port = os.getenv('CALLBACK_CONSUMER_PORT', '')
        self.context = None
        self.socket = None
        self._init_logging()
        self._init_connection()

    def _init_logging(self):
        try:
            self.job_callback_debug = int(os.getenv('JOB_CALLBACK_DEBUG', '0'))
        except ValueError:
            self.job_callback_debug = 0
        self.logger = logging.getLogger('awx.plugins.callback.job_event_callback')
        if self.job_callback_debug >= 2:
            self.logger.setLevel(logging.DEBUG)
        elif self.job_callback_debug >= 1:
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.WARNING)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)-8s %(process)-8d %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def _init_connection(self):
        self.context = None
        self.socket = None

    def _start_connection(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(self.callback_consumer_port)

    def _post_job_event_queue_msg(self, event, event_data):
        msg = {
            'job_id': self.job_id,
            'event': event,
            'event_data': event_data,
            'created': datetime.datetime.utcnow().isoformat(),
        }
        active_pid = os.getpid()
        if self.job_callback_debug:
            msg.update({
                'pid': active_pid,
            })
        for retry_count in xrange(4):
            try:
                if not hasattr(self, 'connection_pid'):
                    self.connection_pid = active_pid
                if self.connection_pid != active_pid:
                    self._init_connection()
                if self.context is None:
                    self._start_connection()

                self.socket.send_json(msg)
                self.socket.recv()
                return
            except Exception, e:
                self.logger.info('Publish Exception: %r, retry=%d', e,
                                 retry_count, exc_info=True)
                # TODO: Maybe recycle connection here?
                if retry_count >= 3:
                    raise

    def _post_rest_api_event(self, event, event_data):
        data = json.dumps({
            'event': event,
            'event_data': event_data,
        })
        parts = urlparse.urlsplit(self.base_url)
        if parts.username and parts.password:
            auth = (parts.username, parts.password)
        elif self.auth_token:
            auth = TokenAuth(self.auth_token)
        else:
            auth = None
        port = parts.port or (443 if parts.scheme == 'https' else 80)
        url = urlparse.urlunsplit([parts.scheme,
                                   '%s:%d' % (parts.hostname, port),
                                   parts.path, parts.query, parts.fragment])
        url_path = '/api/v1/jobs/%d/job_events/' % self.job_id
        url = urlparse.urljoin(url, url_path)
        headers = {'content-type': 'application/json'}
        response = requests.post(url, data=data, headers=headers, auth=auth)
        response.raise_for_status()

    def _log_event(self, event, **event_data):
        play = getattr(self, 'play', None)
        play_name = getattr(play, 'name', '')
        if play_name and event not in self.EVENTS_WITHOUT_PLAY:
            event_data['play'] = play_name
        task = getattr(self, 'task', None)
        task_name = getattr(task, 'name', '')
        role_name = getattr(task, 'role_name', '')
        if task_name and event not in self.EVENTS_WITHOUT_TASK:
            event_data['task'] = task_name
        if role_name and event not in self.EVENTS_WITHOUT_TASK:
            event_data['role'] = role_name
        if self.callback_consumer_port:
            self._post_job_event_queue_msg(event, event_data)
        else:
            self._post_rest_api_event(event, event_data)

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        self._log_event('runner_on_failed', host=host, res=res,
                        ignore_errors=ignore_errors)

    def runner_on_ok(self, host, res):
        self._log_event('runner_on_ok', host=host, res=res)

    def runner_on_error(self, host, msg):
        self._log_event('runner_on_error', host=host, msg=msg)

    def runner_on_skipped(self, host, item=None):
        self._log_event('runner_on_skipped', host=host, item=item)

    def runner_on_unreachable(self, host, res):
        self._log_event('runner_on_unreachable', host=host, res=res)

    def runner_on_no_hosts(self):
        self._log_event('runner_on_no_hosts')

    def runner_on_async_poll(self, host, res, jid, clock):
        self._log_event('runner_on_async_poll', host=host, res=res, jid=jid,
                        clock=clock)

    def runner_on_async_ok(self, host, res, jid):
        self._log_event('runner_on_async_ok', host=host, res=res, jid=jid)

    def runner_on_async_failed(self, host, res, jid):
        self._log_event('runner_on_async_failed', host=host, res=res, jid=jid)

    def runner_on_file_diff(self, host, diff):
        self._log_event('runner_on_file_diff', host=host, diff=diff)

    def playbook_on_start(self):
        self._log_event('playbook_on_start')

    def playbook_on_notify(self, host, handler):
        self._log_event('playbook_on_notify', host=host, handler=handler)

    def playbook_on_no_hosts_matched(self):
        self._log_event('playbook_on_no_hosts_matched')

    def playbook_on_no_hosts_remaining(self):
        self._log_event('playbook_on_no_hosts_remaining')

    def playbook_on_task_start(self, name, is_conditional):
        self._log_event('playbook_on_task_start', name=name,
                        is_conditional=is_conditional)

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None,
                                encrypt=None, confirm=False, salt_size=None,
                                salt=None, default=None):
        self._log_event('playbook_on_vars_prompt', varname=varname,
                        private=private, prompt=prompt, encrypt=encrypt,
                        confirm=confirm, salt_size=salt_size, salt=salt,
                        default=default)

    def playbook_on_setup(self):
        self._log_event('playbook_on_setup')

    def playbook_on_import_for_host(self, host, imported_file):
        # don't care about recording this one
        # self._log_event('playbook_on_import_for_host', host=host,
        #                imported_file=imported_file)
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        # don't care about recording this one
        #self._log_event('playbook_on_not_import_for_host', host=host,
        #                missing_file=missing_file)
        pass

    def playbook_on_play_start(self, pattern):
        self._log_event('playbook_on_play_start', pattern=pattern)

    def playbook_on_stats(self, stats):
        d = {}
        for attr in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped'):
            d[attr] = getattr(stats, attr)
        self._log_event('playbook_on_stats', **d)
