# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import datetime
import json
import logging
import requests
import dateutil.parser as dp

from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

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

logger = logging.getLogger('awx.main.notifications.grafana_backend')


class GrafanaBackend(AWXBaseEmailBackend, CustomNotificationBase):

    init_parameters = {"grafana_url": {"label": "Grafana URL", "type": "string"},
                       "grafana_key": {"label": "Grafana API Key", "type": "password"}}
    recipient_parameter = "grafana_url"
    sender_parameter = None

    DEFAULT_BODY = "{{ job_metadata }}"
    default_messages = {"started": {"body": DEFAULT_BODY, "message": DEFAULT_MSG},
                        "success": {"body": DEFAULT_BODY, "message": DEFAULT_MSG},
                        "error": {"body": DEFAULT_BODY, "message": DEFAULT_MSG},
                        "workflow_approval": {"running": {"message": DEFAULT_APPROVAL_RUNNING_MSG, "body": DEFAULT_APPROVAL_RUNNING_BODY},
                                              "approved": {"message": DEFAULT_APPROVAL_APPROVED_MSG,"body": DEFAULT_APPROVAL_APPROVED_BODY},
                                              "timed_out": {"message": DEFAULT_APPROVAL_TIMEOUT_MSG, "body": DEFAULT_APPROVAL_TIMEOUT_BODY},
                                              "denied": {"message": DEFAULT_APPROVAL_DENIED_MSG, "body": DEFAULT_APPROVAL_DENIED_BODY}}}

    def __init__(self, grafana_key,dashboardId=None, panelId=None, annotation_tags=None, grafana_no_verify_ssl=False, isRegion=True,
                 fail_silently=False, **kwargs):
        super(GrafanaBackend, self).__init__(fail_silently=fail_silently)
        self.grafana_key = grafana_key
        self.dashboardId = dashboardId
        self.panelId = panelId
        self.annotation_tags = annotation_tags if annotation_tags is not None else []
        self.grafana_no_verify_ssl = grafana_no_verify_ssl
        self.isRegion = isRegion

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
        for m in messages:
            grafana_data = {}
            grafana_headers = {}
            if 'started' in m.body:
                try:
                    epoch=datetime.datetime.utcfromtimestamp(0)
                    grafana_data['time'] = grafana_data['timeEnd'] = int((dp.parse(m.body['started']).replace(tzinfo=None) - epoch).total_seconds() * 1000)
                    if m.body.get('finished'):
                        grafana_data['timeEnd'] = int((dp.parse(m.body['finished']).replace(tzinfo=None) - epoch).total_seconds() * 1000)
                except ValueError:
                    logger.error(smart_text(_("Error converting time {} or timeEnd {} to int.").format(m.body['started'],m.body['finished'])))
                    if not self.fail_silently:
                        raise Exception(smart_text(_("Error converting time {} and/or timeEnd {} to int.").format(m.body['started'],m.body['finished'])))
            grafana_data['isRegion'] = self.isRegion
            grafana_data['dashboardId'] = self.dashboardId
            grafana_data['panelId'] = self.panelId
            if self.annotation_tags:
                grafana_data['tags'] = self.annotation_tags
            grafana_data['text'] = m.subject
            grafana_headers['Authorization'] = "Bearer {}".format(self.grafana_key)
            grafana_headers['Content-Type'] = "application/json"
            r = requests.post("{}/api/annotations".format(m.recipients()[0]),
                              json=grafana_data,
                              headers=grafana_headers,
                              verify=(not self.grafana_no_verify_ssl))
            if r.status_code >= 400:
                logger.error(smart_text(_("Error sending notification grafana: {}").format(r.status_code)))
                if not self.fail_silently:
                    raise Exception(smart_text(_("Error sending notification grafana: {}").format(r.status_code)))
            sent_messages += 1
        return sent_messages
