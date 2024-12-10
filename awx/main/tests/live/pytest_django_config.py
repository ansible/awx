import django

from awx import prepare_env


def pytest_load_initial_conftests(args):
    """Replacement for same-named method in pytest_django plugin

    Instead of setting up a test database, this just sets up Django normally
    this will give access to the postgres database as-is, for better and worse"""
    prepare_env()
    django.setup()
