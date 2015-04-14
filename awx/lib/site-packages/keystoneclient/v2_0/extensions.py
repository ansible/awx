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

from keystoneclient import base


class Extension(base.Resource):
    """Represents an Identity API extension."""
    def __repr__(self):
        return "<Extension %s>" % self._info


class ExtensionManager(base.ManagerWithFind):
    """Manager class for listing Identity API extensions."""

    resource_class = Extension

    def list(self):
        """List all available extensions."""
        return self._list('/extensions', 'extensions')
