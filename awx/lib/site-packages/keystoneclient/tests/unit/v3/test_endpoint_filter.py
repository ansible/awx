# Copyright 2014 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

from keystoneclient.tests.unit.v3 import utils


class EndpointTestUtils(object):
    """Mixin class with shared methods between Endpoint Filter & Policy."""

    def new_ref(self, **kwargs):
        # copied from CrudTests as we need to create endpoint and project
        # refs for our tests. EndpointFilter is not exactly CRUD API.
        kwargs.setdefault('id', uuid.uuid4().hex)
        kwargs.setdefault('enabled', True)
        return kwargs

    def new_endpoint_ref(self, **kwargs):
        # copied from EndpointTests as we need endpoint refs for our tests
        kwargs = self.new_ref(**kwargs)
        kwargs.setdefault('interface', 'public')
        kwargs.setdefault('region', uuid.uuid4().hex)
        kwargs.setdefault('service_id', uuid.uuid4().hex)
        kwargs.setdefault('url', uuid.uuid4().hex)
        return kwargs


class EndpointFilterTests(utils.TestCase, EndpointTestUtils):
    """Test project-endpoint associations (a.k.a. EndpointFilter Extension).

    Endpoint filter provides associations between service endpoints and
    projects. These assciations are then used to create ad-hoc catalogs for
    each project-scoped token request.

    """

    def setUp(self):
        super(EndpointFilterTests, self).setUp()
        self.manager = self.client.endpoint_filter

    def new_project_ref(self, **kwargs):
        # copied from ProjectTests as we need project refs for our tests
        kwargs = self.new_ref(**kwargs)
        kwargs.setdefault('domain_id', uuid.uuid4().hex)
        kwargs.setdefault('name', uuid.uuid4().hex)
        return kwargs

    def test_add_endpoint_to_project_via_id(self):
        endpoint_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex

        self.stub_url('PUT',
                      [self.manager.OS_EP_FILTER_EXT, 'projects', project_id,
                       'endpoints', endpoint_id],
                      status_code=201)

        self.manager.add_endpoint_to_project(project=project_id,
                                             endpoint=endpoint_id)

    def test_add_endpoint_to_project_via_obj(self):
        project_ref = self.new_project_ref()
        endpoint_ref = self.new_endpoint_ref()
        project = self.client.projects.resource_class(self.client.projects,
                                                      project_ref,
                                                      loaded=True)
        endpoint = self.client.endpoints.resource_class(self.client.endpoints,
                                                        endpoint_ref,
                                                        loaded=True)

        self.stub_url('PUT',
                      [self.manager.OS_EP_FILTER_EXT,
                       'projects', project_ref['id'],
                       'endpoints', endpoint_ref['id']],
                      status_code=201)

        self.manager.add_endpoint_to_project(project=project,
                                             endpoint=endpoint)

    def test_delete_endpoint_from_project(self):
        endpoint_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex

        self.stub_url('DELETE',
                      [self.manager.OS_EP_FILTER_EXT, 'projects', project_id,
                       'endpoints', endpoint_id],
                      status_code=201)

        self.manager.delete_endpoint_from_project(project=project_id,
                                                  endpoint=endpoint_id)

    def test_check_endpoint_in_project(self):
        endpoint_id = uuid.uuid4().hex
        project_id = uuid.uuid4().hex

        self.stub_url('HEAD',
                      [self.manager.OS_EP_FILTER_EXT, 'projects', project_id,
                       'endpoints', endpoint_id],
                      status_code=201)

        self.manager.check_endpoint_in_project(project=project_id,
                                               endpoint=endpoint_id)

    def test_list_endpoints_for_project(self):
        project_id = uuid.uuid4().hex
        endpoints = {'endpoints': [self.new_endpoint_ref(),
                                   self.new_endpoint_ref()]}
        self.stub_url('GET',
                      [self.manager.OS_EP_FILTER_EXT, 'projects', project_id,
                       'endpoints'],
                      json=endpoints,
                      status_code=200)

        endpoints_resp = self.manager.list_endpoints_for_project(
            project=project_id)

        expected_endpoint_ids = [
            endpoint['id'] for endpoint in endpoints['endpoints']]
        actual_endpoint_ids = [endpoint.id for endpoint in endpoints_resp]
        self.assertEqual(expected_endpoint_ids, actual_endpoint_ids)

    def test_list_projects_for_endpoint(self):
        endpoint_id = uuid.uuid4().hex
        projects = {'projects': [self.new_project_ref(),
                                 self.new_project_ref()]}
        self.stub_url('GET',
                      [self.manager.OS_EP_FILTER_EXT, 'endpoints', endpoint_id,
                       'projects'],
                      json=projects,
                      status_code=200)

        projects_resp = self.manager.list_projects_for_endpoint(
            endpoint=endpoint_id)

        expected_project_ids = [
            project['id'] for project in projects['projects']]
        actual_project_ids = [project.id for project in projects_resp]
        self.assertEqual(expected_project_ids, actual_project_ids)
