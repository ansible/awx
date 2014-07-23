# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import warnings

__all__ = [
    'SHOW_DEPRECATION_WARNING',
    'SHOW_IN_DEVELOPMENT_WARNING',
    'OLD_API_REMOVE_VERSION',
    'deprecated_warning',
    'in_development_warning'
]


SHOW_DEPRECATION_WARNING = True
SHOW_IN_DEVELOPMENT_WARNING = True
OLD_API_REMOVE_VERSION = '0.7.0'


def deprecated_warning(module):
    if SHOW_DEPRECATION_WARNING:
        warnings.warn('This path has been deprecated and the module'
                      ' is now available at "libcloud.compute.%s".'
                      ' This path will be fully removed in libcloud %s.' %
                      (module, OLD_API_REMOVE_VERSION),
                      category=DeprecationWarning)


def in_development_warning(module):
    if SHOW_IN_DEVELOPMENT_WARNING:
        warnings.warn('The module %s is in development and your are advised '
                      'against using it in production.' % (module),
                      category=FutureWarning)
