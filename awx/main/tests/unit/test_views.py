import pytest
import mock

# Django REST Framework
from rest_framework import exceptions
from rest_framework.generics import ListAPIView

# AWX
from awx.main.views import ApiErrorView
from awx.api.views import JobList, InventorySourceList


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


@pytest.mark.parametrize('version, supports_post', [(1, False), (2, True)])
def test_disable_post_on_v1_inventory_source_list(version, supports_post):
    inv_source_list = InventorySourceList()
    inv_source_list.request = mock.MagicMock()
    with mock.patch('awx.api.views.get_request_version', return_value=version):
        assert ('POST' in inv_source_list.allowed_methods) == supports_post


def test_views_have_search_fields(all_views):
    # Gather any views that don't have search fields defined
    views_missing_search = []
    for View in all_views:
        if not issubclass(View, ListAPIView):
            continue
        view = View()
        if not hasattr(view, 'search_fields') or len(view.search_fields) == 0:
            views_missing_search.append(view)

    if views_missing_search:
        raise Exception('{} views do not have search fields defined:\n{}'.format(
            len(views_missing_search),
            '\n'.join([
                v.__class__.__name__ + ' (model: {})'.format(getattr(v, 'model', type(None)).__name__)
                for v in views_missing_search
            ]))
        )
