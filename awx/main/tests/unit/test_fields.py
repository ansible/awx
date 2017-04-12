
# Python
import pytest
from pyparsing import ParseException

# AWX
from awx.main.fields import DynamicFilterField

# Django
from django.db.models import Q


class TestDynamicFilterFieldFilterStringToQ():
    @pytest.mark.parametrize("filter_string,q_expected", [
        ('facts__facts__blank=""', Q(**{u"facts__facts__blank": u""})),
        ('"facts__facts__ space "="f"', Q(**{u"facts__facts__ space ": u"f"})),
        ('"facts__facts__ e "=no_quotes_here', Q(**{u"facts__facts__ e ": u"no_quotes_here"})),
        ('a__b__c=3', Q(**{u"a__b__c": 3})),
        ('a__b__c=3.14', Q(**{u"a__b__c": 3.14})),
        ('a__b__c=true', Q(**{u"a__b__c": True})),
        ('a__b__c=false', Q(**{u"a__b__c": False})),
        ('a__b__c="true"', Q(**{u"a__b__c": u"true"})),
        #('"a__b\"__c"="true"', Q(**{u"a__b\"__c": "true"})),
        #('a__b\"__c="true"', Q(**{u"a__b\"__c": "true"})),
    ])
    def test_query_generated(self, filter_string, q_expected):
        q = DynamicFilterField.filter_string_to_q(filter_string)
        assert unicode(q) == unicode(q_expected)

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
        assert unicode(q) == unicode(q_expected)

    @pytest.mark.parametrize("filter_string,q_expected", [
        ('(a=b)', Q(**{u"a": u"b"})),
        ('a=b and c=d', Q(**{u"a": u"b"}) & Q(**{u"c": u"d"})),
        ('(a=b and c=d)', Q(**{u"a": u"b"}) & Q(**{u"c": u"d"})),
        ('a=b or c=d', Q(**{u"a": u"b"}) | Q(**{u"c": u"d"})),
        ('(a=b and c=d) or (e=f)', (Q(**{u"a": u"b"}) & Q(**{u"c": u"d"})) | (Q(**{u"e": u"f"}))),
        ('(a=b and not c=d) or not (e=f)', (Q(**{u"a": u"b"}) & ~Q(**{u"c": u"d"})) | (~Q(**{u"e": u"f"}))),
        ('(a=b) and not (c=d or (e=f and (g=h or i=j))) or (y=z)', Q(**{u"a": u"b"}) & ~(Q(**{u"c": u"d"}) | (Q(**{u"e": u"f"}) & (Q(**{u"g": u"h"}) | Q(**{u"i": u"j"})))) | Q(**{u"y": u"z"}))
    ])
    def test_boolean_parenthesis(self, filter_string, q_expected):
        q = DynamicFilterField.filter_string_to_q(filter_string)
        assert unicode(q) == unicode(q_expected)

    @pytest.mark.parametrize("filter_string,q_expected", [
        ('a__b__c[]=3', Q(**{u"a__b__c__contains": [3]})),
        ('a__b__c[]=3.14', Q(**{u"a__b__c__contains": [3.14]})),
        ('a__b__c[]=true', Q(**{u"a__b__c__contains": [True]})),
        ('a__b__c[]=false', Q(**{u"a__b__c__contains": [False]})),
        ('a__b__c[]="true"', Q(**{u"a__b__c__contains": [u"true"]})),
        ('a__b__c[]="hello world"', Q(**{u"a__b__c__contains": [u"hello world"]})),
        ('a__b__c[]__d[]="foobar"', Q(**{u"a__b__c__contains": [{u"d": [u"foobar"]}]})),
        ('a__b__c[]__d="foobar"', Q(**{u"a__b__c__contains": [{u"d": u"foobar"}]})),
        ('a__b__c[]__d__e="foobar"', Q(**{u"a__b__c__contains": [{u"d": {u"e": u"foobar"}}]})),
        ('a__b__c[]__d__e[]="foobar"', Q(**{u"a__b__c__contains": [{u"d": {u"e": [u"foobar"]}}]})),
        ('a__b__c[]__d__e__f[]="foobar"', Q(**{u"a__b__c__contains": [{u"d": {u"e": {u"f": [u"foobar"]}}}]})),
        ('(a__b__c[]__d__e__f[]="foobar") and (a__b__c[]__d__e[]="foobar")', Q(**{ u"a__b__c__contains": [{u"d": {u"e": {u"f": [u"foobar"]}}}]}) & Q(**{u"a__b__c__contains": [{u"d": {u"e": [u"foobar"]}}]})),
        #('"a__b\"__c"="true"', Q(**{u"a__b\"__c": "true"})),
        #('a__b\"__c="true"', Q(**{u"a__b\"__c": "true"})),
    ])
    def test_contains_query_generated(self, filter_string, q_expected):
        q = DynamicFilterField.filter_string_to_q(filter_string)
        assert unicode(q) == unicode(q_expected)

    @pytest.mark.parametrize("filter_string,q_expected", [
        #('a__b__c[]="true"', Q(**{u"a__b__c__contains": u"\"true\""})),
        ('a__b__c="true"', Q(**{u"a__b__c": u"true"})),
        #('"a__b\"__c"="true"', Q(**{u"a__b\"__c": "true"})),
        #('a__b\"__c="true"', Q(**{u"a__b\"__c": "true"})),
    ])
    def test_contains_query_generated_unicode(self, filter_string, q_expected):
        q = DynamicFilterField.filter_string_to_q(filter_string)
        assert unicode(q) == unicode(q_expected)


'''
#('"facts__quoted_val"="f\"oo"', 1),
#('facts__facts__arr[]="foo"', 1),
#('facts__facts__arr_nested[]__a[]="foo"', 1), 
'''
