
# Python
import pytest
from pyparsing import ParseException

# AWX
from awx.main.fields import DynamicFilterField

# Django
from django.db.models import Q


class TestDynamicFilterFieldFilterStringToQ():
    @pytest.mark.parametrize("filter_string,q_expected", [
        ('facts__facts__blank=""', Q(facts__facts__blank="")),
        ('"facts__facts__ space "="f"', Q(**{ "facts__facts__ space ": "f"})),
        ('"facts__facts__ e "=no_quotes_here', Q(**{ "facts__facts__ e ": "no_quotes_here"})),
        ('a__b__c=3', Q(**{ "a__b__c": 3})),
        ('a__b__c=3.14', Q(**{ "a__b__c": 3.14})),
        ('a__b__c=true', Q(**{ "a__b__c": True})),
        ('a__b__c=false', Q(**{ "a__b__c": False})),
        ('a__b__c="true"', Q(**{ "a__b__c": "true"})),
        #('"a__b\"__c"="true"', Q(**{ "a__b\"__c": "true"})),
        #('a__b\"__c="true"', Q(**{ "a__b\"__c": "true"})),
    ])
    def test_query_generated(self, filter_string, q_expected):
        q = DynamicFilterField.filter_string_to_q(filter_string)
        assert str(q) == str(q_expected)

    @pytest.mark.parametrize("filter_string", [
        'facts__facts__blank='
        'a__b__c__ space  =ggg',
    ])
    def test_invalid_filter_strings(self, filter_string):
        with pytest.raises(ParseException):
            DynamicFilterField.filter_string_to_q(filter_string)

    @pytest.mark.parametrize("filter_string,q_expected", [
        (u'(a=abc\u1F5E3def)', Q(**{u"a": u"abc\u1F5E3def"})),
    ])
    def test_unicode(self, filter_string, q_expected):
        q = DynamicFilterField.filter_string_to_q(filter_string)
        assert str(q) == str(q_expected)

    @pytest.mark.parametrize("filter_string,q_expected", [
        ('(a=b)', Q(**{"a": "b"})),
        ('a=b and c=d', Q(**{"a": "b"}) & Q(**{"c": "d"})),
        ('(a=b and c=d)', Q(**{"a": "b"}) & Q(**{"c": "d"})),
        ('a=b or c=d', Q(**{"a": "b"}) | Q(**{"c": "d"})),
        ('(a=b and c=d) or (e=f)', (Q(**{"a": "b"}) & Q(**{"c": "d"})) | (Q(**{"e": "f"}))),
        ('(a=b) and (c=d or (e=f and (g=h or i=j))) or (y=z)', Q(**{"a": "b"}) & (Q(**{"c": "d"}) | (Q(**{"e": "f"}) & (Q(**{"g": "h"}) | Q(**{"i": "j"})))) | Q(**{"y": "z"}))
    ])
    def test_boolean_parenthesis(self, filter_string, q_expected):
        q = DynamicFilterField.filter_string_to_q(filter_string)
        assert str(q) == str(q_expected)

    @pytest.mark.parametrize("filter_string,q_expected", [
        ('a__b__c[]=3', Q(**{ "a__b__c__contains": 3})),
        ('a__b__c[]=3.14', Q(**{ "a__b__c__contains": 3.14})),
        ('a__b__c[]=true', Q(**{ "a__b__c__contains": True})),
        ('a__b__c[]=false', Q(**{ "a__b__c__contains": False})),
        ('a__b__c[]="true"', Q(**{ "a__b__c__contains": "true"})),
        ('a__b__c[]__d[]="foobar"', Q(**{ "a__b__c__contains": [{"d": ["foobar"]}]})),
        ('a__b__c[]__d="foobar"', Q(**{ "a__b__c__contains": [{"d": "foobar"}]})),
        ('a__b__c[]__d__e="foobar"', Q(**{ "a__b__c__contains": [{"d": {"e": "foobar"}}]})),
        ('a__b__c[]__d__e[]="foobar"', Q(**{ "a__b__c__contains": [{"d": {"e": ["foobar"]}}]})),
        ('a__b__c[]__d__e__f[]="foobar"', Q(**{ "a__b__c__contains": [{"d": {"e": {"f": ["foobar"]}}}]})),
        ('(a__b__c[]__d__e__f[]="foobar") and (a__b__c[]__d__e[]="foobar")', Q(**{ "a__b__c__contains": [{"d": {"e": {"f": ["foobar"]}}}]}) & Q(**{ "a__b__c__contains": [{"d": {"e": ["foobar"]}}]})),
        #('"a__b\"__c"="true"', Q(**{ "a__b\"__c": "true"})),
        #('a__b\"__c="true"', Q(**{ "a__b\"__c": "true"})),
    ])
    def test_contains_query_generated(self, filter_string, q_expected):
        q = DynamicFilterField.filter_string_to_q(filter_string)
        assert str(q) == str(q_expected)


'''
#('"facts__quoted_val"="f\"oo"', 1),
#('facts__facts__arr[]="foo"', 1),
#('facts__facts__arr_nested[]__a[]="foo"', 1), 
'''
