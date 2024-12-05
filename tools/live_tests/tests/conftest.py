import pytest

from awx.main.tests.functional.conftest import _request

from awx.main.models import User


# # this is done to turn off the pytest-django test database
# @pytest.fixture(scope='session')
# def django_db_setup():
#     pass


@pytest.fixture
def admin_user():
    user, _ = User.objects.get_or_create(username='admin', is_superuser=True)
    return user


# TODO: do this better somehow


@pytest.fixture
def post():
    return _request('post')


@pytest.fixture
def get():
    return _request('get')


@pytest.fixture
def put():
    return _request('put')


@pytest.fixture
def patch():
    return _request('patch')


@pytest.fixture
def delete():
    return _request('delete')


@pytest.fixture
def head():
    return _request('head')


@pytest.fixture
def options():
    return _request('options')
