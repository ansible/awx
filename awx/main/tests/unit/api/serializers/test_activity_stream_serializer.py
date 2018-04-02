from awx.api.serializers import ActivityStreamSerializer
from awx.main.registrar import activity_stream_registrar
from awx.main.models import ActivityStream

from awx.conf.models import Setting


def test_activity_stream_related():
    '''
    If this test failed with content in `missing_models`, that means that a
    model has been connected to the activity stream, but the model has not
    been added to the activity stream serializer.

    How to fix this:
    Ideally, all models should be in awx.api.serializers.SUMMARIZABLE_FK_FIELDS

    If, for whatever reason, the missing model should not generally be
    summarized from related resources, then a special case can be carved out in
    ActivityStreamSerializer._local_summarizable_fk_fields
    '''
    serializer_related = set(
        ActivityStream._meta.get_field(field_name).related_model for field_name, stuff in
        ActivityStreamSerializer()._local_summarizable_fk_fields
        if hasattr(ActivityStream, field_name)
    )
    
    models = set(activity_stream_registrar.models)
    models.remove(Setting)

    missing_models = models - serializer_related
    assert not missing_models
