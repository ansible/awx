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

from keystoneclient import exceptions
from keystoneclient.tests.unit.v3 import utils
from keystoneclient.v3 import projects


class ProjectTests(utils.TestCase, utils.CrudTests):
    def setUp(self):
        super(ProjectTests, self).setUp()
        self.key = 'project'
        self.collection_key = 'projects'
        self.model = projects.Project
        self.manager = self.client.projects

    def new_ref(self, **kwargs):
        kwargs = super(ProjectTests, self).new_ref(**kwargs)
        return self._new_project_ref(ref=kwargs)

    def _new_project_ref(self, ref=None):
        ref = ref or {}
        ref.setdefault('domain_id', uuid.uuid4().hex)
        ref.setdefault('enabled', True)
        ref.setdefault('name', uuid.uuid4().hex)
        return ref

    def test_list_projects_for_user(self):
        ref_list = [self.new_ref(), self.new_ref()]
        user_id = uuid.uuid4().hex

        self.stub_entity('GET',
                         ['users', user_id, self.collection_key],
                         entity=ref_list)

        returned_list = self.manager.list(user=user_id)
        self.assertEqual(len(ref_list), len(returned_list))
        [self.assertIsInstance(r, self.model) for r in returned_list]

    def test_list_projects_for_domain(self):
        ref_list = [self.new_ref(), self.new_ref()]
        domain_id = uuid.uuid4().hex

        self.stub_entity('GET', [self.collection_key],
                         entity=ref_list)

        returned_list = self.manager.list(domain=domain_id)
        self.assertEqual(len(ref_list), len(returned_list))
        [self.assertIsInstance(r, self.model) for r in returned_list]

        self.assertQueryStringIs('domain_id=%s' % domain_id)

    def test_create_with_parent(self):
        parent_ref = self.new_ref()
        parent_ref['parent_id'] = uuid.uuid4().hex
        parent = self.test_create(ref=parent_ref)
        parent.id = parent_ref['id']

        # Create another project under 'parent' in the hierarchy
        ref = self.new_ref()
        ref['parent_id'] = parent.id

        child_ref = ref.copy()
        del child_ref['parent_id']
        child_ref['parent'] = parent

        # test_create() pops the 'id' of the mocked response
        del ref['id']

        # Resource objects may peform lazy-loading. The create() method of
        # ProjectManager will try to access the 'uuid' attribute of the parent
        # object, which will trigger a call to fetch the Resource attributes.
        self.stub_entity('GET', id=parent_ref['id'], entity=parent_ref)
        self.test_create(ref=child_ref, req_ref=ref)

    def test_create_with_parent_id(self):
        ref = self._new_project_ref()
        ref['parent_id'] = uuid.uuid4().hex

        self.stub_entity('POST', entity=ref, status_code=201)

        returned = self.manager.create(name=ref['name'],
                                       domain=ref['domain_id'],
                                       parent_id=ref['parent_id'])

        self.assertIsInstance(returned, self.model)
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)
        self.assertEntityRequestBodyIs(ref)

    def test_create_with_parent_and_parent_id(self):
        ref = self._new_project_ref()
        ref['parent_id'] = uuid.uuid4().hex

        self.stub_entity('POST', entity=ref, status_code=201)

        # Should ignore the 'parent_id' argument since we are also passing
        # 'parent'
        returned = self.manager.create(name=ref['name'],
                                       domain=ref['domain_id'],
                                       parent=ref['parent_id'],
                                       parent_id=uuid.uuid4().hex)

        self.assertIsInstance(returned, self.model)
        for attr in ref:
            self.assertEqual(
                getattr(returned, attr),
                ref[attr],
                'Expected different %s' % attr)
        self.assertEntityRequestBodyIs(ref)

    def _create_projects_hierarchy(self, hierarchy_size=3):
        """Creates a project hierarchy with specified size.

        :param hierarchy_size: the desired hierarchy size, default is 3.

        :returns: a list of the projects in the created hierarchy.

        """

        ref = self.new_ref()
        project_id = ref['id']
        projects = [ref]

        for i in range(1, hierarchy_size):
            new_ref = self.new_ref()
            new_ref['parent_id'] = project_id
            projects.append(new_ref)
            project_id = new_ref['id']

        return projects

    def test_get_with_subtree_as_ids(self):
        projects = self._create_projects_hierarchy()
        ref = projects[0]

        # We will query for projects[0] subtree, it should include projects[1]
        # and projects[2] structured like the following:
        # {
        #   projects[1]: {
        #       projects[2]: None
        #   }
        # }
        ref['subtree'] = {
            projects[1]['id']: {
                projects[2]['id']: None
            }
        }

        self.stub_entity('GET', id=ref['id'], entity=ref)

        returned = self.manager.get(ref['id'], subtree_as_ids=True)
        self.assertQueryStringIs('subtree_as_ids')
        self.assertDictEqual(ref['subtree'], returned.subtree)

    def test_get_with_parents_as_ids(self):
        projects = self._create_projects_hierarchy()
        ref = projects[2]

        # We will query for projects[2] parents, it should include projects[1]
        # and projects[0] structured like the following:
        # {
        #   projects[1]: {
        #       projects[0]: None
        #   }
        # }
        ref['parents'] = {
            projects[1]['id']: {
                projects[0]['id']: None
            }
        }

        self.stub_entity('GET', id=ref['id'], entity=ref)

        returned = self.manager.get(ref['id'], parents_as_ids=True)
        self.assertQueryStringIs('parents_as_ids')
        self.assertDictEqual(ref['parents'], returned.parents)

    def test_get_with_parents_as_ids_and_subtree_as_ids(self):
        ref = self.new_ref()
        projects = self._create_projects_hierarchy()
        ref = projects[1]

        # We will query for projects[1] subtree and parents. The subtree should
        # include projects[2] and the parents should include projects[2].
        ref['parents'] = {
            projects[0]['id']: None
        }
        ref['subtree'] = {
            projects[2]['id']: None
        }

        self.stub_entity('GET', id=ref['id'], entity=ref)

        returned = self.manager.get(ref['id'],
                                    parents_as_ids=True,
                                    subtree_as_ids=True)
        self.assertQueryStringIs('subtree_as_ids&parents_as_ids')
        self.assertDictEqual(ref['parents'], returned.parents)
        self.assertDictEqual(ref['subtree'], returned.subtree)

    def test_get_with_subtree_as_list(self):
        projects = self._create_projects_hierarchy()
        ref = projects[0]

        ref['subtree_as_list'] = []
        for i in range(1, len(projects)):
            ref['subtree_as_list'].append(projects[i])

        self.stub_entity('GET', id=ref['id'], entity=ref)

        returned = self.manager.get(ref['id'], subtree_as_list=True)
        self.assertQueryStringIs('subtree_as_list')
        for i in range(1, len(projects)):
            for attr in projects[i]:
                child = getattr(returned, 'subtree_as_list')[i - 1]
                self.assertEqual(
                    child[attr],
                    projects[i][attr],
                    'Expected different %s' % attr)

    def test_get_with_parents_as_list(self):
        projects = self._create_projects_hierarchy()
        ref = projects[2]

        ref['parents_as_list'] = []
        for i in range(0, len(projects) - 1):
            ref['parents_as_list'].append(projects[i])

        self.stub_entity('GET', id=ref['id'], entity=ref)

        returned = self.manager.get(ref['id'], parents_as_list=True)
        self.assertQueryStringIs('parents_as_list')
        for i in range(0, len(projects) - 1):
            for attr in projects[i]:
                parent = getattr(returned, 'parents_as_list')[i]
                self.assertEqual(
                    parent[attr],
                    projects[i][attr],
                    'Expected different %s' % attr)

    def test_get_with_parents_as_list_and_subtree_as_list(self):
        ref = self.new_ref()
        projects = self._create_projects_hierarchy()
        ref = projects[1]

        ref['parents_as_list'] = [projects[0]]
        ref['subtree_as_list'] = [projects[2]]

        self.stub_entity('GET', id=ref['id'], entity=ref)

        returned = self.manager.get(ref['id'],
                                    parents_as_list=True,
                                    subtree_as_list=True)
        self.assertQueryStringIs('subtree_as_list&parents_as_list')

        for attr in projects[0]:
            parent = getattr(returned, 'parents_as_list')[0]
            self.assertEqual(
                parent[attr],
                projects[0][attr],
                'Expected different %s' % attr)

        for attr in projects[2]:
            child = getattr(returned, 'subtree_as_list')[0]
            self.assertEqual(
                child[attr],
                projects[2][attr],
                'Expected different %s' % attr)

    def test_get_with_invalid_parameters_combination(self):
        # subtree_as_list and subtree_as_ids can not be included at the
        # same time in the call.
        self.assertRaises(exceptions.ValidationError,
                          self.manager.get,
                          project=uuid.uuid4().hex,
                          subtree_as_list=True,
                          subtree_as_ids=True)

        # parents_as_list and parents_as_ids can not be included at the
        # same time in the call.
        self.assertRaises(exceptions.ValidationError,
                          self.manager.get,
                          project=uuid.uuid4().hex,
                          parents_as_list=True,
                          parents_as_ids=True)

    def test_update_with_parent_project(self):
        ref = self.new_ref()
        ref['parent_id'] = uuid.uuid4().hex

        self.stub_entity('PATCH', id=ref['id'], entity=ref, status_code=403)
        req_ref = ref.copy()
        req_ref.pop('id')

        # NOTE(rodrigods): this is the expected behaviour of the Identity
        # server, a different implementation might not fail this request.
        self.assertRaises(exceptions.Forbidden, self.manager.update,
                          ref['id'], **utils.parameterize(req_ref))
