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

import os
import sys

import mock
from oslo_serialization import jsonutils
import six
from testtools import matchers

from keystoneclient import fixture
from keystoneclient.tests.unit.v2_0 import utils


DEFAULT_USERNAME = 'username'
DEFAULT_PASSWORD = 'password'
DEFAULT_TENANT_ID = 'tenant_id'
DEFAULT_TENANT_NAME = 'tenant_name'
DEFAULT_AUTH_URL = 'http://127.0.0.1:5000/v2.0/'
DEFAULT_ADMIN_URL = 'http://127.0.0.1:35357/v2.0/'


class ShellTests(utils.TestCase):

    TEST_URL = DEFAULT_ADMIN_URL

    def setUp(self):
        """Patch os.environ to avoid required auth info."""

        super(ShellTests, self).setUp()

        self.old_environment = os.environ.copy()
        os.environ = {
            'OS_USERNAME': DEFAULT_USERNAME,
            'OS_PASSWORD': DEFAULT_PASSWORD,
            'OS_TENANT_ID': DEFAULT_TENANT_ID,
            'OS_TENANT_NAME': DEFAULT_TENANT_NAME,
            'OS_AUTH_URL': DEFAULT_AUTH_URL,
        }
        import keystoneclient.shell
        self.shell = keystoneclient.shell.OpenStackIdentityShell()

        self.token = fixture.V2Token()
        self.token.set_scope()
        svc = self.token.add_service('identity')
        svc.add_endpoint(public=DEFAULT_AUTH_URL,
                         admin=DEFAULT_ADMIN_URL)

        self.stub_auth(json=self.token, base_url=DEFAULT_AUTH_URL)

    def tearDown(self):
        os.environ = self.old_environment
        super(ShellTests, self).tearDown()

    def run_command(self, cmd):
        orig = sys.stdout
        try:
            sys.stdout = six.StringIO()
            if isinstance(cmd, list):
                self.shell.main(cmd)
            else:
                self.shell.main(cmd.split())
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertEqual(exc_value.code, 0)
        finally:
            out = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = orig
        return out

    def assert_called(self, method, path, base_url=TEST_URL):
        self.assertEqual(method, self.requests_mock.last_request.method)
        self.assertEqual(base_url + path.lstrip('/'),
                         self.requests_mock.last_request.url)

    def test_user_list(self):
        self.stub_url('GET', ['users'], json={'users': []})
        self.run_command('user-list')
        self.assert_called('GET', '/users')

    def test_user_create(self):
        self.stub_url('POST', ['users'], json={'user': {}})
        self.run_command('user-create --name new-user')

        self.assert_called('POST', '/users')
        self.assertRequestBodyIs(json={'user': {'email': None,
                                                'password': None,
                                                'enabled': True,
                                                'name': 'new-user',
                                                'tenantId': None}})

    @mock.patch('sys.stdin', autospec=True)
    def test_user_create_password_prompt(self, mock_stdin):
        self.stub_url('POST', ['users'], json={'user': {}})

        with mock.patch('getpass.getpass') as mock_getpass:
            del(os.environ['OS_PASSWORD'])
            mock_stdin.isatty = lambda: True
            mock_getpass.return_value = 'newpass'
            self.run_command('user-create --name new-user --pass')

            self.assert_called('POST', '/users')
            self.assertRequestBodyIs(json={'user': {'email': None,
                                                    'password': 'newpass',
                                                    'enabled': True,
                                                    'name': 'new-user',
                                                    'tenantId': None}})

    def test_user_get(self):
        self.stub_url('GET', ['users', '1'],
                      json={'user': {'id': '1'}})
        self.run_command('user-get 1')
        self.assert_called('GET', '/users/1')

    def test_user_delete(self):
        self.stub_url('GET', ['users', '1'],
                      json={'user': {'id': '1'}})
        self.stub_url('DELETE', ['users', '1'])
        self.run_command('user-delete 1')
        self.assert_called('DELETE', '/users/1')

    def test_user_password_update(self):
        self.stub_url('GET', ['users', '1'],
                      json={'user': {'id': '1'}})
        self.stub_url('PUT', ['users', '1', 'OS-KSADM', 'password'])
        self.run_command('user-password-update --pass newpass 1')
        self.assert_called('PUT', '/users/1/OS-KSADM/password')

    def test_user_update(self):
        self.stub_url('PUT', ['users', '1'])
        self.stub_url('GET', ['users', '1'],
                      json={"user": {"tenantId": "1",
                                     "enabled": "true",
                                     "id": "1",
                                     "name": "username"}})

        self.run_command('user-update --name new-user1'
                         ' --email user@email.com --enabled true 1')
        self.assert_called('PUT', '/users/1')
        body = {'user': {'id': '1', 'email': 'user@email.com',
                         'enabled': True, 'name': 'new-user1'}}
        self.assertRequestBodyIs(json=body)

        required = 'User not updated, no arguments present.'
        out = self.run_command('user-update 1')
        self.assertThat(out, matchers.MatchesRegex(required))

        self.run_command(['user-update', '--email', '', '1'])
        self.assert_called('PUT', '/users/1')
        self.assertRequestBodyIs(json={'user': {'id': '1', 'email': ''}})

    def test_role_create(self):
        self.stub_url('POST', ['OS-KSADM', 'roles'], json={'role': {}})
        self.run_command('role-create --name new-role')
        self.assert_called('POST', '/OS-KSADM/roles')
        self.assertRequestBodyIs(json={"role": {"name": "new-role"}})

    def test_role_get(self):
        self.stub_url('GET', ['OS-KSADM', 'roles', '1'],
                      json={'role': {'id': '1'}})
        self.run_command('role-get 1')
        self.assert_called('GET', '/OS-KSADM/roles/1')

    def test_role_list(self):
        self.stub_url('GET', ['OS-KSADM', 'roles'], json={'roles': []})
        self.run_command('role-list')
        self.assert_called('GET', '/OS-KSADM/roles')

    def test_role_delete(self):
        self.stub_url('GET', ['OS-KSADM', 'roles', '1'],
                      json={'role': {'id': '1'}})
        self.stub_url('DELETE', ['OS-KSADM', 'roles', '1'])
        self.run_command('role-delete 1')
        self.assert_called('DELETE', '/OS-KSADM/roles/1')

    def test_user_role_add(self):
        self.stub_url('GET', ['users', '1'],
                      json={'user': {'id': '1'}})
        self.stub_url('GET', ['OS-KSADM', 'roles', '1'],
                      json={'role': {'id': '1'}})

        self.stub_url('PUT', ['users', '1', 'roles', 'OS-KSADM', '1'])
        self.run_command('user-role-add --user_id 1 --role_id 1')
        self.assert_called('PUT', '/users/1/roles/OS-KSADM/1')

    def test_user_role_list(self):
        self.stub_url('GET', ['tenants', self.token.tenant_id],
                      json={'tenant': {'id': self.token.tenant_id}})
        self.stub_url('GET', ['tenants', self.token.tenant_id,
                              'users', self.token.user_id, 'roles'],
                      json={'roles': []})

        url = '/tenants/%s/users/%s/roles' % (self.token.tenant_id,
                                              self.token.user_id)

        self.run_command('user-role-list --user_id %s --tenant-id %s' %
                         (self.token.user_id, self.token.tenant_id))
        self.assert_called('GET', url)

        self.run_command('user-role-list --user_id %s' % self.token.user_id)
        self.assert_called('GET', url)

        self.run_command('user-role-list')
        self.assert_called('GET', url)

    def test_user_role_remove(self):
        self.stub_url('GET', ['users', '1'],
                      json={'user': {'id': 1}})
        self.stub_url('GET', ['OS-KSADM', 'roles', '1'],
                      json={'role': {'id': 1}})
        self.stub_url('DELETE',
                      ['users', '1', 'roles', 'OS-KSADM', '1'])

        self.run_command('user-role-remove --user_id 1 --role_id 1')
        self.assert_called('DELETE', '/users/1/roles/OS-KSADM/1')

    def test_tenant_create(self):
        self.stub_url('POST', ['tenants'], json={'tenant': {}})
        self.run_command('tenant-create --name new-tenant')
        self.assertRequestBodyIs(json={"tenant": {"enabled": True,
                                                  "name": "new-tenant",
                                                  "description": None}})

    def test_tenant_get(self):
        self.stub_url('GET', ['tenants', '2'], json={'tenant': {}})
        self.run_command('tenant-get 2')
        self.assert_called('GET', '/tenants/2')

    def test_tenant_list(self):
        self.stub_url('GET', ['tenants'], json={'tenants': []})
        self.run_command('tenant-list')
        self.assert_called('GET', '/tenants')

    def test_tenant_update(self):
        self.stub_url('GET', ['tenants', '1'],
                      json={'tenant': {'id': '1'}})
        self.stub_url('GET', ['tenants', '2'],
                      json={'tenant': {'id': '2'}})
        self.stub_url('POST', ['tenants', '2'],
                      json={'tenant': {'id': '2'}})
        self.run_command('tenant-update'
                         ' --name new-tenant1 --enabled false'
                         ' --description desc 2')
        self.assert_called('POST', '/tenants/2')
        self.assertRequestBodyIs(json={"tenant": {"enabled": False,
                                                  "id": "2",
                                                  "description": "desc",
                                                  "name": "new-tenant1"}})

        required = 'Tenant not updated, no arguments present.'
        out = self.run_command('tenant-update 1')
        self.assertThat(out, matchers.MatchesRegex(required))

    def test_tenant_delete(self):
        self.stub_url('GET', ['tenants', '2'],
                      json={'tenant': {'id': '2'}})
        self.stub_url('DELETE', ['tenants', '2'])
        self.run_command('tenant-delete 2')
        self.assert_called('DELETE', '/tenants/2')

    def test_service_create_with_required_arguments_only(self):
        self.stub_url('POST', ['OS-KSADM', 'services'],
                      json={'OS-KSADM:service': {}})
        self.run_command('service-create --type compute')
        self.assert_called('POST', '/OS-KSADM/services')
        json = {"OS-KSADM:service": {"type": "compute",
                                     "name": None,
                                     "description": None}}
        self.assertRequestBodyIs(json=json)

    def test_service_create_with_all_arguments(self):
        self.stub_url('POST', ['OS-KSADM', 'services'],
                      json={'OS-KSADM:service': {}})
        self.run_command('service-create --type compute '
                         '--name service1 --description desc1')
        self.assert_called('POST', '/OS-KSADM/services')
        json = {"OS-KSADM:service": {"type": "compute",
                                     "name": "service1",
                                     "description": "desc1"}}
        self.assertRequestBodyIs(json=json)

    def test_service_get(self):
        self.stub_url('GET', ['OS-KSADM', 'services', '1'],
                      json={'OS-KSADM:service': {'id': '1'}})
        self.run_command('service-get 1')
        self.assert_called('GET', '/OS-KSADM/services/1')

    def test_service_list(self):
        self.stub_url('GET', ['OS-KSADM', 'services'],
                      json={'OS-KSADM:services': []})
        self.run_command('service-list')
        self.assert_called('GET', '/OS-KSADM/services')

    def test_service_delete(self):
        self.stub_url('GET', ['OS-KSADM', 'services', '1'],
                      json={'OS-KSADM:service': {'id': 1}})
        self.stub_url('DELETE', ['OS-KSADM', 'services', '1'])
        self.run_command('service-delete 1')
        self.assert_called('DELETE', '/OS-KSADM/services/1')

    def test_catalog(self):
        self.run_command('catalog')
        self.run_command('catalog --service compute')

    def test_ec2_credentials_create(self):
        self.stub_url('POST',
                      ['users', self.token.user_id, 'credentials', 'OS-EC2'],
                      json={'credential': {}})

        url = '/users/%s/credentials/OS-EC2' % self.token.user_id
        self.run_command('ec2-credentials-create --tenant-id 1 '
                         '--user-id %s' % self.token.user_id)
        self.assert_called('POST', url)
        self.assertRequestBodyIs(json={'tenant_id': '1'})

        self.run_command('ec2-credentials-create --tenant-id 1')
        self.assert_called('POST', url)
        self.assertRequestBodyIs(json={'tenant_id': '1'})

        self.run_command('ec2-credentials-create')
        self.assert_called('POST', url)
        self.assertRequestBodyIs(json={'tenant_id': self.token.tenant_id})

    def test_ec2_credentials_delete(self):
        self.stub_url('DELETE',
                      ['users', self.token.user_id,
                       'credentials', 'OS-EC2', '2'])
        self.run_command('ec2-credentials-delete --access 2 --user-id %s' %
                         self.token.user_id)

        url = '/users/%s/credentials/OS-EC2/2' % self.token.user_id
        self.assert_called('DELETE', url)

        self.run_command('ec2-credentials-delete --access 2')
        self.assert_called('DELETE', url)

    def test_ec2_credentials_list(self):
        self.stub_url('GET',
                      ['users', self.token.user_id, 'credentials', 'OS-EC2'],
                      json={'credentials': []})
        self.run_command('ec2-credentials-list --user-id %s'
                         % self.token.user_id)

        url = '/users/%s/credentials/OS-EC2' % self.token.user_id
        self.assert_called('GET', url)

        self.run_command('ec2-credentials-list')
        self.assert_called('GET', url)

    def test_ec2_credentials_get(self):
        self.stub_url('GET',
                      ['users', '1', 'credentials', 'OS-EC2', '2'],
                      json={'credential': {}})
        self.run_command('ec2-credentials-get --access 2 --user-id 1')
        self.assert_called('GET', '/users/1/credentials/OS-EC2/2')

    def test_bootstrap(self):
        user = {'user': {'id': '1'}}
        role = {'role': {'id': '1'}}
        tenant = {'tenant': {'id': '1'}}

        token = fixture.V2Token(user_id=1, tenant_id=1)
        token.add_role(id=1)
        svc = token.add_service('identity')
        svc.add_endpoint(public=DEFAULT_AUTH_URL,
                         admin=DEFAULT_ADMIN_URL)

        self.stub_auth(json=token)

        self.stub_url('POST', ['OS-KSADM', 'roles'], json=role)
        self.stub_url('GET', ['OS-KSADM', 'roles', '1'], json=role)
        self.stub_url('POST', ['tenants'], json=tenant)
        self.stub_url('GET', ['tenants', '1'], json=tenant)
        self.stub_url('POST', ['users'], json=user)
        self.stub_url('GET', ['users', '1'], json=user)
        self.stub_url('PUT',
                      ['tenants', '1', 'users', '1', 'roles', 'OS-KSADM', '1'],
                      json=role)

        self.run_command('bootstrap --user-name new-user'
                         ' --pass 1 --role-name admin'
                         ' --tenant-name new-tenant')

        def called_anytime(method, path, json=None):
            test_url = self.TEST_URL.strip('/')
            for r in self.requests_mock.request_history:
                if not r.method == method:
                    continue
                if not r.url == test_url + path:
                    continue

                if json:
                    json_body = jsonutils.loads(r.body)
                    if not json_body == json:
                        continue

                return True

            raise AssertionError('URL never called')

        called_anytime('POST', '/users', {'user': {'email': None,
                                                   'password': '1',
                                                   'enabled': True,
                                                   'name': 'new-user',
                                                   'tenantId': None}})

        called_anytime('POST', '/tenants', {"tenant": {"enabled": True,
                                                       "name": "new-tenant",
                                                       "description": None}})

        called_anytime('POST', '/OS-KSADM/roles',
                       {"role": {"name": "admin"}})

        called_anytime('PUT', '/tenants/1/users/1/roles/OS-KSADM/1')

    def test_bash_completion(self):
        self.run_command('bash-completion')

    def test_help(self):
        out = self.run_command('help')
        required = 'usage: keystone'
        self.assertThat(out, matchers.MatchesRegex(required))

    def test_password_update(self):
        self.stub_url('PATCH',
                      ['OS-KSCRUD', 'users', self.token.user_id],
                      base_url=DEFAULT_AUTH_URL)
        self.run_command('password-update --current-password oldpass'
                         ' --new-password newpass')
        self.assert_called('PATCH',
                           '/OS-KSCRUD/users/%s' % self.token.user_id,
                           base_url=DEFAULT_AUTH_URL)
        self.assertRequestBodyIs(json={'user': {'original_password': 'oldpass',
                                                'password': 'newpass'}})

    def test_endpoint_create(self):
        self.stub_url('GET', ['OS-KSADM', 'services', '1'],
                      json={'OS-KSADM:service': {'id': '1'}})
        self.stub_url('POST', ['endpoints'], json={'endpoint': {}})
        self.run_command('endpoint-create --service-id 1 '
                         '--publicurl=http://example.com:1234/go')
        self.assert_called('POST', '/endpoints')
        json = {'endpoint': {'adminurl': None,
                             'service_id': '1',
                             'region': 'regionOne',
                             'internalurl': None,
                             'publicurl': "http://example.com:1234/go"}}
        self.assertRequestBodyIs(json=json)

    def test_endpoint_list(self):
        self.stub_url('GET', ['endpoints'], json={'endpoints': []})
        self.run_command('endpoint-list')
        self.assert_called('GET', '/endpoints')
