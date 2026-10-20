from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import sys

import pytest

VARS_TEXT_FIELDS = ['extra_vars', 'variables', 'source_vars']


@pytest.fixture
def controller_api_module(collection_import):
    """A module instance built without touching the API, for the comparison helpers."""
    controller_api_class = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    return controller_api_class(argument_spec={}, direct_params=dict(controller_host='https://localhost'))


@pytest.mark.parametrize(
    "value, expected",
    [
        # a field that was never set reads back from the API as an empty string
        ['', {}],
        [None, {}],
        ['--- {}\n', {}],
        # the API returns YAML, or JSON, for a field the module takes as a dict
        ['foo: bar\n', {'foo': 'bar'}],
        ['{"foo": "bar"}', {'foo': 'bar'}],
        # a dict is already comparable
        [{'foo': 'bar'}, {'foo': 'bar'}],
        [{}, {}],
        # unparseable text is compared as the opaque string it is, not raised on
        ['foo: [unbalanced', 'foo: [unbalanced'],
        # JSON is read as JSON: YAML 1.1 would read 1e+20 as a string
        ['{"threshold": 1e+20}', {'threshold': 1e+20}],
        # the API treats '""' as empty
        ['""', {}],
        # PyYAML raises ValueError, not YAMLError, for an invalid date: compared as text, not raised
        ['a: 2001-02-30\n', 'a: 2001-02-30\n'],
        # nesting deeper than the recursion limit is compared as text, not raised
        pytest.param('[' * 100000, '[' * 100000, id='deeply-nested'),
        # an integer longer than the int conversion limit fails both parsers, so it is compared as text
        pytest.param(
            '1' * 5000, '1' * 5000, id='over-long-integer',
            marks=pytest.mark.skipif(not hasattr(sys, 'get_int_max_str_digits'), reason='no int conversion limit'),
        ),
    ],
)
def test_normalize_vars_field(collection_import, value, expected):
    controller_api_class = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    assert controller_api_class._normalize_vars_field(value) == expected


@pytest.mark.parametrize("field", VARS_TEXT_FIELDS)
def test_serialize_vars_fields_renders_yaml(collection_import, field):
    controller_api_class = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    new_item = controller_api_class._serialize_vars_fields({'name': 'test', field: {'foo': 'bar'}})
    assert new_item[field] == '---\nfoo: bar\n'
    assert new_item['name'] == 'test'


@pytest.mark.parametrize("field", VARS_TEXT_FIELDS)
def test_serialize_vars_fields_empty_dict_clears(collection_import, field):
    """An empty dict has to reach the API as an empty string, which is how these fields are cleared."""
    controller_api_class = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    assert controller_api_class._serialize_vars_fields({field: {}})[field] == ''


@pytest.mark.parametrize("field", VARS_TEXT_FIELDS)
def test_serialize_vars_fields_does_not_mutate_the_caller(collection_import, field):
    controller_api_class = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    declared = {field: {'foo': 'bar'}}
    controller_api_class._serialize_vars_fields(declared)
    assert declared[field] == {'foo': 'bar'}


def test_serialize_vars_fields_leaves_other_values_alone(collection_import):
    controller_api_class = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    # text the user supplied directly passes through, and a dict field that the API
    # really does store as structured data is not touched
    new_item = controller_api_class._serialize_vars_fields({'extra_vars': 'foo: bar\n', 'inputs': {'foo': 'bar'}})
    assert new_item['extra_vars'] == 'foo: bar\n'
    assert new_item['inputs'] == {'foo': 'bar'}


@pytest.mark.parametrize(
    "old, new, expected",
    [
        # the API's text form and the module's dict form are the same data
        ['foo: bar\n', {'foo': 'bar'}, False],
        ['{"foo": "bar"}', {'foo': 'bar'}, False],
        ['', {}, False],
        [None, {}, False],
        # real differences still register
        ['foo: bar\n', {'foo': 'baz'}, True],
        ['foo: bar\n', {}, True],
        ['', {'foo': 'bar'}, True],
        # booleans and integers compare equal under ==, but are different values
        ['flag: true\n', {'flag': 1}, True],
        ['flag: false\n', {'flag': 0}, True],
        ['flag: 1\n', {'flag': True}, True],
        ['items: [true]\n', {'items': [1]}, True],
        ['outer: {flag: true}\n', {'outer': {'flag': 1}}, True],
        ['flag: true\n', {'flag': True}, False],
        ['items: [1, 2]\n', {'items': [1, 2]}, False],
    ],
)
@pytest.mark.parametrize("field", VARS_TEXT_FIELDS)
def test_objects_could_be_different_normalizes_vars_fields(controller_api_module, field, old, new, expected):
    assert controller_api_module.objects_could_be_different({field: old}, {field: new}) is expected


@pytest.mark.parametrize("field", VARS_TEXT_FIELDS)
def test_serialized_vars_match_what_the_api_returns(controller_api_module, field):
    """The round trip a second run makes: what was sent last time compares equal to what came back."""
    controller_api_class = type(controller_api_module)
    new_item = controller_api_class._serialize_vars_fields({field: {'foo': 'bar'}})
    assert controller_api_module.objects_could_be_different({field: 'foo: bar\n'}, new_item) is False


def test_objects_could_be_different_keeps_dict_comparison_for_other_fields(controller_api_module):
    assert controller_api_module.objects_could_be_different({'inputs': {'foo': 'bar'}}, {'inputs': {'foo': 'bar'}}) is False
    assert controller_api_module.objects_could_be_different({'inputs': {'foo': 'bar'}}, {'inputs': {'foo': 'baz'}}) is True


def test_json_number_differs_from_a_string(collection_import):
    """A number stored as JSON must not compare equal to the same text requested as a string."""
    controller_api_class = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    stored = controller_api_class._normalize_vars_field('{"threshold": 1e+20}')
    requested = controller_api_class._normalize_vars_field({'threshold': '1e+20'})
    assert not controller_api_class._vars_equal(stored, requested)


@pytest.fixture
def without_yaml(collection_import, monkeypatch):
    controller_api = collection_import('plugins.module_utils.controller_api')
    monkeypatch.setattr(controller_api, 'HAS_YAML', False)
    return controller_api.ControllerAPIModule


@pytest.mark.parametrize("field", VARS_TEXT_FIELDS)
def test_serialize_vars_fields_without_yaml_sends_json_text(without_yaml, field):
    new_item = without_yaml._serialize_vars_fields({'name': 'test', field: {'foo': 'bar'}})
    assert isinstance(new_item[field], str)
    assert json.loads(new_item[field]) == {'foo': 'bar'}


@pytest.mark.parametrize("field", VARS_TEXT_FIELDS)
def test_serialize_vars_fields_without_yaml_clears_empty(without_yaml, field):
    assert without_yaml._serialize_vars_fields({field: {}})[field] == ''


def test_normalize_vars_field_without_yaml(without_yaml):
    # JSON still compares structurally; YAML is kept as the opaque string it is
    assert without_yaml._normalize_vars_field('{"foo": "bar"}') == {'foo': 'bar'}
    assert without_yaml._normalize_vars_field('foo: bar\n') == 'foo: bar\n'
    assert without_yaml._vars_equal(without_yaml._normalize_vars_field('{"a": 1}'), without_yaml._normalize_vars_field({'a': 1}))


@pytest.mark.parametrize("has_yaml", [True, False])
@pytest.mark.parametrize(
    "requested",
    [
        {'threshold': 1e20, 'ratio': 0.5, 'count': 3},
        {'enabled': True, 'level': 1},
        {'nested': {'list': [1, 'two', {'three': 3.0}]}},
        {'unicode': 'caf\u00e9 \U0001f600'},
    ],
)
def test_sent_value_reads_back_as_requested(collection_import, monkeypatch, has_yaml, requested):
    """What the module sends compares equal to the request when read back, with or without PyYAML."""
    controller_api = collection_import('plugins.module_utils.controller_api')
    monkeypatch.setattr(controller_api, 'HAS_YAML', has_yaml)
    module_class = controller_api.ControllerAPIModule
    sent = module_class._serialize_vars_fields({'variables': requested})['variables']
    assert isinstance(sent, str)
    assert module_class._vars_equal(module_class._normalize_vars_field(sent), module_class._normalize_vars_field(requested))
