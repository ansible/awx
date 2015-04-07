# Copyright 2014 OpenStack Foundation
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
from keystoneclient.v3 import endpoints
from keystoneclient.v3 import projects


class EndpointFilterManager(base.Manager):
    """Manager class for manipulating project-endpoint associations."""
    OS_EP_FILTER_EXT = '/OS-EP-FILTER'

    def _build_base_url(self, project=None, endpoint=None):
        project_id = base.getid(project)
        endpoint_id = base.getid(endpoint)

        if project_id and endpoint_id:
            api_path = '/projects/%s/endpoints/%s' % (project_id, endpoint_id)
        elif project_id:
            api_path = '/projects/%s/endpoints' % (project_id)
        elif endpoint_id:
            api_path = '/endpoints/%s/projects' % (endpoint_id)
        else:
            msg = _('Must specify a project, an endpoint, or both')
            raise exceptions.ValidationError(msg)

        return self.OS_EP_FILTER_EXT + api_path

    def add_endpoint_to_project(self, project, endpoint):
        """Create a project-endpoint association."""
        if not (project and endpoint):
            raise ValueError(_('project and endpoint are required'))

        base_url = self._build_base_url(project=project,
                                        endpoint=endpoint)
        return super(EndpointFilterManager, self)._put(url=base_url)

    def delete_endpoint_from_project(self, project, endpoint):
        """Remove a project-endpoint association."""
        if not (project and endpoint):
            raise ValueError(_('project and endpoint are required'))

        base_url = self._build_base_url(project=project,
                                        endpoint=endpoint)
        return super(EndpointFilterManager, self)._delete(url=base_url)

    def check_endpoint_in_project(self, project, endpoint):
        """Checks if project-endpoint association exist."""
        if not (project and endpoint):
            raise ValueError(_('project and endpoint are required'))

        base_url = self._build_base_url(project=project,
                                        endpoint=endpoint)
        return super(EndpointFilterManager, self)._head(url=base_url)

    def list_endpoints_for_project(self, project):
        """List all endpoints for a given project."""
        if not project:
            raise ValueError(_('project is required'))

        base_url = self._build_base_url(project=project)
        return super(EndpointFilterManager, self)._list(
            base_url,
            endpoints.EndpointManager.collection_key,
            obj_class=endpoints.EndpointManager.resource_class)

    def list_projects_for_endpoint(self, endpoint):
        """List all projects for a given endpoint."""
        if not endpoint:
            raise ValueError(_('endpoint is required'))

        base_url = self._build_base_url(endpoint=endpoint)
        return super(EndpointFilterManager, self)._list(
            base_url,
            projects.ProjectManager.collection_key,
            obj_class=projects.ProjectManager.resource_class)
