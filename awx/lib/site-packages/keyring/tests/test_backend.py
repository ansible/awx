# -*- coding: utf-8 -*-
"""
test_backend.py

Test case for keyring basic function

created by Kang Zhang 2009-07-14
"""
from __future__ import with_statement

import string

from keyring.util import escape
from .util import random_string
from keyring import errors

DIFFICULT_CHARS = string.whitespace + string.punctuation
# unicode only characters
# Sourced from The Quick Brown Fox... Pangrams
# http://www.columbia.edu/~fdc/utf8/
UNICODE_CHARS = escape.u(
    """זהכיףסתםלשמועאיךתנצחקרפדעץטובבגן"""
    """ξεσκεπάζωτηνψυχοφθόραβδελυγμία"""
    """Съешьжеещёэтихмягкихфранцузскихбулокдавыпейчаю"""
    """Жълтатадюлябешещастливачепухъткойтоцъфназамръзнакатогьон"""
)

# ensure no-ascii chars slip by - watch your editor!
assert min(ord(char) for char in UNICODE_CHARS) > 127

class BackendBasicTests(object):
    """Test for the keyring's basic functions. password_set and password_get
    """

    def setUp(self):
        self.keyring = self.init_keyring()
        self.credentials_created = set()

    def tearDown(self):
        for item in self.credentials_created:
            self.keyring.delete_password(*item)

    def set_password(self, service, username, password):
        # set the password and save the result so the test runner can clean
        #  up after if necessary.
        self.keyring.set_password(service, username, password)
        self.credentials_created.add((service, username))

    def check_set_get(self, service, username, password):
        keyring = self.keyring

        # for the non-existent password
        self.assertEqual(keyring.get_password(service, username), None)

        # common usage
        self.set_password(service, username, password)
        self.assertEqual(keyring.get_password(service, username), password)

        # for the empty password
        self.set_password(service, username, "")
        self.assertEqual(keyring.get_password(service, username), "")

    def test_password_set_get(self):
        password = random_string(20)
        username = random_string(20)
        service = random_string(20)
        self.check_set_get(service, username, password)

    def test_difficult_chars(self):
        password = random_string(20, DIFFICULT_CHARS)
        username = random_string(20, DIFFICULT_CHARS)
        service = random_string(20, DIFFICULT_CHARS)
        self.check_set_get(service, username, password)

    def test_delete_present(self):
        password = random_string(20, DIFFICULT_CHARS)
        username = random_string(20, DIFFICULT_CHARS)
        service = random_string(20, DIFFICULT_CHARS)
        self.keyring.set_password(service, username, password)
        self.keyring.delete_password(service, username)
        self.assertTrue(self.keyring.get_password(service, username) is None)

    def test_delete_not_present(self):
        username = random_string(20, DIFFICULT_CHARS)
        service = random_string(20, DIFFICULT_CHARS)
        self.assertRaises(errors.PasswordDeleteError,
            self.keyring.delete_password, service, username)

    def test_unicode_chars(self):
        password = random_string(20, UNICODE_CHARS)
        username = random_string(20, UNICODE_CHARS)
        service = random_string(20, UNICODE_CHARS)
        self.check_set_get(service, username, password)

    def test_unicode_and_ascii_chars(self):
        source = (random_string(10, UNICODE_CHARS) + random_string(10) +
                 random_string(10, DIFFICULT_CHARS))
        password = random_string(20, source)
        username = random_string(20, source)
        service = random_string(20, source)
        self.check_set_get(service, username, password)

    def test_different_user(self):
        """
        Issue #47 reports that WinVault isn't storing passwords for
        multiple users. This test exercises that test for each of the
        backends.
        """

        keyring = self.keyring
        self.set_password('service1', 'user1', 'password1')
        self.set_password('service1', 'user2', 'password2')
        self.assertEqual(keyring.get_password('service1', 'user1'),
            'password1')
        self.assertEqual(keyring.get_password('service1', 'user2'),
            'password2')
        self.set_password('service2', 'user3', 'password3')
        self.assertEqual(keyring.get_password('service1', 'user1'),
            'password1')
