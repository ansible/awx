import json
from http import HTTPStatus
from unittest.mock import patch

from requests import Response

from awx.main.utils.licensing import Licenser


def test_rhsm_licensing():
    def mocked_requests_get(*args, **kwargs):
        assert kwargs['verify'] == True
        response = Response()
        subs = json.dumps({'body': []})
        response.status_code = HTTPStatus.OK
        response._content = bytes(subs, 'utf-8')
        return response

    licenser = Licenser()
    with patch('awx.main.utils.analytics_proxy.OIDCClient.make_request', new=mocked_requests_get):
        subs = licenser.get_rhsm_subs('localhost', 'admin', 'admin')
        assert subs == []


def test_satellite_licensing():
    def mocked_requests_get(*args, **kwargs):
        assert kwargs['verify'] == True
        response = Response()
        subs = json.dumps({'results': []})
        response.status_code = HTTPStatus.OK
        response._content = bytes(subs, 'utf-8')
        return response

    licenser = Licenser()
    with patch('requests.get', new=mocked_requests_get):
        subs = licenser.get_satellite_subs('localhost', 'admin', 'admin')
        assert subs == []
