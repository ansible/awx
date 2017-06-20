from django.utils.translation import ugettext_lazy as _

from awx.main import utils
from awx.conf.migrations._reencrypt import (
    decrypt_field,
    should_decrypt_field,
)

from awx.main.notifications.email_backend import CustomEmailBackend
from awx.main.notifications.slack_backend import SlackBackend
from awx.main.notifications.twilio_backend import TwilioBackend
from awx.main.notifications.pagerduty_backend import PagerDutyBackend
from awx.main.notifications.hipchat_backend import HipChatBackend
from awx.main.notifications.webhook_backend import WebhookBackend
from awx.main.notifications.irc_backend import IrcBackend
from awx.main.models.credential import Credential

__all__ = ['replace_aesecb_fernet']


NOTIFICATION_TYPES = [('email', _('Email'), CustomEmailBackend),
                      ('slack', _('Slack'), SlackBackend),
                      ('twilio', _('Twilio'), TwilioBackend),
                      ('pagerduty', _('Pagerduty'), PagerDutyBackend),
                      ('hipchat', _('HipChat'), HipChatBackend),
                      ('webhook', _('Webhook'), WebhookBackend),
                      ('irc', _('IRC'), IrcBackend)]


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
                value = decrypt_field(nt, 'notification_configuration', subfield=field)
                nt.notification_configuration[field] = value
        nt.save()


def _credentials(apps):
    # TODO: Try to not use the model directly imported from our
    # source (should use apps.get_model) to make the migration less britle.
    for credential in Credential.objects.all():
        for field_name, value in credential.inputs.items():
            if should_decrypt_field(value):
                value = decrypt_field(credential, field_name)
                credential.inputs[field_name] = value
        credential.save()


def _unified_jobs(apps):
    UnifiedJob = apps.get_model('main', 'UnifiedJob')
    for uj in UnifiedJob.objects.all():
        if uj.start_args is not None:
            if should_decrypt_field(uj.start_args):
                start_args = decrypt_field(uj, 'start_args')
                uj.start_args = start_args
                uj.save()
