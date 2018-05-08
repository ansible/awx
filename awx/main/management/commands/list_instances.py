# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from awx.main.models import Instance, InstanceGroup
from django.core.management.base import BaseCommand
import six


class Command(BaseCommand):
    """List instances from the Tower database
    """

    def handle(self, *args, **options):
        super(Command, self).__init__()

        for instance in Instance.objects.all():
            print(six.text_type(
                "hostname: {0.hostname}; created: {0.created}; "
                "heartbeat: {0.modified}; capacity: {0.capacity}").format(instance))
        for instance_group in InstanceGroup.objects.all():
            print(six.text_type(
                "Instance Group: {0.name}; created: {0.created}; "
                "capacity: {0.capacity}; members: {1}").format(instance_group,
                                                               [x.hostname for x in instance_group.instances.all()]))
