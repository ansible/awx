# Python
import pytest

# AWX
from awx.api.serializers import (
    InventorySourceSerializer,
)
from awx.main.models import InventorySource


@pytest.fixture
def inventory_source(mocker):
    obj = mocker.MagicMock(
        pk=22,
        id=22,
        inventory=mocker.MagicMock(pk=23),
        update=mocker.MagicMock(),
        source_project_id=None,
        current_update=None,
        last_update=None,
        spec=InventorySource,
        created_by=mocker.MagicMock(pk=442),
        modified_by=mocker.MagicMock(pk=552),
        credential=89,
        execution_environment_id=99,
    )
    return obj


class TestInventorySourceSerializerGetRelated(object):
    @pytest.mark.parametrize(
        'related_resource_name',
        [
            'activity_stream',
            'notification_templates_error',
            'notification_templates_success',
            'notification_templates_started',
            'inventory_updates',
            'update',
            'hosts',
            'groups',
        ],
    )
    def test_get_related(self, test_get_related, inventory_source, related_resource_name):
        test_get_related(InventorySourceSerializer, inventory_source, 'inventory_sources', related_resource_name)
