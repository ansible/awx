# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import json
import logging
import requests

from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

from awx.main.notifications.base import AWXBaseEmailBackend
from awx.main.utils import get_awx_version
from awx.main.notifications.custom_notification_base import CustomNotificationBase

logger = logging.getLogger('awx.main.notifications.webhook_backend')


class WebhookBackend(AWXBaseEmailBackend, CustomNotificationBase):

    init_parameters = {"url": {"label": "Target URL", "type": "string"},
                       "http_method": {"label": "HTTP Method", "type": "string", "default": "POST"},
                       "disable_ssl_verification": {"label": "Verify SSL", "type": "bool", "default": False},
                       "username": {"label": "Username", "type": "string", "default": ""},
                       "password": {"label": "Password", "type": "password", "default": ""},
                       "headers": {"label": "HTTP Headers", "type": "object"}}
    recipient_parameter = "url"
    sender_parameter = None

    DEFAULT_BODY = "{{ job_metadata }}"
    default_messages = {"started": {"body": DEFAULT_BODY},
                        "success": {"body": DEFAULT_BODY},
                        "error": {"body": DEFAULT_BODY},
                        "workflow_approval": {
                            "running": {"body": '{"body": "The approval node \\"{{ approval_node_name }}\\" needs review. '
                                                'This node can be viewed at: {{ workflow_url }}"}'},
                            "approved": {"body": '{"body": "The approval node \\"{{ approval_node_name }}\\" was approved. {{ workflow_url }}"}'},
                            "timed_out": {"body": '{"body": "The approval node \\"{{ approval_node_name }}\\" has timed out. {{ workflow_url }}"}'},
                            "denied": {"body": '{"body": "The approval node \\"{{ approval_node_name }}\\" was denied. {{ workflow_url }}"}'}}}

    def __init__(self, http_method, headers, disable_ssl_verification=False, fail_silently=False, username=None, password=None, **kwargs):
        self.http_method = http_method
        self.disable_ssl_verification = disable_ssl_verification
        self.headers = headers
        self.username = username
        self.password = password
        super(WebhookBackend, self).__init__(fail_silently=fail_silently)

    def format_body(self, body):
        # expect body to be a string representing a dict
        try:
            potential_body = json.loads(body)
            if isinstance(potential_body, dict):
                body = potential_body
        except json.JSONDecodeError:
            body = {}
        return body

    def send_messages(self, messages):
        sent_messages = 0
        self.headers['Content-Type'] = 'application/json'
        if 'User-Agent' not in self.headers:
            self.headers['User-Agent'] = "Tower {}".format(get_awx_version())
        if self.http_method.lower() not in ['put','post']:
            raise ValueError("HTTP method must be either 'POST' or 'PUT'.")
        chosen_method = getattr(requests, self.http_method.lower(), None)
        for m in messages:
            auth = None
            if self.username or self.password:
                auth = (self.username, self.password)
            r = chosen_method("{}".format(m.recipients()[0]),
                              auth=auth,
                              data=json.dumps(m.body, ensure_ascii=False).encode('utf-8'),
                              headers=self.headers,
                              verify=(not self.disable_ssl_verification))
            if r.status_code >= 400:
                logger.error(smart_text(_("Error sending notification webhook: {}").format(r.status_code)))
                if not self.fail_silently:
                    raise Exception(smart_text(_("Error sending notification webhook: {}").format(r.status_code)))
            sent_messages += 1
        return sent_messages
