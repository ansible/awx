from unittest import mock
import pytest


@pytest.fixture
def get_related_assert():
    def fn(model_obj, related, resource_name, related_resource_name):
        assert related_resource_name in related
        assert related[related_resource_name] == '/api/v2/%s/%d/%s/' % (resource_name, model_obj.pk, related_resource_name)
    return fn


@pytest.fixture
def get_related_mock_and_run():
    def fn(serializer_class, model_obj):
        serializer = serializer_class()
        related = serializer.get_related(model_obj)
        return related
    return fn


@pytest.fixture
def test_get_related(get_related_assert, get_related_mock_and_run):
    def fn(serializer_class, model_obj, resource_name, related_resource_name):
        related = get_related_mock_and_run(serializer_class, model_obj)
        get_related_assert(model_obj, related, resource_name, related_resource_name)
        return related
    return fn


@pytest.fixture
def get_summary_fields_assert():
    def fn(summary, summary_field_name):
        assert summary_field_name in summary
    return fn


@pytest.fixture
def get_summary_fields_mock_and_run():
    def fn(serializer_class, model_obj):
        serializer = serializer_class()
        serializer.show_capabilities = []
        serializer.context['view'] = mock.Mock(kwargs={})
        return serializer.get_summary_fields(model_obj)
    return fn


@pytest.fixture
def test_get_summary_fields(get_summary_fields_mock_and_run, get_summary_fields_assert):
    def fn(serializer_class, model_obj, summary_field_name):
        summary = get_summary_fields_mock_and_run(serializer_class, model_obj)
        get_summary_fields_assert(summary, summary_field_name)
        return summary
    return fn
