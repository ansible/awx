# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo.serialization import jsonutils

from novaclient.tests.unit import fakes
from novaclient.tests.unit.fixture_data import base
from novaclient.tests.unit.v2 import fakes as v2_fakes


class Base(base.Fixture):

    base_url = 'servers'

    def setUp(self):
        super(Base, self).setUp()

        get_servers = {
            "servers": [
                {'id': 1234, 'name': 'sample-server'},
                {'id': 5678, 'name': 'sample-server2'}
            ]
        }

        self.requests.register_uri('GET', self.url(),
                                   json=get_servers,
                                   headers=self.json_headers)

        self.server_1234 = {
            "id": 1234,
            "name": "sample-server",
            "image": {
                "id": 2,
                "name": "sample image",
            },
            "flavor": {
                "id": 1,
                "name": "256 MB Server",
            },
            "hostId": "e4d909c290d0fb1ca068ffaddf22cbd0",
            "status": "BUILD",
            "progress": 60,
            "addresses": {
                "public": [
                    {
                        "version": 4,
                        "addr": "1.2.3.4",
                    },
                    {
                        "version": 4,
                        "addr": "5.6.7.8",
                    }],
                "private": [{
                    "version": 4,
                    "addr": "10.11.12.13",
                }],
            },
            "metadata": {
                "Server Label": "Web Head 1",
                "Image Version": "2.1"
            },
            "OS-EXT-SRV-ATTR:host": "computenode1",
            "security_groups": [{
                'id': 1, 'name': 'securitygroup1',
                'description': 'FAKE_SECURITY_GROUP',
                'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7'
            }],
            "OS-EXT-MOD:some_thing": "mod_some_thing_value",
        }

        self.server_5678 = {
            "id": 5678,
            "name": "sample-server2",
            "image": {
                "id": 2,
                "name": "sample image",
            },
            "flavor": {
                "id": 1,
                "name": "256 MB Server",
            },
            "hostId": "9e107d9d372bb6826bd81d3542a419d6",
            "status": "ACTIVE",
            "addresses": {
                "public": [
                    {
                        "version": 4,
                        "addr": "4.5.6.7",
                    },
                    {
                        "version": 4,
                        "addr": "5.6.9.8",
                    }],
                "private": [{
                    "version": 4,
                    "addr": "10.13.12.13",
                }],
            },
            "metadata": {
                "Server Label": "DB 1"
            },
            "OS-EXT-SRV-ATTR:host": "computenode2",
            "security_groups": [
                {
                    'id': 1, 'name': 'securitygroup1',
                    'description': 'FAKE_SECURITY_GROUP',
                    'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7'
                },
                {
                    'id': 2, 'name': 'securitygroup2',
                    'description': 'ANOTHER_FAKE_SECURITY_GROUP',
                    'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7'
                }],
        }

        self.server_9012 = {
            "id": 9012,
            "name": "sample-server3",
            "image": "",
            "flavor": {
                "id": 1,
                "name": "256 MB Server",
            },
            "hostId": "9e107d9d372bb6826bd81d3542a419d6",
            "status": "ACTIVE",
            "addresses": {
                "public": [
                    {
                        "version": 4,
                        "addr": "4.5.6.7",
                    },
                    {
                        "version": 4,
                        "addr": "5.6.9.8",
                    }],
                "private": [{
                    "version": 4,
                    "addr": "10.13.12.13",
                }],
            },
            "metadata": {
                "Server Label": "DB 1"
            }
        }

        servers = [self.server_1234, self.server_5678, self.server_9012]
        get_servers_detail = {"servers": servers}

        self.requests.register_uri('GET', self.url('detail'),
                                   json=get_servers_detail,
                                   headers=self.json_headers)

        self.server_1235 = self.server_1234.copy()
        self.server_1235['id'] = 1235
        self.server_1235['status'] = 'error'
        self.server_1235['fault'] = {'message': 'something went wrong!'}

        for s in servers + [self.server_1235]:
            self.requests.register_uri('GET', self.url(s['id']),
                                       json={'server': s},
                                       headers=self.json_headers)

        for s in (1234, 5678):
            self.requests.register_uri('DELETE', self.url(s), status_code=202)

        for k in ('test_key', 'key1', 'key2'):
            self.requests.register_uri('DELETE',
                                       self.url(1234, 'metadata', k),
                                       status_code=204)

        metadata1 = {'metadata': {'test_key': 'test_value'}}
        self.requests.register_uri('POST', self.url(1234, 'metadata'),
                                   json=metadata1,
                                   headers=self.json_headers)
        self.requests.register_uri('PUT',
                                   self.url(1234, 'metadata', 'test_key'),
                                   json=metadata1,
                                   headers=self.json_headers)

        self.diagnostic = {'data': 'Fake diagnostics'}

        metadata2 = {'metadata': {'key1': 'val1'}}
        for u in ('uuid1', 'uuid2', 'uuid3', 'uuid4'):
            self.requests.register_uri('POST', self.url(u, 'metadata'),
                                       json=metadata2, status_code=204)
            self.requests.register_uri('DELETE',
                                       self.url(u, 'metadata', 'key1'),
                                       json=self.diagnostic,
                                       headers=self.json_headers)

        get_security_groups = {
            "security_groups": [{
                'id': 1,
                'name': 'securitygroup1',
                'description': 'FAKE_SECURITY_GROUP',
                'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7',
                'rules': []}]
        }

        self.requests.register_uri('GET',
                                   self.url('1234', 'os-security-groups'),
                                   json=get_security_groups)

        self.requests.register_uri('POST', self.url(),
                                   json=self.post_servers,
                                   headers=self.json_headers)

        self.requests.register_uri('POST', self.url('1234', 'action'),
                                   json=self.post_servers_1234_action,
                                   headers=self.json_headers)

        get_os_interface = {
            "interfaceAttachments": [
                {
                    "port_state": "ACTIVE",
                    "net_id": "net-id-1",
                    "port_id": "port-id-1",
                    "mac_address": "aa:bb:cc:dd:ee:ff",
                    "fixed_ips": [{"ip_address": "1.2.3.4"}],
                },
                {
                    "port_state": "ACTIVE",
                    "net_id": "net-id-1",
                    "port_id": "port-id-1",
                    "mac_address": "aa:bb:cc:dd:ee:ff",
                    "fixed_ips": [{"ip_address": "1.2.3.4"}],
                }
            ]
        }

        self.requests.register_uri('GET',
                                   self.url('1234', 'os-interface'),
                                   json=get_os_interface,
                                   headers=self.json_headers)

        interface_data = {'interfaceAttachment': {}}
        self.requests.register_uri('POST',
                                   self.url('1234', 'os-interface'),
                                   json=interface_data,
                                   headers=self.json_headers)

        def put_servers_1234(request, context):
            body = jsonutils.loads(request.body)
            assert list(body) == ['server']
            fakes.assert_has_keys(body['server'],
                                  optional=['name', 'adminPass'])
            return request.body

        self.requests.register_uri('PUT', self.url(1234),
                                   text=put_servers_1234,
                                   status_code=204,
                                   headers=self.json_headers)

        def post_os_volumes_boot(request, context):
            body = jsonutils.loads(request.body)
            assert (set(body.keys()) <=
                    set(['server', 'os:scheduler_hints']))

            fakes.assert_has_keys(body['server'],
                                  required=['name', 'flavorRef'],
                                  optional=['imageRef'])

            data = body['server']

            # Require one, and only one, of the keys for bdm
            if 'block_device_mapping' not in data:
                if 'block_device_mapping_v2' not in data:
                    msg = "missing required keys: 'block_device_mapping'"
                    raise AssertionError(msg)
            elif 'block_device_mapping_v2' in data:
                msg = "found extra keys: 'block_device_mapping'"
                raise AssertionError(msg)

            return {'server': self.server_9012}

        # NOTE(jamielennox): hack to make os_volumes mock go to the right place
        base_url = self.base_url
        self.base_url = None
        self.requests.register_uri('POST', self.url('os-volumes_boot'),
                                   json=post_os_volumes_boot,
                                   status_code=202,
                                   headers=self.json_headers)
        self.base_url = base_url

        #
        # Server password
        #

        self.requests.register_uri('DELETE',
                                   self.url(1234, 'os-server-password'),
                                   status_code=202)


class V1(Base):

    def setUp(self):
        super(V1, self).setUp()

        #
        # Server Addresses
        #

        add = self.server_1234['addresses']
        self.requests.register_uri('GET', self.url(1234, 'ips'),
                                   json={'addresses': add},
                                   headers=self.json_headers)

        self.requests.register_uri('GET', self.url(1234, 'ips', 'public'),
                                   json={'public': add['public']},
                                   headers=self.json_headers)

        self.requests.register_uri('GET', self.url(1234, 'ips', 'private'),
                                   json={'private': add['private']},
                                   headers=self.json_headers)

        self.requests.register_uri('DELETE',
                                   self.url(1234, 'ips', 'public', '1.2.3.4'),
                                   status_code=202)

        self.requests.register_uri('GET',
                                   self.url('1234', 'diagnostics'),
                                   json=self.diagnostic)

        self.requests.register_uri('DELETE',
                                   self.url('1234', 'os-interface', 'port-id'))

        # Testing with the following password and key
        #
        # Clear password: FooBar123
        #
        # RSA Private Key: novaclient/tests/unit/idfake.pem
        #
        # Encrypted password
        # OIuEuQttO8Rk93BcKlwHQsziDAnkAm/V6V8VPToA8ZeUaUBWwS0gwo2K6Y61Z96r
        # qG447iRz0uTEEYq3RAYJk1mh3mMIRVl27t8MtIecR5ggVVbz1S9AwXJQypDKl0ho
        # QFvhCBcMWPohyGewDJOhDbtuN1IoFI9G55ZvFwCm5y7m7B2aVcoLeIsJZE4PLsIw
        # /y5a6Z3/AoJZYGG7IH5WN88UROU3B9JZGFB2qtPLQTOvDMZLUhoPRIJeHiVSlo1N
        # tI2/++UsXVg3ow6ItqCJGgdNuGG5JB+bslDHWPxROpesEIHdczk46HCpHQN8f1sk
        # Hi/fmZZNQQqj1Ijq0caOIw==

        get_server_password = {
            'password':
            'OIuEuQttO8Rk93BcKlwHQsziDAnkAm/V6V8VPToA8ZeUaUBWwS0gwo2K6Y61Z96r'
            'qG447iRz0uTEEYq3RAYJk1mh3mMIRVl27t8MtIecR5ggVVbz1S9AwXJQypDKl0ho'
            'QFvhCBcMWPohyGewDJOhDbtuN1IoFI9G55ZvFwCm5y7m7B2aVcoLeIsJZE4PLsIw'
            '/y5a6Z3/AoJZYGG7IH5WN88UROU3B9JZGFB2qtPLQTOvDMZLUhoPRIJeHiVSlo1N'
            'tI2/++UsXVg3ow6ItqCJGgdNuGG5JB+bslDHWPxROpesEIHdczk46HCpHQN8f1sk'
            'Hi/fmZZNQQqj1Ijq0caOIw=='}
        self.requests.register_uri('GET',
                                   self.url(1234, 'os-server-password'),
                                   json=get_server_password)

    def post_servers(self, request, context):
        body = jsonutils.loads(request.body)
        context.status_code = 202
        assert (set(body.keys()) <=
                set(['server', 'os:scheduler_hints']))
        fakes.assert_has_keys(body['server'],
                              required=['name', 'imageRef', 'flavorRef'],
                              optional=['metadata', 'personality'])
        if 'personality' in body['server']:
            for pfile in body['server']['personality']:
                fakes.assert_has_keys(pfile, required=['path', 'contents'])
        if body['server']['name'] == 'some-bad-server':
            body = self.server_1235
        else:
            body = self.server_1234

        return {'server': body}

    def post_servers_1234_action(self, request, context):
        _body = ''
        body = jsonutils.loads(request.body)
        context.status_code = 202
        assert len(body.keys()) == 1
        action = list(body)[0]

        if v2_fakes.FakeHTTPClient.check_server_actions(body):
            # NOTE(snikitin): No need to do any operations here. This 'pass'
            # is needed to avoid AssertionError in the last 'else' statement
            # if we found 'action' in method check_server_actions and
            # raise AssertionError if we didn't find 'action' at all.
            pass
        elif action == 'rebuild':
            body = body[action]
            adminPass = body.get('adminPass', 'randompassword')
            assert 'imageRef' in body
            _body = self.server_1234.copy()
            _body['adminPass'] = adminPass
        elif action == 'confirmResize':
            assert body[action] is None
            # This one method returns a different response code
            context.status_code = 204
            return None
        elif action == 'rescue':
            if body[action]:
                keys = set(body[action].keys())
                assert not (keys - set(['adminPass', 'rescue_image_ref']))
            else:
                assert body[action] is None
            _body = {'adminPass': 'RescuePassword'}
        elif action == 'createImage':
            assert set(body[action].keys()) == set(['name', 'metadata'])
            context.headers['location'] = "http://blah/images/456"
        elif action == 'os-getConsoleOutput':
            assert list(body[action]) == ['length']
            context.status_code = 202
            return {'output': 'foo'}
        elif action == 'os-getSerialConsole':
            assert list(body[action]) == ['type']
        elif action == 'evacuate':
            keys = list(body[action])
            if 'adminPass' in keys:
                keys.remove('adminPass')
            assert set(keys) == set(['host', 'onSharedStorage'])
        else:
            raise AssertionError("Unexpected server action: %s" % action)
        return {'server': _body}
