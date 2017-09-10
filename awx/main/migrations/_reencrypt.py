import logging
from django.utils.translation import ugettext_lazy as _

from awx.conf.migrations._reencrypt import (
    decrypt_field,
    should_decrypt_field,
)
from awx.main.utils.encryption import encrypt_field

from awx.main.notifications.email_backend import CustomEmailBackend
from awx.main.notifications.slack_backend import SlackBackend
from awx.main.notifications.twilio_backend import TwilioBackend
from awx.main.notifications.pagerduty_backend import PagerDutyBackend
from awx.main.notifications.hipchat_backend import HipChatBackend
from awx.main.notifications.mattermost_backend import MattermostBackend
from awx.main.notifications.webhook_backend import WebhookBackend
from awx.main.notifications.irc_backend import IrcBackend

logger = logging.getLogger('awx.main.migrations')

__all__ = ['replace_aesecb_fernet']


NOTIFICATION_TYPES = [('email', _('Email'), CustomEmailBackend),
                      ('slack', _('Slack'), SlackBackend),
                      ('twilio', _('Twilio'), TwilioBackend),
                      ('pagerduty', _('Pagerduty'), PagerDutyBackend),
                      ('hipchat', _('HipChat'), HipChatBackend),
                      ('mattermost', _('Mattermost'), MattermostBackend),
                      ('webhook', _('Webhook'), WebhookBackend),
                      ('irc', _('IRC'), IrcBackend)]


PASSWORD_FIELDS = ('password', 'security_token', 'ssh_key_data', 'ssh_key_unlock',
                   'become_password', 'vault_password', 'secret', 'authorize_password')


def replace_aesecb_fernet(apps, schema_editor):
    _notification_templates(apps)
    _credentials(apps)
    _unified_jobs(apps)


def _notification_templates(apps):
    NotificationTemplate = apps.get_model('main', 'NotificationTemplate')
    for nt in NotificationTemplate.objects.all():
        CLASS_FOR_NOTIFICATION_TYPE = dict([(x[0], x[2]) for x in NOTIFICATION_TYPES])
        notification_class = CLASS_FOR_NOTIFICATION_TYPE[nt.notification_type]
        for field in filter(lambda x: notification_class.init_parameters[x]['type'] == "password",
                            notification_class.init_parameters):
            if should_decrypt_field(nt.notification_configuration[field]):
                nt.notification_configuration[field] = decrypt_field(nt, 'notification_configuration', subfield=field)
                nt.notification_configuration[field] = encrypt_field(nt, 'notification_configuration', subfield=field)
        nt.save()


def _credentials(apps):
    for credential in apps.get_model('main', 'Credential').objects.all():
        for field_name in PASSWORD_FIELDS:
            value = getattr(credential, field_name)
            if should_decrypt_field(value):
                value = decrypt_field(credential, field_name)
                setattr(credential, field_name, value)
                setattr(credential, field_name, encrypt_field(credential, field_name))
        credential.save()



def _unified_jobs(apps):
    UnifiedJob = apps.get_model('main', 'UnifiedJob')
    for uj in UnifiedJob.objects.all():
        if uj.start_args is not None:
            if should_decrypt_field(uj.start_args):
                uj.start_args = decrypt_field(uj, 'start_args')
                uj.start_args = encrypt_field(uj, 'start_args')
                uj.save()
