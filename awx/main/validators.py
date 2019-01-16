# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import base64
import re

# Django
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

# REST framework
from rest_framework.serializers import ValidationError as RestValidationError
from rest_framework.exceptions import ParseError

# AWX
from awx.main.utils import parse_yaml_or_json


def validate_pem(data, min_keys=0, max_keys=None, min_certs=0, max_certs=None):
    """
    Validate the given PEM data is valid and contains the required numbers of
    keys and certificates.

    Return a list of PEM objects, where each object is a dict with the following
    keys:
      - 'all': The entire string for the PEM object including BEGIN/END lines.
      - 'type': The type of PEM object ('PRIVATE KEY' or 'CERTIFICATE').
      - 'data': The string inside the BEGIN/END lines.
      - 'b64': Key/certificate as a base64-encoded string.
      - 'bin': Key/certificate as bytes.
      - 'key_type': Only when type == 'PRIVATE KEY', one of 'rsa', 'dsa',
        'ecdsa', 'ed25519' or 'rsa1'.
      - 'key_enc': Only when type == 'PRIVATE KEY', boolean indicating if key is
        encrypted.
    """

    # Map the X in BEGIN X PRIVATE KEY to the key type (ssh-keygen -t).
    # Tower jobs using OPENSSH format private keys may still fail if the
    # system SSH implementation lacks support for this format.
    private_key_types = {
        'RSA': 'rsa',
        'DSA': 'dsa',
        'EC': 'ecdsa',
        'OPENSSH': 'ed25519',
        '': 'rsa1',
    }

    # Build regular expressions for matching each object in the PEM file.
    pem_obj_re = re.compile(
        r'^(?P<dashes>-{4,}) *BEGIN (?P<type>[A-Z ]+?) *(?P=dashes)' +
        r'\s*(?P<data>.+?)\s*' +
        r'(?P=dashes) *END (?P=type) *(?P=dashes)' +
        r'(?P<next>.*?)$', re.DOTALL
    )
    pem_obj_header_re = re.compile(r'^(.+?):\s*?(.+?)(\\??)$')

    pem_objects = []
    key_count, cert_count = 0, 0

    # Strip leading whitespaces at the start of the PEM data
    data = data.lstrip()

    while data:
        match = pem_obj_re.match(data)
        if not match:
            raise ValidationError(_('Invalid certificate or key: %s...') % data[:100])

        # The rest of the PEM data to process
        data = match.group('next').lstrip()

        # Check PEM object type, check key type if private key.
        pem_obj_info = {}
        pem_obj_info['all'] = match.group(0)
        pem_obj_info['type'] = pem_obj_type = match.group('type')
        if pem_obj_type.endswith('PRIVATE KEY'):
            key_count += 1
            pem_obj_info['type'] = 'PRIVATE KEY'
            key_type = pem_obj_type.replace('ENCRYPTED PRIVATE KEY', '').replace('PRIVATE KEY', '').strip()
            try:
                pem_obj_info['key_type'] = private_key_types[key_type]
            except KeyError:
                raise ValidationError(_('Invalid private key: unsupported type "%s"') % key_type)
        elif pem_obj_type == 'CERTIFICATE':
            cert_count += 1
        else:
            raise ValidationError(_('Unsupported PEM object type: "%s"') % pem_obj_type)

        # Ensure that this PEM object is valid base64 data.
        pem_obj_info['data'] = match.group('data')
        base64_data = ''
        line_continues = False
        for line in pem_obj_info['data'].splitlines():
            line = line.strip()
            if not line:
                continue
            if line_continues:
                line_continues = line.endswith('\\')
                continue
            line_match = pem_obj_header_re.match(line)
            if line_match:
                line_continues = line.endswith('\\')
                continue
            base64_data += line
        try:
            decoded_data = base64.b64decode(base64_data)
            if not decoded_data:
                raise TypeError
            pem_obj_info['b64'] = base64_data
            pem_obj_info['bin'] = decoded_data
        except TypeError:
            raise ValidationError(_('Invalid base64-encoded data'))

        # If private key, check whether it is encrypted.
        if pem_obj_info.get('key_type', '') == 'ed25519':
            # See https://github.com/openssh/openssh-portable/blob/master/sshkey.c#L3218
            # Decoded key data starts with magic string (null-terminated), four byte
            # length field, followed by the ciphername -- if ciphername is anything
            # other than 'none' the key is encrypted.
            pem_obj_info['key_enc'] = not bool(pem_obj_info['bin'].startswith(b'openssh-key-v1\x00\x00\x00\x00\x04none'))
        elif match.group('type') == 'ENCRYPTED PRIVATE KEY':
            pem_obj_info['key_enc'] = True
        elif pem_obj_info.get('key_type', ''):
            pem_obj_info['key_enc'] = bool('ENCRYPTED' in pem_obj_info['data'])

        pem_objects.append(pem_obj_info)

    # Validate that the number of keys and certs provided are within the limits.
    key_count_dict = dict(min_keys=min_keys, max_keys=max_keys, key_count=key_count)
    if key_count < min_keys:
        if min_keys == 1:
            if max_keys == min_keys:
                raise ValidationError(_('Exactly one private key is required.'))
            else:
                raise ValidationError(_('At least one private key is required.'))
        else:
            raise ValidationError(_('At least %(min_keys)d private keys are required, only %(key_count)d provided.') % key_count_dict)
    elif max_keys is not None and key_count > max_keys:
        if max_keys == 1:
            raise ValidationError(_('Only one private key is allowed, %(key_count)d provided.') % key_count_dict)
        else:
            raise ValidationError(_('No more than %(max_keys)d private keys are allowed, %(key_count)d provided.') % key_count_dict)
    cert_count_dict = dict(min_certs=min_certs, max_certs=max_certs, cert_count=cert_count)
    if cert_count < min_certs:
        if min_certs == 1:
            if max_certs == min_certs:
                raise ValidationError(_('Exactly one certificate is required.'))
            else:
                raise ValidationError(_('At least one certificate is required.'))
        else:
            raise ValidationError(_('At least %(min_certs)d certificates are required, only %(cert_count)d provided.') % cert_count_dict)
    elif max_certs is not None and cert_count > max_certs:
        if max_certs == 1:
            raise ValidationError(_('Only one certificate is allowed, %(cert_count)d provided.') % cert_count_dict)
        else:
            raise ValidationError(_('No more than %(max_certs)d certificates are allowed, %(cert_count)d provided.') % cert_count_dict)

    return pem_objects


def validate_private_key(data):
    """
    Validate that data contains exactly one private key.
    """
    return validate_pem(data, min_keys=1, max_keys=1, max_certs=0)


def validate_certificate(data):
    """
    Validate that data contains one or more certificates. Adds BEGIN/END lines
    if necessary.
    """
    if 'BEGIN ' not in data:
        data = "-----BEGIN CERTIFICATE-----\n{}".format(data)
    if 'END ' not in data:
        data = "{}\n-----END CERTIFICATE-----\n".format(data)
    return validate_pem(data, max_keys=0, min_certs=1)


def validate_ssh_private_key(data):
    """
    Validate that data contains at least one private key and optionally
    certificates; should handle any valid options for ssh_private_key on a
    credential.
    """
    return validate_pem(data, min_keys=1)


def vars_validate_or_raise(vars_str):
    """
    Validate that fields like extra_vars or variables on resources like
    job templates, inventories, or hosts are either an acceptable
    blank string, or are valid JSON or YAML dict
    """
    try:
        parse_yaml_or_json(vars_str, silent_failure=False)
        return vars_str
    except ParseError as e:
        raise RestValidationError(str(e))
