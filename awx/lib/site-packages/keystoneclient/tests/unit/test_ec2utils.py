# Copyright 2012 OpenStack Foundation
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

from __future__ import unicode_literals

import testtools

from keystoneclient.contrib.ec2 import utils


class Ec2SignerTest(testtools.TestCase):

    def setUp(self):
        super(Ec2SignerTest, self).setUp()
        self.access = '966afbde20b84200ae4e62e09acf46b2'
        self.secret = '89cdf9e94e2643cab35b8b8ac5a51f83'
        self.signer = utils.Ec2Signer(self.secret)

    def test_v4_creds_header(self):
        auth_str = 'AWS4-HMAC-SHA256 blah'
        credentials = {'host': '127.0.0.1',
                       'verb': 'GET',
                       'path': '/v1/',
                       'params': {},
                       'headers': {'Authorization': auth_str}}
        self.assertTrue(self.signer._v4_creds(credentials))

    def test_v4_creds_param(self):
        credentials = {'host': '127.0.0.1',
                       'verb': 'GET',
                       'path': '/v1/',
                       'params': {'X-Amz-Algorithm': 'AWS4-HMAC-SHA256'},
                       'headers': {}}
        self.assertTrue(self.signer._v4_creds(credentials))

    def test_v4_creds_false(self):
        credentials = {'host': '127.0.0.1',
                       'verb': 'GET',
                       'path': '/v1/',
                       'params': {'SignatureVersion': '0',
                                  'AWSAccessKeyId': self.access,
                                  'Timestamp': '2012-11-27T11:47:02Z',
                                  'Action': 'Foo'}}
        self.assertFalse(self.signer._v4_creds(credentials))

    def test_generate_0(self):
        """Test generate function for v0 signature."""
        credentials = {'host': '127.0.0.1',
                       'verb': 'GET',
                       'path': '/v1/',
                       'params': {'SignatureVersion': '0',
                                  'AWSAccessKeyId': self.access,
                                  'Timestamp': '2012-11-27T11:47:02Z',
                                  'Action': 'Foo'}}
        signature = self.signer.generate(credentials)
        expected = 'SmXQEZAUdQw5glv5mX8mmixBtas='
        self.assertEqual(signature, expected)

    def test_generate_1(self):
        """Test generate function for v1 signature."""
        credentials = {'host': '127.0.0.1',
                       'verb': 'GET',
                       'path': '/v1/',
                       'params': {'SignatureVersion': '1',
                                  'AWSAccessKeyId': self.access}}
        signature = self.signer.generate(credentials)
        expected = 'VRnoQH/EhVTTLhwRLfuL7jmFW9c='
        self.assertEqual(signature, expected)

    def test_generate_v2_SHA256(self):
        """Test generate function for v2 signature, SHA256."""
        credentials = {'host': '127.0.0.1',
                       'verb': 'GET',
                       'path': '/v1/',
                       'params': {'SignatureVersion': '2',
                                  'AWSAccessKeyId': self.access}}
        signature = self.signer.generate(credentials)
        expected = 'odsGmT811GffUO0Eu13Pq+xTzKNIjJ6NhgZU74tYX/w='
        self.assertEqual(signature, expected)

    def test_generate_v2_SHA1(self):
        """Test generate function for v2 signature, SHA1."""
        credentials = {'host': '127.0.0.1',
                       'verb': 'GET',
                       'path': '/v1/',
                       'params': {'SignatureVersion': '2',
                                  'AWSAccessKeyId': self.access}}
        self.signer.hmac_256 = None
        signature = self.signer.generate(credentials)
        expected = 'ZqCxMI4ZtTXWI175743mJ0hy/Gc='
        self.assertEqual(signature, expected)

    def test_generate_v4(self):
        """Test v4 generator with data from AWS docs example.

        see:
        http://docs.aws.amazon.com/general/latest/gr/
        sigv4-create-canonical-request.html
        and
        http://docs.aws.amazon.com/general/latest/gr/
        sigv4-signed-request-examples.html
        """
        # Create a new signer object with the AWS example key
        secret = 'wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY'
        signer = utils.Ec2Signer(secret)

        body_hash = ('b6359072c78d70ebee1e81adcbab4f0'
                     '1bf2c23245fa365ef83fe8f1f955085e2')
        auth_str = ('AWS4-HMAC-SHA256 '
                    'Credential=AKIAIOSFODNN7EXAMPLE/20110909/'
                    'us-east-1/iam/aws4_request,'
                    'SignedHeaders=content-type;host;x-amz-date,')
        headers = {'Content-type':
                   'application/x-www-form-urlencoded; charset=utf-8',
                   'X-Amz-Date': '20110909T233600Z',
                   'Host': 'iam.amazonaws.com',
                   'Authorization': auth_str}
        # Note the example in the AWS docs is inconsistent, previous
        # examples specify no query string, but the final POST example
        # does, apparently incorrectly since an empty parameter list
        # aligns all steps and the final signature with the examples
        params = {'Action': 'CreateUser',
                  'UserName': 'NewUser',
                  'Version': '2010-05-08',
                  'X-Amz-Algorithm': 'AWS4-HMAC-SHA256',
                  'X-Amz-Credential': 'AKIAEXAMPLE/20140611/'
                                      'us-east-1/iam/aws4_request',
                  'X-Amz-Date': '20140611T231318Z',
                  'X-Amz-Expires': '30',
                  'X-Amz-SignedHeaders': 'host',
                  'X-Amz-Signature': 'ced6826de92d2bdeed8f846f0bf508e8'
                                     '559e98e4b0199114b84c54174deb456c'}
        credentials = {'host': 'iam.amazonaws.com',
                       'verb': 'POST',
                       'path': '/',
                       'params': params,
                       'headers': headers,
                       'body_hash': body_hash}
        signature = signer.generate(credentials)
        expected = ('ced6826de92d2bdeed8f846f0bf508e8'
                    '559e98e4b0199114b84c54174deb456c')
        self.assertEqual(signature, expected)

    def test_generate_v4_port(self):
        """Test v4 generator with host:port format."""
        # Create a new signer object with the AWS example key
        secret = 'wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY'
        signer = utils.Ec2Signer(secret)

        body_hash = ('b6359072c78d70ebee1e81adcbab4f0'
                     '1bf2c23245fa365ef83fe8f1f955085e2')
        auth_str = ('AWS4-HMAC-SHA256 '
                    'Credential=AKIAIOSFODNN7EXAMPLE/20110909/'
                    'us-east-1/iam/aws4_request,'
                    'SignedHeaders=content-type;host;x-amz-date,')
        headers = {'Content-type':
                   'application/x-www-form-urlencoded; charset=utf-8',
                   'X-Amz-Date': '20110909T233600Z',
                   'Host': 'foo:8000',
                   'Authorization': auth_str}
        # Note the example in the AWS docs is inconsistent, previous
        # examples specify no query string, but the final POST example
        # does, apparently incorrectly since an empty parameter list
        # aligns all steps and the final signature with the examples
        params = {}
        credentials = {'host': 'foo:8000',
                       'verb': 'POST',
                       'path': '/',
                       'params': params,
                       'headers': headers,
                       'body_hash': body_hash}
        signature = signer.generate(credentials)

        expected = ('26dd92ea79aaa49f533d13b1055acdc'
                    'd7d7321460d64621f96cc79c4f4d4ab2b')
        self.assertEqual(signature, expected)

    def test_generate_v4_port_strip(self):
        """Test v4 generator with host:port format, but for an old
        (<2.9.3) version of boto, where the port should be stripped
        to match boto behavior.
        """
        # Create a new signer object with the AWS example key
        secret = 'wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY'
        signer = utils.Ec2Signer(secret)

        body_hash = ('b6359072c78d70ebee1e81adcbab4f0'
                     '1bf2c23245fa365ef83fe8f1f955085e2')
        auth_str = ('AWS4-HMAC-SHA256 '
                    'Credential=AKIAIOSFODNN7EXAMPLE/20110909/'
                    'us-east-1/iam/aws4_request,'
                    'SignedHeaders=content-type;host;x-amz-date,')
        headers = {'Content-type':
                   'application/x-www-form-urlencoded; charset=utf-8',
                   'X-Amz-Date': '20110909T233600Z',
                   'Host': 'foo:8000',
                   'Authorization': auth_str,
                   'User-Agent': 'Boto/2.9.2 (linux2)'}
        # Note the example in the AWS docs is inconsistent, previous
        # examples specify no query string, but the final POST example
        # does, apparently incorrectly since an empty parameter list
        # aligns all steps and the final signature with the examples
        params = {}
        credentials = {'host': 'foo:8000',
                       'verb': 'POST',
                       'path': '/',
                       'params': params,
                       'headers': headers,
                       'body_hash': body_hash}
        signature = signer.generate(credentials)

        expected = ('9a4b2276a5039ada3b90f72ea8ec1745'
                    '14b92b909fb106b22ad910c5d75a54f4')
        self.assertEqual(expected, signature)

    def test_generate_v4_port_nostrip(self):
        """Test v4 generator with host:port format, but for an new
        (>=2.9.3) version of boto, where the port should not be stripped.
        """
        # Create a new signer object with the AWS example key
        secret = 'wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY'
        signer = utils.Ec2Signer(secret)

        body_hash = ('b6359072c78d70ebee1e81adcbab4f0'
                     '1bf2c23245fa365ef83fe8f1f955085e2')
        auth_str = ('AWS4-HMAC-SHA256 '
                    'Credential=AKIAIOSFODNN7EXAMPLE/20110909/'
                    'us-east-1/iam/aws4_request,'
                    'SignedHeaders=content-type;host;x-amz-date,')
        headers = {'Content-type':
                   'application/x-www-form-urlencoded; charset=utf-8',
                   'X-Amz-Date': '20110909T233600Z',
                   'Host': 'foo:8000',
                   'Authorization': auth_str,
                   'User-Agent': 'Boto/2.9.3 (linux2)'}
        # Note the example in the AWS docs is inconsistent, previous
        # examples specify no query string, but the final POST example
        # does, apparently incorrectly since an empty parameter list
        # aligns all steps and the final signature with the examples
        params = {}
        credentials = {'host': 'foo:8000',
                       'verb': 'POST',
                       'path': '/',
                       'params': params,
                       'headers': headers,
                       'body_hash': body_hash}
        signature = signer.generate(credentials)

        expected = ('26dd92ea79aaa49f533d13b1055acdc'
                    'd7d7321460d64621f96cc79c4f4d4ab2b')
        self.assertEqual(expected, signature)
