# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import json
import logging

from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _
from pagerduty import EventsApiV2Client

from awx.main.notifications.base import AWXBaseEmailBackend
from awx.main.notifications.custom_notification_base import CustomNotificationBase

DEFAULT_MSG = CustomNotificationBase.DEFAULT_MSG

DEFAULT_APPROVAL_RUNNING_MSG = CustomNotificationBase.DEFAULT_APPROVAL_RUNNING_MSG
DEFAULT_APPROVAL_RUNNING_BODY = CustomNotificationBase.DEFAULT_APPROVAL_RUNNING_BODY

DEFAULT_APPROVAL_APPROVED_MSG = CustomNotificationBase.DEFAULT_APPROVAL_APPROVED_MSG
DEFAULT_APPROVAL_APPROVED_BODY = CustomNotificationBase.DEFAULT_APPROVAL_APPROVED_BODY

DEFAULT_APPROVAL_TIMEOUT_MSG = CustomNotificationBase.DEFAULT_APPROVAL_TIMEOUT_MSG
DEFAULT_APPROVAL_TIMEOUT_BODY = CustomNotificationBase.DEFAULT_APPROVAL_TIMEOUT_BODY

DEFAULT_APPROVAL_DENIED_MSG = CustomNotificationBase.DEFAULT_APPROVAL_DENIED_MSG
DEFAULT_APPROVAL_DENIED_BODY = CustomNotificationBase.DEFAULT_APPROVAL_DENIED_BODY

logger = logging.getLogger('awx.main.notifications.pagerduty_backend')


class PagerDutyBackend(AWXBaseEmailBackend, CustomNotificationBase):
    init_parameters = {
        "subdomain": {"label": "Pagerduty subdomain", "type": "string"},
        "token": {"label": "API Token", "type": "password"},
        "service_key": {"label": "API Service/Integration Key", "type": "string"},
        "client_name": {"label": "Client Identifier", "type": "string"},
    }
    recipient_parameter = "service_key"
    sender_parameter = "client_name"

    DEFAULT_BODY = "{{ job_metadata }}"
    default_messages = {
        "started": {"message": DEFAULT_MSG, "body": DEFAULT_BODY},
        "success": {"message": DEFAULT_MSG, "body": DEFAULT_BODY},
        "error": {"message": DEFAULT_MSG, "body": DEFAULT_BODY},
        "workflow_approval": {
            "running": {"message": DEFAULT_APPROVAL_RUNNING_MSG, "body": DEFAULT_APPROVAL_RUNNING_BODY},
            "approved": {"message": DEFAULT_APPROVAL_APPROVED_MSG, "body": DEFAULT_APPROVAL_APPROVED_BODY},
            "timed_out": {"message": DEFAULT_APPROVAL_TIMEOUT_MSG, "body": DEFAULT_APPROVAL_TIMEOUT_BODY},
            "denied": {"message": DEFAULT_APPROVAL_DENIED_MSG, "body": DEFAULT_APPROVAL_DENIED_BODY},
        },
    }

    def __init__(self, subdomain, token, fail_silently=False, **kwargs):
        super(PagerDutyBackend, self).__init__(fail_silently=fail_silently)
        self.subdomain = subdomain
        self.token = token

    def format_body(self, body):
        if isinstance(body, dict):
            return body

        try:
            potential_body = json.loads(body)
            if isinstance(potential_body, dict):
                return potential_body
        except (TypeError, json.JSONDecodeError):
            pass

        return body

    def send_messages(self, messages):
        sent_messages = 0

        for m in messages:
            try:
                pager = EventsApiV2Client(m.recipients()[0])
            except Exception as e:
                logger.error(smart_str(_("Exception connecting to PagerDuty: {}").format(e)))
                if not self.fail_silently:
                    raise
                continue

            try:
                body = self.format_body(m.body)
                if not isinstance(body, dict):
                    body = {"body": body}

                pager.trigger(
                    summary=m.subject,
                    source=m.from_email,
                    custom_details=body,
                )
                sent_messages += 1
            except Exception as e:
                logger.error(smart_str(_("Exception sending messages: {}").format(e)))
                if not self.fail_silently:
                    raise

        return sent_messages
