# -*- coding: utf-8 -*-

from awx.main.models import Credential, CredentialType


def test_unique_hash_with_unicode():
    ct = CredentialType(name=u'Väult', kind='vault')
    cred = Credential(
        id=4,
        name=u'Iñtërnâtiônàlizætiøn',
        credential_type=ct,
        inputs={
            u'vault_id': u'🐉🐉🐉'
        },
        credential_type_id=42
    )
    assert cred.unique_hash(display=True) == u'Väult (id=🐉🐉🐉)'


def test_custom_cred_with_empty_encrypted_field():
    ct = CredentialType(
        name='My Custom Cred',
        kind='custom',
        inputs={
            'fields': [{
                'id': 'some_field',
                'label': 'My Field',
                'secret': True
            }]
        }
    )
    cred = Credential(
        id=4,
        name='Testing 1 2 3',
        credential_type=ct,
        inputs={}
    )
    assert cred.encrypt_field('some_field', None) is None
