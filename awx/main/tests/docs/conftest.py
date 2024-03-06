from awx.main.tests.functional.conftest import *  # noqa
import os
import pytest


@pytest.fixture()
def release():
    return os.environ.get('VERSION_TARGET', '')
