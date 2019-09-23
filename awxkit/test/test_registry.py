import pytest

from awxkit.api.registry import URLRegistry


class One(object):

    pass


class Two(object):

    pass


@pytest.fixture
def reg():
    return URLRegistry()


def test_url_pattern(reg):
    desired = r'^/some/resources/\d+/(\?.*)*$'
    assert reg.url_pattern(r'/some/resources/\d+/').pattern == desired


def test_methodless_get_from_empty_registry(reg):
    assert reg.get('nonexistent') is None


def test_method_get_from_empty_registry(reg):
    assert reg.get('nonexistent', 'method') is None


def test_methodless_setdefault_methodless_get(reg):
    reg.setdefault(One)
    assert reg.get('some_path') is One


def test_methodless_setdefault_method_get(reg):
    reg.setdefault(One)
    assert reg.get('some_path', 'method') is One


def test_method_setdefault_methodless_get(reg):
    reg.setdefault('method', One)
    assert reg.get('some_path') is None


def test_method_setdefault_matching_method_get(reg):
    reg.setdefault('method', One)
    assert reg.get('some_path', 'method') is One


def test_method_setdefault_nonmatching_method_get(reg):
    reg.setdefault('method', One)
    assert reg.get('some_path', 'nonexistent') is None


def test_multimethod_setdefault_matching_method_get(reg):
    reg.setdefault(('method_one', 'method_two'), One)
    assert reg.get('some_path', 'method_one') is One
    assert reg.get('some_path', 'method_two') is One


def test_multimethod_setdefault_nonmatching_method_get(reg):
    reg.setdefault(('method_one', 'method_two'), One)
    assert reg.get('some_path') is None
    assert reg.get('some_path', 'nonexistent') is None


def test_wildcard_setdefault_methodless_get(reg):
    reg.setdefault('.*', One)
    assert reg.get('some_path') is One


def test_wildcard_setdefault_method_get(reg):
    reg.setdefault('.*', One)
    assert reg.get('some_path', 'method') is One


def test_regex_method_setdefaults_over_wildcard_method_get(reg):
    reg.setdefault('.*', One)
    reg.setdefault('reg.*ex', Two)
    for _ in range(1000):
        assert reg.get('some_path', 'regex') is Two


def test_methodless_registration_with_matching_path_methodless_get(reg):
    reg.register('some_path', One)
    assert reg.get('some_path') is One


def test_methodless_registraion_with_nonmatching_path_methodless_get(reg):
    reg.register('some_path', One)
    assert reg.get('nonexistent') is None


def test_methodless_registration_with_matching_path_nonmatching_method_get(reg):
    reg.register('some_path', One)
    assert reg.get('some_path', 'method') is None


def test_method_registration_with_matching_path_matching_method_get(reg):
    reg.register('some_path', 'method', One)
    assert reg.get('some_path', 'method') is One


def test_method_registration_with_matching_path_nonmatching_method_get(reg):
    reg.register('some_path', 'method_one', One)
    assert reg.get('some_path', 'method_two') is None


def test_multimethod_registration_with_matching_path_matching_method_get(reg):
    reg.register('some_path', ('method_one', 'method_two'), One)
    assert reg.get('some_path', 'method_one') is One
    assert reg.get('some_path', 'method_two') is One


def test_multimethod_registration_with_path_matching_method_get(reg):
    reg.register('some_path', ('method_one', 'method_two'), One)
    assert reg.get('some_path', 'method_three') is None


def test_multipath_methodless_registration_with_matching_path_methodless_get(reg):
    reg.register(('some_path_one', 'some_path_two'), One)
    assert reg.get('some_path_one') is One
    assert reg.get('some_path_two') is One


def test_multipath_methodless_registration_with_matching_path_nonmatching_method_get(reg):
    reg.register(('some_path_one', 'some_path_two'), One)
    assert reg.get('some_path_one', 'method') is None
    assert reg.get('some_path_two', 'method') is None


def test_multipath_method_registration_with_matching_path_matching_method_get(reg):
    reg.register((('some_path_one', 'method_one'), ('some_path_two', 'method_two')), One)
    assert reg.get('some_path_one', 'method_one') is One
    assert reg.get('some_path_two', 'method_two') is One


def test_multipath_partial_method_registration_with_matching_path_matching_method_get(reg):
    reg.register(('some_path_one', ('some_path_two', 'method')), One)
    assert reg.get('some_path_one') is One
    assert reg.get('some_path_two', 'method') is One


def test_wildcard_method_registration_with_methodless_get(reg):
    reg.register('some_path', '.*', One)
    assert reg.get('some_path') is One


def test_wildcard_method_registration_with_method_get(reg):
    reg.register('some_path', '.*', One)
    assert reg.get('some_path', 'method') is One


def test_wildcard_and_specific_method_registration_acts_as_default(reg):
    reg.register('some_path', 'method_one', Two)
    reg.register('some_path', '.*', One)
    reg.register('some_path', 'method_two', Two)
    for _ in range(1000):  # eliminate overt randomness
        assert reg.get('some_path', 'nonexistent') is One
        assert reg.get('some_path', 'method_one') is Two
        assert reg.get('some_path', 'method_two') is Two


@pytest.mark.parametrize('method', ('method', '.*'))
def test_multiple_method_registrations_disallowed_for_single_path_single_registration(reg, method):
    with pytest.raises(TypeError) as e:
        reg.register((('some_path', method), ('some_path', method)), One)
    assert str(e.value) == ('"{0.pattern}" already has registered method "{1}"'
                          .format(reg.url_pattern('some_path'), method))


@pytest.mark.parametrize('method', ('method', '.*'))
def test_multiple_method_registrations_disallowed_for_single_path_multiple_registrations(reg, method):
    reg.register('some_path', method, One)
    with pytest.raises(TypeError) as e:
        reg.register('some_path', method, One)
    assert str(e.value) == ('"{0.pattern}" already has registered method "{1}"'
                          .format(reg.url_pattern('some_path'), method))


def test_paths_can_be_patterns(reg):
    reg.register('.*pattern.*', One)
    assert reg.get('XYZpattern123') is One


def test_mixed_form_single_registration(reg):
    reg.register([('some_path_one', 'method_one'),
                  'some_path_two',
                  ('some_path_three', ('method_two', 'method_three')),
                  'some_path_four', 'some_path_five'], One)
    assert reg.get('some_path_one', 'method_one') is One
    assert reg.get('some_path_one') is None
    assert reg.get('some_path_one', 'nonexistent') is None
    assert reg.get('some_path_two') is One
    assert reg.get('some_path_two', 'nonexistent') is None
    assert reg.get('some_path_three', 'method_two') is One
    assert reg.get('some_path_three', 'method_three') is One
    assert reg.get('some_path_three') is None
    assert reg.get('some_path_three', 'nonexistent') is None
    assert reg.get('some_path_four') is One
    assert reg.get('some_path_four', 'nonexistent') is None
    assert reg.get('some_path_five') is One
    assert reg.get('some_path_five', 'nonexistent') is None


def test_mixed_form_single_registration_with_methodless_default(reg):
    reg.setdefault(One)
    reg.register([('some_path_one', 'method_one'),
                  'some_path_two',
                  ('some_path_three', ('method_two', 'method_three')),
                  'some_path_four', 'some_path_five'], Two)
    assert reg.get('some_path_one', 'method_one') is Two
    assert reg.get('some_path_one') is One
    assert reg.get('some_path_one', 'nonexistent') is One
    assert reg.get('some_path_two') is Two
    assert reg.get('some_path_two', 'nonexistent') is One
    assert reg.get('some_path_three', 'method_two') is Two
    assert reg.get('some_path_three', 'method_three') is Two
    assert reg.get('some_path_three') is One
    assert reg.get('some_path_three', 'nonexistent') is One
    assert reg.get('some_path_four') is Two
    assert reg.get('some_path_four', 'nonexistent') is One
    assert reg.get('some_path_five') is Two
    assert reg.get('some_path_five', 'nonexistent') is One


def test_mixed_form_single_registration_with_method_default(reg):
    reg.setdefault('existent', One)
    reg.register([('some_path_one', 'method_one'),
                  'some_path_two',
                  ('some_path_three', ('method_two', 'method_three')),
                  'some_path_four', 'some_path_five'], Two)
    assert reg.get('some_path_one', 'method_one') is Two
    assert reg.get('some_path_one') is None
    assert reg.get('some_path_one', 'existent') is One
    assert reg.get('some_path_one', 'nonexistent') is None
    assert reg.get('some_path_two') is Two
    assert reg.get('some_path_two', 'existent') is One
    assert reg.get('some_path_two', 'nonexistent') is None
    assert reg.get('some_path_three', 'method_two') is Two
    assert reg.get('some_path_three', 'method_three') is Two
    assert reg.get('some_path_three') is None
    assert reg.get('some_path_three', 'existent') is One
    assert reg.get('some_path_three', 'nonexistent') is None
    assert reg.get('some_path_four') is Two
    assert reg.get('some_path_four', 'existent') is One
    assert reg.get('some_path_four', 'nonexistent') is None
    assert reg.get('some_path_five') is Two
    assert reg.get('some_path_five', 'existent') is One
    assert reg.get('some_path_five', 'nonexistent') is None
