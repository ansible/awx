# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
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

from glanceclient.common import utils


def Client(version=None, endpoint=None, *args, **kwargs):
    if version is not None:
        warnings.warn(("`version` keyword is being deprecated. Please pass the"
                       " version as part of the URL. "
                       "http://$HOST:$PORT/v$VERSION_NUMBER"),
                      DeprecationWarning)

    endpoint, url_version = utils.strip_version(endpoint)

    if not url_version and not version:
        msg = ("Please provide either the version or an url with the form "
               "http://$HOST:$PORT/v$VERSION_NUMBER")
        raise RuntimeError(msg)

    version = int(version or url_version)

    module = utils.import_versioned_module(version, 'client')
    client_class = getattr(module, 'Client')
    return client_class(endpoint, *args, **kwargs)
