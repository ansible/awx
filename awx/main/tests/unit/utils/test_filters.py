# Python
import pytest
from unittest import mock

# AWX
from awx.main.utils.filters import SmartFilter, ExternalLoggerEnabled

# Django
from django.db.models import Q


@pytest.mark.parametrize(
    'params, logger_name, expected',
    [
        # skip all records if enabled_flag = False
        ({'enabled_flag': False}, 'awx.main', False),
        # skip all records if the host is undefined
        ({'enabled_flag': True}, 'awx.main', False),
        # skip all records if underlying logger is used by handlers themselves
        ({'enabled_flag': True}, 'awx.main.utils.handlers', False),
        ({'enabled_flag': True, 'enabled_loggers': ['awx']}, 'awx.main', True),
        ({'enabled_flag': True, 'enabled_loggers': ['abc']}, 'awx.analytics.xyz', False),
        ({'enabled_flag': True, 'enabled_loggers': ['xyz']}, 'awx.analytics.xyz', True),
    ],
)
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
        self._fields = {f.name: f for f in fields}
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
        self._meta = Meta(fields=[Field(name='password', __prevent_search__=True)])


class mockHost:
    def __init__(self):
        print("Host mock created")
        self.objects = mockObjects()
        fields = [Field(name='name'), Field(name='description'), Field(name='created_by', related_model=mockUser())]
        self._meta = Meta(fields=fields)


@mock.patch('awx.main.utils.filters.get_model', return_value=mockHost())
class TestSmartFilterQueryFromString:
    @mock.patch(
        'ansible_base.rest_filters.rest_framework.field_lookup_backend.get_fields_from_path', lambda model, path, **kwargs: ([model], path)
    )  # disable field filtering, because a__b isn't a real Host field
    @pytest.mark.parametrize(
        "filter_string,q_expected",
        [
            ('facts__facts__blank=""', Q(**{"facts__facts__blank": ""})),
            ('"facts__facts__ space "="f"', Q(**{"facts__facts__ space ": "f"})),
            ('"facts__facts__ e "=no_quotes_here', Q(**{"facts__facts__ e ": "no_quotes_here"})),
            ('a__b__c=3', Q(**{"a__b__c": 3})),
            ('a__b__c=3.14', Q(**{"a__b__c": 3.14})),
            ('a__b__c=true', Q(**{"a__b__c": True})),
            ('a__b__c=false', Q(**{"a__b__c": False})),
            ('a__b__c=null', Q(**{"a__b__c": None})),
            ('ansible_facts__a="true"', Q(**{"ansible_facts__contains": {"a": "true"}})),
            ('ansible_facts__a__exact="true"', Q(**{"ansible_facts__contains": {"a": "true"}})),
            # ('"a__b\"__c"="true"', Q(**{u"a__b\"__c": "true"})),
            # ('a__b\"__c="true"', Q(**{u"a__b\"__c": "true"})),
        ],
    )
    def test_query_generated(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)

    @pytest.mark.parametrize(
        "filter_string",
        [
            'ansible_facts__facts__facts__blank=ansible_facts__a__b__c__ space  =ggg',
        ],
    )
    def test_invalid_filter_strings(self, mock_get_host_model, filter_string):
        with pytest.raises(RuntimeError) as e:
            SmartFilter.query_from_string(filter_string)
        assert str(e.value) == "Invalid query " + filter_string

    @pytest.mark.parametrize(
        "filter_string",
        [
            'created_by__password__icontains=pbkdf2search=foo or created_by__password__icontains=pbkdf2',
            'created_by__password__icontains=pbkdf2 or search=foo',
        ],
    )
    def test_forbidden_filter_string(self, mock_get_host_model, filter_string):
        with pytest.raises(Exception) as e:
            SmartFilter.query_from_string(filter_string)
        "Filtering on password is not allowed." in str(e)

    @pytest.mark.parametrize(
        "filter_string,q_expected",
        [
            ('(a=abc\u1f5e3def)', Q(**{"a": "abc\u1f5e3def"})),
            ('(ansible_facts__a=abc\u1f5e3def)', Q(**{"ansible_facts__contains": {"a": "abc\u1f5e3def"}})),
        ],
    )
    def test_unicode(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)

    @pytest.mark.parametrize(
        "filter_string,q_expected",
        [
            ('(a=b)', Q(**{"a": "b"})),
            ('a=b and c=d', Q(**{"a": "b"}) & Q(**{"c": "d"})),
            ('(a=b and c=d)', Q(**{"a": "b"}) & Q(**{"c": "d"})),
            ('a=b or c=d', Q(**{"a": "b"}) | Q(**{"c": "d"})),
            ('(a=b and c=d) or (e=f)', (Q(**{"a": "b"}) & Q(**{"c": "d"})) | (Q(**{"e": "f"}))),
            (
                'a=b or a=d or a=e or a=z and b=h and b=i and b=j and b=k',
                Q(**{"a": "b"}) | Q(**{"a": "d"}) | Q(**{"a": "e"}) | Q(**{"a": "z"}) & Q(**{"b": "h"}) & Q(**{"b": "i"}) & Q(**{"b": "j"}) & Q(**{"b": "k"}),
            ),
        ],
    )
    def test_boolean_parenthesis(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)

    @pytest.mark.parametrize(
        "filter_string,q_expected",
        [
            ('ansible_facts__a__b__c[]=3', Q(**{"ansible_facts__contains": {"a": {"b": {"c": [3]}}}})),
            ('ansible_facts__a__b__c[]=3.14', Q(**{"ansible_facts__contains": {"a": {"b": {"c": [3.14]}}}})),
            ('ansible_facts__a__b__c[]=true', Q(**{"ansible_facts__contains": {"a": {"b": {"c": [True]}}}})),
            ('ansible_facts__a__b__c[]=false', Q(**{"ansible_facts__contains": {"a": {"b": {"c": [False]}}}})),
            ('ansible_facts__a__b__c[]="true"', Q(**{"ansible_facts__contains": {"a": {"b": {"c": ["true"]}}}})),
            ('ansible_facts__a__b__c[]="hello world"', Q(**{"ansible_facts__contains": {"a": {"b": {"c": ["hello world"]}}}})),
            ('ansible_facts__a__b__c[]__d[]="foobar"', Q(**{"ansible_facts__contains": {"a": {"b": {"c": [{"d": ["foobar"]}]}}}})),
            ('ansible_facts__a__b__c[]__d="foobar"', Q(**{"ansible_facts__contains": {"a": {"b": {"c": [{"d": "foobar"}]}}}})),
            ('ansible_facts__a__b__c[]__d__e="foobar"', Q(**{"ansible_facts__contains": {"a": {"b": {"c": [{"d": {"e": "foobar"}}]}}}})),
            ('ansible_facts__a__b__c[]__d__e[]="foobar"', Q(**{"ansible_facts__contains": {"a": {"b": {"c": [{"d": {"e": ["foobar"]}}]}}}})),
            ('ansible_facts__a__b__c[]__d__e__f[]="foobar"', Q(**{"ansible_facts__contains": {"a": {"b": {"c": [{"d": {"e": {"f": ["foobar"]}}}]}}}})),
            (
                '(ansible_facts__a__b__c[]__d__e__f[]="foobar") and (ansible_facts__a__b__c[]__d__e[]="foobar")',
                Q(**{"ansible_facts__contains": {"a": {"b": {"c": [{"d": {"e": {"f": ["foobar"]}}}]}}}})
                & Q(**{"ansible_facts__contains": {"a": {"b": {"c": [{"d": {"e": ["foobar"]}}]}}}}),
            ),
            # ('"a__b\"__c"="true"', Q(**{u"a__b\"__c": "true"})),
            # ('a__b\"__c="true"', Q(**{u"a__b\"__c": "true"})),
        ],
    )
    def test_contains_query_generated(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)

    @pytest.mark.parametrize(
        "filter_string,q_expected",
        [
            # ('a__b__c[]="true"', Q(**{u"a__b__c__contains": u"\"true\""})),
            ('ansible_facts__a="true"', Q(**{"ansible_facts__contains": {"a": "true"}})),
            # ('"a__b\"__c"="true"', Q(**{u"a__b\"__c": "true"})),
            # ('a__b\"__c="true"', Q(**{u"a__b\"__c": "true"})),
        ],
    )
    def test_contains_query_generated_unicode(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)

    @pytest.mark.parametrize(
        "filter_string,q_expected",
        [
            ('ansible_facts__a=null', Q(**{"ansible_facts__contains": {"a": None}})),
            ('ansible_facts__c="null"', Q(**{"ansible_facts__contains": {"c": "\"null\""}})),
        ],
    )
    def test_contains_query_generated_null(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)

    @pytest.mark.parametrize(
        "filter_string,q_expected",
        [
            ('group__search=foo', Q(Q(**{"group__name__icontains": "foo"}) | Q(**{"group__description__icontains": "foo"}))),
            (
                'search=foo and group__search=foo',
                Q(
                    Q(**{"name__icontains": "foo"}) | Q(**{"description__icontains": "foo"}),
                    Q(**{"group__name__icontains": "foo"}) | Q(**{"group__description__icontains": "foo"}),
                ),
            ),
            (
                'search=foo or ansible_facts__a=null',
                Q(Q(**{"name__icontains": "foo"}) | Q(**{"description__icontains": "foo"})) | Q(**{"ansible_facts__contains": {"a": None}}),
            ),
        ],
    )
    def test_search_related_fields(self, mock_get_host_model, filter_string, q_expected):
        q = SmartFilter.query_from_string(filter_string)
        assert str(q) == str(q_expected)


'''
#('"facts__quoted_val"="f\"oo"', 1),
#('facts__facts__arr[]="foo"', 1),
#('facts__facts__arr_nested[]__a[]="foo"', 1),
'''
