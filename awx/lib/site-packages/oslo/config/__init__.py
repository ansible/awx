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

import warnings

from oslo_config import *  # noqa


def deprecated():
    new_name = __name__.replace('.', '_')
    warnings.warn(
        ('The oslo namespace package is deprecated. Please use %s instead.' %
         new_name),
        DeprecationWarning,
        stacklevel=3,
    )


deprecated()
