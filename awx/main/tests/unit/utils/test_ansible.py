import os
import os.path

import pytest

from awx.main.tests import data
from awx.main.utils.ansible import could_be_playbook, could_be_inventory

DATA = os.path.join(os.path.dirname(data.__file__), 'ansible_utils')


@pytest.mark.parametrize('filename', os.listdir(os.path.join(DATA, 'playbooks', 'valid')))
def test_could_be_playbook(filename):
    path = os.path.join(DATA, 'playbooks', 'valid')
    assert could_be_playbook(DATA, path, filename).endswith(filename)


@pytest.mark.parametrize('filename', os.listdir(os.path.join(DATA, 'playbooks', 'invalid')))
def test_is_not_playbook(filename):
    path = os.path.join(DATA, 'playbooks', 'invalid')
    assert could_be_playbook(DATA, path, filename) is None


@pytest.mark.parametrize('filename', os.listdir(os.path.join(DATA, 'inventories', 'valid')))
def test_could_be_inventory(filename):
    path = os.path.join(DATA, 'inventories', 'valid')
    assert could_be_inventory(DATA, path, filename).endswith(filename)


@pytest.mark.parametrize('filename', os.listdir(os.path.join(DATA, 'inventories', 'invalid')))
def test_is_not_inventory(filename):
    path = os.path.join(DATA, 'inventories', 'invalid')
    assert could_be_inventory(DATA, path, filename) is None
