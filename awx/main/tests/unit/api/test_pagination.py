from unittest.mock import patch, MagicMock
import pytest
from django.core.paginator import Paginator as DjangoPaginator
from awx.api.pagination import ActivityStreamPaginator, ActivityStreamPagination, UnifiedJobPaginator, UnifiedJobPagination, DisabledPaginator


class TestActivityStreamPaginator:
    def test_count_uses_unfiltered_table_count(self):
        with patch('awx.api.pagination.ActivityStream') as mock_as:
            mock_as.objects.count.return_value = 713000
            paginator = ActivityStreamPaginator(object_list=[], per_page=25)
            assert paginator.count == 713000
            mock_as.objects.count.assert_called_once()

    def test_count_is_cached(self):
        with patch('awx.api.pagination.ActivityStream') as mock_as:
            mock_as.objects.count.return_value = 500
            paginator = ActivityStreamPaginator(object_list=[], per_page=25)
            _ = paginator.count
            _ = paginator.count
            mock_as.objects.count.assert_called_once()


class TestActivityStreamPagination:
    def test_default_paginator_class(self):
        pagination = ActivityStreamPagination()
        assert pagination.django_paginator_class is ActivityStreamPaginator


@pytest.mark.parametrize(
    'pagination_class, fast_paginator_class',
    [
        (UnifiedJobPagination, UnifiedJobPaginator),
        (ActivityStreamPagination, ActivityStreamPaginator),
    ],
    ids=['UnifiedJobPagination', 'ActivityStreamPagination'],
)
def test_filtered_request_uses_accurate_paginator(pagination_class, fast_paginator_class):
    pagination = pagination_class()
    request = MagicMock()
    request.query_params = {'status': 'canceled'}
    captured_class = {}

    def capture_paginator_class(self_inner, queryset, request, **kwargs):
        captured_class['during'] = pagination.django_paginator_class

    with patch('rest_framework.pagination.PageNumberPagination.paginate_queryset', capture_paginator_class):
        pagination.paginate_queryset(MagicMock(), request)

    assert captured_class['during'] is DjangoPaginator
    assert pagination.django_paginator_class is fast_paginator_class


class TestUnifiedJobPaginator:
    def test_count_uses_unfiltered_table_count(self):
        with patch('awx.api.pagination.UnifiedJob') as mock_uj:
            mock_uj.objects.count.return_value = 42000
            paginator = UnifiedJobPaginator(object_list=[], per_page=25)
            assert paginator.count == 42000
            mock_uj.objects.count.assert_called_once()

    def test_count_is_cached(self):
        with patch('awx.api.pagination.UnifiedJob') as mock_uj:
            mock_uj.objects.count.return_value = 500
            paginator = UnifiedJobPaginator(object_list=[], per_page=25)
            _ = paginator.count
            _ = paginator.count
            mock_uj.objects.count.assert_called_once()


class TestUnifiedJobPagination:
    def test_default_paginator_class(self):
        pagination = UnifiedJobPagination()
        assert pagination.django_paginator_class is UnifiedJobPaginator

    def test_normal_request_preserves_unified_job_paginator(self):
        pagination = UnifiedJobPagination()
        request = MagicMock()
        request.query_params = {}

        with patch('rest_framework.pagination.PageNumberPagination.paginate_queryset', return_value=[]):
            pagination.paginate_queryset(MagicMock(), request)

        assert pagination.count_disabled is False
        assert pagination.django_paginator_class is UnifiedJobPaginator

    def test_count_disabled_restores_unified_job_paginator(self):
        pagination = UnifiedJobPagination()
        request = MagicMock()
        request.query_params = {'count_disabled': 'true'}

        with patch('rest_framework.pagination.PageNumberPagination.paginate_queryset', return_value=[]):
            pagination.paginate_queryset(MagicMock(), request)

        assert pagination.count_disabled is True
        assert pagination.django_paginator_class is UnifiedJobPaginator

    def test_count_disabled_temporarily_uses_disabled_paginator(self):
        pagination = UnifiedJobPagination()
        request = MagicMock()
        request.query_params = {'count_disabled': 'true'}
        captured_class = {}

        def capture_paginator_class(self_inner, queryset, request, **kwargs):
            captured_class['during'] = pagination.django_paginator_class

        with patch('rest_framework.pagination.PageNumberPagination.paginate_queryset', capture_paginator_class):
            pagination.paginate_queryset(MagicMock(), request)

        assert captured_class['during'] is DisabledPaginator
        assert pagination.django_paginator_class is UnifiedJobPaginator

    def test_order_by_and_pagination_params_do_not_trigger_accurate_paginator(self):
        pagination = UnifiedJobPagination()
        request = MagicMock()
        request.query_params = {'order_by': '-finished', 'page': '1', 'page_size': '10', 'no_truncate': '1', 'limit': '5', 'validate': '1'}
        captured_class = {}

        def capture_paginator_class(self_inner, queryset, request, **kwargs):
            captured_class['during'] = pagination.django_paginator_class

        with patch('rest_framework.pagination.PageNumberPagination.paginate_queryset', capture_paginator_class):
            pagination.paginate_queryset(MagicMock(), request)

        assert captured_class['during'] is UnifiedJobPaginator

    def test_search_and_type_params_trigger_accurate_paginator(self):
        # 'search' and 'type' are reserved names FieldLookupBackend excludes from
        # field-lookup parsing, but they still filter results via other backends.
        pagination = UnifiedJobPagination()
        request = MagicMock()
        request.query_params = {'search': 'foo'}
        captured_class = {}

        def capture_paginator_class(self_inner, queryset, request, **kwargs):
            captured_class['during'] = pagination.django_paginator_class

        with patch('rest_framework.pagination.PageNumberPagination.paginate_queryset', capture_paginator_class):
            pagination.paginate_queryset(MagicMock(), request)

        assert captured_class['during'] is DjangoPaginator

    def test_view_specific_reserved_names_do_not_trigger_accurate_paginator(self):
        # UnifiedJobExcludeMixin reserves 'exclude' for unified job views.
        class FakeView:
            rest_filters_reserved_names = ('exclude',)

        pagination = UnifiedJobPagination()
        request = MagicMock()
        request.query_params = {'exclude': 'artifacts'}
        captured_class = {}

        def capture_paginator_class(self_inner, queryset, request, **kwargs):
            captured_class['during'] = pagination.django_paginator_class

        with patch('rest_framework.pagination.PageNumberPagination.paginate_queryset', capture_paginator_class):
            pagination.paginate_queryset(MagicMock(), request, view=FakeView())

        assert captured_class['during'] is UnifiedJobPaginator
