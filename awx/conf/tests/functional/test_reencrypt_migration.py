# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.
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
@pytest.mark.parametrize("old_enc, new_enc, value", [
    ('$encrypted$UTF8$AES', '$encrypted$UTF8$AESCBC$', u'Iñtërnâtiônàlizætiøn'),
    ('$encrypted$AES$', '$encrypted$AESCBC$', 'test'),
])
def test_settings(old_enc, new_enc, value):
    with mock.patch('awx.conf.models.encrypt_field', encrypt_field):
        with mock.patch('awx.conf.settings.decrypt_field', decrypt_field):
            setting = Setting.objects.create(key='SOCIAL_AUTH_GITHUB_SECRET', value=value)
    assert setting.value.startswith(old_enc)

    replace_aesecb_fernet(apps, None)
    setting.refresh_from_db()

    assert setting.value.startswith(new_enc)
    assert new_decrypt_field(setting, 'value') == value

    # This is here for a side-effect.
    # Exception if the encryption type of AESCBC is not properly skipped, ensures
    # our `startswith` calls don't have typos
    replace_aesecb_fernet(apps, None)
