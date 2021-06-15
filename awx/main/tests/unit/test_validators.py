from django.core.exceptions import ValidationError
from awx.main.validators import (
    validate_private_key,
    validate_certificate,
    validate_ssh_private_key,
    vars_validate_or_raise,
    validate_container_image_name,
)
from awx.main.tests.data.ssh import (
    TEST_SSH_RSA1_KEY_DATA,
    TEST_SSH_KEY_DATA,
    TEST_SSH_KEY_DATA_LOCKED,
    TEST_OPENSSH_KEY_DATA,
    TEST_OPENSSH_KEY_DATA_LOCKED,
    TEST_SSH_CERT_KEY,
    TEST_CATTED_SSH_KEY_DATA,
)
from rest_framework.serializers import ValidationError as RestValidationError

import pytest


def test_invalid_keys():
    invalid_keys = [
        "---BEGIN FOO -----foobar-----END FOO----",
        "-----BEGIN FOO---foobar-----END FOO----",
        "-----BEGIN FOO-----foobar---END FOO----",
        "-----  BEGIN FOO  ----- foobar -----  FAIL FOO  ----",
        "-----  FAIL FOO ----- foobar -----  END FOO  ----",
        "----BEGIN FOO----foobar----END BAR----",
    ]
    for invalid_key in invalid_keys:
        with pytest.raises(ValidationError):
            validate_private_key(invalid_key)
        with pytest.raises(ValidationError):
            validate_certificate(invalid_key)
        with pytest.raises(ValidationError):
            validate_ssh_private_key(invalid_key)


def test_invalid_rsa_key():
    invalid_key = TEST_SSH_KEY_DATA.replace('-----END', '----END')
    with pytest.raises(ValidationError):
        validate_private_key(invalid_key)
    with pytest.raises(ValidationError):
        validate_certificate(invalid_key)
    with pytest.raises(ValidationError):
        validate_ssh_private_key(invalid_key)


def test_valid_catted_rsa_key():
    valid_key = TEST_CATTED_SSH_KEY_DATA
    pem_objects = validate_private_key(valid_key)
    assert pem_objects[0]['key_type'] == 'rsa'
    assert not pem_objects[0]['key_enc']
    with pytest.raises(ValidationError):
        validate_certificate(valid_key)
    pem_objects = validate_ssh_private_key(valid_key)
    assert pem_objects[0]['key_type'] == 'rsa'
    assert not pem_objects[0]['key_enc']


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


@pytest.mark.parametrize(
    "var_str",
    [
        '{"a": "b"}',
        '---\na: b\nc: d',
        '',
        '""',
    ],
)
def test_valid_vars(var_str):
    vars_validate_or_raise(var_str)


@pytest.mark.parametrize(
    "var_str",
    [
        '["a": "b"]',
        '["a", "b"]',
        "('a=4', 'c=5')",
        '"',
        "''",
        "5",
        "6.74",
        "hello",
        "OrderedDict([('a', 'b')])",
        "True",
        "False",
    ],
)
def test_invalid_vars(var_str):
    with pytest.raises(RestValidationError):
        vars_validate_or_raise(var_str)


@pytest.mark.parametrize(
    ("image_name", "is_valid"),
    [
        ("localhost", True),
        ("short", True),
        ("simple/name", True),
        ("ab/ab/ab/ab", True),
        ("foo.com/", False),
        ("", False),
        ("localhost/foo", True),
        ("3asdasdf3", True),
        ("xn--7o8h.com/myimage", True),
        ("Asdf.com/foo/bar", True),
        ("Foo/FarB", False),
        ("registry.com:8080/myapp:tag", True),
        ("registry.com:8080/myapp@sha256:be178c0543eb17f5f3043021c9e5fcf30285e557a4fc309cce97ff9ca6182912", True),
        ("registry.com:8080/myapp:tag2@sha256:be178c0543eb17f5f3043021c9e5fcf30285e557a4fc309cce97ff9ca6182912", True),
        ("registry.com:8080/myapp@sha256:badbadbadbad", False),
        ("registry.com:8080/myapp:invalid~tag", False),
        ("bad_hostname.com:8080/myapp:tag", False),
        ("localhost:8080@sha256:be178c0543eb17f5f3043021c9e5fcf30285e557a4fc309cce97ff9ca6182912", True),
        ("localhost:8080/name@sha256:be178c0543eb17f5f3043021c9e5fcf30285e557a4fc309cce97ff9ca6182912", True),
        ("localhost:http/name@sha256:be178c0543eb17f5f3043021c9e5fcf30285e557a4fc309cce97ff9ca6182912", False),
        ("localhost@sha256:be178c0543eb17f5f3043021c9e5fcf30285e557a4fc309cce97ff9ca6182912", True),
        ("registry.com:8080/myapp@bad", False),
        ("registry.com:8080/myapp@2bad", False),
    ],
)
def test_valid_container_image_name(image_name, is_valid):
    if is_valid:
        validate_container_image_name(image_name)
    else:
        with pytest.raises(ValidationError):
            validate_container_image_name(image_name)
