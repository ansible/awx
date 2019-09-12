
# Python
import pytest
from unittest import mock

# AWX
from awx.main.utils.filters import SmartFilter, ExternalLoggerEnabled
from awx.main.models import Host

# Django
from django.db.models import Q



@pytest.mark.parametrize('params, logger_name, expected', [
    # skip all records if enabled_flag = False
    ({'enabled_flag': False}, 'awx.main', False),
    # skip all records if the host is undefined
    ({'enabled_flag': True}, 'awx.main', False),
    # skip all records if underlying logger is used by handlers themselves
    ({'enabled_flag': True}, 'awx.main.utils.handlers', False),
    ({'enabled_flag': True, 'enabled_loggers': ['awx']}, 'awx.main', True),
    ({'enabled_flag': True, 'enabled_loggers': ['abc']}, 'awx.analytics.xyz', False),
    ({'enabled_flag': True, 'enabled_loggers': ['xyz']}, 'awx.analytics.xyz', True),
])
def test_base_logging_handler_skip_log(params, logger_name, expected, dummy_log_record):
    filter = ExternalLoggerEnabled(**params)
    dummy_log_record.name = logger_name
    assert filter.filter(dummy_log_record) is expected, (params, logger_name)


class Field(object):

    def __init__(self, name, related_model=None, __prevent_search__=None):
        self.name = name
        self.related_model = related_model
        self.__prevent_search__ = __prevent_search__


class Meta(object):

    def __init__(self, fields):
        self._fields = {
            f.name: f for f in fields
        }
        self.object_name = 'Host'
        self.fields_map = {}
        self.fields = self._fields.values()

    def get_field(self, f):
        return self._fields.get(f)


class mockObjects:
    def filter(self, *args, **kwargs):
        return Q(*args, **kwargs)


class mockUser:
    def __init__(self):
        print("Host user created")
        self._meta = Meta(fields=[
            Field(name='password', __prevent_search__=True)
        ])


class mockHost:
    def __init__(self):
        print("Host mock created")
        self.objects = mockObjects()
        fields = [
            Field(name='name'),
            Field(name='description'),
            Field(name='created_by', related_model=mockUser())
        ]
        self._meta = Meta(fields=fields)


@mock.patch('awx.main.utils.filters.get_model', return_value=mockHost())
class TestSmartFilterQueryFromString():
    @mock.patch(
        'awx.api.filters.get_fields_from_path',
        lambda model, path: ([model], path)  # disable field filtering, because a__b isn't a real Host field
    )
    @pytest.mark.parametrize("filter_string,q_expected", [
        ('facts__facts__blank=""', Q(**{u"facts__facts__blank": u""})),
        ('"facts__facts__ space "="f"', Q(**{u"facts__facts__ space ": u"f"})),
        ('"facts__facts__ e "=no_quotes_here', Q(**{u"facts__facts__ e ": u"no_quotes_here"})),
        ('a__b__c=3', Q(**{u"a__b__c": 3})),
        ('a__b__c=3.14', Q(**{u"a__b__c": 3.14})),
        ('a__b__c=true', Q(**{u"a__b__c": True})),
        ('a__b__c=false', Q(**{u"a__b__c": False})),
        ('a__b__c=null', Q(**{u"a__b__c": None})),
        ('ansible_facts__a="true"', Q(**{u"ansible_facts__contains": {u"a": u"true"}})),
        ('ansible_facts__a__exact="true"', Q(**{u"ansible_facts__contains": {u"a": u"true"}})),
        #('"a__b\"__c"="true"', Q(**{u"a__b\"__c": "true"})),
        #('a__b\"__c="true"', Q(**{u"a__b\"__c": "true"})),
    ])
    def test_query_generated(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)

    @pytest.mark.parametrize("filter_string", [
        'ansible_facts__facts__facts__blank='
        'ansible_facts__a__b__c__ space  =ggg',
    ])
    def test_invalid_filter_strings(self, mock_get_host_model, filter_string):
        with pytest.raises(RuntimeError) as e:
            SmartFilter.query_from_string(filter_string)
        assert str(e.value) == u"Invalid query " + filter_string

    @pytest.mark.parametrize("filter_string", [
        'created_by__password__icontains=pbkdf2'
        'search=foo or created_by__password__icontains=pbkdf2',
        'created_by__password__icontains=pbkdf2 or search=foo',
    ])
    def test_forbidden_filter_string(self, mock_get_host_model, filter_string):
        with pytest.raises(Exception) as e:
            SmartFilter.query_from_string(filter_string)
        "Filtering on password is not allowed." in str(e)

    @pytest.mark.parametrize("filter_string,q_expected", [
        (u'(a=abc\u1F5E3def)', Q(**{u"a": u"abc\u1F5E3def"})),
        (u'(ansible_facts__a=abc\u1F5E3def)', Q(**{u"ansible_facts__contains": {u"a": u"abc\u1F5E3def"}})),
    ])
    def test_unicode(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)

    @pytest.mark.parametrize("filter_string,q_expected", [
        ('(a=b)', Q(**{u"a": u"b"})),
        ('a=b and c=d', Q(**{u"a": u"b"}) & Q(**{u"c": u"d"})),
        ('(a=b and c=d)', Q(**{u"a": u"b"}) & Q(**{u"c": u"d"})),
        ('a=b or c=d', Q(**{u"a": u"b"}) | Q(**{u"c": u"d"})),
        ('(a=b and c=d) or (e=f)', (Q(**{u"a": u"b"}) & Q(**{u"c": u"d"})) | (Q(**{u"e": u"f"}))),
        (
            'a=b or a=d or a=e or a=z and b=h and b=i and b=j and b=k',
            Q(**{u"a": u"b"}) | Q(**{u"a": u"d"}) | Q(**{u"a": u"e"}) | Q(**{u"a": u"z"}) &
            Q(**{u"b": u"h"}) & Q(**{u"b": u"i"}) & Q(**{u"b": u"j"}) & Q(**{u"b": u"k"})
        )
    ])
    def test_boolean_parenthesis(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)

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
        (
            '(ansible_facts__a__b__c[]__d__e__f[]="foobar") and (ansible_facts__a__b__c[]__d__e[]="foobar")',
            Q(**{ u"ansible_facts__contains": {u"a": {u"b": {u"c": [{u"d": {u"e": {u"f": [u"foobar"]}}}]}}}}) &
            Q(**{u"ansible_facts__contains": {u"a": {u"b": {u"c": [{u"d": {u"e": [u"foobar"]}}]}}}})),
        #('"a__b\"__c"="true"', Q(**{u"a__b\"__c": "true"})),
        #('a__b\"__c="true"', Q(**{u"a__b\"__c": "true"})),
    ])
    def test_contains_query_generated(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)

    @pytest.mark.parametrize("filter_string,q_expected", [
        #('a__b__c[]="true"', Q(**{u"a__b__c__contains": u"\"true\""})),
        ('ansible_facts__a="true"', Q(**{u"ansible_facts__contains": {u"a": u"true"}})),
        #('"a__b\"__c"="true"', Q(**{u"a__b\"__c": "true"})),
        #('a__b\"__c="true"', Q(**{u"a__b\"__c": "true"})),
    ])
    def test_contains_query_generated_unicode(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)

    @pytest.mark.parametrize("filter_string,q_expected", [
        ('ansible_facts__a=null', Q(**{u"ansible_facts__contains": {u"a": None}})),
        ('ansible_facts__c="null"', Q(**{u"ansible_facts__contains": {u"c": u"\"null\""}})),
    ])
    def test_contains_query_generated_null(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)


    @pytest.mark.parametrize("filter_string,q_expected", [
        ('group__search=foo', Q(Q(**{u"group__name__icontains": u"foo"}) | Q(**{u"group__description__icontains": u"foo"}))),
        ('search=foo and group__search=foo', Q(
            Q(**{u"name__icontains": u"foo"}) | Q(**{ u"description__icontains": u"foo"}),
            Q(**{u"group__name__icontains": u"foo"}) | Q(**{u"group__description__icontains": u"foo"}))),
        ('search=foo or ansible_facts__a=null',
            Q(Q(**{u"name__icontains": u"foo"}) | Q(**{u"description__icontains": u"foo"})) |
            Q(**{u"ansible_facts__contains": {u"a": None}})),
    ])
    def test_search_related_fields(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)


class TestSmartFilterQueryFromStringNoDB():
    @pytest.mark.parametrize("filter_string,q_expected", [
        ('ansible_facts__a="true" and ansible_facts__b="true" and ansible_facts__c="true"',
            (Q(**{u"ansible_facts__contains": {u"a": u"true"}}) &
             Q(**{u"ansible_facts__contains": {u"b": u"true"}}) &
             Q(**{u"ansible_facts__contains": {u"c": u"true"}}))),
        ('ansible_facts__a="true" or ansible_facts__b="true" or ansible_facts__c="true"',
            (Q(**{u"ansible_facts__contains": {u"a": u"true"}}) |
             Q(**{u"ansible_facts__contains": {u"b": u"true"}}) |
             Q(**{u"ansible_facts__contains": {u"c": u"true"}}))),
        ('search=foo',
            Q(Q(**{ u"description__icontains": u"foo"}) | Q(**{u"name__icontains": u"foo"}))),
        ('search=foo and ansible_facts__a="null"',
            Q(Q(**{u"description__icontains": u"foo"}) | Q(**{u"name__icontains": u"foo"})) &
            Q(**{u"ansible_facts__contains": {u"a": u"\"null\""}})),
        ('name=foo or name=bar and name=foobar',
            Q(name="foo") | Q(name="bar") & Q(name="foobar"))
    ])
    def test_does_not_invoke_db(self, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q.query) == str(Host.objects.filter(q_expected).query)


'''
#('"facts__quoted_val"="f\"oo"', 1),
#('facts__facts__arr[]="foo"', 1),
#('facts__facts__arr_nested[]__a[]="foo"', 1),
'''
