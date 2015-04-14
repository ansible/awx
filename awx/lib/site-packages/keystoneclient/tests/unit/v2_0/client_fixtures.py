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
    return fixture.V2Token(token_id='3e2813b7ba0b4006840c3825860b86ed',
                           expires='2012-10-03T16:58:01Z',
                           user_id='c4da488862bd435c9e6c0275a0d0e49a',
                           user_name='exampleuser')


def project_scoped_token():
    _TENANT_ID = '225da22d3ce34b15877ea70b2a575f58'

    f = fixture.V2Token(token_id='04c7d5ffaeef485f9dc69c06db285bdb',
                        expires='2012-10-03T16:53:36Z',
                        tenant_id='225da22d3ce34b15877ea70b2a575f58',
                        tenant_name='exampleproject',
                        user_id='c4da488862bd435c9e6c0275a0d0e49a',
                        user_name='exampleuser')

    f.add_role(id='member_id', name='Member')

    s = f.add_service('volume', 'Volume Service')
    s.add_endpoint(public='http://public.com:8776/v1/%s' % _TENANT_ID,
                   admin='http://admin:8776/v1/%s' % _TENANT_ID,
                   internal='http://internal:8776/v1/%s' % _TENANT_ID,
                   region='RegionOne')

    s = f.add_service('image', 'Image Service')
    s.add_endpoint(public='http://public.com:9292/v1',
                   admin='http://admin:9292/v1',
                   internal='http://internal:9292/v1',
                   region='RegionOne')

    s = f.add_service('compute', 'Compute Service')
    s.add_endpoint(public='http://public.com:8774/v2/%s' % _TENANT_ID,
                   admin='http://admin:8774/v2/%s' % _TENANT_ID,
                   internal='http://internal:8774/v2/%s' % _TENANT_ID,
                   region='RegionOne')

    s = f.add_service('ec2', 'EC2 Service')
    s.add_endpoint(public='http://public.com:8773/services/Cloud',
                   admin='http://admin:8773/services/Admin',
                   internal='http://internal:8773/services/Cloud',
                   region='RegionOne')

    s = f.add_service('identity', 'Identity Service')
    s.add_endpoint(public='http://public.com:5000/v2.0',
                   admin='http://admin:35357/v2.0',
                   internal='http://internal:5000/v2.0',
                   region='RegionOne')

    return f


def auth_response_body():
    f = fixture.V2Token(token_id='ab48a9efdfedb23ty3494',
                        expires='2010-11-01T03:32:15-05:00',
                        tenant_id='345',
                        tenant_name='My Project',
                        user_id='123',
                        user_name='jqsmith')

    f.add_role(id='234', name='compute:admin')
    role = f.add_role(id='235', name='object-store:admin')
    role['tenantId'] = '1'

    s = f.add_service('compute', 'Cloud Servers')
    endpoint = s.add_endpoint(public='https://compute.north.host/v1/1234',
                              internal='https://compute.north.host/v1/1234',
                              region='North')
    endpoint['tenantId'] = '1'
    endpoint['versionId'] = '1.0'
    endpoint['versionInfo'] = 'https://compute.north.host/v1.0/'
    endpoint['versionList'] = 'https://compute.north.host/'

    endpoint = s.add_endpoint(public='https://compute.north.host/v1.1/3456',
                              internal='https://compute.north.host/v1.1/3456',
                              region='North')
    endpoint['tenantId'] = '2'
    endpoint['versionId'] = '1.1'
    endpoint['versionInfo'] = 'https://compute.north.host/v1.1/'
    endpoint['versionList'] = 'https://compute.north.host/'

    s = f.add_service('object-store', 'Cloud Files')
    endpoint = s.add_endpoint(public='https://swift.north.host/v1/blah',
                              internal='https://swift.north.host/v1/blah',
                              region='South')
    endpoint['tenantId'] = '11'
    endpoint['versionId'] = '1.0'
    endpoint['versionInfo'] = 'uri'
    endpoint['versionList'] = 'uri'

    endpoint = s.add_endpoint(public='https://swift.north.host/v1.1/blah',
                              internal='https://compute.north.host/v1.1/blah',
                              region='South')
    endpoint['tenantId'] = '2'
    endpoint['versionId'] = '1.1'
    endpoint['versionInfo'] = 'https://swift.north.host/v1.1/'
    endpoint['versionList'] = 'https://swift.north.host/'

    s = f.add_service('image', 'Image Servers')
    s.add_endpoint(public='https://image.north.host/v1/',
                   internal='https://image-internal.north.host/v1/',
                   region='North')
    s.add_endpoint(public='https://image.south.host/v1/',
                   internal='https://image-internal.south.host/v1/',
                   region='South')

    return f
