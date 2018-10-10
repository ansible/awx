# AWX
from awx.api import serializers
from awx.main.models import UnifiedJob, UnifiedJobTemplate

# DRF
from rest_framework.generics import ListAPIView


def test_unified_template_field_consistency():
    '''
    Example of what is being tested:
    The endpoints /projects/N/ and /projects/ should have the same fields as
    that same project when it is serialized by the unified job template serializer
    in /unified_job_templates/
    '''
    for cls in UnifiedJobTemplate.__subclasses__():
        detail_serializer = getattr(serializers, '{}Serializer'.format(cls.__name__))
        unified_serializer = serializers.UnifiedJobTemplateSerializer().get_sub_serializer(cls())
        assert set(detail_serializer().fields.keys()) == set(unified_serializer().fields.keys())


def test_unified_job_list_field_consistency():
    '''
    Example of what is being tested:
    The endpoint /project_updates/ should have the same fields as that
    project update when it is serialized by the unified job template serializer
    in /unified_jobs/
    '''
    for cls in UnifiedJob.__subclasses__():
        list_serializer = getattr(serializers, '{}ListSerializer'.format(cls.__name__))
        unified_serializer = serializers.UnifiedJobListSerializer().get_sub_serializer(cls())
        assert set(list_serializer().fields.keys()) == set(unified_serializer().fields.keys()), (
            'Mismatch between {} list serializer & unified list serializer'.format(cls)
        )


def test_unified_job_detail_exclusive_fields():
    '''
    For each type, assert that the only fields allowed to be exclusive to
    detail view are the allowed types
    '''
    allowed_detail_fields = frozenset(
        ('result_traceback', 'job_args', 'job_cwd', 'job_env', 'event_processing_finished')
    )
    for cls in UnifiedJob.__subclasses__():
        list_serializer = getattr(serializers, '{}ListSerializer'.format(cls.__name__))
        detail_serializer = getattr(serializers, '{}Serializer'.format(cls.__name__))
        list_fields = set(list_serializer().fields.keys())
        detail_fields = set(detail_serializer().fields.keys()) - allowed_detail_fields
        assert list_fields == detail_fields, 'List / detail mismatch for serializers of {}'.format(cls)


def test_list_views_use_list_serializers(all_views):
    '''
    Check that the list serializers are only used for list views,
    and vice versa
    '''
    list_serializers = tuple(
        getattr(serializers, '{}ListSerializer'.format(cls.__name__)) for
        cls in (UnifiedJob.__subclasses__() + [UnifiedJob])
    )
    for View in all_views:
        if hasattr(View, 'model') and issubclass(getattr(View, 'model'), UnifiedJob):
            if issubclass(View, ListAPIView):
                assert issubclass(View.serializer_class, list_serializers), (
                    'View {} serializer {} is not a list serializer'.format(View, View.serializer_class)
                )
            else:
                assert not issubclass(View.model, list_serializers)
