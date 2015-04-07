# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
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

from troveclient import base


class Diagnostics(base.Resource):
    """Account is an opaque instance used to hold account information."""
    def __repr__(self):
        return "<Diagnostics: %s>" % self.version


class DiagnosticsInterrogator(base.ManagerWithFind):
    """Manager class for Interrogator resource."""
    resource_class = Diagnostics

    def get(self, instance):
        """Get the diagnostics of the guest on the instance."""
        return self._get("/mgmt/instances/%s/diagnostics" %
                         base.getid(instance), "diagnostics")

    # Appease the abc gods
    def list(self):
        pass


class HwInfo(base.Resource):

    def __repr__(self):
        return "<HwInfo: %s>" % self.version


class HwInfoInterrogator(base.ManagerWithFind):
    """Manager class for HwInfo."""
    resource_class = HwInfo

    def get(self, instance):
        """Get the hardware information of the instance."""
        return self._get("/mgmt/instances/%s/hwinfo" % base.getid(instance))

    # Appease the abc gods
    def list(self):
        pass
