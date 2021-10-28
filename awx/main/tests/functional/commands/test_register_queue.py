from io import StringIO
from contextlib import redirect_stdout

import pytest

from awx.main.management.commands.register_queue import RegisterQueue
from awx.main.models.ha import InstanceGroup


@pytest.mark.django_db
def test_openshift_idempotence():
    def perform_register():
        with StringIO() as buffer:
            with redirect_stdout(buffer):
                RegisterQueue('default', 100, 0, [], is_container_group=True).register()
                return buffer.getvalue()

    assert '(changed: True)' in perform_register()
    assert '(changed: True)' not in perform_register()
    assert '(changed: True)' not in perform_register()

    ig = InstanceGroup.objects.get(name='default')
    assert ig.policy_instance_percentage == 100
    assert ig.policy_instance_minimum == 0
    assert ig.policy_instance_list == []
    assert ig.is_container_group is True
