# Python
import pytest
import mock
from mock import PropertyMock

# AWX
from awx.api.serializers import (
    CustomInventoryScriptSerializer,
)
from awx.main.models import (
    CustomInventoryScript,
    User,
)

#DRF
from rest_framework.request import Request
from rest_framework.test import (
    APIRequestFactory,
    force_authenticate,
)


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

                with mock.patch('awx.main.models.CustomInventoryScript.admin_role', new_callable=PropertyMock, return_value=roles):
                    cis = CustomInventoryScript(pk=1, script=value)
                    serializer = CustomInventoryScriptSerializer()

                    factory = APIRequestFactory()
                    wsgi_request = factory.post("/inventory_script/1", {'id':1}, format="json")
                    force_authenticate(wsgi_request, user)

                    request = Request(wsgi_request)
                    serializer.context['request'] = request

                    representation = serializer.to_representation(cis)
                    assert representation['script'] == value
