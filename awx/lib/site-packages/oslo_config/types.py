# Copyright 2013 Mirantis, Inc.
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

"""Type conversion and validation classes for configuration options.

Use these classes as values for the `type` argument to
:class:`oslo_config.cfg.Opt` and its subclasses.

"""
import netaddr
import six


class ConfigType(object):

    BASE_TYPES = (None,)

    def is_base_type(self, other):
        return isinstance(other, self.BASE_TYPES)


class String(ConfigType):

    """String type.

    String values do not get transformed and are returned as str objects.

    :param choices: Optional sequence of valid values.
    :param quotes: If True and string is enclosed with single or double
                   quotes, will strip those quotes. Will signal error if
                   string have quote at the beginning and no quote at
                   the end. Turned off by default. Useful if used with
                   container types like List.
    """

    BASE_TYPES = six.string_types

    def __init__(self, choices=None, quotes=False):
        super(String, self).__init__()
        self.choices = choices
        self.quotes = quotes

    def __call__(self, value):
        value = str(value)
        if self.quotes and value:
            if value[0] in "\"'":
                if value[-1] != value[0]:
                    raise ValueError('Non-closed quote: %s' % value)
                value = value[1:-1]

        if self.choices is None or value in self.choices:
            return value

        raise ValueError(
            'Valid values are [%s], but found %s' % (
                ', '.join([str(v) for v in self.choices]),
                repr(value)))

    def __repr__(self):
        if self.choices:
            return 'String(choices=%s)' % repr(self.choices)
        return 'String'

    def __eq__(self, other):
        return (
            (self.__class__ == other.__class__) and
            (self.choices == other.choices) and
            (self.quotes == other.quotes)
        )


class MultiString(String):

    BASE_TYPES = six.string_types + (list,)


class Boolean(ConfigType):

    """Boolean type.

    Values are case insensitive and can be set using
    1/0, yes/no, true/false or on/off.
    """
    TRUE_VALUES = ['true', '1', 'on', 'yes']
    FALSE_VALUES = ['false', '0', 'off', 'no']

    BASE_TYPES = (bool,)

    def __call__(self, value):
        if isinstance(value, bool):
            return value

        s = value.lower()
        if s in self.TRUE_VALUES:
            return True
        elif s in self.FALSE_VALUES:
            return False
        else:
            raise ValueError('Unexpected boolean value %r' % value)

    def __repr__(self):
        return 'Boolean'

    def __eq__(self, other):
        return self.__class__ == other.__class__


class Integer(ConfigType):

    """Integer type.

    Converts value to an integer optionally doing range checking.
    If value is whitespace or empty string will return None.

    :param min: Optional check that value is greater than or equal to min
    :param max: Optional check that value is less than or equal to max
    """

    BASE_TYPES = six.integer_types

    def __init__(self, min=None, max=None):
        super(Integer, self).__init__()
        self.min = min
        self.max = max
        if min and max and max < min:
            raise ValueError('Max value is less than min value')

    def __call__(self, value):
        if not isinstance(value, int):
            s = str(value).strip()
            if s == '':
                value = None
            else:
                value = int(value)

        if value is not None:
            self._check_range(value)

        return value

    def _check_range(self, value):
        if self.min and value < self.min:
            raise ValueError('Should be greater than or equal to %d' %
                             self.min)
        if self.max and value > self.max:
            raise ValueError('Should be less than or equal to %d' % self.max)

    def __repr__(self):
        props = []
        if self.min:
            props.append('min=%d' % self.min)
        if self.max:
            props.append('max=%d' % self.max)

        if props:
            return 'Integer(%s)' % ', '.join(props)
        return 'Integer'

    def __eq__(self, other):
        return (
            (self.__class__ == other.__class__) and
            (self.min == other.min) and
            (self.max == other.max)
        )


class Float(ConfigType):

    """Float type."""

    # allow float to be set from int
    BASE_TYPES = six.integer_types + (float,)

    def __call__(self, value):
        if isinstance(value, float):
            return value

        return float(value)

    def __repr__(self):
        return 'Float'

    def __eq__(self, other):
        return self.__class__ == other.__class__


class List(ConfigType):

    """List type.

    Represent values of other (item) type, separated by commas.
    The resulting value is a list containing those values.

    List doesn't know if item type can also contain commas. To workaround this
    it tries the following: if the next part fails item validation, it appends
    comma and next item until validation succeeds or there is no parts left.
    In the later case it will signal validation error.

    :param item_type: type of list items
    :param bounds: if True, value should be inside "[" and "]" pair
    """

    BASE_TYPES = (list,)

    def __init__(self, item_type=None, bounds=False):
        super(List, self).__init__()

        if item_type is None:
            item_type = String()

        if not callable(item_type):
            raise TypeError('item_type must be callable')
        self.item_type = item_type
        self.bounds = bounds

    def __call__(self, value):
        if isinstance(value, list):
            return value

        result = []
        s = value.strip()

        if self.bounds:
            if not s.startswith('['):
                raise ValueError('Value should start with "["')
            if not s.endswith(']'):
                raise ValueError('Value should end with "]"')
            s = s[1:-1]

        if s == '':
            return result

        values = s.split(',')
        while values:
            value = values.pop(0)
            while True:
                first_error = None
                try:
                    validated_value = self.item_type(value.strip())
                    break
                except ValueError as e:
                    if not first_error:
                        first_error = e
                    if len(values) == 0:
                        raise first_error

                value += ',' + values.pop(0)

            result.append(validated_value)

        return result

    def __repr__(self):
        return 'List of %s' % repr(self.item_type)

    def __eq__(self, other):
        return (
            (self.__class__ == other.__class__) and
            (self.item_type == other.item_type)
        )


class Dict(ConfigType):

    """Dictionary type.

    Dictionary type values are key:value pairs separated by commas.
    The resulting value is a dictionary of these key/value pairs.
    Type of dictionary key is always string, but dictionary value
    type can be customized.

    :param value_type: type of values in dictionary
    :param bounds: if True, value should be inside "{" and "}" pair
    """

    BASE_TYPES = (dict,)

    def __init__(self, value_type=None, bounds=False):
        super(Dict, self).__init__()

        if value_type is None:
            value_type = String()

        if not callable(value_type):
            raise TypeError('value_type must be callable')
        self.value_type = value_type
        self.bounds = bounds

    def __call__(self, value):
        if isinstance(value, dict):
            return value

        result = {}
        s = value.strip()

        if self.bounds:
            if not s.startswith('{'):
                raise ValueError('Value should start with "{"')
            if not s.endswith('}'):
                raise ValueError('Value should end with "}"')
            s = s[1:-1]

        if s == '':
            return result

        pairs = s.split(',')
        while pairs:
            pair = pairs.pop(0)

            while True:
                first_error = None
                try:
                    key_value = pair.split(':', 1)

                    if len(key_value) < 2:
                        raise ValueError('Value should be NAME:VALUE pairs '
                                         'separated by ","')

                    key, value = key_value
                    key = key.strip()
                    value = value.strip()

                    value = self.value_type(value)
                    break
                except ValueError as e:
                    if not first_error:
                        first_error = e
                    if not pairs:
                        raise first_error

                pair += ',' + pairs.pop(0)

            if key == '':
                raise ValueError('Key name should not be empty')

            if key in result:
                raise ValueError('Duplicate key %s' % key)

            result[key] = value

        return result

    def __repr__(self):
        return 'Dict of %s' % repr(self.value_type)

    def __eq__(self, other):
        return (
            (self.__class__ == other.__class__) and
            (self.value_type == other.value_type)
        )


class IPAddress(ConfigType):

    """IP address type

    Represents either ipv4 or ipv6. Without specifying version parameter both
    versions are checked

    :param version: defines which version should be explicitly checked (4 or 6)

    """

    BASE_TYPES = six.string_types

    def __init__(self, version=None):
        super(IPAddress, self).__init__()
        version_checkers = {
            None: self._check_both_versions,
            4: self._check_ipv4,
            6: self._check_ipv6
        }

        self.version_checker = version_checkers.get(version)
        if self.version_checker is None:
            raise TypeError("%s is not a valid IP version." % version)

    def __call__(self, value):
        value = str(value)
        if not value:
            raise ValueError("IP address cannot be an empty string")
        self.version_checker(value)
        return value

    def __repr__(self):
        return "IPAddress"

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def _check_ipv4(self, address):
        if not netaddr.valid_ipv4(address, netaddr.core.INET_PTON):
            raise ValueError("%s is not an IPv4 address" % address)

    def _check_ipv6(self, address):
        if not netaddr.valid_ipv6(address, netaddr.core.INET_PTON):
            raise ValueError("%s is not an IPv6 address" % address)

    def _check_both_versions(self, address):
        if not (netaddr.valid_ipv4(address, netaddr.core.INET_PTON) or
                netaddr.valid_ipv6(address, netaddr.core.INET_PTON)):
            raise ValueError("%s is not IPv4 or IPv6 address" % address)
