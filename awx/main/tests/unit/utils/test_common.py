# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.
import os
import pytest
from uuid import uuid4

from django.core.cache import cache

from awx.main.utils import common

from awx.main.models import (
    Job,
    AdHocCommand,
    InventoryUpdate,
    ProjectUpdate,
    SystemJob,
    WorkflowJob
)


@pytest.fixture(autouse=True)
def clear_cache():
    '''
    Clear cache (local memory) for each test to prevent using cached settings.
    '''
    cache.clear()


@pytest.mark.parametrize('input_, output', [
    ({"foo": "bar"}, {"foo": "bar"}),
    ('{"foo": "bar"}', {"foo": "bar"}),
    ('---\nfoo: bar', {"foo": "bar"}),
    (4399, {}),
])
def test_parse_yaml_or_json(input_, output):
    assert common.parse_yaml_or_json(input_) == output


def test_set_environ():
    key = str(uuid4())
    old_environ = os.environ.copy()
    with common.set_environ(**{key: 'bar'}):
        assert os.environ[key] == 'bar'
        assert set(os.environ.keys()) - set(old_environ.keys()) == set([key])
    assert os.environ == old_environ
    assert key not in os.environ


# Cases relied on for scheduler dependent jobs list
@pytest.mark.parametrize('model,name', [
    (Job, 'job'),
    (AdHocCommand, 'ad_hoc_command'),
    (InventoryUpdate, 'inventory_update'),
    (ProjectUpdate, 'project_update'),
    (SystemJob, 'system_job'),
    (WorkflowJob, 'workflow_job')
])
def test_get_type_for_model(model, name):
    assert common.get_type_for_model(model) == name


@pytest.fixture
def memoized_function(mocker):
    @common.memoize(track_function=True)
    def myfunction(key, value):
        if key not in myfunction.calls:
            myfunction.calls[key] = 0

        myfunction.calls[key] += 1

        if myfunction.calls[key] == 1:
            return value
        else:
            return '%s called %s times' % (value, myfunction.calls[key])
    myfunction.calls = dict()
    return myfunction


def test_memoize_track_function(memoized_function):
    assert memoized_function('scott', 'scotterson') == 'scotterson'
    assert cache.get('myfunction') == {u'scott-scotterson': 'scotterson'}
    assert memoized_function('scott', 'scotterson') == 'scotterson'

    assert memoized_function.calls['scott'] == 1

    assert memoized_function('john', 'smith') == 'smith'
    assert cache.get('myfunction') == {u'scott-scotterson': 'scotterson', u'john-smith': 'smith'}
    assert memoized_function('john', 'smith') == 'smith'
    
    assert memoized_function.calls['john'] == 1


def test_memoize_delete(memoized_function):
    assert memoized_function('john', 'smith') == 'smith'
    assert memoized_function('john', 'smith') == 'smith'
    assert memoized_function.calls['john'] == 1
    
    assert cache.get('myfunction') == {u'john-smith': 'smith'}

    common.memoize_delete('myfunction')

    assert cache.get('myfunction') is None

    assert memoized_function('john', 'smith') == 'smith called 2 times'
    assert memoized_function.calls['john'] == 2


def test_memoize_parameter_error():
    @common.memoize(cache_key='foo', track_function=True)
    def fn():
        return

    with pytest.raises(common.IllegalArgumentError):
        fn()

