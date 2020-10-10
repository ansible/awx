from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves import StringIO
from ansible.module_utils.six.moves.urllib.parse import urlparse, urlencode
from ansible.module_utils.six.moves.configparser import ConfigParser, NoOptionError
from socket import gethostbyname
import re
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
    authenticated = False
    config_name = 'tower_cli.cfg'
    version_checked = False
    error_callback = None
    warn_callback = None

    def __init__(self, argument_spec=None, direct_params=None, error_callback=None, warn_callback=None, **kwargs):
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

    def build_url(self, endpoint, query_params=None):
        # Make sure we start with /api/vX
        if not endpoint.startswith("/"):
            endpoint = "/{0}".format(endpoint)
        if not endpoint.startswith("/api/"):
            endpoint = "/api/v2{0}".format(endpoint)
        if not endpoint.endswith('/') and '?' not in endpoint:
            endpoint = "{0}/".format(endpoint)

        # Update the URL path with the endpoint
        url = self.url._replace(path=endpoint)

        if query_params:
            url = url._replace(query=urlencode(query_params))

        return url

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

    def logout(self):
        # This method is intended to be overridden
        pass

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
