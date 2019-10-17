import os
import os.path

import pytest

from awx.main.tests import data
from awx.main.utils.ansible import could_be_playbook, could_be_inventory, unique_folders

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


def test_unique_paths():
    playbooks = [
        'folder1/azure_credentials_test.yml',
        'become.yml',
        'check.yml',
        'clear_facts.yml',
        'cloud_modules/aws.yml',
        'cloud_modules/azure_rm.yml',
        'cloud_modules/gce.yml',
        'cloud_modules/vmware.yml',
        'custom_json.yml',
        'debug-50.yml',
        'debug.yml',
        'debug2.yml',
        'tower_modules/main.yml',
        'tower_modules/wrapper.yml',
        'use_debug_collection_role.yml',
        'use_facts.yml',
        'utils/trigger_update.yml',
        'valid_yaml_invalid_ansible.yml',
        'vault.yml',
        'vaulted_ansible_env.yml',
        'vaulted_debug_hostvars.yml']
    print(unique_folders(playbooks))
    assert unique_folders(playbooks) == set(['', 'utils', 'cloud_modules', 'folder1', 'tower_modules'])
