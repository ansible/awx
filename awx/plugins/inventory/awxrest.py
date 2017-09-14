#!/usr/bin/env python

# Copyright (c) 2015 Ansible, Inc.
# This file is a utility script that is not part of the AWX or Ansible
# packages.  It does not import any code from either package, nor does its
# license apply to Ansible or AWX.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
#    Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#    Neither the name of the <ORGANIZATION> nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Python
import json
import optparse
import os
import sys
import traceback
import urllib
import urlparse

# Requests
try:
    import requests
except ImportError:
    # If running from an AWX installation, use the local version of requests if
    # if cannot be found globally.
    local_site_packages = os.path.join(os.path.dirname(__file__), '..', '..',
                                       'lib', 'site-packages')
    if os.path.exists(local_site_packages):
        sys.path.insert(0, local_site_packages)
    import requests

class TokenAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        request.headers['Authorization'] = 'Token %s' % self.token
        return request

class InventoryScript(object):

    def __init__(self, **options):
        self.options = options

    def get_data(self, output):
        parts = urlparse.urlsplit(self.base_url)
        if parts.username and parts.password:
            auth = (parts.username, parts.password)
        elif self.auth_token:
            auth = TokenAuth(self.auth_token)
        else:
            auth = None
        port = parts.port or (443 if parts.scheme == 'https' else 80)
        url = urlparse.urlunsplit([parts.scheme,
                                   '%s:%d' % (parts.hostname, port),
                                   parts.path, parts.query, parts.fragment])
        url_path = '/api/v1/inventories/%d/script/' % self.inventory_id
        q = {}
        if self.show_all:
            q['all'] = 1
        if self.hostname:
            q['host'] = self.hostname
        elif self.hostvars:
            q['hostvars'] = 1
        url_path += '?%s' % urllib.urlencode(q)
        url = urlparse.urljoin(url, url_path)
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        output.write(json.dumps(json.loads(response.content),
                                    indent=self.indent) + '\n')

    def run(self, output=sys.stdout):
        try:
            self.base_url = self.options.get('base_url', '') or \
                os.getenv('REST_API_URL', '')
            if not self.base_url:
                raise ValueError('No REST API URL specified')
            self.auth_token = self.options.get('authtoken', '') or \
                os.getenv('REST_API_TOKEN', '')
            parts = urlparse.urlsplit(self.base_url)
            if not (parts.username and parts.password) and not self.auth_token:
                raise ValueError('No username/password specified in REST API '
                                 'URL, and no REST API token provided')
            try:
                # Command line argument takes precedence over environment
                # variable.
                self.inventory_id = int(self.options.get('inventory_id', 0) or
                                        os.getenv('INVENTORY_ID', 0))
            except ValueError:
                raise ValueError('Inventory ID must be an integer')
            if not self.inventory_id:
                raise ValueError('No inventory ID specified')
            self.hostname = self.options.get('hostname', '')
            self.list_ = self.options.get('list', False)
            self.hostvars = bool(self.options.get('hostvars', False) or
                                 os.getenv('INVENTORY_HOSTVARS', ''))
            self.show_all = bool(self.options.get('show_all', False) or
                                 os.getenv('INVENTORY_ALL', ''))
            self.indent = self.options.get('indent', None)
            if self.list_ and self.hostname:
                raise RuntimeError('Only --list or --host may be specified')
            elif self.list_ or self.hostname:
                self.get_data(output)
            else:
                raise RuntimeError('Either --list or --host must be specified')
        except Exception as e:
            output.write('%s\n' % json.dumps(dict(failed=True)))
            if self.options.get('traceback', False):
                sys.stderr.write(traceback.format_exc())
            else:
                sys.stderr.write('%s\n' % str(e))
            if hasattr(e, 'response'):
                if hasattr(e.response, 'content'):
                    sys.stderr.write('%s\n' % e.response.content)
                else:
                    sys.stderr.write('%s\n' % e.response)
            raise

def main():
    parser = optparse.OptionParser()
    parser.add_option('-v', '--verbosity', action='store', dest='verbosity',
                      default='1', type='choice', choices=['0', '1', '2', '3'],
                      help='Verbosity level; 0=minimal output, 1=normal output'
                      ', 2=verbose output, 3=very verbose output')
    parser.add_option('--traceback', action='store_true',
                      help='Raise on exception on error')
    parser.add_option('-u', '--url', dest='base_url', default='',
                      help='Base URL to access REST API, including username '
                      'and password for authentication (can also be specified'
                      ' using REST_API_URL environment variable)')
    parser.add_option('--authtoken', dest='authtoken', default='',
                      help='Authentication token used to access REST API (can '
                      'also be specified using REST_API_TOKEN environment '
                      'variable)')
    parser.add_option('-i', '--inventory', dest='inventory_id', type='int',
                      default=0, help='Inventory ID (can also be specified '
                      'using INVENTORY_ID environment variable)')
    parser.add_option('--list', action='store_true', dest='list',
                      default=False, help='Return JSON hash of host groups.')
    parser.add_option('--hostvars', action='store_true', dest='hostvars',
                      default=False, help='Return hostvars inline with --list,'
                      ' under ["_meta"]["hostvars"]. Can also be specified '
                      'using INVENTORY_HOSTVARS environment variable.')
    parser.add_option('--all', action='store_true', dest='show_all',
                      default=False, help='Return all hosts, including those '
                      'marked as offline/disabled. Can also be specified '
                      'using INVENTORY_ALL environment variable.')
    parser.add_option('--host', dest='hostname', default='',
                      help='Return JSON hash of host vars.')
    parser.add_option('--indent', dest='indent', type='int', default=None,
                      help='Indentation level for pretty printing output')
    options, args = parser.parse_args()
    try:
        InventoryScript(**vars(options)).run()
    except Exception:
        sys.exit(1)


if __name__ == '__main__':
    main()
