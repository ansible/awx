# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

from itertools import chain

from awx.settings.application_name import set_application_name
from django.conf import settings


def get_all_field_names(model):
    # Implements compatibility with _meta.get_all_field_names
    # See: https://docs.djangoproject.com/en/1.11/ref/models/meta/#migrating-from-the-old-api
    return list(
        set(
            chain.from_iterable(
                (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
                for field in model._meta.get_fields()
                # For complete backwards compatibility, you may want to exclude
                # GenericForeignKey from the results.
                if not (field.many_to_one and field.related_model is None)
            )
        )
    )


def set_connection_name(function):
    set_application_name(settings.DATABASES, settings.CLUSTER_HOST_ID, function=function)
