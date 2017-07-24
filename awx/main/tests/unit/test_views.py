import pytest
import mock

# Django REST Framework
from rest_framework import exceptions

# AWX
from awx.main.views import ApiErrorView
from awx.api.views import JobList


HTTP_METHOD_NAMES = [
    'get',
    'post',
    'put',
    'patch',
    'delete',
    'head',
    'options',
    'trace',
]


@pytest.fixture
def api_view_obj_fixture():
    return ApiErrorView()


@pytest.mark.parametrize('method_name', HTTP_METHOD_NAMES)
def test_exception_view_allow_http_methods(method_name):
    assert hasattr(ApiErrorView, method_name)


@pytest.mark.parametrize('method_name', HTTP_METHOD_NAMES)
def test_exception_view_raises_exception(api_view_obj_fixture, method_name):
    request_mock = mock.MagicMock()
    with pytest.raises(exceptions.APIException):
        getattr(api_view_obj_fixture, method_name)(request_mock)


@pytest.mark.parametrize('version, supports_post', [(1, True), (2, False)])
def test_disable_post_on_v2_jobs_list(version, supports_post):
    job_list = JobList()
    job_list.request = mock.MagicMock()
    with mock.patch('awx.api.views.get_request_version', return_value=version):
        assert ('POST' in job_list.allowed_methods) == supports_post
