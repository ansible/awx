# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.
import sys

from awx.main.utils.pglock import advisory_lock
from awx.main.models import InstanceGroup

from optparse import make_option
from django.db import transaction
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

    @transaction.atomic
    def handle(self, **options):
        queuename = options.get('queuename')
        if not queuename:
            raise CommandError('Must specify `--queuename` in order to use command.')
        with advisory_lock('instance_group_registration_%s' % queuename):
            ig = InstanceGroup.objects.filter(name=queuename)
            if not ig.exists():
                print("Instance group doesn't exist")
                sys.exit(1)
            ig = ig.first()
            ig.delete()
            print("Instance Group Removed")
            print('(changed: True)')
