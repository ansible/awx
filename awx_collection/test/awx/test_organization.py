from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
import random

from awx.main.models import Organization, Credential, CredentialType


@pytest.mark.django_db
def test_create_organization(run_module, admin_user):

    module_args = {
        'name': 'foo',
        'description': 'barfoo',
        'state': 'present',
        'max_hosts': '0',
        'controller_host': None,
        'controller_username': None,
        'controller_password': None,
        'validate_certs': None,
        'controller_oauthtoken': None,
        'controller_config_file': None,
    }

    result = run_module('organization', module_args, admin_user)
    assert result.get('changed'), result

    org = Organization.objects.get(name='foo')
    assert result == {"name": "foo", "changed": True, "id": org.id, "invocation": {"module_args": module_args}}

    assert org.description == 'barfoo'


@pytest.mark.django_db
def test_galaxy_credential_order(run_module, admin_user):
    org = Organization.objects.create(name='foo')
    cred_type = CredentialType.defaults['galaxy_api_token']()
    cred_type.save()

    cred_ids = []
    for number in range(1, 10):
        new_cred = Credential.objects.create(name=f"Galaxy Credential {number}", credential_type=cred_type, organization=org, inputs={'url': 'www.redhat.com'})
        cred_ids.append(new_cred.id)

    random.shuffle(cred_ids)

    module_args = {
        'name': 'foo',
        'state': 'present',
        'controller_host': None,
        'controller_username': None,
        'controller_password': None,
        'validate_certs': None,
        'controller_oauthtoken': None,
        'controller_config_file': None,
        'galaxy_credentials': cred_ids,
    }

    result = run_module('organization', module_args, admin_user)
    print(result)
    assert result['changed'] is True

    cred_order_in_org = []
    for a_cred in org.galaxy_credentials.all():
        cred_order_in_org.append(a_cred.id)

    assert cred_order_in_org == cred_ids

    # Shuffle them up and try again to make sure a new order is honored
    random.shuffle(cred_ids)

    module_args = {
        'name': 'foo',
        'state': 'present',
        'controller_host': None,
        'controller_username': None,
        'controller_password': None,
        'validate_certs': None,
        'controller_oauthtoken': None,
        'controller_config_file': None,
        'galaxy_credentials': cred_ids,
    }

    result = run_module('organization', module_args, admin_user)
    assert result['changed'] is True

    cred_order_in_org = []
    for a_cred in org.galaxy_credentials.all():
        cred_order_in_org.append(a_cred.id)

    assert cred_order_in_org == cred_ids
