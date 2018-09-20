# -*- coding: utf-8 -*-

from copy import deepcopy
import pytest
import yaml
import json
from awx.main.utils.safe_yaml import safe_dump, VaultDecoder, VaultEncoder, SafeLoader


@pytest.mark.parametrize('value', [None, 1, 1.5, []])
def test_native_types(value):
    # Native non-string types should dump the same way that `yaml.safe_dump` does
    assert safe_dump(value) == yaml.safe_dump(value)


def test_empty():
    assert safe_dump({}) == ''


def test_raw_string():
    assert safe_dump('foo') == "!unsafe 'foo'\n"


def test_kv_null():
    assert safe_dump({'a': None}) == "!unsafe 'a': null\n"


def test_kv_null_safe():
    assert safe_dump({'a': None}, {'a': None}) == "a: null\n"


def test_kv_null_unsafe():
    assert safe_dump({'a': ''}, {'a': None}) == "!unsafe 'a': !unsafe ''\n"


def test_kv_int():
    assert safe_dump({'a': 1}) == "!unsafe 'a': 1\n"


def test_kv_float():
    assert safe_dump({'a': 1.5}) == "!unsafe 'a': 1.5\n"


def test_kv_unsafe():
    assert safe_dump({'a': 'b'}) == "!unsafe 'a': !unsafe 'b'\n"


def test_kv_unsafe_unicode():
    assert safe_dump({'a': u'🐉'}) == '!unsafe \'a\': !unsafe "\\U0001F409"\n'


def test_kv_unsafe_in_list():
    assert safe_dump({'a': ['b']}) == "!unsafe 'a':\n- !unsafe 'b'\n"


def test_kv_unsafe_in_mixed_list():
    assert safe_dump({'a': [1, 'b']}) == "!unsafe 'a':\n- 1\n- !unsafe 'b'\n"


def test_kv_unsafe_deep_nesting():
    yaml = safe_dump({'a': [1, [{'b': {'c': [{'d': 'e'}]}}]]})
    for x in ('a', 'b', 'c', 'd', 'e'):
        assert "!unsafe '{}'".format(x) in yaml


def test_kv_unsafe_multiple():
    assert safe_dump({'a': 'b', 'c': 'd'}) == '\n'.join([
        "!unsafe 'a': !unsafe 'b'",
        "!unsafe 'c': !unsafe 'd'",
        ""
    ])


def test_safe_marking():
    assert safe_dump({'a': 'b'}, safe_dict={'a': 'b'}) == "a: b\n"


def test_safe_marking_mixed():
    assert safe_dump({'a': 'b', 'c': 'd'}, safe_dict={'a': 'b'}) == '\n'.join([
        "a: b",
        "!unsafe 'c': !unsafe 'd'",
        ""
    ])


def test_safe_marking_deep_nesting():
    deep = {'a': [1, [{'b': {'c': [{'d': 'e'}]}}]]}
    yaml = safe_dump(deep, deepcopy(deep))
    for x in ('a', 'b', 'c', 'd', 'e'):
        assert "!unsafe '{}'".format(x) not in yaml


def test_deep_diff_unsafe_marking():
    deep = {'a': [1, [{'b': {'c': [{'d': 'e'}]}}]]}
    jt_vars = deepcopy(deep)
    deep['a'][1][0]['b']['z'] = 'not safe'
    yaml = safe_dump(deep, jt_vars)
    assert "!unsafe 'z'" in yaml


def test_mark_variable_as_vault():
    JSON_DATA = '''
    {
        "vars_secret_funky_json": {
            "__ansible_vault": "$ANSIBLE_VAULT;1.2;AES256;alan_host\\n3535666661663330333731376634656261396131326233353066343239\\n3733\\n"
        }
    }
    '''
    vars = json.loads(JSON_DATA, cls=VaultDecoder)
    output = safe_dump(vars)
    assert "!unsafe 'vars_secret_funky_json': !vault |" in output


def test_convert_constructor_to_json_form():
    YAML_DATA = '''
    vars_secret_funky_json: !vault |
        $ANSIBLE_VAULT;1.2;AES256;alan_host
        35356666616633303337313766346562613961313262333530663432393965303736653334306433
        6239666265343936343462653836386162343234353961330a306665396665353364613863316362
        66646663313737393763383565333237316663666339623063646666646261643338616261633330
        3634313634666264620a383632386661653330326435633861333031643334643237366430313733
        3733
    '''
    vars = yaml.load(YAML_DATA, Loader=SafeLoader)
    output = json.dumps(vars, cls=VaultEncoder)
    assert '__ansible_vault' in output
