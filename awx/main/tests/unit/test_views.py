import pytest
from unittest import mock

# Django REST Framework
from rest_framework import exceptions
from rest_framework.generics import ListAPIView

# AWX
from awx.main.views import ApiErrorView
from awx.api.views import JobList
from awx.api.generics import ListCreateAPIView, SubListAttachDetachAPIView


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


def test_disable_post_on_v2_jobs_list():
    job_list = JobList()
    job_list.request = mock.MagicMock()
    assert ('POST' in job_list.allowed_methods) is False


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


def test_global_creation_always_possible(all_views):
    """To not make life very difficult for clients, this test
    asserts that all creatable resources can be created by
    POSTing to the global resource list
    """
    views_by_model = {}
    for View in all_views:
        if not getattr(View, 'deprecated', False) and issubclass(View, ListAPIView) and hasattr(View, 'model'):
            views_by_model.setdefault(View.model, []).append(View)
    for model, views in views_by_model.items():
        creatable = False
        global_view = None
        creatable_view = None
        for View in views:
            if '{}ListView'.format(model.__name__) == View.__name__:
                global_view = View
            if issubclass(View, ListCreateAPIView) and not issubclass(View, SubListAttachDetachAPIView):
                creatable = True
                creatable_view = View
        if not creatable or not global_view:
            continue
        assert 'POST' in global_view().allowed_methods, (
            'Resource {} should be creatable in global list view {}. '
            'Can be created now in {}'.format(model, global_view, creatable_view)
        )
