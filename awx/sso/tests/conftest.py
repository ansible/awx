import pytest

from django.contrib.auth.models import User

from awx.sso.backends import TACACSPlusBackend
from awx.sso.models import UserEnterpriseAuth


@pytest.fixture
def tacacsplus_backend():
    return TACACSPlusBackend()


@pytest.fixture
def existing_normal_user():
    try:
        user = User.objects.get(username="alice")
    except User.DoesNotExist:
        user = User(username="alice", password="password")
        user.save()
    return user


@pytest.fixture
def existing_tacacsplus_user():
    try:
        user = User.objects.get(username="foo")
    except User.DoesNotExist:
        user = User(username="foo")
        user.set_unusable_password()
        user.save()
        enterprise_auth = UserEnterpriseAuth(user=user, provider='tacacs+')
        enterprise_auth.save()
    return user
