# Copyright 2014 NEC Corporation.  All rights reserved.
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

"""
version interface
"""

from novaclient import base


class Version(base.Resource):
    """
    Compute REST API information
    """
    def __repr__(self):
        return "<Version>"


class VersionManager(base.ManagerWithFind):
    resource_class = Version

    def list(self):
        """List all versions."""
        return self._list(None, "versions")
