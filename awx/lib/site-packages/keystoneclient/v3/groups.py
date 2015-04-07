# Copyright 2011 OpenStack Foundation
# Copyright 2011 Nebula, Inc.
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

from keystoneclient import base
from keystoneclient import utils


class Group(base.Resource):
    """Represents an Identity user group.

    Attributes:
        * id: a uuid that identifies the group
        * name: group name
        * description: group description

    """
    @utils.positional(enforcement=utils.positional.WARN)
    def update(self, name=None, description=None):
        kwargs = {
            'name': name if name is not None else self.name,
            'description': (description
                            if description is not None
                            else self.description),
        }

        try:
            retval = self.manager.update(self.id, **kwargs)
            self = retval
        except Exception:
            retval = None

        return retval


class GroupManager(base.CrudManager):
    """Manager class for manipulating Identity groups."""
    resource_class = Group
    collection_key = 'groups'
    key = 'group'

    @utils.positional(1, enforcement=utils.positional.WARN)
    def create(self, name, domain=None, description=None, **kwargs):
        return super(GroupManager, self).create(
            name=name,
            domain_id=base.getid(domain),
            description=description,
            **kwargs)

    @utils.positional(enforcement=utils.positional.WARN)
    def list(self, user=None, domain=None, **kwargs):
        """List groups.

        If domain or user is provided, then filter groups with
        that attribute.

        If ``**kwargs`` are provided, then filter groups with
        attributes matching ``**kwargs``.
        """
        if user:
            base_url = '/users/%s' % base.getid(user)
        else:
            base_url = None
        return super(GroupManager, self).list(
            base_url=base_url,
            domain_id=base.getid(domain),
            **kwargs)

    def get(self, group):
        return super(GroupManager, self).get(
            group_id=base.getid(group))

    @utils.positional(enforcement=utils.positional.WARN)
    def update(self, group, name=None, description=None, **kwargs):
        return super(GroupManager, self).update(
            group_id=base.getid(group),
            name=name,
            description=description,
            **kwargs)

    def delete(self, group):
        return super(GroupManager, self).delete(
            group_id=base.getid(group))
