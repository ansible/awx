# -*- coding: utf-8 -*-
from datetime import datetime
import sys

from unittest import mock
import pytest

from awxkit import utils
from awxkit import exceptions as exc


@pytest.mark.parametrize('inp, out',
                         [[True, True],
                          [False, False],
                          [1, True],
                          [0, False],
                          [1.0, True],
                          [0.0, False],
                          ['TrUe', True],
                          ['FalSe', False],
                          ['yEs', True],
                          ['No', False],
                          ['oN', True],
                          ['oFf', False],
                          ['asdf', True],
                          ['0', False],
                          ['', False],
                          [{1: 1}, True],
                          [{}, False],
                          [(0,), True],
                          [(), False],
                          [[1], True],
                          [[], False]])
def test_to_bool(inp, out):
    assert utils.to_bool(inp) == out


@pytest.mark.parametrize('inp, out',
                         [["{}", {}],
                          ["{'null': null}", {"null": None}],
                          ["{'bool': true}", {"bool": True}],
                          ["{'bool': false}", {"bool": False}],
                          ["{'int': 0}", {"int": 0}],
                          ["{'float': 1.0}", {"float": 1.0}],
                          ["{'str': 'abc'}", {"str": "abc"}],
                          ["{'obj': {}}", {"obj": {}}],
                          ["{'list': []}", {"list": []}],
                          ["---", None],
                          ["---\n'null': null", {'null': None}],
                          ["---\n'bool': true", {'bool': True}],
                          ["---\n'bool': false", {'bool': False}],
                          ["---\n'int': 0", {'int': 0}],
                          ["---\n'float': 1.0", {'float': 1.0}],
                          ["---\n'string': 'abc'", {'string': 'abc'}],
                          ["---\n'obj': {}", {'obj': {}}],
                          ["---\n'list': []", {'list': []}],
                          ["", None],
                          ["'null': null", {'null': None}],
                          ["'bool': true", {'bool': True}],
                          ["'bool': false", {'bool': False}],
                          ["'int': 0", {'int': 0}],
                          ["'float': 1.0", {'float': 1.0}],
                          ["'string': 'abc'", {'string': 'abc'}],
                          ["'obj': {}", {'obj': {}}],
                          ["'list': []", {'list': []}]])
def test_load_valid_json_or_yaml(inp, out):
    assert utils.load_json_or_yaml(inp) == out


@pytest.mark.parametrize('inp', [True, False, 0, 1.0, {}, [], None])
def test_load_invalid_json_or_yaml(inp):
    with pytest.raises(TypeError):
        utils.load_json_or_yaml(inp)


@pytest.mark.parametrize('non_ascii', [True, False])
@pytest.mark.skipif(
    sys.version_info < (3, 6),
    reason='this is only intended to be used in py3, not the CLI'
)
def test_random_titles_are_unicode(non_ascii):
    assert isinstance(utils.random_title(non_ascii=non_ascii), str)


@pytest.mark.parametrize('non_ascii', [True, False])
@pytest.mark.skipif(
    sys.version_info < (3, 6),
    reason='this is only intended to be used in py3, not the CLI'
)
def test_random_titles_generates_correct_characters(non_ascii):
    title = utils.random_title(non_ascii=non_ascii)
    if non_ascii:
        with pytest.raises(UnicodeEncodeError):
            title.encode('ascii')
        title.encode('utf-8')
    else:
        title.encode('ascii')
        title.encode('utf-8')


@pytest.mark.parametrize('inp, out',
                         [['ClassNameShouldChange', 'class_name_should_change'],
                          ['classnameshouldntchange', 'classnameshouldntchange'],
                          ['Classspacingshouldntchange', 'classspacingshouldntchange'],
                          ['Class1Name2Should3Change', 'class_1_name_2_should_3_change'],
                          ['Class123name234should345change456', 'class_123_name_234_should_345_change_456']])
def test_class_name_to_kw_arg(inp, out):
    assert utils.class_name_to_kw_arg(inp) == out


@pytest.mark.parametrize('first, second, expected',
                         [['/api/v2/resources/', '/api/v2/resources/', True],
                          ['/api/v2/resources/', '/api/v2/resources/?test=ignored', True],
                          ['/api/v2/resources/?one=ignored', '/api/v2/resources/?two=ignored', True],
                          ['http://one.com', 'http://one.com', True],
                          ['http://one.com', 'http://www.one.com', True],
                          ['http://one.com', 'http://one.com?test=ignored', True],
                          ['http://one.com', 'http://www.one.com?test=ignored', True],
                          ['http://one.com', 'https://one.com', False],
                          ['http://one.com', 'https://one.com?test=ignored', False]])
def test_are_same_endpoint(first, second, expected):
    assert utils.are_same_endpoint(first, second) == expected


@pytest.mark.parametrize('endpoint, expected',
                         [['/api/v2/resources/', 'v2'],
                          ['/api/v2000/resources/', 'v2000'],
                          ['/api/', 'common']])
def test_version_from_endpoint(endpoint, expected):
    assert utils.version_from_endpoint(endpoint) == expected


class OneClass:
    pass

class TwoClass:
    pass

class ThreeClass:
    pass

class FourClass(ThreeClass):
    pass

def test_filter_by_class_with_subclass_class():
    filtered = utils.filter_by_class((OneClass, OneClass), (FourClass, ThreeClass))
    assert filtered == [OneClass, FourClass]

def test_filter_by_class_with_subclass_instance():
    one = OneClass()
    four = FourClass()
    filtered = utils.filter_by_class((one, OneClass), (four, ThreeClass))
    assert filtered == [one, four]

def test_filter_by_class_no_arg_tuples():
    three = ThreeClass()
    filtered = utils.filter_by_class((True, OneClass), (False, TwoClass), (three, ThreeClass))
    assert filtered == [OneClass, None, three]

def test_filter_by_class_with_arg_tuples_containing_class():
    one = OneClass()
    three = (ThreeClass, dict(one=1, two=2))
    filtered = utils.filter_by_class((one, OneClass), (False, TwoClass), (three, ThreeClass))
    assert filtered == [one, None, three]

def test_filter_by_class_with_arg_tuples_containing_subclass():
    one = OneClass()
    three = (FourClass, dict(one=1, two=2))
    filtered = utils.filter_by_class((one, OneClass), (False, TwoClass), (three, ThreeClass))
    assert filtered == [one, None, three]

@pytest.mark.parametrize('truthy', (True, 123, 'yes'))
def test_filter_by_class_with_arg_tuples_containing_truthy(truthy):
    one = OneClass()
    three = (truthy, dict(one=1, two=2))
    filtered = utils.filter_by_class((one, OneClass), (False, TwoClass), (three, ThreeClass))
    assert filtered == [one, None, (ThreeClass, dict(one=1, two=2))]


@pytest.mark.parametrize('date_string,now,expected', [
    ('2017-12-20T00:00:01.5Z', datetime(2017, 12, 20, 0, 0, 2, 750000), 1.25),
    ('2017-12-20T00:00:01.5Z', datetime(2017, 12, 20, 0, 0, 1, 500000), 0.00),
    ('2017-12-20T00:00:01.5Z', datetime(2017, 12, 20, 0, 0, 0, 500000), -1.00),
])
def test_seconds_since_date_string(date_string, now, expected):
    with mock.patch('awxkit.utils.utcnow', return_value=now):
        assert utils.seconds_since_date_string(date_string) == expected


class RecordingCallback(object):

    def __init__(self, value=True):
        self.call_count = 0
        self.value = value

    def __call__(self):
        self.call_count += 1
        return self.value


def test_suppress():
    callback = RecordingCallback()

    with utils.suppress(ZeroDivisionError, IndexError):
        raise ZeroDivisionError
        callback()
        raise IndexError
        raise KeyError
    assert callback.call_count == 0

    with utils.suppress(ZeroDivisionError, IndexError):
        raise IndexError
        callback()
        raise ZeroDivisionError
        raise KeyError
    assert callback.call_count == 0

    with pytest.raises(KeyError):
        with utils.suppress(ZeroDivisionError, IndexError):
            raise KeyError
            callback()
            raise ZeroDivisionError
            raise IndexError
    assert callback.call_count == 0


class TestPollUntil(object):

    @pytest.mark.parametrize('timeout', [0, 0.0, -0.5, -1, -9999999])
    def test_callback_called_once_for_non_positive_timeout(self, timeout):
        with mock.patch('awxkit.utils.logged_sleep') as sleep:
            callback = RecordingCallback()
            utils.poll_until(callback, timeout=timeout)
            assert not sleep.called
            assert callback.call_count == 1

    def test_exc_raised_on_timeout(self):
        with mock.patch('awxkit.utils.logged_sleep'):
            with pytest.raises(exc.WaitUntilTimeout):
                utils.poll_until(lambda: False, timeout=0)

    @pytest.mark.parametrize('callback_value', [{'hello': 1}, 'foo', True])
    def test_non_falsey_callback_value_is_returned(self, callback_value):
        with mock.patch('awxkit.utils.logged_sleep'):
            assert utils.poll_until(lambda: callback_value) == callback_value


class TestPseudoNamespace(object):

    def test_set_item_check_item(self):
        pn = utils.PseudoNamespace()
        pn['key'] = 'value'
        assert pn['key'] == 'value'

    def test_set_item_check_attr(self):
        pn = utils.PseudoNamespace()
        pn['key'] = 'value'
        assert pn.key == 'value'

    def test_set_attr_check_item(self):
        pn = utils.PseudoNamespace()
        pn.key = 'value'
        assert pn['key'] == 'value'

    def test_set_attr_check_attr(self):
        pn = utils.PseudoNamespace()
        pn.key = 'value'
        assert pn.key == 'value'

    def test_auto_dicts_cast(self):
        pn = utils.PseudoNamespace()
        pn.one = dict()
        pn.one.two = dict(three=3)
        assert pn.one.two.three == 3
        assert pn == dict(one=dict(two=dict(three=3)))

    def test_auto_list_of_dicts_cast(self):
        pn = utils.PseudoNamespace()
        pn.one = [dict(two=2), dict(three=3)]
        assert pn.one[0].two == 2
        assert pn == dict(one=[dict(two=2), dict(three=3)])

    def test_auto_tuple_of_dicts_cast(self):
        pn = utils.PseudoNamespace()
        pn.one = (dict(two=2), dict(three=3))
        assert pn.one[0].two == 2
        assert pn == dict(one=(dict(two=2), dict(three=3)))

    def test_instantiation_via_dict(self):
        pn = utils.PseudoNamespace(dict(one=1, two=2, three=3))
        assert pn.one == 1
        assert pn == dict(one=1, two=2, three=3)
        assert len(pn.keys()) == 3

    def test_instantiation_via_kwargs(self):
        pn = utils.PseudoNamespace(one=1, two=2, three=3)
        assert pn.one == 1
        assert pn == dict(one=1, two=2, three=3)
        assert len(pn.keys()) == 3

    def test_instantiation_via_dict_and_kwargs(self):
        pn = utils.PseudoNamespace(dict(one=1, two=2, three=3), four=4, five=5)
        assert pn.one == 1
        assert pn.four == 4
        assert pn == dict(one=1, two=2, three=3, four=4, five=5)
        assert len(pn.keys()) == 5

    def test_instantiation_via_nested_dict(self):
        pn = utils.PseudoNamespace(dict(one=1, two=2), three=dict(four=4, five=dict(six=6)))
        assert pn.one == 1
        assert pn.three.four == 4
        assert pn.three.five.six == 6
        assert pn == dict(one=1, two=2, three=dict(four=4, five=dict(six=6)))

    def test_instantiation_via_nested_dict_with_list(self):
        pn = utils.PseudoNamespace(dict(one=[dict(two=2), dict(three=3)]))
        assert pn.one[0].two == 2
        assert pn.one[1].three == 3
        assert pn == dict(one=[dict(two=2), dict(three=3)])

    def test_instantiation_via_nested_dict_with_lists(self):
        pn = utils.PseudoNamespace(dict(one=[dict(two=2),
                                             dict(three=dict(four=4,
                                                             five=[dict(six=6),
                                                                   dict(seven=7)]))]))
        assert pn.one[1].three.five[1].seven == 7

    def test_instantiation_via_nested_dict_with_tuple(self):
        pn = utils.PseudoNamespace(dict(one=(dict(two=2), dict(three=3))))
        assert pn.one[0].two == 2
        assert pn.one[1].three == 3
        assert pn == dict(one=(dict(two=2), dict(three=3)))

    def test_instantiation_via_nested_dict_with_tuples(self):
        pn = utils.PseudoNamespace(dict(one=(dict(two=2),
                                             dict(three=dict(four=4,
                                                             five=(dict(six=6),
                                                                   dict(seven=7)))))))
        assert pn.one[1].three.five[1].seven == 7

    def test_update_with_nested_dict(self):
        pn = utils.PseudoNamespace()
        pn.update(dict(one=1, two=2, three=3), four=4, five=5)
        assert pn.one == 1
        assert pn.four == 4
        assert pn == dict(one=1, two=2, three=3, four=4, five=5)
        assert len(pn.keys()) == 5

    def test_update_with_nested_dict_with_lists(self):
        pn = utils.PseudoNamespace()
        pn.update(dict(one=[dict(two=2),
                            dict(three=dict(four=4,
                                            five=[dict(six=6),
                                                  dict(seven=7)]))]))
        assert pn.one[1].three.five[1].seven == 7

    def test_update_with_nested_dict_with_tuples(self):
        pn = utils.PseudoNamespace()
        pn.update(dict(one=(dict(two=2),
                            dict(three=dict(four=4,
                                            five=(dict(six=6),
                                                  dict(seven=7)))))))
        assert pn.one[1].three.five[1].seven == 7


class TestUpdatePayload(object):

    def test_empty_payload(self):
        fields = ('one', 'two', 'three', 'four')
        kwargs = dict(two=2, four=4)
        payload = {}
        utils.update_payload(payload, fields, kwargs)
        assert payload == kwargs

    def test_untouched_payload(self):
        fields = ('not', 'in', 'kwargs')
        kwargs = dict(one=1, two=2)
        payload = dict(three=3, four=4)
        utils.update_payload(payload, fields, kwargs)
        assert payload == dict(three=3, four=4)

    def test_overwritten_payload(self):
        fields = ('one', 'two')
        kwargs = dict(one=1, two=2)
        payload = dict(one='one', two='two')
        utils.update_payload(payload, fields, kwargs)
        assert payload == kwargs

    def test_falsy_kwargs(self):
        fields = ('one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight')
        kwargs = dict(one=False, two=(), three='', four=None, five=0, six={}, seven=set(), eight=[])
        payload = {}
        utils.update_payload(payload, fields, kwargs)
        assert payload == kwargs

    def test_not_provided_strips_payload(self):
        fields = ('one', 'two')
        kwargs = dict(one=utils.not_provided)
        payload = dict(one=1, two=2)
        utils.update_payload(payload, fields, kwargs)
        assert payload == dict(two=2)


def test_to_ical():
    now = datetime.utcnow()
    ical_datetime = utils.to_ical(now)
    date = str(now.date()).replace('-', '')
    time = str(now.time()).split('.')[0].replace(':', '')
    assert ical_datetime == '{}T{}Z'.format(date, time)
