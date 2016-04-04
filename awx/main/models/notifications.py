# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging

from django.db import models
from django.core.urlresolvers import reverse
from django.core.mail.message import EmailMessage
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_str

from awx.main.models.base import * # noqa
from awx.main.utils import encrypt_field, decrypt_field
from awx.main.notifications.email_backend import CustomEmailBackend
from awx.main.notifications.slack_backend import SlackBackend
from awx.main.notifications.twilio_backend import TwilioBackend
from awx.main.notifications.pagerduty_backend import PagerDutyBackend
from awx.main.notifications.hipchat_backend import HipChatBackend
from awx.main.notifications.webhook_backend import WebhookBackend
from awx.main.notifications.irc_backend import IrcBackend

# Django-JSONField
from jsonfield import JSONField

logger = logging.getLogger('awx.main.models.notifications')

__all__ = ['Notifier', 'Notification']

class Notifier(CommonModel):

    NOTIFICATION_TYPES = [('email', _('Email'), CustomEmailBackend),
                          ('slack', _('Slack'), SlackBackend),
                          ('twilio', _('Twilio'), TwilioBackend),
                          ('pagerduty', _('Pagerduty'), PagerDutyBackend),
                          ('hipchat', _('HipChat'), HipChatBackend),
                          ('webhook', _('Webhook'), WebhookBackend),
                          ('irc', _('IRC'), IrcBackend)]
    NOTIFICATION_TYPE_CHOICES = [(x[0], x[1]) for x in NOTIFICATION_TYPES]
    CLASS_FOR_NOTIFICATION_TYPE = dict([(x[0], x[2]) for x in NOTIFICATION_TYPES])

    class Meta:
        app_label = 'main'

    organization = models.ForeignKey(
        'Organization',
        blank=False,
        null=True,
        on_delete=models.SET_NULL,
        related_name='notifiers',
    )

    notification_type = models.CharField(
        max_length = 32,
        choices=NOTIFICATION_TYPE_CHOICES,
    )

    notification_configuration = JSONField(blank=False)

    def get_absolute_url(self):
        return reverse('api:notifier_detail', args=(self.pk,))

    @property
    def notification_class(self):
        return self.CLASS_FOR_NOTIFICATION_TYPE[self.notification_type]

    def save(self, *args, **kwargs):
        new_instance = not bool(self.pk)
        update_fields = kwargs.get('update_fields', [])
        for field in filter(lambda x: self.notification_class.init_parameters[x]['type'] == "password",
                            self.notification_class.init_parameters):
            if self.notification_configuration[field].startswith("$encrypted$"):
                continue
            if new_instance:
                value = self.notification_configuration[field]
                setattr(self, '_saved_{}_{}'.format("config", field), value)
                self.notification_configuration[field] = ''
            else:
                encrypted = encrypt_field(self, 'notification_configuration', subfield=field)
                self.notification_configuration[field] = encrypted
                if 'notification_configuration' not in update_fields:
                    update_fields.append('notification_configuration')
        super(Notifier, self).save(*args, **kwargs)
        if new_instance:
            update_fields = []
            for field in filter(lambda x: self.notification_class.init_parameters[x]['type'] == "password",
                                self.notification_class.init_parameters):
                saved_value = getattr(self, '_saved_{}_{}'.format("config", field), '')
                self.notification_configuration[field] = saved_value
                if 'notification_configuration' not in update_fields:
                    update_fields.append('notification_configuration')
            self.save(update_fields=update_fields)

    @property
    def recipients(self):
        return self.notification_configuration[self.notification_class.recipient_parameter]

    def generate_notification(self, subject, message):
        notification = Notification(notifier=self,
                                    notification_type=self.notification_type,
                                    recipients=smart_str(self.recipients),
                                    subject=subject,
                                    body=message)
        notification.save()
        return notification

    def send(self, subject, body):
        for field in filter(lambda x: self.notification_class.init_parameters[x]['type'] == "password",
                            self.notification_class.init_parameters):
            self.notification_configuration[field] = decrypt_field(self,
                                                                   'notification_configuration',
                                                                   subfield=field)
        recipients = self.notification_configuration.pop(self.notification_class.recipient_parameter)
        if not isinstance(recipients, list):
            recipients = [recipients]
        sender = self.notification_configuration.pop(self.notification_class.sender_parameter, None)
        backend_obj = self.notification_class(**self.notification_configuration)
        notification_obj = EmailMessage(subject, backend_obj.format_body(body), sender, recipients)
        return backend_obj.send_messages([notification_obj])

class Notification(CreatedModifiedModel):
    '''
    A notification event emitted when a Notifier is run
    '''

    NOTIFICATION_STATE_CHOICES = [
        ('pending', _('Pending')),
        ('successful', _('Successful')),
        ('failed', _('Failed')),
    ]

    class Meta:
        app_label = 'main'
        ordering = ('pk',)

    notifier = models.ForeignKey(
        'Notifier',
        related_name='notifications',
        on_delete=models.CASCADE,
        editable=False
    )
    status = models.CharField(
        max_length=20,
        choices=NOTIFICATION_STATE_CHOICES,
        default='pending',
        editable=False,
    )
    error = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    notifications_sent = models.IntegerField(
        default=0,
        editable=False,
    )
    notification_type = models.CharField(
        max_length = 32,
        choices=Notifier.NOTIFICATION_TYPE_CHOICES,
    )
    recipients = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    subject = models.TextField(
        blank=True,
        default='',
        editable=False,
    )
    body = JSONField(blank=True)
    
    def get_absolute_url(self):
        return reverse('api:notification_detail', args=(self.pk,))
