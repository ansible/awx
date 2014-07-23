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

from libcloud.utils.py3 import httplib

__all__ = [
    "LibcloudError",
    "MalformedResponseError",
    "ProviderError",
    "InvalidCredsError",
    "InvalidCredsException",
    "LazyList"
]


class LibcloudError(Exception):
    """The base class for other libcloud exceptions"""

    def __init__(self, value, driver=None):
        self.value = value
        self.driver = driver

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return ("<LibcloudError in "
                + repr(self.driver)
                + " "
                + repr(self.value) + ">")


class MalformedResponseError(LibcloudError):
    """Exception for the cases when a provider returns a malformed
    response, e.g. you request JSON and provider returns
    '<h3>something</h3>' due to some error on their side."""

    def __init__(self, value, body=None, driver=None):
        self.value = value
        self.driver = driver
        self.body = body

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return ("<MalformedResponseException in "
                + repr(self.driver)
                + " "
                + repr(self.value)
                + ">: "
                + repr(self.body))


class ProviderError(LibcloudError):
    """
    Exception used when provider gives back
    error response (HTTP 4xx, 5xx) for a request.

    Specific sub types can be derieved for errors like
    HTTP 401 : InvalidCredsError
    HTTP 404 : NodeNotFoundError, ContainerDoesNotExistError
    """

    def __init__(self, value, http_code,
                 driver=None):
        self.value = value
        self.http_code = http_code
        self.driver = driver

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return repr(self.value)


class InvalidCredsError(ProviderError):
    """Exception used when invalid credentials are used on a provider."""

    def __init__(self, value='Invalid credentials with the provider',
                 driver=None):
        super(InvalidCredsError, self).__init__(value,
                                                http_code=httplib.UNAUTHORIZED,
                                                driver=driver)


# Deprecated alias of :class:`InvalidCredsError`
InvalidCredsException = InvalidCredsError


class LazyList(object):

    def __init__(self, get_more, value_dict=None):
        self._data = []
        self._last_key = None
        self._exhausted = False
        self._all_loaded = False
        self._get_more = get_more
        self._value_dict = value_dict or {}

    def __iter__(self):
        if not self._all_loaded:
            self._load_all()

        data = self._data
        for i in data:
            yield i

    def __getitem__(self, index):
        if index >= len(self._data) and not self._all_loaded:
            self._load_all()

        return self._data[index]

    def __len__(self):
        self._load_all()
        return len(self._data)

    def __repr__(self):
        self._load_all()
        repr_string = ', ' .join([repr(item) for item in self._data])
        repr_string = '[%s]' % (repr_string)
        return repr_string

    def _load_all(self):
        while not self._exhausted:
            newdata, self._last_key, self._exhausted = \
                self._get_more(last_key=self._last_key,
                               value_dict=self._value_dict)
            self._data.extend(newdata)
        self._all_loaded = True
