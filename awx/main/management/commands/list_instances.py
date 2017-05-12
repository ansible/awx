# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from awx.main.models import Instance, InstanceGroup
from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):
    """List instances from the Tower database
    """

    def handle(self, **options):
        super(Command, self).__init__()

        for instance in Instance.objects.all():
            print("hostname: {}; created: {}; heartbeat: {}; capacity: {}".format(instance.hostname, instance.created,
                                                                                  instance.modified, instance.capacity))
        for instance_group in InstanceGroup.objects.all():
            print("Instance Group: {}; created: {}; capacity: {}; members: {}".format(instance_group.name,
                                                                                      instance_group.created,
                                                                                      instance_group.capacity,
                                                                                      [x.hostname for x in instance_group.instances.all()]))
