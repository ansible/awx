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


from keystoneclient.auth.base import *  # noqa
from keystoneclient.auth.cli import *  # noqa
from keystoneclient.auth.conf import *  # noqa


__all__ = [
    # auth.base
    'AUTH_INTERFACE',
    'BaseAuthPlugin',
    'get_plugin_class',
    'IDENTITY_AUTH_HEADER_NAME',
    'PLUGIN_NAMESPACE',

    # auth.cli
    'load_from_argparse_arguments',
    'register_argparse_arguments',

    # auth.conf
    'get_common_conf_options',
    'get_plugin_options',
    'load_from_conf_options',
    'register_conf_options',
]
