import pytest
from io import StringIO

# AWX
from awx.api.parsers import JSONParser

# Django REST Framework
from rest_framework.exceptions import ParseError


@pytest.mark.parametrize(
    'input_, output', [
        ('{"foo": "bar"}', {'foo': 'bar'}),
        ('null', None),
        ('', {}),
    ]
)
def test_jsonparser_valid_input(input_, output):
    input_stream = StringIO(input_)
    assert JSONParser().parse(input_stream) == output
    input_stream.close()


@pytest.mark.parametrize('invalid_input', ['1', '"foobar"', '3.14', '{"foo": "bar",}'])
def test_json_parser_invalid_input(invalid_input):
    input_stream = StringIO(invalid_input)
    with pytest.raises(ParseError):
        JSONParser().parse(input_stream)
    input_stream.close()
