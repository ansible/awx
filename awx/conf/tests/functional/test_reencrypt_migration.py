import pytest
import mock

from django.apps import apps
from awx.conf.migrations._reencrypt import (
    replace_aesecb_fernet,
    encrypt_field,
    decrypt_field,
)
from awx.conf.settings import Setting
from awx.main.utils import decrypt_field as new_decrypt_field


@pytest.mark.django_db
def test_settings():
    with mock.patch('awx.conf.models.encrypt_field', encrypt_field):
        with mock.patch('awx.conf.settings.decrypt_field', decrypt_field):
            setting = Setting.objects.create(key='SOCIAL_AUTH_GITHUB_SECRET', value='test')
    assert setting.value.startswith('$encrypted$AES$')

    replace_aesecb_fernet(apps, None)
    setting.refresh_from_db()

    assert setting.value.startswith('$encrypted$AESCBC$')
    assert new_decrypt_field(setting, 'value') == 'test'
