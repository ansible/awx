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
        make_option('--controller', dest='controller', type='string', default='',
                    help='The controlling group (makes this an isolated group)'),
    )

    def handle(self, **options):
        ig = InstanceGroup.objects.filter(name=options.get('queuename'))
        control_ig = None
        if options.get('controller'):
            control_ig = InstanceGroup.objects.filter(name=options.get('controller')).first()
        if ig.exists():
            print("Instance Group already registered {}".format(ig[0]))
            ig = ig[0]
            if control_ig and ig.controller_id != control_ig.pk:
                ig.controller = control_ig
                ig.save()
                print("Set controller group {} on {}.".format(control_ig, ig))
        else:
            print("Creating instance group {}".format(options.get('queuename')))
            ig = InstanceGroup(name=options.get('queuename'))
            if control_ig:
                ig.controller = control_ig
            ig.save()
        hostname_list = []
        if options.get('hostnames'):
            hostname_list = options.get('hostnames').split(",")
        instance_list = [x.strip() for x in hostname_list]
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
