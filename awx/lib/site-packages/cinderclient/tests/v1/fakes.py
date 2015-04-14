# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright (c) 2011 OpenStack Foundation
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

from datetime import datetime

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from cinderclient import client as base_client
from cinderclient.tests import fakes
import cinderclient.tests.utils as utils
from cinderclient.v1 import client


def _stub_volume(**kwargs):
    volume = {
        'id': '1234',
        'display_name': None,
        'display_description': None,
        "attachments": [],
        "bootable": "false",
        "availability_zone": "cinder",
        "created_at": "2012-08-27T00:00:00.000000",
        "id": '00000000-0000-0000-0000-000000000000',
        "metadata": {},
        "size": 1,
        "snapshot_id": None,
        "status": "available",
        "volume_type": "None",
    }
    volume.update(kwargs)
    return volume


def _stub_snapshot(**kwargs):
    snapshot = {
        "created_at": "2012-08-28T16:30:31.000000",
        "display_description": None,
        "display_name": None,
        "id": '11111111-1111-1111-1111-111111111111',
        "size": 1,
        "status": "available",
        "volume_id": '00000000-0000-0000-0000-000000000000',
    }
    snapshot.update(kwargs)
    return snapshot


def _self_href(base_uri, tenant_id, backup_id):
    return '%s/v1/%s/backups/%s' % (base_uri, tenant_id, backup_id)


def _bookmark_href(base_uri, tenant_id, backup_id):
    return '%s/%s/backups/%s' % (base_uri, tenant_id, backup_id)


def _stub_backup_full(id, base_uri, tenant_id):
    return {
        'id': id,
        'name': 'backup',
        'description': 'nightly backup',
        'volume_id': '712f4980-5ac1-41e5-9383-390aa7c9f58b',
        'container': 'volumebackups',
        'object_count': 220,
        'size': 10,
        'availability_zone': 'az1',
        'created_at': '2013-04-12T08:16:37.000000',
        'status': 'available',
        'links': [
            {
                'href': _self_href(base_uri, tenant_id, id),
                'rel': 'self'
            },
            {
                'href': _bookmark_href(base_uri, tenant_id, id),
                'rel': 'bookmark'
            }
        ]
    }


def _stub_backup(id, base_uri, tenant_id):
    return {
        'id': id,
        'name': 'backup',
        'links': [
            {
                'href': _self_href(base_uri, tenant_id, id),
                'rel': 'self'
            },
            {
                'href': _bookmark_href(base_uri, tenant_id, id),
                'rel': 'bookmark'
            }
        ]
    }


def _stub_restore():
    return {'volume_id': '712f4980-5ac1-41e5-9383-390aa7c9f58b'}


def _stub_qos_full(id, base_uri, tenant_id, name=None, specs=None):
    if not name:
        name = 'fake-name'
    if not specs:
        specs = {}

    return {
        'qos_specs': {
            'id': id,
            'name': name,
            'consumer': 'back-end',
            'specs': specs,
        },
        'links': {
            'href': _bookmark_href(base_uri, tenant_id, id),
            'rel': 'bookmark'
        }
    }


def _stub_qos_associates(id, name):
    return {
        'assoications_type': 'volume_type',
        'name': name,
        'id': id,
    }


def _stub_transfer_full(id, base_uri, tenant_id):
    return {
        'id': id,
        'name': 'transfer',
        'volume_id': '8c05f861-6052-4df6-b3e0-0aebfbe686cc',
        'created_at': '2013-04-12T08:16:37.000000',
        'auth_key': '123456',
        'links': [
            {
                'href': _self_href(base_uri, tenant_id, id),
                'rel': 'self'
            },
            {
                'href': _bookmark_href(base_uri, tenant_id, id),
                'rel': 'bookmark'
            }
        ]
    }


def _stub_transfer(id, base_uri, tenant_id):
    return {
        'id': id,
        'name': 'transfer',
        'volume_id': '8c05f861-6052-4df6-b3e0-0aebfbe686cc',
        'links': [
            {
                'href': _self_href(base_uri, tenant_id, id),
                'rel': 'self'
            },
            {
                'href': _bookmark_href(base_uri, tenant_id, id),
                'rel': 'bookmark'
            }
        ]
    }


def _stub_extend(id, new_size):
    return {'volume_id': '712f4980-5ac1-41e5-9383-390aa7c9f58b'}


class FakeClient(fakes.FakeClient, client.Client):

    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url',
                               extensions=kwargs.get('extensions'))
        self.client = FakeHTTPClient(**kwargs)

    def get_volume_api_version_from_endpoint(self):
        return self.client.get_volume_api_version_from_endpoint()


class FakeHTTPClient(base_client.HTTPClient):

    def __init__(self, **kwargs):
        self.username = 'username'
        self.password = 'password'
        self.auth_url = 'auth_url'
        self.callstack = []
        self.management_url = 'http://10.0.2.15:8776/v1/fake'

    def _cs_request(self, url, method, **kwargs):
        # Check that certain things are called correctly
        if method in ['GET', 'DELETE']:
            assert 'body' not in kwargs
        elif method == 'PUT':
            assert 'body' in kwargs

        # Call the method
        args = urlparse.parse_qsl(urlparse.urlparse(url)[4])
        kwargs.update(args)
        munged_url = url.rsplit('?', 1)[0]
        munged_url = munged_url.strip('/').replace('/', '_').replace('.', '_')
        munged_url = munged_url.replace('-', '_')

        callback = "%s_%s" % (method.lower(), munged_url)

        if not hasattr(self, callback):
            raise AssertionError('Called unknown API method: %s %s, '
                                 'expected fakes method name: %s' %
                                 (method, url, callback))

        # Note the call
        self.callstack.append((method, url, kwargs.get('body', None)))
        status, headers, body = getattr(self, callback)(**kwargs)
        r = utils.TestResponse({
            "status_code": status,
            "text": body,
            "headers": headers,
        })
        return r, body

        if hasattr(status, 'items'):
            return utils.TestResponse(status), body
        else:
            return utils.TestResponse({"status": status}), body

    def get_volume_api_version_from_endpoint(self):
        magic_tuple = urlparse.urlsplit(self.management_url)
        scheme, netloc, path, query, frag = magic_tuple
        return path.lstrip('/').split('/')[0][1:]

    #
    # Snapshots
    #

    def get_snapshots_detail(self, **kw):
        return (200, {}, {'snapshots': [
            _stub_snapshot(),
        ]})

    def get_snapshots_1234(self, **kw):
        return (200, {}, {'snapshot': _stub_snapshot(id='1234')})

    def get_snapshots_5678(self, **kw):
        return (200, {}, {'snapshot': _stub_snapshot(id='5678')})

    def put_snapshots_1234(self, **kw):
        snapshot = _stub_snapshot(id='1234')
        snapshot.update(kw['body']['snapshot'])
        return (200, {}, {'snapshot': snapshot})

    def post_snapshots_1234_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(list(body)) == 1
        action = list(body)[0]
        if action == 'os-reset_status':
            assert 'status' in body['os-reset_status']
        elif action == 'os-update_snapshot_status':
            assert 'status' in body['os-update_snapshot_status']
        else:
            raise AssertionError("Unexpected action: %s" % action)
        return (resp, {}, _body)

    def post_snapshots_5678_action(self, body, **kw):
        return self.post_snapshots_1234_action(body, **kw)

    def delete_snapshots_1234(self, **kw):
        return (202, {}, {})

    def delete_snapshots_5678(self, **kw):
        return (202, {}, {})

    #
    # Volumes
    #

    def put_volumes_1234(self, **kw):
        volume = _stub_volume(id='1234')
        volume.update(kw['body']['volume'])
        return (200, {}, {'volume': volume})

    def get_volumes(self, **kw):
        return (200, {}, {"volumes": [
            {'id': 1234, 'name': 'sample-volume'},
            {'id': 5678, 'name': 'sample-volume2'}
        ]})

    # TODO(jdg): This will need to change
    # at the very least it's not complete
    def get_volumes_detail(self, **kw):
        return (200, {}, {"volumes": [
            {'id': kw.get('id', 1234),
             'name': 'sample-volume',
             'attachments': [{'server_id': 1234}]},
        ]})

    def get_volumes_1234(self, **kw):
        r = {'volume': self.get_volumes_detail(id=1234)[2]['volumes'][0]}
        return (200, {}, r)

    def get_volumes_5678(self, **kw):
        r = {'volume': self.get_volumes_detail(id=5678)[2]['volumes'][0]}
        return (200, {}, r)

    def get_volumes_1234_encryption(self, **kw):
        r = {'encryption_key_id': 'id'}
        return (200, {}, r)

    def post_volumes_1234_action(self, body, **kw):
        _body = None
        resp = 202
        assert len(list(body)) == 1
        action = list(body)[0]
        if action == 'os-attach':
            assert sorted(list(body[action])) == ['instance_uuid',
                                                  'mode',
                                                  'mountpoint']
        elif action == 'os-detach':
            assert body[action] is None
        elif action == 'os-reserve':
            assert body[action] is None
        elif action == 'os-unreserve':
            assert body[action] is None
        elif action == 'os-initialize_connection':
            assert list(body[action]) == ['connector']
            return (202, {}, {'connection_info': 'foos'})
        elif action == 'os-terminate_connection':
            assert list(body[action]) == ['connector']
        elif action == 'os-begin_detaching':
            assert body[action] is None
        elif action == 'os-roll_detaching':
            assert body[action] is None
        elif action == 'os-reset_status':
            assert 'status' in body[action]
        elif action == 'os-extend':
            assert list(body[action]) == ['new_size']
        elif action == 'os-migrate_volume':
            assert 'host' in body[action]
            assert 'force_host_copy' in body[action]
        elif action == 'os-update_readonly_flag':
            assert list(body[action]) == ['readonly']
        elif action == 'os-set_bootable':
            assert list(body[action]) == ['bootable']
        else:
            raise AssertionError("Unexpected action: %s" % action)
        return (resp, {}, _body)

    def post_volumes_5678_action(self, body, **kw):
        return self.post_volumes_1234_action(body, **kw)

    def post_volumes(self, **kw):
        return (202, {}, {'volume': {}})

    def delete_volumes_1234(self, **kw):
        return (202, {}, None)

    def delete_volumes_5678(self, **kw):
        return (202, {}, None)

    #
    # Quotas
    #

    def get_os_quota_sets_test(self, **kw):
        return (200, {}, {'quota_set': {
                          'tenant_id': 'test',
                          'metadata_items': [],
                          'volumes': 1,
                          'snapshots': 1,
                          'gigabytes': 1}})

    def get_os_quota_sets_test_defaults(self):
        return (200, {}, {'quota_set': {
                          'tenant_id': 'test',
                          'metadata_items': [],
                          'volumes': 1,
                          'snapshots': 1,
                          'gigabytes': 1}})

    def put_os_quota_sets_test(self, body, **kw):
        assert list(body) == ['quota_set']
        fakes.assert_has_keys(body['quota_set'],
                              required=['tenant_id'])
        return (200, {}, {'quota_set': {
                          'tenant_id': 'test',
                          'metadata_items': [],
                          'volumes': 2,
                          'snapshots': 2,
                          'gigabytes': 1}})

    def delete_os_quota_sets_1234(self, **kw):
        return (200, {}, {})

    def delete_os_quota_sets_test(self, **kw):
        return (200, {}, {})

    #
    # Quota Classes
    #

    def get_os_quota_class_sets_test(self, **kw):
        return (200, {}, {'quota_class_set': {
                          'class_name': 'test',
                          'metadata_items': [],
                          'volumes': 1,
                          'snapshots': 1,
                          'gigabytes': 1}})

    def put_os_quota_class_sets_test(self, body, **kw):
        assert list(body) == ['quota_class_set']
        fakes.assert_has_keys(body['quota_class_set'],
                              required=['class_name'])
        return (200, {}, {'quota_class_set': {
                          'class_name': 'test',
                          'metadata_items': [],
                          'volumes': 2,
                          'snapshots': 2,
                          'gigabytes': 1}})

    #
    # VolumeTypes
    #
    def get_types(self, **kw):
        return (200, {}, {
            'volume_types': [{'id': 1,
                              'name': 'test-type-1',
                              'extra_specs': {}},
                             {'id': 2,
                              'name': 'test-type-2',
                              'extra_specs': {}}]})

    def get_types_1(self, **kw):
        return (200, {}, {'volume_type': {'id': 1,
                          'name': 'test-type-1',
                          'extra_specs': {}}})

    def get_types_2(self, **kw):
        return (200, {}, {'volume_type': {'id': 2,
                          'name': 'test-type-2',
                          'extra_specs': {}}})

    def post_types(self, body, **kw):
        return (202, {}, {'volume_type': {'id': 3,
                          'name': 'test-type-3',
                          'extra_specs': {}}})

    def post_types_1_extra_specs(self, body, **kw):
        assert list(body) == ['extra_specs']
        return (200, {}, {'extra_specs': {'k': 'v'}})

    def delete_types_1_extra_specs_k(self, **kw):
        return(204, {}, None)

    def delete_types_1(self, **kw):
        return (202, {}, None)

    #
    # VolumeEncryptionTypes
    #
    def get_types_1_encryption(self, **kw):
        return (200, {}, {'id': 1, 'volume_type_id': 1, 'provider': 'test',
                          'cipher': 'test', 'key_size': 1,
                          'control_location': 'front-end'})

    def get_types_2_encryption(self, **kw):
        return (200, {}, {})

    def post_types_2_encryption(self, body, **kw):
        return (200, {}, {'encryption': body})

    def put_types_1_encryption_1(self, body, **kw):
        return (200, {}, {})

    def delete_types_1_encryption_provider(self, **kw):
        return (202, {}, None)

    #
    # Set/Unset metadata
    #
    def delete_volumes_1234_metadata_test_key(self, **kw):
        return (204, {}, None)

    def delete_volumes_1234_metadata_key1(self, **kw):
        return (204, {}, None)

    def delete_volumes_1234_metadata_key2(self, **kw):
        return (204, {}, None)

    def post_volumes_1234_metadata(self, **kw):
        return (204, {}, {'metadata': {'test_key': 'test_value'}})

    #
    # List all extensions
    #
    def get_extensions(self, **kw):
        exts = [
            {
                "alias": "FAKE-1",
                "description": "Fake extension number 1",
                "links": [],
                "name": "Fake1",
                "namespace": ("http://docs.openstack.org/"
                              "/ext/fake1/api/v1.1"),
                "updated": "2011-06-09T00:00:00+00:00"
            },
            {
                "alias": "FAKE-2",
                "description": "Fake extension number 2",
                "links": [],
                "name": "Fake2",
                "namespace": ("http://docs.openstack.org/"
                              "/ext/fake1/api/v1.1"),
                "updated": "2011-06-09T00:00:00+00:00"
            },
        ]
        return (200, {}, {"extensions": exts, })

    #
    # VolumeBackups
    #

    def get_backups_76a17945_3c6f_435c_975b_b5685db10b62(self, **kw):
        base_uri = 'http://localhost:8776'
        tenant_id = '0fa851f6668144cf9cd8c8419c1646c1'
        backup1 = '76a17945-3c6f-435c-975b-b5685db10b62'
        return (200, {},
                {'backup': _stub_backup_full(backup1, base_uri, tenant_id)})

    def get_backups_detail(self, **kw):
        base_uri = 'http://localhost:8776'
        tenant_id = '0fa851f6668144cf9cd8c8419c1646c1'
        backup1 = '76a17945-3c6f-435c-975b-b5685db10b62'
        backup2 = 'd09534c6-08b8-4441-9e87-8976f3a8f699'
        return (200, {},
                {'backups': [
                    _stub_backup_full(backup1, base_uri, tenant_id),
                    _stub_backup_full(backup2, base_uri, tenant_id)]})

    def delete_backups_76a17945_3c6f_435c_975b_b5685db10b62(self, **kw):
        return (202, {}, None)

    def post_backups(self, **kw):
        base_uri = 'http://localhost:8776'
        tenant_id = '0fa851f6668144cf9cd8c8419c1646c1'
        backup1 = '76a17945-3c6f-435c-975b-b5685db10b62'
        return (202, {},
                {'backup': _stub_backup(backup1, base_uri, tenant_id)})

    def post_backups_76a17945_3c6f_435c_975b_b5685db10b62_restore(self, **kw):
        return (200, {},
                {'restore': _stub_restore()})

    def post_backups_1234_restore(self, **kw):
        return (200, {},
                {'restore': _stub_restore()})

    #
    # QoSSpecs
    #

    def get_qos_specs_1B6B6A04_A927_4AEB_810B_B7BAAD49F57C(self, **kw):
        base_uri = 'http://localhost:8776'
        tenant_id = '0fa851f6668144cf9cd8c8419c1646c1'
        qos_id1 = '1B6B6A04-A927-4AEB-810B-B7BAAD49F57C'
        return (200, {},
                _stub_qos_full(qos_id1, base_uri, tenant_id))

    def get_qos_specs(self, **kw):
        base_uri = 'http://localhost:8776'
        tenant_id = '0fa851f6668144cf9cd8c8419c1646c1'
        qos_id1 = '1B6B6A04-A927-4AEB-810B-B7BAAD49F57C'
        qos_id2 = '0FD8DD14-A396-4E55-9573-1FE59042E95B'
        return (200, {},
                {'qos_specs': [
                    _stub_qos_full(qos_id1, base_uri, tenant_id, 'name-1'),
                    _stub_qos_full(qos_id2, base_uri, tenant_id)]})

    def post_qos_specs(self, **kw):
        base_uri = 'http://localhost:8776'
        tenant_id = '0fa851f6668144cf9cd8c8419c1646c1'
        qos_id = '1B6B6A04-A927-4AEB-810B-B7BAAD49F57C'
        qos_name = 'qos-name'
        return (202, {},
                _stub_qos_full(qos_id, base_uri, tenant_id, qos_name))

    def put_qos_specs_1B6B6A04_A927_4AEB_810B_B7BAAD49F57C(self, **kw):
        return (202, {}, None)

    def put_qos_specs_1B6B6A04_A927_4AEB_810B_B7BAAD49F57C_delete_keys(
            self, **kw):
        return (202, {}, None)

    def delete_qos_specs_1B6B6A04_A927_4AEB_810B_B7BAAD49F57C(self, **kw):
        return (202, {}, None)

    def get_qos_specs_1B6B6A04_A927_4AEB_810B_B7BAAD49F57C_associations(
            self, **kw):
        type_id1 = '4230B13A-7A37-4E84-B777-EFBA6FCEE4FF'
        type_id2 = '4230B13A-AB37-4E84-B777-EFBA6FCEE4FF'
        type_name1 = 'type1'
        type_name2 = 'type2'
        return (202, {},
                {'qos_associations': [
                    _stub_qos_associates(type_id1, type_name1),
                    _stub_qos_associates(type_id2, type_name2)]})

    def get_qos_specs_1B6B6A04_A927_4AEB_810B_B7BAAD49F57C_associate(
            self, **kw):
        return (202, {}, None)

    def get_qos_specs_1B6B6A04_A927_4AEB_810B_B7BAAD49F57C_disassociate(
            self, **kw):
        return (202, {}, None)

    def get_qos_specs_1B6B6A04_A927_4AEB_810B_B7BAAD49F57C_disassociate_all(
            self, **kw):
        return (202, {}, None)

    #
    # VolumeTransfers
    #

    def get_os_volume_transfer_5678(self, **kw):
        base_uri = 'http://localhost:8776'
        tenant_id = '0fa851f6668144cf9cd8c8419c1646c1'
        transfer1 = '5678'
        return (200, {},
                {'transfer':
                 _stub_transfer_full(transfer1, base_uri, tenant_id)})

    def get_os_volume_transfer_detail(self, **kw):
        base_uri = 'http://localhost:8776'
        tenant_id = '0fa851f6668144cf9cd8c8419c1646c1'
        transfer1 = '5678'
        transfer2 = 'f625ec3e-13dd-4498-a22a-50afd534cc41'
        return (200, {},
                {'transfers': [
                    _stub_transfer_full(transfer1, base_uri, tenant_id),
                    _stub_transfer_full(transfer2, base_uri, tenant_id)]})

    def delete_os_volume_transfer_5678(self, **kw):
        return (202, {}, None)

    def post_os_volume_transfer(self, **kw):
        base_uri = 'http://localhost:8776'
        tenant_id = '0fa851f6668144cf9cd8c8419c1646c1'
        transfer1 = '5678'
        return (202, {},
                {'transfer': _stub_transfer(transfer1, base_uri, tenant_id)})

    def post_os_volume_transfer_5678_accept(self, **kw):
        base_uri = 'http://localhost:8776'
        tenant_id = '0fa851f6668144cf9cd8c8419c1646c1'
        transfer1 = '5678'
        return (200, {},
                {'transfer': _stub_transfer(transfer1, base_uri, tenant_id)})

    #
    # Services
    #
    def get_os_services(self, **kw):
        host = kw.get('host', None)
        binary = kw.get('binary', None)
        services = [
            {
                'binary': 'cinder-volume',
                'host': 'host1',
                'zone': 'cinder',
                'status': 'enabled',
                'state': 'up',
                'updated_at': datetime(2012, 10, 29, 13, 42, 2)
            },
            {
                'binary': 'cinder-volume',
                'host': 'host2',
                'zone': 'cinder',
                'status': 'disabled',
                'state': 'down',
                'updated_at': datetime(2012, 9, 18, 8, 3, 38)
            },
            {
                'binary': 'cinder-scheduler',
                'host': 'host2',
                'zone': 'cinder',
                'status': 'disabled',
                'state': 'down',
                'updated_at': datetime(2012, 9, 18, 8, 3, 38)
            },
        ]
        if host:
            services = filter(lambda i: i['host'] == host, services)
        if binary:
            services = filter(lambda i: i['binary'] == binary, services)
        return (200, {}, {'services': services})

    def put_os_services_enable(self, body, **kw):
        return (200, {}, {'host': body['host'], 'binary': body['binary'],
                'status': 'enabled'})

    def put_os_services_disable(self, body, **kw):
        return (200, {}, {'host': body['host'], 'binary': body['binary'],
                'status': 'disabled'})

    def put_os_services_disable_log_reason(self, body, **kw):
        return (200, {}, {'host': body['host'], 'binary': body['binary'],
                'status': 'disabled',
                'disabled_reason': body['disabled_reason']})

    def get_os_availability_zone(self, **kw):
        return (200, {}, {
            "availabilityZoneInfo": [
                {
                    "zoneName": "zone-1",
                    "zoneState": {"available": True},
                    "hosts": None,
                },
                {
                    "zoneName": "zone-2",
                    "zoneState": {"available": False},
                    "hosts": None,
                },
                ]
        })

    def get_os_availability_zone_detail(self, **kw):
        return (200, {}, {
            "availabilityZoneInfo": [
                {
                    "zoneName": "zone-1",
                    "zoneState": {"available": True},
                    "hosts": {
                        "fake_host-1": {
                            "cinder-volume": {
                                "active": True,
                                "available": True,
                                "updated_at":
                                datetime(2012, 12, 26, 14, 45, 25, 0)
                            }
                        }
                    }
                },
                {
                    "zoneName": "internal",
                    "zoneState": {"available": True},
                    "hosts": {
                        "fake_host-1": {
                            "cinder-sched": {
                                "active": True,
                                "available": True,
                                "updated_at":
                                datetime(2012, 12, 26, 14, 45, 24, 0)
                            }
                        }
                    }
                },
                {
                    "zoneName": "zone-2",
                    "zoneState": {"available": False},
                    "hosts": None,
                },
                ]
        })

    def post_snapshots_1234_metadata(self, **kw):
        return (200, {}, {"metadata": {"key1": "val1", "key2": "val2"}})

    def delete_snapshots_1234_metadata_key1(self, **kw):
        return (200, {}, None)

    def delete_snapshots_1234_metadata_key2(self, **kw):
        return (200, {}, None)

    def put_volumes_1234_metadata(self, **kw):
        return (200, {}, {"metadata": {"key1": "val1", "key2": "val2"}})

    def put_snapshots_1234_metadata(self, **kw):
        return (200, {}, {"metadata": {"key1": "val1", "key2": "val2"}})
