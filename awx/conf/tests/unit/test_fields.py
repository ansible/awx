import pytest

from rest_framework.fields import ValidationError
from awx.conf.fields import StringListBooleanField, StringListPathField, ListTuplesField, URLField


class TestStringListBooleanField():

    FIELD_VALUES = [
        ("hello", "hello"),
        (("a", "b"), ["a", "b"]),
        (["a", "b", 1, 3.13, "foo", "bar", "foobar"], ["a", "b", "1", "3.13", "foo", "bar", "foobar"]),
        ("True", True),
        ("TRUE", True),
        ("true", True),
        (True, True),
        ("False", False),
        ("FALSE", False),
        ("false", False),
        (False, False),
        ("", None),
        ("null", None),
        ("NULL", None),
    ]

    FIELD_VALUES_INVALID = [
        1.245,
        {"a": "b"},
    ]

    @pytest.mark.parametrize("value_in, value_known", FIELD_VALUES)
    def test_to_internal_value_valid(self, value_in, value_known):
        field = StringListBooleanField()
        v = field.to_internal_value(value_in)
        assert v == value_known

    @pytest.mark.parametrize("value", FIELD_VALUES_INVALID)
    def test_to_internal_value_invalid(self, value):
        field = StringListBooleanField()
        with pytest.raises(ValidationError) as e:
            field.to_internal_value(value)
        assert e.value.detail[0] == "Expected None, True, False, a string or list " \
            "of strings but got {} instead.".format(type(value))

    @pytest.mark.parametrize("value_in, value_known", FIELD_VALUES)
    def test_to_representation_valid(self, value_in, value_known):
        field = StringListBooleanField()
        v = field.to_representation(value_in)
        assert v == value_known

    @pytest.mark.parametrize("value", FIELD_VALUES_INVALID)
    def test_to_representation_invalid(self, value):
        field = StringListBooleanField()
        with pytest.raises(ValidationError) as e:
            field.to_representation(value)
        assert e.value.detail[0] == "Expected None, True, False, a string or list " \
            "of strings but got {} instead.".format(type(value))


class TestListTuplesField():

    FIELD_VALUES = [
        ([('a', 'b'), ('abc', '123')], [("a", "b"), ("abc", "123")]),
    ]

    FIELD_VALUES_INVALID = [
        ("abc", type("abc")),
        ([('a', 'b', 'c'), ('abc', '123', '456')], type(('a',))),
        (['a', 'b'], type('a')),
        (123, type(123)),
    ]

    @pytest.mark.parametrize("value_in, value_known", FIELD_VALUES)
    def test_to_internal_value_valid(self, value_in, value_known):
        field = ListTuplesField()
        v = field.to_internal_value(value_in)
        assert v == value_known

    @pytest.mark.parametrize("value, t", FIELD_VALUES_INVALID)
    def test_to_internal_value_invalid(self, value, t):
        field = ListTuplesField()
        with pytest.raises(ValidationError) as e:
            field.to_internal_value(value)
        assert e.value.detail[0] == "Expected a list of tuples of max length 2 " \
            "but got {} instead.".format(t)


class TestStringListPathField():

    FIELD_VALUES = [
        ((".", "..", "/"), [".", "..", "/"]),
        (("/home",), ["/home"]),
        (("///home///",), ["/home"]),
        (("/home/././././",), ["/home"]),
        (("/home", "/home", "/home/"), ["/home"]),
        (["/home/", "/home/", "/opt/", "/opt/", "/var/"], ["/home", "/opt", "/var"])
    ]

    FIELD_VALUES_INVALID_TYPE = [
        1.245,
        {"a": "b"},
        ("/home"),
    ]

    FIELD_VALUES_INVALID_PATH = [
        "",
        "~/",
        "home",
        "/invalid_path",
        "/home/invalid_path",
    ]

    @pytest.mark.parametrize("value_in, value_known", FIELD_VALUES)
    def test_to_internal_value_valid(self, value_in, value_known):
        field = StringListPathField()
        v = field.to_internal_value(value_in)
        assert v == value_known

    @pytest.mark.parametrize("value", FIELD_VALUES_INVALID_TYPE)
    def test_to_internal_value_invalid_type(self, value):
        field = StringListPathField()
        with pytest.raises(ValidationError) as e:
            field.to_internal_value(value)
        assert e.value.detail[0] == "Expected list of strings but got {} instead.".format(type(value))

    @pytest.mark.parametrize("value", FIELD_VALUES_INVALID_PATH)
    def test_to_internal_value_invalid_path(self, value):
        field = StringListPathField()
        with pytest.raises(ValidationError) as e:
            field.to_internal_value([value])
        assert e.value.detail[0] == "{} is not a valid path choice.".format(value)


class TestURLField():
    regex = "^https://www.example.org$"

    @pytest.mark.parametrize("url,schemes,regex, allow_numbers_in_top_level_domain, expect_no_error",[
        ("ldap://www.example.org42", "ldap", None, True, True),
        ("https://www.example.org42", "https", None, False, False),
        ("https://www.example.org", None,  regex, None, True),
        ("https://www.example3.org", None, regex, None, False),
        ("ftp://www.example.org", "https", None, None, False)
    ])
    def test_urls(self, url, schemes, regex, allow_numbers_in_top_level_domain, expect_no_error):
        kwargs = {}
        kwargs.setdefault("allow_numbers_in_top_level_domain", allow_numbers_in_top_level_domain)
        kwargs.setdefault("schemes", schemes)
        kwargs.setdefault("regex", regex)
        field = URLField(**kwargs)
        if expect_no_error:
            field.run_validators(url)
        else:
            with pytest.raises(ValidationError):
                field.run_validators(url)
