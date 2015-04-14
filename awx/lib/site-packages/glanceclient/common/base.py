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

"""
Base utilities to build API operation managers and objects on top of.

DEPRECATED post v.0.12.0. Use 'glanceclient.openstack.common.apiclient.base'
instead of this module."
"""

import warnings

from glanceclient.openstack.common.apiclient import base


warnings.warn("The 'glanceclient.common.base' module is deprecated post "
              "v.0.12.0. Use 'glanceclient.openstack.common.apiclient.base' "
              "instead of this one.", DeprecationWarning)


getid = base.getid
Manager = base.ManagerWithFind
Resource = base.Resource
