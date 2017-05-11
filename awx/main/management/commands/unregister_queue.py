# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.
import sys

from awx.main.models import InstanceGroup

from optparse import make_option
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--queuename', dest='queuename', type='string',
                    help='Queue to create/update'),
    )

    def handle(self, **options):
        ig = InstanceGroup.objects.filter(name=options.get('queuename'))
        if not ig.exists():
            print("Instance group doesn't exist")
            sys.exit(1)
        ig = ig.first()
        ig.delete()
        print("Instance Group Removed")
