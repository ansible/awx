# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.
import os
import pytest
from uuid import uuid4
import json
import yaml
from unittest import mock

from rest_framework.exceptions import ParseError

from awx.main.utils import common

from awx.main.models import Job, AdHocCommand, InventoryUpdate, ProjectUpdate, SystemJob, WorkflowJob, Inventory, JobTemplate, UnifiedJobTemplate, UnifiedJob


@pytest.mark.parametrize(
    'input_, output',
    [
        ({"foo": "bar"}, {"foo": "bar"}),
        ('{"foo": "bar"}', {"foo": "bar"}),
        ('---\nfoo: bar', {"foo": "bar"}),
        (4399, {}),
    ],
)
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
    (UnifiedJobTemplate, 'unified_job_template'),
]


# Cases relied on for scheduler dependent jobs list
@pytest.mark.parametrize('model,name', TEST_MODELS)
def test_get_type_for_model(model, name):
    assert common.get_type_for_model(model) == name


def test_get_model_for_invalid_type():
    with pytest.raises(LookupError):
        common.get_model_for_type('foobar')


@pytest.mark.parametrize("model_type,model_class", [(name, cls) for cls, name in TEST_MODELS])
def test_get_model_for_valid_type(model_type, model_class):
    assert common.get_model_for_type(model_type) == model_class


@pytest.mark.parametrize("model_type,model_class", [(name, cls) for cls, name in TEST_MODELS])
def test_get_capacity_type(model_type, model_class):
    if model_type in ('job', 'ad_hoc_command', 'inventory_update', 'job_template'):
        expectation = 'execution'
    elif model_type in ('project_update', 'system_job'):
        expectation = 'control'
    else:
        expectation = None
    if model_type in ('unified_job', 'unified_job_template', 'inventory'):
        with pytest.raises(RuntimeError):
            common.get_capacity_type(model_class)
    else:
        assert common.get_capacity_type(model_class) == expectation
        assert common.get_capacity_type(model_class()) == expectation


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
    my_dict = {"foobar": "baz", "ansible_connetion_setting": "1928"}
    redacted, var_list = common.extract_ansible_vars(json.dumps(my_dict))
    assert var_list == set(['ansible_connetion_setting'])
    assert redacted == {"foobar": "baz"}


@pytest.mark.parametrize(
    'scm_type, url, username, password, check_special_cases, scp_format, expected',
    [
        # General/random cases
        ('git', '', True, True, True, False, ''),
        ('git', 'git://example.com/foo.git', True, True, True, False, 'git://example.com/foo.git'),
        ('git', 'http://example.com/foo.git', True, True, True, False, 'http://example.com/foo.git'),
        ('git', 'example.com:bar.git', True, True, True, False, 'git+ssh://example.com/bar.git'),
        ('git', 'user@example.com:bar.git', True, True, True, False, 'git+ssh://user@example.com/bar.git'),
        ('git', '127.0.0.1:bar.git', True, True, True, False, 'git+ssh://127.0.0.1/bar.git'),
        ('git', 'git+ssh://127.0.0.1/bar.git', True, True, True, True, '127.0.0.1:bar.git'),
        ('git', 'ssh://127.0.0.1:22/bar.git', True, True, True, False, 'ssh://127.0.0.1:22/bar.git'),
        ('git', 'ssh://root@127.0.0.1:22/bar.git', True, True, True, False, 'ssh://root@127.0.0.1:22/bar.git'),
        ('git', 'some/path', True, True, True, False, 'file:///some/path'),
        ('git', '/some/path', True, True, True, False, 'file:///some/path'),
        # Invalid URLs - ensure we error properly
        ('cvs', 'anything', True, True, True, False, ValueError('Unsupported SCM type "cvs"')),
        ('svn', 'anything-without-colon-slash-slash', True, True, True, False, ValueError('Invalid svn URL')),
        ('git', 'http://example.com:123invalidport/foo.git', True, True, True, False, ValueError('Invalid git URL')),
        ('git', 'git+ssh://127.0.0.1/bar.git', True, True, True, False, ValueError('Unsupported git URL')),
        ('git', 'git@example.com:3000:/git/repo.git', True, True, True, False, ValueError('Invalid git URL')),
        ('insights', 'git://example.com/foo.git', True, True, True, False, ValueError('Unsupported insights URL')),
        ('svn', 'file://example/path', True, True, True, False, ValueError('Unsupported host "example" for file:// URL')),
        ('svn', 'svn:///example', True, True, True, False, ValueError('Host is required for svn URL')),
        # Username/password cases
        ('git', 'https://example@example.com/bar.git', False, True, True, False, 'https://example.com/bar.git'),
        ('git', 'https://example@example.com/bar.git', 'user', True, True, False, 'https://user@example.com/bar.git'),
        ('git', 'https://example@example.com/bar.git', 'user:pw', True, True, False, 'https://user%3Apw@example.com/bar.git'),
        ('git', 'https://example@example.com/bar.git', False, 'pw', True, False, 'https://example.com/bar.git'),
        ('git', 'https://some:example@example.com/bar.git', True, False, True, False, 'https://some@example.com/bar.git'),
        ('git', 'https://some:example@example.com/bar.git', False, False, True, False, 'https://example.com/bar.git'),
        ('git', 'https://example.com/bar.git', 'user', 'pw', True, False, 'https://user:pw@example.com/bar.git'),
        ('git', 'https://example@example.com/bar.git', False, 'something', True, False, 'https://example.com/bar.git'),
        # Special github/bitbucket cases
        ('git', 'notgit@github.com:ansible/awx.git', True, True, True, False, ValueError('Username must be "git" for SSH access to github.com.')),
        (
            'git',
            'notgit@bitbucket.org:does-not-exist/example.git',
            True,
            True,
            True,
            False,
            ValueError('Username must be "git" for SSH access to bitbucket.org.'),
        ),
        (
            'git',
            'notgit@altssh.bitbucket.org:does-not-exist/example.git',
            True,
            True,
            True,
            False,
            ValueError('Username must be "git" for SSH access to altssh.bitbucket.org.'),
        ),
        ('git', 'git:password@github.com:ansible/awx.git', True, True, True, False, 'git+ssh://git@github.com/ansible/awx.git'),
        # Disabling the special handling should not raise an error
        ('git', 'notgit@github.com:ansible/awx.git', True, True, False, False, 'git+ssh://notgit@github.com/ansible/awx.git'),
        ('git', 'notgit@bitbucket.org:does-not-exist/example.git', True, True, False, False, 'git+ssh://notgit@bitbucket.org/does-not-exist/example.git'),
        (
            'git',
            'notgit@altssh.bitbucket.org:does-not-exist/example.git',
            True,
            True,
            False,
            False,
            'git+ssh://notgit@altssh.bitbucket.org/does-not-exist/example.git',
        ),
        # awx#12992 - IPv6
        ('git', 'http://[fd00:1234:2345:6789::11]:3000/foo.git', True, True, True, False, 'http://[fd00:1234:2345:6789::11]:3000/foo.git'),
        ('git', 'http://foo:bar@[fd00:1234:2345:6789::11]:3000/foo.git', True, True, True, False, 'http://foo:bar@[fd00:1234:2345:6789::11]:3000/foo.git'),
        ('git', 'example@[fd00:1234:2345:6789::11]:example/foo.git', True, True, True, False, 'git+ssh://example@[fd00:1234:2345:6789::11]/example/foo.git'),
    ],
)
def test_update_scm_url(scm_type, url, username, password, check_special_cases, scp_format, expected):
    if isinstance(expected, Exception):
        with pytest.raises(type(expected)) as excinfo:
            common.update_scm_url(scm_type, url, username, password, check_special_cases, scp_format)
        assert str(excinfo.value) == str(expected)
    else:
        assert common.update_scm_url(scm_type, url, username, password, check_special_cases, scp_format) == expected
