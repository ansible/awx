from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import Request, SSLValidationError, ConnectionError
from ansible.module_utils.six.moves.urllib.parse import urlparse, urlencode

from socket import gethostbyname
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.six.moves.http_cookiejar import CookieJar
from ansible.module_utils.six.moves.configparser import ConfigParser, NoOptionError, NoSectionError
import re
from json import loads, dumps
from os.path import isfile
from os import access, R_OK


class TowerModule(AnsibleModule):
    url = None
    honorred_settings = ['host', 'username', 'password', 'verify_ssl', 'oauth_token']
    host = '127.0.0.1'
    username = None
    password = None
    verify_ssl = True
    oauth_token = None
    oauth_token_id = None
    session = None
    cookie_jar = CookieJar()
    authenticated = False
    json_output = {'changed': False}

    def __init__(self, argument_spec, **kwargs):
        args = dict(
            tower_host=dict(required=False, fallback=(env_fallback, ['TOWER_HOST'])),
            tower_username=dict(required=False, fallback=(env_fallback, ['TOWER_USERNAME'])),
            tower_password=dict(no_log=True, required=False, fallback=(env_fallback, ['TOWER_PASSWORD'])),
            validate_certs=dict(type='bool', aliases=['tower_verify_ssl'], required=False, fallback=(env_fallback, ['TOWER_VERIFY_SSL'])),
            tower_oauthtoken=dict(type='str', no_log=True, required=False, fallback=(env_fallback, ['TOWER_OAUTH_TOKEN'])),
            tower_config_file=dict(type='path', required=False, default=None),
        )
        args.update(argument_spec)
        kwargs['supports_check_mode'] = True

        super(TowerModule, self).__init__(argument_spec=args, **kwargs)

        # If we have a tower config, load it
        if self.params.get('tower_config_file'):
            self.load_config(self.params.get('tower_config_file'))

        # Parameters specified on command line will override settings in config
        if self.params.get('tower_host'):
            self.host = self.params.get('tower_host')
        if self.params.get('tower_username'):
            self.username = self.params.get('tower_username')
        if self.params.get('tower_password'):
            self.password = self.params.get('tower_password')
        if self.params.get('validate_certs') is not None:
            self.verify_ssl = self.params.get('validate_certs')
        if self.params.get('tower_oauthtoken'):
            self.oauth_token = self.params.get('tower_oauthtoken')

        # Perform some basic validation
        if not re.match('^https{0,1}://', self.host):
            self.host = "https://{0}".format(self.host)

        # Try to parse the hostname as a url
        try:
            self.url = urlparse(self.host)
        except Exception as e:
            self.fail_json(msg="Unable to parse tower_host as a URL ({1}): {0}".format(self.host, e))

        # Try to resolve the hostname
        hostname = self.url.netloc.split(':')[0]
        try:
            gethostbyname(hostname)
        except Exception as e:
            self.fail_json(msg="Unable to resolve tower_host ({1}): {0}".format(hostname, e))

        self.session = Request(cookies=self.cookie_jar)

    def load_config(self, config_path):
        config = ConfigParser()
        # Validate the config file is an actual file
        if not isfile(config_path):
            self.fail_json(msg='The specified config file does not exist')

        if not access(config_path, R_OK):
            self.fail_json(msg="The specified config file can not be read")

        config.read(config_path)

        for honorred_setting in self.honorred_settings:
            try:
                setattr(self, honorred_setting, config.get('general', honorred_setting))
            except (NoSectionError) as nse:
                self.fail_json(msg="The specified config file does not contain a general section ({0})".format(nse))
            except (NoOptionError):
                pass

    def get_endpoint(self, endpoint, *args, **kwargs):
        return self.make_request('GET', endpoint, **kwargs)

    def patch_endpoint(self, endpoint, *args, **kwargs):
        # Handle check mode
        if self.check_mode:
            self.json_output['changed'] = True
            self.exit_json(**self.json_output)

        return self.make_request('PATCH', endpoint, **kwargs)

    def post_endpoint(self, endpoint, handle_return=True, item_type='item', item_name='', *args, **kwargs):
        # Handle check mode
        if self.check_mode:
            self.json_output['changed'] = True
            self.exit_json(**self.json_output)

        response = self.make_request('POST', endpoint, **kwargs)
        if response['status_code'] == 201:
            self.json_output['changed'] = True
            self.json_output['id'] = response['json']['id']
            self.exit_json(**self.json_output)
        else:
            if 'json' in response and '__all__' in response['json']:
                self.fail_json(msg="Unable to create {0} {1}: {2}".format(item_type, item_name, response['json']['__all__'][0]))
            else:
                self.fail_json(msg="Unable to create {0} {1}: {2}".format(item_type, item_name, response['status_code']))

    def delete_endpoint(self, endpoint, handle_return=True, item_type='item', item_name='', *args, **kwargs):
        # Handle check mode
        if self.check_mode:
            self.json_output['changed'] = True
            self.exit_json(**self.json_output)

        response = self.make_request('DELETE', endpoint, **kwargs)
        if not handle_return:
            return response
        elif response['status_code'] in [202, 204]:
            self.json_output['changed'] = True
            self.exit_json(**self.json_output)
        else:
            self.fail_json(msg="Unable to delete {0} {1}: {2}".format(item_type, item_name, response['status_code']))

    def get_all_endpoint(self, endpoint, *args, **kwargs):
        response = self.get_endpoint(endpoint, *args, **kwargs)
        next_page = response['json']['next']

        if response['json']['count'] > 10000:
            self.fail_json(msg='The number of items being queried for is higher than 10,000.')

        while next_page is not None:
            next_response = self.get_endpoint(next_page)
            response['json']['results'] = response['json']['results'] + next_response['json']['results']
            next_page = next_response['json']['next']
        return response

    def get_one(self, endpoint, *args, **kwargs):
        response = self.get_endpoint(endpoint, *args, **kwargs)
        if response['status_code'] != 200:
            self.fail_json(msg="Got a {0} response when trying to get one from {1}".format(response['status_code'], endpoint))

        if 'count' not in response['json'] or 'results' not in response['json']:
            self.fail_json(msg="The endpoint did not provide count and results")

        if response['json']['count'] == 0:
            return None
        elif response['json']['count'] > 1:
            self.fail_json(msg="An unexpected number of items was returned from the API ({0})".format(response['json']['count']))

        return response['json']['results'][0]

    def resolve_name_to_id(self, endpoint, name_or_id):
        # Try to resolve the object by name
        response = self.get_endpoint(endpoint, **{'data': {'name': name_or_id}})
        if response['json']['count'] == 1:
            return response['json']['results'][0]['id']
        elif response['json']['count'] == 0:
            self.fail_json(msg="The {0} {1} was not found on the Tower server".format(endpoint, name_or_id))
        else:
            self.fail_json(msg="Found too many names {0} at endpoint {1}".format(name_or_id, endpoint))

    def make_request(self, method, endpoint, *args, **kwargs):
        # Incase someone is calling us directly; make sure we were given a method, lets not just assume a GET
        if not method:
            raise Exception("The HTTP method must be defined")

        # Make sure we start with /api/vX
        if not endpoint.startswith("/"):
            endpoint = "/{0}".format(endpoint)
        if not endpoint.startswith("/api/"):
            endpoint = "/api/v2{0}".format(endpoint)
        if not endpoint.endswith('/') and '?' not in endpoint:
            endpoint = "{0}/".format(endpoint)

        # Extract the headers, this will be used in a couple of places
        headers = kwargs.get('headers', {})

        # Authenticate to Tower (if we've not already done so)
        if not self.authenticated:
            # This method will set a cookie in the cookie jar for us
            self.authenticate(**kwargs)
        if self.oauth_token:
            # If we have a oauth toekn we just use a bearer header
            headers['Authorization'] = 'Bearer {0}'.format(self.oauth_token)

        # Update the URL path with the endpoint
        self.url = self.url._replace(path=endpoint)

        if method in ['POST', 'PUT', 'PATCH']:
            headers.setdefault('Content-Type', 'application/json')
            kwargs['headers'] = headers
        elif kwargs.get('data'):
            self.url = self.url._replace(query=urlencode(kwargs.get('data')))

        data = {}
        if headers.get('Content-Type', '') == 'application/json':
            data = dumps(kwargs.get('data', {}))

        try:
            response = self.session.open(method, self.url.geturl(), headers=headers, validate_certs=self.verify_ssl, follow_redirects=True, data=data)
            self.url = self.url._replace(query=None)
        except(SSLValidationError) as ssl_err:
            self.fail_json(msg="Could not establish a secure connection to your host ({1}): {0}.".format(self.url.netloc, ssl_err))
        except(ConnectionError) as con_err:
            self.fail_json(msg="There was a network error of some kind trying to connect to your host ({1}): {0}.".format(self.url.netloc, con_err))
        except(HTTPError) as he:
            # Sanity check: Did the server send back some kind of internal error?
            if he.code >= 500:
                self.fail_json(msg='The host sent back a server error ({1}): {0}. Please check the logs and try again later'.format(self.url.path, he))
            # Sanity check: Did we fail to authenticate properly?  If so, fail out now; this is always a failure.
            elif he.code == 401:
                self.fail_json(msg='Invalid Tower authentication credentials for {0} (HTTP 401).'.format(self.url.path))
            # Sanity check: Did we get a forbidden response, which means that the user isn't allowed to do this? Report that.
            elif he.code == 403:
                self.fail_json(msg="You don't have permission to {1} to {0} (HTTP 403).".format(self.url.path, method))
            # Sanity check: Did we get a 404 response?
            # Requests with primary keys will return a 404 if there is no response, and we want to consistently trap these.
            elif he.code == 404:
                self.fail_json(msg='The requested object could not be found at {0}.'.format(self.url.path))
            # Sanity check: Did we get a 405 response?
            # A 405 means we used a method that isn't allowed. Usually this is a bad request, but it requires special treatment because the
            # API sends it as a logic error in a few situations (e.g. trying to cancel a job that isn't running).
            elif he.code == 405:
                self.fail_json(msg="The Tower server says you can't make a request with the {0} method to this endpoing {1}".format(method, self.url.path))
            # Sanity check: Did we get some other kind of error?  If so, write an appropriate error message.
            elif he.code >= 400:
                # We are going to return a 400 so the module can decide what to do with it
                page_data = he.read()
                try:
                    return {'status_code': he.code, 'json': loads(page_data)}
                # JSONDecodeError only available on Python 3.5+
                except ValueError:
                    return {'status_code': he.code, 'text': page_data}
                # self.fail_json(msg='The Tower server claims it was sent a bad request.\n{0} {1}\nstatus code: {2}\n\nResponse: {3}'.format(
                #     method, self.url.path, he.code, he.read()))
            elif he.code == 204 and method == 'DELETE':
                # a 204 is a normal response for a delete function
                pass
            else:
                self.fail_json(msg="Unexpected return code when calling {0}: {1}".format(self.url.geturl(), he))
        except(Exception) as e:
            self.fail_json(msg="There was an unknown error when trying to connect to {2}: {0} {1}".format(type(e).__name__, e, self.url.geturl()))

        response_body = ''
        try:
            response_body = response.read()
        except(Exception) as e:
            self.fail_json(msg="Failed to read response body: {0}".format(e))

        response_json = {}
        if response_body and response_body != '':
            try:
                response_json = loads(response_body)
            except(Exception) as e:
                self.fail_json(msg="Failed to parse the response json: {0}".format(e))

        return {'status_code': response.status, 'json': response_json}

    def authenticate(self, **kwargs):
        if self.username and self.password:
            # Attempt to get a token from /api/v2/tokens/ by giving it our username/password combo
            # If we have a username and password we need to get a session cookie
            login_data = {
                "description": "Ansible Tower Module Token",
                "application": None,
                "scope": "write",
            }
            # Post to the tokens endpoint with baisc auth to try and get a token
            api_token_url = (self.url._replace(path='/api/v2/tokens/')).geturl()

            try:
                response = self.session.open(
                    'POST', api_token_url,
                    validate_certs=self.verify_ssl, follow_redirects=True,
                    force_basic_auth=True, url_username=self.username, url_password=self.password,
                    data=dumps(login_data), headers={'Content-Type': 'application/json'}
                )
            except(Exception) as e:
                # Sanity check: Did the server send back some kind of internal error?
                self.fail_json(msg='Failed to get token: {0}'.format(e))

            try:
                response_json = loads(response.read())
                self.oauth_token_id = response_json['id']
                self.oauth_token = response_json['token']
            except(Exception) as e:
                self.fail_json(msg="Failed to extract token information from response: {0}".format(e))

        # If we have neiter of these then we can try un-authenticated access
        self.authenticated = True

    def default_check_mode(self):
        '''Execute check mode logic for Ansible Tower modules'''
        if self.check_mode:
            try:
                result = self.get_endpoint('ping')
                self.exit_json(**{'changed': True, 'tower_version': '{0}'.format(result['json']['version'])})
            except(Exception) as excinfo:
                self.fail_json(changed=False, msg='Failed check mode: {0}'.format(excinfo))

    def update_if_needed(self, existing_item, new_item, handle_response=True, **existing_return):
        for field in new_item:
            existing_field = existing_item.get(field, None)
            new_field = new_item.get(field, None)
            # If the two items don't match and we are not comparing '' to None
            if existing_field != new_field and not (existing_field in (None, '') and new_field == ''):
                # something dosent match so lets do it

                response = self.patch_endpoint(existing_item['url'], **{'data': new_item})
                if not handle_response:
                    return response
                elif response['status_code'] == 200:
                    existing_return['changed'] = True
                    existing_return['id'] = response['json'].get('id')
                    self.exit_json(**existing_return)
                elif 'json' in response and '__all__' in response['json']:
                    self.fail_json(msg=response['json']['__all__'])
                else:
                    self.fail_json(**{'msg': "Unable to update object, see response", 'response': response})

        # Since we made it here, we don't need to update, status ok
        existing_return['changed'] = False
        existing_return['id'] = existing_item.get('id')
        self.exit_json(**existing_return)

    def logout(self):
        if self.oauth_token_id is not None and self.username and self.password:
            # Attempt to delete our current token from /api/v2/tokens/
            # Post to the tokens endpoint with baisc auth to try and get a token
            api_token_url = (self.url._replace(path='/api/v2/tokens/{0}/'.format(self.oauth_token_id))).geturl()

            try:
                response = self.session.open(
                    'DELETE', api_token_url,
                    validate_certs=self.verify_ssl, follow_redirects=True,
                    force_basic_auth=True, url_username=self.username, url_password=self.password
                )
                self.oauth_token_id = None
                self.authenticated = False
            except(Exception) as e:
                # Sanity check: Did the server send back some kind of internal error?
                self.warn('Failed to release tower token {0}: {1}'.format(self.oauth_token_id, e))

    def fail_json(self, **kwargs):
        # Try to logout if we are authenticated
        self.logout()
        super().fail_json(**kwargs)

    def exit_json(self, **kwargs):
        # Try to logout if we are authenticated
        self.logout()
        super().exit_json(**kwargs)
