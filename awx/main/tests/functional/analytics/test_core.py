import importlib
import json
import os
import tarfile
from unittest import mock
import pytest

from django.conf import settings
from awx.main.analytics import gather, register


@register('example', '1.0')
def example(since):
    return {'awx': 123}


@register('bad_json', '1.0')
def bad_json(since):
    return set()


@register('throws_error', '1.0')
def throws_error(since):
    raise ValueError()
    

def _valid_license():
    pass


@pytest.fixture
def mock_valid_license():
    with mock.patch('awx.main.analytics.core._valid_license') as license:
        license.return_value = True
        yield license


@pytest.mark.django_db
def test_gather(mock_valid_license):
    settings.INSIGHTS_TRACKING_STATE = True
    
    tgz = gather(module=importlib.import_module(__name__))
    files = {}
    with tarfile.open(tgz, "r:gz") as archive:
        for member in archive.getmembers():
            files[member.name] = archive.extractfile(member)

        # functions that returned valid JSON should show up
        assert './example.json' in files.keys()
        assert json.loads(files['./example.json'].read()) == {'awx': 123}

        # functions that don't return serializable objects should not
        assert './bad_json.json' not in files.keys()
        assert './throws_error.json' not in files.keys()
    try:
        os.remove(tgz)
    except Exception:
        pass
        
