import json
import os
import re
from collections import namedtuple
from unittest import mock

import pytest
from django.conf import settings

from awx.main.constants import CLOUD_PROVIDERS, STANDARD_INVENTORY_UPDATE_ENV
from awx.main.models import (Credential, CredentialType, ExecutionEnvironment,
                             InventorySource, UnifiedJob)
from awx.main.tasks.jobs import RunInventoryUpdate
from awx.main.tests import data
from awx.main.utils.execution_environments import to_container_path

DATA = os.path.join(os.path.dirname(data.__file__), 'inventory')


@pytest.mark.django_db
@pytest.mark.parametrize('this_kind', CLOUD_PROVIDERS)
def test_inventory_update_injected_content(this_kind, inventory, fake_credential_factory, mock_me):
    ExecutionEnvironment.objects.create(name='Control Plane EE', managed=True)
    ExecutionEnvironment.objects.create(name='Default Job EE', managed=False)

    injector = InventorySource.injectors[this_kind]
    if injector.plugin_name is None:
        pytest.skip('Use of inventory plugin is not enabled for this source')

    src_vars = dict(base_source_var='value_of_var')
    src_vars['plugin'] = injector.get_proper_name()
    inventory_source = InventorySource.objects.create(
        inventory=inventory,
        source=this_kind,
        source_vars=src_vars,
    )
    inventory_source.credentials.add(fake_credential_factory(this_kind))
    inventory_update = inventory_source.create_unified_job()
    task = RunInventoryUpdate()
