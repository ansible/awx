#!/usr/bin/env python

# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import json
import optparse
import os
import sys
import urllib
import urlparse

# Requests
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

    def get_data(self):
        parts = urlparse.urlsplit(self.base_url)
        if parts.username and parts.password:
            auth = (parts.username, parts.password)
        elif self.auth_token:
            auth = TokenAuth(self.auth_token)
        else:
            auth = None
        url = urlparse.urlunsplit([parts.scheme,
                                   '%s:%d' % (parts.hostname, parts.port),
                                   parts.path, parts.query, parts.fragment])
        url_path = '/api/v1/inventories/%d/script/' % self.inventory_id
        if self.hostname:
            url_path += '?%s' % urllib.urlencode({'host': self.hostname})
        url = urlparse.urljoin(url, url_path)
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        sys.stdout.write(json.dumps(response.json(), indent=self.indent) + '\n')

    def run(self):
        try:
            self.base_url = self.options.get('base_url', '') or \
                            os.getenv('REST_API_URL', '')
            if not self.base_url:
                raise ValueError('No REST API URL specified')
            self.auth_token = self.options.get('authtoken', '') or \
                              os.getenv('REST_API_TOKEN', '')
            parts = urlparse.urlsplit(self.base_url)
            if not (parts.username and parts.password) and not self.auth_token:
                raise ValueError('No REST API token or username/password '
                                 'specified')
            try:
                # Command line argument takes precedence over environment
                # variable.
                self.inventory_id = int(self.options.get('inventory_id', 0) or \
                                        os.getenv('INVENTORY_ID', 0))
            except ValueError:
                raise ValueError('Inventory ID must be an integer')
            if not self.inventory_id:
                raise ValueError('No inventory ID specified')
            self.hostname = self.options.get('hostname', '')
            self.list_ = self.options.get('list', False)
            self.indent = self.options.get('indent', None)
            if self.list_ and self.hostname:
                raise RuntimeError('Only --list or --host may be specified')
            elif self.list_ or self.hostname:
                self.get_data()
            else:
                raise RuntimeError('Either --list or --host must be specified')
        except Exception, e:
            # Always return an empty hash on stdout, even when an error occurs.
            sys.stdout.write(json.dumps({}))
            #print >> file(os.path.join(os.path.dirname(__file__), 'foo.log'), 'a'), repr(e)
            #if hasattr(e, 'response'):
            #    print >> file(os.path.join(os.path.dirname(__file__), 'foo.log'), 'a'), e.response.content
            if self.options.get('traceback', False):
                raise
            sys.stderr.write(str(e) + '\n')
            if hasattr(e, 'response'):
                sys.stderr.write(e.response.content + '\n')
            sys.exit(1)

def main():
    parser = optparse.OptionParser()
    parser.add_option('-v', '--verbosity', action='store', dest='verbosity',
                      default='1', type='choice', choices=['0', '1', '2', '3'],
                      help='Verbosity level; 0=minimal output, 1=normal output'
                      ', 2=verbose output, 3=very verbose output')
    parser.add_option('--traceback', action='store_true',
                      help='Raise on exception on error')
    parser.add_option('-u', '--url', dest='base_url', default='',
                      help='Base URL to access REST API (can also be specified'
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
    parser.add_option('--host', dest='hostname', default='',
                      help='Return JSON hash of host vars.')
    parser.add_option('--indent', dest='indent', type='int', default=None,
                      help='Indentation level for pretty printing output')
    options, args = parser.parse_args()
    InventoryScript(**vars(options)).run()

if __name__ == '__main__':
    main()
