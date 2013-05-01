# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
# 
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License. 
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Ansible Commander. If not, see <http://www.gnu.org/licenses/>.

import contextlib
import datetime
import json
import os
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth.models import User
import django.test
from django.test.client import Client
from lib.main.models import *


class BaseTestMixin(object):
    '''
    Mixin with shared code for use by all test cases.
    '''

    def setUp(self):
        super(BaseTestMixin, self).setUp()
        self.object_ctr = 0
        self._temp_project_dirs = []
        self._current_auth = None
        self._user_passwords = {}

    def tearDown(self):
        super(BaseTestMixin, self).tearDown()
        for project_dir in self._temp_project_dirs:
            if os.path.exists(project_dir):
                shutil.rmtree(project_dir, True)

    def make_user(self, username, password=None, super_user=False):
        user = None
        password = password or username
        if super_user:
            user = User.objects.create_superuser(username, "%s@example.com", password)
        else:
            user = User.objects.create_user(username, "%s@example.com", password)
        self.assertTrue(user.auth_token)
        self._user_passwords[user.username] = password
        return user

    @contextlib.contextmanager
    def current_user(self, user_or_username, password=None):
        try:
            if isinstance(user_or_username, User):
                username = user_or_username.username
            else:
                username = user_or_username
            password = password or self._user_passwords.get(username)
            previous_auth = self._current_auth
            self._current_auth = (username, password)
            yield
        finally:
            self._current_auth = previous_auth

    def make_organizations(self, created_by, count=1):
        results = []
        for x in range(0, count):
            self.object_ctr = self.object_ctr + 1
            results.append(Organization.objects.create(
                name="org%s-%s" % (x, self.object_ctr), description="org%s" % x, created_by=created_by
            ))
        return results

    def make_projects(self, created_by, count=1, playbook_content=''):
        results = []

        if not os.path.exists(settings.PROJECTS_ROOT):
            os.makedirs(settings.PROJECTS_ROOT)

        for x in range(0, count):
            self.object_ctr = self.object_ctr + 1
            # Create temp project directory.

            project_dir = tempfile.mkdtemp(dir=settings.PROJECTS_ROOT)
            self._temp_project_dirs.append(project_dir)
            # Create temp playbook in project (if playbook content is given).
            if playbook_content:
                handle, playbook_path = tempfile.mkstemp(suffix='.yml',
                                                         dir=project_dir)
                test_playbook_file = os.fdopen(handle, 'w')
                test_playbook_file.write(playbook_content)
                test_playbook_file.close()
            results.append(Project.objects.create(
                name="proj%s-%s" % (x, self.object_ctr), description="proj%s" % x,
                #scm_type='git',  default_playbook='foo.yml',
                local_path=project_dir, created_by=created_by
            ))
        return results

    def check_pagination_and_size(self, data, desired_count, previous=None, next=None):
        self.assertEquals(data['previous'], previous)
        self.assertEquals(data['next'], next)

    def setup_users(self, just_super_user=False):
        # Create a user.
        self.super_username  = 'admin'
        self.super_password  = 'admin'
        self.normal_username = 'normal'
        self.normal_password = 'normal'
        self.other_username  = 'other'
        self.other_password  = 'other'

        self.super_django_user  = self.make_user(self.super_username,  self.super_password, super_user=True)

        if not just_super_user:

            self.normal_django_user = self.make_user(self.normal_username, self.normal_password, super_user=False)
            self.other_django_user  = self.make_user(self.other_username,  self.other_password, super_user=False)

    def get_super_credentials(self):
        return (self.super_username, self.super_password)

    def get_normal_credentials(self):
        return (self.normal_username, self.normal_password)

    def get_other_credentials(self):
        return (self.other_username, self.other_password)

    def get_invalid_credentials(self):
        return ('random', 'combination')
        
    def _generic_rest(self, url, data=None, expect=204, auth=None, method=None):
        assert method is not None
        method_name = method.lower()
        if method_name not in ('options', 'head', 'get', 'delete'):
            assert data is not None
        client = Client()
        auth = auth or self._current_auth
        if auth:
            if isinstance(auth, (list, tuple)):
                client.login(username=auth[0], password=auth[1])
            elif isinstance(auth, basestring):
                client = Client(HTTP_AUTHORIZATION='Token %s' % auth)
        method = getattr(client, method_name)
        response = None
        if data is not None:
            response = method(url, json.dumps(data), 'application/json')
        else:
            response = method(url)

        if response.status_code == 500 and expect != 500:
            assert False, "Failed: %s" % response.content
        if expect is not None:
            assert response.status_code == expect, "expected status %s, got %s for url=%s as auth=%s: %s" % (expect, response.status_code, url, auth, response.content)
        if method_name == 'head':
            self.assertFalse(response.content)
        if response.status_code not in [ 202, 204, 400, 405, 409 ] and method_name != 'head':
            # no JSON responses in these at least for now, 400/409 should probably return some (FIXME)
            return json.loads(response.content)
        else:
            return None

    def options(self, url, expect=200, auth=None):
        return self._generic_rest(url, data=None, expect=expect, auth=auth, method='options')

    def head(self, url, expect=200, auth=None):
        return self._generic_rest(url, data=None, expect=expect, auth=auth, method='head')
 
    def get(self, url, expect=200, auth=None):
        return self._generic_rest(url, data=None, expect=expect, auth=auth, method='get')

    def post(self, url, data, expect=204, auth=None):
        return self._generic_rest(url, data=data, expect=expect, auth=auth, method='post')

    def put(self, url, data, expect=200, auth=None):
        return self._generic_rest(url, data=data, expect=expect, auth=auth, method='put')

    def delete(self, url, expect=201, auth=None):
        return self._generic_rest(url, data=None, expect=expect, auth=auth, method='delete')

    def get_urls(self, collection_url, auth=None):
        # TODO: this test helper function doesn't support pagination
        data = self.get(collection_url, expect=200, auth=auth)
        return [item['url'] for item in data['results']]
    
class BaseTest(BaseTestMixin, django.test.TestCase):
    '''
    Base class for unit tests.
    '''

class BaseTransactionTest(BaseTestMixin, django.test.TransactionTestCase):
    '''
    Base class for tests requiring transactions (or where the test database
    needs to be accessed by subprocesses).
    '''
