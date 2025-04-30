import subprocess
import time

import pytest
from unittest import mock

from awx.main.models.projects import Project
from awx.main.models.organization import Organization
from awx.main.models.inventory import Group, Inventory, InventoryUpdate, InventorySource
from awx.main.tests.live.tests.conftest import wait_for_job


NAME_PREFIX = "test-ivu"
GIT_REPO_FOLDER = "inventory_vars"


def create_new_by_name(model, **kwargs):
    """
    Create a new model instance. Delete an existing instance first.

    :param model: The Django model.
    :param dict kwargs: The keyword arguments required to create a model
        instance. Must contain at least `name`.
    :return: The model instance.
    """
    name = kwargs["name"]
    try:
        instance = model.objects.get(name=name)
    except model.DoesNotExist:
        pass
    else:
        print(f"FORCE DELETE {name}")
        instance.delete()
    finally:
        instance = model.objects.create(**kwargs)
    return instance


def wait_for_update(instance, timeout=3.0):
    """Wait until the last update of *instance* is finished."""
    start = time.time()
    while time.time() - start < timeout:
        if instance.current_job or instance.last_job or instance.last_job_run:
            break
        time.sleep(0.2)
    assert instance.current_job or instance.last_job or instance.last_job_run, f'Instance never updated id={instance.id}'
    update = instance.current_job or instance.last_job
    if update:
        wait_for_job(update)


@pytest.fixture
def organization():
    name = f"{NAME_PREFIX}-org"
    instance = create_new_by_name(Organization, name=name, description=f"Description for {name}")
    yield instance
    instance.delete()


@pytest.fixture
def project(organization, live_tmp_folder):
    name = f"{NAME_PREFIX}-project"
    instance = create_new_by_name(
        Project,
        name=name,
        description=f"Description for {name}",
        organization=organization,
        scm_url=f"file://{live_tmp_folder}/{GIT_REPO_FOLDER}",
        scm_type="git",
    )
    yield instance
    instance.delete()


@pytest.fixture
def inventory(organization):
    name = f"{NAME_PREFIX}-inventory"
    instance = create_new_by_name(
        Inventory,
        name=name,
        description=f"Description for {name}",
        organization=organization,
    )
    yield instance
    instance.delete()


@pytest.fixture
def inventory_source(inventory, project):
    name = f"{NAME_PREFIX}-invsrc"
    inv_src = InventorySource(
        name=name,
        source_project=project,
        source="scm",
        source_path="inventory_var_deleted_in_source.ini",
        inventory=inventory,
    )
    with mock.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.update'):
        inv_src.save()
    yield inv_src
    inv_src.delete()


def test_inventory_var_deleted_in_source(live_tmp_folder, project, inventory, inventory_source):
    """
    Verify that a variable which is deleted from its (git-)source between two
    updates is also deleted from the inventory.

    Verifies https://issues.redhat.com/browse/AAP-17690
    """
    inventory_source.update()
    wait_for_update(inventory_source)
    inv_vars = Inventory.objects.get(name=inventory.name).variables_dict
    print(f"After 1st update: {inv_vars=}")
    assert inv_vars == {"a": "value_a", "b": "value_b"}
    # Remove variable `a` from source.
    repo_path = f"{live_tmp_folder}/{GIT_REPO_FOLDER}"
    path = f"{repo_path}/inventory_var_deleted_in_source.ini"
    with open(path, "w") as fp:
        fp.write("[all:vars]\n")
        fp.write("b=value_b\n")
    subprocess.run('git add .; git commit -m "Update variables"', cwd=repo_path, shell=True)
    # Update the project to sync the changed repo contents.
    project.update()
    wait_for_update(project)
    # Update the inventory from the changed source.
    inventory_source.update()
    wait_for_update(inventory_source)
    #
    inv_vars = Inventory.objects.get(name=inventory.name).variables_dict
    print(f"After 2nd update: {inv_vars=}")
    assert inv_vars == {"b": "value_b"}
