# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.
import pytest

from awx.main.utils import common


@pytest.mark.parametrize('input_, output', [
    ({"foo": "bar"}, {"foo": "bar"}),
    ('{"foo": "bar"}', {"foo": "bar"}),
    ('---\nfoo: bar', {"foo": "bar"}),
    (4399, {}),
])
def test_parse_yaml_or_json(input_, output):
    assert common.parse_yaml_or_json(input_) == output
