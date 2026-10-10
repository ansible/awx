# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved

# Python
from unittest import mock

import pytest

# Django
from django.core.management.base import CommandError

# AWX
from awx.main.management.commands.inventory_import import AnsibleInventoryLoader, Command


@pytest.mark.inventory_import
class TestInvalidOptions:
    def test_invalid_options_no_options_specified(self):
        cmd = Command()
        with pytest.raises(CommandError) as err:
            cmd.handle()
        assert 'inventory-id' in str(err.value)
        assert 'required' in str(err.value)

    def test_invalid_options_name_and_id(self):
        # You can not specify both name and if of the inventory
        cmd = Command()
        with pytest.raises(CommandError) as err:
            cmd.handle(inventory_id=42, inventory_name='my-inventory')
        assert 'inventory-id' in str(err.value)
        assert 'exclusive' in str(err.value)

    def test_invalid_options_missing_source(self):
        cmd = Command()
        with pytest.raises(CommandError) as err:
            cmd.handle(inventory_id=42)
        assert '--source' in str(err.value)
        assert 'required' in str(err.value)


@pytest.mark.inventory_import
def test_base_args_remove_container_on_exit():
    ee = mock.Mock(image='quay.io/ansible/awx-ee:latest', credential=None)
    with (
        mock.patch('awx.main.management.commands.inventory_import.get_default_execution_environment', return_value=ee),
        mock.patch('awx.main.management.commands.inventory_import.settings') as s,
    ):
        s.IS_K8S = False
        bargs = AnsibleInventoryLoader('/tmp/inv').get_base_args()
    assert bargs[:3] == ['podman', 'run', '--rm']
