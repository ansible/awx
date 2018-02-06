from awx.main.tests.functional.conftest import *  # noqa


def pytest_addoption(parser):
    parser.addoption("--release", action="store", help="a release version number, e.g., 3.3.0")


def pytest_generate_tests(metafunc):
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".
    option_value = metafunc.config.option.release
    if 'release' in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("release", [option_value])
