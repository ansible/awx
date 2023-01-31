# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.
import sys

from awx.main.utils.pglock import advisory_lock
from awx.main.models import Instance, InstanceGroup

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class InstanceNotFound(Exception):
    def __init__(self, message, changed, *args, **kwargs):
        self.message = message
        self.changed = changed
        super(InstanceNotFound, self).__init__(*args, **kwargs)


class RegisterQueue:
    def __init__(
        self, queuename, instance_percent, inst_min, hostname_list, is_container_group=None, pod_spec_override=None, max_forks=None, max_concurrent_jobs=None
    ):
        self.instance_not_found_err = None
        self.queuename = queuename
        self.instance_percent = instance_percent
        self.instance_min = inst_min
        self.hostname_list = hostname_list
        self.is_container_group = is_container_group
        self.pod_spec_override = pod_spec_override
        self.max_forks = max_forks
        self.max_concurrent_jobs = max_concurrent_jobs

    def get_create_update_instance_group(self):
        created = False
        changed = False
        (ig, created) = InstanceGroup.objects.get_or_create(name=self.queuename)
        if ig.policy_instance_percentage != self.instance_percent:
            ig.policy_instance_percentage = self.instance_percent
            changed = True
        if ig.policy_instance_minimum != self.instance_min:
            ig.policy_instance_minimum = self.instance_min
            changed = True

        if self.is_container_group and (ig.is_container_group != self.is_container_group):
            ig.is_container_group = self.is_container_group
            changed = True

        if self.pod_spec_override and (ig.pod_spec_override != self.pod_spec_override):
            ig.pod_spec_override = self.pod_spec_override
            changed = True

        if self.max_forks and (ig.max_forks != self.max_forks):
            ig.max_forks = self.max_forks
            changed = True

        if self.max_concurrent_jobs and (ig.max_concurrent_jobs != self.max_concurrent_jobs):
            ig.max_concurrent_jobs = self.max_concurrent_jobs
            changed = True

        if changed:
            ig.save()

        return (ig, created, changed)

    def add_instances_to_group(self, ig):
        changed = False

        instance_list_unique = {x for x in (x.strip() for x in self.hostname_list) if x}
        instances = []
        for inst_name in instance_list_unique:
            instance = Instance.objects.filter(hostname=inst_name).exclude(node_type='hop')
            if instance.exists():
                instances.append(instance[0])
            else:
                raise InstanceNotFound("Instance does not exist or cannot run jobs: {}".format(inst_name), changed)

        ig.instances.add(*instances)

        instance_list_before = ig.policy_instance_list
        instance_list_after = instance_list_unique
        new_instances = set(instance_list_after) - set(instance_list_before)
        if new_instances:
            changed = True
            ig.policy_instance_list = ig.policy_instance_list + list(new_instances)
            ig.save()

        return (instances, changed)

    def register(self):
        with advisory_lock('cluster_policy_lock'):
            with transaction.atomic():
                changed2 = False
                (ig, created, changed1) = self.get_create_update_instance_group()
                if created:
                    print("Creating instance group {}".format(ig.name))
                elif not created:
                    print("Instance Group already registered {}".format(ig.name))

                try:
                    (instances, changed2) = self.add_instances_to_group(ig)
                    for i in instances:
                        print("Added instance {} to {}".format(i.hostname, ig.name))
                except InstanceNotFound as e:
                    self.instance_not_found_err = e

        if changed1 or changed2:
            print('(changed: True)')


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--queuename', dest='queuename', type=str, help='Queue to create/update')
        parser.add_argument(
            '--hostnames', dest='hostnames', type=str, help='Comma-Delimited Hosts to add to the Queue (will not remove already assigned instances)'
        )
        parser.add_argument(
            '--instance_percent', dest='instance_percent', type=int, default=0, help='The percentage of active instances that will be assigned to this group'
        ),
        parser.add_argument(
            '--instance_minimum',
            dest='instance_minimum',
            type=int,
            default=0,
            help='The minimum number of instance that will be retained for this group from available instances',
        )

    def handle(self, **options):
        queuename = options.get('queuename')
        if not queuename:
            raise CommandError("Specify `--queuename` to use this command.")
        inst_per = options.get('instance_percent')
        instance_min = options.get('instance_minimum')
        hostname_list = []
        if options.get('hostnames'):
            hostname_list = options.get('hostnames').split(",")

        rq = RegisterQueue(queuename, inst_per, instance_min, hostname_list)
        rq.register()
        if rq.instance_not_found_err:
            print(rq.instance_not_found_err.message)
            sys.exit(1)
