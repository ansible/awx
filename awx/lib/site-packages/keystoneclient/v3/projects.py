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
from keystoneclient import exceptions
from keystoneclient.i18n import _
from keystoneclient import utils


class Project(base.Resource):
    """Represents an Identity project.

    Attributes:
        * id: a uuid that identifies the project
        * name: project name
        * description: project description
        * enabled: boolean to indicate if project is enabled
        * parent_id: a uuid representing this project's parent in hierarchy
        * parents: a list or a structured dict containing the parents of this
                   project in the hierarchy
        * subtree: a list or a structured dict containing the subtree of this
                   project in the hierarchy

    """
    @utils.positional(enforcement=utils.positional.WARN)
    def update(self, name=None, description=None, enabled=None):
        kwargs = {
            'name': name if name is not None else self.name,
            'description': (description
                            if description is not None
                            else self.description),
            'enabled': enabled if enabled is not None else self.enabled,
        }

        try:
            retval = self.manager.update(self.id, **kwargs)
            self = retval
        except Exception:
            retval = None

        return retval


class ProjectManager(base.CrudManager):
    """Manager class for manipulating Identity projects."""
    resource_class = Project
    collection_key = 'projects'
    key = 'project'

    @utils.positional(1, enforcement=utils.positional.WARN)
    def create(self, name, domain, description=None,
               enabled=True, parent=None, **kwargs):
        """Create a project.

        :param str name: project name.
        :param domain: the project domain.
        :type domain: :py:class:`keystoneclient.v3.domains.Domain` or str
        :param str description: the project description. (optional)
        :param boolean enabled: if the project is enabled. (optional)
        :param parent: the project's parent in the hierarchy. (optional)
        :type parent: :py:class:`keystoneclient.v3.projects.Project` or str
        """

        # NOTE(rodrigods): the API must be backwards compatible, so if an
        # application was passing a 'parent_id' before as kwargs, the call
        # should not fail. If both 'parent' and 'parent_id' are provided,
        # 'parent' will be preferred.
        if parent:
            kwargs['parent_id'] = base.getid(parent)

        return super(ProjectManager, self).create(
            domain_id=base.getid(domain),
            name=name,
            description=description,
            enabled=enabled,
            **kwargs)

    @utils.positional(enforcement=utils.positional.WARN)
    def list(self, domain=None, user=None, **kwargs):
        """List projects.

        If domain or user are provided, then filter projects with
        those attributes.

        If ``**kwargs`` are provided, then filter projects with
        attributes matching ``**kwargs``.
        """
        base_url = '/users/%s' % base.getid(user) if user else None
        return super(ProjectManager, self).list(
            base_url=base_url,
            domain_id=base.getid(domain),
            fallback_to_auth=True,
            **kwargs)

    def _check_not_parents_as_ids_and_parents_as_list(self, parents_as_ids,
                                                      parents_as_list):
        if parents_as_ids and parents_as_list:
            msg = _('Specify either parents_as_ids or parents_as_list '
                    'parameters, not both')
            raise exceptions.ValidationError(msg)

    def _check_not_subtree_as_ids_and_subtree_as_list(self, subtree_as_ids,
                                                      subtree_as_list):
        if subtree_as_ids and subtree_as_list:
            msg = _('Specify either subtree_as_ids or subtree_as_list '
                    'parameters, not both')
            raise exceptions.ValidationError(msg)

    @utils.positional()
    def get(self, project, subtree_as_list=False, parents_as_list=False,
            subtree_as_ids=False, parents_as_ids=False):
        """Get a project.

        :param project: project to be retrieved.
        :type project: :py:class:`keystoneclient.v3.projects.Project` or str
        :param boolean subtree_as_list: retrieve projects below this project
                                        in the hierarchy as a flat list.
                                        (optional)
        :param boolean parents_as_list: retrieve projects above this project
                                        in the hierarchy as a flat list.
                                        (optional)
        :param boolean subtree_as_ids: retrieve the IDs from the projects below
                                       this project in the hierarchy as a
                                       structured dictionary. (optional)
        :param boolean parents_as_ids: retrieve the IDs from the projects above
                                       this project in the hierarchy as a
                                       structured dictionary. (optional)

        :raises keystoneclient.exceptions.ValidationError: if subtree_as_list
            and subtree_as_ids or parents_as_list and parents_as_ids are
            included at the same time in the call.
        """
        self._check_not_parents_as_ids_and_parents_as_list(
            parents_as_ids, parents_as_list)
        self._check_not_subtree_as_ids_and_subtree_as_list(
            subtree_as_ids, subtree_as_list)

        # According to the API spec, the query params are key only
        query_params = []
        if subtree_as_list:
            query_params.append('subtree_as_list')
        if subtree_as_ids:
            query_params.append('subtree_as_ids')
        if parents_as_list:
            query_params.append('parents_as_list')
        if parents_as_ids:
            query_params.append('parents_as_ids')

        query = self.build_key_only_query(query_params)
        dict_args = {'project_id': base.getid(project)}
        url = self.build_url(dict_args_in_out=dict_args)
        return self._get(url + query, self.key)

    @utils.positional(enforcement=utils.positional.WARN)
    def update(self, project, name=None, domain=None, description=None,
               enabled=None, **kwargs):
        return super(ProjectManager, self).update(
            project_id=base.getid(project),
            domain_id=base.getid(domain),
            name=name,
            description=description,
            enabled=enabled,
            **kwargs)

    def delete(self, project):
        return super(ProjectManager, self).delete(
            project_id=base.getid(project))
