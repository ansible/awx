# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.
import os
import pytest
from uuid import uuid4
import json
import yaml
from unittest import mock

from backports.tempfile import TemporaryDirectory
from django.conf import settings

from rest_framework.exceptions import ParseError

from awx.main.utils import common

from awx.main.models import (
    Job,
    AdHocCommand,
    InventoryUpdate,
    ProjectUpdate,
    SystemJob,
    WorkflowJob,
    Inventory,
    JobTemplate,
    UnifiedJobTemplate,
    UnifiedJob
)


@pytest.mark.parametrize('input_, output', [
    ({"foo": "bar"}, {"foo": "bar"}),
    ('{"foo": "bar"}', {"foo": "bar"}),
    ('---\nfoo: bar', {"foo": "bar"}),
    (4399, {}),
])
def test_parse_yaml_or_json(input_, output):
    assert common.parse_yaml_or_json(input_) == output


def test_recursive_vars_not_allowed():
    rdict = {}
    rdict['a'] = rdict
    # YAML dumper will use a tag to give recursive data
    data = yaml.dump(rdict, default_flow_style=False)
    with pytest.raises(ParseError) as exc:
        common.parse_yaml_or_json(data, silent_failure=False)
    assert 'Circular reference detected' in str(exc)


class TestParserExceptions:

    @staticmethod
    def json_error(data):
        try:
            json.loads(data)
            return None
        except Exception as e:
            return str(e)

    @staticmethod
    def yaml_error(data):
        try:
            yaml.safe_load(data)
            return None
        except Exception as e:
            return str(e)

    def test_invalid_JSON_and_YAML(self):
        data = "{key:val"
        with pytest.raises(ParseError) as exc:
            common.parse_yaml_or_json(data, silent_failure=False)
        message = str(exc.value)
        assert "Cannot parse as" in message
        assert self.json_error(data) in message
        assert self.yaml_error(data) in message

    def test_invalid_vars_type(self):
        data = "[1, 2, 3]"
        with pytest.raises(ParseError) as exc:
            common.parse_yaml_or_json(data, silent_failure=False)
        message = str(exc.value)
        assert "Cannot parse as" in message
        assert "Input type `list` is not a dictionary" in message


def test_set_environ():
    key = str(uuid4())
    old_environ = os.environ.copy()
    with common.set_environ(**{key: 'bar'}):
        assert os.environ[key] == 'bar'
        assert set(os.environ.keys()) - set(old_environ.keys()) == set([key])
    assert os.environ == old_environ
    assert key not in os.environ


TEST_MODELS = [
    (Job, 'job'),
    (AdHocCommand, 'ad_hoc_command'),
    (InventoryUpdate, 'inventory_update'),
    (ProjectUpdate, 'project_update'),
    (SystemJob, 'system_job'),
    (WorkflowJob, 'workflow_job'),
    (UnifiedJob, 'unified_job'),
    (Inventory, 'inventory'),
    (JobTemplate, 'job_template'),
    (UnifiedJobTemplate, 'unified_job_template')
]


# Cases relied on for scheduler dependent jobs list
@pytest.mark.parametrize('model,name', TEST_MODELS)
def test_get_type_for_model(model, name):
    assert common.get_type_for_model(model) == name


@pytest.mark.django_db
def test_get_model_for_invalid_type():
    with pytest.raises(LookupError):
        common.get_model_for_type('foobar')


@pytest.mark.django_db
@pytest.mark.parametrize("model_type,model_class", [
    (name, cls) for cls, name in TEST_MODELS
])
def test_get_model_for_valid_type(model_type, model_class):
    assert common.get_model_for_type(model_type) == model_class


@pytest.fixture
def memoized_function(mocker, mock_cache):
    with mock.patch('awx.main.utils.common.get_memoize_cache', return_value=mock_cache):
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


def test_memoize_track_function(memoized_function, mock_cache):
    assert memoized_function('scott', 'scotterson') == 'scotterson'
    assert mock_cache.get('myfunction') == {u'scott-scotterson': 'scotterson'}
    assert memoized_function('scott', 'scotterson') == 'scotterson'

    assert memoized_function.calls['scott'] == 1

    assert memoized_function('john', 'smith') == 'smith'
    assert mock_cache.get('myfunction') == {u'scott-scotterson': 'scotterson', u'john-smith': 'smith'}
    assert memoized_function('john', 'smith') == 'smith'

    assert memoized_function.calls['john'] == 1


def test_memoize_delete(memoized_function, mock_cache):
    assert memoized_function('john', 'smith') == 'smith'
    assert memoized_function('john', 'smith') == 'smith'
    assert memoized_function.calls['john'] == 1

    assert mock_cache.get('myfunction') == {u'john-smith': 'smith'}

    with mock.patch('awx.main.utils.common.memoize_delete', side_effect=mock_cache.delete):
        common.memoize_delete('myfunction')

    assert mock_cache.get('myfunction') is None

    assert memoized_function('john', 'smith') == 'smith called 2 times'
    assert memoized_function.calls['john'] == 2


def test_memoize_parameter_error():

    with pytest.raises(common.IllegalArgumentError):
        @common.memoize(cache_key='foo', track_function=True)
        def fn():
            return


def test_extract_ansible_vars():
    my_dict = {
        "foobar": "baz",
        "ansible_connetion_setting": "1928"
    }
    redacted, var_list = common.extract_ansible_vars(json.dumps(my_dict))
    assert var_list == set(['ansible_connetion_setting'])
    assert redacted == {"foobar": "baz"}


def test_get_custom_venv_choices():
    bundled_venv = os.path.join(settings.BASE_VENV_PATH, 'ansible', '')
    assert sorted(common.get_custom_venv_choices()) == [bundled_venv]

    with TemporaryDirectory(dir=settings.BASE_VENV_PATH, prefix='tmp') as temp_dir:
        os.makedirs(os.path.join(temp_dir, 'bin', 'activate'))

        custom_venv_dir = os.path.join(temp_dir, 'custom')
        custom_venv_1 = os.path.join(custom_venv_dir, 'venv-1')
        custom_venv_awx = os.path.join(custom_venv_dir, 'custom', 'awx')

        os.makedirs(os.path.join(custom_venv_1, 'bin', 'activate'))
        os.makedirs(os.path.join(custom_venv_awx, 'bin', 'activate'))

        assert sorted(common.get_custom_venv_choices([custom_venv_dir])) == [
            bundled_venv,
            os.path.join(temp_dir, ''),
            os.path.join(custom_venv_1, '')
        ]
