# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from awx.conf.models import Setting
from awx.main.utils import common


def test_encrypt_field():
    field = Setting(pk=123, value='ANSIBLE')
    encrypted = field.value = common.encrypt_field(field, 'value')
    assert encrypted == '$encrypted$AES$Ey83gcmMuBBT1OEq2lepnw=='
    assert common.decrypt_field(field, 'value') == 'ANSIBLE'


def test_encrypt_field_without_pk():
    field = Setting(value='ANSIBLE')
    encrypted = field.value = common.encrypt_field(field, 'value')
    assert encrypted == '$encrypted$AES$8uIzEoGyY6QJwoTWbMFGhw=='
    assert common.decrypt_field(field, 'value') == 'ANSIBLE'


def test_encrypt_field_with_unicode_string():
    value = u'Iñtërnâtiônàlizætiøn'
    field = Setting(value=value)
    encrypted = field.value = common.encrypt_field(field, 'value')
    assert encrypted == '$encrypted$UTF8$AES$AESQbqOefpYcLC7x8yZ2aWG4FlXlS66JgavLbDp/DSM='
    assert common.decrypt_field(field, 'value') == value


def test_encrypt_field_force_disable_unicode():
    value = u"NothingSpecial"
    field = Setting(value=value)
    encrypted = field.value = common.encrypt_field(field, 'value', skip_utf8=True)
    assert "UTF8" not in encrypted
    assert common.decrypt_field(field, 'value') == value


def test_encrypt_subfield():
    field = Setting(value={'name': 'ANSIBLE'})
    encrypted = field.value = common.encrypt_field(field, 'value', subfield='name')
    assert encrypted == '$encrypted$AES$8uIzEoGyY6QJwoTWbMFGhw=='
    assert common.decrypt_field(field, 'value', subfield='name') == 'ANSIBLE'


def test_encrypt_field_with_ask():
    encrypted = common.encrypt_field(Setting(value='ASK'), 'value', ask=True)
    assert encrypted == 'ASK'


def test_encrypt_field_with_empty_value():
    encrypted = common.encrypt_field(Setting(value=None), 'value')
    assert encrypted is None
