# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.

# Django
from django.conf import settings

# AWX
from awx.main.models import Instance


def construct_bcast_queue_name(common_name):
    return common_name.encode('utf8') + '_' + settings.CLUSTER_HOST_ID


def _add_remove_celery_worker_queues(app, controlled_instances, worker_queues, worker_name):
    removed_queues = []
    added_queues = []
    ig_names = set()
    hostnames = set([instance.hostname for instance in controlled_instances])
    for instance in controlled_instances:
        ig_names.update(instance.rampart_groups.values_list('name', flat=True))
    worker_queue_names = set([q['name'] for q in worker_queues])

    bcast_queue_names = set([construct_bcast_queue_name(n) for n in settings.AWX_CELERY_BCAST_QUEUES_STATIC])
    all_queue_names = ig_names | hostnames | set(settings.AWX_CELERY_QUEUES_STATIC)
    desired_queues = bcast_queue_names | (all_queue_names if instance.enabled else set())

    # Remove queues
    for queue_name in worker_queue_names:
        if queue_name not in desired_queues:
            app.control.cancel_consumer(queue_name.encode("utf8"), reply=True, destination=[worker_name])
            removed_queues.append(queue_name.encode("utf8"))

    # Add queues for instance and instance groups
    for queue_name in all_queue_names:
        if queue_name not in worker_queue_names:
            app.control.add_consumer(queue_name.encode("utf8"), reply=True, destination=[worker_name])
            added_queues.append(queue_name.encode("utf8"))

    # Add stable-named broadcast queues
    for queue_name in settings.AWX_CELERY_BCAST_QUEUES_STATIC:
        bcast_queue_name = construct_bcast_queue_name(queue_name)
        if bcast_queue_name not in worker_queue_names:
            app.control.add_consumer(bcast_queue_name,
                                     exchange=queue_name.encode("utf8"),
                                     exchange_type='fanout',
                                     routing_key=queue_name.encode("utf8"),
                                     reply=True)
            added_queues.append(bcast_queue_name)

    return (added_queues, removed_queues)


class AWXCeleryRouter(object):
    def route_for_task(self, task, args=None, kwargs=None):
        (changed, instance) = Instance.objects.get_or_register()
        tasks = [
            'awx.main.tasks.cluster_node_heartbeat',
            'awx.main.tasks.purge_old_stdout_files',
        ]
        isolated_tasks = [
            'awx.main.tasks.awx_isolated_heartbeat',
        ]
        if task in tasks:
            return {'queue': instance.hostname.encode("utf8"), 'routing_key': instance.hostname.encode("utf8")}

        if instance.is_controller() and task in isolated_tasks:
            return {'queue': instance.hostname.encode("utf8"), 'routing_key': instance.hostname.encode("utf8")}


def register_celery_worker_queues(app, celery_worker_name):
    instance = Instance.objects.me()
    controlled_instances = [instance]
    if instance.is_controller():
        controlled_instances.extend(Instance.objects.filter(
            rampart_groups__controller__instances__hostname=instance.hostname
        ))
    added_queues = []
    removed_queues = []

    celery_host_queues = app.control.inspect([celery_worker_name]).active_queues()

    celery_worker_queues = celery_host_queues[celery_worker_name] if celery_host_queues else []
    (added_queues, removed_queues) = _add_remove_celery_worker_queues(app, controlled_instances,
                                                                      celery_worker_queues, celery_worker_name)
    return (controlled_instances, removed_queues, added_queues)

