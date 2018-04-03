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
