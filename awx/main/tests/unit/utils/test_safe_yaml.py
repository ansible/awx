# -*- coding: utf-8 -*-

from copy import deepcopy
import pytest
import yaml
from awx.main.utils.safe_yaml import safe_dump


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
