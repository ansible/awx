# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.
import pytest

from awx.conf.models import Setting
from awx.main.utils import encryption


def test_encrypt_field():
    field = Setting(pk=123, value='ANSIBLE')
    encrypted = field.value = encryption.encrypt_field(field, 'value')
    assert encryption.decrypt_field(field, 'value') == 'ANSIBLE'
    assert encrypted.startswith('$encrypted$UTF8$AESCBC$')


def test_encrypt_field_without_pk():
    field = Setting(value='ANSIBLE')
    encrypted = field.value = encryption.encrypt_field(field, 'value')
    assert encryption.decrypt_field(field, 'value') == 'ANSIBLE'
    assert encrypted.startswith('$encrypted$UTF8$AESCBC$')


def test_encrypt_field_with_unicode_string():
    value = u'Iñtërnâtiônàlizætiøn'
    field = Setting(value=value)
    encrypted = field.value = encryption.encrypt_field(field, 'value')
    assert encryption.decrypt_field(field, 'value') == value
    assert encrypted.startswith('$encrypted$UTF8$AESCBC$')


def test_encrypt_subfield():
    field = Setting(value={'name': 'ANSIBLE'})
    encrypted = field.value = encryption.encrypt_field(field, 'value', subfield='name')
    assert encryption.decrypt_field(field, 'value', subfield='name') == 'ANSIBLE'
    assert encrypted.startswith('$encrypted$UTF8$AESCBC$')


def test_encrypt_field_with_ask():
    encrypted = encryption.encrypt_field(Setting(value='ASK'), 'value', ask=True)
    assert encrypted == 'ASK'


def test_encrypt_field_with_empty_value():
    encrypted = encryption.encrypt_field(Setting(value=None), 'value')
    assert encrypted is None


def test_encrypt_field_with_undefined_attr_raises_expected_exception():
    with pytest.raises(AttributeError):
        encryption.encrypt_field({}, 'undefined_attr')


def test_decrypt_field_with_undefined_attr_raises_expected_exception():
    with pytest.raises(AttributeError):
        encryption.decrypt_field({}, 'undefined_attr')


class TestSurveyReversibilityValue:
    '''
    Tests to enforce the contract with survey password question encrypted values
    '''
    _key = encryption.get_encryption_key('value', None)

    def test_encrypt_empty_string(self):
        assert encryption.encrypt_value('') == ''
        # the reverse, decryption, does not work

    def test_encrypt_encryption_key(self):
        assert encryption.encrypt_value('$encrypted$') == '$encrypted$'
        # the reverse, decryption, does not work

    def test_encrypt_empty_string_twice(self):
        # Encryption is idempotent
        val = encryption.encrypt_value('foobar')
        val2 = encryption.encrypt_value(val)
        assert encryption.decrypt_value(self._key, val2) == 'foobar'
