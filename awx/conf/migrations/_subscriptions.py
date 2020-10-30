# -*- coding: utf-8 -*-
import logging
from django.utils.timezone import now
from awx.main.utils.encryption import decrypt_field, encrypt_field

logger = logging.getLogger('awx.conf.settings')

__all__ = ['clear_old_license', 'prefill_rh_credentials']
    

def clear_old_license(apps, schema_editor):
    Setting = apps.get_model('conf', 'Setting')
    Setting.objects.filter(key='LICENSE').delete()


def _migrate_setting(apps, old_key, new_key, encrypted=False):
    Setting = apps.get_model('conf', 'Setting')
    if not Setting.objects.filter(key=old_key).exists():
        return
    new_setting = Setting.objects.create(key=new_key,
                                         created=now(),
                                         modified=now()
                                         )
    if encrypted:
        new_setting.value = decrypt_field(Setting.objects.filter(key=old_key).first(), 'value')
        new_setting.value = encrypt_field(new_setting, 'value')
    else:
        new_setting.value = getattr(Setting.objects.filter(key=old_key).first(), 'value')
    new_setting.save()


def prefill_rh_credentials(apps, schema_editor):
    _migrate_setting(apps, 'REDHAT_USERNAME', 'SUBSCRIPTIONS_USERNAME', encrypted=False)
    _migrate_setting(apps, 'REDHAT_PASSWORD', 'SUBSCRIPTIONS_PASSWORD', encrypted=True)
