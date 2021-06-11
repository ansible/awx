import pytest


from awxkit.api.pages import credentials
from awxkit.utils import PseudoNamespace


def set_config_cred_to_desired(config, location):
    split = location.split('.')
    config_ref = config.credentials
    for _location in split[:-1]:
        setattr(config_ref, _location, PseudoNamespace())
        config_ref = config_ref[_location]
    setattr(config_ref, split[-1], 'desired')


class MockCredentialType(object):
    def __init__(self, name, kind, managed=True):
        self.name = name
        self.kind = kind
        self.managed = managed


@pytest.mark.parametrize(
    'field, kind, config_cred, desired_field, desired_value',
    [
        ('field', 'ssh', PseudoNamespace(field=123), 'field', 123),
        ('subscription', 'azure', PseudoNamespace(subscription_id=123), 'subscription', 123),
        ('project_id', 'gce', PseudoNamespace(project=123), 'project', 123),
        ('authorize_password', 'net', PseudoNamespace(authorize=123), 'authorize_password', 123),
    ],
)
def test_get_payload_field_and_value_from_config_cred(field, kind, config_cred, desired_field, desired_value):
    ret_field, ret_val = credentials.get_payload_field_and_value_from_kwargs_or_config_cred(field, kind, {}, config_cred)
    assert ret_field == desired_field
    assert ret_val == desired_value


@pytest.mark.parametrize(
    'field, kind, kwargs, desired_field, desired_value',
    [
        ('field', 'ssh', dict(field=123), 'field', 123),
        ('subscription', 'azure', dict(subscription=123), 'subscription', 123),
        ('project_id', 'gce', dict(project_id=123), 'project', 123),
        ('authorize_password', 'net', dict(authorize_password=123), 'authorize_password', 123),
    ],
)
def test_get_payload_field_and_value_from_kwarg(field, kind, kwargs, desired_field, desired_value):
    ret_field, ret_val = credentials.get_payload_field_and_value_from_kwargs_or_config_cred(field, kind, kwargs, PseudoNamespace())
    assert ret_field == desired_field
    assert ret_val == desired_value
