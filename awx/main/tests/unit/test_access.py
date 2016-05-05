from django.contrib.auth.models import User
from awx.main.access import (
    BaseAccess,
    check_superuser,
)


def test_superuser(mocker):
    user = mocker.MagicMock(spec=User, id=1, is_superuser=True)
    access = BaseAccess(user)

    can_add = check_superuser(BaseAccess.can_add)
    assert can_add(access, None) is True

def test_not_superuser(mocker):
    user = mocker.MagicMock(spec=User, id=1, is_superuser=False)
    access = BaseAccess(user)

    can_add = check_superuser(BaseAccess.can_add)
    assert can_add(access, None) is False

