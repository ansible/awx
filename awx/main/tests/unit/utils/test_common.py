# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.
import os
import pytest
from uuid import uuid4

from awx.main.utils import common

from awx.main.models import (
    Job,
    AdHocCommand,
    InventoryUpdate,
    ProjectUpdate,
    SystemJob,
    WorkflowJob
)


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
