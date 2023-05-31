# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import json
import logging
import requests

from awx.main.notifications.base import AWXBaseEmailBackend
from awx.main.utils import get_awx_http_client_headers
from awx.main.notifications.custom_notification_base import CustomNotificationBase

logger = logging.getLogger('awx.main.notifications.webhook_backend')


class WebhookBackend(AWXBaseEmailBackend, CustomNotificationBase):
    MAX_RETRIES = 5

    init_parameters = {
        "url": {"label": "Target URL", "type": "string"},
        "http_method": {"label": "HTTP Method", "type": "string", "default": "POST"},
        "disable_ssl_verification": {"label": "Verify SSL", "type": "bool", "default": False},
        "username": {"label": "Username", "type": "string", "default": ""},
        "password": {"label": "Password", "type": "password", "default": ""},
        "headers": {"label": "HTTP Headers", "type": "object"},
    }
    recipient_parameter = "url"
    sender_parameter = None

    DEFAULT_BODY = "{{ job_metadata }}"
    default_messages = {
        "started": {"body": DEFAULT_BODY},
        "success": {"body": DEFAULT_BODY},
        "error": {"body": DEFAULT_BODY},
        "workflow_approval": {
            "running": {"body": '{"body": "The approval node \\"{{ approval_node_name }}\\" needs review. This node can be viewed at: {{ workflow_url }}"}'},
            "approved": {"body": '{"body": "The approval node \\"{{ approval_node_name }}\\" was approved. {{ workflow_url }}"}'},
            "timed_out": {"body": '{"body": "The approval node \\"{{ approval_node_name }}\\" has timed out. {{ workflow_url }}"}'},
            "denied": {"body": '{"body": "The approval node \\"{{ approval_node_name }}\\" was denied. {{ workflow_url }}"}'},
        },
    }

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
        if self.http_method.lower() not in ['put', 'post']:
            raise ValueError("HTTP method must be either 'POST' or 'PUT'.")
        chosen_method = getattr(requests, self.http_method.lower(), None)

        for m in messages:
            auth = None
            if self.username or self.password:
                auth = (self.username, self.password)

            # the constructor for EmailMessage - https://docs.djangoproject.com/en/4.1/_modules/django/core/mail/message will turn an empty dictionary to an empty string
            # sometimes an empty dict is intentional and we added this conditional to enforce that
            if not m.body:
                m.body = {}

            url = str(m.recipients()[0])
            data = json.dumps(m.body, ensure_ascii=False).encode('utf-8')
            headers = {**(get_awx_http_client_headers()), **(self.headers or {})}

            err = None

            for retries in range(self.MAX_RETRIES):
                # Sometimes we hit redirect URLs. We must account for this. We still extract the redirect URL from the response headers and try again. Max retires == 5
                resp = chosen_method(
                    url=url,
                    auth=auth,
                    data=data,
                    headers=headers,
                    verify=(not self.disable_ssl_verification),
                    allow_redirects=False,  # override default behaviour for redirects
                )

                # either success or error reached if this conditional fires
                if resp.status_code not in [301, 307]:
                    break

                # we've hit a redirect. extract the redirect URL out of the first response header and try again
                logger.warning(
                    f"Received a {resp.status_code} from {url}, trying to reach redirect url {resp.headers.get('Location', None)}; attempt #{retries+1}"
                )

                # take the first redirect URL in the response header and try that
                url = resp.headers.get("Location", None)

                if url is None:
                    err = f"Webhook notification received redirect to a blank URL from {url}. Response headers={resp.headers}"
                    break
            else:
                # no break condition in the loop encountered; therefore we have hit the maximum number of retries
                err = f"Webhook notification max number of retries [{self.MAX_RETRIES}] exceeded. Failed to send webhook notification to {url}"

            if resp.status_code >= 400:
                err = f"Error sending webhook notification: {resp.status_code}"

            # log error message
            if err:
                logger.error(err)
                if not self.fail_silently:
                    raise Exception(err)

            # no errors were encountered therefore we successfully sent off the notification webhook
            if resp.status_code in range(200, 299):
                logger.debug(f"Notification webhook successfully sent to {url}. Received {resp.status_code}")
                sent_messages += 1

        return sent_messages
