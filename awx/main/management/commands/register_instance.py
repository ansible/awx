# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from awx.main.management.commands._base_instance import BaseCommandInstance
from awx.main.models import Instance

instance_str = BaseCommandInstance.instance_str

class Command(BaseCommandInstance):
    """
    Internal tower command.
    Regsiter this instance with the database for HA tracking.

    This command is idempotent.
    """
    def __init__(self):
        super(Command, self).__init__()
        self.include_option_hostname_set()

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)

        uuid = self.get_UUID()

        instance = Instance.objects.filter(hostname=self.get_option_hostname())
        if instance.exists():
            print("Instance already registered %s" % instance_str(instance[0]))
            return
        instance = Instance(uuid=uuid, hostname=self.get_option_hostname())
        instance.save()
        print('Successfully registered instance %s.' % instance_str(instance))
