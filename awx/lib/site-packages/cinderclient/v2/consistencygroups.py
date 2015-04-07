# Copyright (C) 2012 - 2014 EMC Corporation.
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

"""Consistencygroup interface (v2 extension)."""

import six
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from cinderclient import base


class Consistencygroup(base.Resource):
    """A Consistencygroup of volumes."""
    def __repr__(self):
        return "<Consistencygroup: %s>" % self.id

    def delete(self, force='False'):
        """Delete this consistencygroup."""
        self.manager.delete(self, force)

    def update(self, **kwargs):
        """Update the name or description for this consistencygroup."""
        self.manager.update(self, **kwargs)


class ConsistencygroupManager(base.ManagerWithFind):
    """Manage :class:`Consistencygroup` resources."""
    resource_class = Consistencygroup

    def create(self, volume_types, name=None,
               description=None, user_id=None,
               project_id=None, availability_zone=None):
        """Creates a consistencygroup.

        :param name: Name of the ConsistencyGroup
        :param description: Description of the ConsistencyGroup
        :param volume_types: Types of volume
        :param user_id: User id derived from context
        :param project_id: Project id derived from context
        :param availability_zone: Availability Zone to use
        :rtype: :class:`Consistencygroup`
       """

        body = {'consistencygroup': {'name': name,
                                     'description': description,
                                     'volume_types': volume_types,
                                     'user_id': user_id,
                                     'project_id': project_id,
                                     'availability_zone': availability_zone,
                                     'status': "creating",
                                     }}

        return self._create('/consistencygroups', body, 'consistencygroup')

    def get(self, group_id):
        """Get a consistencygroup.

        :param group_id: The ID of the consistencygroup to get.
        :rtype: :class:`Consistencygroup`
        """
        return self._get("/consistencygroups/%s" % group_id,
                         "consistencygroup")

    def list(self, detailed=True, search_opts=None):
        """Lists all consistencygroups.

        :rtype: list of :class:`Consistencygroup`
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in six.iteritems(search_opts):
            if val:
                qparams[opt] = val

        query_string = "?%s" % urlencode(qparams) if qparams else ""

        detail = ""
        if detailed:
            detail = "/detail"

        return self._list("/consistencygroups%s%s" % (detail, query_string),
                          "consistencygroups")

    def delete(self, consistencygroup, force=False):
        """Delete a consistencygroup.

        :param Consistencygroup: The :class:`Consistencygroup` to delete.
        """
        body = {'consistencygroup': {'force': force}}
        self.run_hooks('modify_body_for_action', body, 'consistencygroup')
        url = '/consistencygroups/%s/delete' % base.getid(consistencygroup)
        return self.api.client.post(url, body=body)

    def update(self, consistencygroup, **kwargs):
        """Update the name or description for a consistencygroup.

        :param Consistencygroup: The :class:`Consistencygroup` to update.
        """
        if not kwargs:
            return

        body = {"consistencygroup": kwargs}

        self._update("/consistencygroups/%s" % base.getid(consistencygroup),
                     body)

    def _action(self, action, consistencygroup, info=None, **kwargs):
        """Perform a consistencygroup "action."
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/consistencygroups/%s/action' % base.getid(consistencygroup)
        return self.api.client.post(url, body=body)
