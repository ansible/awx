# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import uuid

# AWX
from awx.main.tests.base import BaseTest
from command_base import BaseCommandMixin
from awx.main.models import * # noqa

__all__ = ['RemoveInstanceCommandFunctionalTest']

class RemoveInstanceCommandFunctionalTest(BaseCommandMixin, BaseTest):
    uuids = []
    instances = []

    def setup_instances(self):
        self.uuids = [uuid.uuid4().hex for x in range(0, 3)]
        self.instances.append(Instance(uuid=settings.SYSTEM_UUID, primary=True, hostname='127.0.0.1'))
        self.instances.append(Instance(uuid=self.uuids[0], primary=False, hostname='127.0.0.2'))
        self.instances.append(Instance(uuid=self.uuids[1], primary=False, hostname='127.0.0.3'))
        self.instances.append(Instance(uuid=self.uuids[2], primary=False, hostname='127.0.0.4'))
        for x in self.instances:
            x.save()

    def setUp(self):
        super(RemoveInstanceCommandFunctionalTest, self).setUp()
        self.create_test_license_file()
        self.setup_instances()
        self.setup_users()

    def test_default(self):
        self.assertEqual(Instance.objects.filter(hostname="127.0.0.2").count(), 1)
        result, stdout, stderr = self.run_command('remove_instance', hostname='127.0.0.2')
        self.assertIsNone(result)
        self.assertEqual(stdout, 'Successfully removed instance (uuid="%s",hostname="127.0.0.2",role="secondary").\n' % (self.uuids[0]))
        self.assertEqual(Instance.objects.filter(hostname="127.0.0.2").count(), 0)

