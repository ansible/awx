# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.
import os
import pytest
from uuid import uuid4

from awx.main.utils import common


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
