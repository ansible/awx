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

from keystoneclient import utils
from keystoneclient.v2_0 import client


@utils.arg('--user-name', metavar='<user-name>', default='admin', dest='user',
           help='The name of the user to be created (default="admin").')
@utils.arg('--pass', metavar='<password>', required=True, dest='passwd',
           help='The password for the new user.')
@utils.arg('--role-name', metavar='<role-name>', default='admin', dest='role',
           help='The name of the role to be created and granted to the user '
           '(default="admin").')
@utils.arg('--tenant-name', metavar='<tenant-name>', default='admin',
           dest='tenant',
           help='The name of the tenant to be created (default="admin").')
def do_bootstrap(kc, args):
    """Grants a new role to a new user on a new tenant, after creating each."""
    tenant = kc.tenants.create(tenant_name=args.tenant)
    role = kc.roles.create(name=args.role)
    user = kc.users.create(name=args.user, password=args.passwd, email=None)
    kc.roles.add_user_role(user=user, role=role, tenant=tenant)

    # verify the result
    user_client = client.Client(
        username=args.user,
        password=args.passwd,
        tenant_name=args.tenant,
        auth_url=kc.management_url)
    user_client.authenticate()
