# Copyright 2011 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
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

from troveclient import base
from troveclient import common


class Account(base.Resource):
    """Account is an opaque instance used to hold account information."""
    def __repr__(self):
        return "<Account: %s>" % self.name


class Accounts(base.ManagerWithFind):
    """Manage :class:`Account` information."""

    resource_class = Account

    def _list(self, url, response_key):
        resp, body = self.api.client.get(url)
        if not body:
            raise Exception("Call to " + url + " did not return a body.")
        return self.resource_class(self, body[response_key])

    def index(self):
        """Get a list of all accounts with non-deleted instances."""

        url = "/mgmt/accounts"
        resp, body = self.api.client.get(url)
        common.check_for_exceptions(resp, body, url)
        if not body:
            raise Exception("Call to " + url + " did not return a body.")
        return base.Resource(self, body)

    def show(self, account):
        """Get details of one account.

        :rtype: :class:`Account`.
        """

        acct_name = self._get_account_name(account)
        return self._list("/mgmt/accounts/%s" % acct_name, 'account')

    # Appease the abc gods
    def list(self):
        pass

    @staticmethod
    def _get_account_name(account):
        try:
            if account.name:
                return account.name
        except AttributeError:
            return account
