# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved

# Python
import pytest

# Django
from django.core.management.base import CommandError

# AWX
from awx.main.management.commands.inventory_import import (
    Command
)


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
            cmd.handle(
                inventory_id=42, inventory_name='my-inventory'
            )
        assert 'inventory-id' in str(err.value)
        assert 'exclusive' in str(err.value)

    def test_invalid_options_id_and_keep_vars(self):
        # You can't overwrite and keep_vars at the same time, that wouldn't make sense
        cmd = Command()
        with pytest.raises(CommandError) as err:
            cmd.handle(
                inventory_id=42, overwrite=True, keep_vars=True
            )
        assert 'overwrite-vars' in str(err.value)
        assert 'exclusive' in str(err.value)

    def test_invalid_options_id_but_no_source(self):
        # Need a source to import
        cmd = Command()
        with pytest.raises(CommandError) as err:
            cmd.handle(
                inventory_id=42, overwrite=True, keep_vars=True
            )
        assert 'overwrite-vars' in str(err.value)
        assert 'exclusive' in str(err.value)
        with pytest.raises(CommandError) as err:
            cmd.handle(
                inventory_id=42, overwrite_vars=True, keep_vars=True
            )
        assert 'overwrite-vars' in str(err.value)
        assert 'exclusive' in str(err.value)

    def test_invalid_options_missing_source(self):
        cmd = Command()
        with pytest.raises(CommandError) as err:
            cmd.handle(inventory_id=42)
        assert '--source' in str(err.value)
        assert 'required' in str(err.value)

