# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging

from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from awx.main.models.base import * # noqa
from awx.main.notifications.email_backend import CustomEmailBackend
from awx.main.notifications.slack_backend import SlackBackend
from awx.main.notifications.twilio_backend import TwilioBackend

# Django-JSONField
from jsonfield import JSONField

logger = logging.getLogger('awx.main.models.notifications')

__all__ = ['NotificationTemplate']

class NotificationTemplate(CommonModel):

    NOTIFICATION_TYPES = [('email', _('Email'), CustomEmailBackend),
                          ('slack', _('Slack'), SlackBackend),
                          ('twilio', _('Twilio'), TwilioBackend)]
    NOTIFICATION_TYPE_CHOICES = [(x[0], x[1]) for x in NOTIFICATION_TYPES]
    CLASS_FOR_NOTIFICATION_TYPE = dict([(x[0], x[2]) for x in NOTIFICATION_TYPES])

    class Meta:
        app_label = 'main'

    notification_type = models.CharField(
        max_length = 32,
        choices=NOTIFICATION_TYPE_CHOICES,
    )

    notification_configuration = JSONField(blank=False)

    def get_absolute_url(self):
        return reverse('api:notification_template_detail', args=(self.pk,))

    @property
    def notification_class(self):
        return CLASS_FOR_NOTIFICATION_TYPE[self.notification_type]
