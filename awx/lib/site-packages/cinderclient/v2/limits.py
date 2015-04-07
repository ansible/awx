# Copyright 2013 OpenStack Foundation
#
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

from cinderclient import base


class Limits(base.Resource):
    """A collection of RateLimit and AbsoluteLimit objects."""

    def __repr__(self):
        return "<Limits>"

    @property
    def absolute(self):
        for (name, value) in list(self._info['absolute'].items()):
            yield AbsoluteLimit(name, value)

    @property
    def rate(self):
        for group in self._info['rate']:
            uri = group['uri']
            regex = group['regex']
            for rate in group['limit']:
                yield RateLimit(rate['verb'], uri, regex, rate['value'],
                                rate['remaining'], rate['unit'],
                                rate['next-available'])


class RateLimit(object):
    """Data model that represents a flattened view of a single rate limit."""

    def __init__(self, verb, uri, regex, value, remain,
                 unit, next_available):
        self.verb = verb
        self.uri = uri
        self.regex = regex
        self.value = value
        self.remain = remain
        self.unit = unit
        self.next_available = next_available

    def __eq__(self, other):
        return self.uri == other.uri \
            and self.regex == other.regex \
            and self.value == other.value \
            and self.verb == other.verb \
            and self.remain == other.remain \
            and self.unit == other.unit \
            and self.next_available == other.next_available

    def __repr__(self):
        return "<RateLimit: method=%s uri=%s>" % (self.verb, self.uri)


class AbsoluteLimit(object):
    """Data model that represents a single absolute limit."""

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __eq__(self, other):
        return self.value == other.value and self.name == other.name

    def __repr__(self):
        return "<AbsoluteLimit: name=%s>" % (self.name)


class LimitsManager(base.Manager):
    """Manager object used to interact with limits resource."""

    resource_class = Limits

    def get(self):
        """Get a specific extension.

        :rtype: :class:`Limits`
        """
        return self._get("/limits", "limits")
