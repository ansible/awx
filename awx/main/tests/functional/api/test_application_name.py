import pytest
from awx.settings.application_name import get_service_name, set_application_name


@pytest.mark.parametrize(
    'argv,result',
    (
        ([], None),
        (['-m'], None),
        (['-m', 'python'], None),
        (['-m', 'python', 'manage'], None),
        (['-m', 'python', 'manage', 'a'], 'a'),
        (['-m', 'python', 'manage', 'b', 'a'], 'b'),
        (['-m', 'python', 'manage', 'run_something', 'b', 'a'], 'something'),
    ),
)
def test_get_service_name(argv, result):
    assert get_service_name(argv) == result


@pytest.mark.parametrize('DATABASES,CLUSTER_ID,function', (({}, 12, ''), ({'default': {'ENGINE': 'sqllite3'}}, 12, '')))
def test_set_application_name(DATABASES, CLUSTER_ID, function):
    set_application_name(DATABASES, CLUSTER_ID, function)
