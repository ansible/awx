import pytest
from django.apps import apps

from awx.main.migrations._dab_rbac import setup_managed_role_definitions


@pytest.fixture
def managed_roles():
    "Run the migration script to pre-create managed role definitions"
    setup_managed_role_definitions(apps, None)
