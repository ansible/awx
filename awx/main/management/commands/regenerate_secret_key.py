import base64
import json
import os

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save

from awx.conf import settings_registry
from awx.conf.models import Setting
from awx.conf.signals import on_post_save_setting
from awx.main.models import (
    UnifiedJob, Credential, NotificationTemplate, Job, JobTemplate, WorkflowJob,
    WorkflowJobTemplate, OAuth2Application
)
from awx.main.utils.encryption import (
    encrypt_field, decrypt_field, encrypt_value, decrypt_value, get_encryption_key
)


class Command(BaseCommand):
    """
    Regenerate a new SECRET_KEY value and re-encrypt every secret in the
    Tower database.
    """

    @transaction.atomic
    def handle(self, **options):
        self.old_key = settings.SECRET_KEY
        self.new_key = base64.encodebytes(os.urandom(33)).decode().rstrip()
        self._notification_templates()
        self._credentials()
        self._unified_jobs()
        self._oauth2_app_secrets()
        self._settings()
        self._survey_passwords()
        return self.new_key

    def _notification_templates(self):
        for nt in NotificationTemplate.objects.iterator():
            CLASS_FOR_NOTIFICATION_TYPE = dict([(x[0], x[2]) for x in NotificationTemplate.NOTIFICATION_TYPES])
            notification_class = CLASS_FOR_NOTIFICATION_TYPE[nt.notification_type]
            for field in filter(lambda x: notification_class.init_parameters[x]['type'] == "password",
                                notification_class.init_parameters):
                nt.notification_configuration[field] = decrypt_field(nt, 'notification_configuration', subfield=field, secret_key=self.old_key)
                nt.notification_configuration[field] = encrypt_field(nt, 'notification_configuration', subfield=field, secret_key=self.new_key)
            nt.save()

    def _credentials(self):
        for credential in Credential.objects.iterator():
            for field_name in credential.credential_type.secret_fields:
                if field_name in credential.inputs:
                    credential.inputs[field_name] = decrypt_field(
                        credential,
                        field_name,
                        secret_key=self.old_key
                    )
                    credential.inputs[field_name] = encrypt_field(
                        credential,
                        field_name,
                        secret_key=self.new_key
                    )
                credential.save()

    def _unified_jobs(self):
        for uj in UnifiedJob.objects.iterator():
            if uj.start_args:
                uj.start_args = decrypt_field(
                    uj,
                    'start_args',
                    secret_key=self.old_key
                )
                uj.start_args = encrypt_field(uj, 'start_args', secret_key=self.new_key)
                uj.save()

    def _oauth2_app_secrets(self):
        for app in OAuth2Application.objects.iterator():
            raw = app.client_secret
            app.client_secret = raw
            encrypted = encrypt_value(raw, secret_key=self.new_key)
            OAuth2Application.objects.filter(pk=app.pk).update(client_secret=encrypted)

    def _settings(self):
        # don't update the cache, the *actual* value isn't changing
        post_save.disconnect(on_post_save_setting, sender=Setting)
        for setting in Setting.objects.filter().order_by('pk'):
            if settings_registry.is_setting_encrypted(setting.key):
                setting.value = decrypt_field(setting, 'value', secret_key=self.old_key)
                setting.value = encrypt_field(setting, 'value', secret_key=self.new_key)
                setting.save()

    def _survey_passwords(self):
        for _type in (JobTemplate, WorkflowJobTemplate):
            for jt in _type.objects.exclude(survey_spec={}):
                changed = False
                if jt.survey_spec.get('spec', []):
                    for field in jt.survey_spec['spec']:
                        if field.get('type') == 'password' and field.get('default', ''):
                            raw = decrypt_value(
                                get_encryption_key('value', None, secret_key=self.old_key),
                                field['default']
                            )
                            field['default'] = encrypt_value(
                                raw,
                                pk=None,
                                secret_key=self.new_key
                            )
                            changed = True
                if changed:
                    jt.save(update_fields=["survey_spec"])

        for _type in (Job, WorkflowJob):
            for job in _type.objects.exclude(survey_passwords={}).iterator():
                changed = False
                for key in job.survey_passwords:
                    if key in job.extra_vars:
                        extra_vars = json.loads(job.extra_vars)
                        if not extra_vars.get(key):
                            continue
                        raw = decrypt_value(
                            get_encryption_key('value', None, secret_key=self.old_key),
                            extra_vars[key]
                        )
                        extra_vars[key] = encrypt_value(raw, pk=None, secret_key=self.new_key)
                        job.extra_vars = json.dumps(extra_vars)
                        changed = True
                if changed:
                    job.save(update_fields=["extra_vars"])
