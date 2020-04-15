from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.urls import Request, SSLValidationError, ConnectionError
from ansible.module_utils.six import PY2
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


class AnsibleTowerException(Exception):
    def __init__(self, message, response=None):
        self.message = message
        self.response = response


class ConfigFileException(Exception):
    pass


class ItemNotDefined(Exception):
    pass


class TowerConnector:
    url = None
    honorred_settings = ('host', 'username', 'password', 'verify_ssl', 'oauth_token')
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
    warning_method = None

    def __init__(self, **kwargs):
        # See if we were given a warning method and, if so, mark it for use.
        if kwargs.get('warning_method', None) is not None:
            self.warning_method = kwargs.get('warning_method')

        # Load our config file
        self.load_config_files(**kwargs)

        # Parameters specified on command line will override settings in any config
        if kwargs.get('host', None) is not None:
            self.host = kwargs.get('host')
        if kwargs.get('username', None) is not None:
            self.username = kwargs.get('username')
        if kwargs.get('password', None) is not None:
            self.password = kwargs.get('password')
        if kwargs.get('verify_ssl', None) is not None:
            self.verify_ssl = kwargs.get('verify_ssl')
        if kwargs.get('oauth_token', None) is not None:
            self.oauth_token = kwargs.get('oauth_token')

        # Perform some basic validation
        if not self.host:
            raise AnsibleTowerException("A host must be defined")

        if not re.match('^https{0,1}://', self.host):
            self.host = "https://{0}".format(self.host)

        # Try to parse the hostname as a url
        try:
            self.url = urlparse(self.host)
        except Exception as e:
            raise AnsibleTowerException("Unable to parse tower_host as a URL ({1}): {0}".format(self.host, e))

        # Try to resolve the hostname
        hostname = self.url.netloc.split(':')[0]
        try:
            gethostbyname(hostname)
        except Exception as e:
            raise AnsibleTowerException("Unable to resolve tower_host ({1}): {0}".format(hostname, e))

        self.session = Request(cookies=CookieJar(), validate_certs=self.verify_ssl)

    def do_warn(self, message):
        if self.warning_method:
            self.warning_method(message)
        # What to do if there is a warning
        pass

    def load_config_files(self, **kwargs):
        # Load configs like TowerCLI would have from least import to most
        config_files = ['/etc/tower/tower_cli.cfg', join(expanduser("~"), ".{0}".format(self.config_name))]
        local_dir = getcwd()
        config_files.append(join(local_dir, self.config_name))
        while split(local_dir)[1]:
            local_dir = split(local_dir)[0]
            config_files.insert(2, join(local_dir, ".{0}".format(self.config_name)))

        for config_file in config_files:
            if exists(config_file) and not isdir(config_file):
                # Only throw a formatting error if the file exists and is not a directory
                try:
                    self.load_config(config_file, warn_on_dupes=False, **kwargs)
                except ConfigFileException:
                    raise AnsibleTowerException('The config file {0} is not properly formatted'.format(config_file))

        # If we have a specified  tower config, load it
        if kwargs.get('tower_config_file', None):
            try:
                # TODO: warn if there are conflicts with other params
                self.load_config(kwargs.get('tower_config_file'), warn_on_dupes=True, **kwargs)
            except ConfigFileException as cfe:
                # Since we were told specifically to load this we want it to fail if we have an error
                raise AnsibleTowerException(cfe)

    def load_config(self, config_path, warn_on_dupes=False, **kwargs):
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
            config_data = yaml.load(config_string, Loader=yaml.SafeLoader)
            # If this is an actual ini file, yaml will return the whole thing as a string instead of a dict
            if type(config_data) is not dict:
                raise AssertionError("The yaml config file is not properly formatted as a dict.")

        except(AttributeError, yaml.YAMLError, AssertionError):
            # TowerCLI used to support a config file with a missing [general] section by prepending it if missing
            if '[general]' not in config_string:
                config_string = '[general]{0}'.format(config_string)

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
                for honorred_setting in self.honorred_settings:
                    try:
                        config_data[honorred_setting] = config.get('general', honorred_setting)
                    except (NoOptionError):
                        pass

            except Exception as e:
                raise ConfigFileException("An unknown exception occured trying to ini load config file: {0}".format(e))

        except Exception as e:
            raise ConfigFileException("An unknown exception occured trying to load config file: {0}".format(e))

        # If we made it here, we have a dict which has values in it from our config, any final settings logic can be performed here
        duplicated_params = []
        for honorred_setting in self.honorred_settings:
            if honorred_setting in config_data:
                if kwargs.get(honorred_setting, None):
                    duplicated_params.append(honorred_setting)

                # Veriffy SSL must be a boolean
                if honorred_setting == 'verify_ssl':
                    if type(config_data[honorred_setting]) is str:
                        setattr(self, honorred_setting, strtobool(config_data[honorred_setting]))
                    else:
                        setattr(self, honorred_setting, bool(config_data[honorred_setting]))
                else:
                    setattr(self, honorred_setting, config_data[honorred_setting])

        if warn_on_dupes and duplicated_params:
            self.do_warn((
                'The parameter(s) {0} were found in the specified tower_config_file file but their values were also set as parameters. '
                'The parameter will take precedence.'
            ).format(', '.join(duplicated_params)))

    def make_request(self, method, endpoint, *args, **kwargs):
        # In case someone is calling us directly; make sure we were given a method, let's not just assume a GET
        if not method:
            raise AnsibleTowerException("The HTTP method must be defined")

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
            raise AnsibleTowerException("Could not establish a secure connection to your host ({1}): {0}.".format(self.url.netloc, ssl_err))
        except(ConnectionError) as con_err:
            raise AnsibleTowerException("There was a network error of some kind trying to connect to your host ({1}): {0}.".format(self.url.netloc, con_err))
        except(HTTPError) as he:
            # Sanity check: Did the server send back some kind of internal error?
            if he.code >= 500:
                raise AnsibleTowerException(
                    'The host sent back a server error ({1}): {0}. Please check the logs and try again later'.format(self.url.path, he),
                    he
                )
            # Sanity check: Did we fail to authenticate properly?  If so, fail out now; this is always a failure.
            elif he.code == 401:
                raise AnsibleTowerException('Invalid Tower authentication credentials for {0} (HTTP 401).'.format(self.url.path), he)
            # Sanity check: Did we get a forbidden response, which means that the user isn't allowed to do this? Report that.
            elif he.code == 403:
                raise AnsibleTowerException("You don't have permission to {1} to {0} (HTTP 403).".format(self.url.path, method), he)
            # Sanity check: Did we get a 404 response?
            # Requests with primary keys will return a 404 if there is no response, and we want to consistently trap these.
            elif he.code == 404:
                if kwargs.get('return_none_on_404', False):
                    return None
                raise AnsibleTowerException('The requested object could not be found at {0}.'.format(self.url.path), he)
            # Sanity check: Did we get a 405 response?
            # A 405 means we used a method that isn't allowed. Usually this is a bad request, but it requires special treatment because the
            # API sends it as a logic error in a few situations (e.g. trying to cancel a job that isn't running).
            elif he.code == 405:
                raise AnsibleTowerException(
                    "The Tower server says you can't make a request with the {0} method to this endpoing {1}".format(method, self.url.path),
                    he
                )
            # Sanity check: Did we get some other kind of error?  If so, write an appropriate error message.
            elif he.code >= 400:
                # We are going to return a 400 so the module can decide what to do with it
                page_data = he.read()
                try:
                    return {'status_code': he.code, 'json': loads(page_data)}
                # JSONDecodeError only available on Python 3.5+
                except ValueError:
                    raise AnsibleTowerException("Recieved an unparsable 400 error from tower, see request", he)
            elif he.code == 204 and method == 'DELETE':
                # A 204 is a normal response for a delete function
                pass
            else:
                raise AnsibleTowerException("Unexpected return code when calling {0}: {1}".format(self.url.geturl(), he.code), he)
        except(Exception) as e:
            raise AnsibleTowerException("There was an unknown error when trying to connect to {2}: {0} {1}".format(type(e).__name__, e, self.url.geturl()))
        finally:
            self.url = self.url._replace(query=None)

        response_body = ''
        try:
            response_body = response.read()
        except(Exception) as e:
            raise AnsibleTowerException("Failed to read response body: {0}".format(e), response)

        response_json = {}
        if response_body and response_body != '':
            try:
                response_json = loads(response_body)
            except(Exception) as e:
                raise AnsibleTowerException("Failed to parse the response json: {0}".format(e), response)

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
                raise AnsibleTowerException('Failed to get token: {0}'.format(he), resp)
            except(Exception) as e:
                # Sanity check: Did the server send back some kind of internal error?
                raise AnsibleTowerException('Failed to get token: {0}'.format(e))

            token_response = None
            try:
                token_response = response.read()
                response_json = loads(token_response)
                self.oauth_token_id = response_json['id']
                self.oauth_token = response_json['token']
            except(Exception) as e:
                raise AnsibleTowerException("Failed to extract token information from login response: {0}".format(e), token_response)

        # If we have neither of these, then we can try un-authenticated access
        self.authenticated = True

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
                self.do_warn('Failed to release tower token: {0}, response: {1}'.format(he, resp))
            except(Exception) as e:
                # Sanity check: Did the server send back some kind of internal error?
                self.do_warn('Failed to release tower token {0}: {1}'.format(self.oauth_token_id, e))
