# Python
from collections import OrderedDict
import json

# Django
from django.conf import settings
from django.utils import six
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework import parsers
from rest_framework.exceptions import ParseError


def _remove_trailing_commas(data):
    left = 0
    right = 0
    in_string = False
    ret = []
    while left != len(data):
        if data[left] == ',' and not in_string:
            while right != len(data) and data[right] in ',\n\t\r ':
                right += 1
            if right == len(data) or data[right] not in '}]':
                ret.append(',')
        else:
            if data[left] == '"' and (left - 1 >= 0 and data[left - 1] != '\\'):
                in_string = not in_string
            ret.append(data[left])
            right += 1
        left = right
    return ''.join(ret)


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
            data = _remove_trailing_commas(stream.read().decode(encoding))
            obj = json.loads(data, object_pairs_hook=OrderedDict)
            if not isinstance(obj, dict):
                raise ParseError(_('JSON parse error - not a JSON object'))
            return obj
        except ValueError as exc:
            raise ParseError(_('JSON parse error - %s') % six.text_type(exc))
