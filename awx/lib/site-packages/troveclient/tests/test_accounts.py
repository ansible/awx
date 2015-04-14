# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
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

import mock
import testtools

from troveclient import base
from troveclient.v1 import accounts

"""
Unit tests for accounts.py
"""


class AccountTest(testtools.TestCase):

    def setUp(self):
        super(AccountTest, self).setUp()
        self.orig__init = accounts.Account.__init__
        accounts.Account.__init__ = mock.Mock(return_value=None)
        self.account = accounts.Account()

    def tearDown(self):
        super(AccountTest, self).tearDown()
        accounts.Account.__init__ = self.orig__init

    def test___repr__(self):
        self.account.name = "account-1"
        self.assertEqual('<Account: account-1>', self.account.__repr__())


class AccountsTest(testtools.TestCase):

    def setUp(self):
        super(AccountsTest, self).setUp()
        self.orig__init = accounts.Accounts.__init__
        accounts.Accounts.__init__ = mock.Mock(return_value=None)
        self.accounts = accounts.Accounts()
        self.accounts.api = mock.Mock()
        self.accounts.api.client = mock.Mock()

    def tearDown(self):
        super(AccountsTest, self).tearDown()
        accounts.Accounts.__init__ = self.orig__init

    def test__list(self):
        def side_effect_func(self, val):
            return val

        self.accounts.resource_class = mock.Mock(side_effect=side_effect_func)
        key_ = 'key'
        body_ = {key_: "test-value"}
        self.accounts.api.client.get = mock.Mock(return_value=('resp', body_))
        self.assertEqual("test-value", self.accounts._list('url', key_))

        self.accounts.api.client.get = mock.Mock(return_value=('resp', None))
        self.assertRaises(Exception, self.accounts._list, 'url', None)

    def test_index(self):
        resp = mock.Mock()
        resp.status_code = 400
        body = {"Accounts": {}}
        self.accounts.api.client.get = mock.Mock(return_value=(resp, body))
        self.assertRaises(Exception, self.accounts.index)
        resp.status_code = 200
        self.assertTrue(isinstance(self.accounts.index(), base.Resource))
        self.accounts.api.client.get = mock.Mock(return_value=(resp, None))
        self.assertRaises(Exception, self.accounts.index)

    def test_show(self):
        def side_effect_func(acct_name, acct):
            return acct_name, acct

        account_ = mock.Mock()
        account_.name = "test-account"
        self.accounts._list = mock.Mock(side_effect=side_effect_func)
        self.assertEqual(('/mgmt/accounts/test-account', 'account'),
                         self.accounts.show(account_))

    def test__get_account_name(self):
        account_ = 'account with no name'
        self.assertEqual(account_,
                         accounts.Accounts._get_account_name(account_))
        account_ = mock.Mock()
        account_.name = "account-name"
        self.assertEqual("account-name",
                         accounts.Accounts._get_account_name(account_))
