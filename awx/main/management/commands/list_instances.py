# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from awx.main.models import Instance, InstanceGroup
from django.core.management.base import BaseCommand


class Ungrouped(object):
    name = 'ungrouped'
    policy_instance_percentage = None
    policy_instance_minimum = None

    def __init__(self):
        self.qs = Instance.objects.filter(rampart_groups__isnull=True)

    @property
    def instances(self):
        return self.qs

    @property
    def capacity(self):
        return sum(x.capacity for x in self.instances.all())


class Command(BaseCommand):
    """List instances from the Tower database"""

    def handle(self, *args, **options):
        super(Command, self).__init__()
        no_color = options.get("no_color", False)

        groups = list(InstanceGroup.objects.all())
        ungrouped = Ungrouped()
        if len(ungrouped.instances.all()):
            groups.append(ungrouped)

        for ig in groups:
            policy = ''
            if ig.policy_instance_percentage:
                policy = f' policy={ig.policy_instance_percentage}%'
            if ig.policy_instance_minimum:
                policy = f' policy>={ig.policy_instance_minimum}'
            print(f'[{ig.name} capacity={ig.capacity}{policy}]')

            for x in ig.instances.all():
                color = '\033[92m'
                end_color = '\033[0m'
                if x.capacity == 0 and x.node_type != 'hop':
                    color = '\033[91m'
                if not x.enabled:
                    color = '\033[90m[DISABLED] '
                if no_color:
                    color = ''
                    end_color = ''

                capacity = f' capacity={x.capacity}' if x.node_type != 'hop' else ''
                version = f" version={x.version or '?'}" if x.node_type != 'hop' else ''
                heartbeat = f' heartbeat="{x.last_seen:%Y-%m-%d %H:%M:%S}"' if x.capacity or x.node_type == 'hop' else ''
                print(f'\t{color}{x.hostname}{capacity} node_type={x.node_type}{version}{heartbeat}{end_color}')

            print()
