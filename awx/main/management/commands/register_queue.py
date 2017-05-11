# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.
import sys

from awx.main.models import Instance, InstanceGroup

from optparse import make_option
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--queuename', dest='queuename', type='string',
                    help='Queue to create/update'),
        make_option('--hostnames', dest='hostnames', type='string',
                    help='Comma-Delimited Hosts to add to the Queue'),
    )

    def handle(self, **options):
        ig = InstanceGroup.objects.filter(name=options.get('queuename'))
        if ig.exists():
            print("Instance Group already registered {}".format(ig[0]))
            ig = ig[0]
        else:
            print("Creating instance group {}".format(options.get('queuename')))
            ig = InstanceGroup(name=options.get('queuename'))
            ig.save()
        instance_list = [x.strip() for x in options.get('hostnames').split(",")]
        for inst_name in instance_list:
            instance = Instance.objects.filter(hostname=inst_name)
            if instance.exists() and instance not in ig.instances.all():
                ig.instances.add(instance[0])
                print("Added instance {} to {}".format(instance[0], ig))
            elif not instance.exists():
                print("Instance does not exist: {}".format(inst_name))
                sys.exit(1)
            else:
                print("Instance already registered {}".format(instance[0]))
