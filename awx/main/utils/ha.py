# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.

# Python
import six

# Django
from django.conf import settings

# AWX
from awx.main.models import Instance


def _add_remove_celery_worker_queues(app, controlled_instances, worker_queues, worker_name):
    removed_queues = []
    added_queues = []
    ig_names = set([six.text_type('tower_instance_router')])
    hostnames = set([instance.hostname for instance in controlled_instances])
    for instance in controlled_instances:
        ig_names.update(instance.rampart_groups.values_list('name', flat=True))
    worker_queue_names = set([q['name'] for q in worker_queues])

    # Remove queues that aren't in the instance group
    for queue in worker_queues:
        if queue['name'] in settings.AWX_CELERY_QUEUES_STATIC or \
                queue['alias'] in settings.AWX_CELERY_QUEUES_STATIC:
            continue

        if queue['name'] not in ig_names | hostnames or not instance.enabled:
            app.control.cancel_consumer(queue['name'].encode("utf8"), reply=True, destination=[worker_name])
            removed_queues.append(queue['name'].encode("utf8"))

    # Add queues for instance and instance groups
    for queue_name in ig_names | hostnames:
        if queue_name not in worker_queue_names:
            res = app.control.add_consumer(queue_name.encode("utf8"), reply=True, destination=[worker_name])
            added_queues.append(queue_name.encode("utf8"))

    return (added_queues, removed_queues)


def update_celery_worker_routes(instance, conf):
    tasks = [
        'awx.main.tasks.cluster_node_heartbeat',
        'awx.main.tasks.purge_old_stdout_files',
    ]
    routes_updated = {}
    # Instance is, effectively, a controller node
    if instance.is_controller():
        tasks.append('awx.main.tasks.awx_isolated_heartbeat')
    else:
        if 'awx.main.tasks.awx_isolated_heartbeat' in conf.CELERY_ROUTES:
            del conf.CELERY_ROUTES['awx.main.tasks.awx_isolated_heartbeat']

    for t in tasks:
        conf.CELERY_ROUTES[t] = {'queue': instance.hostname.encode("utf8"), 'routing_key': instance.hostname.encode("utf8")}
        routes_updated[t] = conf.CELERY_ROUTES[t]

    return routes_updated


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

