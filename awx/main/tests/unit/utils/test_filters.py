
# Python
import pytest
import mock
from collections import namedtuple

# AWX
from awx.main.utils.filters import SmartFilter

# Django
from django.db.models import Q


Field = namedtuple('Field', 'name')
Meta = namedtuple('Meta', 'fields')


class mockObjects:
    def filter(self, *args, **kwargs):
        return Q(*args, **kwargs)


class mockHost:
    def __init__(self):
        print("Host mock created")
        self.objects = mockObjects()
        self._meta = Meta(fields=(Field(name='name'), Field(name='description')))


@mock.patch('awx.main.utils.filters.get_model', return_value=mockHost())
class TestSmartFilterQueryFromString():
    @pytest.mark.parametrize("filter_string,q_expected", [
        ('facts__facts__blank=""', Q(**{u"facts__facts__blank": u""})),
        ('"facts__facts__ space "="f"', Q(**{u"facts__facts__ space ": u"f"})),
        ('"facts__facts__ e "=no_quotes_here', Q(**{u"facts__facts__ e ": u"no_quotes_here"})),
        ('a__b__c=3', Q(**{u"a__b__c": 3})),
        ('a__b__c=3.14', Q(**{u"a__b__c": 3.14})),
        ('a__b__c=true', Q(**{u"a__b__c": True})),
        ('a__b__c=false', Q(**{u"a__b__c": False})),
        ('ansible_facts__a="true"', Q(**{u"ansible_facts__contains": {u"a": u"true"}})),
        #('"a__b\"__c"="true"', Q(**{u"a__b\"__c": "true"})),
        #('a__b\"__c="true"', Q(**{u"a__b\"__c": "true"})),
    ])
    def test_query_generated(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert unicode(q) == unicode(q_expected)

    @pytest.mark.parametrize("filter_string", [
        'ansible_facts__facts__facts__blank='
        'ansible_facts__a__b__c__ space  =ggg',
    ])
    def test_invalid_filter_strings(self, mock_get_host_model, filter_string):
        with pytest.raises(RuntimeError) as e:
            SmartFilter.query_from_string(filter_string)
        assert e.value.message == u"Invalid query " + filter_string

    @pytest.mark.parametrize("filter_string,q_expected", [
        (u'(a=abc\u1F5E3def)', Q(**{u"a": u"abc\u1F5E3def"})),
        (u'(ansible_facts__a=abc\u1F5E3def)', Q(**{u"ansible_facts__contains": {u"a": u"abc\u1F5E3def"}})),
    ])
    def test_unicode(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert unicode(q) == unicode(q_expected)

    @pytest.mark.parametrize("filter_string,q_expected", [
        ('(a=b)', Q(**{u"a": u"b"})),
        ('a=b and c=d', Q(**{u"a": u"b"}) & Q(**{u"c": u"d"})),
        ('(a=b and c=d)', Q(**{u"a": u"b"}) & Q(**{u"c": u"d"})),
        ('a=b or c=d', Q(**{u"a": u"b"}) | Q(**{u"c": u"d"})),
        ('(a=b and c=d) or (e=f)', (Q(**{u"a": u"b"}) & Q(**{u"c": u"d"})) | (Q(**{u"e": u"f"}))),
        ('a=b or a=d or a=e or a=z and b=h and b=i and b=j and b=k', Q(**{u"a": u"b"}) | Q(**{u"a": u"d"}) | Q(**{u"a": u"e"}) | Q(**{u"a": u"z"}) & Q(**{u"b": u"h"}) & Q(**{u"b": u"i"}) & Q(**{u"b": u"j"}) & Q(**{u"b": u"k"}))
    ])
    def test_boolean_parenthesis(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert unicode(q) == unicode(q_expected)

    @pytest.mark.parametrize("filter_string,q_expected", [
        ('ansible_facts__a__b__c[]=3', Q(**{u"ansible_facts__contains": {u"a": {u"b": {u"c": [3]}}}})),
        ('ansible_facts__a__b__c[]=3.14', Q(**{u"ansible_facts__contains": {u"a": {u"b": {u"c": [3.14]}}}})),
        ('ansible_facts__a__b__c[]=true', Q(**{u"ansible_facts__contains": {u"a": {u"b": {u"c": [True]}}}})),
        ('ansible_facts__a__b__c[]=false', Q(**{u"ansible_facts__contains": {u"a": {u"b": {u"c": [False]}}}})),
        ('ansible_facts__a__b__c[]="true"', Q(**{u"ansible_facts__contains": {u"a": {u"b": {u"c": [u"true"]}}}})),
        ('ansible_facts__a__b__c[]="hello world"', Q(**{u"ansible_facts__contains": {u"a": {u"b": {u"c": [u"hello world"]}}}})),
        ('ansible_facts__a__b__c[]__d[]="foobar"', Q(**{u"ansible_facts__contains": {u"a": {u"b": {u"c": [{u"d": [u"foobar"]}]}}}})),
        ('ansible_facts__a__b__c[]__d="foobar"', Q(**{u"ansible_facts__contains": {u"a": {u"b": {u"c": [{u"d": u"foobar"}]}}}})),
        ('ansible_facts__a__b__c[]__d__e="foobar"', Q(**{u"ansible_facts__contains": {u"a": {u"b": {u"c": [{u"d": {u"e": u"foobar"}}]}}}})),
        ('ansible_facts__a__b__c[]__d__e[]="foobar"', Q(**{u"ansible_facts__contains": {u"a": {u"b": {u"c": [{u"d": {u"e": [u"foobar"]}}]}}}})),
        ('ansible_facts__a__b__c[]__d__e__f[]="foobar"', Q(**{u"ansible_facts__contains": {u"a": {u"b": {u"c": [{u"d": {u"e": {u"f": [u"foobar"]}}}]}}}})),
        ('(ansible_facts__a__b__c[]__d__e__f[]="foobar") and (ansible_facts__a__b__c[]__d__e[]="foobar")', Q(**{ u"ansible_facts__contains": {u"a": {u"b": {u"c": [{u"d": {u"e": {u"f": [u"foobar"]}}}]}}}}) & Q(**{u"ansible_facts__contains": {u"a": {u"b": {u"c": [{u"d": {u"e": [u"foobar"]}}]}}}})),
        #('"a__b\"__c"="true"', Q(**{u"a__b\"__c": "true"})),
        #('a__b\"__c="true"', Q(**{u"a__b\"__c": "true"})),
    ])
    def test_contains_query_generated(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert unicode(q) == unicode(q_expected)

    @pytest.mark.parametrize("filter_string,q_expected", [
        #('a__b__c[]="true"', Q(**{u"a__b__c__contains": u"\"true\""})),
        ('ansible_facts__a="true"', Q(**{u"ansible_facts__contains": {u"a": u"true"}})),
        #('"a__b\"__c"="true"', Q(**{u"a__b\"__c": "true"})),
        #('a__b\"__c="true"', Q(**{u"a__b\"__c": "true"})),
    ])
    def test_contains_query_generated_unicode(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert unicode(q) == unicode(q_expected)

    @pytest.mark.parametrize("filter_string,q_expected", [
        ('ansible_facts__a=null', Q(**{u"ansible_facts__contains": {u"a": u"null"}})),
        ('ansible_facts__c="null"', Q(**{u"ansible_facts__contains": {u"c": u"\"null\""}})),
    ])
    def test_contains_query_generated_null(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert unicode(q) == unicode(q_expected)


    @pytest.mark.parametrize("filter_string,q_expected", [
        ('search=foo', Q(Q(**{u"name__contains": u"foo"}) | Q(**{ u"description__contains": u"foo"}))),
        ('group__search=foo', Q(Q(**{u"group__name__contains": u"foo"}) | Q(**{u"group__description__contains": u"foo"}))),
        ('search=foo and group__search=foo', Q(
            Q(**{u"name__contains": u"foo"}) | Q(**{ u"description__contains": u"foo"}),
            Q(**{u"group__name__contains": u"foo"}) | Q(**{u"group__description__contains": u"foo"}))),
        ('search=foo or ansible_facts__a=null',
            Q(Q(**{u"name__contains": u"foo"}) | Q(**{u"description__contains": u"foo"})) |
            Q(**{u"ansible_facts__contains": {u"a": u"null"}})),
    ])
    def test_search_related_fields(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert unicode(q) == unicode(q_expected)


'''
#('"facts__quoted_val"="f\"oo"', 1),
#('facts__facts__arr[]="foo"', 1),
#('facts__facts__arr_nested[]__a[]="foo"', 1),
'''
