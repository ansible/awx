# Copyright 2012 IBM Corp.
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

"""
agent interface
"""

from novaclient import base


class Agent(base.Resource):
    def __repr__(self):
        return "<Agent: %s>" % self.agent

    def _add_details(self, info):
        dico = 'resource' in info and info['resource'] or info
        for (k, v) in dico.items():
            setattr(self, k, v)


class AgentsManager(base.ManagerWithFind):
    resource_class = Agent

    def list(self, hypervisor=None):
        """List all agent builds."""
        url = "/os-agents"
        if hypervisor:
            url = "/os-agents?hypervisor=%s" % hypervisor
        return self._list(url, "agents")

    def _build_update_body(self, version, url, md5hash):
        return {'para': {'version': version,
                         'url': url,
                         'md5hash': md5hash}}

    def update(self, id, version,
               url, md5hash):
        """Update an existing agent build."""
        body = self._build_update_body(version, url, md5hash)
        return self._update('/os-agents/%s' % id, body, 'agent')

    def create(self, os, architecture, version,
               url, md5hash, hypervisor):
        """Create a new agent build."""
        body = {'agent': {'hypervisor': hypervisor,
                          'os': os,
                          'architecture': architecture,
                          'version': version,
                          'url': url,
                          'md5hash': md5hash}}
        return self._create('/os-agents', body, 'agent')

    def delete(self, id):
        """Deletes an existing agent build."""
        self._delete('/os-agents/%s' % id)
