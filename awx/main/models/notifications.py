# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging

from django.db import models
from django.conf import settings
from django.core.mail.message import EmailMessage
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_str, force_text

# AWX
from awx.api.versioning import reverse
from awx.main.models.base import CommonModelNameNotUnique, CreatedModifiedModel
from awx.main.utils import encrypt_field, decrypt_field, set_environ
from awx.main.notifications.email_backend import CustomEmailBackend
from awx.main.notifications.slack_backend import SlackBackend
from awx.main.notifications.twilio_backend import TwilioBackend
from awx.main.notifications.pagerduty_backend import PagerDutyBackend
from awx.main.notifications.hipchat_backend import HipChatBackend
from awx.main.notifications.webhook_backend import WebhookBackend
from awx.main.notifications.mattermost_backend import MattermostBackend
from awx.main.notifications.grafana_backend import GrafanaBackend
from awx.main.notifications.rocketchat_backend import RocketChatBackend
from awx.main.notifications.irc_backend import IrcBackend
from awx.main.fields import JSONField


logger = logging.getLogger('awx.main.models.notifications')

__all__ = ['NotificationTemplate', 'Notification']


class NotificationTemplate(CommonModelNameNotUnique):

    NOTIFICATION_TYPES = [('email', _('Email'), CustomEmailBackend),
                          ('slack', _('Slack'), SlackBackend),
                          ('twilio', _('Twilio'), TwilioBackend),
                          ('pagerduty', _('Pagerduty'), PagerDutyBackend),
                          ('grafana', _('Grafana'), GrafanaBackend),
                          ('hipchat', _('HipChat'), HipChatBackend),
                          ('webhook', _('Webhook'), WebhookBackend),
                          ('mattermost', _('Mattermost'), MattermostBackend),
                          ('rocketchat', _('Rocket.Chat'), RocketChatBackend),
                          ('irc', _('IRC'), IrcBackend)]
    NOTIFICATION_TYPE_CHOICES = [(x[0], x[1]) for x in NOTIFICATION_TYPES]
    CLASS_FOR_NOTIFICATION_TYPE = dict([(x[0], x[2]) for x in NOTIFICATION_TYPES])

    class Meta:
        app_label = 'main'
        unique_together = ('organization', 'name')

    organization = models.ForeignKey(
        'Organization',
        blank=False,
        null=True,
        on_delete=models.CASCADE,
        related_name='notification_templates',
    )

    notification_type = models.CharField(
        max_length = 32,
        choices=NOTIFICATION_TYPE_CHOICES,
    )

    notification_configuration = JSONField(blank=False)

    def get_absolute_url(self, request=None):
        return reverse('api:notification_template_detail', kwargs={'pk': self.pk}, request=request)

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
        super(NotificationTemplate, self).save(*args, **kwargs)
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
        notification = Notification(notification_template=self,
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
        with set_environ(**settings.AWX_TASK_ENV):
            return backend_obj.send_messages([notification_obj])

    def display_notification_configuration(self):
        field_val = self.notification_configuration.copy()
        for field in self.notification_class.init_parameters:
            if field in field_val and force_text(field_val[field]).startswith('$encrypted$'):
                field_val[field] = '$encrypted$'
        return field_val


class Notification(CreatedModifiedModel):
    '''
    A notification event emitted when a NotificationTemplate is run
    '''

    NOTIFICATION_STATE_CHOICES = [
        ('pending', _('Pending')),
        ('successful', _('Successful')),
        ('failed', _('Failed')),
    ]

    class Meta:
        app_label = 'main'
        ordering = ('pk',)

    notification_template = models.ForeignKey(
        'NotificationTemplate',
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
        choices=NotificationTemplate.NOTIFICATION_TYPE_CHOICES,
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

    def get_absolute_url(self, request=None):
        return reverse('api:notification_detail', kwargs={'pk': self.pk}, request=request)


class JobNotificationMixin(object):
    def get_notification_templates(self):
        raise RuntimeError("Define me")

    def get_notification_friendly_name(self):
        raise RuntimeError("Define me")

    def _build_notification_message(self, status_str):
        notification_body = self.notification_data()
        notification_subject = u"{} #{} '{}' {}: {}".format(self.get_notification_friendly_name(),
                                                            self.id,
                                                            self.name,
                                                            status_str,
                                                            notification_body['url'])
        notification_body['friendly_name'] = self.get_notification_friendly_name()
        return (notification_subject, notification_body)

    def build_notification_succeeded_message(self):
        return self._build_notification_message('succeeded')

    def build_notification_failed_message(self):
        return self._build_notification_message('failed')

    def send_notification_templates(self, status_str):
        from awx.main.tasks import send_notifications  # avoid circular import
        if status_str not in ['succeeded', 'failed']:
            raise ValueError(_("status_str must be either succeeded or failed"))
        try:
            notification_templates = self.get_notification_templates()
        except Exception:
            logger.warn("No notification template defined for emitting notification")
            notification_templates = None
        if notification_templates:
            if status_str == 'succeeded':
                notification_template_type = 'success'
            else:
                notification_template_type = 'error'
            all_notification_templates = set(notification_templates.get(notification_template_type, []) + notification_templates.get('any', []))
            if len(all_notification_templates):
                try:
                    (notification_subject, notification_body) = getattr(self, 'build_notification_%s_message' % status_str)()
                except AttributeError:
                    raise NotImplementedError("build_notification_%s_message() does not exist" % status_str)
                send_notifications.delay([n.generate_notification(notification_subject, notification_body).id
                                          for n in all_notification_templates],
                                         job_id=self.id)
