import importlib
import json
import os
import tarfile
import pytest

from django.conf import settings
from awx.main.analytics import AnalyticsCollector
from insights_analytics_collector import register


@register('config', '1.0', config=True)
def config(since, **kwargs):
    return {'required': 'yes'}


@register('example', '1.0')
def example(since, **kwargs):
    return {'awx': 123}


@register('bad_json', '1.0')
def bad_json(since, **kwargs):
    return set()


@register('throws_error', '1.0')
def throws_error(since, **kwargs):
    raise ValueError()


@pytest.fixture
def collector(mocker):
    collector = AnalyticsCollector(collector_module=importlib.import_module(__name__), collection_type=AnalyticsCollector.DRY_RUN)
    mocker.patch.object(collector, '_is_valid_license', return_value=True)
    mocker.patch.object(collector, 'config_present', return_value=True)

    return collector


@pytest.mark.django_db
def test_gather(collector):
    settings.INSIGHTS_TRACKING_STATE = True
    tgzfiles = collector.gather()
    files = {}
    with tarfile.open(tgzfiles[0], "r:gz") as archive:
        for member in archive.getmembers():
            files[member.name] = archive.extractfile(member)

        # functions that returned valid JSON should show up
        assert './config.json' in files.keys()
        assert json.loads(files['./config.json'].read()) == {'required': 'yes'}
        assert './example.json' in files.keys()
        assert json.loads(files['./example.json'].read()) == {'awx': 123}

        # functions that don't return serializable objects should not
        assert './bad_json.json' not in files.keys()
        assert './throws_error.json' not in files.keys()
    try:
        for tgz in tgzfiles:
            os.remove(tgz)
    except Exception:
        pass
