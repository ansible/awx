import pytest

from awx.conf.migrations._ldap_group_type import fill_ldap_group_type_params
from awx.conf.models import Setting

from django.apps import apps


@pytest.mark.django_db
def test_fill_group_type_params_no_op():
    fill_ldap_group_type_params(apps, 'dont-use-me')
    assert Setting.objects.count() == 0


@pytest.mark.django_db
def test_keep_old_setting_with_default_value():
    Setting.objects.create(key='AUTH_LDAP_GROUP_TYPE', value={'name_attr': 'cn', 'member_attr': 'member'})
    fill_ldap_group_type_params(apps, 'dont-use-me')
    assert Setting.objects.count() == 1
    s = Setting.objects.first()
    assert s.value == {'name_attr': 'cn', 'member_attr': 'member'}


# NOTE: would be good to test the removal of attributes by migration
# but this requires fighting with the validator and is not done here
