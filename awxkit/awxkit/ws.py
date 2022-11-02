import threading
import logging
import atexit
import json
import ssl
import datetime

from queue import Queue, Empty
from urllib.parse import urlparse

from awxkit.config import config


log = logging.getLogger(__name__)


class WSClientException(Exception):

    pass


changed = 'changed'
limit_reached = 'limit_reached'
status_changed = 'status_changed'
summary = 'summary'


class WSClient(object):
    """Provides a basic means of testing pub/sub notifications with payloads similar to
    'groups': {'jobs': ['status_changed', 'summary'],
               'schedules': ['changed'],
               'ad_hoc_command_events': [ids...],
               'job_events': [ids...],
               'workflow_events': [ids...],
               'project_update_events': [ids...],
               'inventory_update_events': [ids...],
               'system_job_events': [ids...],
               'control': ['limit_reached']}
    e.x:
    ```
    ws = WSClient(token, port=8013, secure=False).connect()
    ws.job_details()
    ... # launch job
    job_messages = [msg for msg in ws]
    ws.ad_hoc_stdout()
    ... # launch ad hoc command
    ad_hoc_messages = [msg for msg in ws]
    ws.close()
    ```
    """

    # Subscription group types

    def __init__(
        self, token=None, hostname='', port=443, secure=True, session_id=None, csrftoken=None, add_received_time=False, session_cookie_name='awx_sessionid'
    ):
        # delay this import, because this is an optional dependency
        import websocket

        if not hostname:
            result = urlparse(config.base_url)
            secure = result.scheme == 'https'
            port = result.port
            if port is None:
                port = 80
                if secure:
                    port = 443
            # should we be adding result.path here?
            hostname = result.hostname

        self.port = port
        self._use_ssl = secure
        self.hostname = hostname
        self.token = token
        self.session_id = session_id
        self.csrftoken = csrftoken
        self._recv_queue = Queue()
        self._ws_closed = False
        self._ws_connected_flag = threading.Event()
        if self.token is not None:
            auth_cookie = 'token="{0.token}";'.format(self)
        elif self.session_id is not None:
            auth_cookie = '{1}="{0.session_id}"'.format(self, session_cookie_name)
            if self.csrftoken:
                auth_cookie += ';csrftoken={0.csrftoken}'.format(self)
        else:
            auth_cookie = ''
        pref = 'wss://' if self._use_ssl else 'ws://'
        url = '{0}{1.hostname}:{1.port}/websocket/'.format(pref, self)
        self.ws = websocket.WebSocketApp(
            url, on_open=self._on_open, on_message=self._on_message, on_error=self._on_error, on_close=self._on_close, cookie=auth_cookie
        )
        self._message_cache = []
        self._should_subscribe_to_pending_job = False
        self._pending_unsubscribe = threading.Event()
        self._add_received_time = add_received_time

    def connect(self):
        wst = threading.Thread(target=self._ws_run_forever, args=(self.ws, {"cert_reqs": ssl.CERT_NONE}))
        wst.daemon = True
        wst.start()
        atexit.register(self.close)
        if not self._ws_connected_flag.wait(20):
            raise WSClientException('Failed to establish channel connection w/ AWX.')
        return self

    def close(self):
        log.info('close method was called, but ignoring')
        if not self._ws_closed:
            log.info('Closing websocket connection.')
            self.ws.close()

    def job_details(self, *job_ids):
        """subscribes to job status, summary, and, for the specified ids, job events"""
        self.subscribe(jobs=[status_changed, summary], job_events=list(job_ids))

    def pending_job_details(self):
        """subscribes to job status and summary, with responsive
        job event subscription for an id provided by AWX
        """
        self.subscribe_to_pending_events('job_events', [status_changed, summary])

    def status_changes(self):
        self.subscribe(jobs=[status_changed])

    def job_stdout(self, *job_ids):
        self.subscribe(jobs=[status_changed], job_events=list(job_ids))

    def pending_job_stdout(self):
        self.subscribe_to_pending_events('job_events')

    # mirror page behavior
    def ad_hoc_stdout(self, *ahc_ids):
        self.subscribe(jobs=[status_changed], ad_hoc_command_events=list(ahc_ids))

    def pending_ad_hoc_stdout(self):
        self.subscribe_to_pending_events('ad_hoc_command_events')

    def project_update_stdout(self, *project_update_ids):
        self.subscribe(jobs=[status_changed], project_update_events=list(project_update_ids))

    def pending_project_update_stdout(self):
        self.subscribe_to_pending_events('project_update_events')

    def inventory_update_stdout(self, *inventory_update_ids):
        self.subscribe(jobs=[status_changed], inventory_update_events=list(inventory_update_ids))

    def pending_inventory_update_stdout(self):
        self.subscribe_to_pending_events('inventory_update_events')

    def workflow_events(self, *wfjt_ids):
        self.subscribe(jobs=[status_changed], workflow_events=list(wfjt_ids))

    def pending_workflow_events(self):
        self.subscribe_to_pending_events('workflow_events')

    def system_job_events(self, *system_job_ids):
        self.subscribe(jobs=[status_changed], system_job_events=list(system_job_ids))

    def pending_system_job_events(self):
        self.subscribe_to_pending_events('system_job_events')

    def subscribe_to_pending_events(self, events, jobs=[status_changed]):
        self._should_subscribe_to_pending_job = dict(jobs=jobs, events=events)
        self.subscribe(jobs=jobs)

    # mirror page behavior
    def jobs_list(self):
        self.subscribe(jobs=[status_changed, summary], schedules=[changed])

    # mirror page behavior
    def dashboard(self):
        self.subscribe(jobs=[status_changed])

    def subscribe(self, **groups):
        """Sends a subscription request for the specified channel groups.
        ```
        ws.subscribe(jobs=[ws.status_changed, ws.summary],
                     job_events=[1,2,3])
        ```
        """
        self._subscribe(groups=groups)

    def _subscribe(self, **payload):
        payload['xrftoken'] = self.csrftoken
        self._send(json.dumps(payload))

    def unsubscribe(self, wait=True, timeout=10):
        if wait:
            # Other unnsubscribe events could have caused the edge to trigger.
            # This way the _next_ event will trigger our waiting.
            self._pending_unsubscribe.clear()
            self._send(json.dumps(dict(groups={}, xrftoken=self.csrftoken)))
            if not self._pending_unsubscribe.wait(timeout):
                raise RuntimeError("Failed while waiting on unsubscribe reply because timeout of {} seconds was reached.".format(timeout))
        else:
            self._send(json.dumps(dict(groups={}, xrftoken=self.csrftoken)))

    def _on_message(self, message):
        message = json.loads(message)
        log.debug('received message: {}'.format(message))
        if self._add_received_time:
            message['received_time'] = datetime.datetime.utcnow()

        if all([message.get('group_name') == 'jobs', message.get('status') == 'pending', message.get('unified_job_id'), self._should_subscribe_to_pending_job]):
            if bool(message.get('project_id')) == (self._should_subscribe_to_pending_job['events'] == 'project_update_events'):
                self._update_subscription(message['unified_job_id'])

        ret = self._recv_queue.put(message)

        # unsubscribe acknowledgement
        if 'groups_current' in message:
            self._pending_unsubscribe.set()

        return ret

    def _update_subscription(self, job_id):
        subscription = dict(jobs=self._should_subscribe_to_pending_job['jobs'])
        events = self._should_subscribe_to_pending_job['events']
        subscription[events] = [job_id]
        self.subscribe(**subscription)
        self._should_subscribe_to_pending_job = False

    def _on_open(self):
        self._ws_connected_flag.set()

    def _on_error(self, error):
        log.info('Error received: {}'.format(error))

    def _on_close(self):
        log.info('Successfully closed ws.')
        self._ws_closed = True

    def _ws_run_forever(self, sockopt=None, sslopt=None):
        self.ws.run_forever(sslopt=sslopt)
        log.debug('ws.run_forever finished')

    def _recv(self, wait=False, timeout=10):
        try:
            msg = self._recv_queue.get(wait, timeout)
        except Empty:
            return None
        return msg

    def _send(self, data):
        self.ws.send(data)
        log.debug('successfully sent {}'.format(data))

    def __iter__(self):
        while True:
            val = self._recv()
            if not val:
                return
            yield val
