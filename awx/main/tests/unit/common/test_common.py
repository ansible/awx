from awx.conf.models import Setting
from awx.main.utils import common


def test_encrypt_field():
    field = Setting(pk=123, value='ANSIBLE')
    encrypted = common.encrypt_field(field, 'value')
    assert encrypted == '$encrypted$AES$Ey83gcmMuBBT1OEq2lepnw=='
    assert common.decrypt_field(field, 'value') == 'ANSIBLE'


def test_encrypt_field_without_pk():
    field = Setting(value='ANSIBLE')
    encrypted = common.encrypt_field(field, 'value')
    assert encrypted == '$encrypted$AES$8uIzEoGyY6QJwoTWbMFGhw=='
    assert common.decrypt_field(field, 'value') == 'ANSIBLE'


def test_encrypt_subfield():
    field = Setting(value={'name': 'ANSIBLE'})
    encrypted = common.encrypt_field(field, 'value', subfield='name')
    assert encrypted == '$encrypted$AES$8uIzEoGyY6QJwoTWbMFGhw=='
    assert common.decrypt_field(field, 'value', subfield='name') == 'ANSIBLE'


def test_encrypt_field_with_ask():
    encrypted = common.encrypt_field(Setting(value='ASK'), 'value', ask=True)
    assert encrypted == 'ASK'


def test_encrypt_field_with_empty_value():
    encrypted = common.encrypt_field(Setting(value=None), 'value')
    assert encrypted is None
