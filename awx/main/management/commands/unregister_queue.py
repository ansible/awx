# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.
import sys

from awx.main.models import InstanceGroup

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    help = (
        "Remove specified queue (instance group) from database.\n"
        "Instances inside of queue will continue to exist, \n"
        "but jobs will no longer be processed by queue.")

    option_list = BaseCommand.option_list + (
        make_option('--queuename', dest='queuename', type='string',
                    help='Queue to create/update'),
    )

    def handle(self, **options):
        if not options.get('queuename'):
            raise CommandError('Must specify `--queuename` in order to use command.')
        ig = InstanceGroup.objects.filter(name=options.get('queuename'))
        if not ig.exists():
            print("Instance group doesn't exist")
            sys.exit(1)
        ig = ig.first()
        ig.delete()
        print("Instance Group Removed")
        print('(changed: True)')
