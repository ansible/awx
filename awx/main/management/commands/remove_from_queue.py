# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.
import sys

from awx.main.models import Instance, InstanceGroup
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    help = (
        "Remove an instance (specified by --hostname) from the specified queue (instance group).\n"
        "In order remove the queue, use the `unregister_queue` command.")

    def add_arguments(self, parser):
        parser.add_argument('--queuename', dest='queuename', type=str,
                            help='Queue to be removed from')
        parser.add_argument('--hostname', dest='hostname', type=str,
                            help='Host to remove from queue')

    def handle(self, *arg, **options):
        if not options.get('queuename'):
            raise CommandError('Must specify `--queuename` in order to use command.')
        ig = InstanceGroup.objects.filter(name=options.get('queuename'))
        if not ig.exists():
            print("Queue doesn't exist")
            sys.exit(1)
        ig = ig.first()
        i = Instance.objects.filter(hostname=options.get("hostname"))
        if not i.exists():
            print("Host doesn't exist")
            sys.exit(1)
        i = i.first()
        ig.instances.remove(i)
        if i.hostname in ig.policy_instance_list:
            ig.policy_instance_list.remove(i.hostname)
            ig.save()
        print("Instance removed from instance group")
