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

try:
    set
except NameError:
    from sets import Set as set     # Python 2.3 fallback

from collections import defaultdict
from copy import deepcopy
import logging
import pickle
import sys

from django.conf import settings
import django.db.models.signals
from django.contrib.auth.models import User, Permission, Group
from django.test import TestCase

try:
    from django.test.utils import override_settings
except ImportError:
    override_settings = lambda *args, **kwargs: (lambda v: v)

from django_auth_ldap.models import TestUser, TestProfile
from django_auth_ldap import backend
from django_auth_ldap.config import _LDAPConfig, LDAPSearch, LDAPSearchUnion
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


class MockLDAP(object):
    """
    This is a stand-in for the python-ldap module; it serves as both the ldap
    module and the LDAPObject class. While it's temping to add some real LDAP
    capabilities here, this is designed to remain as simple as possible, so as
    to minimize the risk of creating bogus unit tests through a buggy test
    harness.

    Simple operations can be simulated, but for nontrivial searches, the client
    will have to seed the mock object with return values for expected API calls.
    This may sound like cheating, but it's really no more so than a simulated
    LDAP server. The fact is we can not require python-ldap to be installed in
    order to run the unit tests, so all we can do is verify that LDAPBackend is
    calling the APIs that we expect.

    set_return_value takes the name of an API, a tuple of arguments, and a
    return value. Every time an API is called, it looks for a predetermined
    return value based on the arguments received. If it finds one, then it
    returns it, or raises it if it's an Exception. If it doesn't find one, then
    it tries to satisfy the request internally. If it can't, it raises a
    PresetReturnRequiredError.

    At any time, the client may call ldap_methods_called_with_arguments() or
    ldap_methods_called() to get a record of all of the LDAP API calls that have
    been made, with or without arguments.
    """
    class PresetReturnRequiredError(Exception):
        pass

    SCOPE_BASE = 0
    SCOPE_ONELEVEL = 1
    SCOPE_SUBTREE = 2

    RES_SEARCH_RESULT = 101

    class LDAPError(Exception):
        pass

    class INVALID_CREDENTIALS(LDAPError):
        pass

    class NO_SUCH_OBJECT(LDAPError):
        pass

    class NO_SUCH_ATTRIBUTE(LDAPError):
        pass

    #
    # Submodules
    #
    class dn(object):
        def escape_dn_chars(s):
            return s
        escape_dn_chars = staticmethod(escape_dn_chars)

    class filter(object):
        def escape_filter_chars(s):
            return s
        escape_filter_chars = staticmethod(escape_filter_chars)

    class cidict(object):
        class cidict(dict):
            pass

    def __init__(self, directory):
        """
        directory is a complex structure with the entire contents of the
        mock LDAP directory. directory must be a dictionary mapping
        distinguished names to dictionaries of attributes. Each attribute
        dictionary maps attribute names to lists of values. e.g.:

        {
            "uid=alice,ou=users,dc=example,dc=com":
            {
                "uid": ["alice"],
                "userPassword": ["secret"],
            },
        }
        """
        self.directory = self.cidict.cidict(directory)

        self.reset()

    def reset(self):
        """
        Resets our recorded API calls and queued return values as well as
        miscellaneous configuration options.
        """
        self.calls = []
        self.return_value_maps = defaultdict(lambda: {})
        self.async_results = []
        self.options = {}
        self.tls_enabled = False

    def set_return_value(self, api_name, arguments, value):
        """
        Stores a preset return value for a given API with a given set of
        arguments.
        """
        self.return_value_maps[api_name][arguments] = value

    def ldap_methods_called_with_arguments(self):
        """
        Returns a list of 2-tuples, one for each API call made since the last
        reset. Each tuple contains the name of the API and a dictionary of
        arguments. Argument defaults are included.
        """
        return self.calls

    def ldap_methods_called(self):
        """
        Returns the list of API names called.
        """
        return [call[0] for call in self.calls]

    #
    # Begin LDAP methods
    #

    def set_option(self, option, invalue):
        self._record_call('set_option', {
            'option': option,
            'invalue': invalue
        })

        self.options[option] = invalue

    def initialize(self, uri, trace_level=0, trace_file=sys.stdout, trace_stack_limit=None):
        self._record_call('initialize', {
            'uri': uri,
            'trace_level': trace_level,
            'trace_file': trace_file,
            'trace_stack_limit': trace_stack_limit
        })

        value = self._get_return_value('initialize',
            (uri, trace_level, trace_file, trace_stack_limit))
        if value is None:
            value = self

        return value

    def simple_bind_s(self, who='', cred=''):
        self._record_call('simple_bind_s', {
            'who': who,
            'cred': cred
        })

        value = self._get_return_value('simple_bind_s', (who, cred))
        if value is None:
            value = self._simple_bind_s(who, cred)

        return value

    def search(self, base, scope, filterstr='(objectClass=*)', attrlist=None, attrsonly=0):
        self._record_call('search', {
            'base': base,
            'scope': scope,
            'filterstr': filterstr,
            'attrlist': attrlist,
            'attrsonly': attrsonly
        })

        value = self._get_return_value('search_s',
            (base, scope, filterstr, attrlist, attrsonly))
        if value is None:
            value = self._search_s(base, scope, filterstr, attrlist, attrsonly)

        return self._add_async_result(value)

    def result(self, msgid, all=1, timeout=None):
        self._record_call('result', {
            'msgid': msgid,
            'all': all,
            'timeout': timeout,
        })

        return self.RES_SEARCH_RESULT, self._pop_async_result(msgid)

    def search_s(self, base, scope, filterstr='(objectClass=*)', attrlist=None, attrsonly=0):
        self._record_call('search_s', {
            'base': base,
            'scope': scope,
            'filterstr': filterstr,
            'attrlist': attrlist,
            'attrsonly': attrsonly
        })

        value = self._get_return_value('search_s',
            (base, scope, filterstr, attrlist, attrsonly))
        if value is None:
            value = self._search_s(base, scope, filterstr, attrlist, attrsonly)

        return value

    def start_tls_s(self):
        self.tls_enabled = True

    def compare_s(self, dn, attr, value):
        self._record_call('compare_s', {
            'dn': dn,
            'attr': attr,
            'value': value
        })

        result = self._get_return_value('compare_s', (dn, attr, value))
        if result is None:
            result = self._compare_s(dn, attr, value)

        # print "compare_s('%s', '%s', '%s'): %d" % (dn, attr, value, result)

        return result

    #
    # Internal implementations
    #

    def _simple_bind_s(self, who='', cred=''):
        success = False

        if(who == '' and cred == ''):
            success = True
        elif self._compare_s(who.lower(), 'userPassword', cred):
            success = True

        if success:
            return (97, []) # python-ldap returns this; I don't know what it means
        else:
            raise self.INVALID_CREDENTIALS('%s:%s' % (who, cred))

    def _compare_s(self, dn, attr, value):
        if dn not in self.directory:
            raise self.NO_SUCH_OBJECT

        if attr not in self.directory[dn]:
            raise self.NO_SUCH_ATTRIBUTE

        return (value in self.directory[dn][attr]) and 1 or 0

    def _search_s(self, base, scope, filterstr, attrlist, attrsonly):
        """
        We can do a SCOPE_BASE search with the default filter. Beyond that,
        you're on your own.
        """
        if scope != self.SCOPE_BASE:
            raise self.PresetReturnRequiredError('search_s("%s", %d, "%s", "%s", %d)' %
                (base, scope, filterstr, attrlist, attrsonly))

        if filterstr != '(objectClass=*)':
            raise self.PresetReturnRequiredError('search_s("%s", %d, "%s", "%s", %d)' %
                (base, scope, filterstr, attrlist, attrsonly))

        attrs = self.directory.get(base)
        if attrs is None:
            raise self.NO_SUCH_OBJECT()

        return [(base, attrs)]

    def _add_async_result(self, value):
        self.async_results.append(value)

        return len(self.async_results) - 1

    def _pop_async_result(self, msgid):
        if msgid in xrange(len(self.async_results)):
            value = self.async_results[msgid]
            self.async_results[msgid] = None
        else:
            value = None

        return value

    #
    # Utils
    #

    def _record_call(self, api_name, arguments):
        self.calls.append((api_name, arguments))

    def _get_return_value(self, api_name, arguments):
        try:
            value = self.return_value_maps[api_name][arguments]
        except KeyError:
            value = None

        if isinstance(value, Exception):
            raise value

        return value


class LDAPTest(TestCase):
    # Following are the objecgs in our mock LDAP directory
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

    # groupOfUniqueName groups
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

    mock_ldap = MockLDAP({
        alice[0]: alice[1],
        bob[0]: bob[1],
        dressler[0]: dressler[1],
        nobody[0]: nobody[1],
        active_px[0]: active_px[1],
        staff_px[0]: staff_px[1],
        superuser_px[0]: superuser_px[1],
        active_gon[0]: active_gon[1],
        staff_gon[0]: staff_gon[1],
        superuser_gon[0]: superuser_gon[1],
        parent_gon[0]: parent_gon[1],
        nested_gon[0]: nested_gon[1],
        circular_gon[0]: circular_gon[1],
    })

    logging_configured = False

    def configure_logger(cls):
        if not cls.logging_configured:
            logger = logging.getLogger('django_auth_ldap')
            formatter = logging.Formatter("LDAP auth - %(levelname)s - %(message)s")
            handler = logging.StreamHandler()

            handler.setLevel(logging.DEBUG)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            logger.setLevel(logging.CRITICAL)

            cls.logging_configured = True
    configure_logger = classmethod(configure_logger)

    def setUp(self):
        self.configure_logger()

        self.ldap = _LDAPConfig.ldap = self.mock_ldap

        self.backend = backend.LDAPBackend()
        self.backend.ldap # Force global configuration

        self.mock_ldap.reset()

    def tearDown(self):
        pass

    def test_options(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            CONNECTION_OPTIONS={'opt1': 'value1'}
        )

        self.backend.authenticate(username='alice', password='password')

        self.assertEqual(self.mock_ldap.options, {'opt1': 'value1'})

    def test_simple_bind(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )
        user_count = User.objects.count()

        user = self.backend.authenticate(username='alice', password='password')

        self.assert_(not user.has_usable_password())
        self.assertEqual(user.username, 'alice')
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s'])

    def test_new_user_lowercase(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )
        user_count = User.objects.count()

        user = self.backend.authenticate(username='Alice', password='password')

        self.assert_(not user.has_usable_password())
        self.assertEqual(user.username, 'alice')
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s'])

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

        self.assert_(isinstance(user, TestUser))

    @override_settings(AUTH_USER_MODEL='django_auth_ldap.TestUser')
    def test_get_custom_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
        )

        user = self.backend.authenticate(username='Alice', password='password')
        user = self.backend.get_user(user.id)

        self.assert_(isinstance(user, TestUser))

    def test_new_user_whitespace(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )
        user_count = User.objects.count()

        user = self.backend.authenticate(username=' alice', password='password')
        user = self.backend.authenticate(username='alice ', password='password')

        self.assert_(not user.has_usable_password())
        self.assertEqual(user.username, 'alice')
        self.assertEqual(User.objects.count(), user_count + 1)

    def test_simple_bind_bad_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )
        user_count = User.objects.count()

        user = self.backend.authenticate(username='evil_alice', password='password')

        self.assert_(user is None)
        self.assertEqual(User.objects.count(), user_count)
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s'])

    def test_simple_bind_bad_password(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )
        user_count = User.objects.count()

        user = self.backend.authenticate(username='alice', password='bogus')

        self.assert_(user is None)
        self.assertEqual(User.objects.count(), user_count)
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s'])

    def test_existing_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )
        User.objects.create(username='alice')
        user_count = User.objects.count()

        user = self.backend.authenticate(username='alice', password='password')

        # Make sure we only created one user
        self.assert_(user is not None)
        self.assertEqual(User.objects.count(), user_count)

    def test_existing_user_insensitive(self):
        self._init_settings(
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", self.mock_ldap.SCOPE_SUBTREE, '(uid=%(user)s)'
            )
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=people,o=test", 2, "(uid=Alice)", None, 0), [self.alice])
        User.objects.create(username='alice')

        user = self.backend.authenticate(username='Alice', password='password')

        self.assert_(user is not None)
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
                "ou=people,o=test", self.mock_ldap.SCOPE_SUBTREE, '(uid=%(user)s)'
            )
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=people,o=test", 2, "(uid=alice)", None, 0), [self.alice])
        user_count = User.objects.count()

        user = self.backend.authenticate(username='alice', password='password')

        self.assert_(user is not None)
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s', 'search_s', 'simple_bind_s'])

    def test_search_bind_no_user(self):
        self._init_settings(
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", self.mock_ldap.SCOPE_SUBTREE, '(cn=%(user)s)'
            )
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=people,o=test", 2, "(cn=alice)", None, 0), [])

        user = self.backend.authenticate(username='alice', password='password')

        self.assert_(user is None)
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s', 'search_s'])

    def test_search_bind_multiple_users(self):
        self._init_settings(
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", self.mock_ldap.SCOPE_SUBTREE, '(uid=*)'
            )
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=people,o=test", 2, "(uid=*)", None, 0), [self.alice, self.bob])

        user = self.backend.authenticate(username='alice', password='password')

        self.assert_(user is None)
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s', 'search_s'])

    def test_search_bind_bad_password(self):
        self._init_settings(
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", self.mock_ldap.SCOPE_SUBTREE, '(uid=%(user)s)'
            )
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=people,o=test", 2, "(uid=alice)", None, 0), [self.alice])

        user = self.backend.authenticate(username='alice', password='bogus')

        self.assert_(user is None)
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s', 'search_s', 'simple_bind_s'])

    def test_search_bind_with_credentials(self):
        self._init_settings(
            BIND_DN='uid=bob,ou=people,o=test',
            BIND_PASSWORD='password',
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", self.mock_ldap.SCOPE_SUBTREE, '(uid=%(user)s)'
            )
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=people,o=test", 2, "(uid=alice)", None, 0), [self.alice])

        user = self.backend.authenticate(username='alice', password='password')

        self.assert_(user is not None)
        self.assert_(user.ldap_user is not None)
        self.assertEqual(user.ldap_user.dn, self.alice[0])
        self.assertEqual(user.ldap_user.attrs, self.alice[1])
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s', 'search_s', 'simple_bind_s'])

    def test_search_bind_with_bad_credentials(self):
        self._init_settings(
            BIND_DN='uid=bob,ou=people,o=test',
            BIND_PASSWORD='bogus',
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", self.mock_ldap.SCOPE_SUBTREE, '(uid=%(user)s)'
            )
        )

        user = self.backend.authenticate(username='alice', password='password')

        self.assert_(user is None)
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s'])

    def test_unicode_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            USER_ATTR_MAP={'first_name': 'givenName', 'last_name': 'sn'}
        )

        user = self.backend.authenticate(username=u'dreßler', password='password')

        self.assert_(user is not None)
        self.assertEqual(user.username, u'dreßler')
        self.assertEqual(user.last_name, u'Dreßler')

    def test_cidict(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
        )

        user = self.backend.authenticate(username="alice", password="password")

        self.assert_(isinstance(user.ldap_user.attrs, self.ldap.cidict.cidict))

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
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s', 'simple_bind_s', 'search_s'])

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
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s', 'search_s'])

    def test_signal_populate_user(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )

        def handle_populate_user(sender, **kwargs):
            self.assert_('user' in kwargs and 'ldap_user' in kwargs)
            kwargs['user'].populate_user_handled = True
        backend.populate_user.connect(handle_populate_user)

        user = self.backend.authenticate(username='alice', password='password')

        self.assert_(user.populate_user_handled)

    def test_signal_populate_user_profile(self):
        settings.AUTH_PROFILE_MODULE = 'django_auth_ldap.TestProfile'

        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test'
        )

        def handle_user_saved(sender, **kwargs):
            if kwargs['created']:
                TestProfile.objects.create(user=kwargs['instance'])

        def handle_populate_user_profile(sender, **kwargs):
            self.assert_('profile' in kwargs and 'ldap_user' in kwargs)
            kwargs['profile'].populated = True

        django.db.models.signals.post_save.connect(handle_user_saved, sender=User)
        backend.populate_user_profile.connect(handle_populate_user_profile)

        user = self.backend.authenticate(username='alice', password='password')

        self.assert_(user.get_profile().populated)

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
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            REQUIRE_GROUP="cn=active_gon,ou=groups,o=test"
        )

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assert_(alice is not None)
        self.assert_(bob is None)
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s', 'simple_bind_s', 'compare_s', 'initialize', 'simple_bind_s', 'simple_bind_s', 'compare_s'])

    def test_denied_group(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            DENY_GROUP="cn=active_gon,ou=groups,o=test"
        )

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assert_(alice is None)
        self.assert_(bob is not None)
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s', 'simple_bind_s', 'compare_s', 'initialize', 'simple_bind_s', 'simple_bind_s', 'compare_s'])

    def test_group_dns(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(member=uid=alice,ou=people,o=test))", None, 0),
            [self.active_gon, self.staff_gon, self.superuser_gon, self.nested_gon]
        )

        alice = self.backend.authenticate(username='alice', password='password')

        self.assertEqual(alice.ldap_user.group_dns, set((g[0].lower() for g in [self.active_gon, self.staff_gon, self.superuser_gon, self.nested_gon])))

    def test_group_names(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(member=uid=alice,ou=people,o=test))", None, 0),
            [self.active_gon, self.staff_gon, self.superuser_gon, self.nested_gon]
        )

        alice = self.backend.authenticate(username='alice', password='password')

        self.assertEqual(alice.ldap_user.group_names, set(['active_gon', 'staff_gon', 'superuser_gon', 'nested_gon']))

    def test_dn_group_membership(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            USER_FLAGS_BY_GROUP={
                'is_active': "cn=active_gon,ou=groups,o=test",
                'is_staff': "cn=staff_gon,ou=groups,o=test",
                'is_superuser': "cn=superuser_gon,ou=groups,o=test"
            }
        )

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assert_(alice.is_active)
        self.assert_(alice.is_staff)
        self.assert_(alice.is_superuser)
        self.assert_(not bob.is_active)
        self.assert_(not bob.is_staff)
        self.assert_(not bob.is_superuser)

    def test_posix_membership(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=PosixGroupType(),
            USER_FLAGS_BY_GROUP={
                'is_active': "cn=active_px,ou=groups,o=test",
                'is_staff': "cn=staff_px,ou=groups,o=test",
                'is_superuser': "cn=superuser_px,ou=groups,o=test"
            }
        )

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assert_(alice.is_active)
        self.assert_(alice.is_staff)
        self.assert_(alice.is_superuser)
        self.assert_(not bob.is_active)
        self.assert_(not bob.is_staff)
        self.assert_(not bob.is_superuser)

    def test_nested_dn_group_membership(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=NestedMemberDNGroupType(member_attr='member'),
            USER_FLAGS_BY_GROUP={
                'is_active': "cn=parent_gon,ou=groups,o=test",
                'is_staff': "cn=parent_gon,ou=groups,o=test",
            }
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(|(member=uid=alice,ou=people,o=test)))", None, 0),
            [self.active_gon, self.nested_gon]
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(|(member=cn=active_gon,ou=groups,o=test)(member=cn=nested_gon,ou=groups,o=test)))", None, 0),
            [self.parent_gon]
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(|(member=cn=parent_gon,ou=groups,o=test)))", None, 0),
            [self.circular_gon]
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(|(member=cn=circular_gon,ou=groups,o=test)))", None, 0),
            [self.nested_gon]
        )

        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(|(member=uid=bob,ou=people,o=test)))", None, 0),
            []
        )

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assert_(alice.is_active)
        self.assert_(alice.is_staff)
        self.assert_(not bob.is_active)
        self.assert_(not bob.is_staff)

    def test_posix_missing_attributes(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=PosixGroupType(),
            USER_FLAGS_BY_GROUP={
                'is_active': "cn=active_px,ou=groups,o=test"
            }
        )

        nobody = self.backend.authenticate(username='nobody', password='password')

        self.assert_(not nobody.is_active)

    def test_profile_flags(self):
        settings.AUTH_PROFILE_MODULE = 'django_auth_ldap.TestProfile'

        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            PROFILE_FLAGS_BY_GROUP={
                'is_special': "cn=superuser_gon,ou=groups,o=test"
            }
        )

        def handle_user_saved(sender, **kwargs):
            if kwargs['created']:
                TestProfile.objects.create(user=kwargs['instance'])

        django.db.models.signals.post_save.connect(handle_user_saved, sender=User)

        alice = self.backend.authenticate(username='alice', password='password')
        bob = self.backend.authenticate(username='bob', password='password')

        self.assert_(alice.get_profile().is_special)
        self.assert_(not bob.get_profile().is_special)

    def test_dn_group_permissions(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            FIND_GROUP_PERMS=True
        )
        self._init_groups()
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(member=uid=alice,ou=people,o=test))", None, 0),
            [self.active_gon, self.staff_gon, self.superuser_gon, self.nested_gon]
        )

        alice = User.objects.create(username='alice')
        alice = self.backend.get_user(alice.pk)

        self.assertEqual(self.backend.get_group_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assertEqual(self.backend.get_all_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assert_(self.backend.has_perm(alice, "auth.add_user"))
        self.assert_(self.backend.has_module_perms(alice, "auth"))

    def test_empty_group_permissions(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            FIND_GROUP_PERMS=True
        )
        self._init_groups()
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(member=uid=bob,ou=people,o=test))", None, 0),
            []
        )

        bob = User.objects.create(username='bob')
        bob = self.backend.get_user(bob.pk)

        self.assertEqual(self.backend.get_group_permissions(bob), set())
        self.assertEqual(self.backend.get_all_permissions(bob), set())
        self.assert_(not self.backend.has_perm(bob, "auth.add_user"))
        self.assert_(not self.backend.has_module_perms(bob, "auth"))

    def test_posix_group_permissions(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test',
                self.mock_ldap.SCOPE_SUBTREE, "(objectClass=posixGroup)"
            ),
            GROUP_TYPE=PosixGroupType(),
            FIND_GROUP_PERMS=True
        )
        self._init_groups()
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=posixGroup)(|(gidNumber=1000)(memberUid=alice)))", None, 0),
            [self.active_px, self.staff_px, self.superuser_px]
        )

        alice = User.objects.create(username='alice')
        alice = self.backend.get_user(alice.pk)

        self.assertEqual(self.backend.get_group_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assertEqual(self.backend.get_all_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assert_(self.backend.has_perm(alice, "auth.add_user"))
        self.assert_(self.backend.has_module_perms(alice, "auth"))

    def test_foreign_user_permissions(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            FIND_GROUP_PERMS=True
        )
        self._init_groups()

        alice = User.objects.create(username='alice')

        self.assertEqual(self.backend.get_group_permissions(alice), set())

    def test_group_cache(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            FIND_GROUP_PERMS=True,
            CACHE_GROUPS=True
        )
        self._init_groups()
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(member=uid=alice,ou=people,o=test))", None, 0),
            [self.active_gon, self.staff_gon, self.superuser_gon, self.nested_gon]
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(member=uid=bob,ou=people,o=test))", None, 0),
            []
        )

        alice_id = User.objects.create(username='alice').pk
        bob_id = User.objects.create(username='bob').pk

        # Check permissions twice for each user
        for i in range(2):
            alice = self.backend.get_user(alice_id)
            self.assertEqual(self.backend.get_group_permissions(alice),
                set(["auth.add_user", "auth.change_user"]))

            bob = self.backend.get_user(bob_id)
            self.assertEqual(self.backend.get_group_permissions(bob), set())

        # Should have executed one LDAP search per user
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s', 'search_s', 'initialize', 'simple_bind_s', 'search_s'])

    def test_group_mirroring(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test',
                self.mock_ldap.SCOPE_SUBTREE, "(objectClass=posixGroup)"
            ),
            GROUP_TYPE=PosixGroupType(),
            MIRROR_GROUPS=True,
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=posixGroup)(|(gidNumber=1000)(memberUid=alice)))", None, 0),
            [self.active_px, self.staff_px, self.superuser_px]
        )

        self.assertEqual(Group.objects.count(), 0)

        alice = self.backend.authenticate(username='alice', password='password')

        self.assertEqual(Group.objects.count(), 3)
        self.assertEqual(set(alice.groups.all()), set(Group.objects.all()))

    def test_nested_group_mirroring(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=NestedMemberDNGroupType(member_attr='member'),
            MIRROR_GROUPS=True,
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(|(member=uid=alice,ou=people,o=test)))", None, 0),
            [self.active_gon, self.nested_gon]
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(|(member=cn=active_gon,ou=groups,o=test)(member=cn=nested_gon,ou=groups,o=test)))", None, 0),
            [self.parent_gon]
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(|(member=cn=parent_gon,ou=groups,o=test)))", None, 0),
            [self.circular_gon]
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(|(member=cn=circular_gon,ou=groups,o=test)))", None, 0),
            [self.nested_gon]
        )

        alice = self.backend.authenticate(username='alice', password='password')

        self.assertEqual(Group.objects.count(), 4)
        self.assertEqual(set(Group.objects.all().values_list('name', flat=True)),
            set(['active_gon', 'nested_gon', 'parent_gon', 'circular_gon']))
        self.assertEqual(set(alice.groups.all()), set(Group.objects.all()))

    def test_authorize_external_users(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            FIND_GROUP_PERMS=True,
            AUTHORIZE_ALL_USERS=True
        )
        self._init_groups()
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(member=uid=alice,ou=people,o=test))", None, 0),
            [self.active_gon, self.staff_gon, self.superuser_gon, self.nested_gon]
        )

        alice = User.objects.create(username='alice')

        self.assertEqual(self.backend.get_group_permissions(alice), set(["auth.add_user", "auth.change_user"]))

    def test_create_without_auth(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
        )

        alice = self.backend.populate_user('alice')
        bob = self.backend.populate_user('bob')

        self.assert_(alice is not None)
        self.assertEqual(alice.first_name, u"")
        self.assertEqual(alice.last_name, u"")
        self.assert_(alice.is_active)
        self.assert_(not alice.is_staff)
        self.assert_(not alice.is_superuser)
        self.assert_(bob is not None)
        self.assertEqual(bob.first_name, u"")
        self.assertEqual(bob.last_name, u"")
        self.assert_(bob.is_active)
        self.assert_(not bob.is_staff)
        self.assert_(not bob.is_superuser)

    def test_populate_without_auth(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            ALWAYS_UPDATE_USER=False,
            USER_ATTR_MAP={'first_name': 'givenName', 'last_name': 'sn'},
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
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

        self.assert_(alice is not None)
        self.assertEqual(alice.first_name, u"Alice")
        self.assertEqual(alice.last_name, u"Adams")
        self.assert_(alice.is_active)
        self.assert_(alice.is_staff)
        self.assert_(alice.is_superuser)
        self.assert_(bob is not None)
        self.assertEqual(bob.first_name, u"Robert")
        self.assertEqual(bob.last_name, u"Barker")
        self.assert_(not bob.is_active)
        self.assert_(not bob.is_staff)
        self.assert_(not bob.is_superuser)

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

        self.assert_(not self.mock_ldap.tls_enabled)
        self.backend.authenticate(username='alice', password='password')
        self.assert_(not self.mock_ldap.tls_enabled)

    def test_start_tls(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            START_TLS=True,
        )

        self.assert_(not self.mock_ldap.tls_enabled)
        self.backend.authenticate(username='alice', password='password')
        self.assert_(self.mock_ldap.tls_enabled)

    def test_null_search_results(self):
        """
        Make sure we're not phased by referrals.
        """
        self._init_settings(
            USER_SEARCH=LDAPSearch(
                "ou=people,o=test", self.mock_ldap.SCOPE_SUBTREE, '(uid=%(user)s)'
            )
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=people,o=test", 2, "(uid=alice)", None, 0), [self.alice, (None, '')])

        self.backend.authenticate(username='alice', password='password')

    def test_union_search(self):
        self._init_settings(
            USER_SEARCH=LDAPSearchUnion(
                LDAPSearch("ou=groups,o=test", self.mock_ldap.SCOPE_SUBTREE, '(uid=%(user)s)'),
                LDAPSearch("ou=people,o=test", self.mock_ldap.SCOPE_SUBTREE, '(uid=%(user)s)'),
            )
        )
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(uid=alice)", None, 0), [])
        self.mock_ldap.set_return_value('search_s',
            ("ou=people,o=test", 2, "(uid=alice)", None, 0), [self.alice])

        alice = self.backend.authenticate(username='alice', password='password')

        self.assert_(alice is not None)

        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s', 'search', 'search', 'result',
                'result', 'simple_bind_s'])

    def test_deny_empty_password(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
        )

        alice = self.backend.authenticate(username=u'alice', password=u'')

        self.assertEqual(alice, None)
        self.assertEqual(self.mock_ldap.ldap_methods_called(), [])

    def test_permit_empty_password(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            PERMIT_EMPTY_PASSWORD=True,
        )

        alice = self.backend.authenticate(username=u'alice', password=u'')

        self.assertEqual(alice, None)
        self.assertEqual(self.mock_ldap.ldap_methods_called(),
            ['initialize', 'simple_bind_s'])

    def test_pickle(self):
        self._init_settings(
            USER_DN_TEMPLATE='uid=%(user)s,ou=people,o=test',
            GROUP_SEARCH=LDAPSearch('ou=groups,o=test', self.mock_ldap.SCOPE_SUBTREE),
            GROUP_TYPE=MemberDNGroupType(member_attr='member'),
            FIND_GROUP_PERMS=True
        )
        self._init_groups()
        self.mock_ldap.set_return_value('search_s',
            ("ou=groups,o=test", 2, "(&(objectClass=*)(member=uid=alice,ou=people,o=test))", None, 0),
            [self.active_gon, self.staff_gon, self.superuser_gon, self.nested_gon]
        )

        alice0 = self.backend.authenticate(username=u'alice', password=u'password')

        pickled = pickle.dumps(alice0, pickle.HIGHEST_PROTOCOL)
        alice = pickle.loads(pickled)
        alice.ldap_user.backend.settings = alice0.ldap_user.backend.settings

        self.assert_(alice is not None)
        self.assertEqual(self.backend.get_group_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assertEqual(self.backend.get_all_permissions(alice), set(["auth.add_user", "auth.change_user"]))
        self.assert_(self.backend.has_perm(alice, "auth.add_user"))
        self.assert_(self.backend.has_module_perms(alice, "auth"))

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
