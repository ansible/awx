# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import os

import yaml

try:
    import keystoneclient.auth as ksc_auth
except ImportError:
    ksc_auth = None

from os_client_config import cloud_config
from os_client_config import defaults
from os_client_config import exceptions
from os_client_config import vendors

CONFIG_HOME = os.path.join(os.path.expanduser(
    os.environ.get('XDG_CONFIG_HOME', os.path.join('~', '.config'))),
    'openstack')
CONFIG_SEARCH_PATH = [os.getcwd(), CONFIG_HOME, '/etc/openstack']
CONFIG_FILES = [
    os.path.join(d, 'clouds.yaml') for d in CONFIG_SEARCH_PATH]
CACHE_PATH = os.path.join(os.path.expanduser(
    os.environ.get('XDG_CACHE_PATH', os.path.join('~', '.cache'))),
    'openstack')
BOOL_KEYS = ('insecure', 'cache')
VENDOR_SEARCH_PATH = [os.getcwd(), CONFIG_HOME, '/etc/openstack']
VENDOR_FILES = [
    os.path.join(d, 'clouds-public.yaml') for d in VENDOR_SEARCH_PATH]


def set_default(key, value):
    defaults._defaults[key] = value


def get_boolean(value):
    if value.lower() == 'true':
        return True
    return False


def _get_os_environ():
    ret = dict(defaults._defaults)
    for (k, v) in os.environ.items():
        if k.startswith('OS_'):
            newkey = k[3:].lower()
            ret[newkey] = v
    return ret


def _auth_update(old_dict, new_dict):
    """Like dict.update, except handling the nested dict called auth."""
    for (k, v) in new_dict.items():
        if k == 'auth':
            if k in old_dict:
                old_dict[k].update(v)
            else:
                old_dict[k] = v.copy()
        else:
            old_dict[k] = v
    return old_dict


class OpenStackConfig(object):

    def __init__(self, config_files=None, vendor_files=None):
        self._config_files = config_files or CONFIG_FILES
        self._vendor_files = vendor_files or VENDOR_FILES

        self.defaults = _get_os_environ()

        # use a config file if it exists where expected
        self.cloud_config = self._load_config_file()
        if not self.cloud_config:
            self.cloud_config = dict(
                clouds=dict(openstack=dict(self.defaults)))

        self._cache_max_age = 300
        self._cache_path = CACHE_PATH
        self._cache_class = 'dogpile.cache.memory'
        self._cache_arguments = {}
        if 'cache' in self.cloud_config:
            self._cache_max_age = self.cloud_config['cache'].get(
                'max_age', self._cache_max_age)
            self._cache_path = os.path.expanduser(
                self.cloud_config['cache'].get('path', self._cache_path))
            self._cache_class = self.cloud_config['cache'].get(
                'class', self._cache_class)
            self._cache_arguments = self.cloud_config['cache'].get(
                'arguments', self._cache_arguments)

    def _load_config_file(self):
        for path in self._config_files:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return yaml.safe_load(f)

    def _load_vendor_file(self):
        for path in self._vendor_files:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return yaml.safe_load(f)

    def get_cache_max_age(self):
        return self._cache_max_age

    def get_cache_path(self):
        return self._cache_path

    def get_cache_class(self):
        return self._cache_class

    def get_cache_arguments(self):
        return self._cache_arguments

    def _get_regions(self, cloud):
        try:
            return self.cloud_config['clouds'][cloud]['region_name']
        except KeyError:
            # No region configured
            return ''

    def _get_region(self, cloud):
        return self._get_regions(cloud).split(',')[0]

    def _get_cloud_sections(self):
        return self.cloud_config['clouds'].keys()

    def _get_base_cloud_config(self, name):
        cloud = dict()

        # Only validate cloud name if one was given
        if name and name not in self.cloud_config['clouds']:
            raise exceptions.OpenStackConfigException(
                "Named cloud {name} requested that was not found.".format(
                    name=name))

        our_cloud = self.cloud_config['clouds'].get(name, dict())

        # Get the defaults (including env vars) first
        cloud.update(self.defaults)

        # yes, I know the next line looks silly
        if 'cloud' in our_cloud:
            cloud_name = our_cloud['cloud']
            vendor_file = self._load_vendor_file()
            if vendor_file and cloud_name in vendor_file['public-clouds']:
                _auth_update(cloud, vendor_file['public-clouds'][cloud_name])
            else:
                try:
                    _auth_update(cloud, vendors.CLOUD_DEFAULTS[cloud_name])
                except KeyError:
                    # Can't find the requested vendor config, go about business
                    pass

        if 'auth' not in cloud:
            cloud['auth'] = dict()

        _auth_update(cloud, our_cloud)
        if 'cloud' in cloud:
            del cloud['cloud']

        return self._fix_backwards_madness(cloud)

    def _fix_backwards_madness(self, cloud):
        cloud = self._fix_backwards_project(cloud)
        cloud = self._fix_backwards_auth_plugin(cloud)
        return cloud

    def _fix_backwards_project(self, cloud):
        # Do the lists backwards so that project_name is the ultimate winner
        mappings = {
            'project_name': ('tenant_id', 'project_id',
                             'tenant_name', 'project_name'),
        }
        for target_key, possible_values in mappings.items():
            target = None
            for key in possible_values:
                if key in cloud:
                    target = cloud[key]
                    del cloud[key]
                if key in cloud['auth']:
                    target = cloud['auth'][key]
                    del cloud['auth'][key]
            cloud['auth'][target_key] = target
        return cloud

    def _fix_backwards_auth_plugin(self, cloud):
        # Do the lists backwards so that auth_type is the ultimate winner
        mappings = {
            'auth_type': ('auth_plugin', 'auth_type'),
        }
        for target_key, possible_values in mappings.items():
            target = None
            for key in possible_values:
                if key in cloud:
                    target = cloud[key]
                    del cloud[key]
            cloud[target_key] = target
        return cloud

    def get_all_clouds(self):

        clouds = []

        for cloud in self._get_cloud_sections():
            for region in self._get_regions(cloud).split(','):
                clouds.append(self.get_one_cloud(cloud, region_name=region))
        return clouds

    def _fix_args(self, args, argparse=None):
        """Massage the passed-in options

        Replace - with _ and strip os_ prefixes.

        Convert an argparse Namespace object to a dict, removing values
        that are either None or ''.
        """

        if argparse:
            # Convert the passed-in Namespace
            o_dict = vars(argparse)
            parsed_args = dict()
            for k in o_dict:
                if o_dict[k] is not None and o_dict[k] != '':
                    parsed_args[k] = o_dict[k]
            args.update(parsed_args)

        os_args = dict()
        new_args = dict()
        for (key, val) in iter(args.items()):
            key = key.replace('-', '_')
            if key.startswith('os'):
                os_args[key[3:]] = val
            else:
                new_args[key] = val
        new_args.update(os_args)
        return new_args

    def _find_winning_auth_value(self, opt, config):
        opt_name = opt.name.replace('-', '_')
        if opt_name in config:
            return config[opt_name]
        else:
            for d_opt in opt.deprecated_opts:
                d_opt_name = d_opt.name.replace('-', '_')
                if d_opt_name in config:
                    return config[d_opt_name]

    def _validate_auth(self, config):
        # May throw a keystoneclient.exceptions.NoMatchingPlugin
        plugin_options = ksc_auth.get_plugin_class(
            config['auth_type']).get_options()

        for p_opt in plugin_options:
            # if it's in config.auth, win, kill it from config dict
            # if it's in config and not in config.auth, move it
            # deprecated loses to current
            # provided beats default, deprecated or not
            winning_value = self._find_winning_auth_value(
                p_opt, config['auth'])
            if not winning_value:
                winning_value = self._find_winning_auth_value(p_opt, config)

            # if the plugin tells us that this value is required
            # then error if it's doesn't exist now
            if not winning_value and p_opt.required:
                raise exceptions.OpenStackConfigException(
                    'Unable to find auth information for cloud'
                    ' {cloud} in config files {files}'
                    ' or environment variables. Missing value {auth_key}'
                    ' required for auth plugin {plugin}'.format(
                        cloud=cloud, files=','.join(self._config_files),
                        auth_key=p_opt.name, plugin=config.get('auth_type')))

            # Clean up after ourselves
            for opt in [p_opt.name] + [o.name for o in p_opt.deprecated_opts]:
                opt = opt.replace('-', '_')
                config.pop(opt, None)
                config['auth'].pop(opt, None)

            if winning_value:
                # Prefer the plugin configuration dest value if the value's key
                # is marked as depreciated.
                if p_opt.dest is None:
                    config['auth'][p_opt.name.replace('-', '_')] = (
                        winning_value)
                else:
                    config['auth'][p_opt.dest] = winning_value

        return config

    def get_one_cloud(self, cloud=None, validate=True,
                      argparse=None, **kwargs):
        """Retrieve a single cloud configuration and merge additional options

        :param string cloud:
            The name of the configuration to load from clouds.yaml
        :param boolean validate:
            Validate that required arguments are present and certain
            argument combinations are valid
        :param Namespace argparse:
            An argparse Namespace object; allows direct passing in of
            argparse options to be added to the cloud config.  Values
            of None and '' will be removed.
        :param kwargs: Additional configuration options
        """

        args = self._fix_args(kwargs, argparse=argparse)

        if 'region_name' not in args or args['region_name'] is None:
            args['region_name'] = self._get_region(cloud)

        config = self._get_base_cloud_config(cloud)

        # Can't just do update, because None values take over
        for (key, val) in iter(args.items()):
            if val is not None:
                config[key] = val

        for key in BOOL_KEYS:
            if key in config:
                if type(config[key]) is not bool:
                    config[key] = get_boolean(config[key])

        if 'auth_type' in config:
            if config['auth_type'] in ('', 'None', None):
                validate = False

        if validate and ksc_auth:
            config = self._validate_auth(config)

        # If any of the defaults reference other values, we need to expand
        for (key, value) in config.items():
            if hasattr(value, 'format'):
                config[key] = value.format(**config)

        return cloud_config.CloudConfig(
            name=cloud, region=config['region_name'], config=config)

if __name__ == '__main__':
    config = OpenStackConfig().get_all_clouds()
    for cloud in config:
        print(cloud.name, cloud.region, cloud.config)
