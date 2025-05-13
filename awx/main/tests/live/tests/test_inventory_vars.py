import subprocess
import time
import os.path
from urllib.parse import urlsplit

import pytest
from unittest import mock

from awx.main.models.projects import Project
from awx.main.models.organization import Organization
from awx.main.models.inventory import Inventory, InventorySource
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


def change_source_vars_and_update(invsrc, group_vars):
    """
    Change the variables content of an inventory source and update its
    inventory.

    Does not return before the inventory update is finished.

    :param invsrc: The inventory source instance.
    :param dict group_vars: The variables for various groups. Format::

        {
            <group>: {<variable>: <value>, <variable>: <value>, ..}, <group>:
            {<variable>: <value>, <variable>: <value>, ..}, ..
        }

    :return: None
    """
    project = invsrc.source_project
    repo_path = urlsplit(project.scm_url).path
    filepath = os.path.join(repo_path, invsrc.source_path)
    # print(f"change_source_vars_and_update: {project=} {repo_path=} {filepath=}")
    with open(filepath, "w") as fp:
        for group, variables in group_vars.items():
            fp.write(f"[{group}:vars]\n")
            for name, value in variables.items():
                fp.write(f"{name}={value}\n")
    subprocess.run('git add .; git commit -m "Update variables in invsrc.source_path"', cwd=repo_path, shell=True)
    # Update the project to sync the changed repo contents.
    project.update()
    wait_for_update(project)
    # Update the inventory from the changed source.
    invsrc.update()
    wait_for_update(invsrc)


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
        overwrite_vars=True,
    )
    with mock.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.update'):
        inv_src.save()
    yield inv_src
    inv_src.delete()


@pytest.fixture
def inventory_source_factory(inventory, project):
    """
    Use this fixture if you want to use multiple inventory sources for the same
    inventory in your test.
    """
    # https://docs.pytest.org/en/stable/how-to/fixtures.html#factories-as-fixtures

    created = []
    # repo_path = f"{live_tmp_folder}/{GIT_REPO_FOLDER}"

    def _factory(inventory_file, name):
        # Make sure the inventory file exists before the inventory source
        # instance is created.
        #
        # Note: The current implementation of the inventory source object allows
        # to create an instance even when the inventory source file does not
        # exist. If this behaviour changes, uncomment the following code block
        # and add the fixture `live_tmp_folder` to the factory function
        # signature.
        #
        # inventory_file_path = os.path.join(repo_path, inventory_file) if not
        # os.path.isfile(inventory_file_path): with open(inventory_file_path,
        #     "w") as fp: pass subprocess.run(f'git add .; git commit -m "Create
        #         {inventory_file_path}"', cwd=repo_path, shell=True)
        #
        # Create the inventory source instance.
        name = f"{NAME_PREFIX}-invsrc-{name}"
        inv_src = InventorySource(
            name=name,
            source_project=project,
            source="scm",
            source_path=inventory_file,
            inventory=inventory,
            overwrite_vars=True,
        )
        with mock.patch('awx.main.models.unified_jobs.UnifiedJobTemplate.update'):
            inv_src.save()
        return inv_src

    yield _factory
    for instance in created:
        instance.delete()


def test_inventory_var_deleted_in_source(inventory, inventory_source):
    """
    Verify that a variable which is deleted from its (git-)source between two
    updates is also deleted from the inventory.

    Verifies https://issues.redhat.com/browse/AAP-17690
    """
    inventory_source.update()
    wait_for_update(inventory_source)
    assert {"a": "value_a", "b": "value_b"} == Inventory.objects.get(name=inventory.name).variables_dict
    # Remove variable `a` from source and verify that it is also removed from
    # the inventory variables.
    change_source_vars_and_update(inventory_source, {"all": {"b": "value_b"}})
    assert {"b": "value_b"} == Inventory.objects.get(name=inventory.name).variables_dict


def test_inventory_vars_with_multiple_sources(inventory, inventory_source_factory):
    """
    Verify a sequence of updates from various sources with changing content.
    """
    invsrc_a = inventory_source_factory("invsrc_a.ini", "A")
    invsrc_b = inventory_source_factory("invsrc_b.ini", "B")
    invsrc_c = inventory_source_factory("invsrc_c.ini", "C")

    change_source_vars_and_update(invsrc_a, {"all": {"x": "x_from_a", "y": "y_from_a"}})
    assert {"x": "x_from_a", "y": "y_from_a"} == Inventory.objects.get(name=inventory.name).variables_dict
    change_source_vars_and_update(invsrc_b, {"all": {"x": "x_from_b", "y": "y_from_b", "z": "z_from_b"}})
    assert {"x": "x_from_b", "y": "y_from_b", "z": "z_from_b"} == Inventory.objects.get(name=inventory.name).variables_dict
    change_source_vars_and_update(invsrc_c, {"all": {"x": "x_from_c", "z": "z_from_c"}})
    assert {"x": "x_from_c", "y": "y_from_b", "z": "z_from_c"} == Inventory.objects.get(name=inventory.name).variables_dict
    change_source_vars_and_update(invsrc_b, {"all": {}})
    assert {"x": "x_from_c", "y": "y_from_a", "z": "z_from_c"} == Inventory.objects.get(name=inventory.name).variables_dict
    change_source_vars_and_update(invsrc_c, {"all": {"z": "z_from_c"}})
    assert {"x": "x_from_a", "y": "y_from_a", "z": "z_from_c"} == Inventory.objects.get(name=inventory.name).variables_dict
    change_source_vars_and_update(invsrc_a, {"all": {}})
    assert {"z": "z_from_c"} == Inventory.objects.get(name=inventory.name).variables_dict
    change_source_vars_and_update(invsrc_c, {"all": {}})
    assert {} == Inventory.objects.get(name=inventory.name).variables_dict
