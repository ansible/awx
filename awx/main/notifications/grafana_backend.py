# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import datetime
import logging
import requests
import dateutil.parser as dp

from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from awx.main.notifications.base import AWXBaseEmailBackend


logger = logging.getLogger('awx.main.notifications.grafana_backend')


class GrafanaBackend(AWXBaseEmailBackend):

    init_parameters = {"grafana_url": {"label": "Grafana URL", "type": "string"},
                       "grafana_key": {"label": "Grafana API Key", "type": "password"}}
    recipient_parameter = "grafana_url"
    sender_parameter = None

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
        return body

    def send_messages(self, messages):
        sent_messages = 0
        for m in messages:
            grafana_data = {}
            grafana_headers = {}
            try:
                epoch=datetime.datetime.utcfromtimestamp(0)
                grafana_data['time'] = int((dp.parse(m.body['started']).replace(tzinfo=None) - epoch).total_seconds() * 1000)
                grafana_data['timeEnd'] = int((dp.parse(m.body['finished']).replace(tzinfo=None) - epoch).total_seconds() * 1000)
            except ValueError:
                logger.error(smart_text(_("Error converting time {} or timeEnd {} to int.").format(m.body['started'],m.body['finished'])))
                if not self.fail_silently:
                    raise Exception(smart_text(_("Error converting time {} and/or timeEnd {} to int.").format(m.body['started'],m.body['finished'])))
            grafana_data['isRegion'] = self.isRegion
            grafana_data['dashboardId'] = self.dashboardId
            grafana_data['panelId'] = self.panelId
            grafana_data['tags'] = self.annotation_tags
            grafana_data['text'] = m.subject
            grafana_headers['Authorization'] = "Bearer {}".format(self.grafana_key)
            grafana_headers['Content-Type'] = "application/json"
            r = requests.post("{}/api/annotations".format(m.recipients()[0]),
                              json=grafana_data,
                              headers=grafana_headers,
                              verify=(not self.grafana_no_verify_ssl))
            if r.status_code >= 400:
                logger.error(smart_text(_("Error sending notification grafana: {}").format(r.text)))
                if not self.fail_silently:
                    raise Exception(smart_text(_("Error sending notification grafana: {}").format(r.text)))
            sent_messages += 1
        return sent_messages
