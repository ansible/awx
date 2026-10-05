# This conftest registers pytest-django CLI options and INI keys as harmless
# no-ops so that the awxkit tox environment (which does not install Django or
# pytest-django) does not crash when the root pytest.ini config leaks through.
#
# Root pytest.ini contains settings like --reuse-db, --nomigrations, and
# DJANGO_SETTINGS_MODULE that are only meaningful for Django tests.  Placing
# this conftest at the awxkit/ level ensures it is loaded before argument
# parsing regardless of which config file pytest ultimately selects.


def pytest_addoption(parser):
    group = parser.getgroup("awxkit-compat", "awxkit tox compatibility shims")
    group.addoption("--reuse-db", action="store_true", default=False, help="(no-op in awxkit) pytest-django compat")
    group.addoption("--nomigrations", action="store_true", default=False, help="(no-op in awxkit) pytest-django compat")
    group.addoption("--create-db", action="store_true", default=False, help="(no-op in awxkit) pytest-django compat")
    parser.addini("DJANGO_SETTINGS_MODULE", help="(no-op in awxkit) pytest-django compat", default="")
