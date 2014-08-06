# -*- coding: utf-8 -*-
# Copyright (c) 2012 Rackspace
# flake8: noqa
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
OpenStack Swift Python client binding.
"""
from .client import *

# At setup.py time, we haven't installed anything yet, so there
# is nothing that is able to set this version property. Squelching
# that exception here should be fine- if there are problems with
# pkg_resources in a real install, that will manifest itself as
# an error still
try:
    from swiftclient import version

    __version__ = version.version_string
except Exception:
    pass
