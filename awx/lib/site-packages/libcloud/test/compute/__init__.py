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

from libcloud.compute.base import Node, NodeImage, NodeLocation, StorageVolume
from libcloud.pricing import get_pricing


class TestCaseMixin(object):
    should_list_locations = True
    should_have_pricing = False
    should_list_volumes = False

    def test_list_nodes_response(self):
        nodes = self.driver.list_nodes()
        self.assertTrue(isinstance(nodes, list))
        for node in nodes:
            self.assertTrue(isinstance(node, Node))

    def test_list_sizes_response(self):
        sizes = self.driver.list_sizes()
        size = sizes[0]
        self.assertTrue(isinstance(sizes, list))
        # Check that size values are ints or None
        self.assertTrue(size.ram is None or isinstance(size.ram, int))
        self.assertTrue(size.disk is None or isinstance(size.disk, int))
        self.assertTrue(size.bandwidth is None or
                        isinstance(size.bandwidth, int))
        # Check that price values are ints, floats, or None.
        self.assertTrue(size.price is None or isinstance(size.price, float)
                        or isinstance(size.price, int))

    def test_list_images_response(self):
        images = self.driver.list_images()
        self.assertTrue(isinstance(images, list))
        for image in images:
            self.assertTrue(isinstance(image, NodeImage))

    def test_list_volumes_response(self):
        if not self.should_list_volumes:
            return None

        volumes = self.driver.list_volumes()
        self.assertTrue(isinstance(volumes, list))
        for volume in volumes:
            self.assertTrue(isinstance(volume, StorageVolume))

    def test_list_locations_response(self):
        if not self.should_list_locations:
            return None

        locations = self.driver.list_locations()
        self.assertTrue(isinstance(locations, list))
        for dc in locations:
            self.assertTrue(isinstance(dc, NodeLocation))

    def test_create_node_response(self):
        # should return a node object
        size = self.driver.list_sizes()[0]
        image = self.driver.list_images()[0]
        node = self.driver.create_node(name='node-name',
                                       image=image,
                                       size=size)
        self.assertTrue(isinstance(node, Node))

    def test_destroy_node_response(self):
        # should return a node object
        node = self.driver.list_nodes()[0]
        ret = self.driver.destroy_node(node)
        self.assertTrue(isinstance(ret, bool))

    def test_reboot_node_response(self):
        # should return a node object
        node = self.driver.list_nodes()[0]
        ret = self.driver.reboot_node(node)
        self.assertTrue(isinstance(ret, bool))

    def test_get_pricing_success(self):
        if not self.should_have_pricing:
            return None

        driver_type = 'compute'
        try:
            get_pricing(driver_type=driver_type,
                        driver_name=self.driver.api_name)
        except KeyError:
            self.fail("No {driver_type!r} pricing info for {driver}.".format(
                driver=self.driver.__class__.__name__,
                driver_type=driver_type,
            ))

if __name__ == "__main__":
    import doctest
    doctest.testmod()
