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

# Helper class for loading large fixture data
from __future__ import with_statement

import os

from libcloud.utils.py3 import PY3
from libcloud.utils.py3 import u

FIXTURES_ROOT = {
    'compute': 'compute/fixtures',
    'storage': 'storage/fixtures',
    'loadbalancer': 'loadbalancer/fixtures',
    'dns': 'dns/fixtures',
    'openstack': 'compute/fixtures/openstack',
}


class FileFixtures(object):
    def __init__(self, fixtures_type, sub_dir=''):
        script_dir = os.path.abspath(os.path.split(__file__)[0])
        self.root = os.path.join(script_dir, FIXTURES_ROOT[fixtures_type],
                                 sub_dir)

    def load(self, file):
        path = os.path.join(self.root, file)
        if os.path.exists(path):
            if PY3:
                kwargs = {'encoding': 'utf-8'}
            else:
                kwargs = {}

            with open(path, 'r', **kwargs) as fh:
                content = fh.read()
            return u(content)
        else:
            raise IOError(path)


class ComputeFileFixtures(FileFixtures):
    def __init__(self, sub_dir=''):
        super(ComputeFileFixtures, self).__init__(fixtures_type='compute',
                                                  sub_dir=sub_dir)


class StorageFileFixtures(FileFixtures):
    def __init__(self, sub_dir=''):
        super(StorageFileFixtures, self).__init__(fixtures_type='storage',
                                                  sub_dir=sub_dir)


class LoadBalancerFileFixtures(FileFixtures):
    def __init__(self, sub_dir=''):
        super(LoadBalancerFileFixtures, self).__init__(fixtures_type='loadbalancer',
                                                       sub_dir=sub_dir)


class DNSFileFixtures(FileFixtures):
    def __init__(self, sub_dir=''):
        super(DNSFileFixtures, self).__init__(fixtures_type='dns',
                                              sub_dir=sub_dir)


class OpenStackFixtures(FileFixtures):
    def __init__(self, sub_dir=''):
        super(OpenStackFixtures, self).__init__(fixtures_type='openstack',
                                                sub_dir=sub_dir)
