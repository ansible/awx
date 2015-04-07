# Copyright 2013 OpenStack Foundation
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

import os

import fixtures
from oslo_serialization import jsonutils
from oslo_utils import timeutils
import six
import testresources

from keystoneclient.common import cms
from keystoneclient import utils


TESTDIR = os.path.dirname(os.path.abspath(__file__))
ROOTDIR = os.path.normpath(os.path.join(TESTDIR, '..', '..', '..'))
CERTDIR = os.path.join(ROOTDIR, 'examples', 'pki', 'certs')
CMSDIR = os.path.join(ROOTDIR, 'examples', 'pki', 'cms')
KEYDIR = os.path.join(ROOTDIR, 'examples', 'pki', 'private')


def _hash_signed_token_safe(signed_text, **kwargs):
    if isinstance(signed_text, six.text_type):
        signed_text = signed_text.encode('utf-8')
    return utils.hash_signed_token(signed_text, **kwargs)


class Examples(fixtures.Fixture):
    """Example tokens and certs loaded from the examples directory.

    To use this class correctly, the module needs to override the test suite
    class to use testresources.OptimisingTestSuite (otherwise the files will
    be read on every test). This is done by defining a load_tests function
    in the module, like this:

    def load_tests(loader, tests, pattern):
        return testresources.OptimisingTestSuite(tests)

    (see http://docs.python.org/2/library/unittest.html#load-tests-protocol )

    """

    def setUp(self):
        super(Examples, self).setUp()

        # The data for several tests are signed using openssl and are stored in
        # files in the signing subdirectory.  In order to keep the values
        # consistent between the tests and the signed documents, we read them
        # in for use in the tests.
        with open(os.path.join(CMSDIR, 'auth_token_scoped.json')) as f:
            self.TOKEN_SCOPED_DATA = cms.cms_to_token(f.read())

        with open(os.path.join(CMSDIR, 'auth_token_scoped.pem')) as f:
            self.SIGNED_TOKEN_SCOPED = cms.cms_to_token(f.read())
        self.SIGNED_TOKEN_SCOPED_HASH = _hash_signed_token_safe(
            self.SIGNED_TOKEN_SCOPED)
        self.SIGNED_TOKEN_SCOPED_HASH_SHA256 = _hash_signed_token_safe(
            self.SIGNED_TOKEN_SCOPED, mode='sha256')
        with open(os.path.join(CMSDIR, 'auth_token_unscoped.pem')) as f:
            self.SIGNED_TOKEN_UNSCOPED = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_v3_token_scoped.pem')) as f:
            self.SIGNED_v3_TOKEN_SCOPED = cms.cms_to_token(f.read())
        self.SIGNED_v3_TOKEN_SCOPED_HASH = _hash_signed_token_safe(
            self.SIGNED_v3_TOKEN_SCOPED)
        self.SIGNED_v3_TOKEN_SCOPED_HASH_SHA256 = _hash_signed_token_safe(
            self.SIGNED_v3_TOKEN_SCOPED, mode='sha256')
        with open(os.path.join(CMSDIR, 'auth_token_revoked.pem')) as f:
            self.REVOKED_TOKEN = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_token_scoped_expired.pem')) as f:
            self.SIGNED_TOKEN_SCOPED_EXPIRED = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_v3_token_revoked.pem')) as f:
            self.REVOKED_v3_TOKEN = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_token_scoped.pkiz')) as f:
            self.SIGNED_TOKEN_SCOPED_PKIZ = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_token_unscoped.pkiz')) as f:
            self.SIGNED_TOKEN_UNSCOPED_PKIZ = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_v3_token_scoped.pkiz')) as f:
            self.SIGNED_v3_TOKEN_SCOPED_PKIZ = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_token_revoked.pkiz')) as f:
            self.REVOKED_TOKEN_PKIZ = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR,
                               'auth_token_scoped_expired.pkiz')) as f:
            self.SIGNED_TOKEN_SCOPED_EXPIRED_PKIZ = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'auth_v3_token_revoked.pkiz')) as f:
            self.REVOKED_v3_TOKEN_PKIZ = cms.cms_to_token(f.read())
        with open(os.path.join(CMSDIR, 'revocation_list.json')) as f:
            self.REVOCATION_LIST = jsonutils.loads(f.read())
        with open(os.path.join(CMSDIR, 'revocation_list.pem')) as f:
            self.SIGNED_REVOCATION_LIST = jsonutils.dumps({'signed': f.read()})

        self.SIGNING_CERT_FILE = os.path.join(CERTDIR, 'signing_cert.pem')
        with open(self.SIGNING_CERT_FILE) as f:
            self.SIGNING_CERT = f.read()

        self.KERBEROS_BIND = 'USER@REALM'

        self.SIGNING_KEY_FILE = os.path.join(KEYDIR, 'signing_key.pem')
        with open(self.SIGNING_KEY_FILE) as f:
            self.SIGNING_KEY = f.read()

        self.SIGNING_CA_FILE = os.path.join(CERTDIR, 'cacert.pem')
        with open(self.SIGNING_CA_FILE) as f:
            self.SIGNING_CA = f.read()

        self.UUID_TOKEN_DEFAULT = "ec6c0710ec2f471498484c1b53ab4f9d"
        self.UUID_TOKEN_NO_SERVICE_CATALOG = '8286720fbe4941e69fa8241723bb02df'
        self.UUID_TOKEN_UNSCOPED = '731f903721c14827be7b2dc912af7776'
        self.UUID_TOKEN_BIND = '3fc54048ad64405c98225ce0897af7c5'
        self.UUID_TOKEN_UNKNOWN_BIND = '8885fdf4d42e4fb9879e6379fa1eaf48'
        self.VALID_DIABLO_TOKEN = 'b0cf19b55dbb4f20a6ee18e6c6cf1726'
        self.v3_UUID_TOKEN_DEFAULT = '5603457654b346fdbb93437bfe76f2f1'
        self.v3_UUID_TOKEN_UNSCOPED = 'd34835fdaec447e695a0a024d84f8d79'
        self.v3_UUID_TOKEN_DOMAIN_SCOPED = 'e8a7b63aaa4449f38f0c5c05c3581792'
        self.v3_UUID_TOKEN_BIND = '2f61f73e1c854cbb9534c487f9bd63c2'
        self.v3_UUID_TOKEN_UNKNOWN_BIND = '7ed9781b62cd4880b8d8c6788ab1d1e2'

        revoked_token = self.REVOKED_TOKEN
        if isinstance(revoked_token, six.text_type):
            revoked_token = revoked_token.encode('utf-8')
        self.REVOKED_TOKEN_HASH = utils.hash_signed_token(revoked_token)
        self.REVOKED_TOKEN_HASH_SHA256 = utils.hash_signed_token(revoked_token,
                                                                 mode='sha256')
        self.REVOKED_TOKEN_LIST = (
            {'revoked': [{'id': self.REVOKED_TOKEN_HASH,
                          'expires': timeutils.utcnow()}]})
        self.REVOKED_TOKEN_LIST_JSON = jsonutils.dumps(self.REVOKED_TOKEN_LIST)

        revoked_v3_token = self.REVOKED_v3_TOKEN
        if isinstance(revoked_v3_token, six.text_type):
            revoked_v3_token = revoked_v3_token.encode('utf-8')
        self.REVOKED_v3_TOKEN_HASH = utils.hash_signed_token(revoked_v3_token)
        hash = utils.hash_signed_token(revoked_v3_token, mode='sha256')
        self.REVOKED_v3_TOKEN_HASH_SHA256 = hash
        self.REVOKED_v3_TOKEN_LIST = (
            {'revoked': [{'id': self.REVOKED_v3_TOKEN_HASH,
                          'expires': timeutils.utcnow()}]})
        self.REVOKED_v3_TOKEN_LIST_JSON = jsonutils.dumps(
            self.REVOKED_v3_TOKEN_LIST)

        revoked_token_pkiz = self.REVOKED_TOKEN_PKIZ
        if isinstance(revoked_token_pkiz, six.text_type):
            revoked_token_pkiz = revoked_token_pkiz.encode('utf-8')
        self.REVOKED_TOKEN_PKIZ_HASH = utils.hash_signed_token(
            revoked_token_pkiz)
        revoked_v3_token_pkiz = self.REVOKED_v3_TOKEN_PKIZ
        if isinstance(revoked_v3_token_pkiz, six.text_type):
            revoked_v3_token_pkiz = revoked_v3_token_pkiz.encode('utf-8')
        self.REVOKED_v3_PKIZ_TOKEN_HASH = utils.hash_signed_token(
            revoked_v3_token_pkiz)

        self.REVOKED_TOKEN_PKIZ_LIST = (
            {'revoked': [{'id': self.REVOKED_TOKEN_PKIZ_HASH,
                          'expires': timeutils.utcnow()},
                         {'id': self.REVOKED_v3_PKIZ_TOKEN_HASH,
                          'expires': timeutils.utcnow()},
                         ]})
        self.REVOKED_TOKEN_PKIZ_LIST_JSON = jsonutils.dumps(
            self.REVOKED_TOKEN_PKIZ_LIST)

        self.SIGNED_TOKEN_SCOPED_KEY = cms.cms_hash_token(
            self.SIGNED_TOKEN_SCOPED)
        self.SIGNED_TOKEN_UNSCOPED_KEY = cms.cms_hash_token(
            self.SIGNED_TOKEN_UNSCOPED)
        self.SIGNED_v3_TOKEN_SCOPED_KEY = cms.cms_hash_token(
            self.SIGNED_v3_TOKEN_SCOPED)

        self.SIGNED_TOKEN_SCOPED_PKIZ_KEY = cms.cms_hash_token(
            self.SIGNED_TOKEN_SCOPED_PKIZ)
        self.SIGNED_TOKEN_UNSCOPED_PKIZ_KEY = cms.cms_hash_token(
            self.SIGNED_TOKEN_UNSCOPED_PKIZ)
        self.SIGNED_v3_TOKEN_SCOPED_PKIZ_KEY = cms.cms_hash_token(
            self.SIGNED_v3_TOKEN_SCOPED_PKIZ)

        self.INVALID_SIGNED_TOKEN = (
            "MIIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
            "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"
            "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
            "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
            "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "1111111111111111111111111111111111111111111111111111111111111111"
            "2222222222222222222222222222222222222222222222222222222222222222"
            "3333333333333333333333333333333333333333333333333333333333333333"
            "4444444444444444444444444444444444444444444444444444444444444444"
            "5555555555555555555555555555555555555555555555555555555555555555"
            "6666666666666666666666666666666666666666666666666666666666666666"
            "7777777777777777777777777777777777777777777777777777777777777777"
            "8888888888888888888888888888888888888888888888888888888888888888"
            "9999999999999999999999999999999999999999999999999999999999999999"
            "0000000000000000000000000000000000000000000000000000000000000000")

        self.INVALID_SIGNED_PKIZ_TOKEN = (
            "PKIZ_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
            "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"
            "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
            "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
            "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
            "0000000000000000000000000000000000000000000000000000000000000000"
            "1111111111111111111111111111111111111111111111111111111111111111"
            "2222222222222222222222222222222222222222222222222222222222222222"
            "3333333333333333333333333333333333333333333333333333333333333333"
            "4444444444444444444444444444444444444444444444444444444444444444"
            "5555555555555555555555555555555555555555555555555555555555555555"
            "6666666666666666666666666666666666666666666666666666666666666666"
            "7777777777777777777777777777777777777777777777777777777777777777"
            "8888888888888888888888888888888888888888888888888888888888888888"
            "9999999999999999999999999999999999999999999999999999999999999999"
            "0000000000000000000000000000000000000000000000000000000000000000")

        # JSON responses keyed by token ID
        self.TOKEN_RESPONSES = {
            self.UUID_TOKEN_DEFAULT: {
                'access': {
                    'token': {
                        'id': self.UUID_TOKEN_DEFAULT,
                        'expires': '2020-01-01T00:00:10.000123Z',
                        'tenant': {
                            'id': 'tenant_id1',
                            'name': 'tenant_name1',
                        },
                    },
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'roles': [
                            {'name': 'role1'},
                            {'name': 'role2'},
                        ],
                    },
                    'serviceCatalog': {}
                },
            },
            self.VALID_DIABLO_TOKEN: {
                'access': {
                    'token': {
                        'id': self.VALID_DIABLO_TOKEN,
                        'expires': '2020-01-01T00:00:10.000123Z',
                        'tenantId': 'tenant_id1',
                    },
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'roles': [
                            {'name': 'role1'},
                            {'name': 'role2'},
                        ],
                    },
                },
            },
            self.UUID_TOKEN_UNSCOPED: {
                'access': {
                    'token': {
                        'id': self.UUID_TOKEN_UNSCOPED,
                        'expires': '2020-01-01T00:00:10.000123Z',
                    },
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'roles': [
                            {'name': 'role1'},
                            {'name': 'role2'},
                        ],
                    },
                },
            },
            self.UUID_TOKEN_NO_SERVICE_CATALOG: {
                'access': {
                    'token': {
                        'id': 'valid-token',
                        'expires': '2020-01-01T00:00:10.000123Z',
                        'tenant': {
                            'id': 'tenant_id1',
                            'name': 'tenant_name1',
                        },
                    },
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'roles': [
                            {'name': 'role1'},
                            {'name': 'role2'},
                        ],
                    }
                },
            },
            self.UUID_TOKEN_BIND: {
                'access': {
                    'token': {
                        'bind': {'kerberos': self.KERBEROS_BIND},
                        'id': self.UUID_TOKEN_BIND,
                        'expires': '2020-01-01T00:00:10.000123Z',
                        'tenant': {
                            'id': 'tenant_id1',
                            'name': 'tenant_name1',
                        },
                    },
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'roles': [
                            {'name': 'role1'},
                            {'name': 'role2'},
                        ],
                    },
                    'serviceCatalog': {}
                },
            },
            self.UUID_TOKEN_UNKNOWN_BIND: {
                'access': {
                    'token': {
                        'bind': {'FOO': 'BAR'},
                        'id': self.UUID_TOKEN_UNKNOWN_BIND,
                        'expires': '2020-01-01T00:00:10.000123Z',
                        'tenant': {
                            'id': 'tenant_id1',
                            'name': 'tenant_name1',
                        },
                    },
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'roles': [
                            {'name': 'role1'},
                            {'name': 'role2'},
                        ],
                    },
                    'serviceCatalog': {}
                },
            },
            self.v3_UUID_TOKEN_DEFAULT: {
                'token': {
                    'expires_at': '2020-01-01T00:00:10.000123Z',
                    'methods': ['password'],
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'domain': {
                            'id': 'domain_id1',
                            'name': 'domain_name1'
                        }
                    },
                    'project': {
                        'id': 'tenant_id1',
                        'name': 'tenant_name1',
                        'domain': {
                            'id': 'domain_id1',
                            'name': 'domain_name1'
                        }
                    },
                    'roles': [
                        {'name': 'role1', 'id': 'Role1'},
                        {'name': 'role2', 'id': 'Role2'},
                    ],
                    'catalog': {}
                }
            },
            self.v3_UUID_TOKEN_UNSCOPED: {
                'token': {
                    'expires_at': '2020-01-01T00:00:10.000123Z',
                    'methods': ['password'],
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'domain': {
                            'id': 'domain_id1',
                            'name': 'domain_name1'
                        }
                    }
                }
            },
            self.v3_UUID_TOKEN_DOMAIN_SCOPED: {
                'token': {
                    'expires_at': '2020-01-01T00:00:10.000123Z',
                    'methods': ['password'],
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'domain': {
                            'id': 'domain_id1',
                            'name': 'domain_name1'
                        }
                    },
                    'domain': {
                        'id': 'domain_id1',
                        'name': 'domain_name1',
                    },
                    'roles': [
                        {'name': 'role1', 'id': 'Role1'},
                        {'name': 'role2', 'id': 'Role2'},
                    ],
                    'catalog': {}
                }
            },
            self.SIGNED_TOKEN_SCOPED_KEY: {
                'access': {
                    'token': {
                        'id': self.SIGNED_TOKEN_SCOPED_KEY,
                        'expires': '2020-01-01T00:00:10.000123Z',
                    },
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'tenantId': 'tenant_id1',
                        'tenantName': 'tenant_name1',
                        'roles': [
                            {'name': 'role1'},
                            {'name': 'role2'},
                        ],
                    },
                },
            },
            self.SIGNED_TOKEN_UNSCOPED_KEY: {
                'access': {
                    'token': {
                        'id': self.SIGNED_TOKEN_UNSCOPED_KEY,
                        'expires': '2020-01-01T00:00:10.000123Z',
                    },
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'roles': [
                            {'name': 'role1'},
                            {'name': 'role2'},
                        ],
                    },
                },
            },
            self.SIGNED_v3_TOKEN_SCOPED_KEY: {
                'token': {
                    'expires_at': '2020-01-01T00:00:10.000123Z',
                    'methods': ['password'],
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'domain': {
                            'id': 'domain_id1',
                            'name': 'domain_name1'
                        }
                    },
                    'project': {
                        'id': 'tenant_id1',
                        'name': 'tenant_name1',
                        'domain': {
                            'id': 'domain_id1',
                            'name': 'domain_name1'
                        }
                    },
                    'roles': [
                        {'name': 'role1'},
                        {'name': 'role2'}
                    ],
                    'catalog': {}
                }
            },
            self.v3_UUID_TOKEN_BIND: {
                'token': {
                    'bind': {'kerberos': self.KERBEROS_BIND},
                    'methods': ['password'],
                    'expires_at': '2020-01-01T00:00:10.000123Z',
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'domain': {
                            'id': 'domain_id1',
                            'name': 'domain_name1'
                        }
                    },
                    'project': {
                        'id': 'tenant_id1',
                        'name': 'tenant_name1',
                        'domain': {
                            'id': 'domain_id1',
                            'name': 'domain_name1'
                        }
                    },
                    'roles': [
                        {'name': 'role1', 'id': 'Role1'},
                        {'name': 'role2', 'id': 'Role2'},
                    ],
                    'catalog': {}
                }
            },
            self.v3_UUID_TOKEN_UNKNOWN_BIND: {
                'token': {
                    'bind': {'FOO': 'BAR'},
                    'expires_at': '2020-01-01T00:00:10.000123Z',
                    'methods': ['password'],
                    'user': {
                        'id': 'user_id1',
                        'name': 'user_name1',
                        'domain': {
                            'id': 'domain_id1',
                            'name': 'domain_name1'
                        }
                    },
                    'project': {
                        'id': 'tenant_id1',
                        'name': 'tenant_name1',
                        'domain': {
                            'id': 'domain_id1',
                            'name': 'domain_name1'
                        }
                    },
                    'roles': [
                        {'name': 'role1', 'id': 'Role1'},
                        {'name': 'role2', 'id': 'Role2'},
                    ],
                    'catalog': {}
                }
            },
        }
        self.TOKEN_RESPONSES[self.SIGNED_TOKEN_SCOPED_PKIZ_KEY] = (
            self.TOKEN_RESPONSES[self.SIGNED_TOKEN_SCOPED_KEY])
        self.TOKEN_RESPONSES[self.SIGNED_TOKEN_UNSCOPED_PKIZ_KEY] = (
            self.TOKEN_RESPONSES[self.SIGNED_TOKEN_UNSCOPED_KEY])
        self.TOKEN_RESPONSES[self.SIGNED_v3_TOKEN_SCOPED_PKIZ_KEY] = (
            self.TOKEN_RESPONSES[self.SIGNED_v3_TOKEN_SCOPED_KEY])

        self.JSON_TOKEN_RESPONSES = dict([(k, jsonutils.dumps(v)) for k, v in
                                          six.iteritems(self.TOKEN_RESPONSES)])


EXAMPLES_RESOURCE = testresources.FixtureResource(Examples())


class HackingCode(fixtures.Fixture):
    """A fixture to house the various code examples for the keystoneclient
    hacking style checks.
    """

    oslo_namespace_imports = {
        'code': """
            import oslo.utils
            import oslo_utils
            import oslo.utils.encodeutils
            import oslo_utils.encodeutils
            from oslo import utils
            from oslo.utils import encodeutils
            from oslo_utils import encodeutils

            import oslo.serialization
            import oslo_serialization
            import oslo.serialization.jsonutils
            import oslo_serialization.jsonutils
            from oslo import serialization
            from oslo.serialization import jsonutils
            from oslo_serialization import jsonutils

            import oslo.config
            import oslo_config
            import oslo.config.cfg
            import oslo_config.cfg
            from oslo import config
            from oslo.config import cfg
            from oslo_config import cfg

            import oslo.i18n
            import oslo_i18n
            import oslo.i18n.log
            import oslo_i18n.log
            from oslo import i18n
            from oslo.i18n import log
            from oslo_i18n import log
        """,
        'expected_errors': [
            (1, 0, 'K333'),
            (3, 0, 'K333'),
            (5, 0, 'K333'),
            (6, 0, 'K333'),
            (9, 0, 'K333'),
            (11, 0, 'K333'),
            (13, 0, 'K333'),
            (14, 0, 'K333'),
            (17, 0, 'K333'),
            (19, 0, 'K333'),
            (21, 0, 'K333'),
            (22, 0, 'K333'),
            (25, 0, 'K333'),
            (27, 0, 'K333'),
            (29, 0, 'K333'),
            (30, 0, 'K333'),
        ],
    }
