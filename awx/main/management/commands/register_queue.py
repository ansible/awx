# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.
import sys

from awx.main.utils.pglock import advisory_lock
from awx.main.models import Instance, InstanceGroup

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--queuename', dest='queuename', type=str,
                            help='Queue to create/update')
        parser.add_argument('--hostnames', dest='hostnames', type=str,
                            help='Comma-Delimited Hosts to add to the Queue')
        parser.add_argument('--controller', dest='controller', type=str,
                            default='', help='The controlling group (makes this an isolated group)')
        parser.add_argument('--instance_percent', dest='instance_percent', type=int, default=0,
                            help='The percentage of active instances that will be assigned to this group'),
        parser.add_argument('--instance_minimum', dest='instance_minimum', type=int, default=0,
                            help='The minimum number of instance that will be retained for this group from available instances')

    def handle(self, **options):
        queuename = options.get('queuename')
        if not queuename:
            raise CommandError("Specify `--queuename` to use this command.")
        changed = False
        with advisory_lock('instance_group_registration_%s' % queuename):
            ig = InstanceGroup.objects.filter(name=queuename)
            control_ig = None
            if options.get('controller'):
                control_ig = InstanceGroup.objects.filter(name=options.get('controller')).first()
            if ig.exists():
                print("Instance Group already registered {}".format(ig[0].name))
                ig = ig[0]
                if control_ig and ig.controller_id != control_ig.pk:
                    ig.controller = control_ig
                    ig.save()
                    print("Set controller group {} on {}.".format(control_ig.name, ig.name))
                    changed = True
            else:
                print("Creating instance group {}".format(queuename))
                ig = InstanceGroup(name=queuename,
                                   policy_instance_percentage=options.get('instance_percent'),
                                   policy_instance_minimum=options.get('instance_minimum'))
                if control_ig:
                    ig.controller = control_ig
                ig.save()
                changed = True
            hostname_list = []
            if options.get('hostnames'):
                hostname_list = options.get('hostnames').split(",")
            instance_list = [x.strip() for x in hostname_list if x]
            for inst_name in instance_list:
                instance = Instance.objects.filter(hostname=inst_name)
                if instance.exists() and instance[0] not in ig.instances.all():
                    ig.instances.add(instance[0])
                    print("Added instance {} to {}".format(instance[0].hostname, ig.name))
                    changed = True
                elif not instance.exists():
                    print("Instance does not exist: {}".format(inst_name))
                    if changed:
                        print('(changed: True)')
                    sys.exit(1)
                else:
                    print("Instance already registered {}".format(instance[0].hostname))
            ig.policy_instance_list = instance_list
            ig.save()
            if changed:
                print('(changed: True)')
