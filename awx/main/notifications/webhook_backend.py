# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging
import requests

from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from awx.main.notifications.base import AWXBaseEmailBackend
from awx.main.utils import get_awx_version

logger = logging.getLogger('awx.main.notifications.webhook_backend')


class WebhookBackend(AWXBaseEmailBackend):

    init_parameters = {"url": {"label": "Target URL", "type": "string"},
                       "headers": {"label": "HTTP Headers", "type": "object"}}
    recipient_parameter = "url"
    sender_parameter = None

    def __init__(self, headers, fail_silently=False, **kwargs):
        self.headers = headers
        super(WebhookBackend, self).__init__(fail_silently=fail_silently)

    def format_body(self, body):
        return body

    def send_messages(self, messages):
        sent_messages = 0
        if 'User-Agent' not in self.headers:
            self.headers['User-Agent'] = "Tower {}".format(get_awx_version())
        for m in messages:
            r = requests.post("{}".format(m.recipients()[0]),
                              json=m.body,
                              headers=self.headers)
            if r.status_code >= 400:
                logger.error(smart_text(_("Error sending notification webhook: {}").format(r.text)))
                if not self.fail_silently:
                    raise Exception(smart_text(_("Error sending notification webhook: {}").format(r.text)))
            sent_messages += 1
        return sent_messages
