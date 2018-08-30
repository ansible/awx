# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.

from django.conf import settings


class AWXCeleryRouter(object):
    def route_for_task(self, task, args=None, kwargs=None):
        tasks = [
            'awx.main.tasks.cluster_node_heartbeat',
            'awx.main.tasks.purge_old_stdout_files',
            'awx.main.tasks.awx_isolated_heartbeat',
        ]
        if task in tasks:
            return {'queue': settings.CLUSTER_HOST_ID, 'routing_key': settings.CLUSTER_HOST_ID}
