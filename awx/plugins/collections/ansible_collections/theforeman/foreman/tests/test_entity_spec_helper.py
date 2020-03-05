from plugins.module_utils.foreman_helper import _entity_spec_helper


def test_empty_entity():
    spec = {}
    entity_spec, argument_spec = _entity_spec_helper(spec)
    assert spec == {}
    assert entity_spec == {'id': {}}
    assert argument_spec == {}


def test_full_entity():
    spec = {
        'name': {},
        'count': {'type': 'int', 'aliases': ['number']},
        'street': {'type': 'entity', 'flat_name': 'street_id'},
        'houses': {'type': 'entity_list', 'flat_name': 'house_ids'},
        'prices': {'type': 'nested_list', 'entity_spec': {
            'value': {},
        }},
    }
    entity_spec, argument_spec = _entity_spec_helper(spec)
    assert spec == {
        'name': {},
        'count': {'type': 'int', 'aliases': ['number']},
        'street': {'type': 'entity', 'flat_name': 'street_id'},
        'houses': {'type': 'entity_list', 'flat_name': 'house_ids'},
        'prices': {'type': 'nested_list', 'entity_spec': {
            'value': {},
        }},
    }
    assert entity_spec == {
        'id': {},
        'name': {},
        'count': {},
        'street': {'type': 'entity', 'flat_name': 'street_id'},
        'street_id': {},
        'houses': {'type': 'entity_list', 'flat_name': 'house_ids'},
        'house_ids': {},
    }
    assert argument_spec == {
        'name': {},
        'count': {'type': 'int', 'aliases': ['number']},
        'street': {},
        'houses': {'type': 'list'},
        'prices': {'type': 'list', 'elements': 'dict', 'options': {
            'value': {},
        }},
    }
