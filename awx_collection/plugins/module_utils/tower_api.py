from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.urls import Request, SSLValidationError, ConnectionError
from ansible.module_utils.six import PY2, string_types
from ansible.module_utils.six.moves import StringIO
from ansible.module_utils.six.moves.urllib.parse import urlparse, urlencode
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.six.moves.http_cookiejar import CookieJar
from ansible.module_utils.six.moves.configparser import ConfigParser, NoOptionError
from socket import gethostbyname
import re
from json import loads, dumps
from os.path import isfile, expanduser, split, join, exists, isdir
from os import access, R_OK, getcwd
from distutils.util import strtobool

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class ConfigFileException(Exception):
    pass


class ItemNotDefined(Exception):
    pass


class TowerModule(AnsibleModule):
    # This gets set by the make process so whatever is in here is irrelevant
    _COLLECTION_VERSION = "0.0.1-devel"
    _COLLECTION_TYPE = "awx"
    # This maps the collections type (awx/tower) to the values returned by the API
    # Those values can be found in awx/api/generics.py line 204
    collection_to_version = {
        'awx': 'AWX',
        'tower': 'Red Hat Ansible Tower',
    }
    url = None
    AUTH_ARGSPEC = dict(
        tower_host=dict(required=False, fallback=(env_fallback, ['TOWER_HOST'])),
        tower_username=dict(required=False, fallback=(env_fallback, ['TOWER_USERNAME'])),
        tower_password=dict(no_log=True, required=False, fallback=(env_fallback, ['TOWER_PASSWORD'])),
        validate_certs=dict(type='bool', aliases=['tower_verify_ssl'], required=False, fallback=(env_fallback, ['TOWER_VERIFY_SSL'])),
        tower_oauthtoken=dict(type='raw', no_log=True, required=False, fallback=(env_fallback, ['TOWER_OAUTH_TOKEN'])),
        tower_config_file=dict(type='path', required=False, default=None),
    )
    short_params = {
        'host': 'tower_host',
        'username': 'tower_username',
        'password': 'tower_password',
        'verify_ssl': 'validate_certs',
        'oauth_token': 'tower_oauthtoken',
    }
    host = '127.0.0.1'
    username = None
    password = None
    verify_ssl = True
    oauth_token = None
    oauth_token_id = None
    session = None
    cookie_jar = CookieJar()
    authenticated = False
    config_name = 'tower_cli.cfg'
    ENCRYPTED_STRING = "$encrypted$"
    version_checked = False
    error_callback = None
    warn_callback = None

    def __init__(self, argument_spec, direct_params=None, error_callback=None, warn_callback=None, **kwargs):
        full_argspec = {}
        full_argspec.update(TowerModule.AUTH_ARGSPEC)
        full_argspec.update(argument_spec)
        kwargs['supports_check_mode'] = True

        self.error_callback = error_callback
        self.warn_callback = warn_callback

        self.json_output = {'changed': False}

        if direct_params is not None:
            self.params = direct_params
        else:
            super(TowerModule, self).__init__(argument_spec=full_argspec, **kwargs)

        self.load_config_files()

        # Parameters specified on command line will override settings in any config
        for short_param, long_param in self.short_params.items():
            direct_value = self.params.get(long_param)
            if direct_value is not None:
                setattr(self, short_param, direct_value)

        # Perform magic depending on whether tower_oauthtoken is a string or a dict
        if self.params.get('tower_oauthtoken'):
            token_param = self.params.get('tower_oauthtoken')
            if type(token_param) is dict:
                if 'token' in token_param:
                    self.oauth_token = self.params.get('tower_oauthtoken')['token']
                else:
                    self.fail_json(msg="The provided dict in tower_oauthtoken did not properly contain the token entry")
            elif isinstance(token_param, string_types):
                self.oauth_token = self.params.get('tower_oauthtoken')
            else:
                error_msg = "The provided tower_oauthtoken type was not valid ({0}). Valid options are str or dict.".format(type(token_param).__name__)
                self.fail_json(msg=error_msg)

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

        self.session = Request(cookies=CookieJar(), validate_certs=self.verify_ssl)

    def load_config_files(self):
        # Load configs like TowerCLI would have from least import to most
        config_files = ['/etc/tower/tower_cli.cfg', join(expanduser("~"), ".{0}".format(self.config_name))]
        local_dir = getcwd()
        config_files.append(join(local_dir, self.config_name))
        while split(local_dir)[1]:
            local_dir = split(local_dir)[0]
            config_files.insert(2, join(local_dir, ".{0}".format(self.config_name)))

        # If we have a specified  tower config, load it
        if self.params.get('tower_config_file'):
            duplicated_params = [
                fn for fn in self.AUTH_ARGSPEC
                if fn != 'tower_config_file' and self.params.get(fn) is not None
            ]
            if duplicated_params:
                self.warn((
                    'The parameter(s) {0} were provided at the same time as tower_config_file. '
                    'Precedence may be unstable, we suggest either using config file or params.'
                ).format(', '.join(duplicated_params)))
            try:
                # TODO: warn if there are conflicts with other params
                self.load_config(self.params.get('tower_config_file'))
            except ConfigFileException as cfe:
                # Since we were told specifically to load this we want it to fail if we have an error
                self.fail_json(msg=cfe)
        else:
            for config_file in config_files:
                if exists(config_file) and not isdir(config_file):
                    # Only throw a formatting error if the file exists and is not a directory
                    try:
                        self.load_config(config_file)
                    except ConfigFileException:
                        self.fail_json(msg='The config file {0} is not properly formatted'.format(config_file))

    def load_config(self, config_path):
        # Validate the config file is an actual file
        if not isfile(config_path):
            raise ConfigFileException('The specified config file does not exist')

        if not access(config_path, R_OK):
            raise ConfigFileException("The specified config file cannot be read")

        # Read in the file contents:
        with open(config_path, 'r') as f:
            config_string = f.read()

        # First try to yaml load the content (which will also load json)
        try:
            try_config_parsing = True
            if HAS_YAML:
                try:
                    config_data = yaml.load(config_string, Loader=yaml.SafeLoader)
                    # If this is an actual ini file, yaml will return the whole thing as a string instead of a dict
                    if type(config_data) is not dict:
                        raise AssertionError("The yaml config file is not properly formatted as a dict.")
                    try_config_parsing = False

                except(AttributeError, yaml.YAMLError, AssertionError):
                    try_config_parsing = True

            if try_config_parsing:
                # TowerCLI used to support a config file with a missing [general] section by prepending it if missing
                if '[general]' not in config_string:
                    config_string = '[general]\n{0}'.format(config_string)

                config = ConfigParser()

                try:
                    placeholder_file = StringIO(config_string)
                    # py2 ConfigParser has readfp, that has been deprecated in favor of read_file in py3
                    # This "if" removes the deprecation warning
                    if hasattr(config, 'read_file'):
                        config.read_file(placeholder_file)
                    else:
                        config.readfp(placeholder_file)

                    # If we made it here then we have values from reading the ini file, so let's pull them out into a dict
                    config_data = {}
                    for honorred_setting in self.short_params:
                        try:
                            config_data[honorred_setting] = config.get('general', honorred_setting)
                        except NoOptionError:
                            pass

                except Exception as e:
                    raise ConfigFileException("An unknown exception occured trying to ini load config file: {0}".format(e))

        except Exception as e:
            raise ConfigFileException("An unknown exception occured trying to load config file: {0}".format(e))

        # If we made it here, we have a dict which has values in it from our config, any final settings logic can be performed here
        for honorred_setting in self.short_params:
            if honorred_setting in config_data:
                # Veriffy SSL must be a boolean
                if honorred_setting == 'verify_ssl':
                    if type(config_data[honorred_setting]) is str:
                        setattr(self, honorred_setting, strtobool(config_data[honorred_setting]))
                    else:
                        setattr(self, honorred_setting, bool(config_data[honorred_setting]))
                else:
                    setattr(self, honorred_setting, config_data[honorred_setting])

    @staticmethod
    def param_to_endpoint(name):
        exceptions = {
            'inventory': 'inventories',
            'target_team': 'teams',
            'workflow': 'workflow_job_templates'
        }
        return exceptions.get(name, '{0}s'.format(name))

    def head_endpoint(self, endpoint, *args, **kwargs):
        return self.make_request('HEAD', endpoint, **kwargs)

    def get_endpoint(self, endpoint, *args, **kwargs):
        return self.make_request('GET', endpoint, **kwargs)

    def patch_endpoint(self, endpoint, *args, **kwargs):
        # Handle check mode
        if self.check_mode:
            self.json_output['changed'] = True
            self.exit_json(**self.json_output)

        return self.make_request('PATCH', endpoint, **kwargs)

    def post_endpoint(self, endpoint, *args, **kwargs):
        # Handle check mode
        if self.check_mode:
            self.json_output['changed'] = True
            self.exit_json(**self.json_output)

        return self.make_request('POST', endpoint, **kwargs)

    def delete_endpoint(self, endpoint, *args, **kwargs):
        # Handle check mode
        if self.check_mode:
            self.json_output['changed'] = True
            self.exit_json(**self.json_output)

        return self.make_request('DELETE', endpoint, **kwargs)

    def get_all_endpoint(self, endpoint, *args, **kwargs):
        response = self.get_endpoint(endpoint, *args, **kwargs)
        if 'next' not in response['json']:
            raise RuntimeError('Expected list from API at {0}, got: {1}'.format(endpoint, response))
        next_page = response['json']['next']

        if response['json']['count'] > 10000:
            self.fail_json(msg='The number of items being queried for is higher than 10,000.')

        while next_page is not None:
            next_response = self.get_endpoint(next_page)
            response['json']['results'] = response['json']['results'] + next_response['json']['results']
            next_page = next_response['json']['next']
            response['json']['next'] = next_page
        return response

    def get_one(self, endpoint, *args, **kwargs):
        response = self.get_endpoint(endpoint, *args, **kwargs)
        if response['status_code'] != 200:
            fail_msg = "Got a {0} response when trying to get one from {1}".format(response['status_code'], endpoint)
            if 'detail' in response.get('json', {}):
                fail_msg += ', detail: {0}'.format(response['json']['detail'])
            self.fail_json(msg=fail_msg)

        if 'count' not in response['json'] or 'results' not in response['json']:
            self.fail_json(msg="The endpoint did not provide count and results")

        if response['json']['count'] == 0:
            return None
        elif response['json']['count'] > 1:
            self.fail_json(msg="An unexpected number of items was returned from the API ({0})".format(response['json']['count']))

        return response['json']['results'][0]

    def resolve_name_to_id(self, endpoint, name_or_id):
        # Try to resolve the object by name
        name_field = 'name'
        if endpoint == 'users':
            name_field = 'username'

        response = self.get_endpoint(endpoint, **{'data': {name_field: name_or_id}})
        if response['status_code'] == 400:
            self.fail_json(msg="Unable to try and resolve {0} for {1} : {2}".format(endpoint, name_or_id, response['json']['detail']))

        if response['json']['count'] == 1:
            return response['json']['results'][0]['id']
        elif response['json']['count'] == 0:
            try:
                int(name_or_id)
                # If we got 0 items by name, maybe they gave us an ID, let's try looking it up by ID
                response = self.head_endpoint("{0}/{1}".format(endpoint, name_or_id), **{'return_none_on_404': True})
                if response is not None:
                    return name_or_id
            except ValueError:
                # If we got a value error than we didn't have an integer so we can just pass and fall down to the fail
                pass

            self.fail_json(msg="The {0} {1} was not found on the Tower server".format(endpoint, name_or_id))
        else:
            self.fail_json(msg="Found too many names {0} at endpoint {1} try using an ID instead of a name".format(name_or_id, endpoint))

    def make_request(self, method, endpoint, *args, **kwargs):
        # In case someone is calling us directly; make sure we were given a method, let's not just assume a GET
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

        # Authenticate to Tower (if we don't have a token and if not already done so)
        if not self.oauth_token and not self.authenticated:
            # This method will set a cookie in the cookie jar for us and also an oauth_token
            self.authenticate(**kwargs)
        if self.oauth_token:
            # If we have a oauth token, we just use a bearer header
            headers['Authorization'] = 'Bearer {0}'.format(self.oauth_token)

        # Update the URL path with the endpoint
        self.url = self.url._replace(path=endpoint)

        if method in ['POST', 'PUT', 'PATCH']:
            headers.setdefault('Content-Type', 'application/json')
            kwargs['headers'] = headers
        elif kwargs.get('data'):
            self.url = self.url._replace(query=urlencode(kwargs.get('data')))

        data = None  # Important, if content type is not JSON, this should not be dict type
        if headers.get('Content-Type', '') == 'application/json':
            data = dumps(kwargs.get('data', {}))

        try:
            response = self.session.open(method, self.url.geturl(), headers=headers, validate_certs=self.verify_ssl, follow_redirects=True, data=data)
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
                if kwargs.get('return_none_on_404', False):
                    return None
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
            elif he.code == 204 and method == 'DELETE':
                # A 204 is a normal response for a delete function
                pass
            else:
                self.fail_json(msg="Unexpected return code when calling {0}: {1}".format(self.url.geturl(), he))
        except(Exception) as e:
            self.fail_json(msg="There was an unknown error when trying to connect to {2}: {0} {1}".format(type(e).__name__, e, self.url.geturl()))
        finally:
            self.url = self.url._replace(query=None)

        if not self.version_checked:
            # In PY2 we get back an HTTPResponse object but PY2 is returning an addinfourl
            # First try to get the headers in PY3 format and then drop down to PY2.
            try:
                tower_type = response.getheader('X-API-Product-Name', None)
                tower_version = response.getheader('X-API-Product-Version', None)
            except Exception:
                tower_type = response.info().getheader('X-API-Product-Name', None)
                tower_version = response.info().getheader('X-API-Product-Version', None)

            if self._COLLECTION_TYPE not in self.collection_to_version or self.collection_to_version[self._COLLECTION_TYPE] != tower_type:
                self.warn("You are using the {0} version of this collection but connecting to {1}".format(
                    self._COLLECTION_TYPE, tower_type
                ))
            elif self._COLLECTION_VERSION != tower_version:
                self.warn("You are running collection version {0} but connecting to tower version {1}".format(
                    self._COLLECTION_VERSION, tower_version
                ))
            self.version_checked = True

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

        if PY2:
            status_code = response.getcode()
        else:
            status_code = response.status
        return {'status_code': status_code, 'json': response_json}

    def authenticate(self, **kwargs):
        if self.username and self.password:
            # Attempt to get a token from /api/v2/tokens/ by giving it our username/password combo
            # If we have a username and password, we need to get a session cookie
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
            except HTTPError as he:
                try:
                    resp = he.read()
                except Exception as e:
                    resp = 'unknown {0}'.format(e)
                self.fail_json(msg='Failed to get token: {0}'.format(he), response=resp)
            except(Exception) as e:
                # Sanity check: Did the server send back some kind of internal error?
                self.fail_json(msg='Failed to get token: {0}'.format(e))

            token_response = None
            try:
                token_response = response.read()
                response_json = loads(token_response)
                self.oauth_token_id = response_json['id']
                self.oauth_token = response_json['token']
            except(Exception) as e:
                self.fail_json(msg="Failed to extract token information from login response: {0}".format(e), **{'response': token_response})

        # If we have neither of these, then we can try un-authenticated access
        self.authenticated = True

    def delete_if_needed(self, existing_item, on_delete=None):
        # This will exit from the module on its own.
        # If the method successfully deletes an item and on_delete param is defined,
        #   the on_delete parameter will be called as a method pasing in this object and the json from the response
        # This will return one of two things:
        #   1. None if the existing_item is not defined (so no delete needs to happen)
        #   2. The response from Tower from calling the delete on the endpont. It's up to you to process the response and exit from the module
        # Note: common error codes from the Tower API can cause the module to fail
        if existing_item:
            # If we have an item, we can try to delete it
            try:
                item_url = existing_item['url']
                item_type = existing_item['type']
                item_id = existing_item['id']
            except KeyError as ke:
                self.fail_json(msg="Unable to process delete of item due to missing data {0}".format(ke))

            if 'name' in existing_item:
                item_name = existing_item['name']
            elif 'username' in existing_item:
                item_name = existing_item['username']
            elif 'identifier' in existing_item:
                item_name = existing_item['identifier']
            elif item_type == 'o_auth2_access_token':
                # An oauth2 token has no name, instead we will use its id for any of the messages
                item_name = existing_item['id']
            elif item_type == 'credential_input_source':
                # An credential_input_source has no name, instead we will use its id for any of the messages
                item_name = existing_item['id']
            else:
                self.fail_json(msg="Unable to process delete of {0} due to missing name".format(item_type))

            response = self.delete_endpoint(item_url)

            if response['status_code'] in [202, 204]:
                if on_delete:
                    on_delete(self, response['json'])
                self.json_output['changed'] = True
                self.json_output['id'] = item_id
                self.exit_json(**self.json_output)
            else:
                if 'json' in response and '__all__' in response['json']:
                    self.fail_json(msg="Unable to delete {0} {1}: {2}".format(item_type, item_name, response['json']['__all__'][0]))
                elif 'json' in response:
                    # This is from a project delete (if there is an active job against it)
                    if 'error' in response['json']:
                        self.fail_json(msg="Unable to delete {0} {1}: {2}".format(item_type, item_name, response['json']['error']))
                    else:
                        self.fail_json(msg="Unable to delete {0} {1}: {2}".format(item_type, item_name, response['json']))
                else:
                    self.fail_json(msg="Unable to delete {0} {1}: {2}".format(item_type, item_name, response['status_code']))
        else:
            self.exit_json(**self.json_output)

    def modify_associations(self, association_endpoint, new_association_list):
        # if we got None instead of [] we are not modifying the association_list
        if new_association_list is None:
            return

        # First get the existing associations
        response = self.get_all_endpoint(association_endpoint)
        existing_associated_ids = [association['id'] for association in response['json']['results']]

        # Disassociate anything that is in existing_associated_ids but not in new_association_list
        ids_to_remove = list(set(existing_associated_ids) - set(new_association_list))
        for an_id in ids_to_remove:
            response = self.post_endpoint(association_endpoint, **{'data': {'id': int(an_id), 'disassociate': True}})
            if response['status_code'] == 204:
                self.json_output['changed'] = True
            else:
                self.fail_json(msg="Failed to disassociate item {0}".format(response['json']['detail']))

        # Associate anything that is in new_association_list but not in `association`
        for an_id in list(set(new_association_list) - set(existing_associated_ids)):
            response = self.post_endpoint(association_endpoint, **{'data': {'id': int(an_id)}})
            if response['status_code'] == 204:
                self.json_output['changed'] = True
            else:
                self.fail_json(msg="Failed to associate item {0}".format(response['json']['detail']))

    def create_if_needed(self, existing_item, new_item, endpoint, on_create=None, item_type='unknown', associations=None):

        # This will exit from the module on its own
        # If the method successfully creates an item and on_create param is defined,
        #    the on_create parameter will be called as a method pasing in this object and the json from the response
        # This will return one of two things:
        #    1. None if the existing_item is already defined (so no create needs to happen)
        #    2. The response from Tower from calling the patch on the endpont. It's up to you to process the response and exit from the module
        # Note: common error codes from the Tower API can cause the module to fail

        if not endpoint:
            self.fail_json(msg="Unable to create new {0} due to missing endpoint".format(item_type))

        item_url = None
        if existing_item:
            try:
                item_url = existing_item['url']
            except KeyError as ke:
                self.fail_json(msg="Unable to process create of item due to missing data {0}".format(ke))
        else:
            # If we don't have an exisitng_item, we can try to create it

            # We have to rely on item_type being passed in since we don't have an existing item that declares its type
            # We will pull the item_name out from the new_item, if it exists
            for key in ('name', 'username', 'identifier', 'hostname'):
                if key in new_item:
                    item_name = new_item[key]
                    break
            else:
                item_name = 'unknown'

            response = self.post_endpoint(endpoint, **{'data': new_item})
            if response['status_code'] == 201:
                self.json_output['name'] = 'unknown'
                for key in ('name', 'username', 'identifier', 'hostname'):
                    if key in response['json']:
                        self.json_output['name'] = response['json'][key]
                self.json_output['id'] = response['json']['id']
                self.json_output['changed'] = True
                item_url = response['json']['url']
            else:
                if 'json' in response and '__all__' in response['json']:
                    self.fail_json(msg="Unable to create {0} {1}: {2}".format(item_type, item_name, response['json']['__all__'][0]))
                elif 'json' in response:
                    self.fail_json(msg="Unable to create {0} {1}: {2}".format(item_type, item_name, response['json']))
                else:
                    self.fail_json(msg="Unable to create {0} {1}: {2}".format(item_type, item_name, response['status_code']))

        # Process any associations with this item
        if associations is not None:
            for association_type in associations:
                sub_endpoint = '{0}{1}/'.format(item_url, association_type)
                self.modify_associations(sub_endpoint, associations[association_type])

        # If we have an on_create method and we actually changed something we can call on_create
        if on_create is not None and self.json_output['changed']:
            on_create(self, response['json'])
        else:
            self.exit_json(**self.json_output)

    def _encrypted_changed_warning(self, field, old, warning=False):
        if not warning:
            return
        self.warn(
            'The field {0} of {1} {2} has encrypted data and may inaccurately report task is changed.'.format(
                field, old.get('type', 'unknown'), old.get('id', 'unknown')
            ))

    @staticmethod
    def has_encrypted_values(obj):
        """Returns True if JSON-like python content in obj has $encrypted$
        anywhere in the data as a value
        """
        if isinstance(obj, dict):
            for val in obj.values():
                if TowerModule.has_encrypted_values(val):
                    return True
        elif isinstance(obj, list):
            for val in obj:
                if TowerModule.has_encrypted_values(val):
                    return True
        elif obj == TowerModule.ENCRYPTED_STRING:
            return True
        return False

    def objects_could_be_different(self, old, new, field_set=None, warning=False):
        if field_set is None:
            field_set = set(fd for fd in new.keys() if fd not in ('modified', 'related', 'summary_fields'))
        for field in field_set:
            new_field = new.get(field, None)
            old_field = old.get(field, None)
            if old_field != new_field:
                return True  # Something doesn't match
            elif self.has_encrypted_values(new_field) or field not in new:
                # case of 'field not in new' - user password write-only field that API will not display
                self._encrypted_changed_warning(field, old, warning=warning)
                return True
        return False

    def update_if_needed(self, existing_item, new_item, on_update=None, associations=None):
        # This will exit from the module on its own
        # If the method successfully updates an item and on_update param is defined,
        #   the on_update parameter will be called as a method pasing in this object and the json from the response
        # This will return one of three things:
        #    1. None if the existing_item does not need to be updated
        #    2. The response from Tower from patching to the endpoint. It's up to you to process the response and exit from the module.
        #    3. An ItemNotDefined exception, if the existing_item does not exist
        # Note: common error codes from the Tower API can cause the module to fail
        response = None
        if existing_item:

            # If we have an item, we can see if it needs an update
            try:
                item_url = existing_item['url']
                item_type = existing_item['type']
                if item_type == 'user':
                    item_name = existing_item['username']
                elif item_type == 'workflow_job_template_node':
                    item_name = existing_item['identifier']
                elif item_type == 'credential_input_source':
                    item_name = existing_item['id']
                else:
                    item_name = existing_item['name']
                item_id = existing_item['id']
            except KeyError as ke:
                self.fail_json(msg="Unable to process update of item due to missing data {0}".format(ke))

            # Check to see if anything within the item requires the item to be updated
            needs_patch = self.objects_could_be_different(existing_item, new_item)

            # If we decided the item needs to be updated, update it
            self.json_output['id'] = item_id
            if needs_patch:
                response = self.patch_endpoint(item_url, **{'data': new_item})
                if response['status_code'] == 200:
                    # compare apples-to-apples, old API data to new API data
                    # but do so considering the fields given in parameters
                    self.json_output['changed'] = self.objects_could_be_different(
                        existing_item, response['json'], field_set=new_item.keys(), warning=True)
                elif 'json' in response and '__all__' in response['json']:
                    self.fail_json(msg=response['json']['__all__'])
                else:
                    self.fail_json(**{'msg': "Unable to update {0} {1}, see response".format(item_type, item_name), 'response': response})

        else:
            raise RuntimeError('update_if_needed called incorrectly without existing_item')

        # Process any associations with this item
        if associations is not None:
            for association_type, id_list in associations.items():
                endpoint = '{0}{1}/'.format(item_url, association_type)
                self.modify_associations(endpoint, id_list)

        # If we change something and have an on_change call it
        if on_update is not None and self.json_output['changed']:
            if response is None:
                last_data = existing_item
            else:
                last_data = response['json']
            on_update(self, last_data)
        else:
            self.exit_json(**self.json_output)

    def create_or_update_if_needed(self, existing_item, new_item, endpoint=None, item_type='unknown', on_create=None, on_update=None, associations=None):
        if existing_item:
            return self.update_if_needed(existing_item, new_item, on_update=on_update, associations=associations)
        else:
            return self.create_if_needed(existing_item, new_item, endpoint, on_create=on_create, item_type=item_type, associations=associations)

    def logout(self):
        if self.authenticated:
            # Attempt to delete our current token from /api/v2/tokens/
            # Post to the tokens endpoint with baisc auth to try and get a token
            api_token_url = (
                self.url._replace(
                    path='/api/v2/tokens/{0}/'.format(self.oauth_token_id),
                    query=None  # in error cases, fail_json exists before exception handling
                )
            ).geturl()

            try:
                self.session.open(
                    'DELETE',
                    api_token_url,
                    validate_certs=self.verify_ssl,
                    follow_redirects=True,
                    force_basic_auth=True,
                    url_username=self.username,
                    url_password=self.password
                )
                self.oauth_token_id = None
                self.authenticated = False
            except HTTPError as he:
                try:
                    resp = he.read()
                except Exception as e:
                    resp = 'unknown {0}'.format(e)
                self.warn('Failed to release tower token: {0}, response: {1}'.format(he, resp))
            except(Exception) as e:
                # Sanity check: Did the server send back some kind of internal error?
                self.warn('Failed to release tower token {0}: {1}'.format(self.oauth_token_id, e))

    def fail_json(self, **kwargs):
        # Try to log out if we are authenticated
        self.logout()
        if self.error_callback:
            self.error_callback(**kwargs)
        else:
            super(TowerModule, self).fail_json(**kwargs)

    def exit_json(self, **kwargs):
        # Try to log out if we are authenticated
        self.logout()
        super(TowerModule, self).exit_json(**kwargs)

    def warn(self, warning):
        if self.warn_callback is not None:
            self.warn_callback(warning)
        else:
            super(TowerModule, self).warn(warning)

    def is_job_done(self, job_status):
        if job_status in ['new', 'pending', 'waiting', 'running']:
            return False
        else:
            return True
