# -*- coding: utf-8 -*-

import pytest

from types import SimpleNamespace
from unittest import mock

from awx.main.models import Credential, CredentialType
from awx.main.models.credential import CredentialTypeHelper, ManagedCredentialType

from django.apps import apps


@pytest.mark.django_db
def test_unique_hash_with_unicode():
    ct = CredentialType.objects.create(name="Väult", kind="vault")
    cred = Credential.objects.create(
        name="Iñtërnâtiônàlizætiøn", credential_type=ct, inputs={"vault_id": "🐉🐉🐉"}
    )
    assert cred.unique_hash(display=True) == "Väult (id=🐉🐉🐉)"


def test_custom_cred_with_empty_encrypted_field():
    ct = CredentialType(
        name="My Custom Cred",
        kind="custom",
        inputs={"fields": [{"id": "some_field", "label": "My Field", "secret": True}]},
    )
    cred = Credential(id=4, name="Testing 1 2 3", credential_type=ct, inputs={})
    assert cred.encrypt_field("some_field", None) is None


@pytest.mark.parametrize(
    (
        "apps",
        "app_config",
    ),
    [
        (
            apps,
            None,
        ),
        (
            None,
            apps.get_app_config("main"),
        ),
    ],
)
def test__get_credential_type_class(apps, app_config):
    ct = CredentialType._get_credential_type_class(apps=apps, app_config=app_config)
    assert ct.__name__ == "CredentialType"


def test__get_credential_type_class_invalid_params():
    with pytest.raises(ValueError) as e:
        CredentialType._get_credential_type_class(
            apps=apps, app_config=apps.get_app_config("main")
        )

    assert type(e.value) is ValueError
    assert str(e.value) == "Expected only apps or app_config to be defined, not both"


def test_workload_tokens_owned_by_prep_data():
    """Test that workload tokens live on TaskPrepData, not individual credentials."""
    from awx.main.tasks.prep import TaskPrepData

    ct = CredentialType(name="Test Cred", kind="vault")
    cred = Credential(id=1, name="Test Credential", credential_type=ct, inputs={})
    prep = TaskPrepData.for_testing(
        None, [cred], workload_tokens={42: {"workload_identity_token": "eyJ.test"}}
    )

    assert prep.workload_tokens == {42: {"workload_identity_token": "eyJ.test"}}
    # All credentials in the prep share the same workload_tokens
    assert prep.credentials[0]._prep_data is prep


def test_workload_tokens_independent_between_prep_instances():
    """Test that workload tokens are independent between TaskPrepData instances."""
    from awx.main.tasks.prep import TaskPrepData

    ct = CredentialType(name="Test Cred", kind="vault")
    cred1 = Credential(id=1, name="Cred 1", credential_type=ct, inputs={})
    cred2 = Credential(id=2, name="Cred 2", credential_type=ct, inputs={})
    prep1 = TaskPrepData.for_testing(None, [cred1], workload_tokens={1: {"token": "a"}})
    prep2 = TaskPrepData.for_testing(None, [cred2], workload_tokens={2: {"token": "b"}})

    assert prep1.workload_tokens == {1: {"token": "a"}}
    assert prep2.workload_tokens == {2: {"token": "b"}}
    assert prep1.workload_tokens is not prep2.workload_tokens


def test_credentials_of_kind():
    """Test TaskPrepData.credentials_of_kind filters by credential type kind."""
    from awx.main.tasks.prep import TaskPrepData

    ssh_type = CredentialType(name="SSH", kind="ssh")
    vault_type = CredentialType(name="Vault", kind="vault")
    cloud_type = CredentialType(name="AWS", kind="cloud")

    ssh_cred = Credential(id=1, name="ssh", credential_type=ssh_type, inputs={})
    vault_cred1 = Credential(
        id=2, name="vault-1", credential_type=vault_type, inputs={}
    )
    vault_cred2 = Credential(
        id=3, name="vault-2", credential_type=vault_type, inputs={}
    )
    cloud_cred = Credential(id=4, name="aws", credential_type=cloud_type, inputs={})

    prep = TaskPrepData(
        None, [ssh_cred, vault_cred1, cloud_cred, vault_cred2], galaxy_credentials=[]
    )

    vault_creds = prep.credentials_of_kind("vault")
    assert len(vault_creds) == 2
    assert vault_creds[0].pk == 2
    assert vault_creds[1].pk == 3

    ssh_creds = prep.credentials_of_kind("ssh")
    assert len(ssh_creds) == 1
    assert ssh_creds[0].pk == 1

    net_creds = prep.credentials_of_kind("net")
    assert net_creds == []


def test_load_plugin_passes_description():
    plugin = SimpleNamespace(
        name="test_plugin",
        inputs={"fields": []},
        backend=None,
        plugin_description="A test plugin",
    )
    CredentialType.load_plugin("test_ns", plugin)
    entry = ManagedCredentialType.registry["test_ns"]
    assert entry.description == "A test plugin"
    del ManagedCredentialType.registry["test_ns"]


def test_load_plugin_missing_description():
    plugin = SimpleNamespace(name="test_plugin", inputs={"fields": []}, backend=None)
    CredentialType.load_plugin("test_ns", plugin)
    entry = ManagedCredentialType.registry["test_ns"]
    assert entry.description == ""
    del ManagedCredentialType.registry["test_ns"]


def test_get_creation_params_external_includes_description():
    cred_type = SimpleNamespace(
        namespace="test_ns", kind="external", name="Test", description="My description"
    )
    params = CredentialTypeHelper.get_creation_params(cred_type)
    assert params["description"] == "My description"


def test_get_creation_params_external_missing_description():
    cred_type = SimpleNamespace(namespace="test_ns", kind="external", name="Test")
    params = CredentialTypeHelper.get_creation_params(cred_type)
    assert params["description"] == ""


@pytest.mark.django_db
def test_setup_tower_managed_defaults_updates_description():
    registry_entry = SimpleNamespace(
        namespace="test_ns",
        kind="external",
        name="Test Plugin",
        inputs={"fields": []},
        backend=None,
        description="Updated description",
    )
    # Create an existing credential type with no description
    ct = CredentialType.objects.create(
        name="Test Plugin", kind="external", namespace="old_ns"
    )
    assert ct.description == ""

    with mock.patch.dict(
        ManagedCredentialType.registry, {"test_ns": registry_entry}, clear=True
    ):
        CredentialType._setup_tower_managed_defaults()

    ct.refresh_from_db()
    assert ct.description == "Updated description"
    assert ct.namespace == "test_ns"
