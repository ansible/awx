import pytest

from awx.main.tests.functional.conftest import post, get, put, patch, delete, head, options  # noqa

from awx.main.models import User


@pytest.fixture
def admin_user():
    user, _ = User.objects.get_or_create(username='admin', is_superuser=True)
    return user
