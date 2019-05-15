
from django.contrib.contenttypes.models import ContentType
from django.db import models

from awx.main.utils.common import camelcase_to_underscore


def build_polymorphic_ctypes_map(cls):
    # {'1': 'unified_job', '2': 'Job', '3': 'project_update', ...}
    mapping = {}
    for ct in ContentType.objects.filter(app_label='main'):
        ct_model_class = ct.model_class()
        if ct_model_class and issubclass(ct_model_class, cls):
            mapping[ct.id] = camelcase_to_underscore(ct_model_class.__name__)
    return mapping


def SET_NULL(collector, field, sub_objs, using):
    return models.SET_NULL(collector, field, sub_objs.non_polymorphic(), using)
