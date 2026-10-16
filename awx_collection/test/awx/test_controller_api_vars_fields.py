from __future__ import absolute_import, division, print_function

__metaclass__ = type

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
