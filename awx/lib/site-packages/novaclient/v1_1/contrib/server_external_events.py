# Copyright (C) 2014, Red Hat, Inc.
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
External event triggering for servers, not to be used by users.
"""

from novaclient import base


class Event(base.Resource):
    def __repr__(self):
        return "<Event: %s>" % self.name


class ServerExternalEventManager(base.Manager):
    resource_class = Event

    def create(self, events):
        """Create one or more server events.

        :param:events: A list of dictionaries containing 'server_uuid', 'name',
                       'status', and 'tag' (which may be absent)
        """

        body = {'events': events}
        return self._create('/os-server-external-events', body, 'events',
                            return_raw=True)


manager_class = ServerExternalEventManager
name = 'server_external_events'
