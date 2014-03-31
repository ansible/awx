# coding: utf-8

# Copyright (c) 2009, Peter Sagerson
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from copy import deepcopy
import logging
import pickle

import ldap
try:
    import mockldap
except ImportError:
    mockldap = None

from django.conf import settings
import django.db.models.signals
from django.contrib.auth.models import User, Permission, Group
from django.test import TestCase
from django.utils import unittest
try:
    from django.test.utils import override_settings
except ImportError:
    override_settings = lambda *args, **kwargs: (lambda v: v)

from django_auth_ldap.models import TestUser, TestProfile
from django_auth_ldap import backend
from django_auth_ldap.config import LDAPSearch, LDAPSearchUnion
from django_auth_ldap.config import PosixGroupType, MemberDNGroupType, NestedMemberDNGroupType
from django_auth_ldap.config import GroupOfNamesType


class TestSettings(backend.LDAPSettings):
    """
    A replacement for backend.LDAPSettings that does not load settings
    from django.conf.
    """
    def __init__(self, **kwargs):
        for name, default in self.defaults.iteritems():
            value = kwargs.get(name, default)
            setattr(self, name, value)


class LDAPTest(TestCase):
    top = ("o=test", {"o": "test"})
    people = ("ou=people,o=test", {"ou": "people"})
    groups = ("ou=groups,o=test", {"ou": "groups"})
    moregroups = ("ou=moregroups,o=test", {"ou": "moregroups"})

    alice = ("uid=alice,ou=people,o=test", {
        "uid": ["alice"],
        "objectClass": ["person", "organizationalPerson", "inetOrgPerson", "posixAccount"],
        "userPassword": ["password"],
        "uidNumber": ["1000"],
        "gidNumber": ["1000"],
        "givenName": ["Alice"],
        "sn": ["Adams"]
    })
    bob = ("uid=bob,ou=people,o=test", {
        "uid": ["bob"],
        "objectClass": ["person", "organizationalPerson", "inetOrgPerson", "posixAccount"],
        "userPassword": ["password"],
        "uidNumber": ["1001"],
        "gidNumber": ["50"],
        "givenName": ["Robert"],
        "sn": ["Barker"]
    })
    dressler = (u"uid=dreßler,ou=people,o=test".encode('utf-8'), {
        "uid": [u"dreßler".encode('utf-8')],
        "objectClass": ["person", "organizationalPerson", "inetOrgPerson", "posixAccount"],
        "userPassword": ["password"],
        "uidNumber": ["1002"],
        "gidNumber": ["50"],
        "givenName": ["Wolfgang"],
        "sn": [u"Dreßler".encode('utf-8')]
    })
    nobody = ("uid=nobody,ou=people,o=test", {
        "uid": ["nobody"],
        "objectClass": ["person", "organizationalPerson", "inetOrgPerson", "posixAccount"],
        "userPassword": ["password"],
        "binaryAttr": ["\xb2"]  # Invalid UTF-8
    })

    # posixGroup objects
    active_px = ("cn=active_px,ou=groups,o=test", {
        "cn": ["active_px"],
        "objectClass": ["posixGroup"],
        "gidNumber": ["1000"],
        "memberUid": [],
    })
    staff_px = ("cn=staff_px,ou=groups,o=test", {
        "cn": ["staff_px"],
        "objectClass": ["posixGroup"],
        "gidNumber": ["1001"],
        "memberUid": ["alice"],
    })
    superuser_px = ("cn=superuser_px,ou=groups,o=test", {
        "cn": ["superuser_px"],
        "objectClass": ["posixGroup"],
        "gidNumber": ["1002"],
        "memberUid": ["alice"],
    })

    # groupOfNames groups
    empty_gon = ("cn=empty_gon,ou=groups,o=test", {
        "cn": ["empty_gon"],
        "objectClass": ["groupOfNames"],
        "member": []
    })
    active_gon = ("cn=active_gon,ou=groups,o=test", {
        "cn": ["active_gon"],
        "objectClass": ["groupOfNames"],
        "member": ["uid=alice,ou=people,o=test"]
    })
    staff_gon = ("cn=staff_gon,ou=groups,o=test", {
        "cn": ["staff_gon"],
        "objectClass": ["groupOfNames"],
        "member": ["uid=alice,ou=people,o=test"]
    })
    superuser_gon = ("cn=superuser_gon,ou=groups,o=test", {
        "cn": ["superuser_gon"],
        "objectClass": ["groupOfNames"],
        "member": ["uid=alice,ou=people,o=test"]
    })
    other_gon = ("cn=other_gon,ou=moregroups,o=test", {
        "cn": ["other_gon"],
        "objectClass": ["groupOfNames"],
        "member": ["uid=bob,ou=people,o=test"]
    })

    # Nested groups with a circular reference
    parent_gon = ("cn=parent_gon,ou=groups,o=test", {
        "cn": ["parent_gon"],
        "objectClass": ["groupOfNames"],
        "member": ["cn=nested_gon,ou=groups,o=test"]
    })
    nested_gon = ("CN=nested_gon,ou=groups,o=test", {
        "cn": ["nested_gon"],
        "objectClass": ["groupOfNames"],
        "member": [
            "uid=alice,ou=people,o=test",
            "cn=circular_gon,ou=groups,o=test"
        ]
    })
    circular_gon = ("cn=circular_gon,ou=groups,o=test", {
        "cn": ["circular_gon"],
        "objectClass": ["groupOfNames"],
        "member": ["cn=parent_gon,ou=groups,o=test"]
    })

    directory = dict([top, people, groups, moregroups, alice, bob, dressler,
                      nobody, active_px, staff_px, superuser_px, empty_gon,
                      active_gon, staff_gon, superuser_gon, other_gon,
                      parent_gon, nested_gon, circular_gon])

    @classmethod
    def configure_logger(cls):
        logger = logging.getLogger('django_auth_ldap')
        formatter = logging.Formatter("LDAP auth - %(levelname)s - %(message)s")
        handler = logging.StreamHandler()

        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.setLevel(logging.CRITICAL)

    @classmethod
    def setUpClass(cls):
        cls.configure_logger()
        cls.mockldap = mockldap.MockLdap(cls.directory)

    @classmethod
    def tearDownClass(cls):
        del cls.mockldap

    def setUp(self):
        self.mockldap.start()
        self.ldapobj = self.mockldap['ldap://localhost']

        self.backend = backend.LDAPBackend()
        self.backend.ldap  # Force global configuration

    def tearDown(self):
        self.mockldap.stop()
        del self.ldapobj

    def test_options(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            CONNECTION_OPTIONS={'opt1': 'value1'}
        )
        self.backend.authenticate(username='alice', password='password')

        self.assertEqual(self.ldapobj.get_option('opt1'), 'value1')

    def test_callable_server_uri(self):
        self._init_settings(
            SERVER_URI=lambda: 'ldap://ldap.example.com',
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )

        self.backend.authenticate(username='alice', password='password')

        ldapobj = self.mockldap['ldap://ldap.example.com']
        self.assertEqual(
            ldapobj.methods_called(with_args=True),
            [('initialize', ('ldap://ldap.example.com',), {}),
             ('simple_bind_s', ('uid=alice,ou=people,o=test', 'password'), {})]
        )

    def test_simple_bind(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )
        user_count = User.objects.count()

        user = self.backend.authenticate(username='alice', password='password')

        self.assertTrue(not user.has_usable_password())
        self.assertEqual(user.username, 'alice')
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s']
        )

    def test_new_user_lowercase(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )
        user_count = User.objects.count()

        user = self.backend.authenticate(username='Alice', password='password')

        self.assertTrue(not user.has_usable_password())
        self.assertEqual(user.username, 'alice')
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s']
        )

    def test_deepcopy(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )

        user = self.backend.authenticate(username='Alice', password='password')
        user = deepcopy(user)

    @override_settings(AUTH_USER_MODEL='django_auth_ldap.TestUser')
    def test_auth_custom_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
        )

        user = self.backend.authenticate(username='Alice', password='password')

        self.assertTrue(isinstance(user, TestUser))

    @override_settings(AUTH_USER_MODEL='django_auth_ldap.TestUser')
    def test_get_custom_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
        )

        user = self.backend.authenticate(username='Alice', password='password')
        user = self.backend.get_user(user.id)

        self.assertTrue(isinstance(user, TestUser))

    def test_new_user_whitespace(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )
        user_count = User.objects.count()

        user = self.backend.authenticate(username=' alice', password='password')
        user = self.backend.authenticate(username='alice ', password='password')

        self.assertTrue(not user.has_usable_password())
        self.assertEqual(user.username, 'alice')
        self.assertEqual(User.objects.count(), user_count + 1)

    def test_simple_bind_bad_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )
        user_count = User.objects.count()

        user = self.backend.authenticate(username='evil_alice', password='password')

        self.assertTrue(user is None)
        self.assertEqual(User.objects.count(), user_count)
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s']
        )

    def test_simple_bind_bad_password(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )
        user_count = User.objects.count()

        user = self.backend.authenticate(username='alice', password='bogus')

        self.assertTrue(user is None)
        self.assertEqual(User.objects.count(), user_count)
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s']
        )

    def test_existing_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )
        User.objects.create(username='alice')
        user_count = User.objects.count()

        user = self.backend.authenticate(username='alice', password='password')

        # Make sure we only created one user
        self.assertTrue(user is not None)
        self.assertEqual(User.objects.count(), user_count)

    def test_existing_user_insensitive(self):
        self._init_settings(
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", ldap.SCOPE_SUBTREE, '(uid=%(user)s)'
            )
        )
        # mockldap doesn't handle case-insensitive matching properly.
        self.ldapobj.search_s.seed('ou=people,o=test', ldap.SCOPE_SUBTREE,
                                   '(uid=Alice)')([self.alice])
        User.objects.create(username='alice')

        user = self.backend.authenticate(username='Alice', password='password')

        self.assertTrue(user is not None)
        self.assertEqual(user.username, 'alice')
        self.assertEqual(User.objects.count(), 1)

    def test_convert_username(self):
        class MyBackend(backend.LDAPBackend):
            def ldap_to_django_username(self, username):
                return 'ldap_%s' % username

            def django_to_ldap_username(self, username):
                return username[5:]

        self.backend = MyBackend()
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )
        user_count = User.objects.count()

        user1 = self.backend.authenticate(username='alice', password='password')
        user2 = self.backend.get_user(user1.pk)

        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertEqual(user1.username, 'ldap_alice')
        self.assertEqual(user1.ldap_user._username, 'alice')
        self.assertEqual(user1.ldap_username, 'alice')
        self.assertEqual(user2.username, 'ldap_alice')
        self.assertEqual(user2.ldap_user._username, 'alice')
        self.assertEqual(user2.ldap_username, 'alice')

    def test_search_bind(self):
        self._init_settings(
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", ldap.SCOPE_SUBTREE, '(uid=%(user)s)'
            )
        )
        user_count = User.objects.count()

        user = self.backend.authenticate(username='alice', password='password')

        self.assertTrue(user is not None)
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s', 'search_s', 'simple_bind_s']
        )

    def test_search_bind_no_user(self):
        self._init_settings(
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", ldap.SCOPE_SUBTREE, '(cn=%(user)s)'
            )
        )

        user = self.backend.authenticate(username='alice', password='password')

        self.assertTrue(user is None)
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s', 'search_s']
        )

    def test_search_bind_multiple_users(self):
        self._init_settings(
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", ldap.SCOPE_SUBTREE, '(uid=*)'
            )
        )

        user = self.backend.authenticate(username='alice', password='password')

        self.assertTrue(user is None)
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s', 'search_s']
        )

    def test_search_bind_bad_password(self):
        self._init_settings(
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", ldap.SCOPE_SUBTREE, '(uid=%(user)s)'
            )
        )

        user = self.backend.authenticate(username='alice', password='bogus')

        self.assertTrue(user is None)
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s', 'search_s', 'simple_bind_s']
        )

    def test_search_bind_with_credentials(self):
        self._init_settings(
            BIND_DN='uid=bob,ou=people,o=test',
            BIND_PASSWORD='password',
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", ldap.SCOPE_SUBTREE, '(uid=%(user)s)'
            )
        )

        user = self.backend.authenticate(username='alice', password='password')

        self.assertTrue(user is not None)
        self.assertTrue(user.ldap_user is not None)
        self.assertEqual(user.ldap_user.dn, self.alice[0])
        self.assertEqual(user.ldap_user.attrs, ldap.cidict.cidict(self.alice[1]))
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s', 'search_s', 'simple_bind_s']
        )

    def test_search_bind_with_bad_credentials(self):
        self._init_settings(
            BIND_DN='uid=bob,ou=people,o=test',
            BIND_PASSWORD='bogus',
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", ldap.SCOPE_SUBTREE, '(uid=%(user)s)'
            )
        )

        user = self.backend.authenticate(username='alice', password='password')

        self.assertTrue(user is None)
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s']
        )

    def test_unicode_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            USER_ATTR_MAP={'first_name': 'givenName', 'last_name': 'sn'}
        )

        user = self.backend.authenticate(username=u'dreßler', password='password')
        self.assertTrue(user is not None)
        self.assertEqual(user.username, u'dreßler')
        self.assertEqual(user.last_name, u'Dreßler')

    def test_cidict(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
        )

        user = self.backend.authenticate(username="alice", password="password")
        self.assertTrue(isinstance(user.ldap_user.attrs, ldap.cidict.cidict))

    def test_populate_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            USER_ATTR_MAP={'first_name': 'givenName', 'last_name': 'sn'}
        )

        user = self.backend.authenticate(username='alice', password='password')

        self.assertEqual(user.username, 'alice')
        self.assertEqual(user.first_name, 'Alice')
        self.assertEqual(user.last_name, 'Adams')

        # init, bind as user, bind anonymous, lookup user attrs
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s', 'simple_bind_s', 'search_s']
        )

    def test_bind_as_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            USER_ATTR_MAP={'first_name': 'givenName', 'last_name': 'sn'},
            BIND_AS_AUTHENTICATING_USER=True,
        )

        user = self.backend.authenticate(username='alice', password='password')

        self.assertEqual(user.username, 'alice')
        self.assertEqual(user.first_name, 'Alice')
        self.assertEqual(user.last_name, 'Adams')

        # init, bind as user, lookup user attrs
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s', 'search_s']
        )

    def test_signal_populate_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )

        def handle_populate_user(sender, **kwargs):
            self.assertTrue('user' in kwargs and 'ldap_user' in kwargs)
            kwargs['user'].populate_user_handled = True
        backend.populate_user.connect(handle_populate_user)

        user = self.backend.authenticate(username='alice', password='password')

        self.assertTrue(user.populate_user_handled)

    def test_signal_populate_user_profile(self):
        settings.AUTH_PROFILE_MODULE = 'django_auth_ldap.TestProfile'

        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )

        def handle_user_saved(sender, **kwargs):
            if kwargs['created']:
                TestProfile.objects.create(user=kwargs['instance'])

        def handle_populate_user_profile(sender, **kwargs):
            self.assertTrue('profile' in kwargs and 'ldap_user' in kwargs)
            kwargs['profile'].populated = True

        django.db.models.signals.post_save.connect(handle_user_saved, sender=User)
        backend.populate_user_profile.connect(handle_populate_user_profile)

        user = self.backend.authenticate(username='alice', password='password')

        self.assertTrue(user.get_profile().populated)

    def test_no_update_existing(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            USER_ATTR_MAP={'first_name': 'givenName', 'last_name': 'sn'},
            ALWAYS_UPDATE_USER=False
        )
        User.objects.create(username='alice', first_name='Alicia', last_name='Astro')

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assertEqual(alice.first_name, 'Alicia')
        self.assertEqual(alice.last_name, 'Astro')
        self.assertEqual(bob.first_name, 'Robert')
        self.assertEqual(bob.last_name, 'Barker')

    def test_require_group(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE, '(objectClass=groupOfNames)'),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            REQUIRE_GROUP="cn=active_gon,ou=groups,o=test"
        )

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assertTrue(alice is not None)
        self.assertTrue(bob is None)
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s', 'simple_bind_s', 'compare_s',
             'initialize', 'simple_bind_s', 'simple_bind_s', 'compare_s']
        )

    def test_group_union(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearchUnion(
                LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE, '(objectClass=groupOfNames)'),
                LDAPSearch('ou=moregroups,o=test', ldap.SCOPE_SUBTREE, '(objectClass=groupOfNames)')
            ),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            REQUIRE_GROUP="cn=other_gon,ou=moregroups,o=test"
        )

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assertTrue(alice is None)
        self.assertTrue(bob is not None)
        self.assertEqual(bob.ldap_user.group_names, set(['other_gon']))

    def test_nested_group_union(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearchUnion(
                LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE, '(objectClass=groupOfNames)'),
                LDAPSearch('ou=moregroups,o=test', ldap.SCOPE_SUBTREE, '(objectClass=groupOfNames)')
            ),
            GROUP_TYPE=NestedMemberDNGroupType(member_attr='member'),
            REQUIRE_GROUP="cn=other_gon,ou=moregroups,o=test"
        )

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assertTrue(alice is None)
        self.assertTrue(bob is not None)
        self.assertEqual(bob.ldap_user.group_names, set(['other_gon']))

    def test_denied_group(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            DENY_GROUP="cn=active_gon,ou=groups,o=test"
        )

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assertTrue(alice is None)
        self.assertTrue(bob is not None)
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s', 'simple_bind_s', 'compare_s',
             'initialize', 'simple_bind_s', 'simple_bind_s', 'compare_s']
        )

    def test_group_dns(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
        )
        alice = self.backend.authenticate(username='alice', password='password')

        self.assertEqual(alice.ldap_user.group_dns, set((g[0].lower() for g in [self.active_gon, self.staff_gon, self.superuser_gon, self.nested_gon])))

    def test_group_names(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
        )
        alice = self.backend.authenticate(username='alice', password='password')

        self.assertEqual(alice.ldap_user.group_names, set(['active_gon', 'staff_gon', 'superuser_gon', 'nested_gon']))

    def test_dn_group_membership(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            USER_FLAGS_BY_GROUP={
                'is_active': "cn=active_gon,ou=groups,o=test",
                'is_staff': ["cn=empty_gon,ou=groups,o=test",
                             "cn=staff_gon,ou=groups,o=test"],
                'is_superuser': "cn=superuser_gon,ou=groups,o=test"
            }
        )

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assertTrue(alice.is_active)
        self.assertTrue(alice.is_staff)
        self.assertTrue(alice.is_superuser)
        self.assertTrue(not bob.is_active)
        self.assertTrue(not bob.is_staff)
        self.assertTrue(not bob.is_superuser)

    def test_posix_membership(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=PosixGroupType(),
            USER_FLAGS_BY_GROUP={
                'is_active': "cn=active_px,ou=groups,o=test",
                'is_staff': "cn=staff_px,ou=groups,o=test",
                'is_superuser': "cn=superuser_px,ou=groups,o=test"
            }
        )

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assertTrue(alice.is_active)
        self.assertTrue(alice.is_staff)
        self.assertTrue(alice.is_superuser)
        self.assertTrue(not bob.is_active)
        self.assertTrue(not bob.is_staff)
        self.assertTrue(not bob.is_superuser)

    def test_nested_dn_group_membership(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=NestedMemberDNGroupType(member_attr='member'),
            USER_FLAGS_BY_GROUP={
                'is_active': "cn=parent_gon,ou=groups,o=test",
                'is_staff': "cn=parent_gon,ou=groups,o=test",
            }
        )
        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assertTrue(alice.is_active)
        self.assertTrue(alice.is_staff)
        self.assertTrue(not bob.is_active)
        self.assertTrue(not bob.is_staff)

    def test_posix_missing_attributes(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=PosixGroupType(),
            USER_FLAGS_BY_GROUP={
                'is_active': "cn=active_px,ou=groups,o=test"
            }
        )

        nobody = self.backend.authenticate(username='nobody', password='password')

        self.assertTrue(not nobody.is_active)

    def test_profile_flags(self):
        settings.AUTH_PROFILE_MODULE = 'django_auth_ldap.TestProfile'

        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            PROFILE_FLAGS_BY_GROUP={
                'is_special': ["cn=superuser_gon,ou=groups,o=test"]
            }
        )

        def handle_user_saved(sender, **kwargs):
            if kwargs['created']:
                TestProfile.objects.create(user=kwargs['instance'])

        django.db.models.signals.post_save.connect(handle_user_saved, sender=User)

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assertTrue(alice.get_profile().is_special)
        self.assertTrue(not bob.get_profile().is_special)

    def test_dn_group_permissions(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            FIND_GROUP_PERMS=True
        )
        self._init_groups()

        alice = User.objects.create(username='alice')
        alice = self.backend.get_user(alice.pk)

        self.assertEqual(self.backend.get_group_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assertEqual(self.backend.get_all_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assertTrue(self.backend.has_perm(alice, "auth.add_user"))
        self.assertTrue(self.backend.has_module_perms(alice, "auth"))

    def test_empty_group_permissions(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            FIND_GROUP_PERMS=True
        )
        self._init_groups()

        bob = User.objects.create(username='bob')
        bob = self.backend.get_user(bob.pk)

        self.assertEqual(self.backend.get_group_permissions(bob), set())
        self.assertEqual(self.backend.get_all_permissions(bob), set())
        self.assertTrue(not self.backend.has_perm(bob, "auth.add_user"))
        self.assertTrue(not self.backend.has_module_perms(bob, "auth"))

    def test_posix_group_permissions(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE,
                                    '(objectClass=posixGroup)'),
            GROUP_TYPE=PosixGroupType(),
            FIND_GROUP_PERMS=True
        )
        self._init_groups()

        alice = User.objects.create(username='alice')
        alice = self.backend.get_user(alice.pk)

        self.assertEqual(self.backend.get_group_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assertEqual(self.backend.get_all_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assertTrue(self.backend.has_perm(alice, "auth.add_user"))
        self.assertTrue(self.backend.has_module_perms(alice, "auth"))

    def test_posix_group_permissions_no_gid(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE,
                                    '(objectClass=posixGroup)'),
            GROUP_TYPE=PosixGroupType(),
            FIND_GROUP_PERMS=True
        )
        self._init_groups()
        self.ldapobj.modify_s(self.alice[0], [(ldap.MOD_DELETE, 'gidNumber', None)])
        self.ldapobj.modify_s(self.active_px[0], [(ldap.MOD_ADD, 'memberUid', ['alice'])])

        alice = User.objects.create(username='alice')
        alice = self.backend.get_user(alice.pk)

        self.assertEqual(self.backend.get_group_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assertEqual(self.backend.get_all_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assertTrue(self.backend.has_perm(alice, "auth.add_user"))
        self.assertTrue(self.backend.has_module_perms(alice, "auth"))

    def test_foreign_user_permissions(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            FIND_GROUP_PERMS=True
        )
        self._init_groups()

        alice = User.objects.create(username='alice')

        self.assertEqual(self.backend.get_group_permissions(alice), set())

    def test_group_cache(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            FIND_GROUP_PERMS=True,
            CACHE_GROUPS=True
        )
        self._init_groups()

        alice_id = User.objects.create(username='alice').pk
        bob_id = User.objects.create(username='bob').pk

        # Check permissions twice for each user
        for i in range(2):
            alice = self.backend.get_user(alice_id)
            self.assertEqual(
                self.backend.get_group_permissions(alice),
                set(["auth.add_user", "auth.change_user"])
            )

            bob = self.backend.get_user(bob_id)
            self.assertEqual(self.backend.get_group_permissions(bob), set())

        # Should have executed one LDAP search per user
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s', 'search_s',
             'initialize', 'simple_bind_s', 'search_s']
        )

    def test_group_mirroring(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE,
                                    '(objectClass=posixGroup)'),
            GROUP_TYPE=PosixGroupType(),
            MIRROR_GROUPS=True,
        )

        self.assertEqual(Group.objects.count(), 0)

        alice = self.backend.authenticate(username='alice', password='password')

        self.assertEqual(Group.objects.count(), 3)
        self.assertEqual(set(alice.groups.all()), set(Group.objects.all()))

    def test_nested_group_mirroring(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE,
                                    '(objectClass=groupOfNames)'),
            GROUP_TYPE=NestedMemberDNGroupType(member_attr='member'),
            MIRROR_GROUPS=True,
        )

        alice = self.backend.authenticate(username='alice', password='password')

        self.assertEqual(
            set(Group.objects.all().values_list('name', flat=True)),
            set(['active_gon', 'staff_gon', 'superuser_gon', 'nested_gon',
                 'parent_gon', 'circular_gon'])
        )
        self.assertEqual(set(alice.groups.all()), set(Group.objects.all()))

    def test_authorize_external_users(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            FIND_GROUP_PERMS=True,
            AUTHORIZE_ALL_USERS=True
        )
        self._init_groups()

        alice = User.objects.create(username='alice')

        self.assertEqual(self.backend.get_group_permissions(alice), set(["auth.add_user", "auth.change_user"]))

    def test_create_without_auth(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
        )

        alice = self.backend.populate_user('alice')
        bob = self.backend.populate_user('bob')

        self.assertTrue(alice is not None)
        self.assertEqual(alice.first_name, u"")
        self.assertEqual(alice.last_name, u"")
        self.assertTrue(alice.is_active)
        self.assertTrue(not alice.is_staff)
        self.assertTrue(not alice.is_superuser)
        self.assertTrue(bob is not None)
        self.assertEqual(bob.first_name, u"")
        self.assertEqual(bob.last_name, u"")
        self.assertTrue(bob.is_active)
        self.assertTrue(not bob.is_staff)
        self.assertTrue(not bob.is_superuser)

    def test_populate_without_auth(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            ALWAYS_UPDATE_USER=False,
            USER_ATTR_MAP={'first_name': 'givenName', 'last_name': 'sn'},
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=GroupOfNamesType(),
            USER_FLAGS_BY_GROUP={
                'is_active': "cn=active_gon,ou=groups,o=test",
                'is_staff': "cn=staff_gon,ou=groups,o=test",
                'is_superuser': "cn=superuser_gon,ou=groups,o=test"
            }
        )

        User.objects.create(username='alice')
        User.objects.create(username='bob')

        alice = self.backend.populate_user('alice')
        bob = self.backend.populate_user('bob')

        self.assertTrue(alice is not None)
        self.assertEqual(alice.first_name, u"Alice")
        self.assertEqual(alice.last_name, u"Adams")
        self.assertTrue(alice.is_active)
        self.assertTrue(alice.is_staff)
        self.assertTrue(alice.is_superuser)
        self.assertTrue(bob is not None)
        self.assertEqual(bob.first_name, u"Robert")
        self.assertEqual(bob.last_name, u"Barker")
        self.assertTrue(not bob.is_active)
        self.assertTrue(not bob.is_staff)
        self.assertTrue(not bob.is_superuser)

    def test_populate_bogus_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
        )

        bogus = self.backend.populate_user('bogus')

        self.assertEqual(bogus, None)

    def test_start_tls_missing(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            START_TLS=False,
        )

        self.assertTrue(not self.ldapobj.tls_enabled)
        self.backend.authenticate(username='alice', password='password')
        self.assertTrue(not self.ldapobj.tls_enabled)

    def test_start_tls(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            START_TLS=True,
        )

        self.assertTrue(not self.ldapobj.tls_enabled)
        self.backend.authenticate(username='alice', password='password')
        self.assertTrue(self.ldapobj.tls_enabled)

    def test_null_search_results(self):
        """
        Make sure we're not phased by referrals.
        """
        self._init_settings(
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", ldap.SCOPE_SUBTREE, '(uid=%(user)s)'
            )
        )
        self.backend.authenticate(username='alice', password='password')

    def test_union_search(self):
        self._init_settings(
            USER_SEARCH=LDAPSearchUnion(
                LDAPSearch("ou=groups,o=test", ldap.SCOPE_SUBTREE, '(uid=%(user)s)'),
                LDAPSearch("ou=people,o=test", ldap.SCOPE_SUBTREE, '(uid=%(user)s)'),
            )
        )
        alice = self.backend.authenticate(username='alice', password='password')

        self.assertTrue(alice is not None)

        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s', 'search', 'search', 'result',
             'result', 'simple_bind_s']
        )

    def test_deny_empty_password(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
        )

        alice = self.backend.authenticate(username=u'alice', password=u'')

        self.assertEqual(alice, None)
        self.assertEqual(self.ldapobj.methods_called(), [])

    def test_permit_empty_password(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            PERMIT_EMPTY_PASSWORD=True,
        )

        alice = self.backend.authenticate(username=u'alice', password=u'')

        self.assertEqual(alice, None)
        self.assertEqual(
            self.ldapobj.methods_called(),
            ['initialize', 'simple_bind_s']
        )

    def test_pickle(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            FIND_GROUP_PERMS=True
        )
        self._init_groups()

        alice0 = self.backend.authenticate(username=u'alice', password=u'password')

        pickled = pickle.dumps(alice0, pickle.HIGHEST_PROTOCOL)
        alice = pickle.loads(pickled)
        alice.ldap_user.backend.settings = alice0.ldap_user.backend.settings

        self.assertTrue(alice is not None)
        self.assertEqual(self.backend.get_group_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assertEqual(self.backend.get_all_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assertTrue(self.backend.has_perm(alice, "auth.add_user"))
        self.assertTrue(self.backend.has_module_perms(alice, "auth"))

    def _init_settings(self, **kwargs):
        self.backend.settings = TestSettings(**kwargs)

    def _init_groups(self):
        permissions = [
            Permission.objects.get(codename="add_user"),
            Permission.objects.get(codename="change_user")
        ]

        active_gon = Group.objects.create(name='active_gon')
        active_gon.permissions.add(*permissions)

        active_px = Group.objects.create(name='active_px')
        active_px.permissions.add(*permissions)


# Python 2.5-compatible class decoration
LDAPTest = unittest.skipIf(mockldap is None, "django_auth_ldap tests require the mockldap package.")(LDAPTest)
