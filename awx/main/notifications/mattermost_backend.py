# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging
import requests

from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

from awx.main.notifications.base import AWXBaseEmailBackend
from awx.main.notifications.custom_notification_base import CustomNotificationBase

logger = logging.getLogger('awx.main.notifications.mattermost_backend')


class MattermostBackend(AWXBaseEmailBackend, CustomNotificationBase):

    init_parameters = {"mattermost_url": {"label": "Target URL", "type": "string"},
                       "mattermost_no_verify_ssl": {"label": "Verify SSL", "type": "bool"}}
    recipient_parameter = "mattermost_url"
    sender_parameter = None

    def __init__(self, mattermost_no_verify_ssl=False, mattermost_channel=None, mattermost_username=None,
                 mattermost_icon_url=None, fail_silently=False, **kwargs):
        super(MattermostBackend, self).__init__(fail_silently=fail_silently)
        self.mattermost_channel = mattermost_channel
        self.mattermost_username = mattermost_username
        self.mattermost_icon_url = mattermost_icon_url
        self.mattermost_no_verify_ssl = mattermost_no_verify_ssl

    def format_body(self, body):
        return body

    def send_messages(self, messages):
        sent_messages = 0
        for m in messages:
            payload = {}
            for opt, optval in {'mattermost_icon_url':'icon_url',
                                'mattermost_channel': 'channel', 'mattermost_username': 'username'}.items():
                optvalue = getattr(self, opt)
                if optvalue is not None:
                    payload[optval] = optvalue.strip()

            payload['text'] = m.subject

            r = requests.post("{}".format(m.recipients()[0]),
                              json=payload, verify=(not self.mattermost_no_verify_ssl))
            if r.status_code >= 400:
                logger.error(smart_text(_("Error sending notification mattermost: {}").format(r.status_code)))
                if not self.fail_silently:
                    raise Exception(smart_text(_("Error sending notification mattermost: {}").format(r.status_code)))
            sent_messages += 1
        return sent_messages
