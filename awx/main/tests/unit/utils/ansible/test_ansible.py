import os
import os.path

import pytest

from awx.main.utils.ansible import could_be_playbook, could_be_inventory

HERE, _ = os.path.split(__file__)


@pytest.mark.parametrize('filename', os.listdir(os.path.join(HERE, 'playbooks', 'valid')))
def test_could_be_playbook(filename):
    path = os.path.join(HERE, 'playbooks', 'valid')
    assert could_be_playbook(HERE, path, filename).endswith(filename)


@pytest.mark.parametrize('filename', os.listdir(os.path.join(HERE, 'playbooks', 'invalid')))
def test_is_not_playbook(filename):
    path = os.path.join(HERE, 'playbooks', 'invalid')
    assert could_be_playbook(HERE, path, filename) is None


@pytest.mark.parametrize('filename', os.listdir(os.path.join(HERE, 'inventories', 'valid')))
def test_could_be_inventory(filename):
    path = os.path.join(HERE, 'inventories', 'valid')
    assert could_be_inventory(HERE, path, filename).endswith(filename)


@pytest.mark.parametrize('filename', os.listdir(os.path.join(HERE, 'inventories', 'invalid')))
def test_is_not_inventory(filename):
    path = os.path.join(HERE, 'inventories', 'invalid')
    assert could_be_inventory(HERE, path, filename) is None
