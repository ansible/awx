# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import uuid
import base64
import unittest
import datetime

from libcloud.compute.base import Node, NodeImage, NodeLocation
from libcloud.compute.types import NodeState
from libcloud.compute.drivers.cloudframes import CloudFramesNodeDriver
from libcloud.compute.drivers.cloudframes import CloudFramesSnapshot

from libcloud.utils.py3 import httplib, xmlrpclib, b
from libcloud.test import MockHttpTestCase
from libcloud.test.compute import TestCaseMixin
from libcloud.test.secrets import CLOUDFRAMES_PARAMS
from libcloud.test.file_fixtures import ComputeFileFixtures


# how many seconds to give the vm to boot and have VMWare tools start up
START_TIMEOUT = 300


class CloudFramesMockHttp(MockHttpTestCase):
    fixtures = ComputeFileFixtures('cloudframes')

    content_headers = {
        'Server': 'TwistedWeb/9.0.0',
        'Date': datetime.datetime.now().ctime(),
        'Content-Type': 'text/xml',
    }

    def __getattr__(self, key):
        if key == '_appserver_xmlrpc_http:__host:8888_appserver_xmlrpc':
            return self._xmlrpc
        raise AttributeError(key)

    def _xmlrpc(self, method, url, body, headers):
        params, methodname = xmlrpclib.loads(body)
        meth_name = methodname.replace('.', '_').replace('cloud_api_', '')
        return getattr(self, meth_name)(method, url, params, headers)

    def _authenticate(self, headers):
        self.assertTrue('Authorization' in headers.keys())
        self.assertTrue(headers['Authorization'].startswith('Basic '))
        auth = base64.b64decode(
            b(headers['Authorization'].split(' ', 1)[1])).decode('ascii')
        username, password = auth.split(':', 1)
        self.assertEqual(username, CLOUDFRAMES_PARAMS[0])
        self.assertEqual(password, CLOUDFRAMES_PARAMS[1])

    def cloudspace_find(self, method, url, params, headers):
        self._authenticate(headers)
        body = self.fixtures.load('_cloudspace_find.xml')
        return (httplib.OK, body, self.content_headers,
                httplib.responses[httplib.OK])

    def machine_find(self, method, url, params, headers):
        self._authenticate(headers)
        if params[18]:
            body = self.fixtures.load('_machine_find_templates.xml')
        elif params[17] == 'PHYSICAL':
            body = self.fixtures.load('_machine_find_physical.xml')
        elif params[17] == 'VIRTUALSERVER':
            body = self.fixtures.load('_machine_find_virtualserver.xml')
        elif params[17] == 'VIRTUALDESKTOP':
            body = self.fixtures.load('_machine_find_virtualdesktop.xml')
        else:
            raise Exception(
                'unknown machine.find query with params: %s' % params)
        return (httplib.OK, body, self.content_headers,
                httplib.responses[httplib.OK])

    def machine_list(self, method, url, params, headers):
        self._authenticate(headers)
        body = None
        if params[3]:
            body = self.fixtures.load(
                '_machine_list_machineguid_%s.xml' % params[3])
        if body:
            return (httplib.OK, body, self.content_headers,
                    httplib.responses[httplib.OK])
        else:
            return (httplib.INTERNAL_SERVER_ERROR, '',
                    self.content_headers, 'Could not parse request')

    def machine_delete(self, method, url, params, headers):
        self._authenticate(headers)
        body = self.fixtures.load('_machine_delete.xml')
        return (httplib.OK, body, self.content_headers,
                httplib.responses[httplib.OK])

    def machine_stop(self, method, url, params, headers):
        self._authenticate(headers)
        body = self.fixtures.load('_machine_stop.xml')
        return (httplib.OK, body, self.content_headers,
                httplib.responses[httplib.OK])

    def machine_reboot(self, method, url, params, headers):
        self._authenticate(headers)
        body = self.fixtures.load('_machine_reboot.xml')
        return (httplib.OK, body, self.content_headers,
                httplib.responses[httplib.OK])

    def machine_createFromTemplate(self, method, url, params, headers):
        self._authenticate(headers)
        body = self.fixtures.load('_machine_createFromTemplate.xml')
        return (httplib.OK, body, self.content_headers,
                httplib.responses[httplib.OK])

    def machine_start(self, method, url, params, headers):
        self._authenticate(headers)
        body = self.fixtures.load('_machine_start.xml')
        return (httplib.OK, body, self.content_headers,
                httplib.responses[httplib.OK])

    def machine_snapshot(self, method, url, params, headers):
        self._authenticate(headers)
        body = self.fixtures.load('_machine_snapshot.xml')
        return (httplib.OK, body, self.content_headers,
                httplib.responses[httplib.OK])

    def machine_listSnapshots(self, method, url, params, headers):
        self._authenticate(headers)
        body = self.fixtures.load('_machine_listSnapshots.xml')
        return (httplib.OK, body, self.content_headers,
                httplib.responses[httplib.OK])

    def machine_rollback(self, method, url, params, headers):
        self._authenticate(headers)
        body = self.fixtures.load('_machine_rollback.xml')
        return (httplib.OK, body, self.content_headers,
                httplib.responses[httplib.OK])

    def lan_find(self, method, url, params, headers):
        self._authenticate(headers)
        body = self.fixtures.load('_lan_find.xml')
        return (httplib.OK, body, self.content_headers,
                httplib.responses[httplib.OK])


class CloudFramesTests(unittest.TestCase, TestCaseMixin):

    should_list_locations = True
    should_have_pricing = False
    should_list_volumes = False

    def __init__(self, name, url=None):
        self.url = url
        super(CloudFramesTests, self).__init__(name)

    def setUp(self):
        if self.url:
            args = ()
            kwargs = {'url': self.url}
        else:
            CloudFramesNodeDriver.connectionCls.conn_classes = (
                CloudFramesMockHttp, CloudFramesMockHttp)
            args = CLOUDFRAMES_PARAMS
            kwargs = {}
        self.driver = CloudFramesNodeDriver(*args, **kwargs)

    def _retry_until_up(self, cmd, *args, **kwargs):
        """
        When testing against a live system, this will cause the given command
        to be retried until it succeeds.
        (Calls like snapshot/reboot will fail until the vm has started fully.)
        """
        now = datetime.datetime.now()
        while not (datetime.datetime.now() - now).seconds > START_TIMEOUT:
            try:
                return cmd(*args, **kwargs)
            except:
                pass
        else:
            raise Exception('VMWare tools did not become available in time')

    def test_connection(self):
        key, secret, secure, host, port = CLOUDFRAMES_PARAMS
        CloudFramesNodeDriver(key, secret, secure, host)
        CloudFramesNodeDriver(key, secret, secure, host, 80)
        self.assertRaises(NotImplementedError, CloudFramesNodeDriver,
                          key, secret, True, host, 80)
        CloudFramesNodeDriver(key, secret, secure, host, '80')
        self.assertRaises(NotImplementedError, CloudFramesNodeDriver,
                          key, secure=secure, host=host)
        self.assertRaises(NotImplementedError, CloudFramesNodeDriver,
                          secret=secret, secure=secure, host=host)
        CloudFramesNodeDriver(
            url='http://%s:%s@%s:80/appserver/xmlrpc' % (key, secret, host))
        CloudFramesNodeDriver(
            url='http://%s:%s@%s/appserver/xmlrpc' % (key, secret, host))
        self.assertRaises(NotImplementedError, CloudFramesNodeDriver,
                          key=key, secret=secret,
                          url='https://%s/appserver/xmlrpc' % host)
        self.assertRaises(NotImplementedError, CloudFramesNodeDriver,
                          key=key, secret=secret, secure=False,
                          url='https://%s/appserver/xmlrpc' % host)
        self.assertRaises(NotImplementedError, CloudFramesNodeDriver,
                          url='http://%s@%s/appserver/xmlrpc' % (key, host))
        CloudFramesNodeDriver(
            secret=secret, url='http://%s@%s/appserver/xmlrpc' % (key, host))
        self.assertRaises(NotImplementedError, CloudFramesNodeDriver,
                          url='http://%s/appserver/xmlrpc' % host)
        self.assertRaises(
            NotImplementedError, CloudFramesNodeDriver,
            secret=secret, url='http://%s/appserver/xmlrpc' % host)
        self.assertRaises(NotImplementedError, CloudFramesNodeDriver,
                          key=key, url='http://%s/appserver/xmlrpc' % host)
        CloudFramesNodeDriver(
            key=key, secret=secret, url='http://%s/appserver/xmlrpc' % host)

    def test_snapshot(self):
        nodes = [node for node in self.driver.list_nodes()
                 if node.state == NodeState.RUNNING]
        if not nodes:
            raise Exception('No running vm to test snapshotting')
        self._test_snapshot(nodes[0])

    def _test_snapshot(self, node):
        if self.url:
            self.assertEqual(len(self.driver.ex_list_snapshots(node)), 0)
        snapshot1 = self._retry_until_up(
            self.driver.ex_snapshot_node, node)
        self.assertTrue(isinstance(snapshot1, CloudFramesSnapshot))
        if self.url:
            self.assertEqual(len(self.driver.ex_list_snapshots(node)), 1)
        snapshot2 = self.driver.ex_snapshot_node(node)
        self.assertTrue(isinstance(snapshot2, CloudFramesSnapshot))
        if self.url:
            self.assertEqual(len(self.driver.ex_list_snapshots(node)), 2)
        self.driver.ex_destroy_snapshot(node, snapshot2)
        if self.url:
            self.assertEqual(len(self.driver.ex_list_snapshots(node)), 1)
        self.driver.ex_rollback_node(node, snapshot1)
        if self.url:
            self.assertEqual(len(self.driver.ex_list_snapshots(node)), 1)
        self.driver.ex_destroy_snapshot(node, snapshot1)

    def test_comprehensive(self):
        """
        Creates a node with the first location, image and size it finds.

        Then boots the node, reboots, creates two snapshots.
        Deletes one snapshot, rolls back to the other, then destroys the node.

        In between these operations it verifies the node status and lists.
        """
        if not self.url:
            return
        location = self.driver.list_locations()[0]
        self.assertTrue(isinstance(location, NodeLocation))
        image = self.driver.list_images()[0]
        self.assertTrue(isinstance(image, NodeImage))
        size = self.driver.list_sizes()[0]
        name = 'AUTOTEST_%s' % uuid.uuid4()
        node = self.driver.create_node(
            image=image, name=name, size=size, location=location)
        # give the node time to boot up and load the vmware tools
        self.assertTrue(isinstance(node, Node))
        self.assertTrue(node.id in [x.id for x in self.driver.list_nodes()])
        self.assertTrue(node.state == NodeState.RUNNING)
        self._test_snapshot(node)
        self._retry_until_up(self.driver.reboot_node, node)
        self.driver.destroy_node(node)
        self.assertFalse(node.id in [x.id for x in self.driver.list_nodes()])


if __name__ == '__main__':
    # add a full url as first arg to this script to test against a live system
    # fi: http://key:secret@host:port/appserver/xmlrpc
    if len(sys.argv) > 1:
        suite = unittest.TestSuite()
        suite.addTest(CloudFramesTests('test_comprehensive', sys.argv[1]))
        if not unittest.TextTestRunner().run(suite).wasSuccessful():
            sys.exit(1)
        del sys.argv[1]
    sys.exit(unittest.main())
