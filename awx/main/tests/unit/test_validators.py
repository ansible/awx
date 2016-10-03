from django.core.exceptions import ValidationError
from awx.main.validators import (
    validate_private_key,
    validate_certificate,
    validate_ssh_private_key,
)
from awx.main.tests.data.ssh import (
    TEST_SSH_RSA1_KEY_DATA,
    TEST_SSH_KEY_DATA,
    TEST_SSH_KEY_DATA_LOCKED,
    TEST_OPENSSH_KEY_DATA,
    TEST_OPENSSH_KEY_DATA_LOCKED,
    TEST_SSH_CERT_KEY,
)

import pytest

def test_valid_rsa_key():
    valid_key = TEST_SSH_KEY_DATA
    pem_objects = validate_private_key(valid_key)
    assert pem_objects[0]['key_type'] == 'rsa'
    assert not pem_objects[0]['key_enc']
    with pytest.raises(ValidationError):
        validate_certificate(valid_key)
    pem_objects = validate_ssh_private_key(valid_key)
    assert pem_objects[0]['key_type'] == 'rsa'
    assert not pem_objects[0]['key_enc']

def test_valid_locked_rsa_key():
    valid_key = TEST_SSH_KEY_DATA_LOCKED
    pem_objects = validate_private_key(valid_key)
    assert pem_objects[0]['key_type'] == 'rsa'
    assert pem_objects[0]['key_enc']
    with pytest.raises(ValidationError):
        validate_certificate(valid_key)
    pem_objects = validate_ssh_private_key(valid_key)
    assert pem_objects[0]['key_type'] == 'rsa'
    assert pem_objects[0]['key_enc']

def test_invalid_rsa_key():
    invalid_key = TEST_SSH_KEY_DATA.replace('-----END', '----END')
    with pytest.raises(ValidationError):
        validate_private_key(invalid_key)
    with pytest.raises(ValidationError):
        validate_certificate(invalid_key)
    with pytest.raises(ValidationError):
        validate_ssh_private_key(invalid_key)

def test_valid_openssh_key():
    valid_key = TEST_OPENSSH_KEY_DATA
    pem_objects = validate_private_key(valid_key)
    assert pem_objects[0]['key_type'] == 'ed25519'
    assert not pem_objects[0]['key_enc']
    with pytest.raises(ValidationError):
        validate_certificate(valid_key)
    pem_objects = validate_ssh_private_key(valid_key)
    assert pem_objects[0]['key_type'] == 'ed25519'
    assert not pem_objects[0]['key_enc']

def test_valid_locked_openssh_key():
    valid_key = TEST_OPENSSH_KEY_DATA_LOCKED
    pem_objects = validate_private_key(valid_key)
    assert pem_objects[0]['key_type'] == 'ed25519'
    assert pem_objects[0]['key_enc']
    with pytest.raises(ValidationError):
        validate_certificate(valid_key)
    pem_objects = validate_ssh_private_key(valid_key)
    assert pem_objects[0]['key_type'] == 'ed25519'
    assert pem_objects[0]['key_enc']
    
def test_valid_rsa1_key():
    valid_key = TEST_SSH_RSA1_KEY_DATA
    pem_objects = validate_ssh_private_key(valid_key)
    assert pem_objects[0]['key_type'] == 'rsa1'
    assert not pem_objects[0]['key_enc']
    with pytest.raises(ValidationError):
        validate_certificate(valid_key)
    pem_objects = validate_ssh_private_key(valid_key)
    assert pem_objects[0]['key_type'] == 'rsa1'
    assert not pem_objects[0]['key_enc']

def test_cert_with_key():
    cert_with_key = TEST_SSH_CERT_KEY
    with pytest.raises(ValidationError):
        validate_private_key(cert_with_key)
    with pytest.raises(ValidationError):
        validate_certificate(cert_with_key)
    pem_objects = validate_ssh_private_key(cert_with_key)
    assert pem_objects[0]['type'] == 'CERTIFICATE'
    assert pem_objects[1]['key_type'] == 'rsa'
    assert not pem_objects[1]['key_enc']
