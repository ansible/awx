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

from keystoneclient import exceptions
from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import role_assignments


class RoleAssignmentsTests(utils.TestCase, utils.CrudTests):

    def setUp(self):
        super(RoleAssignmentsTests, self).setUp()
        self.key = 'role_assignment'
        self.collection_key = 'role_assignments'
        self.model = role_assignments.RoleAssignment
        self.manager = self.client.role_assignments
        self.TEST_USER_DOMAIN_LIST = [{
            'role': {
                'id': self.TEST_ROLE_ID
            },
            'scope': {
                'domain': {
                    'id': self.TEST_DOMAIN_ID
                }
            },
            'user': {
                'id': self.TEST_USER_ID
            }
        }]
        self.TEST_GROUP_PROJECT_LIST = [{
            'group': {
                'id': self.TEST_GROUP_ID
            },
            'role': {
                'id': self.TEST_ROLE_ID
            },
            'scope': {
                'project': {
                    'id': self.TEST_TENANT_ID
                }
            }
        }]
        self.TEST_USER_PROJECT_LIST = [{
            'user': {
                'id': self.TEST_USER_ID
            },
            'role': {
                'id': self.TEST_ROLE_ID
            },
            'scope': {
                'project': {
                    'id': self.TEST_TENANT_ID
                }
            }
        }]

        self.TEST_ALL_RESPONSE_LIST = (self.TEST_USER_PROJECT_LIST +
                                       self.TEST_GROUP_PROJECT_LIST +
                                       self.TEST_USER_DOMAIN_LIST)

    def _assert_returned_list(self, ref_list, returned_list):
        self.assertEqual(len(ref_list), len(returned_list))
        [self.assertIsInstance(r, self.model) for r in returned_list]

    def test_list_params(self):
        ref_list = self.TEST_USER_PROJECT_LIST
        self.stub_entity('GET',
                         [self.collection_key,
                          '?scope.project.id=%s&user.id=%s' %
                          (self.TEST_TENANT_ID, self.TEST_USER_ID)],
                         entity=ref_list)

        returned_list = self.manager.list(user=self.TEST_USER_ID,
                                          project=self.TEST_TENANT_ID)
        self._assert_returned_list(ref_list, returned_list)

        kwargs = {'scope.project.id': self.TEST_TENANT_ID,
                  'user.id': self.TEST_USER_ID}
        self.assertQueryStringContains(**kwargs)

    def test_all_assignments_list(self):
        ref_list = self.TEST_ALL_RESPONSE_LIST
        self.stub_entity('GET',
                         [self.collection_key],
                         entity=ref_list)

        returned_list = self.manager.list()
        self._assert_returned_list(ref_list, returned_list)

        kwargs = {}
        self.assertQueryStringContains(**kwargs)

    def test_project_assignments_list(self):
        ref_list = self.TEST_GROUP_PROJECT_LIST + self.TEST_USER_PROJECT_LIST
        self.stub_entity('GET',
                         [self.collection_key,
                          '?scope.project.id=%s' % self.TEST_TENANT_ID],
                         entity=ref_list)

        returned_list = self.manager.list(project=self.TEST_TENANT_ID)
        self._assert_returned_list(ref_list, returned_list)

        kwargs = {'scope.project.id': self.TEST_TENANT_ID}
        self.assertQueryStringContains(**kwargs)

    def test_domain_assignments_list(self):
        ref_list = self.TEST_USER_DOMAIN_LIST
        self.stub_entity('GET',
                         [self.collection_key,
                          '?scope.domain.id=%s' % self.TEST_DOMAIN_ID],
                         entity=ref_list)

        returned_list = self.manager.list(domain=self.TEST_DOMAIN_ID)
        self._assert_returned_list(ref_list, returned_list)

        kwargs = {'scope.domain.id': self.TEST_DOMAIN_ID}
        self.assertQueryStringContains(**kwargs)

    def test_group_assignments_list(self):
        ref_list = self.TEST_GROUP_PROJECT_LIST
        self.stub_entity('GET',
                         [self.collection_key,
                          '?group.id=%s' % self.TEST_GROUP_ID],
                         entity=ref_list)

        returned_list = self.manager.list(group=self.TEST_GROUP_ID)
        self._assert_returned_list(ref_list, returned_list)

        kwargs = {'group.id': self.TEST_GROUP_ID}
        self.assertQueryStringContains(**kwargs)

    def test_user_assignments_list(self):
        ref_list = self.TEST_USER_DOMAIN_LIST + self.TEST_USER_PROJECT_LIST
        self.stub_entity('GET',
                         [self.collection_key,
                          '?user.id=%s' % self.TEST_USER_ID],
                         entity=ref_list)

        returned_list = self.manager.list(user=self.TEST_USER_ID)
        self._assert_returned_list(ref_list, returned_list)

        kwargs = {'user.id': self.TEST_USER_ID}
        self.assertQueryStringContains(**kwargs)

    def test_effective_assignments_list(self):
        ref_list = self.TEST_USER_PROJECT_LIST + self.TEST_USER_DOMAIN_LIST
        self.stub_entity('GET',
                         [self.collection_key,
                          '?effective=True'],
                         entity=ref_list)

        returned_list = self.manager.list(effective=True)
        self._assert_returned_list(ref_list, returned_list)

        kwargs = {'effective': 'True'}
        self.assertQueryStringContains(**kwargs)

    def test_role_assignments_list(self):
        ref_list = self.TEST_ALL_RESPONSE_LIST
        self.stub_entity('GET',
                         [self.collection_key,
                          '?role.id=' + self.TEST_ROLE_ID],
                         entity=ref_list)

        returned_list = self.manager.list(role=self.TEST_ROLE_ID)
        self._assert_returned_list(ref_list, returned_list)

        kwargs = {'role.id': self.TEST_ROLE_ID}
        self.assertQueryStringContains(**kwargs)

    def test_role_assignments_inherited_list(self):
        ref_list = self.TEST_ALL_RESPONSE_LIST
        self.stub_entity('GET',
                         [self.collection_key,
                          '?scope.OS-INHERIT:inherited_to=projects'],
                         entity=ref_list
                         )

        returned_list = self.manager.list(
            os_inherit_extension_inherited_to='projects')
        self._assert_returned_list(ref_list, returned_list)

        query_string = 'scope.OS-INHERIT:inherited_to=projects'
        self.assertQueryStringIs(query_string)

    def test_domain_and_project_list(self):
        # Should only accept either domain or project, never both
        self.assertRaises(exceptions.ValidationError,
                          self.manager.list,
                          domain=self.TEST_DOMAIN_ID,
                          project=self.TEST_TENANT_ID)

    def test_user_and_group_list(self):
        # Should only accept either user or group, never both
        self.assertRaises(exceptions.ValidationError, self.manager.list,
                          user=self.TEST_USER_ID, group=self.TEST_GROUP_ID)

    def test_create(self):
        # Create not supported for role assignments
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.create)

    def test_update(self):
        # Update not supported for role assignments
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.update)

    def test_delete(self):
        # Delete not supported for role assignments
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.delete)

    def test_get(self):
        # Get not supported for role assignments
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.get)

    def test_find(self):
        # Find not supported for role assignments
        self.assertRaises(exceptions.MethodNotImplemented, self.manager.find)
