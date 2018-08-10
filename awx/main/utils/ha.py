# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.

from awx.main.models import Instance


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
