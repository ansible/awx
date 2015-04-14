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

from keystoneclient.auth.identity import base
from keystoneclient.auth.identity import generic
from keystoneclient.auth.identity import v2
from keystoneclient.auth.identity import v3


BaseIdentityPlugin = base.BaseIdentityPlugin

V2Password = v2.Password
V2Token = v2.Token

V3Password = v3.Password
V3Token = v3.Token

Password = generic.Password
Token = generic.Token


__all__ = ['BaseIdentityPlugin',
           'Password',
           'Token',
           'V2Password',
           'V2Token',
           'V3Password',
           'V3Token']
