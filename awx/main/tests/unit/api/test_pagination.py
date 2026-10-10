from unittest.mock import patch, MagicMock

from awx.api.pagination import (
    ActivityStreamPaginator,
    ActivityStreamPagination,
    DisabledPaginator,
    JobPaginator,
    JobPagination,
    UnifiedJobPaginator,
    UnifiedJobPagination,
)


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

    def test_normal_request_preserves_activity_stream_paginator(self):
        pagination = ActivityStreamPagination()
        request = MagicMock()
        request.query_params = {}

        with patch('rest_framework.pagination.PageNumberPagination.paginate_queryset', return_value=[]):
            pagination.paginate_queryset(MagicMock(), request)

        assert pagination.count_disabled is False
        assert pagination.django_paginator_class is ActivityStreamPaginator

    def test_count_disabled_restores_activity_stream_paginator(self):
        pagination = ActivityStreamPagination()
        request = MagicMock()
        request.query_params = {'count_disabled': 'true'}

        with patch('rest_framework.pagination.PageNumberPagination.paginate_queryset', return_value=[]):
            pagination.paginate_queryset(MagicMock(), request)

        assert pagination.count_disabled is True
        assert pagination.django_paginator_class is ActivityStreamPaginator

    def test_count_disabled_temporarily_uses_disabled_paginator(self):
        pagination = ActivityStreamPagination()
        request = MagicMock()
        request.query_params = {'count_disabled': 'true'}
        captured_class = {}

        def capture_paginator_class(self_inner, queryset, request, **kwargs):
            captured_class['during'] = pagination.django_paginator_class

        with patch('rest_framework.pagination.PageNumberPagination.paginate_queryset', capture_paginator_class):
            pagination.paginate_queryset(MagicMock(), request)

        assert captured_class['during'] is DisabledPaginator
        assert pagination.django_paginator_class is ActivityStreamPaginator


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


class TestJobPaginator:
    def test_count_uses_primary_key_subquery(self):
        object_list = MagicMock()
        object_list.order_by.return_value.values.return_value = "visible_pks"
        object_list.model.objects.filter.return_value.count.return_value = 713

        paginator = JobPaginator(object_list=object_list, per_page=25)

        assert paginator.count == 713
        object_list.order_by.assert_called_once_with()
        object_list.order_by.return_value.values.assert_called_once_with("pk")
        object_list.model.objects.filter.assert_called_once_with(pk__in="visible_pks")

    def test_count_is_cached(self):
        object_list = MagicMock()
        object_list.order_by.return_value.values.return_value = "visible_pks"
        object_list.model.objects.filter.return_value.count.return_value = 500
        paginator = JobPaginator(object_list=object_list, per_page=25)

        _ = paginator.count
        _ = paginator.count

        object_list.model.objects.filter.assert_called_once_with(pk__in="visible_pks")


class TestJobPagination:
    def test_default_paginator_class(self):
        pagination = JobPagination()
        assert pagination.django_paginator_class is JobPaginator


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
