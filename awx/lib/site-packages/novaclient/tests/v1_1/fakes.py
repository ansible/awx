# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2011 OpenStack Foundation
# Copyright 2013 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime

from oslo.utils import strutils
import six
from six.moves.urllib import parse

from novaclient import client as base_client
from novaclient import exceptions
from novaclient.tests import fakes
from novaclient.tests import utils
from novaclient.v1_1 import client


class FakeClient(fakes.FakeClient, client.Client):

    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url',
                               extensions=kwargs.get('extensions'))
        self.client = FakeHTTPClient(**kwargs)


class FakeHTTPClient(base_client.HTTPClient):

    def __init__(self, **kwargs):
        self.username = 'username'
        self.password = 'password'
        self.auth_url = 'auth_url'
        self.tenant_id = 'tenant_id'
        self.callstack = []
        self.projectid = 'projectid'
        self.user = 'user'
        self.region_name = 'region_name'
        self.endpoint_type = 'endpoint_type'
        self.service_type = 'service_type'
        self.service_name = 'service_name'
        self.volume_service_name = 'volume_service_name'
        self.timings = 'timings'
        self.bypass_url = 'bypass_url'
        self.os_cache = 'os_cache'
        self.http_log_debug = 'http_log_debug'

    def _cs_request(self, url, method, **kwargs):
        # Check that certain things are called correctly
        if method in ['GET', 'DELETE']:
            assert 'body' not in kwargs
        elif method == 'PUT':
            assert 'body' in kwargs

        # Call the method
        args = parse.parse_qsl(parse.urlparse(url)[4])
        kwargs.update(args)
        munged_url = url.rsplit('?', 1)[0]
        munged_url = munged_url.strip('/').replace('/', '_').replace('.', '_')
        munged_url = munged_url.replace('-', '_')
        munged_url = munged_url.replace(' ', '_')

        callback = "%s_%s" % (method.lower(), munged_url)

        if not hasattr(self, callback):
            raise AssertionError('Called unknown API method: %s %s, '
                                 'expected fakes method name: %s' %
                                 (method, url, callback))

        # Note the call
        self.callstack.append((method, url, kwargs.get('body')))

        status, headers, body = getattr(self, callback)(**kwargs)
        r = utils.TestResponse({
            "status_code": status,
            "text": body,
            "headers": headers,
        })
        return r, body

    #
    # agents
    #

    def get_os_agents(self, **kw):
        hypervisor = kw.get('hypervisor', 'kvm')
        return (200, {}, {'agents':
                    [{'hypervisor': hypervisor,
                      'os': 'win',
                     'architecture': 'x86',
                     'version': '7.0',
                     'url': 'xxx://xxxx/xxx/xxx',
                     'md5hash': 'add6bb58e139be103324d04d82d8f545',
                     'id': 1},
                    {'hypervisor': hypervisor,
                     'os': 'linux',
                     'architecture': 'x86',
                     'version': '16.0',
                     'url': 'xxx://xxxx/xxx/xxx1',
                     'md5hash': 'add6bb58e139be103324d04d82d8f546',
                     'id': 2},
                    ]})

    def post_os_agents(self, body):
        return (200, {}, {'agent': {
                          'url': '/xxx/xxx/xxx',
                          'hypervisor': body['agent']['hypervisor'],
                          'md5hash': 'add6bb58e139be103324d04d82d8f546',
                          'version': '7.0',
                          'architecture': 'x86',
                          'os': 'win',
                          'id': 1}})

    def delete_os_agents_1(self, **kw):
        return (202, {}, None)

    def put_os_agents_1(self, body, **kw):
        return (200, {}, {"agent": {
                           "url": "/yyy/yyyy/yyyy",
                           "version": "8.0",
                           "md5hash": "add6bb58e139be103324d04d82d8f546",
                           'id': 1}})

    #
    # List all extensions
    #

    def get_extensions(self, **kw):
        exts = [
            {
                "alias": "NMN",
                "description": "Multiple network support",
                "links": [],
                "name": "Multinic",
                "namespace": ("http://docs.openstack.org/"
                              "compute/ext/multinic/api/v1.1"),
                "updated": "2011-06-09T00:00:00+00:00"
            },
            {
                "alias": "OS-DCF",
                "description": "Disk Management Extension",
                "links": [],
                "name": "DiskConfig",
                "namespace": ("http://docs.openstack.org/"
                              "compute/ext/disk_config/api/v1.1"),
                "updated": "2011-09-27T00:00:00+00:00"
            },
            {
                "alias": "OS-EXT-SRV-ATTR",
                "description": "Extended Server Attributes support.",
                "links": [],
                "name": "ExtendedServerAttributes",
                "namespace": ("http://docs.openstack.org/"
                              "compute/ext/extended_status/api/v1.1"),
                "updated": "2011-11-03T00:00:00+00:00"
            },
            {
                "alias": "OS-EXT-STS",
                "description": "Extended Status support",
                "links": [],
                "name": "ExtendedStatus",
                "namespace": ("http://docs.openstack.org/"
                              "compute/ext/extended_status/api/v1.1"),
                "updated": "2011-11-03T00:00:00+00:00"
            },
        ]
        return (200, {}, {
            "extensions": exts,
        })

    #
    # Limits
    #

    def get_limits(self, **kw):
        return (200, {}, {"limits": {
            "rate": [
                {
                    "uri": "*",
                    "regex": ".*",
                    "limit": [
                        {
                            "value": 10,
                            "verb": "POST",
                            "remaining": 2,
                            "unit": "MINUTE",
                            "next-available": "2011-12-15T22:42:45Z"
                        },
                        {
                            "value": 10,
                            "verb": "PUT",
                            "remaining": 2,
                            "unit": "MINUTE",
                            "next-available": "2011-12-15T22:42:45Z"
                        },
                        {
                            "value": 100,
                            "verb": "DELETE",
                            "remaining": 100,
                            "unit": "MINUTE",
                            "next-available": "2011-12-15T22:42:45Z"
                        }
                    ]
                },
                {
                    "uri": "*/servers",
                    "regex": "^/servers",
                    "limit": [
                        {
                            "verb": "POST",
                            "value": 25,
                            "remaining": 24,
                            "unit": "DAY",
                            "next-available": "2011-12-15T22:42:45Z"
                        }
                    ]
                }
            ],
            "absolute": {
                "maxTotalRAMSize": 51200,
                "maxServerMeta": 5,
                "maxImageMeta": 5,
                "maxPersonality": 5,
                "maxPersonalitySize": 10240
            },
        },
    })

    #
    # Servers
    #

    def get_servers(self, **kw):
        return (200, {}, {"servers": [
            {'id': 1234, 'name': 'sample-server'},
            {'id': 5678, 'name': 'sample-server2'}
        ]})

    def get_servers_detail(self, **kw):
        return (200, {}, {"servers": [
            {
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
                    "public": [{
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
            },
            {
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
                    "public": [{
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
                "security_groups": [{
                    'id': 1, 'name': 'securitygroup1',
                    'description': 'FAKE_SECURITY_GROUP',
                    'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7'
                },
                {
                    'id': 2, 'name': 'securitygroup2',
                    'description': 'ANOTHER_FAKE_SECURITY_GROUP',
                    'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7'
                }],
            },
            {
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
                    "public": [{
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
        ]})

    def post_servers(self, body, **kw):
        assert set(body.keys()) <= set(['server', 'os:scheduler_hints'])
        fakes.assert_has_keys(body['server'],
                        required=['name', 'imageRef', 'flavorRef'],
                        optional=['metadata', 'personality'])
        if 'personality' in body['server']:
            for pfile in body['server']['personality']:
                fakes.assert_has_keys(pfile, required=['path', 'contents'])
        if body['server']['name'] == 'some-bad-server':
            return (202, {}, self.get_servers_1235()[2])
        else:
            return (202, {}, self.get_servers_1234()[2])

    def post_os_volumes_boot(self, body, **kw):
        assert set(body.keys()) <= set(['server', 'os:scheduler_hints'])
        fakes.assert_has_keys(body['server'],
                        required=['name', 'flavorRef'],
                        optional=['imageRef'])

        # Require one, and only one, of the keys for bdm
        if 'block_device_mapping' not in body['server']:
            if 'block_device_mapping_v2' not in body['server']:
                raise AssertionError(
                    "missing required keys: 'block_device_mapping'"
                )
        elif 'block_device_mapping_v2' in body['server']:
            raise AssertionError("found extra keys: 'block_device_mapping'")

        return (202, {}, self.get_servers_9012()[2])

    def get_servers_1234(self, **kw):
        r = {'server': self.get_servers_detail()[2]['servers'][0]}
        return (200, {}, r)

    def get_servers_1235(self, **kw):
        r = {'server': self.get_servers_detail()[2]['servers'][0]}
        r['server']['id'] = 1235
        r['server']['status'] = 'error'
        r['server']['fault'] = {'message': 'something went wrong!'}
        return (200, {}, r)

    def get_servers_5678(self, **kw):
        r = {'server': self.get_servers_detail()[2]['servers'][1]}
        return (200, {}, r)

    def get_servers_9012(self, **kw):
        r = {'server': self.get_servers_detail()[2]['servers'][2]}
        return (200, {}, r)

    def put_servers_1234(self, body, **kw):
        assert list(body) == ['server']
        fakes.assert_has_keys(body['server'], optional=['name', 'adminPass'])
        return (204, {}, body)

    def delete_os_server_groups_12345(self, **kw):
        return (202, {}, None)

    def delete_os_server_groups_56789(self, **kw):
        return (202, {}, None)

    def delete_servers_1234(self, **kw):
        return (202, {}, None)

    def delete_servers_5678(self, **kw):
        return (202, {}, None)

    def delete_servers_1234_metadata_test_key(self, **kw):
        return (204, {}, None)

    def delete_servers_1234_metadata_key1(self, **kw):
        return (204, {}, None)

    def delete_servers_1234_metadata_key2(self, **kw):
        return (204, {}, None)

    def post_servers_1234_metadata(self, **kw):
        return (204, {}, {'metadata': {'test_key': 'test_value'}})

    def put_servers_1234_metadata_test_key(self, **kw):
        return (200, {}, {'meta': {'test_key': 'test_value'}})

    def get_servers_1234_diagnostics(self, **kw):
        return (200, {}, {'data': 'Fake diagnostics'})

    def post_servers_uuid1_metadata(self, **kw):
        return (204, {}, {'metadata': {'key1': 'val1'}})

    def post_servers_uuid2_metadata(self, **kw):
        return (204, {}, {'metadata': {'key1': 'val1'}})

    def post_servers_uuid3_metadata(self, **kw):
        return (204, {}, {'metadata': {'key1': 'val1'}})

    def post_servers_uuid4_metadata(self, **kw):
        return (204, {}, {'metadata': {'key1': 'val1'}})

    def delete_servers_uuid1_metadata_key1(self, **kw):
        return (200, {}, {'data': 'Fake diagnostics'})

    def delete_servers_uuid2_metadata_key1(self, **kw):
        return (200, {}, {'data': 'Fake diagnostics'})

    def delete_servers_uuid3_metadata_key1(self, **kw):
        return (200, {}, {'data': 'Fake diagnostics'})

    def delete_servers_uuid4_metadata_key1(self, **kw):
        return (200, {}, {'data': 'Fake diagnostics'})

    def get_servers_1234_os_security_groups(self, **kw):
        return (200, {}, {
            "security_groups": [{
                'id': 1,
                'name': 'securitygroup1',
                'description': 'FAKE_SECURITY_GROUP',
                'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7',
                'rules': []}]
        })

    #
    # Server Addresses
    #

    def get_servers_1234_ips(self, **kw):
        return (200, {}, {'addresses':
                      self.get_servers_1234()[1]['server']['addresses']})

    def get_servers_1234_ips_public(self, **kw):
        return (200, {}, {'public':
                      self.get_servers_1234_ips()[1]['addresses']['public']})

    def get_servers_1234_ips_private(self, **kw):
        return (200, {}, {'private':
                      self.get_servers_1234_ips()[1]['addresses']['private']})

    def delete_servers_1234_ips_public_1_2_3_4(self, **kw):
        return (202, {}, None)

    #
    # Server password
    #

    # Testing with the following password and key
    #
    # Clear password: FooBar123
    #
    # RSA Private Key: novaclient/tests/idfake.pem
    #
    # Encrypted password
    # OIuEuQttO8Rk93BcKlwHQsziDAnkAm/V6V8VPToA8ZeUaUBWwS0gwo2K6Y61Z96r
    # qG447iRz0uTEEYq3RAYJk1mh3mMIRVl27t8MtIecR5ggVVbz1S9AwXJQypDKl0ho
    # QFvhCBcMWPohyGewDJOhDbtuN1IoFI9G55ZvFwCm5y7m7B2aVcoLeIsJZE4PLsIw
    # /y5a6Z3/AoJZYGG7IH5WN88UROU3B9JZGFB2qtPLQTOvDMZLUhoPRIJeHiVSlo1N
    # tI2/++UsXVg3ow6ItqCJGgdNuGG5JB+bslDHWPxROpesEIHdczk46HCpHQN8f1sk
    # Hi/fmZZNQQqj1Ijq0caOIw==
    def get_servers_1234_os_server_password(self, **kw):
        return (200, {}, {'password':
            'OIuEuQttO8Rk93BcKlwHQsziDAnkAm/V6V8VPToA8ZeUaUBWwS0gwo2K6Y61Z96r'
            'qG447iRz0uTEEYq3RAYJk1mh3mMIRVl27t8MtIecR5ggVVbz1S9AwXJQypDKl0ho'
            'QFvhCBcMWPohyGewDJOhDbtuN1IoFI9G55ZvFwCm5y7m7B2aVcoLeIsJZE4PLsIw'
            '/y5a6Z3/AoJZYGG7IH5WN88UROU3B9JZGFB2qtPLQTOvDMZLUhoPRIJeHiVSlo1N'
            'tI2/++UsXVg3ow6ItqCJGgdNuGG5JB+bslDHWPxROpesEIHdczk46HCpHQN8f1sk'
            'Hi/fmZZNQQqj1Ijq0caOIw=='})

    def delete_servers_1234_os_server_password(self, **kw):
        return (202, {}, None)

    #
    # Server actions
    #

    def post_servers_1234_action(self, body, **kw):
        _headers = None
        _body = None
        resp = 202
        assert len(body.keys()) == 1
        action = list(body)[0]
        if action == 'reboot':
            assert list(body[action]) == ['type']
            assert body[action]['type'] in ['HARD', 'SOFT']
        elif action == 'rebuild':
            body = body[action]
            adminPass = body.get('adminPass', 'randompassword')
            assert 'imageRef' in body
            _body = self.get_servers_1234()[2]
            _body['server']['adminPass'] = adminPass
        elif action == 'resize':
            keys = body[action].keys()
            assert 'flavorRef' in keys
        elif action == 'confirmResize':
            assert body[action] is None
            # This one method returns a different response code
            return (204, {}, None)
        elif action == 'revertResize':
            assert body[action] is None
        elif action == 'migrate':
            assert body[action] is None
        elif action == 'os-stop':
            assert body[action] is None
        elif action == 'os-start':
            assert body[action] is None
        elif action == 'forceDelete':
            assert body[action] is None
        elif action == 'restore':
            assert body[action] is None
        elif action == 'pause':
            assert body[action] is None
        elif action == 'unpause':
            assert body[action] is None
        elif action == 'lock':
            assert body[action] is None
        elif action == 'unlock':
            assert body[action] is None
        elif action == 'rescue':
            assert body[action] is None
            _body = {'Password': 'RescuePassword'}
        elif action == 'unrescue':
            assert body[action] is None
        elif action == 'resume':
            assert body[action] is None
        elif action == 'suspend':
            assert body[action] is None
        elif action == 'lock':
            assert body[action] is None
        elif action == 'unlock':
            assert body[action] is None
        elif action == 'shelve':
            assert body[action] is None
        elif action == 'shelveOffload':
            assert body[action] is None
        elif action == 'unshelve':
            assert body[action] is None
        elif action == 'addFixedIp':
            assert list(body[action]) == ['networkId']
        elif action == 'removeFixedIp':
            assert list(body[action]) == ['address']
        elif action == 'addFloatingIp':
            assert (list(body[action]) == ['address'] or
                    sorted(list(body[action])) == ['address',
                                                   'fixed_address'])
        elif action == 'removeFloatingIp':
            assert list(body[action]) == ['address']
        elif action == 'createImage':
            assert set(body[action].keys()) == set(['name', 'metadata'])
            _headers = dict(location="http://blah/images/456")
        elif action == 'changePassword':
            assert list(body[action]) == ['adminPass']
        elif action == 'os-getConsoleOutput':
            assert list(body[action]) == ['length']
            return (202, {}, {'output': 'foo'})
        elif action == 'os-getVNCConsole':
            assert list(body[action]) == ['type']
        elif action == 'os-getSPICEConsole':
            assert list(body[action]) == ['type']
        elif action == 'os-getRDPConsole':
            assert list(body[action]) == ['type']
        elif action == 'os-migrateLive':
            assert set(body[action].keys()) == set(['host',
                                                    'block_migration',
                                                    'disk_over_commit'])
        elif action == 'os-resetState':
            assert list(body[action]) == ['state']
        elif action == 'resetNetwork':
            assert body[action] is None
        elif action == 'addSecurityGroup':
            assert list(body[action]) == ['name']
        elif action == 'removeSecurityGroup':
            assert list(body[action]) == ['name']
        elif action == 'createBackup':
            assert set(body[action]) == set(['name',
                                             'backup_type',
                                             'rotation'])
        elif action == 'evacuate':
            keys = list(body[action])
            if 'adminPass' in keys:
                keys.remove('adminPass')
            if 'host' in keys:
                keys.remove('host')
            assert set(keys) == set(['onSharedStorage'])
        else:
            raise AssertionError("Unexpected server action: %s" % action)
        return (resp, _headers, _body)

    def post_servers_5678_action(self, body, **kw):
        return self.post_servers_1234_action(body, **kw)

    #
    # Cloudpipe
    #

    def get_os_cloudpipe(self, **kw):
        return (
            200,
            {},
            {'cloudpipes': [{'project_id': 1}]}
        )

    def post_os_cloudpipe(self, **ks):
        return (
            202,
            {},
            {'instance_id': '9d5824aa-20e6-4b9f-b967-76a699fc51fd'}
        )

    def put_os_cloudpipe_configure_project(self, **kw):
        return (202, {}, None)

    #
    # Flavors
    #

    def get_flavors(self, **kw):
        status, header, flavors = self.get_flavors_detail(**kw)
        for flavor in flavors['flavors']:
            for k in list(flavor):
                if k not in ['id', 'name']:
                    del flavor[k]

        return (200, {}, flavors)

    def get_flavors_detail(self, **kw):
        flavors = {'flavors': [
            {'id': 1, 'name': '256 MB Server', 'ram': 256, 'disk': 10,
             'OS-FLV-EXT-DATA:ephemeral': 10,
             'os-flavor-access:is_public': True,
             'links': {}},
            {'id': 2, 'name': '512 MB Server', 'ram': 512, 'disk': 20,
             'OS-FLV-EXT-DATA:ephemeral': 20,
             'os-flavor-access:is_public': False,
             'links': {}},
            {'id': 4, 'name': '1024 MB Server', 'ram': 1024, 'disk': 10,
             'OS-FLV-EXT-DATA:ephemeral': 10,
             'os-flavor-access:is_public': True,
             'links': {}},
            {'id': 'aa1', 'name': '128 MB Server', 'ram': 128, 'disk': 0,
             'OS-FLV-EXT-DATA:ephemeral': 0,
             'os-flavor-access:is_public': True,
             'links': {}}
        ]}

        if 'is_public' not in kw:
            filter_is_public = True
        else:
            if kw['is_public'].lower() == 'none':
                filter_is_public = None
            else:
                filter_is_public = strutils.bool_from_string(kw['is_public'],
                                                             True)

        if filter_is_public is not None:
            if filter_is_public:
                flavors['flavors'] = [
                    v for v in flavors['flavors']
                    if v['os-flavor-access:is_public']
                ]
            else:
                flavors['flavors'] = [
                    v for v in flavors['flavors']
                    if not v['os-flavor-access:is_public']
                ]

        return (200, {}, flavors)

    def get_flavors_1(self, **kw):
        return (
            200,
            {},
            {'flavor':
                self.get_flavors_detail(is_public='None')[2]['flavors'][0]}
        )

    def get_flavors_2(self, **kw):
        return (
            200,
            {},
            {'flavor':
                self.get_flavors_detail(is_public='None')[2]['flavors'][1]}
        )

    def get_flavors_3(self, **kw):
        # Diablo has no ephemeral
        return (
            200,
            {},
            {'flavor': {
                'id': 3,
                'name': '256 MB Server',
                'ram': 256,
                'disk': 10,
            }},
        )

    def get_flavors_512_MB_Server(self, **kw):
        raise exceptions.NotFound('404')

    def get_flavors_128_MB_Server(self, **kw):
        raise exceptions.NotFound('404')

    def get_flavors_aa1(self, **kw):
        # Alphanumeric flavor id are allowed.
        return (
            200,
            {},
            {'flavor':
                self.get_flavors_detail(is_public='None')[2]['flavors'][3]}
        )

    def get_flavors_4(self, **kw):
        return (
            200,
            {},
            {'flavor':
                self.get_flavors_detail(is_public='None')[2]['flavors'][2]}
        )

    def delete_flavors_flavordelete(self, **kw):
        return (202, {}, None)

    def delete_flavors_2(self, **kw):
        return (202, {}, None)

    def post_flavors(self, body, **kw):
        return (
            202,
            {},
            {'flavor':
                self.get_flavors_detail(is_public='None')[2]['flavors'][0]}
        )

    def get_flavors_1_os_extra_specs(self, **kw):
        return (200,
            {},
            {'extra_specs': {"k1": "v1"}})

    def get_flavors_2_os_extra_specs(self, **kw):
        return (200,
            {},
            {'extra_specs': {"k2": "v2"}})

    def get_flavors_aa1_os_extra_specs(self, **kw):
        return (200, {},
            {'extra_specs': {"k3": "v3"}})

    def get_flavors_4_os_extra_specs(self, **kw):
        return (200,
            {},
            {'extra_specs': {"k4": "v4"}})

    def post_flavors_1_os_extra_specs(self, body, **kw):
        assert list(body) == ['extra_specs']
        fakes.assert_has_keys(body['extra_specs'],
                              required=['k1'])
        return (200,
            {},
            {'extra_specs': {"k1": "v1"}})

    def post_flavors_4_os_extra_specs(self, body, **kw):
        assert list(body) == ['extra_specs']

        return (200,
            {},
            body)

    def delete_flavors_1_os_extra_specs_k1(self, **kw):
        return (204, {}, None)

    #
    # Flavor access
    #

    def get_flavors_1_os_flavor_access(self, **kw):
        return (404, {}, None)

    def get_flavors_2_os_flavor_access(self, **kw):
        return (200, {}, {'flavor_access': [
            {'flavor_id': '2', 'tenant_id': 'proj1'},
            {'flavor_id': '2', 'tenant_id': 'proj2'}
        ]})

    def post_flavors_2_action(self, body, **kw):
        return (202, {}, self.get_flavors_2_os_flavor_access()[2])

    #
    # Floating ips
    #

    def get_os_floating_ip_pools(self):
        return (
            200,
            {},
            {'floating_ip_pools': [{'name': 'foo'}, {'name': 'bar'}]}
        )

    def get_os_floating_ips(self, **kw):
        return (
            200,
            {},
            {'floating_ips': [
                {'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1'},
                {'id': 2, 'fixed_ip': '10.0.0.2', 'ip': '11.0.0.2'},
            ]},
        )

    def get_os_floating_ips_1(self, **kw):
        return (200, {}, {'floating_ip':
            {'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1'}
        })

    def post_os_floating_ips(self, body):
        if body.get('pool'):
            return (200, {}, {'floating_ip':
                {'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1',
                                                            'pool': 'nova'}})
        else:
            return (200, {}, {'floating_ip':
                {'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1',
                                                            'pool': None}})

    def delete_os_floating_ips_1(self, **kw):
        return (204, {}, None)

    def get_os_floating_ip_dns(self, **kw):
        return (205, {}, {'domain_entries':
                          [{'domain': 'example.org'},
                           {'domain': 'example.com'}]})

    def get_os_floating_ip_dns_testdomain_entries(self, **kw):
        if kw.get('ip'):
            return (205, {}, {'dns_entries':
                          [{'dns_entry':
                             {'ip': kw.get('ip'),
                              'name': "host1",
                              'type': "A",
                              'domain': 'testdomain'}},
                           {'dns_entry':
                             {'ip': kw.get('ip'),
                              'name': "host2",
                              'type': "A",
                              'domain': 'testdomain'}}]})
        else:
            return (404, {}, None)

    def get_os_floating_ip_dns_testdomain_entries_testname(self, **kw):
        return (205, {}, {'dns_entry':
                        {'ip': "10.10.10.10",
                         'name': 'testname',
                         'type': "A",
                         'domain': 'testdomain'}})

    def put_os_floating_ip_dns_testdomain(self, body, **kw):
        if body['domain_entry']['scope'] == 'private':
            fakes.assert_has_keys(body['domain_entry'],
                            required=['availability_zone', 'scope'])
        elif body['domain_entry']['scope'] == 'public':
            fakes.assert_has_keys(body['domain_entry'],
                            required=['project', 'scope'])

        else:
            fakes.assert_has_keys(body['domain_entry'],
                            required=['project', 'scope'])
        return (205, {}, body)

    def put_os_floating_ip_dns_testdomain_entries_testname(self, body, **kw):
        fakes.assert_has_keys(body['dns_entry'],
                        required=['ip', 'dns_type'])
        return (205, {}, body)

    def delete_os_floating_ip_dns_testdomain(self, **kw):
        return (200, {}, None)

    def delete_os_floating_ip_dns_testdomain_entries_testname(self, **kw):
        return (200, {}, None)

    def get_os_floating_ips_bulk(self, **kw):
        return (200, {}, {'floating_ip_info': [
            {'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1'},
            {'id': 2, 'fixed_ip': '10.0.0.2', 'ip': '11.0.0.2'},
        ]})

    def get_os_floating_ips_bulk_testHost(self, **kw):
        return (200, {}, {'floating_ip_info': [
            {'id': 1, 'fixed_ip': '10.0.0.1', 'ip': '11.0.0.1'},
            {'id': 2, 'fixed_ip': '10.0.0.2', 'ip': '11.0.0.2'},
        ]})

    def post_os_floating_ips_bulk(self, **kw):
        params = kw.get('body').get('floating_ips_bulk_create')
        pool = params.get('pool', 'defaultPool')
        interface = params.get('interface', 'defaultInterface')
        return (200, {}, {'floating_ips_bulk_create':
                          {'ip_range': '192.168.1.0/30',
                           'pool': pool,
                           'interface': interface}})

    def put_os_floating_ips_bulk_delete(self, **kw):
        ip_range = kw.get('body').get('ip_range')
        return (200, {}, {'floating_ips_bulk_delete': ip_range})

    #
    # Images
    #
    def get_images(self, **kw):
        return (200, {}, {'images': [
            {'id': 1, 'name': 'CentOS 5.2'},
            {'id': 2, 'name': 'My Server Backup'}
        ]})

    def get_images_detail(self, **kw):
        return (200, {}, {'images': [
            {
                'id': 1,
                'name': 'CentOS 5.2',
                "updated": "2010-10-10T12:00:00Z",
                "created": "2010-08-10T12:00:00Z",
                "status": "ACTIVE",
                "metadata": {
                    "test_key": "test_value",
                },
                "links": {},
            },
            {
                "id": 2,
                "name": "My Server Backup",
                "serverId": 1234,
                "updated": "2010-10-10T12:00:00Z",
                "created": "2010-08-10T12:00:00Z",
                "status": "SAVING",
                "progress": 80,
                "links": {},
            }
        ]})

    def get_images_1(self, **kw):
        return (200, {}, {'image': self.get_images_detail()[2]['images'][0]})

    def get_images_2(self, **kw):
        return (200, {}, {'image': self.get_images_detail()[2]['images'][1]})

    def get_images_456(self, **kw):
        return (200, {}, {'image': self.get_images_detail()[2]['images'][1]})

    def post_images(self, body, **kw):
        assert list(body) == ['image']
        fakes.assert_has_keys(body['image'], required=['serverId', 'name'])
        return (202, {}, self.get_images_1()[2])

    def post_images_1_metadata(self, body, **kw):
        assert list(body) == ['metadata']
        fakes.assert_has_keys(body['metadata'],
                              required=['test_key'])
        return (200,
            {},
            {'metadata': self.get_images_1()[2]['image']['metadata']})

    def delete_images_1(self, **kw):
        return (204, {}, None)

    def delete_images_2(self, **kw):
        return (204, {}, None)

    def delete_images_1_metadata_test_key(self, **kw):
        return (204, {}, None)

    #
    # Keypairs
    #
    def get_os_keypairs_test(self, *kw):
        return (200, {}, {'keypair':
                          self.get_os_keypairs()[2]['keypairs'][0]['keypair']})

    def get_os_keypairs(self, *kw):
        return (200, {}, {"keypairs": [
                              {"keypair": {
                                  "public_key": "FAKE_SSH_RSA",
                                  "private_key": "FAKE_PRIVATE_KEY",
                                  "user_id":
                                      "81e373b596d6466e99c4896826abaa46",
                                  "name": "test",
                                  "deleted": False,
                                  "created_at": "2014-04-19T02:16:44.000000",
                                  "updated_at": "2014-04-19T10:12:3.000000",
                                  "figerprint": "FAKE_KEYPAIR",
                                  "deleted_at": None,
                                  "id": 4}
                               }]})

    def delete_os_keypairs_test(self, **kw):
        return (202, {}, None)

    def post_os_keypairs(self, body, **kw):
        assert list(body) == ['keypair']
        fakes.assert_has_keys(body['keypair'],
                              required=['name'])
        r = {'keypair': self.get_os_keypairs()[2]['keypairs'][0]['keypair']}
        return (202, {}, r)

    #
    # Virtual Interfaces
    #
    def get_servers_1234_os_virtual_interfaces(self, **kw):
        return (200, {}, {"virtual_interfaces": [
            {'id': 'fakeid', 'mac_address': 'fakemac'}
        ]})

    #
    # Quotas
    #

    def get_os_quota_sets_test(self, **kw):
        return (200, {}, {'quota_set': {
                      'tenant_id': 'test',
                      'metadata_items': [],
                      'injected_file_content_bytes': 1,
                      'injected_file_path_bytes': 1,
                      'ram': 1,
                      'floating_ips': 1,
                      'instances': 1,
                      'injected_files': 1,
                      'cores': 1,
                      'keypairs': 1,
                      'security_groups': 1,
                      'security_group_rules': 1}})

    def get_os_quota_sets_tenant_id(self, **kw):
        return (200, {}, {'quota_set': {
                      'tenant_id': 'test',
                      'metadata_items': [],
                      'injected_file_content_bytes': 1,
                      'injected_file_path_bytes': 1,
                      'ram': 1,
                      'floating_ips': 1,
                      'instances': 1,
                      'injected_files': 1,
                      'cores': 1,
                      'keypairs': 1,
                      'security_groups': 1,
                      'security_group_rules': 1}})

    def get_os_quota_sets_97f4c221bff44578b0300df4ef119353(self, **kw):
        return (200, {}, {'quota_set': {
                      'tenant_id': '97f4c221bff44578b0300df4ef119353',
                      'metadata_items': [],
                      'injected_file_content_bytes': 1,
                      'injected_file_path_bytes': 1,
                      'ram': 1,
                      'floating_ips': 1,
                      'instances': 1,
                      'injected_files': 1,
                      'cores': 1,
                      'keypairs': 1,
                      'security_groups': 1,
                      'security_group_rules': 1}})

    def put_os_quota_sets_97f4c221_bff4_4578_b030_0df4ef119353(self, **kw):
        return (200, {}, {'quota_set': {
                      'tenant_id': '97f4c221-bff4-4578-b030-0df4ef119353',
                      'metadata_items': [],
                      'injected_file_content_bytes': 1,
                      'injected_file_path_bytes': 1,
                      'ram': 1,
                      'floating_ips': 1,
                      'instances': 1,
                      'injected_files': 1,
                      'cores': 1,
                      'keypairs': 1,
                      'security_groups': 1,
                      'security_group_rules': 1}})

    def get_os_quota_sets_97f4c221_bff4_4578_b030_0df4ef119353(self, **kw):
        return (200, {}, {'quota_set': {
                      'tenant_id': '97f4c221-bff4-4578-b030-0df4ef119353',
                      'metadata_items': [],
                      'injected_file_content_bytes': 1,
                      'injected_file_path_bytes': 1,
                      'ram': 1,
                      'floating_ips': 1,
                      'instances': 1,
                      'injected_files': 1,
                      'cores': 1,
                      'keypairs': 1,
                      'security_groups': 1,
                      'security_group_rules': 1}})

    def get_os_quota_sets_97f4c221bff44578b0300df4ef119353_defaults(self):
        return (200, {}, {'quota_set': {
                      'tenant_id': 'test',
                      'metadata_items': [],
                      'injected_file_content_bytes': 1,
                      'injected_file_path_bytes': 1,
                      'ram': 1,
                      'floating_ips': 1,
                      'instances': 1,
                      'injected_files': 1,
                      'cores': 1,
                      'keypairs': 1,
                      'security_groups': 1,
                      'security_group_rules': 1}})

    def get_os_quota_sets_tenant_id_defaults(self):
        return (200, {}, {'quota_set': {
                      'tenant_id': 'test',
                      'metadata_items': [],
                      'injected_file_content_bytes': 1,
                      'injected_file_path_bytes': 1,
                      'ram': 1,
                      'floating_ips': 1,
                      'instances': 1,
                      'injected_files': 1,
                      'cores': 1,
                      'keypairs': 1,
                      'security_groups': 1,
                      'security_group_rules': 1}})

    def put_os_quota_sets_97f4c221bff44578b0300df4ef119353(self, body, **kw):
        assert list(body) == ['quota_set']
        fakes.assert_has_keys(body['quota_set'],
                              required=['tenant_id'])
        return (200, {}, {'quota_set': {
                      'tenant_id': '97f4c221bff44578b0300df4ef119353',
                      'metadata_items': [],
                      'injected_file_content_bytes': 1,
                      'injected_file_path_bytes': 1,
                      'ram': 1,
                      'floating_ips': 1,
                      'instances': 1,
                      'injected_files': 1,
                      'cores': 1,
                      'keypairs': 1,
                      'security_groups': 1,
                      'security_group_rules': 1}})

    def delete_os_quota_sets_test(self, **kw):
        return (202, {}, {})

    def delete_os_quota_sets_97f4c221bff44578b0300df4ef119353(self, **kw):
        return (202, {}, {})

    #
    # Quota Classes
    #

    def get_os_quota_class_sets_test(self, **kw):
        return (200, {}, {'quota_class_set': {
                      'id': 'test',
                      'metadata_items': 1,
                      'injected_file_content_bytes': 1,
                      'injected_file_path_bytes': 1,
                      'ram': 1,
                      'floating_ips': 1,
                      'instances': 1,
                      'injected_files': 1,
                      'cores': 1,
                      'key_pairs': 1,
                      'security_groups': 1,
                      'security_group_rules': 1}})

    def put_os_quota_class_sets_test(self, body, **kw):
        assert list(body) == ['quota_class_set']
        return (200, {}, {'quota_class_set': {
                      'metadata_items': 1,
                      'injected_file_content_bytes': 1,
                      'injected_file_path_bytes': 1,
                      'ram': 1,
                      'floating_ips': 1,
                      'instances': 1,
                      'injected_files': 1,
                      'cores': 1,
                      'key_pairs': 1,
                      'security_groups': 1,
                      'security_group_rules': 1}})

    def put_os_quota_class_sets_97f4c221bff44578b0300df4ef119353(self,
                                                            body, **kw):
        assert list(body) == ['quota_class_set']
        return (200, {}, {'quota_class_set': {
                      'metadata_items': 1,
                      'injected_file_content_bytes': 1,
                      'injected_file_path_bytes': 1,
                      'ram': 1,
                      'floating_ips': 1,
                      'instances': 1,
                      'injected_files': 1,
                      'cores': 1,
                      'key_pairs': 1,
                      'security_groups': 1,
                      'security_group_rules': 1}})

    #
    # Security Groups
    #
    def get_os_security_groups(self, **kw):
        return (200, {}, {"security_groups": [
            {"name": "test",
             "description": "FAKE_SECURITY_GROUP",
             "tenant_id":
                 "4ffc664c198e435e9853f2538fbcd7a7",
             "id": 1,
             "rules": [
                 {"id": 11,
                  "group": {},
                  "ip_protocol": "TCP",
                  "from_port": 22,
                  "to_port": 22,
                  "parent_group_id": 1,
                  "ip_range":
                      {"cidr": "10.0.0.0/8"}},
                 {"id": 12,
                  "group": {
                      "tenant_id":
                          "272bee4c1e624cd4a72a6b0ea55b4582",
                      "name": "test2"},

                  "ip_protocol": "TCP",
                  "from_port": 222,
                  "to_port": 222,
                  "parent_group_id": 1,
                  "ip_range": {}}]},
            {"name": "test2",
             "description": "FAKE_SECURITY_GROUP2",
             "tenant_id": "272bee4c1e624cd4a72a6b0ea55b4582",
             "id": 2,
             "rules": []}
            ]}
        )

    def get_os_security_groups_1(self, **kw):
        return (200, {}, {"security_group":
                {'id': 1, 'name': 'test', 'description': 'FAKE_SECURITY_GROUP'}
        })

    def delete_os_security_groups_1(self, **kw):
        return (202, {}, None)

    def post_os_security_groups(self, body, **kw):
        assert list(body) == ['security_group']
        fakes.assert_has_keys(body['security_group'],
                              required=['name', 'description'])
        r = {'security_group':
                self.get_os_security_groups()[2]['security_groups'][0]}
        return (202, {}, r)

    def put_os_security_groups_1(self, body, **kw):
        assert list(body) == ['security_group']
        fakes.assert_has_keys(body['security_group'],
                              required=['name', 'description'])
        return (205, {}, body)

    #
    # Security Group Rules
    #
    def get_os_security_group_rules(self, **kw):
        return (200, {}, {"security_group_rules": [
                {'id': 1, 'parent_group_id': 1, 'group_id': 2,
                 'ip_protocol': 'TCP', 'from_port': 22, 'to_port': 22,
                 'cidr': '10.0.0.0/8'}
        ]})

    def delete_os_security_group_rules_1(self, **kw):
        return (202, {}, None)

    def delete_os_security_group_rules_11(self, **kw):
        return (202, {}, None)

    def delete_os_security_group_rules_12(self, **kw):
        return (202, {}, None)

    def post_os_security_group_rules(self, body, **kw):
        assert list(body) == ['security_group_rule']
        fakes.assert_has_keys(body['security_group_rule'],
            required=['parent_group_id'],
            optional=['group_id', 'ip_protocol', 'from_port',
                      'to_port', 'cidr'])
        r = {'security_group_rule':
            self.get_os_security_group_rules()[2]['security_group_rules'][0]}
        return (202, {}, r)

    #
    # Security Group Default Rules
    #
    def get_os_security_group_default_rules(self, **kw):
        return (200, {}, {"security_group_default_rules": [
                {'id': 1, 'ip_protocol': 'TCP', 'from_port': 22,
                 'to_port': 22, 'cidr': '10.0.0.0/8'}
        ]})

    def delete_os_security_group_default_rules_1(self, **kw):
        return (202, {}, None)

    def delete_os_security_group_default_rules_11(self, **kw):
        return (202, {}, None)

    def delete_os_security_group_default_rules_12(self, **kw):
        return (202, {}, None)

    def post_os_security_group_default_rules(self, body, **kw):
        assert list(body) == ['security_group_default_rule']
        fakes.assert_has_keys(body['security_group_default_rule'],
            optional=['ip_protocol', 'from_port',
                      'to_port', 'cidr'])
        rules = self.get_os_security_group_default_rules()
        r = {'security_group_default_rule':
            rules[2]['security_group_default_rules'][0]}
        return (202, {}, r)

    #
    # Tenant Usage
    #
    def get_os_simple_tenant_usage(self, **kw):
        return (200, {},
                {six.u('tenant_usages'): [{
                    six.u('total_memory_mb_usage'): 25451.762807466665,
                    six.u('total_vcpus_usage'): 49.71047423333333,
                    six.u('total_hours'): 49.71047423333333,
                    six.u('tenant_id'):
                        six.u('7b0a1d73f8fb41718f3343c207597869'),
                    six.u('stop'): six.u('2012-01-22 19:48:41.750722'),
                    six.u('server_usages'): [{
                        six.u('hours'): 49.71047423333333,
                        six.u('uptime'): 27035,
                        six.u('local_gb'): 0,
                        six.u('ended_at'): None,
                        six.u('name'): six.u('f15image1'),
                        six.u('tenant_id'):
                            six.u('7b0a1d73f8fb41718f3343c207597869'),
                        six.u('vcpus'): 1,
                        six.u('memory_mb'): 512,
                        six.u('state'): six.u('active'),
                        six.u('flavor'): six.u('m1.tiny'),
                        six.u('started_at'):
                            six.u('2012-01-20 18:06:06.479998')}],
                    six.u('start'): six.u('2011-12-25 19:48:41.750687'),
                    six.u('total_local_gb_usage'): 0.0}]})

    def get_os_simple_tenant_usage_tenantfoo(self, **kw):
        return (200, {},
                {six.u('tenant_usage'): {
                    six.u('total_memory_mb_usage'): 25451.762807466665,
                    six.u('total_vcpus_usage'): 49.71047423333333,
                    six.u('total_hours'): 49.71047423333333,
                    six.u('tenant_id'):
                        six.u('7b0a1d73f8fb41718f3343c207597869'),
                    six.u('stop'): six.u('2012-01-22 19:48:41.750722'),
                    six.u('server_usages'): [{
                        six.u('hours'): 49.71047423333333,
                        six.u('uptime'): 27035, six.u('local_gb'): 0,
                        six.u('ended_at'): None,
                        six.u('name'): six.u('f15image1'),
                        six.u('tenant_id'):
                            six.u('7b0a1d73f8fb41718f3343c207597869'),
                        six.u('vcpus'): 1, six.u('memory_mb'): 512,
                        six.u('state'): six.u('active'),
                        six.u('flavor'): six.u('m1.tiny'),
                        six.u('started_at'):
                            six.u('2012-01-20 18:06:06.479998')}],
                    six.u('start'): six.u('2011-12-25 19:48:41.750687'),
                    six.u('total_local_gb_usage'): 0.0}})

    def get_os_simple_tenant_usage_test(self, **kw):
        return (200, {}, {six.u('tenant_usage'): {
            six.u('total_memory_mb_usage'): 25451.762807466665,
            six.u('total_vcpus_usage'): 49.71047423333333,
            six.u('total_hours'): 49.71047423333333,
            six.u('tenant_id'): six.u('7b0a1d73f8fb41718f3343c207597869'),
            six.u('stop'): six.u('2012-01-22 19:48:41.750722'),
            six.u('server_usages'): [{
                six.u('hours'): 49.71047423333333,
                six.u('uptime'): 27035, six.u('local_gb'): 0,
                six.u('ended_at'): None,
                six.u('name'): six.u('f15image1'),
                six.u('tenant_id'): six.u('7b0a1d73f8fb41718f3343c207597869'),
                six.u('vcpus'): 1, six.u('memory_mb'): 512,
                six.u('state'): six.u('active'),
                six.u('flavor'): six.u('m1.tiny'),
                six.u('started_at'): six.u('2012-01-20 18:06:06.479998')}],
            six.u('start'): six.u('2011-12-25 19:48:41.750687'),
            six.u('total_local_gb_usage'): 0.0}})

    def get_os_simple_tenant_usage_tenant_id(self, **kw):
        return (200, {}, {six.u('tenant_usage'): {
            six.u('total_memory_mb_usage'): 25451.762807466665,
            six.u('total_vcpus_usage'): 49.71047423333333,
            six.u('total_hours'): 49.71047423333333,
            six.u('tenant_id'): six.u('7b0a1d73f8fb41718f3343c207597869'),
            six.u('stop'): six.u('2012-01-22 19:48:41.750722'),
            six.u('server_usages'): [{
                six.u('hours'): 49.71047423333333,
                six.u('uptime'): 27035, six.u('local_gb'): 0,
                six.u('ended_at'): None,
                six.u('name'): six.u('f15image1'),
                six.u('tenant_id'): six.u('7b0a1d73f8fb41718f3343c207597869'),
                six.u('vcpus'): 1, six.u('memory_mb'): 512,
                six.u('state'): six.u('active'),
                six.u('flavor'): six.u('m1.tiny'),
                six.u('started_at'): six.u('2012-01-20 18:06:06.479998')}],
            six.u('start'): six.u('2011-12-25 19:48:41.750687'),
            six.u('total_local_gb_usage'): 0.0}})
    #
    # Certificates
    #

    def get_os_certificates_root(self, **kw):
        return (
            200,
            {},
            {'certificate': {'private_key': None, 'data': 'foo'}}
        )

    def post_os_certificates(self, **kw):
        return (
            200,
            {},
            {'certificate': {'private_key': 'foo', 'data': 'bar'}}
        )

    #
    # Aggregates
    #

    def get_os_aggregates(self, *kw):
        return (200, {}, {"aggregates": [
            {'id': '1',
             'name': 'test',
             'availability_zone': 'nova1'},
            {'id': '2',
             'name': 'test2',
             'availability_zone': 'nova1'},
            {'id': '3',
             'name': 'test3',
             'metadata': {'test': "dup", "none_key": "Nine"}},
        ]})

    def _return_aggregate(self):
        r = {'aggregate': self.get_os_aggregates()[2]['aggregates'][0]}
        return (200, {}, r)

    def _return_aggregate_3(self):
        r = {'aggregate': self.get_os_aggregates()[2]['aggregates'][2]}
        return (200, {}, r)

    def get_os_aggregates_1(self, **kw):
        return self._return_aggregate()

    def get_os_aggregates_3(self, **kw):
        return self._return_aggregate_3()

    def post_os_aggregates(self, body, **kw):
        return self._return_aggregate()

    def put_os_aggregates_1(self, body, **kw):
        return self._return_aggregate()

    def put_os_aggregates_2(self, body, **kw):
        return self._return_aggregate()

    def put_os_aggregates_3(self, body, **kw):
        return self._return_aggregate_3()

    def post_os_aggregates_1_action(self, body, **kw):
        return self._return_aggregate()

    def post_os_aggregates_2_action(self, body, **kw):
        return self._return_aggregate()

    def post_os_aggregates_3_action(self, body, **kw):
        return self._return_aggregate_3()

    def delete_os_aggregates_1(self, **kw):
        return (202, {}, None)

    #
    # Services
    #
    def get_os_services(self, **kw):
        host = kw.get('host', 'host1')
        binary = kw.get('binary', 'nova-compute')
        return (200, {}, {'services':
                     [{'binary': binary,
                       'host': host,
                       'zone': 'nova',
                       'status': 'enabled',
                       'state': 'up',
                       'updated_at': datetime.datetime(
                           2012, 10, 29, 13, 42, 2
                       )},
                      {'binary': binary,
                       'host': host,
                       'zone': 'nova',
                       'status': 'disabled',
                       'state': 'down',
                       'updated_at': datetime.datetime(
                           2012, 9, 18, 8, 3, 38
                       )},
                      ]})

    def put_os_services_enable(self, body, **kw):
        return (200, {}, {'service': {'host': body['host'],
                                      'binary': body['binary'],
                                      'status': 'enabled'}})

    def put_os_services_disable(self, body, **kw):
        return (200, {}, {'service': {'host': body['host'],
                                      'binary': body['binary'],
                                      'status': 'disabled'}})

    def put_os_services_disable_log_reason(self, body, **kw):
        return (200, {}, {'service': {'host': body['host'],
                          'binary': body['binary'],
                          'status': 'disabled',
                          'disabled_reason': body['disabled_reason']}})

    def delete_os_services_1(self, **kw):
        return (204, {}, None)

    #
    # Fixed IPs
    #
    def get_os_fixed_ips_192_168_1_1(self, *kw):
        return (200, {}, {"fixed_ip":
                      {'cidr': '192.168.1.0/24',
                       'address': '192.168.1.1',
                       'hostname': 'foo',
                       'host': 'bar'}})

    def post_os_fixed_ips_192_168_1_1_action(self, body, **kw):
        return (202, {}, None)

    #
    # Hosts
    #
    def get_os_hosts_host(self, *kw):
        return (200, {}, {'host':
                [{'resource': {'project': '(total)', 'host': 'dummy',
                  'cpu': 16, 'memory_mb': 32234, 'disk_gb': 128}},
                 {'resource': {'project': '(used_now)', 'host': 'dummy',
                  'cpu': 1, 'memory_mb': 2075, 'disk_gb': 45}},
                 {'resource': {'project': '(used_max)', 'host': 'dummy',
                  'cpu': 1, 'memory_mb': 2048, 'disk_gb': 30}},
                 {'resource': {'project': 'admin', 'host': 'dummy',
                  'cpu': 1, 'memory_mb': 2048, 'disk_gb': 30}}]})

    def get_os_hosts(self, **kw):
        zone = kw.get('zone', 'nova1')
        return (200, {}, {'hosts':
                    [{'host': 'host1',
                      'service': 'nova-compute',
                      'zone': zone},
                     {'host': 'host1',
                      'service': 'nova-cert',
                      'zone': zone}]})

    def get_os_hosts_sample_host(self, *kw):
        return (200, {}, {'host': [{'resource': {'host': 'sample_host'}}], })

    def put_os_hosts_sample_host_1(self, body, **kw):
        return (200, {}, {'host': 'sample-host_1',
                      'status': 'enabled'})

    def put_os_hosts_sample_host_2(self, body, **kw):
        return (200, {}, {'host': 'sample-host_2',
                      'maintenance_mode': 'on_maintenance'})

    def put_os_hosts_sample_host_3(self, body, **kw):
        return (200, {}, {'host': 'sample-host_3',
                      'status': 'enabled',
                      'maintenance_mode': 'on_maintenance'})

    def get_os_hosts_sample_host_reboot(self, **kw):
        return (200, {}, {'host': 'sample_host',
                          'power_action': 'reboot'})

    def get_os_hosts_sample_host_startup(self, **kw):
        return (200, {}, {'host': 'sample_host',
                          'power_action': 'startup'})

    def get_os_hosts_sample_host_shutdown(self, **kw):
        return (200, {}, {'host': 'sample_host',
                          'power_action': 'shutdown'})

    def put_os_hosts_sample_host(self, body, **kw):
        result = {'host': 'dummy'}
        result.update(body)
        return (200, {}, result)

    def get_os_hypervisors(self, **kw):
        return (200, {}, {"hypervisors": [
                    {'id': 1234, 'hypervisor_hostname': 'hyper1'},
                    {'id': 5678, 'hypervisor_hostname': 'hyper2'},
                    ]})

    def get_os_hypervisors_detail(self, **kw):
        return (200, {}, {"hypervisors": [
                    {'id': 1234,
                     'service': {'id': 1, 'host': 'compute1'},
                     'vcpus': 4,
                     'memory_mb': 10 * 1024,
                     'local_gb': 250,
                     'vcpus_used': 2,
                     'memory_mb_used': 5 * 1024,
                     'local_gb_used': 125,
                     'hypervisor_type': "xen",
                     'hypervisor_version': 3,
                     'hypervisor_hostname': "hyper1",
                     'free_ram_mb': 5 * 1024,
                     'free_disk_gb': 125,
                     'current_workload': 2,
                     'running_vms': 2,
                     'cpu_info': 'cpu_info',
                     'disk_available_least': 100},
                    {'id': 2,
                     'service': {'id': 2, 'host': "compute2"},
                     'vcpus': 4,
                     'memory_mb': 10 * 1024,
                     'local_gb': 250,
                     'vcpus_used': 2,
                     'memory_mb_used': 5 * 1024,
                     'local_gb_used': 125,
                     'hypervisor_type': "xen",
                     'hypervisor_version': 3,
                     'hypervisor_hostname': "hyper2",
                     'free_ram_mb': 5 * 1024,
                     'free_disk_gb': 125,
                     'current_workload': 2,
                     'running_vms': 2,
                     'cpu_info': 'cpu_info',
                     'disk_available_least': 100}
                    ]})

    def get_os_hypervisors_statistics(self, **kw):
        return (200, {}, {"hypervisor_statistics": {
                    'count': 2,
                    'vcpus': 8,
                    'memory_mb': 20 * 1024,
                    'local_gb': 500,
                    'vcpus_used': 4,
                    'memory_mb_used': 10 * 1024,
                    'local_gb_used': 250,
                    'free_ram_mb': 10 * 1024,
                    'free_disk_gb': 250,
                    'current_workload': 4,
                    'running_vms': 4,
                    'disk_available_least': 200,
                    }})

    def get_os_hypervisors_hyper_search(self, **kw):
        return (200, {}, {'hypervisors': [
                    {'id': 1234, 'hypervisor_hostname': 'hyper1'},
                    {'id': 5678, 'hypervisor_hostname': 'hyper2'}
                    ]})

    def get_os_hypervisors_hyper_servers(self, **kw):
        return (200, {}, {'hypervisors': [
                    {'id': 1234,
                     'hypervisor_hostname': 'hyper1',
                     'servers': [
                            {'name': 'inst1', 'uuid': 'uuid1'},
                            {'name': 'inst2', 'uuid': 'uuid2'}
                            ]},
                    {'id': 5678,
                     'hypervisor_hostname': 'hyper2',
                     'servers': [
                            {'name': 'inst3', 'uuid': 'uuid3'},
                            {'name': 'inst4', 'uuid': 'uuid4'}
                            ]}
                    ]})

    def get_os_hypervisors_hyper_no_servers_servers(self, **kw):
        return (200, {}, {'hypervisors':
                          [{'id': 1234, 'hypervisor_hostname': 'hyper1'}]})

    def get_os_hypervisors_1234(self, **kw):
        return (200, {}, {'hypervisor':
                          {'id': 1234,
                           'service': {'id': 1, 'host': 'compute1'},
                           'vcpus': 4,
                           'memory_mb': 10 * 1024,
                           'local_gb': 250,
                           'vcpus_used': 2,
                           'memory_mb_used': 5 * 1024,
                           'local_gb_used': 125,
                           'hypervisor_type': "xen",
                           'hypervisor_version': 3,
                           'hypervisor_hostname': "hyper1",
                           'free_ram_mb': 5 * 1024,
                           'free_disk_gb': 125,
                           'current_workload': 2,
                           'running_vms': 2,
                           'cpu_info': 'cpu_info',
                           'disk_available_least': 100}})

    def get_os_hypervisors_1234_uptime(self, **kw):
        return (200, {}, {'hypervisor':
                          {'id': 1234,
                           'hypervisor_hostname': "hyper1",
                           'uptime': "fake uptime"}})

    def get_os_networks(self, **kw):
        return (200, {}, {'networks': [{"label": "1", "cidr": "10.0.0.0/24",
                'project_id': '4ffc664c198e435e9853f2538fbcd7a7',
                'id': '1', 'vlan': '1234'}]})

    def delete_os_networks_1(self, **kw):
        return (202, {}, None)

    def post_os_networks(self, **kw):
        return (202, {}, {'network': kw})

    def get_os_networks_1(self, **kw):
        return (200, {}, {'network': {"label": "1", "cidr": "10.0.0.0/24",
                                      "id": "1"}})

    def delete_os_networks_networkdelete(self, **kw):
        return (202, {}, None)

    def post_os_networks_add(self, **kw):
        return (202, {}, None)

    def post_os_networks_networkdisassociate_action(self, **kw):
        return (202, {}, None)

    def get_os_fping(self, **kw):
        return (
            200, {}, {
                'servers': [
                    {
                        "id": "1",
                        "project_id": "fake-project",
                        "alive": True,
                    },
                    {
                        "id": "2",
                        "project_id": "fake-project",
                        "alive": True,
                    },
                ]
            }
        )

    def get_os_fping_1(self, **kw):
        return (
            200, {}, {
                'server': {
                    "id": "1",
                    "project_id": "fake-project",
                    "alive": True,
                }
            }
        )

    def post_os_networks_1_action(self, **kw):
        return (202, {}, None)

    def post_os_networks_networktest_action(self, **kw):
        return (202, {}, None)

    def post_os_networks_2_action(self, **kw):
        return (202, {}, None)

    def get_os_availability_zone(self, **kw):
        return (200, {}, {"availabilityZoneInfo": [
                              {"zoneName": "zone-1",
                               "zoneState": {"available": True},
                               "hosts": None},
                              {"zoneName": "zone-2",
                               "zoneState": {"available": False},
                               "hosts": None}]})

    def get_os_availability_zone_detail(self, **kw):
        return (200, {}, {"availabilityZoneInfo": [
                              {"zoneName": "zone-1",
                               "zoneState": {"available": True},
                               "hosts": {
                                   "fake_host-1": {
                                       "nova-compute": {"active": True,
                                           "available": True,
                                           "updated_at":
                                   datetime.datetime(
                                       2012, 12, 26, 14, 45, 25, 0
                                   )}}}},
                              {"zoneName": "internal",
                               "zoneState": {"available": True},
                               "hosts": {
                                   "fake_host-1": {
                                       "nova-sched": {
                                           "active": True,
                                           "available": True,
                                           "updated_at":
                                   datetime.datetime(
                                       2012, 12, 26, 14, 45, 25, 0
                                   )}},
                                   "fake_host-2": {
                                       "nova-network": {
                                           "active": True,
                                           "available": False,
                                           "updated_at":
                                   datetime.datetime(
                                       2012, 12, 26, 14, 45, 24, 0
                                   )}}}},
                              {"zoneName": "zone-2",
                               "zoneState": {"available": False},
                               "hosts": None}]})

    def get_servers_1234_os_interface(self, **kw):
        return (200, {}, {"interfaceAttachments": [
                             {"port_state": "ACTIVE",
                              "net_id": "net-id-1",
                              "port_id": "port-id-1",
                              "mac_address": "aa:bb:cc:dd:ee:ff",
                              "fixed_ips": [{"ip_address": "1.2.3.4"}],
                              },
                             {"port_state": "ACTIVE",
                              "net_id": "net-id-1",
                              "port_id": "port-id-1",
                              "mac_address": "aa:bb:cc:dd:ee:ff",
                              "fixed_ips": [{"ip_address": "1.2.3.4"}],
                              }]})

    def post_servers_1234_os_interface(self, **kw):
        return (200, {}, {'interfaceAttachment': {}})

    def delete_servers_1234_os_interface_port_id(self, **kw):
        return (200, {}, None)

    # NOTE (vkhomenko):
    # Volume responses was taken from:
    # https://wiki.openstack.org/wiki/CreateVolumeFromImage
    # http://jorgew.github.com/block-storage-api/content/
    # GET_listDetailVolumes_v1__tenantId__volumes_detail_.html
    # I suppose they are outdated and should be updated after Cinder released

    def get_volumes_detail(self, **kw):
        return (200, {}, {"volumes": [
            {
                "display_name": "Work",
                "display_description": "volume for work",
                "status": "ATTACHED",
                "id": "15e59938-07d5-11e1-90e3-e3dffe0c5983",
                "created_at": "2011-09-09T00:00:00Z",
                "attached": "2011-11-11T00:00:00Z",
                "size": 1024,
                "attachments": [
                    {"id": "3333",
                     "links": ''}],
                "metadata": {}},
            {
                "display_name": "Work2",
                "display_description": "volume for work2",
                "status": "ATTACHED",
                "id": "15e59938-07d5-11e1-90e3-ee32ba30feaa",
                "created_at": "2011-09-09T00:00:00Z",
                "attached": "2011-11-11T00:00:00Z",
                "size": 1024,
                "attachments": [
                    {"id": "2222",
                     "links": ''}],
                "metadata": {}}]})

    def get_volumes(self, **kw):
        return (200, {}, {"volumes": [
            {
                "display_name": "Work",
                "display_description": "volume for work",
                "status": "ATTACHED",
                "id": "15e59938-07d5-11e1-90e3-e3dffe0c5983",
                "created_at": "2011-09-09T00:00:00Z",
                "attached": "2011-11-11T00:00:00Z",
                "size": 1024,
                "attachments": [
                    {"id": "3333",
                     "links": ''}],
                "metadata": {}},
            {
                "display_name": "Work2",
                "display_description": "volume for work2",
                "status": "ATTACHED",
                "id": "15e59938-07d5-11e1-90e3-ee32ba30feaa",
                "created_at": "2011-09-09T00:00:00Z",
                "attached": "2011-11-11T00:00:00Z",
                "size": 1024,
                "attachments": [
                    {"id": "2222",
                     "links": ''}],
                "metadata": {}}]})

    def get_volumes_15e59938_07d5_11e1_90e3_e3dffe0c5983(self, **kw):
        return (200, {}, {
                "volume": self.get_volumes_detail()[2]['volumes'][0]})

    def get_volumes_15e59938_07d5_11e1_90e3_ee32ba30feaa(self, **kw):
        return (200, {}, {
                "volume": self.get_volumes_detail()[2]['volumes'][1]})

    def post_volumes(self, **kw):
        return (200, {}, {"volume":
                {"status": "creating",
                 "display_name": "vol-007",
                 "attachments": [(0)],
                 "availability_zone": "cinder",
                 "created_at": "2012-08-13T10:57:17.000000",
                 "display_description": "create volume from image",
                 "image_id": "f4cf905f-7c58-4d7b-8314-8dd8a2d1d483",
                 "volume_type": "None",
                 "metadata": {},
                 "id": "5cb239f6-1baf-4fe1-bd78-c852cf00fa39",
                 "size": 1}})

    def delete_volumes_15e59938_07d5_11e1_90e3_e3dffe0c5983(self, **kw):
        return (200, {}, {})

    def delete_volumes_15e59938_07d5_11e1_90e3_ee32ba30feaa(self, **kw):
        return (200, {}, {})

    def post_servers_1234_os_volume_attachments(self, **kw):
        return (200, {}, {"volumeAttachment":
                {"device": "/dev/vdb",
                 "volumeId": 2}})

    def put_servers_1234_os_volume_attachments_Work(self, **kw):
        return (200, {}, {"volumeAttachment": {"volumeId": 2}})

    def get_servers_1234_os_volume_attachments(self, **kw):
        return (200, {}, {"volumeAttachments": [
                            {"display_name": "Work",
                             "display_description": "volume for work",
                             "status": "ATTACHED",
                             "id": "15e59938-07d5-11e1-90e3-e3dffe0c5983",
                             "created_at": "2011-09-09T00:00:00Z",
                             "attached": "2011-11-11T00:00:00Z",
                             "size": 1024,
                             "attachments": [
                                {"id": "3333",
                                 "links": ''}],
                             "metadata": {}}]})

    def get_servers_1234_os_volume_attachments_Work(self, **kw):
        return (200, {}, {"volumeAttachment":
                            {"display_name": "Work",
                             "display_description": "volume for work",
                             "status": "ATTACHED",
                             "id": "15e59938-07d5-11e1-90e3-e3dffe0c5983",
                             "created_at": "2011-09-09T00:00:00Z",
                             "attached": "2011-11-11T00:00:00Z",
                             "size": 1024,
                             "attachments": [
                                {"id": "3333",
                                 "links": ''}],
                             "metadata": {}}})

    def delete_servers_1234_os_volume_attachments_Work(self, **kw):
        return (200, {}, {})

    def get_servers_1234_os_instance_actions(self, **kw):
        return (200, {}, {"instanceActions":
                [{"instance_uuid": "1234",
                  "user_id": "b968c25e04ab405f9fe4e6ca54cce9a5",
                  "start_time": "2013-03-25T13:45:09.000000",
                  "request_id": "req-abcde12345",
                  "action": "create",
                  "message": None,
                  "project_id": "04019601fe3648c0abd4f4abfb9e6106"}]})

    def get_servers_1234_os_instance_actions_req_abcde12345(self, **kw):
        return (200, {}, {"instanceAction":
                {"instance_uuid": "1234",
                 "user_id": "b968c25e04ab405f9fe4e6ca54cce9a5",
                 "start_time": "2013-03-25T13:45:09.000000",
                 "request_id": "req-abcde12345",
                 "action": "create",
                 "message": None,
                 "project_id": "04019601fe3648c0abd4f4abfb9e6106"}})

    def post_servers_uuid1_action(self, **kw):
        return 202, {}, {}

    def post_servers_uuid2_action(self, **kw):
        return 202, {}, {}

    def post_servers_uuid3_action(self, **kw):
        return 202, {}, {}

    def post_servers_uuid4_action(self, **kw):
        return 202, {}, {}

    def get_os_cells_child_cell(self, **kw):
        cell = {'cell': {
                    'username': 'cell1_user',
                    'name': 'cell1',
                    'rpc_host': '10.0.1.10',
                    'info': {
                        'username': 'cell1_user',
                        'rpc_host': '10.0.1.10',
                        'type': 'child',
                        'name': 'cell1',
                        'rpc_port': 5673
                        },
                    'type': 'child',
                    'rpc_port': 5673,
                    'loaded': True
                }}
        return (200, {}, cell)

    def get_os_cells_capacities(self, **kw):
        cell_capacities_response = {"cell": {"capacities": {"ram_free": {
            "units_by_mb": {"8192": 0, "512": 13, "4096": 1, "2048": 3,
                            "16384": 0}, "total_mb": 7680}, "disk_free": {
            "units_by_mb": {"81920": 11, "20480": 46, "40960": 23, "163840": 5,
                            "0": 0}, "total_mb": 1052672}}}}
        return (200, {}, cell_capacities_response)

    def get_os_cells_child_cell_capacities(self, **kw):
        return self.get_os_cells_capacities()

    def get_os_migrations(self, **kw):
        migrations = {'migrations':
                          [{
                               "created_at": "2012-10-29T13:42:02.000000",
                               "dest_compute": "compute2",
                               "dest_host": "1.2.3.4",
                               "dest_node": "node2",
                               "id": 1234,
                               "instance_uuid": "instance_id_123",
                               "new_instance_type_id": 2,
                               "old_instance_type_id": 1,
                               "source_compute": "compute1",
                               "source_node": "node1",
                               "status": "Done",
                               "updated_at": "2012-10-29T13:42:02.000000"
                           }]}
        return (200, {}, migrations)

    def post_os_server_external_events(self, **kw):
        return (200, {}, {'events': [
                    {'name': 'network-changed',
                     'server_uuid': '1234'}]})

    #
    # Server Groups
    #

    def get_os_server_groups(self, *kw):
        return (200, {},
                {"server_groups": [
                 {"members": [], "metadata": {},
                  "id": "2cbd51f4-fafe-4cdb-801b-cf913a6f288b",
                  "policies": [], "name": "ig1"},
                 {"members": [], "metadata": {},
                  "id": "4473bb03-4370-4bfb-80d3-dc8cffc47d94",
                  "policies": ["anti-affinity"], "name": "ig2"},
                 {"members": [], "metadata": {"key": "value"},
                  "id": "31ab9bdb-55e1-4ac3-b094-97eeb1b65cc4",
                  "policies": [], "name": "ig3"},
                 {"members": ["2dccb4a1-02b9-482a-aa23-5799490d6f5d"],
                  "metadata": {},
                  "id": "4890bb03-7070-45fb-8453-d34556c87d94",
                  "policies": ["anti-affinity"], "name": "ig2"}]})

    def _return_server_group(self):
        r = {'server_group':
             self.get_os_server_groups()[2]['server_groups'][0]}
        return (200, {}, r)

    def post_os_server_groups(self, body, **kw):
        return self._return_server_group()

    def get_os_server_groups_2cbd51f4_fafe_4cdb_801b_cf913a6f288b(self,
                                                                    **kw):
        return self._return_server_group()

    def put_os_server_groups_2cbd51f4_fafe_4cdb_801b_cf913a6f288b(self,
                                                                    **kw):
        return self._return_server_group()

    def post_os_server_groups_2cbd51f4_fafe_4cdb_801b_cf913a6f288b_action(
            self, body, **kw):
        return self._return_server_group()

    def delete_os_server_groups_2cbd51f4_fafe_4cdb_801b_cf913a6f288b(
            self, **kw):
        return (202, {}, None)
