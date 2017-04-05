# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.
from awx.main.models import Instance, InstanceGroup

from optparse import make_option
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--queuename', dest='queuename', type='string',
                    help='Queue to be removed from'),
        make_option('--hostname', dest='hostnames', type='string',
                    help='Host to remove from queue'),
    )

    def handle(self, **options):
        ig = InstanceGroup.objects.filter(name=options.get('queuename'))
        if not ig.exists():
            print("Queue doesn't exist")
        ig = ig.first()
        i = Instance.objects.filter(name=options.get("hostname"))
        if not i.exists():
            print("Host doesn't exist")
        i = i.first()
        ig.instances.remove(i)
        print("Instance removed from instance group")

