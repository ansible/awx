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

import logging

from keystoneclient import base
from keystoneclient import exceptions
from keystoneclient.i18n import _, _LW
from keystoneclient import utils

LOG = logging.getLogger(__name__)


class User(base.Resource):
    """Represents an Identity user.

    Attributes:
        * id: a uuid that identifies the user

    """
    pass


class UserManager(base.CrudManager):
    """Manager class for manipulating Identity users."""
    resource_class = User
    collection_key = 'users'
    key = 'user'

    def _require_user_and_group(self, user, group):
        if not (user and group):
            msg = _('Specify both a user and a group')
            raise exceptions.ValidationError(msg)

    @utils.positional(1, enforcement=utils.positional.WARN)
    def create(self, name, domain=None, project=None, password=None,
               email=None, description=None, enabled=True,
               default_project=None, **kwargs):
        """Create a user.

        .. warning::

          The project argument is deprecated, use default_project instead.

        If both default_project and project is provided, the default_project
        will be used.
        """
        if project:
            LOG.warning(_LW("The project argument is deprecated, "
                            "use default_project instead."))
        default_project_id = base.getid(default_project) or base.getid(project)
        user_data = base.filter_none(name=name,
                                     domain_id=base.getid(domain),
                                     default_project_id=default_project_id,
                                     password=password,
                                     email=email,
                                     description=description,
                                     enabled=enabled,
                                     **kwargs)

        return self._create('/users', {'user': user_data}, 'user',
                            log=not bool(password))

    @utils.positional(enforcement=utils.positional.WARN)
    def list(self, project=None, domain=None, group=None, default_project=None,
             **kwargs):
        """List users.

        If project, domain or group are provided, then filter
        users with those attributes.

        If ``**kwargs`` are provided, then filter users with
        attributes matching ``**kwargs``.

        .. warning::

          The project argument is deprecated, use default_project instead.

        If both default_project and project is provided, the default_project
        will be used.
        """
        if project:
            LOG.warning(_LW("The project argument is deprecated, "
                            "use default_project instead."))
        default_project_id = base.getid(default_project) or base.getid(project)
        if group:
            base_url = '/groups/%s' % base.getid(group)
        else:
            base_url = None

        return super(UserManager, self).list(
            base_url=base_url,
            domain_id=base.getid(domain),
            default_project_id=default_project_id,
            **kwargs)

    def get(self, user):
        return super(UserManager, self).get(
            user_id=base.getid(user))

    @utils.positional(enforcement=utils.positional.WARN)
    def update(self, user, name=None, domain=None, project=None, password=None,
               email=None, description=None, enabled=None,
               default_project=None, **kwargs):
        """Update a user.

        .. warning::

          The project argument is deprecated, use default_project instead.

        If both default_project and project is provided, the default_project
        will be used.
        """
        if project:
            LOG.warning(_LW("The project argument is deprecated, "
                            "use default_project instead."))
        default_project_id = base.getid(default_project) or base.getid(project)
        user_data = base.filter_none(name=name,
                                     domain_id=base.getid(domain),
                                     default_project_id=default_project_id,
                                     password=password,
                                     email=email,
                                     description=description,
                                     enabled=enabled,
                                     **kwargs)

        return self._update('/users/%s' % base.getid(user),
                            {'user': user_data},
                            'user',
                            method='PATCH',
                            log=False)

    def update_password(self, old_password, new_password):
        """Update the password for the user the token belongs to."""
        if not (old_password and new_password):
            msg = _('Specify both the current password and a new password')
            raise exceptions.ValidationError(msg)

        if old_password == new_password:
            msg = _('Old password and new password must be different.')
            raise exceptions.ValidationError(msg)

        params = {'user': {'password': new_password,
                           'original_password': old_password}}

        base_url = '/users/%s/password' % self.api.user_id

        return self._update(base_url, params, method='POST', log=False,
                            endpoint_filter={'interface': 'public'})

    def add_to_group(self, user, group):
        self._require_user_and_group(user, group)

        base_url = '/groups/%s' % base.getid(group)
        return super(UserManager, self).put(
            base_url=base_url,
            user_id=base.getid(user))

    def check_in_group(self, user, group):
        self._require_user_and_group(user, group)

        base_url = '/groups/%s' % base.getid(group)
        return super(UserManager, self).head(
            base_url=base_url,
            user_id=base.getid(user))

    def remove_from_group(self, user, group):
        self._require_user_and_group(user, group)

        base_url = '/groups/%s' % base.getid(group)
        return super(UserManager, self).delete(
            base_url=base_url,
            user_id=base.getid(user))

    def delete(self, user):
        return super(UserManager, self).delete(
            user_id=base.getid(user))
