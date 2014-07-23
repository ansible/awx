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

# Taken from https://github.com/Kami/python-extra-log-formatters

from __future__ import absolute_import

import logging

__all__ = [
    'ExtraLogFormatter'
]


class ExtraLogFormatter(logging.Formatter):
    """
    Custom log formatter which attaches all the attributes from the "extra"
    dictionary which start with an underscore to the end of the log message.

    For example:
    extra={'_id': 'user-1', '_path': '/foo/bar'}
    """
    def format(self, record):
        custom_attributes = dict([(k, v) for k, v in record.__dict__.items()
                                  if k.startswith('_')])
        custom_attributes = self._dict_to_str(custom_attributes)

        msg = logging.Formatter.format(self, record)
        msg = '%s (%s)' % (msg, custom_attributes)
        return msg

    def _dict_to_str(self, dictionary):
        result = ['%s=%s' % (k[1:], str(v)) for k, v in dictionary.items()]
        result = ','.join(result)
        return result
