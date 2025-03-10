import pytest
import os

from django.conf import settings

from awx.main.tests.live.tests.conftest import _copy_folders, PROJ_DATA


@pytest.fixture(scope='session')
def copy_project_folders():
    proj_root = settings.PROJECTS_ROOT
    if not os.path.exists(proj_root):
        os.mkdir(proj_root)
    _copy_folders(PROJ_DATA, proj_root, clear=True)
