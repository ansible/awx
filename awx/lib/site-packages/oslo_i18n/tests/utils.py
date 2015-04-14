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

import six


class SomeObject(object):

    def __init__(self, message):
        self.message = message

    def __unicode__(self):
        return self.message
    # alias for Python 3
    __str__ = __unicode__


class NoDeepCopyObject(object):

    def __init__(self, value):
        self.value = value

    if six.PY3:
        def __str__(self):
            return str(self.value)
    else:
        def __unicode__(self):
            return unicode(self.value)

    def __deepcopy__(self, memo):
        raise TypeError('Deep Copy not supported')
