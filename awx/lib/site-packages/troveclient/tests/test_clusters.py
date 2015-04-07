# Copyright (c) 2014 eBay Software Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
import testtools

from troveclient import base
from troveclient.v1 import clusters

"""
Unit tests for clusters.py
"""


class ClusterTest(testtools.TestCase):

    def setUp(self):
        super(ClusterTest, self).setUp()

    def tearDown(self):
        super(ClusterTest, self).tearDown()

    @mock.patch.object(clusters.Cluster, '__init__', return_value=None)
    def test___repr__(self, mock_init):
        cluster = clusters.Cluster()
        cluster.name = "cluster-1"
        self.assertEqual('<Cluster: cluster-1>', cluster.__repr__())

    @mock.patch.object(clusters.Cluster, '__init__', return_value=None)
    def test_delete(self, mock_init):
        cluster = clusters.Cluster()
        cluster.manager = mock.Mock()
        db_delete_mock = mock.Mock(return_value=None)
        cluster.manager.delete = db_delete_mock
        cluster.delete()
        self.assertEqual(1, db_delete_mock.call_count)


class ClustersTest(testtools.TestCase):

    def setUp(self):
        super(ClustersTest, self).setUp()

    def tearDown(self):
        super(ClustersTest, self).tearDown()

    @mock.patch.object(clusters.Clusters, '__init__', return_value=None)
    def get_clusters(self, mock_init):
        clusters_test = clusters.Clusters()
        clusters_test.api = mock.Mock()
        clusters_test.api.client = mock.Mock()
        clusters_test.resource_class = mock.Mock(return_value="cluster-1")
        return clusters_test

    def test_create(self):
        def side_effect_func(path, body, resp_key):
            return path, body, resp_key

        clusters_test = self.get_clusters()
        clusters_test._create = mock.Mock(side_effect=side_effect_func)
        instance = [{'flavor-id': 11, 'volume': 2}]
        path, body, resp_key = clusters_test.create("test-name", "datastore",
                                                    "datastore-version",
                                                    instance)
        self.assertEqual("/clusters", path)
        self.assertEqual("cluster", resp_key)
        self.assertEqual("test-name", body["cluster"]["name"])
        self.assertEqual("datastore", body["cluster"]["datastore"]["type"])
        self.assertEqual("datastore-version",
                         body["cluster"]["datastore"]["version"])
        self.assertEqual(instance, body["cluster"]["instances"])

    def test_list(self):
        page_mock = mock.Mock()
        clusters_test = self.get_clusters()
        clusters_test._paginated = page_mock
        limit = "test-limit"
        marker = "test-marker"
        clusters_test.list(limit, marker)
        page_mock.assert_called_with("/clusters", "clusters", limit, marker)

    @mock.patch.object(base, 'getid', return_value="cluster1")
    def test_get(self, mock_id):
        def side_effect_func(path, inst):
            return path, inst
        clusters_test = self.get_clusters()
        clusters_test._get = mock.Mock(side_effect=side_effect_func)
        self.assertEqual(('/clusters/cluster1', 'cluster'),
                         clusters_test.get(1))

    def test_delete(self):
        resp = mock.Mock()
        resp.status_code = 200
        body = None
        clusters_test = self.get_clusters()
        clusters_test.api.client.delete = mock.Mock(return_value=(resp, body))
        clusters_test.delete('cluster1')
        resp.status_code = 500
        self.assertRaises(Exception, clusters_test.delete, 'cluster1')


class ClusterStatusTest(testtools.TestCase):

    def test_constants(self):
        self.assertEqual("ACTIVE", clusters.ClusterStatus.ACTIVE)
        self.assertEqual("BUILD", clusters.ClusterStatus.BUILD)
        self.assertEqual("FAILED", clusters.ClusterStatus.FAILED)
        self.assertEqual("SHUTDOWN", clusters.ClusterStatus.SHUTDOWN)
