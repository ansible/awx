# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.


from awx.settings.application_name import set_application_name
from django.conf import settings
from django.db import transaction


def set_connection_name(function):
    set_application_name(settings.DATABASES, settings.CLUSTER_HOST_ID, function=function)


def bulk_update_sorted_by_id(model, objects, fields, batch_size=1000):
    # Filter out objects with None ID
    objects = [obj for obj in objects if obj.id is not None]
    # If there are no valid objects, return early
    if not objects:
        return
    # Sort objects by their ID
    sorted_objects = sorted(objects, key=lambda obj: obj.id)

    # Perform the bulk update within an atomic transaction
    with transaction.atomic():
        model.objects.bulk_update(sorted_objects, fields, batch_size=batch_size)
