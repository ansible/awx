#    Copyright 2011 OpenStack Foundation
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

import copy
import json
import optparse
import os
import pickle
import six
from six.moves.urllib import parse
import sys

from troveclient.compat import client
from troveclient.compat import exceptions


def methods_of(obj):
    """Get all callable methods of an object that don't start with underscore
    returns a list of tuples of the form (method_name, method).
    """
    result = {}
    for i in dir(obj):
        if callable(getattr(obj, i)) and not i.startswith('_'):
            result[i] = getattr(obj, i)
    return result


def check_for_exceptions(resp, body):
    if resp.status in (400, 422, 500):
        raise exceptions.from_response(resp, body)


def print_actions(cmd, actions):
    """Print help for the command with list of options and description."""
    print("Available actions for '%s' cmd:" % cmd)
    for k, v in six.iteritems(actions):
        print("\t%-20s%s" % (k, v.__doc__))
    sys.exit(2)


def print_commands(commands):
    """Print the list of available commands and description."""

    print("Available commands")
    for k, v in six.iteritems(commands):
        print("\t%-20s%s" % (k, v.__doc__))
    sys.exit(2)


def limit_url(url, limit=None, marker=None):
    if not limit and not marker:
        return url
    query = []
    if marker:
        query.append("marker=%s" % marker)
    if limit:
        query.append("limit=%s" % limit)
    query = '?' + '&'.join(query)
    return url + query


def quote_user_host(user, host):
    quoted = ''
    if host:
        quoted = parse.quote("%s@%s" % (user, host))
    else:
        quoted = parse.quote("%s" % user)
    return quoted.replace('.', '%2e')


class CliOptions(object):
    """A token object containing the user, apikey and token which
       is pickleable.
    """

    APITOKEN = os.path.expanduser("~/.apitoken")

    DEFAULT_VALUES = {
        'username': None,
        'apikey': None,
        'tenant_id': None,
        'auth_url': None,
        'auth_type': 'keystone',
        'service_type': 'database',
        'service_name': '',
        'region': 'RegionOne',
        'service_url': None,
        'insecure': False,
        'verbose': False,
        'debug': False,
        'token': None,
    }

    def __init__(self, **kwargs):
        for key, value in self.DEFAULT_VALUES.items():
            setattr(self, key, value)

    @classmethod
    def default(cls):
        kwargs = copy.deepcopy(cls.DEFAULT_VALUES)
        return cls(**kwargs)

    @classmethod
    def load_from_file(cls):
        try:
            with open(cls.APITOKEN, 'rb') as token:
                return pickle.load(token)
        except IOError:
            pass  # File probably not found.
        except Exception:
            print("ERROR: Token file found at %s was corrupt." % cls.APITOKEN)
        return cls.default()

    @classmethod
    def save_from_instance_fields(cls, instance):
        apitoken = cls.default()
        for key, default_value in cls.DEFAULT_VALUES.items():
            final_value = getattr(instance, key, default_value)
            setattr(apitoken, key, final_value)
        with open(cls.APITOKEN, 'wb') as token:
            pickle.dump(apitoken, token, protocol=2)

    @classmethod
    def create_optparser(cls, load_file):
        oparser = optparse.OptionParser(
            usage="%prog [options] <cmd> <action> <args>",
            version='1.0', conflict_handler='resolve')
        if load_file:
            file = cls.load_from_file()
        else:
            file = cls.default()

        def add_option(*args, **kwargs):
            if len(args) == 1:
                name = args[0]
            else:
                name = args[1]
            kwargs['default'] = getattr(file, name, cls.DEFAULT_VALUES[name])
            oparser.add_option("--%s" % name, **kwargs)

        add_option("verbose", action="store_true",
                   help="Show equivalent curl statement along "
                        "with actual HTTP communication.")
        add_option("debug", action="store_true",
                   help="Show the stack trace on errors.")
        add_option("auth_url", help="Auth API endpoint URL with port and "
                   "version. Default: http://localhost:5000/v2.0")
        add_option("username", help="Login username.")
        add_option("apikey", help="API key.")
        add_option("tenant_id",
                   help="Tenant Id associated with the account.")
        add_option("auth_type",
                   help="Auth type to support different auth environments, \
                                Supported values are 'keystone', 'rax'.")
        add_option("service_type",
                   help="Service type is a name associated for the catalog.")
        add_option("service_name",
                   help="Service name as provided in the service catalog.")
        add_option("service_url",
                   help="Service endpoint to use "
                        "if the catalog doesn't have one.")
        add_option("region", help="Region the service is located in.")
        add_option("insecure", action="store_true",
                   help="Run in insecure mode for https endpoints.")
        add_option("token", help="Token from a prior login.")

        oparser.add_option("--json", action="store_false", dest="xml",
                           help="Changes format to JSON.")
        oparser.add_option("--secure", action="store_false", dest="insecure",
                           help="Run in insecure mode for https endpoints.")
        oparser.add_option("--terse", action="store_false", dest="verbose",
                           help="Toggles verbose mode off.")
        oparser.add_option("--hide-debug", action="store_false", dest="debug",
                           help="Toggles debug mode off.")
        return oparser


class ArgumentRequired(Exception):
    def __init__(self, param):
        self.param = param

    def __str__(self):
        return 'Argument "--%s" required.' % self.param


class ArgumentsRequired(ArgumentRequired):
    def __init__(self, *params):
        self.params = params

    def __str__(self):
        returnstring = 'Specify at least one of these arguments: '
        for param in self.params:
            returnstring = returnstring + '"--%s" ' % param
        return returnstring


class CommandsBase(object):
    params = []

    def __init__(self, parser):
        self._parse_options(parser)

    def _get_client(self):
        """Creates the all important client object."""
        try:
            client_cls = client.TroveHTTPClient
            if self.verbose:
                client.log_to_streamhandler(sys.stdout)
                client.RDC_PP = True
            return client.Dbaas(self.username, self.apikey, self.tenant_id,
                                auth_url=self.auth_url,
                                auth_strategy=self.auth_type,
                                service_type=self.service_type,
                                service_name=self.service_name,
                                region_name=self.region,
                                service_url=self.service_url,
                                insecure=self.insecure,
                                client_cls=client_cls)
        except Exception:
            if self.debug:
                raise
            print(sys.exc_info()[1])

    def _safe_exec(self, func, *args, **kwargs):
        if not self.debug:
            try:
                return func(*args, **kwargs)
            except Exception:
                print(sys.exc_info()[1])
                return None
        else:
            return func(*args, **kwargs)

    @classmethod
    def _prepare_parser(cls, parser):
        for param in cls.params:
            parser.add_option("--%s" % param)

    def _parse_options(self, parser):
        opts, args = parser.parse_args()
        for param in opts.__dict__:
            value = getattr(opts, param)
            setattr(self, param, value)

    def _require(self, *params):
        for param in params:
            if not hasattr(self, param):
                raise ArgumentRequired(param)
            if not getattr(self, param):
                raise ArgumentRequired(param)

    def _require_at_least_one_of(self, *params):
        # One or more of params is required to be present.
        argument_present = False
        for param in params:
            if hasattr(self, param):
                if getattr(self, param):
                    argument_present = True
        if argument_present is False:
            raise ArgumentsRequired(*params)

    def _make_list(self, *params):
        # Convert the listed params to lists.
        for param in params:
            raw = getattr(self, param)
            if isinstance(raw, list):
                return
            raw = [item.strip() for item in raw.split(',')]
            setattr(self, param, raw)

    def _pretty_print(self, func, *args, **kwargs):
        if self.verbose:
            self._safe_exec(func, *args, **kwargs)
            return  # Skip this, since the verbose stuff will show up anyway.

        def wrapped_func():
            result = func(*args, **kwargs)
            if result:
                print(json.dumps(result._info, sort_keys=True, indent=4))
            else:
                print("OK")

        self._safe_exec(wrapped_func)

    def _dumps(self, item):
        return json.dumps(item, sort_keys=True, indent=4)

    def _pretty_list(self, func, *args, **kwargs):
        result = self._safe_exec(func, *args, **kwargs)
        if self.verbose:
            return
        if result and len(result) > 0:
            for item in result:
                print(self._dumps(item._info))
        else:
            print("OK")

    def _pretty_paged(self, func, *args, **kwargs):
        try:
            limit = self.limit
            if limit:
                limit = int(limit, 10)
            result = func(*args, limit=limit, marker=self.marker, **kwargs)
            if self.verbose:
                return  # Verbose already shows the output, so skip this.
            if result and len(result) > 0:
                for item in result:
                    print(self._dumps(item._info))
                if result.links:
                    print("Links:")
                    for link in result.links:
                        print(self._dumps((link)))
            else:
                print("OK")
        except Exception:
            if self.debug:
                raise
            print(sys.exc_info()[1])


class Auth(CommandsBase):
    """Authenticate with your username and api key."""
    params = [
        'apikey',
        'auth_strategy',
        'auth_type',
        'auth_url',
        'options',
        'region',
        'service_name',
        'service_type',
        'service_url',
        'tenant_id',
        'username',
    ]

    def __init__(self, parser):
        super(Auth, self).__init__(parser)
        self.dbaas = None

    def login(self):
        """Login to retrieve an auth token to use for other api calls."""
        self._require('username', 'apikey', 'tenant_id', 'auth_url')
        try:
            self.dbaas = self._get_client()
            self.dbaas.authenticate()
            self.token = self.dbaas.client.auth_token
            self.service_url = self.dbaas.client.service_url
            CliOptions.save_from_instance_fields(self)
            print("Token acquired! Saving to %s..." % CliOptions.APITOKEN)
            print("    service_url = %s" % self.service_url)
            print("    token       = %s" % self.token)
        except Exception:
            if self.debug:
                raise
            print(sys.exc_info()[1])


class AuthedCommandsBase(CommandsBase):
    """Commands that work only with an authenticated client."""

    def __init__(self, parser):
        """Makes sure a token is available somehow and logs in."""
        super(AuthedCommandsBase, self).__init__(parser)
        try:
            self._require('token')
        except ArgumentRequired:
            if self.debug:
                raise
            print('No token argument supplied. Use the "auth login" command '
                  'to log in and get a token.\n')
            sys.exit(1)
        try:
            self._require('service_url')
        except ArgumentRequired:
            if self.debug:
                raise
            print('No service_url given.\n')
            sys.exit(1)
        self.dbaas = self._get_client()
        # Actually set the token to avoid a re-auth.
        self.dbaas.client.auth_token = self.token
        self.dbaas.client.authenticate_with_token(self.token, self.service_url)


class Paginated(object):
    """Pretends to be a list if you iterate over it, but also keeps a
       next property you can use to get the next page of data.
    """

    def __init__(self, items=[], next_marker=None, links=[]):
        self.items = items
        self.next = next_marker
        self.links = links

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return self.items.__iter__()

    def __getitem__(self, key):
        return self.items[key]

    def __setitem__(self, key, value):
        self.items[key] = value

    def __delitem__(self, key):
        del self.items[key]

    def __reversed__(self):
        return reversed(self.items)

    def __contains__(self, needle):
        return needle in self.items
