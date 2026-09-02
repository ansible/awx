# Python
import pytest
from unittest import mock

from rest_framework.exceptions import ValidationError

# AWX
from awx.api.serializers import (
    InventorySourceSerializer,
)
from awx.api.validators import contains_path_traversal
from awx.main.models import InventorySource


@pytest.fixture
def inventory_source(mocker):
    obj = mocker.MagicMock(
        pk=22, inventory=mocker.MagicMock(pk=23), update=mocker.MagicMock(), source_project_id=None, current_update=None, last_update=None, spec=InventorySource
    )
    return obj


@mock.patch('awx.api.serializers.UnifiedJobTemplateSerializer.get_related', lambda x, y: {})
@mock.patch('awx.api.serializers.InventorySourceOptionsSerializer.get_related', lambda x, y: {})
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


@pytest.mark.parametrize(
    'value,expected',
    [
        ('playbooks/main.yml', False),
        ('inventories/hosts', False),
        ('backup..yml', False),
        ('', False),
        (None, False),
        ('../etc/passwd', True),
        ('inventories/../secrets', True),
        ('..\\windows\\path', True),
        ('foo\\..\\bar', True),
        ('..', True),
        ('foo/..', True),
    ],
)
def test_contains_path_traversal(value, expected):
    assert contains_path_traversal(value) is expected


class TestInventorySourcePathTraversal:
    def test_rejects_posix_traversal(self):
        serializer = InventorySourceSerializer()
        with pytest.raises(ValidationError) as exc:
            serializer.validate_source_path('../etc/passwd')
        assert 'path segments' in str(exc.value.detail)

    def test_rejects_windows_traversal(self):
        serializer = InventorySourceSerializer()
        with pytest.raises(ValidationError):
            serializer.validate_source_path('..\\windows\\path')

    def test_accepts_valid_relative_path(self):
        serializer = InventorySourceSerializer()
        assert serializer.validate_source_path('playbooks/main.yml') == 'playbooks/main.yml'

    def test_accepts_empty_path(self):
        serializer = InventorySourceSerializer()
        assert serializer.validate_source_path('') == ''

    def test_grandfathers_unchanged_traversal_path(self):
        serializer = InventorySourceSerializer()
        serializer.instance = mock.Mock(source_path='../legacy/hosts')
        assert serializer.validate_source_path('../legacy/hosts') == '../legacy/hosts'

    def test_rejects_changed_traversal_path_on_update(self):
        serializer = InventorySourceSerializer()
        serializer.instance = mock.Mock(source_path='playbooks/main.yml')
        with pytest.raises(ValidationError):
            serializer.validate_source_path('../etc/passwd')
