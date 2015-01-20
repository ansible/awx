# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from awx.main.management.commands._base_instance import BaseCommandInstance
instance_str = BaseCommandInstance.instance_str

from awx.main.models import Instance

class Command(BaseCommandInstance):
    """List instances from the Tower database
    """

    def handle(self, **options):
        super(Command, self).__init__()
        
        for instance in Instance.objects.all():
            print("uuid: %s; hostname: %s; primary: %s; created: %s; modified: %s" %
                  (instance.uuid, instance.hostname, instance.primary, instance.created, instance.modified))
