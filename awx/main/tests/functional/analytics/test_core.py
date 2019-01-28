import importlib
import json
import os
import tarfile

import pytest

from awx.main.analytics import gather, register


@register('example')
def example(since):
    return {'awx': 123}


@register('bad_json')
def bad_json(since):
    return set()


@register('throws_error')
def throws_error(since):
    raise ValueError()


@pytest.mark.django_db
def test_gather():
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
