import pytest

import copy
import json

from awx.main.utils.common import (
    model_instance_diff,
    model_to_dict
)


@pytest.mark.django_db
def test_model_to_dict_user(alice):
    username = copy.copy(alice.username)
    password = copy.copy(alice.password)
    output_dict = model_to_dict(alice)
    assert output_dict['username'] == username
    assert output_dict['password'] == 'hidden'
    assert alice.username == username
    assert alice.password == password


@pytest.mark.django_db
def test_model_to_dict_credential(credential):
    name = copy.copy(credential.name)
    inputs = copy.copy(credential.inputs)
    output_dict = model_to_dict(credential)
    assert output_dict['name'] == name
    assert output_dict['inputs'] == 'hidden'
    assert credential.name == name
    assert credential.inputs == inputs


@pytest.mark.django_db
def test_model_to_dict_notification_template(notification_template_with_encrypt):
    old_configuration = copy.deepcopy(notification_template_with_encrypt.notification_configuration)
    output_dict = model_to_dict(notification_template_with_encrypt)
    new_configuration = json.loads(output_dict['notification_configuration'])
    assert notification_template_with_encrypt.notification_configuration == old_configuration
    assert new_configuration['token'] == '$encrypted$'
    assert new_configuration['channels'] == old_configuration['channels']


@pytest.mark.django_db
def test_model_instance_diff(alice, bob):
    alice_name = copy.copy(alice.username)
    alice_pass = copy.copy(alice.password)
    bob_name = copy.copy(bob.username)
    bob_pass = copy.copy(bob.password)
    output_dict = model_instance_diff(alice, bob)
    assert alice_name == alice.username
    assert alice_pass == alice.password
    assert bob_name == bob.username
    assert bob_pass == bob.password
    assert output_dict['username'][0] == alice_name
    assert output_dict['username'][1] == bob_name
    assert output_dict['password'] == ('hidden', 'hidden')
    assert hasattr(alice, 'is_superuser')
    assert hasattr(bob, 'is_superuser')
    assert 'is_superuser' not in output_dict
