# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.
import sys

from awx.main.models import Instance, InstanceGroup

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    help = (
        "Remove an instance (specified by --hostname) from the specified queue (instance group).\n"
        "In order remove the queue, use the `unregister_queue` command.")

    option_list = BaseCommand.option_list + (
        make_option('--queuename', dest='queuename', type='string',
                    help='Queue to be removed from'),
        make_option('--hostname', dest='hostname', type='string',
                    help='Host to remove from queue'),
    )

    def handle(self, **options):
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
        print("Instance removed from instance group")

