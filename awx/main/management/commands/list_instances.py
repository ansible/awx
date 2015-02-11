# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved

from awx.main.management.commands._base_instance import BaseCommandInstance
from awx.main.models import Instance

instance_str = BaseCommandInstance.instance_str

class Command(BaseCommandInstance):
    """List instances from the Tower database
    """

    def handle(self, **options):
        super(Command, self).__init__()

        for instance in Instance.objects.all():
            print("uuid: %s; hostname: %s; primary: %s; created: %s; modified: %s" %
                  (instance.uuid, instance.hostname, instance.primary, instance.created, instance.modified))
