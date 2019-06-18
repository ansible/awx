# Python
import pytest
from unittest import mock
from unittest.mock import PropertyMock

# AWX
from awx.api.serializers import (
    CustomInventoryScriptSerializer,
    InventorySourceSerializer,
)
from awx.main.models import (
    CustomInventoryScript,
    InventorySource,
    User,
)

#DRF
from rest_framework.request import Request
from rest_framework.test import (
    APIRequestFactory,
    force_authenticate,
)


@pytest.fixture
def inventory_source(mocker):
    obj = mocker.MagicMock(
        pk=22,
        inventory=mocker.MagicMock(pk=23),
        update=mocker.MagicMock(),
        source_project_id=None,
        current_update=None,
        last_update=None,
        spec=InventorySource
    )
    return obj


class TestCustomInventoryScriptSerializer(object):
    @pytest.mark.parametrize("superuser,sysaudit,admin_role,value",
                             ((True, False, False, '#!/python'),
                              (False, True, False, '#!/python'),
                              (False, False, True, '#!/python'),
                              (False, False, False, None)))
    def test_to_representation_orphan(self, superuser, sysaudit, admin_role, value):
        with mock.patch.object(CustomInventoryScriptSerializer, 'get_summary_fields', return_value={}):
            with mock.patch.object(User, 'is_system_auditor', return_value=sysaudit):
                user = User(username="root", is_superuser=superuser)
                roles = [user] if admin_role else []

                with mock.patch('awx.main.models.CustomInventoryScript.admin_role', new_callable=PropertyMock, return_value=roles),\
                        mock.patch('awx.api.serializers.settings'):
                    cis = CustomInventoryScript(pk=1, script=value)
                    serializer = CustomInventoryScriptSerializer()

                    factory = APIRequestFactory()
                    wsgi_request = factory.post("/inventory_script/1", {'id':1}, format="json")
                    force_authenticate(wsgi_request, user)

                    request = Request(wsgi_request)
                    serializer.context['request'] = request

                    representation = serializer.to_representation(cis)
                    assert representation['script'] == value


@mock.patch('awx.api.serializers.UnifiedJobTemplateSerializer.get_related', lambda x,y: {})
@mock.patch('awx.api.serializers.InventorySourceOptionsSerializer.get_related', lambda x,y: {})
class TestInventorySourceSerializerGetRelated(object):
    @pytest.mark.parametrize('related_resource_name', [
        'activity_stream',
        'notification_templates_error',
        'notification_templates_success',
        'notification_templates_started',
        'inventory_updates',
        'update',
        'hosts',
        'groups',
    ])
    def test_get_related(self, test_get_related, inventory_source, related_resource_name):
        test_get_related(
            InventorySourceSerializer,
            inventory_source,
            'inventory_sources',
            related_resource_name
        )
