import pytest
import random

from awx.main.models import Project
from awx.main.analytics import collectors


@pytest.mark.django_db
def test_empty():
    assert collectors.projects_by_scm_type(None) == {
        'manual': 0,
        'git': 0,
        'svn': 0,
        'hg': 0,
        'insights': 0
    }


@pytest.mark.django_db
@pytest.mark.parametrize('scm_type', [t[0] for t in Project.SCM_TYPE_CHOICES])
def test_multiple(scm_type):
    expected = {
        'manual': 0,
        'git': 0,
        'svn': 0,
        'hg': 0,
        'insights': 0
    }
    for i in range(random.randint(0, 10)):
        Project(scm_type=scm_type).save()
        expected[scm_type or 'manual'] += 1
    assert collectors.projects_by_scm_type(None) == expected
