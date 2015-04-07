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

from __future__ import unicode_literals

from keystoneclient import fixture


def unscoped_token():
    return fixture.V3Token(user_id='c4da488862bd435c9e6c0275a0d0e49a',
                           user_name='exampleuser',
                           user_domain_id='4e6893b7ba0b4006840c3845660b86ed',
                           user_domain_name='exampledomain',
                           expires='2010-11-01T03:32:15-05:00')


def domain_scoped_token():
    f = fixture.V3Token(user_id='c4da488862bd435c9e6c0275a0d0e49a',
                        user_name='exampleuser',
                        user_domain_id='4e6893b7ba0b4006840c3845660b86ed',
                        user_domain_name='exampledomain',
                        expires='2010-11-01T03:32:15-05:00',
                        domain_id='8e9283b7ba0b1038840c3842058b86ab',
                        domain_name='anotherdomain')

    f.add_role(id='76e72a', name='admin')
    f.add_role(id='f4f392', name='member')
    region = 'RegionOne'

    s = f.add_service('volume')
    s.add_standard_endpoints(public='http://public.com:8776/v1/None',
                             internal='http://internal.com:8776/v1/None',
                             admin='http://admin.com:8776/v1/None',
                             region=region)

    s = f.add_service('image')
    s.add_standard_endpoints(public='http://public.com:9292/v1',
                             internal='http://internal:9292/v1',
                             admin='http://admin:9292/v1',
                             region=region)

    s = f.add_service('compute')
    s.add_standard_endpoints(public='http://public.com:8774/v1.1/None',
                             internal='http://internal:8774/v1.1/None',
                             admin='http://admin:8774/v1.1/None',
                             region=region)

    s = f.add_service('ec2')
    s.add_standard_endpoints(public='http://public.com:8773/services/Cloud',
                             internal='http://internal:8773/services/Cloud',
                             admin='http://admin:8773/services/Admin',
                             region=region)

    s = f.add_service('identity')
    s.add_standard_endpoints(public='http://public.com:5000/v3',
                             internal='http://internal:5000/v3',
                             admin='http://admin:35357/v3',
                             region=region)

    return f


def project_scoped_token():
    f = fixture.V3Token(user_id='c4da488862bd435c9e6c0275a0d0e49a',
                        user_name='exampleuser',
                        user_domain_id='4e6893b7ba0b4006840c3845660b86ed',
                        user_domain_name='exampledomain',
                        expires='2010-11-01T03:32:15-05:00',
                        project_id='225da22d3ce34b15877ea70b2a575f58',
                        project_name='exampleproject',
                        project_domain_id='4e6893b7ba0b4006840c3845660b86ed',
                        project_domain_name='exampledomain')

    f.add_role(id='76e72a', name='admin')
    f.add_role(id='f4f392', name='member')

    region = 'RegionOne'
    tenant = '225da22d3ce34b15877ea70b2a575f58'

    s = f.add_service('volume')
    s.add_standard_endpoints(public='http://public.com:8776/v1/%s' % tenant,
                             internal='http://internal:8776/v1/%s' % tenant,
                             admin='http://admin:8776/v1/%s' % tenant,
                             region=region)

    s = f.add_service('image')
    s.add_standard_endpoints(public='http://public.com:9292/v1',
                             internal='http://internal:9292/v1',
                             admin='http://admin:9292/v1',
                             region=region)

    s = f.add_service('compute')
    s.add_standard_endpoints(public='http://public.com:8774/v2/%s' % tenant,
                             internal='http://internal:8774/v2/%s' % tenant,
                             admin='http://admin:8774/v2/%s' % tenant,
                             region=region)

    s = f.add_service('ec2')
    s.add_standard_endpoints(public='http://public.com:8773/services/Cloud',
                             internal='http://internal:8773/services/Cloud',
                             admin='http://admin:8773/services/Admin',
                             region=region)

    s = f.add_service('identity')
    s.add_standard_endpoints(public='http://public.com:5000/v3',
                             internal='http://internal:5000/v3',
                             admin='http://admin:35357/v3',
                             region=region)

    return f


AUTH_SUBJECT_TOKEN = '3e2813b7ba0b4006840c3825860b86ed'

AUTH_RESPONSE_HEADERS = {
    'X-Subject-Token': AUTH_SUBJECT_TOKEN,
}


def auth_response_body():
    f = fixture.V3Token(user_id='567',
                        user_name='test',
                        user_domain_id='1',
                        user_domain_name='aDomain',
                        expires='2010-11-01T03:32:15-05:00',
                        project_domain_id='123',
                        project_domain_name='aDomain',
                        project_id='345',
                        project_name='aTenant')

    f.add_role(id='76e72a', name='admin')
    f.add_role(id='f4f392', name='member')

    s = f.add_service('compute', name='nova')
    s.add_standard_endpoints(
        public='https://compute.north.host/novapi/public',
        internal='https://compute.north.host/novapi/internal',
        admin='https://compute.north.host/novapi/admin',
        region='North')

    s = f.add_service('object-store', name='swift')
    s.add_standard_endpoints(
        public='http://swift.north.host/swiftapi/public',
        internal='http://swift.north.host/swiftapi/internal',
        admin='http://swift.north.host/swiftapi/admin',
        region='South')

    s = f.add_service('image', name='glance')
    s.add_standard_endpoints(
        public='http://glance.north.host/glanceapi/public',
        internal='http://glance.north.host/glanceapi/internal',
        admin='http://glance.north.host/glanceapi/admin',
        region='North')

    s.add_standard_endpoints(
        public='http://glance.south.host/glanceapi/public',
        internal='http://glance.south.host/glanceapi/internal',
        admin='http://glance.south.host/glanceapi/admin',
        region='South')

    return f


def trust_token():
    return fixture.V3Token(user_id='0ca8f6',
                           user_name='exampleuser',
                           user_domain_id='4e6893b7ba0b4006840c3845660b86ed',
                           user_domain_name='exampledomain',
                           expires='2010-11-01T03:32:15-05:00',
                           trust_id='fe0aef',
                           trust_impersonation=False,
                           trustee_user_id='0ca8f6',
                           trustor_user_id='bd263c')
