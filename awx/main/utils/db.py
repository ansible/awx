# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.


from awx.settings.application_name import set_application_name
from django.conf import settings


def set_connection_name(function):
    set_application_name(settings.DATABASES, settings.CLUSTER_HOST_ID, function=function)


def bulk_update_sorted_by_id(model, objects, fields, batch_size=1000):
    """
    Perform a sorted bulk update on model instances to avoid database deadlocks.

    This function was introduced to prevent deadlocks observed in the AWX Controller
    when concurrent jobs attempt to update different fields on the same `main_hosts` table.
    Specifically, deadlocks occurred when one process updated `last_job_id` while another
    simultaneously updated `ansible_facts`.

    By sorting updates ID, we ensure a consistent update order,
    which helps avoid the row-level locking contention that can lead to deadlocks
    in PostgreSQL when multiple processes are involved.

    Returns:
        int: The number of rows affected by the update.
    """
    objects = [obj for obj in objects if obj.id is not None]
    if not objects:
        return 0  # Return 0 when nothing is updated

    sorted_objects = sorted(objects, key=lambda obj: obj.id)
    return model.objects.bulk_update(sorted_objects, fields, batch_size=batch_size)
