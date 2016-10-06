# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from awx.main.models import Instance
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    """List instances from the Tower database
    """

    def handle(self, **options):
        super(Command, self).__init__()

        for instance in Instance.objects.all():
            print("hostname: {}; created: {}; heartbeat: {}".format(instance.hostname, instance.created, instance.modified))
