# Python
from collections import OrderedDict
import json
import yaml

# Django
from django.conf import settings
from django.utils import six
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework import parsers
from rest_framework.exceptions import ParseError


class OrderedDictLoader(yaml.SafeLoader):
    """
    This yaml loader is used to deal with current pyYAML (3.12) not supporting
    custom object pairs hook. Remove it when new version adds that support.
    """

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.nodes.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(
                None, None,
                "expected a mapping node, but found %s" % node.id,
                node.start_mark
            )
        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError, exc:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping", node.start_mark,
                    "found unacceptable key (%s)" % exc, key_node.start_mark
                )
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping


class JSONParser(parsers.JSONParser):
    """
    Parses JSON-serialized data, preserving order of dictionary keys.
    """

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as JSON and returns the resulting data.
        """
        parser_context = parser_context or {}
        encoding = parser_context.get('encoding', settings.DEFAULT_CHARSET)

        try:
            data = stream.read().decode(encoding)
            if not data:
                return {}
            obj = json.loads(data, object_pairs_hook=OrderedDict)
            if not isinstance(obj, dict) and obj is not None:
                raise ParseError(_('JSON parse error - not a JSON object'))
            return obj
        except ValueError as exc:
            raise ParseError(_('JSON parse error - %s\nPossible cause: trailing comma.' % six.text_type(exc)))
