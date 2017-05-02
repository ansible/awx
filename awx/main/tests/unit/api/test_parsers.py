import pytest

import StringIO
from collections import OrderedDict

from awx.api.parsers import JSONParser


@pytest.mark.parametrize('input_, output', [
    ('{"foo": "bar", "alice": "bob"}', OrderedDict([("foo", "bar"), ("alice", "bob")])),
    ('{"foo": "bar", "alice": "bob",\n }', OrderedDict([("foo", "bar"), ("alice", "bob")])),
    ('{"foo": ["alice", "bob"]}', {"foo": ["alice","bob"]}),
    ('{"foo": ["alice", "bob",\n ]}', {"foo": ["alice","bob"]}),
    ('{"foo": "\\"bar, \\n}"}', {"foo": "\"bar, \n}"}),
    ('{"foo": ["\\"alice,\\n ]", "bob"]}', {"foo": ["\"alice,\n ]","bob"]}),
])
def test_trailing_comma_support(input_, output):
    input_buffer = StringIO.StringIO()
    input_buffer.write(input_)
    input_buffer.seek(0)
    assert JSONParser().parse(input_buffer) == output
    input_buffer.close()


def test_yaml_load_preserves_input_order():
    input_ = '{"a": "b", "c": "d", "e": "f"}'
    output = ('a', 'c', 'e')
    input_buffer = StringIO.StringIO()
    input_buffer.write(input_)
    input_buffer.seek(0)
    assert tuple(JSONParser().parse(input_buffer)) == output
